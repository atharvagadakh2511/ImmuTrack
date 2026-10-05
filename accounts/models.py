from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Role(models.TextChoices):
    PARENT = 'PARENT', 'Parent / Guardian'
    HEALTH_WORKER = 'HEALTH_WORKER', 'Health Worker'
    ADMIN = 'ADMIN', 'Administrator'

class Clinic(models.Model):
    name = models.CharField(max_length=150, unique=True)
    registration_code = models.CharField(max_length=50, unique=True)
    address = models.TextField()
    contact_phone = models.CharField(max_length=15)
    contact_email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.registration_code})"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.PARENT)
    phone_number = models.CharField(max_length=15, blank=True)
    assigned_clinic = models.ForeignKey(Clinic, on_delete=models.SET_NULL, null=True, blank=True, related_name='staff_members')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"

    @property
    def is_parent(self):
        return self.role == Role.PARENT

    @property
    def is_health_worker(self):
        return self.role == Role.HEALTH_WORKER

    @property
    def is_admin(self):
        return self.role == Role.ADMIN or self.user.is_superuser

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    else:
        if hasattr(instance, 'profile'):
            instance.profile.save()
