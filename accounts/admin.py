from django.contrib import admin
from .models import Clinic, UserProfile


@admin.register(Clinic)
class ClinicAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "registration_code",
        "contact_phone",
        "contact_email",
    )
    search_fields = (
        "name",
        "registration_code",
        "address",
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "role",
        "assigned_clinic",
    )
    list_filter = ("role",)
    search_fields = ("user__username", "phone_number")
