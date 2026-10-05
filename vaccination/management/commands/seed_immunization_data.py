from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import Clinic, UserProfile, Role
from vaccination.models import Vaccine, ScheduleVersion, RecommendedDose
from datetime import date

class Command(BaseCommand):
    help = 'Seeds verified India Universal Immunization Programme (UIP) reference schedule and standard clinics'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Initializing ImmuTrack National Immunization Schedule Reference Data..."))

        # 1. Standard Clinics
        c1, _ = Clinic.objects.get_or_create(
            registration_code="PHC-DEL-01",
            defaults={
                'name': "Safdarjung Community Primary Health Centre",
                'address': "Ring Road, New Delhi, 110029",
                'contact_phone': "+91-11-26165060",
                'contact_email': "safdarjung.uip@delhi.gov.in"
            }
        )
        c2, _ = Clinic.objects.get_or_create(
            registration_code="CHC-BLR-04",
            defaults={
                'name': "Indiranagar Urban Maternal & Child Health Clinic",
                'address': "100 Feet Road, Indiranagar, Bengaluru, Karnataka 560038",
                'contact_phone': "+91-80-25201144",
                'contact_email': "mch.indiranagar@bbmp.gov.in"
            }
        )

        # 2. National Immunization Schedule Version
        schedule_ver, _ = ScheduleVersion.objects.get_or_create(
            version_name="India National Immunization Schedule (NIS / UIP)",
            defaults={
                'official_source': "Ministry of Health and Family Welfare (MoHFW), Govt of India (UIP Guidelines)",
                'effective_date': date(2023, 1, 1),
                'is_current': True,
                'notes': "Official baseline schedule for infants and children including BCG, OPV, Hep-B, Pentavalent, Rotavirus, PCV, MR, and Vitamin-A."
            }
        )

        # 3. Core UIP Vaccines
        vaccines_data = [
            ("BCG", "Bacillus Calmette-Guérin", "Tuberculosis"),
            ("OPV", "Oral Polio Vaccine", "Poliomyelitis"),
            ("HepB", "Hepatitis B Vaccine", "Hepatitis B Virus"),
            ("Penta", "Pentavalent (DTP+HepB+Hib)", "Diphtheria, Tetanus, Pertussis, Hep-B, Hib"),
            ("Rota", "Rotavirus Vaccine", "Rotavirus Diarrhoea"),
            ("fIPV", "Fractional Inactivated Polio Vaccine", "Poliomyelitis"),
            ("PCV", "Pneumococcal Conjugate Vaccine", "Pneumococcal Pneumonia"),
            ("MR", "Measles & Rubella Vaccine", "Measles and Rubella"),
            ("JE", "Japanese Encephalitis Vaccine", "Japanese Encephalitis"),
            ("DPT_Booster", "DPT Booster Vaccine", "Diphtheria, Pertussis, Tetanus"),
            ("OPV_Booster", "OPV Booster", "Poliomyelitis"),
        ]

        created_vaccines = {}
        for code, name, disease in vaccines_data:
            vac, _ = Vaccine.objects.get_or_create(
                code=code,
                defaults={'name': name, 'target_disease': disease}
            )
            created_vaccines[code] = vac

        # 4. Standard UIP Dosing Timeline Offsets
        # Days / Months calculation as per MoHFW UIP Schedule
        doses_schedule = [
            # At Birth
            ("BCG", 1, "BCG (At Birth)", 0, 0),
            ("OPV", 1, "OPV Zero Dose (At Birth)", 0, 0),
            ("HepB", 1, "Hepatitis B Birth Dose", 0, 0),

            # At 6 Weeks (~1.5 months / 42 days)
            ("OPV", 2, "OPV-1 (6 Weeks)", 42, 0),
            ("Penta", 1, "Pentavalent-1 (6 Weeks)", 42, 0),
            ("Rota", 1, "Rotavirus-1 (6 Weeks)", 42, 0),
            ("fIPV", 1, "fIPV-1 (6 Weeks)", 42, 0),
            ("PCV", 1, "PCV-1 (6 Weeks)", 42, 0),

            # At 10 Weeks (~2.5 months / 70 days)
            ("OPV", 3, "OPV-2 (10 Weeks)", 70, 0),
            ("Penta", 2, "Pentavalent-2 (10 Weeks)", 70, 0),
            ("Rota", 2, "Rotavirus-2 (10 Weeks)", 70, 0),

            # At 14 Weeks (~3.5 months / 98 days)
            ("OPV", 4, "OPV-3 (14 Weeks)", 98, 0),
            ("Penta", 3, "Pentavalent-3 (14 Weeks)", 98, 0),
            ("Rota", 3, "Rotavirus-3 (14 Weeks)", 98, 0),
            ("fIPV", 2, "fIPV-2 (14 Weeks)", 98, 0),
            ("PCV", 2, "PCV-2 (14 Weeks)", 98, 0),

            # At 9-12 Months
            ("MR", 1, "MR-1 (9-12 Months)", 0, 9),
            ("PCV", 3, "PCV Booster (9 Months)", 0, 9),

            # At 16-24 Months
            ("MR", 2, "MR-2 (16-24 Months)", 0, 16),
            ("DPT_Booster", 1, "DPT Booster-1 (16-24 Months)", 0, 16),
            ("OPV_Booster", 1, "OPV Booster (16-24 Months)", 0, 16),
        ]

        for code, dose_no, label, off_days, off_months in doses_schedule:
            RecommendedDose.objects.get_or_create(
                schedule_version=schedule_ver,
                vaccine=created_vaccines[code],
                dose_number=dose_no,
                defaults={
                    'dose_label': label,
                    'offset_days': off_days,
                    'offset_months': off_months
                }
            )

        self.stdout.write(self.style.SUCCESS("Official India UIP reference vaccines and schedules seeded successfully!"))
