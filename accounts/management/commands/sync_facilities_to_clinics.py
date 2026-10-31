
from django.core.management.base import BaseCommand
from accounts.models import Clinic
from facilities.models import Facility


class Command(BaseCommand):
    help = "Add Maharashtra facilities to the existing Clinic records"

    def handle(self, *args, **options):
        created = 0
        skipped = 0

        for facility in Facility.objects.all().order_by("facility_id"):
            original_name = (facility.facility_name or "").strip()

            if not original_name:
                skipped += 1
                continue

            # Avoid duplicating existing clinics by name.
            if Clinic.objects.filter(name__iexact=original_name).exists():
                skipped += 1
                continue

            registration_code = f"MH-{facility.facility_id}"

            # Avoid importing the same facility twice.
            if Clinic.objects.filter(
                registration_code=registration_code
            ).exists():
                skipped += 1
                continue

            # Keep the name within the Clinic model's 150-character limit.
            if len(original_name) > 150:
                suffix = f" [{facility.facility_id}]"
                original_name = (
                    original_name[:150 - len(suffix)] + suffix
                )

            Clinic.objects.create(
                name=original_name,
                registration_code=registration_code,
                address=facility.full_address or "",
                contact_phone=(facility.phone or "")[:15],
                contact_email="",
            )

            created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Sync complete: {created} clinics added, "
                f"{skipped} skipped."
            )
        )
