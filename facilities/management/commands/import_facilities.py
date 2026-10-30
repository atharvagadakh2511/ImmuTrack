
import csv
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from facilities.models import Facility


class Command(BaseCommand):
    help = "Import Maharashtra hospitals and vaccination centres from CSV"

    def handle(self, *args, **options):

        csv_path = (
            Path(settings.BASE_DIR)
            / "immutrack_maharashtra_facilities_starter.csv"
        )

        if not csv_path.exists():
            raise CommandError(f"CSV file not found: {csv_path}")

        created = 0
        updated = 0

        with open(csv_path, "r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)

            required_columns = {
                "facility_id",
                "district",
                "city_or_locality",
                "facility_name",
                "facility_type",
                "ownership",
            }

            if not required_columns.issubset(reader.fieldnames or []):
                raise CommandError("CSV file is missing required columns.")

            with transaction.atomic():
                for row in reader:

                    facility_id = (row.get("facility_id") or "").strip()

                    if not facility_id:
                        continue

                    defaults = {
                        "district": (row.get("district") or "").strip(),
                        "city_or_locality": (row.get("city_or_locality") or "").strip(),
                        "facility_name": (row.get("facility_name") or "").strip(),
                        "facility_type": (row.get("facility_type") or "").strip(),
                        "ownership": (row.get("ownership") or "Government").strip(),
                        "vaccination_service_status": (
                            row.get("vaccination_service_status")
                            or "Not verified - contact facility"
                        ).strip(),
                        "phone": (row.get("phone") or "").strip(),
                        "full_address": (row.get("full_address") or "").strip(),
                        "latitude": (row.get("latitude") or "").strip() or None,
                        "longitude": (row.get("longitude") or "").strip() or None,
                        "source_url": (row.get("source_url") or "").strip(),
                        "data_note": (row.get("data_note") or "").strip(),
                    }

                    _, was_created = Facility.objects.update_or_create(
                        facility_id=facility_id,
                        defaults=defaults,
                    )

                    if was_created:
                        created += 1
                    else:
                        updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Import complete: {created} created, {updated} updated."
            )
        )
