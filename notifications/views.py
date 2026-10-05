from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import ReminderLog

@login_required
def notification_center(request):
    notifications = ReminderLog.objects.filter(recipient_user=request.user).order_by('-created_at')
    # Mark unread as read on visit
    unread_qs = notifications.filter(is_read=False)
    unread_qs.update(is_read=True)

    return render(request, 'notifications/notification_list.html', {
        'notifications': notifications
    })
