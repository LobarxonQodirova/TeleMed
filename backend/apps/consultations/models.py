"""Models for consultations, notes, video sessions, and files."""
import uuid

from django.conf import settings
from django.db import models


class Consultation(models.Model):
    """A telemedicine consultation between doctor and patient."""

    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        WAITING = "waiting", "In Waiting Room"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"
        NO_SHOW = "no_show", "No Show"

    class ConsultationType(models.TextChoices):
        VIDEO = "video", "Video Call"
        AUDIO = "audio", "Audio Call"
        CHAT = "chat", "Chat"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    appointment = models.OneToOneField(
        "appointments.Appointment",
        on_delete=models.CASCADE,
        related_name="consultation",
        null=True,
        blank=True,
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="doctor_consultations",
    )
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="patient_consultations",
    )
    consultation_type = models.CharField(
        max_length=10, choices=ConsultationType.choices, default=ConsultationType.VIDEO
    )
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.SCHEDULED)
    chief_complaint = models.TextField(blank=True)
    diagnosis = models.TextField(blank=True)
    treatment_plan = models.TextField(blank=True)
    follow_up_required = models.BooleanField(default=False)
    follow_up_date = models.DateField(null=True, blank=True)
    scheduled_at = models.DateTimeField()
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    queue_position = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-scheduled_at"]
        indexes = [
            models.Index(fields=["doctor", "status"]),
            models.Index(fields=["patient", "status"]),
            models.Index(fields=["scheduled_at"]),
        ]

    def __str__(self):
        return (
            f"Consultation {self.id} - "
            f"Dr. {self.doctor.get_full_name()} & {self.patient.get_full_name()}"
        )

    @property
    def actual_duration(self):
        if self.started_at and self.ended_at:
            delta = self.ended_at - self.started_at
            return int(delta.total_seconds() / 60)
        return None


class ConsultationNote(models.Model):
    """Clinical notes attached to a consultation."""

    class NoteType(models.TextChoices):
        SOAP = "soap", "SOAP Note"
        PROGRESS = "progress", "Progress Note"
        GENERAL = "general", "General Note"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    consultation = models.ForeignKey(
        Consultation, on_delete=models.CASCADE, related_name="notes"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="authored_notes"
    )
    note_type = models.CharField(
        max_length=10, choices=NoteType.choices, default=NoteType.GENERAL
    )
    subjective = models.TextField(blank=True, help_text="Patient's reported symptoms")
    objective = models.TextField(blank=True, help_text="Clinical observations")
    assessment = models.TextField(blank=True, help_text="Clinical assessment")
    plan = models.TextField(blank=True, help_text="Treatment plan")
    content = models.TextField(blank=True, help_text="Free-form note content")
    is_private = models.BooleanField(
        default=False, help_text="Private notes visible only to the doctor"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Note for {self.consultation_id} by {self.author.get_full_name()}"


class VideoSession(models.Model):
    """Tracks a video session for a consultation."""

    class Status(models.TextChoices):
        CREATED = "created", "Created"
        ACTIVE = "active", "Active"
        ENDED = "ended", "Ended"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    consultation = models.ForeignKey(
        Consultation, on_delete=models.CASCADE, related_name="video_sessions"
    )
    session_token = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.CREATED)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    doctor_joined_at = models.DateTimeField(null=True, blank=True)
    patient_joined_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Video session {self.session_token} ({self.status})"


class ConsultationFile(models.Model):
    """Files exchanged during a consultation."""

    class FileType(models.TextChoices):
        IMAGE = "image", "Image"
        DOCUMENT = "document", "Document"
        LAB_REPORT = "lab_report", "Lab Report"
        PRESCRIPTION = "prescription", "Prescription"
        OTHER = "other", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    consultation = models.ForeignKey(
        Consultation, on_delete=models.CASCADE, related_name="files"
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="consultation_files"
    )
    file = models.FileField(upload_to="consultation_files/%Y/%m/%d/")
    original_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=15, choices=FileType.choices, default=FileType.OTHER)
    file_size = models.PositiveIntegerField(help_text="Size in bytes")
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.original_name} ({self.file_type})"
