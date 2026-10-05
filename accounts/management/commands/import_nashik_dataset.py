import csv
from datetime import date, datetime, time
from pathlib import Path

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from accounts.models import Clinic, Role
from analytics.ml.pipeline import DefaulterRiskPipeline
from analytics.models import ChildRiskAssessment, MLModelMetadata
from children.models import Child
from vaccination.models import (DoseStatus, ScheduleVersion, ScheduledDose,
                                VaccineAdministrationRecord)
from vaccination.services import ScheduleEngine


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


class Command(BaseCommand):
    help = "Imports the synthetic Nashik 2026 dataset (clinics, 500 children, vaccination records)."

    def add_arguments(self, parser):
        parser.add_argument("--path", default=str(Path(settings.BASE_DIR) / "data" / "nashik"),
                            help="Folder containing the three Nashik CSV files")
        parser.add_argument("--skip-ml", action="store_true", help="Do not train the ML model / risk scores")
        parser.add_argument("--reset", action="store_true",
                            help="Delete previously imported Nashik parents (and their children) first")

    def handle(self, *args, **opts):
        base = Path(opts["path"])
        files = {k: base / v for k, v in {
            "clinics": "nashik_clinics.csv",
            "children": "nashik_children_2026.csv",
            "vaccs": "nashik_vaccinations_2026.csv"}.items()}
        for p in files.values():
            if not p.exists():
                raise CommandError(f"Missing file: {p}")

        if not ScheduleVersion.objects.filter(is_current=True).exists():
            call_command("seed_immunization_data")

        if opts["reset"]:
            n, _ = User.objects.filter(username__startswith="nsk_parent_").delete()
            self.stdout.write(f"Removed {n} previously imported records.")

        parent_pw = make_password("Parent@12345")   # hash once - much faster than 500 hashes
        worker_pw = make_password("Worker@12345")
        today = date.today()
        today_str = today.isoformat()

        with transaction.atomic():
            # ---- clinics + health workers
            clinics, workers = {}, {}
            for r in read_csv(files["clinics"]):
                clinic, _ = Clinic.objects.get_or_create(
                    registration_code=r["registration_code"],
                    defaults={"name": r["name"], "address": r["address"],
                              "contact_phone": r["contact_phone"], "contact_email": r["contact_email"]})
                clinics[r["registration_code"]] = clinic
                w, created = User.objects.get_or_create(
                    username=r["worker_username"],
                    defaults={"first_name": r["worker_first_name"], "last_name": r["worker_last_name"],
                              "email": r["worker_email"], "password": worker_pw})
                w.profile.role = Role.HEALTH_WORKER
                w.profile.assigned_clinic = clinic
                w.profile.save()
                workers[r["worker_username"]] = w
            self.stdout.write(f"Clinics: {len(clinics)}  Health workers: {len(workers)}")

            # ---- parents + children + schedules
            child_by_ref, dose_maps = {}, {}
            rows = read_csv(files["children"])
            for i, r in enumerate(rows, 1):
                parent, created = User.objects.get_or_create(
                    username=r["guardian_username"],
                    defaults={"first_name": r["guardian_first_name"], "last_name": r["guardian_last_name"],
                              "email": r["guardian_email"], "password": parent_pw})
                parent.profile.role = Role.PARENT
                parent.profile.phone_number = r["guardian_phone"]
                parent.profile.save()

                child, c_created = Child.objects.get_or_create(
                    guardian=parent, first_name=r["first_name"], last_name=r["last_name"],
                    date_of_birth=date.fromisoformat(r["date_of_birth"]),
                    defaults={"gender": r["gender"], "blood_group": r["blood_group"],
                              "guardian_relationship": r["guardian_relationship"],
                              "assigned_clinic": clinics[r["clinic_code"]],
                              "allergies": r["allergies"]})
                if c_created:
                    reg = datetime.combine(date.fromisoformat(r["registration_date"]), time(10, 30))
                    Child.objects.filter(pk=child.pk).update(created_at=timezone.make_aware(reg))
                ScheduleEngine.generate_child_schedule(child)
                child_by_ref[r["child_ref"]] = child
                dose_maps[r["child_ref"]] = {
                    (d.recommended_dose.vaccine.code, d.recommended_dose.dose_number): d
                    for d in child.scheduled_doses.select_related("recommended_dose__vaccine")}
                if i % 100 == 0:
                    self.stdout.write(f"  children processed: {i}/{len(rows)}")

            # ---- administration records
            created_rec = skipped = 0
            for r in read_csv(files["vaccs"]):
                if r["administered_date"] > today_str:      # never import future-dated records
                    skipped += 1
                    continue
                dose = dose_maps[r["child_ref"]].get((r["vaccine_code"], int(r["dose_number"])))
                if dose is None or hasattr(dose, "administration_record"):
                    skipped += 1
                    continue
                VaccineAdministrationRecord.objects.create(
                    scheduled_dose=dose, child=child_by_ref[r["child_ref"]],
                    administered_date=date.fromisoformat(r["administered_date"]),
                    batch_number=r["batch_number"], facility=clinics[r["facility_code"]],
                    administered_by=workers[r["administered_by_username"]],
                    clinical_notes=r["notes"], adverse_reaction=r["adverse_reaction"] == "TRUE",
                    adverse_reaction_notes=r["notes"] if r["adverse_reaction"] == "TRUE" else "")
                dose.status = DoseStatus.COMPLETED
                dose.save(update_fields=["status", "updated_at"])
                created_rec += 1

            for child in child_by_ref.values():          # refresh overdue / due-today flags
                ScheduleEngine.refresh_child_schedule_statuses(child)

        self.stdout.write(f"Administration records created: {created_rec} (skipped {skipped})")

        # ---- ML risk scores
        if not opts["skip_ml"]:
            metrics = DefaulterRiskPipeline.train_and_persist()
            meta = MLModelMetadata.objects.create(
                model_name="Baseline Random Forest Adherence Predictor (Nashik import)", version="1.0.0",
                accuracy=metrics["accuracy"], precision=metrics["precision"], recall=metrics["recall"],
                f1_score=metrics["f1_score"], features_used=", ".join(metrics["features"]))
            for child in child_by_ref.values():
                pred = DefaulterRiskPipeline.predict_risk(child)
                ChildRiskAssessment.objects.update_or_create(
                    child=child, defaults={"model_version": meta, "risk_level": pred["level"],
                                           "probability": pred["probability"], "top_risk_factor": pred["factor"]})
            self.stdout.write("ML risk assessments created.")

        self.stdout.write(self.style.SUCCESS(
            f"Done. {len(child_by_ref)} children imported. Parent login: nsk_parent_0001 / Parent@12345; "
            f"health worker: nurse_nsk_01 / Worker@12345"))
