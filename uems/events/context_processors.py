from .models import Notification


def notifications_context(request):
    if not request.user.is_authenticated:
        return {}

    user_notifications = Notification.objects.filter(
        user=request.user
    ).order_by("-created_at")

    return {
        "notifications": user_notifications[:10],
        "unread_notifications": user_notifications.filter(is_read=False).count()
    }