from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from .models import Child
from .forms import ChildRegistrationForm
from vaccination.services import ScheduleEngine
from vaccination.models import ScheduledDose, DoseStatus
from datetime import date

@login_required
def parent_dashboard(request):
    if not request.user.profile.is_parent:
        return redirect('accounts:dashboard_redirect')
        
    children = Child.objects.filter(guardian=request.user).prefetch_related('scheduled_doses')
    
    total_children = children.count()
    total_doses = ScheduledDose.objects.filter(child__guardian=request.user).count()
    completed_doses = ScheduledDose.objects.filter(child__guardian=request.user, status=DoseStatus.COMPLETED).count()
    upcoming_doses = ScheduledDose.objects.filter(
        child__guardian=request.user, 
        status__in=[DoseStatus.SCHEDULED, DoseStatus.DUE_TODAY],
        due_date__gte=date.today()
    ).count()
    overdue_doses = ScheduledDose.objects.filter(child__guardian=request.user, status=DoseStatus.OVERDUE).count()

    context = {
        'children': children,
        'stats': {
            'total_children': total_children,
            'completed_doses': completed_doses,
            'upcoming_doses': upcoming_doses,
            'overdue_doses': overdue_doses,
        }
    }
    return render(request, 'children/parent_dashboard.html', context)

@login_required
def add_child(request):
    if request.method == 'POST':
        form = ChildRegistrationForm(request.POST)
        if form.is_valid():
            child = form.save(commit=False)
            child.guardian = request.user
            child.save()
            # Automatically generate vaccine schedule based on configured NIS
            ScheduleEngine.generate_child_schedule(child)
            messages.success(request, f'Profile for {child.full_name} created and official immunization schedule generated!')
            return redirect('children:child_detail', child_id=child.id)
    else:
        form = ChildRegistrationForm()
    return render(request, 'children/child_form.html', {'form': form, 'title': 'Register New Child'})

@login_required
def child_detail(request, child_id):
    child = get_object_or_404(Child, id=child_id)
    
    # Ownership or staff check
    user = request.user
    if not (user.profile.is_admin or user.profile.is_health_worker or child.guardian == user):
        raise PermissionDenied("You do not have permission to view this child's record.")

    # Refresh statuses if due dates passed
    ScheduleEngine.refresh_child_schedule_statuses(child)
    
    timeline_doses = child.scheduled_doses.select_related('recommended_dose__vaccine', 'administration_record').order_by('due_date')
    completed = timeline_doses.filter(status=DoseStatus.COMPLETED).count()
    total = timeline_doses.count()
    progress_pct = int((completed / total * 100)) if total > 0 else 0

    return render(request, 'children/child_detail.html', {
        'child': child,
        'doses': timeline_doses,
        'progress_pct': progress_pct,
        'completed_count': completed,
        'total_count': total,
    })
