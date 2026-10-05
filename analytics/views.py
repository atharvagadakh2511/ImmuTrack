import csv
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.utils import timezone
from accounts.models import Clinic, UserProfile, Role
from children.models import Child
from vaccination.models import ScheduledDose, DoseStatus, VaccineAdministrationRecord, Vaccine, AuditLog
from .models import ChildRiskAssessment, MLModelMetadata
from .ml.pipeline import DefaulterRiskPipeline
from .pdf_generator import generate_vaccination_certificate_pdf

@login_required
def admin_dashboard(request):
    if not request.user.profile.is_admin:
        raise PermissionDenied("Administrator privilege required.")

    total_children = Child.objects.count()
    total_completed = ScheduledDose.objects.filter(status=DoseStatus.COMPLETED).count()
    total_overdue = ScheduledDose.objects.filter(status=DoseStatus.OVERDUE).count()
    total_scheduled = ScheduledDose.objects.filter(status=DoseStatus.SCHEDULED).count()

    # Clinic Coverage Breakdown
    clinics = Clinic.objects.annotate(
        child_count=Count('registered_children', distinct=True),
        completed_doses=Count('registered_children__scheduled_doses', filter=Q(registered_children__scheduled_doses__status=DoseStatus.COMPLETED), distinct=True),
        overdue_doses=Count('registered_children__scheduled_doses', filter=Q(registered_children__scheduled_doses__status=DoseStatus.OVERDUE), distinct=True)
    )

    # Vaccine Distribution Breakdown for Chart.js
    vaccines = Vaccine.objects.annotate(
        admin_count=Count('recommended_doses__child_scheduled_doses__administration_record')
    ).values('code', 'admin_count')

    chart_labels = [v['code'] for v in vaccines]
    chart_data = [v['admin_count'] for v in vaccines]

    # Recent High Risk Assessments
    high_risks = ChildRiskAssessment.objects.filter(risk_level='HIGH').select_related('child__guardian')[:10]

    return render(request, 'analytics/admin_dashboard.html', {
        'total_children': total_children,
        'total_completed': total_completed,
        'total_overdue': total_overdue,
        'total_scheduled': total_scheduled,
        'clinics': clinics,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'high_risks': high_risks,
    })

@login_required
def ml_defaulter_risk_view(request):
    if not (request.user.profile.is_admin or request.user.profile.is_health_worker):
        raise PermissionDenied("Access denied.")

    # Trigger training if requested
    if request.method == 'POST' and 'retrain_model' in request.POST:
        metrics = DefaulterRiskPipeline.train_and_persist()
        meta = MLModelMetadata.objects.create(
            model_name="RandomForest Adherence Risk Classifier",
            version="1.2.0",
            accuracy=metrics['accuracy'],
            precision=metrics['precision'],
            recall=metrics['recall'],
            f1_score=metrics['f1_score'],
            features_used=", ".join(metrics['features'])
        )
        
        # Batch predict for all active children
        for c in Child.objects.all():
            res = DefaulterRiskPipeline.predict_risk(c)
            ChildRiskAssessment.objects.update_or_create(
                child=c,
                defaults={
                    'model_version': meta,
                    'risk_level': res['level'],
                    'probability': res['probability'],
                    'top_risk_factor': res['factor']
                }
            )

    assessments = ChildRiskAssessment.objects.select_related('child__assigned_clinic', 'child__guardian').order_by('-probability')
    active_model = MLModelMetadata.objects.order_by('-trained_at').first()

    return render(request, 'analytics/defaulter_risk_dashboard.html', {
        'assessments': assessments,
        'active_model': active_model
    })

@login_required
def download_certificate_pdf(request, child_id):
    child = get_object_or_404(Child, id=child_id)
    user = request.user
    
    # Ownership or staff check
    if not (user.profile.is_admin or user.profile.is_health_worker or child.guardian == user):
        raise PermissionDenied("You do not have access to this certificate.")

    pdf_bytes = generate_vaccination_certificate_pdf(child)
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="ImmuTrack_Cert_{child.first_name}_{child.id.hex[:6]}.pdf"'
    return response

@login_required
def export_clinic_report_csv(request):
    if not (request.user.profile.is_admin or request.user.profile.is_health_worker):
        raise PermissionDenied("Access restricted.")

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="ImmuTrack_Clinic_Report_{timezone.now().strftime("%Y%m%d")}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Child ID', 'Child Name', 'DOB', 'Guardian', 'Phone', 'Vaccine', 'Dose Label', 'Due Date', 'Status', 'Administered Date', 'Facility', 'Batch'])

    doses = ScheduledDose.objects.select_related('child__guardian', 'recommended_dose__vaccine', 'administration_record__facility').all()
    for d in doses:
        has_adm = hasattr(d, 'administration_record')
        writer.writerow([
            str(d.child.id)[:8],
            d.child.full_name,
            d.child.date_of_birth,
            d.child.guardian.username,
            d.child.guardian.profile.phone_number,
            d.recommended_dose.vaccine.name,
            d.recommended_dose.dose_label,
            d.due_date,
            d.status,
            d.administration_record.administered_date if has_adm else 'N/A',
            d.administration_record.facility.name if has_adm else 'N/A',
            d.administration_record.batch_number if has_adm else 'N/A',
        ])

    return response
