
from django.db import models


class Facility(models.Model):

    facility_id = models.CharField(
        max_length=20,
        unique=True
    )

    district = models.CharField(max_length=100)

    city_or_locality = models.CharField(max_length=150)

    facility_name = models.CharField(max_length=255)

    facility_type = models.CharField(max_length=100)

    ownership = models.CharField(
        max_length=50,
        choices=[
            ("Government", "Government"),
            ("Private", "Private"),
        ]
    )

    vaccination_service_status = models.CharField(
        max_length=100,
        default="Not verified - contact facility"
    )

    phone = models.CharField(
        max_length=30,
        blank=True
    )

    full_address = models.TextField(blank=True)

    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True
    )

    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True
    )

    source_url = models.URLField(blank=True)

    data_note = models.TextField(blank=True)

    def __str__(self):
        return f"{self.facility_name} - {self.district}"

    class Meta:
        ordering = ["district", "facility_name"]
        verbose_name = "Hospital / Vaccination Centre"
        verbose_name_plural = "Hospitals / Vaccination Centres"
