"""Celery tasks for the notifications app."""
import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_email_notification(self, notification_id):
    """Send a notification via email."""
    from .models import Notification

    try:
        notification = Notification.objects.select_related("recipient").get(
            id=notification_id
        )
    except Notification.DoesNotExist:
        logger.warning("Notification %s not found.", notification_id)
        return

    if notification.is_sent:
        logger.info("Notification %s already sent.", notification_id)
        return

    try:
        send_mail(
            subject=notification.title,
            message=notification.message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[notification.recipient.email],
            fail_silently=False,
        )
        from django.utils import timezone
        notification.is_sent = True
        notification.sent_at = timezone.now()
        notification.save(update_fields=["is_sent", "sent_at"])
        logger.info("Email notification sent to %s", notification.recipient.email)
    except Exception as exc:
        logger.error("Failed to send email notification %s: %s", notification_id, exc)
        raise self.retry(exc=exc, countdown=60)


@shared_task
def send_bulk_notifications(notification_type, title, message, user_ids=None):
    """Send notifications to multiple users."""
    from django.contrib.auth import get_user_model
    from .models import Notification
    from .services import NotificationService

    User = get_user_model()
    if user_ids:
        users = User.objects.filter(id__in=user_ids)
    else:
        users = User.objects.filter(is_active=True)

    service = NotificationService()
    count = 0
    for user in users:
        service.create_notification(
            recipient=user,
            notification_type=notification_type,
            title=title,
            message=message,
        )
        count += 1

    logger.info("Sent %d bulk notifications of type %s.", count, notification_type)


@shared_task
def cleanup_old_notifications(days=90):
    """Delete read notifications older than N days."""
    from datetime import timedelta
    from django.utils import timezone
    from .models import Notification

    threshold = timezone.now() - timedelta(days=days)
    deleted_count, _ = Notification.objects.filter(
        is_read=True,
        created_at__lt=threshold,
    ).delete()

    if deleted_count:
        logger.info("Cleaned up %d old notifications.", deleted_count)


@shared_task
def send_unread_digest():
    """Send a daily digest email of unread notifications to each user."""
    from django.contrib.auth import get_user_model
    from .models import Notification

    User = get_user_model()
    users_with_unread = (
        Notification.objects
        .filter(is_read=False, channel="in_app")
        .values_list("recipient_id", flat=True)
        .distinct()
    )

    for user_id in users_with_unread:
        try:
            user = User.objects.get(id=user_id)
            unread = Notification.objects.filter(
                recipient=user, is_read=False, channel="in_app"
            ).order_by("-created_at")[:10]

            if not unread:
                continue

            items = "\n".join(
                f"- {n.title}: {n.message[:100]}" for n in unread
            )
            body = (
                f"Hello {user.get_full_name()},\n\n"
                f"You have {unread.count()} unread notifications:\n\n"
                f"{items}\n\n"
                f"Log in to TeleMed to view all notifications.\n\n"
                f"Best regards,\nTeleMed Team"
            )
            send_mail(
                subject=f"TeleMed: You have {unread.count()} unread notifications",
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )
        except User.DoesNotExist:
            continue

    logger.info("Sent unread notification digests.")
