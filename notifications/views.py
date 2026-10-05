import os

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import ReminderLog


@login_required
def notification_center(request):
    notifications = ReminderLog.objects.filter(
        recipient_user=request.user
    ).order_by('-created_at')

    # Mark unread as read on visit
    unread_qs = notifications.filter(is_read=False)
    unread_qs.update(is_read=True)

    return render(request, 'notifications/notification_list.html', {
        'notifications': notifications
    })


@csrf_exempt
def run_reminders(request):
    """
    Secure endpoint used by GitHub Actions to trigger
    vaccination reminder processing.
    """

    if request.method != 'POST':
        return JsonResponse(
            {'error': 'POST request required'},
            status=405
        )

    expected_secret = os.environ.get('REMINDER_SECRET')
    received_secret = request.headers.get('Authorization', '')

    if not expected_secret:
        return JsonResponse(
            {'error': 'REMINDER_SECRET is not configured'},
            status=500
        )

    if received_secret != f'Bearer {expected_secret}':
        return JsonResponse(
            {'error': 'Unauthorized'},
            status=401
        )

    try:
        from django.core.management import call_command

        call_command('send_vaccination_reminders')

        return JsonResponse({
            'success': True,
            'message': 'Vaccination reminders processed successfully.'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
