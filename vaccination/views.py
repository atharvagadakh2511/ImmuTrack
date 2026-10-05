from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q
from .models import ScheduledDose, VaccineAdministrationRecord, DoseStatus, AuditLog
from .forms import DoseAdministrationForm
from children.models import Child

@login_required
def worker_dashboard(request):
    user = request.user
    if not (user.profile.is_health_worker or user.profile.is_admin):
        raise PermissionDenied("Health worker access required.")

    clinic = user.profile.assigned_clinic
    query = request.GET.get('q', '').strip()

    children_qs = Child.objects.all()
    if clinic and not user.profile.is_admin:
        children_qs = children_qs.filter(assigned_clinic=clinic)

    if query:
        children_qs = children_qs.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(guardian__username__icontains=query) |
            Q(guardian__email__icontains=query)
        )

    # Overdue list
    overdue_doses = ScheduledDose.objects.filter(status=DoseStatus.OVERDUE)
    if clinic and not user.profile.is_admin:
        overdue_doses = overdue_doses.filter(child__assigned_clinic=clinic)

    # Today's queue
    due_today_doses = ScheduledDose.objects.filter(status=DoseStatus.DUE_TODAY)
    if clinic and not user.profile.is_admin:
        due_today_doses = due_today_doses.filter(child__assigned_clinic=clinic)

    return render(request, 'vaccination/worker_dashboard.html', {
        'clinic': clinic,
        'children': children_qs[:20],
        'overdue_doses': overdue_doses.select_related('child', 'recommended_dose__vaccine')[:15],
        'due_today_doses': due_today_doses.select_related('child', 'recommended_dose__vaccine')[:15],
        'query': query,
    })

@login_required
def record_dose(request, dose_id):
    user = request.user
    if not (user.profile.is_health_worker or user.profile.is_admin):
        raise PermissionDenied("Only authorized health workers or admins can record doses.")

    scheduled_dose = get_object_or_404(ScheduledDose, id=dose_id)

    # Check if already completed
    if hasattr(scheduled_dose, 'administration_record') or scheduled_dose.status == DoseStatus.COMPLETED:
        messages.warning(request, f"This dose ({scheduled_dose.recommended_dose.dose_label}) has already been administered and verified.")
        return redirect('children:child_detail', child_id=scheduled_dose.child.id)

    if request.method == 'POST':
        form = DoseAdministrationForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                admin_record = form.save(commit=False)
                admin_record.scheduled_dose = scheduled_dose
                admin_record.child = scheduled_dose.child
                admin_record.administered_by = user
                admin_record.save()

                scheduled_dose.status = DoseStatus.COMPLETED
                scheduled_dose.save()

                AuditLog.objects.create(
                    user=user,
                    action="DOSE_ADMINISTERED",
                    target_child=scheduled_dose.child,
                    details=f"Administered {scheduled_dose.recommended_dose.dose_label}. Batch: {admin_record.batch_number}, Facility: {admin_record.facility.name}"
                )

                messages.success(request, f"Dose {scheduled_dose.recommended_dose.dose_label} recorded successfully!")
                return redirect('children:child_detail', child_id=scheduled_dose.child.id)
    else:
        # Prepopulate facility if worker is assigned
        initial = {}
        if user.profile.assigned_clinic:
            initial['facility'] = user.profile.assigned_clinic
        form = DoseAdministrationForm(initial=initial)

    return render(request, 'vaccination/record_dose.html', {
        'form': form,
        'scheduled_dose': scheduled_dose,
        'child': scheduled_dose.child,
    })
