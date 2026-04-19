from .models import Notification


def notifications_context(request):
    if not request.user.is_authenticated:
        return {}

    user_notifications = Notification.objects.filter(
        user=request.user
    ).order_by("-created_at")

    unread_count = user_notifications.filter(is_read=False).count()

    return {
        "notifications": user_notifications[:10],
        "unread_notifications": unread_count
    }