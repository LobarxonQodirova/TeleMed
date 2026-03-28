"""Models for the doctors app -- schedules, reviews, and specialization details."""
import uuid

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.accounts.models import DoctorProfile, Specialty


class Specialization(models.Model):
    """Granular sub-specialization within a broader Specialty."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    specialty = models.ForeignKey(
        Specialty, on_delete=models.CASCADE, related_name="sub_specializations"
    )
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        unique_together = ["specialty", "name"]

    def __str__(self):
        return f"{self.name} ({self.specialty.name})"


class DoctorSchedule(models.Model):
    """Weekly recurring schedule slots for a doctor."""

    class DayOfWeek(models.IntegerChoices):
        MONDAY = 0, "Monday"
        TUESDAY = 1, "Tuesday"
        WEDNESDAY = 2, "Wednesday"
        THURSDAY = 3, "Thursday"
        FRIDAY = 4, "Friday"
        SATURDAY = 5, "Saturday"
        SUNDAY = 6, "Sunday"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    doctor = models.ForeignKey(
        DoctorProfile, on_delete=models.CASCADE, related_name="schedules"
    )
    day_of_week = models.IntegerField(choices=DayOfWeek.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    slot_duration_minutes = models.PositiveIntegerField(
        default=30, help_text="Duration of each appointment slot in minutes"
    )
    max_patients = models.PositiveIntegerField(
        default=1, help_text="Max patients per slot"
    )
    is_active = models.BooleanField(default=True)
    break_start = models.TimeField(null=True, blank=True)
    break_end = models.TimeField(null=True, blank=True)
    consultation_types = models.JSONField(
        default=list,
        blank=True,
        help_text='Allowed types: ["video", "audio", "chat"]',
    )
    effective_from = models.DateField(
        null=True, blank=True, help_text="Date this schedule becomes effective"
    )
    effective_until = models.DateField(
        null=True, blank=True, help_text="Date this schedule expires"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["day_of_week", "start_time"]
        unique_together = ["doctor", "day_of_week", "start_time"]

    def __str__(self):
        return (
            f"Dr. {self.doctor.user.get_full_name()} - "
            f"{self.get_day_of_week_display()} {self.start_time}-{self.end_time}"
        )

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.start_time >= self.end_time:
            raise ValidationError("Start time must be before end time.")
        if self.break_start and self.break_end:
            if self.break_start >= self.break_end:
                raise ValidationError("Break start must be before break end.")
            if self.break_start < self.start_time or self.break_end > self.end_time:
                raise ValidationError("Break must be within schedule hours.")

    @property
    def total_slots(self):
        """Calculate total available slots for this schedule block."""
        from datetime import datetime, timedelta

        start = datetime.combine(datetime.today(), self.start_time)
        end = datetime.combine(datetime.today(), self.end_time)
        total_minutes = (end - start).total_seconds() / 60

        if self.break_start and self.break_end:
            break_start = datetime.combine(datetime.today(), self.break_start)
            break_end = datetime.combine(datetime.today(), self.break_end)
            total_minutes -= (break_end - break_start).total_seconds() / 60

        return int(total_minutes / self.slot_duration_minutes)


class DoctorReview(models.Model):
    """Patient review of a doctor after a consultation."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    doctor = models.ForeignKey(
        DoctorProfile, on_delete=models.CASCADE, related_name="reviews"
    )
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="doctor_reviews"
    )
    consultation = models.OneToOneField(
        "consultations.Consultation",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="review",
    )
    overall_rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    punctuality_rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True,
    )
    communication_rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True,
    )
    knowledge_rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=200, blank=True)
    comment = models.TextField(blank=True)
    is_anonymous = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=True)
    doctor_response = models.TextField(blank=True)
    doctor_responded_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ["doctor", "patient", "consultation"]

    def __str__(self):
        return f"Review by {self.patient.get_full_name()} for Dr. {self.doctor.user.get_full_name()} ({self.overall_rating}/5)"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.doctor.update_rating()
