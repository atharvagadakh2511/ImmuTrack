from django.db import models
from django.contrib.auth.models import User
from accounts.models import Clinic
import uuid

class Gender(models.TextChoices):
    MALE = 'M', 'Male'
    FEMALE = 'F', 'Female'
    OTHER = 'O', 'Other'

class Relationship(models.TextChoices):
    MOTHER = 'MOTHER', 'Mother'
    FATHER = 'FATHER', 'Father'
    GUARDIAN = 'GUARDIAN', 'Legal Guardian'

class Child(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    guardian = models.ForeignKey(User, on_delete=models.CASCADE, related_name='children')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=Gender.choices)
    blood_group = models.CharField(max_length=5, blank=True, null=True)
    guardian_relationship = models.CharField(max_length=20, choices=Relationship.choices, default=Relationship.MOTHER)
    assigned_clinic = models.ForeignKey(Clinic, on_delete=models.SET_NULL, null=True, related_name='registered_children')
    allergies = models.TextField(blank=True, default='None known')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.date_of_birth})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
