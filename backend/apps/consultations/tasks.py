"""Celery tasks for consultations app."""
import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_consultation_reminder(self, consultation_id):
    """Send reminder email before a scheduled consultation."""
    from .models import Consultation

    try:
        consultation = Consultation.objects.select_related(
            "doctor", "patient"
        ).get(id=consultation_id)
    except Consultation.DoesNotExist:
        logger.warning("Consultation %s not found for reminder.", consultation_id)
        return

    if consultation.status != Consultation.Status.SCHEDULED:
        logger.info(
            "Consultation %s is no longer scheduled; skipping reminder.", consultation_id
        )
        return

    for user in (consultation.doctor, consultation.patient):
        subject = f"TeleMed: Upcoming consultation at {consultation.scheduled_at:%H:%M %Z}"
        message = (
            f"Hello {user.get_full_name()},\n\n"
            f"This is a reminder that you have a consultation scheduled at "
            f"{consultation.scheduled_at:%B %d, %Y %H:%M %Z}.\n\n"
            f"Please log in to TeleMed to join the session.\n\n"
            f"Best regards,\nTeleMed Team"
        )
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            logger.info("Reminder sent to %s for consultation %s", user.email, consultation_id)
        except Exception as exc:
            logger.error("Failed to send reminder to %s: %s", user.email, exc)
            raise self.retry(exc=exc, countdown=60)


@shared_task
def mark_no_show_consultations():
    """Mark consultations as no-show if they weren't started within 30 minutes."""
    from .models import Consultation

    threshold = timezone.now() - timezone.timedelta(minutes=30)
    no_shows = Consultation.objects.filter(
        status=Consultation.Status.SCHEDULED,
        scheduled_at__lt=threshold,
    )
    count = no_shows.update(status=Consultation.Status.NO_SHOW)
    if count:
        logger.info("Marked %d consultations as no-show.", count)


@shared_task
def cleanup_ended_video_sessions():
    """Clean up stale video sessions older than 24 hours."""
    from .models import VideoSession

    threshold = timezone.now() - timezone.timedelta(hours=24)
    stale = VideoSession.objects.filter(
        status=VideoSession.Status.ACTIVE,
        created_at__lt=threshold,
    )
    count = stale.update(status=VideoSession.Status.ENDED, ended_at=timezone.now())
    if count:
        logger.info("Cleaned up %d stale video sessions.", count)
