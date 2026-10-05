from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.notification_center, name='notification_center'),
    path(
        'run-reminders/',
        views.run_reminders,
        name='run_reminders'
    ),
]
