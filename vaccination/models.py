from django.db import models
from django.contrib.auth.models import User
from accounts.models import Clinic
from children.models import Child
import uuid

class DoseStatus(models.TextChoices):
    SCHEDULED = 'SCHEDULED', 'Upcoming / Scheduled'
    DUE_TODAY = 'DUE_TODAY', 'Due Today'
    OVERDUE = 'OVERDUE', 'Overdue'
    COMPLETED = 'COMPLETED', 'Completed'
    PENDING_VERIFICATION = 'PENDING_VERIFICATION', 'Pending Verification'

class Vaccine(models.Model):
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=150)
    target_disease = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.code})"

class ScheduleVersion(models.Model):
    version_name = models.CharField(max_length=100)
    official_source = models.CharField(max_length=255, default='Universal Immunization Programme (UIP), MoHFW, Govt of India')
    effective_date = models.DateField()
    is_current = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.version_name} ({'Current' if self.is_current else 'Archived'})"

class RecommendedDose(models.Model):
    schedule_version = models.ForeignKey(ScheduleVersion, on_delete=models.CASCADE, related_name='recommended_doses')
    vaccine = models.ForeignKey(Vaccine, on_delete=models.CASCADE, related_name='recommended_doses')
    dose_number = models.PositiveIntegerField(default=1)
    dose_label = models.CharField(max_length=100) # e.g. "BCG at Birth", "Pentavalent-1 (6 Weeks)"
    offset_days = models.IntegerField(default=0)  # offset from DOB in days
    offset_months = models.IntegerField(default=0) # offset in calendar months
    min_interval_days = models.IntegerField(default=28)
    mandatory = models.BooleanField(default=True)

    class Meta:
        ordering = ['offset_months', 'offset_days', 'dose_number']
        unique_together = ('schedule_version', 'vaccine', 'dose_number')

    def __str__(self):
        return f"{self.vaccine.code} - {self.dose_label}"

class ScheduledDose(models.Model):
    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name='scheduled_doses')
    recommended_dose = models.ForeignKey(RecommendedDose, on_delete=models.CASCADE, related_name='child_scheduled_doses')
    due_date = models.DateField()
    status = models.CharField(max_length=25, choices=DoseStatus.choices, default=DoseStatus.SCHEDULED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['due_date']
        unique_together = ('child', 'recommended_dose')

    def __str__(self):
        return f"{self.child.full_name} - {self.recommended_dose.dose_label} [{self.status}]"

class VaccineAdministrationRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    scheduled_dose = models.OneToOneField(ScheduledDose, on_delete=models.CASCADE, related_name='administration_record')
    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name='administrations')
    administered_date = models.DateField()
    batch_number = models.CharField(max_length=50)
    facility = models.ForeignKey(Clinic, on_delete=models.PROTECT, related_name='administered_records')
    administered_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='administered_vaccines')
    clinical_notes = models.TextField(blank=True)
    adverse_reaction = models.BooleanField(default=False)
    adverse_reaction_notes = models.TextField(blank=True)
    is_verified = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Adm #{self.id.hex[:8]} - {self.scheduled_dose.recommended_dose.vaccine.name} for {self.child.full_name}"

class AuditLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=100)
    target_child = models.ForeignKey(Child, on_delete=models.SET_NULL, null=True, blank=True)
    details = models.TextField()

    class Meta:
        ordering = ['-timestamp']
