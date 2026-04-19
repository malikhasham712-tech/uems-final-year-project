from .models import Notification


def send_notification(user, event=None, ntype="general", message=""):
    """
    Safe notification sender (production-ready)
    """

    # Prevent empty useless notifications
    if not user or not message:
        return None

    return Notification.objects.create(
        user=user,
        event=event if event else None,
        notification_type=ntype,
        message=message
    )