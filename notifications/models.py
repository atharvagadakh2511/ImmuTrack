from django.db import models
from django.contrib.auth.models import User
from vaccination.models import ScheduledDose

class NotificationChannel(models.TextChoices):
    EMAIL = 'EMAIL', 'Email'
    IN_APP = 'IN_APP', 'In-App Dashboard'
    SMS = 'SMS', 'SMS (Dev Adapter)'

class NotificationStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    SENT = 'SENT', 'Sent'
    FAILED = 'FAILED', 'Failed'

class ReminderLog(models.Model):
    scheduled_dose = models.ForeignKey(ScheduledDose, on_delete=models.CASCADE, related_name='reminders')
    recipient_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vaccine_notifications')
    channel = models.CharField(max_length=20, choices=NotificationChannel.choices, default=NotificationChannel.IN_APP)
    scheduled_for = models.DateField()
    sent_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=NotificationStatus.choices, default=NotificationStatus.PENDING)
    subject = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('scheduled_dose', 'channel', 'scheduled_for')

    def __str__(self):
        return f"[{self.status}] {self.recipient_user.username} - {self.subject}"
