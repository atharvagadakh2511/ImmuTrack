from django.urls import path
from . import views

app_name = "facilities"

urlpatterns = [
    path("", views.facility_list, name="facility_list"),
]
