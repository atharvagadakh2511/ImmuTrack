from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.management import call_command
from accounts.models import Role, Clinic
from children.models import Child, Gender, Relationship
from vaccination.models import ScheduledDose, DoseStatus, VaccineAdministrationRecord
from vaccination.services import ScheduleEngine
from analytics.ml.pipeline import DefaulterRiskPipeline
from analytics.models import ChildRiskAssessment, MLModelMetadata
from datetime import date, timedelta

class Command(BaseCommand):
    help = 'Seeds complete demonstration users, children, administration records, and runs initial ML model'

    def handle(self, *args, **options):
        self.stdout.write("--- Seeding ImmuTrack Demonstration Environment ---")
        
        # 1. Seed UIP Vaccines
        call_command('seed_immunization_data')
        
        delhi_clinic = Clinic.objects.get(registration_code="PHC-DEL-01")
        blr_clinic = Clinic.objects.get(registration_code="CHC-BLR-04")

        # 2. Create Users
        # Admin
        admin_user, _ = User.objects.get_or_create(
            username="admin",
            defaults={'first_name': "Super", 'last_name': "Administrator", 'email': "admin@immutrack.gov.in", 'is_staff': True, 'is_superuser': True}
        )
        admin_user.set_password("Admin@12345")
        admin_user.profile.role = Role.ADMIN
        admin_user.save()
        admin_user.profile.save()

        # Health Worker 1
        hw_user, _ = User.objects.get_or_create(
            username="nurse_priya",
            defaults={'first_name': "Priya", 'last_name': "Sharma", 'email': "nurse.priya@delhi.gov.in"}
        )
        hw_user.set_password("Worker@12345")
        hw_user.profile.role = Role.HEALTH_WORKER
        hw_user.profile.assigned_clinic = delhi_clinic
        hw_user.save()
        hw_user.profile.save()

        # Parent 1
        parent_user, _ = User.objects.get_or_create(
            username="rajesh_kumar",
            defaults={'first_name': "Rajesh", 'last_name': "Kumar", 'email': "rajesh.parent@example.com"}
        )
        parent_user.set_password("Parent@12345")
        parent_user.profile.role = Role.PARENT
        parent_user.profile.phone_number = "+91-9876543210"
        parent_user.save()
        parent_user.profile.save()

        # 3. Create Sample Children
        # Child 1: Aarav (6 months old, on-time history)
        c1, _ = Child.objects.get_or_create(
            guardian=parent_user,
            first_name="Aarav",
            last_name="Kumar",
            defaults={
                'date_of_birth': date.today() - timedelta(days=180),
                'gender': Gender.MALE,
                'blood_group': "B+",
                'guardian_relationship': Relationship.FATHER,
                'assigned_clinic': delhi_clinic,
            }
        )
        ScheduleEngine.generate_child_schedule(c1)

        # Administer early doses for Aarav
        birth_doses = c1.scheduled_doses.filter(recommended_dose__offset_days=0, recommended_dose__offset_months=0)
        for bd in birth_doses:
            if not hasattr(bd, 'administration_record'):
                VaccineAdministrationRecord.objects.create(
                    scheduled_dose=bd,
                    child=c1,
                    administered_date=c1.date_of_birth,
                    batch_number="UIP-DEL-2025-01",
                    facility=delhi_clinic,
                    administered_by=hw_user,
                    clinical_notes="Administered at delivery room. Normal reaction."
                )
                bd.status = DoseStatus.COMPLETED
                bd.save()

        # Child 2: Ananya (10 months old, overdue Pentavalent)
        c2, _ = Child.objects.get_or_create(
            guardian=parent_user,
            first_name="Ananya",
            last_name="Kumar",
            defaults={
                'date_of_birth': date.today() - timedelta(days=300),
                'gender': Gender.FEMALE,
                'blood_group': "O+",
                'guardian_relationship': Relationship.FATHER,
                'assigned_clinic': delhi_clinic,
            }
        )
        ScheduleEngine.generate_child_schedule(c2)
        ScheduleEngine.refresh_child_schedule_statuses(c2)

        # 4. Train Initial Baseline ML Model
        metrics = DefaulterRiskPipeline.train_and_persist()
        meta = MLModelMetadata.objects.create(
            model_name="Baseline Random Forest Adherence Predictor",
            version="1.0.0",
            accuracy=metrics['accuracy'],
            precision=metrics['precision'],
            recall=metrics['recall'],
            f1_score=metrics['f1_score'],
            features_used=", ".join(metrics['features'])
        )

        for child_item in [c1, c2]:
            pred = DefaulterRiskPipeline.predict_risk(child_item)
            ChildRiskAssessment.objects.update_or_create(
                child=child_item,
                defaults={
                    'model_version': meta,
                    'risk_level': pred['level'],
                    'probability': pred['probability'],
                    'top_risk_factor': pred['factor']
                }
            )

        self.stdout.write(self.style.SUCCESS("All demo roles, sample child histories, schedules, and ML models successfully initialized!"))
