from django.contrib import admin
from .models import Facility


@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    list_display = (
        "facility_name",
        "district",
        "city_or_locality",
        "facility_type",
        "ownership",
        "vaccination_service_status",
    )

    list_filter = (
        "district",
        "ownership",
        "facility_type",
    )

    search_fields = (
        "facility_name",
        "district",
        "city_or_locality",
    )

    ordering = ("district", "facility_name")
