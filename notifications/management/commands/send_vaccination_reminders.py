from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from vaccination.models import ScheduledDose, DoseStatus
from notifications.models import ReminderLog, NotificationChannel, NotificationStatus
from datetime import date, timedelta

class Command(BaseCommand):
    help = 'Processes upcoming and overdue vaccination reminders safely without duplicates.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Preview reminders without sending or logging records')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        today = date.today()
        upcoming_window = today + timedelta(days=3)

        self.stdout.write(self.style.NOTICE(f"--- Running ImmuTrack Reminder Engine ({today}) [Dry-run: {dry_run}] ---"))

        # 1. Upcoming Reminders (3 days prior or due today)
        upcoming_doses = ScheduledDose.objects.filter(
            status__in=[DoseStatus.SCHEDULED, DoseStatus.DUE_TODAY],
            due_date__lte=upcoming_window,
            due_date__gte=today
        ).select_related('child__guardian', 'recommended_dose__vaccine')

        sent_count = 0

        for dose in upcoming_doses:
            guardian = dose.child.guardian
            subject = f"Upcoming Vaccination Reminder: {dose.child.first_name}'s {dose.recommended_dose.vaccine.name}"
            msg = (
                f"Dear {guardian.first_name or guardian.username},\n\n"
                f"This is a reminder that {dose.child.full_name} is scheduled to receive the following dose:\n"
                f"- Vaccine: {dose.recommended_dose.vaccine.name} ({dose.recommended_dose.dose_label})\n"
                f"- Due Date: {dose.due_date}\n\n"
                f"Please visit your registered clinic ({dose.child.assigned_clinic.name if dose.child.assigned_clinic else 'Designated Health Center'}).\n\n"
                f"- ImmuTrack Automated Health System"
            )

            # Check if reminder already logged for this date
            exists = ReminderLog.objects.filter(
                scheduled_dose=dose,
                channel=NotificationChannel.EMAIL,
                scheduled_for=today
            ).exists()

            if not exists:
                if dry_run:
                    self.stdout.write(f"[Dry-Run] Would send UPCOMING to {guardian.email} for {dose.child.first_name}")
                else:
                    try:
                        if guardian.email:
                            send_mail(
                                subject=subject,
                                message=msg,
                                from_email=settings.DEFAULT_FROM_EMAIL,
                                recipient_list=[guardian.email],
                                fail_silently=False
                            )
                        # Record In-app and Email
                        ReminderLog.objects.create(
                            scheduled_dose=dose,
                            recipient_user=guardian,
                            channel=NotificationChannel.EMAIL,
                            scheduled_for=today,
                            sent_at=timezone.now(),
                            status=NotificationStatus.SENT,
                            subject=subject,
                            message=msg
                        )
                        ReminderLog.objects.create(
                            scheduled_dose=dose,
                            recipient_user=guardian,
                            channel=NotificationChannel.IN_APP,
                            scheduled_for=today,
                            sent_at=timezone.now(),
                            status=NotificationStatus.SENT,
                            subject=subject,
                            message=msg
                        )
                        sent_count += 1
                    except Exception as e:
                        ReminderLog.objects.create(
                            scheduled_dose=dose,
                            recipient_user=guardian,
                            channel=NotificationChannel.EMAIL,
                            scheduled_for=today,
                            status=NotificationStatus.FAILED,
                            subject=subject,
                            message=msg,
                            error_message=str(e)
                        )
                        self.stderr.write(f"Failed sending to {guardian.email}: {e}")

        # 2. Overdue Reminders
        overdue_doses = ScheduledDose.objects.filter(
            status=DoseStatus.OVERDUE,
            due_date__lt=today
        ).select_related('child__guardian', 'recommended_dose__vaccine')

        for dose in overdue_doses:
            guardian = dose.child.guardian
            subject = f"ACTION REQUIRED: Overdue Dose for {dose.child.first_name}"
            msg = (
                f"Attention {guardian.first_name or guardian.username},\n\n"
                f"Our records show that {dose.child.full_name} is overdue for the following dose:\n"
                f"- Vaccine: {dose.recommended_dose.vaccine.name} ({dose.recommended_dose.dose_label})\n"
                f"- Originally Due: {dose.due_date}\n\n"
                f"Please prioritize visiting your health facility promptly.\n\n"
                f"- ImmuTrack Health Support"
            )

            exists = ReminderLog.objects.filter(
                scheduled_dose=dose,
                channel=NotificationChannel.EMAIL,
                scheduled_for=today
            ).exists()

            if not exists:
                if dry_run:
                    self.stdout.write(f"[Dry-Run] Would send OVERDUE to {guardian.email} for {dose.child.first_name}")
                else:
                    try:
                        if guardian.email:
                            send_mail(
                                subject=subject,
                                message=msg,
                                from_email=settings.DEFAULT_FROM_EMAIL,
                                recipient_list=[guardian.email],
                                fail_silently=False
                            )
                        ReminderLog.objects.create(
                            scheduled_dose=dose,
                            recipient_user=guardian,
                            channel=NotificationChannel.EMAIL,
                            scheduled_for=today,
                            sent_at=timezone.now(),
                            status=NotificationStatus.SENT,
                            subject=subject,
                            message=msg
                        )
                        ReminderLog.objects.create(
                            scheduled_dose=dose,
                            recipient_user=guardian,
                            channel=NotificationChannel.IN_APP,
                            scheduled_for=today,
                            sent_at=timezone.now(),
                            status=NotificationStatus.SENT,
                            subject=subject,
                            message=msg
                        )
                        sent_count += 1
                    except Exception as e:
                        self.stderr.write(f"Failed sending overdue to {guardian.email}: {e}")

        self.stdout.write(self.style.SUCCESS(f"Reminder process finished. Total notifications issued: {sent_count}"))
