from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Notification


@login_required
def notifications_list(request):
    notifs = Notification.objects.filter(user=request.user)
    notifs.filter(is_read=False).update(is_read=True)
    return render(request, 'notifications/list.html', {'notifications': notifs})


@login_required
def notifications_api(request):
    """AJAX: get unread count and recent notifications"""
    unread = Notification.objects.filter(user=request.user, is_read=False).count()
    recent = list(Notification.objects.filter(user=request.user).values(
        'id', 'title', 'message', 'is_read', 'created_at'
    )[:5])
    # Format datetime
    for n in recent:
        n['created_at'] = n['created_at'].strftime('%d %b %H:%M')
    return JsonResponse({'unread': unread, 'notifications': recent})


@login_required
def mark_read(request, notif_id):
    notif = get_object_or_404(Notification, id=notif_id, user=request.user)
    notif.is_read = True
    notif.save()
    return JsonResponse({'status': 'ok'})
