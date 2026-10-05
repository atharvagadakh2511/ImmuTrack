from django.urls import path
from . import views

app_name = 'vaccination'

urlpatterns = [
    path('dashboard/', views.worker_dashboard, name='worker_dashboard'),
    path('record/<int:dose_id>/', views.record_dose, name='record_dose'),
]
