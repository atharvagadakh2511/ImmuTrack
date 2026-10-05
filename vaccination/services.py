from datetime import date
from dateutil.relativedelta import relativedelta
from .models import ScheduleVersion, RecommendedDose, ScheduledDose, DoseStatus, AuditLog

class ScheduleEngine:
    @staticmethod
    def calculate_due_date(dob: date, offset_days: int, offset_months: int) -> date:
        calculated = dob
        if offset_months > 0:
            calculated = calculated + relativedelta(months=offset_months)
        if offset_days > 0:
            calculated = calculated + relativedelta(days=offset_days)
        return calculated

    @classmethod
    def generate_child_schedule(cls, child):
        current_version = ScheduleVersion.objects.filter(is_current=True).first()
        if not current_version:
            return []
            
        recommended_doses = RecommendedDose.objects.filter(schedule_version=current_version)
        created_doses = []
        today = date.today()

        for rec in recommended_doses:
            due_date = cls.calculate_due_date(child.date_of_birth, rec.offset_days, rec.offset_months)
            status = DoseStatus.SCHEDULED
            if due_date < today:
                status = DoseStatus.OVERDUE
            elif due_date == today:
                status = DoseStatus.DUE_TODAY

            sch_dose, created = ScheduledDose.objects.get_or_create(
                child=child,
                recommended_dose=rec,
                defaults={'due_date': due_date, 'status': status}
            )
            created_doses.append(sch_dose)
        return created_doses

    @classmethod
    def refresh_child_schedule_statuses(cls, child):
        today = date.today()
        doses = child.scheduled_doses.exclude(status=DoseStatus.COMPLETED)
        for d in doses:
            if d.due_date < today and d.status != DoseStatus.OVERDUE:
                d.status = DoseStatus.OVERDUE
                d.save(update_fields=['status', 'updated_at'])
            elif d.due_date == today and d.status != DoseStatus.DUE_TODAY:
                d.status = DoseStatus.DUE_TODAY
                d.save(update_fields=['status', 'updated_at'])
