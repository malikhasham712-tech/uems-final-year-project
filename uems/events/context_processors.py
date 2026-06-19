from .models import EventMessage, Notification


def notifications_context(request):
    if not request.user.is_authenticated:
        return {}

    notifications = Notification.objects.filter(
        user=request.user
    ).order_by("-created_at")

    unread_count = notifications.filter(is_read=False).count()
    unread_event_messages = EventMessage.objects.filter(
        recipient=request.user,
        is_read=False
    ).count()

    return {
        "notifications": notifications[:10],
        "unread_notifications": unread_count,
        "unread_event_messages": unread_event_messages
    }
