from .models import Notification


def notifications_processor(request):
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
        recent_notifs = Notification.objects.filter(user=request.user)[:5]
        return {
            'unread_notifications': unread_count,
            'recent_notifications': recent_notifs,
        }
    return {'unread_notifications': 0, 'recent_notifications': []}
