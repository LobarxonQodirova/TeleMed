"""Celery tasks for the appointments app."""
import logging
from datetime import date, datetime, timedelta

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_appointment_reminder(self, appointment_id):
    """Send reminder email/notification before an appointment."""
    from .models import Appointment

    try:
        appointment = Appointment.objects.select_related(
            "doctor", "patient"
        ).get(id=appointment_id)
    except Appointment.DoesNotExist:
        logger.warning("Appointment %s not found for reminder.", appointment_id)
        return

    if appointment.status not in ("pending", "confirmed"):
        logger.info("Appointment %s is %s; skipping reminder.", appointment_id, appointment.status)
        return

    if appointment.reminder_sent:
        logger.info("Reminder already sent for appointment %s.", appointment_id)
        return

    for user in (appointment.doctor, appointment.patient):
        role = "Doctor" if user == appointment.doctor else "Patient"
        subject = f"TeleMed: Appointment Reminder - {appointment.scheduled_date}"
        message = (
            f"Hello {user.get_full_name()},\n\n"
            f"This is a reminder about your upcoming appointment:\n\n"
            f"Date: {appointment.scheduled_date}\n"
            f"Time: {appointment.scheduled_time}\n"
            f"Type: {appointment.get_appointment_type_display()}\n"
            f"Mode: {appointment.get_consultation_mode_display()}\n\n"
            f"Please log in to TeleMed to join your session.\n\n"
            f"Best regards,\nTeleMed Team"
        )
        try:
            send_mail(
                subject, message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            logger.info("Reminder sent to %s (%s) for appointment %s", user.email, role, appointment_id)
        except Exception as exc:
            logger.error("Failed to send reminder to %s: %s", user.email, exc)
            raise self.retry(exc=exc, countdown=60)

    appointment.reminder_sent = True
    appointment.save(update_fields=["reminder_sent"])


@shared_task
def send_upcoming_reminders():
    """Batch task: send reminders for appointments happening in the next hour."""
    from .models import Appointment

    now = timezone.now()
    one_hour_later = now + timedelta(hours=1)

    upcoming = Appointment.objects.filter(
        status__in=["pending", "confirmed"],
        reminder_sent=False,
        scheduled_date=now.date(),
    )

    count = 0
    for appointment in upcoming:
        appt_dt = datetime.combine(appointment.scheduled_date, appointment.scheduled_time)
        appt_dt = timezone.make_aware(appt_dt)
        if now <= appt_dt <= one_hour_later:
            send_appointment_reminder.delay(str(appointment.id))
            count += 1

    if count:
        logger.info("Queued %d appointment reminders.", count)


@shared_task
def mark_no_show_appointments():
    """Mark appointments as no-show if they were not checked in within 30 minutes."""
    from .models import Appointment

    now = timezone.now()
    threshold_date = now.date()
    threshold_time = (now - timedelta(minutes=30)).time()

    no_shows = Appointment.objects.filter(
        status__in=["pending", "confirmed"],
        scheduled_date__lte=threshold_date,
        scheduled_time__lte=threshold_time,
    )
    count = no_shows.update(status="no_show")
    if count:
        logger.info("Marked %d appointments as no-show.", count)


@shared_task
def generate_daily_slots():
    """Generate time slots for 7 days out from today for all active doctors."""
    from apps.doctors.models import DoctorSchedule
    from .models import TimeSlot

    target_date = date.today() + timedelta(days=7)
    schedules = DoctorSchedule.objects.filter(
        is_active=True,
        day_of_week=target_date.weekday(),
    ).select_related("doctor__user")

    created_count = 0
    for schedule in schedules:
        current_time = datetime.combine(target_date, schedule.start_time)
        end_time = datetime.combine(target_date, schedule.end_time)
        delta = timedelta(minutes=schedule.slot_duration_minutes)

        while current_time + delta <= end_time:
            if schedule.break_start and schedule.break_end:
                break_s = datetime.combine(target_date, schedule.break_start)
                break_e = datetime.combine(target_date, schedule.break_end)
                if break_s <= current_time < break_e:
                    current_time = break_e
                    continue

            _, created = TimeSlot.objects.get_or_create(
                doctor=schedule.doctor.user,
                date=target_date,
                start_time=current_time.time(),
                defaults={
                    "end_time": (current_time + delta).time(),
                    "schedule": schedule,
                    "max_bookings": schedule.max_patients,
                    "consultation_types": schedule.consultation_types,
                },
            )
            if created:
                created_count += 1
            current_time += delta

    logger.info("Generated %d time slots for %s.", created_count, target_date)
