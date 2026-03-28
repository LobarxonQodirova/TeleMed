"""Models for the notifications app."""
import uuid

from django.conf import settings
from django.db import models


class Notification(models.Model):
    """User notification record."""

    class NotificationType(models.TextChoices):
        APPOINTMENT_REMINDER = "appointment_reminder", "Appointment Reminder"
        APPOINTMENT_CONFIRMED = "appointment_confirmed", "Appointment Confirmed"
        APPOINTMENT_CANCELLED = "appointment_cancelled", "Appointment Cancelled"
        CONSULTATION_STARTED = "consultation_started", "Consultation Started"
        CONSULTATION_ENDED = "consultation_ended", "Consultation Ended"
        PRESCRIPTION_READY = "prescription_ready", "Prescription Ready"
        REFILL_APPROVED = "refill_approved", "Refill Approved"
        REFILL_DENIED = "refill_denied", "Refill Denied"
        LAB_RESULTS = "lab_results", "Lab Results Available"
        PAYMENT_RECEIVED = "payment_received", "Payment Received"
        PAYMENT_FAILED = "payment_failed", "Payment Failed"
        DELIVERY_UPDATE = "delivery_update", "Delivery Update"
        NEW_REVIEW = "new_review", "New Review"
        GENERAL = "general", "General"

    class Channel(models.TextChoices):
        IN_APP = "in_app", "In-App"
        EMAIL = "email", "Email"
        SMS = "sms", "SMS"
        PUSH = "push", "Push Notification"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    notification_type = models.CharField(
        max_length=30, choices=NotificationType.choices, default=NotificationType.GENERAL
    )
    channel = models.CharField(
        max_length=10, choices=Channel.choices, default=Channel.IN_APP
    )
    title = models.CharField(max_length=300)
    message = models.TextField()
    data = models.JSONField(
        default=dict, blank=True,
        help_text="Additional data payload (e.g., appointment_id, link)",
    )
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "is_read"]),
            models.Index(fields=["notification_type"]),
        ]

    def __str__(self):
        return f"{self.title} -> {self.recipient.get_full_name()}"

    def mark_read(self):
        from django.utils import timezone
        self.is_read = True
        self.read_at = timezone.now()
        self.save(update_fields=["is_read", "read_at"])
