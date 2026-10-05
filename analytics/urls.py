from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('defaulter-risk/', views.ml_defaulter_risk_view, name='defaulter_risk'),
    path('certificate/<uuid:child_id>/', views.download_certificate_pdf, name='download_certificate'),
    path('export/csv/', views.export_clinic_report_csv, name='export_clinic_csv'),
]
