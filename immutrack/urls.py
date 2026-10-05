from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='landing.html'), name='home'),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('children/', include('children.urls', namespace='children')),
    path('vaccination/', include('vaccination.urls', namespace='vaccination')),
    path('notifications/', include('notifications.urls', namespace='notifications')),
    path('analytics/', include('analytics.urls', namespace='analytics')),
]
