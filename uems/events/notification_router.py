from .models import Notification


def send_notification(user, event=None, ntype="general", message=""):
    return Notification.objects.create(
        user=user,
        event=event,
        notification_type=ntype,
        message=message
    )