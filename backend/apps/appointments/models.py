"""Models for the appointments app."""
import uuid

from django.conf import settings
from django.db import models


class TimeSlot(models.Model):
    """A bookable time slot for a doctor on a specific date."""

    class SlotStatus(models.TextChoices):
        AVAILABLE = "available", "Available"
        BOOKED = "booked", "Booked"
        BLOCKED = "blocked", "Blocked"
        BREAK = "break", "Break"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="time_slots",
    )
    schedule = models.ForeignKey(
        "doctors.DoctorSchedule",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="generated_slots",
    )
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(
        max_length=10, choices=SlotStatus.choices, default=SlotStatus.AVAILABLE
    )
    max_bookings = models.PositiveIntegerField(default=1)
    current_bookings = models.PositiveIntegerField(default=0)
    consultation_types = models.JSONField(
        default=list, blank=True,
        help_text='Allowed types: ["video", "audio", "chat"]',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["date", "start_time"]
        unique_together = ["doctor", "date", "start_time"]
        indexes = [
            models.Index(fields=["doctor", "date", "status"]),
        ]

    def __str__(self):
        return f"{self.doctor.get_full_name()} - {self.date} {self.start_time}-{self.end_time}"

    @property
    def is_bookable(self):
        return (
            self.status == self.SlotStatus.AVAILABLE
            and self.current_bookings < self.max_bookings
        )


class Appointment(models.Model):
    """Appointment booking between a patient and a doctor."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        CHECKED_IN = "checked_in", "Checked In"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"
        NO_SHOW = "no_show", "No Show"
        RESCHEDULED = "rescheduled", "Rescheduled"

    class AppointmentType(models.TextChoices):
        INITIAL = "initial", "Initial Consultation"
        FOLLOW_UP = "follow_up", "Follow-Up"
        URGENT = "urgent", "Urgent"
        ROUTINE = "routine", "Routine"
        SECOND_OPINION = "second_opinion", "Second Opinion"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="appointments",
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="doctor_appointments",
    )
    time_slot = models.ForeignKey(
        TimeSlot,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="appointments",
    )
    appointment_type = models.CharField(
        max_length=20, choices=AppointmentType.choices, default=AppointmentType.INITIAL
    )
    consultation_mode = models.CharField(
        max_length=10,
        choices=[("video", "Video"), ("audio", "Audio"), ("chat", "Chat")],
        default="video",
    )
    status = models.CharField(
        max_length=15, choices=Status.choices, default=Status.PENDING
    )
    scheduled_date = models.DateField()
    scheduled_time = models.TimeField()
    duration_minutes = models.PositiveIntegerField(default=30)
    reason = models.TextField(blank=True, help_text="Reason for the appointment")
    symptoms = models.JSONField(
        default=list, blank=True, help_text="List of symptoms"
    )
    notes = models.TextField(blank=True, help_text="Additional notes from patient")
    doctor_notes = models.TextField(blank=True, help_text="Pre-appointment notes from doctor")
    is_first_visit = models.BooleanField(default=True)
    reminder_sent = models.BooleanField(default=False)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    checked_in_at = models.DateTimeField(null=True, blank=True)
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-scheduled_date", "-scheduled_time"]
        indexes = [
            models.Index(fields=["patient", "status"]),
            models.Index(fields=["doctor", "status"]),
            models.Index(fields=["scheduled_date", "scheduled_time"]),
        ]

    def __str__(self):
        return (
            f"Appointment {self.id} - "
            f"{self.patient.get_full_name()} with Dr. {self.doctor.get_full_name()} "
            f"on {self.scheduled_date} at {self.scheduled_time}"
        )

    @property
    def scheduled_datetime(self):
        from datetime import datetime
        return datetime.combine(self.scheduled_date, self.scheduled_time)


class Cancellation(models.Model):
    """Tracks appointment cancellation details."""

    class CancelledBy(models.TextChoices):
        PATIENT = "patient", "Patient"
        DOCTOR = "doctor", "Doctor"
        SYSTEM = "system", "System"

    class Reason(models.TextChoices):
        PERSONAL = "personal", "Personal Reasons"
        EMERGENCY = "emergency", "Emergency"
        SCHEDULING = "scheduling", "Scheduling Conflict"
        FEELING_BETTER = "feeling_better", "Feeling Better"
        TECHNICAL = "technical", "Technical Issues"
        OTHER = "other", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    appointment = models.OneToOneField(
        Appointment, on_delete=models.CASCADE, related_name="cancellation"
    )
    cancelled_by = models.CharField(max_length=10, choices=CancelledBy.choices)
    cancelled_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="cancellations_made",
    )
    reason = models.CharField(max_length=20, choices=Reason.choices, default=Reason.OTHER)
    reason_detail = models.TextField(blank=True)
    refund_requested = models.BooleanField(default=False)
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_late_cancellation = models.BooleanField(
        default=False, help_text="Cancelled less than 24 hours before appointment"
    )
    cancelled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-cancelled_at"]

    def __str__(self):
        return f"Cancellation of {self.appointment} by {self.cancelled_by}"

    def save(self, *args, **kwargs):
        from datetime import datetime, timedelta
        from django.utils import timezone

        appt_dt = datetime.combine(
            self.appointment.scheduled_date,
            self.appointment.scheduled_time,
        )
        appt_dt = timezone.make_aware(appt_dt)
        if (appt_dt - timezone.now()) < timedelta(hours=24):
            self.is_late_cancellation = True
        super().save(*args, **kwargs)
