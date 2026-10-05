from django.urls import path
from . import views

app_name = 'children'

urlpatterns = [
    path('dashboard/', views.parent_dashboard, name='parent_dashboard'),
    path('add/', views.add_child, name='add_child'),
    path('<uuid:child_id>/', views.child_detail, name='child_detail'),
]
