"""Models for the records app -- health records, vitals, lab results, documents."""
import uuid

from django.conf import settings
from django.db import models


class HealthRecord(models.Model):
    """A health record entry for a patient, linked to a consultation or standalone."""

    class RecordType(models.TextChoices):
        CONSULTATION = "consultation", "Consultation Record"
        LAB = "lab", "Lab Results"
        IMAGING = "imaging", "Imaging Results"
        PROCEDURE = "procedure", "Procedure Notes"
        DISCHARGE = "discharge", "Discharge Summary"
        REFERRAL = "referral", "Referral"
        GENERAL = "general", "General"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="health_records",
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="authored_records",
    )
    consultation = models.ForeignKey(
        "consultations.Consultation",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="health_records",
    )
    record_type = models.CharField(
        max_length=15, choices=RecordType.choices, default=RecordType.GENERAL
    )
    title = models.CharField(max_length=300)
    summary = models.TextField(blank=True)
    details = models.JSONField(default=dict, blank=True)
    diagnosis_codes = models.JSONField(
        default=list, blank=True,
        help_text="ICD-10 diagnosis codes",
    )
    is_confidential = models.BooleanField(
        default=False, help_text="Restricted access record"
    )
    record_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-record_date", "-created_at"]
        indexes = [
            models.Index(fields=["patient", "record_type"]),
            models.Index(fields=["record_date"]),
        ]

    def __str__(self):
        return f"{self.title} - {self.patient.get_full_name()} ({self.record_date})"


class Vitals(models.Model):
    """Vital signs recorded for a patient."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="vitals",
    )
    health_record = models.ForeignKey(
        HealthRecord,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vitals",
    )
    consultation = models.ForeignKey(
        "consultations.Consultation",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vitals",
    )
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recorded_vitals",
    )
    temperature_f = models.DecimalField(
        max_digits=4, decimal_places=1, null=True, blank=True,
        help_text="Temperature in Fahrenheit",
    )
    heart_rate = models.PositiveIntegerField(
        null=True, blank=True, help_text="Heart rate in bpm"
    )
    blood_pressure_systolic = models.PositiveIntegerField(
        null=True, blank=True, help_text="Systolic blood pressure (mmHg)"
    )
    blood_pressure_diastolic = models.PositiveIntegerField(
        null=True, blank=True, help_text="Diastolic blood pressure (mmHg)"
    )
    respiratory_rate = models.PositiveIntegerField(
        null=True, blank=True, help_text="Breaths per minute"
    )
    oxygen_saturation = models.DecimalField(
        max_digits=4, decimal_places=1, null=True, blank=True,
        help_text="SpO2 percentage",
    )
    weight_kg = models.DecimalField(
        max_digits=5, decimal_places=1, null=True, blank=True
    )
    height_cm = models.DecimalField(
        max_digits=5, decimal_places=1, null=True, blank=True
    )
    blood_glucose = models.DecimalField(
        max_digits=5, decimal_places=1, null=True, blank=True,
        help_text="Blood glucose (mg/dL)",
    )
    pain_level = models.PositiveSmallIntegerField(
        null=True, blank=True, help_text="Pain level 0-10"
    )
    notes = models.TextField(blank=True)
    recorded_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "vitals"
        ordering = ["-recorded_at"]
        indexes = [
            models.Index(fields=["patient", "recorded_at"]),
        ]

    def __str__(self):
        return f"Vitals for {self.patient.get_full_name()} at {self.recorded_at}"

    @property
    def blood_pressure(self):
        if self.blood_pressure_systolic and self.blood_pressure_diastolic:
            return f"{self.blood_pressure_systolic}/{self.blood_pressure_diastolic}"
        return None

    @property
    def bmi(self):
        if self.height_cm and self.weight_kg and self.height_cm > 0:
            h = float(self.height_cm) / 100
            return round(float(self.weight_kg) / (h ** 2), 1)
        return None


class LabResult(models.Model):
    """Laboratory test results for a patient."""

    class ResultStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    class AbnormalFlag(models.TextChoices):
        NORMAL = "normal", "Normal"
        LOW = "low", "Low"
        HIGH = "high", "High"
        CRITICAL_LOW = "critical_low", "Critical Low"
        CRITICAL_HIGH = "critical_high", "Critical High"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="lab_results",
    )
    health_record = models.ForeignKey(
        HealthRecord,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lab_results",
    )
    ordered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ordered_labs",
    )
    test_name = models.CharField(max_length=200)
    test_code = models.CharField(max_length=50, blank=True, help_text="LOINC or lab code")
    category = models.CharField(
        max_length=50, blank=True,
        choices=[
            ("blood", "Blood Test"), ("urine", "Urinalysis"),
            ("imaging", "Imaging"), ("pathology", "Pathology"),
            ("microbiology", "Microbiology"), ("other", "Other"),
        ],
    )
    result_value = models.CharField(max_length=200, blank=True)
    result_unit = models.CharField(max_length=50, blank=True)
    reference_range = models.CharField(max_length=100, blank=True)
    abnormal_flag = models.CharField(
        max_length=15, choices=AbnormalFlag.choices, default=AbnormalFlag.NORMAL
    )
    result_status = models.CharField(
        max_length=10, choices=ResultStatus.choices, default=ResultStatus.PENDING
    )
    lab_name = models.CharField(max_length=200, blank=True)
    specimen_type = models.CharField(max_length=100, blank=True)
    collected_at = models.DateTimeField(null=True, blank=True)
    resulted_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    is_critical = models.BooleanField(default=False)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_labs",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["patient", "test_name"]),
        ]

    def __str__(self):
        return f"{self.test_name}: {self.result_value} {self.result_unit} ({self.patient.get_full_name()})"


class Document(models.Model):
    """Medical documents uploaded for a patient."""

    class DocumentType(models.TextChoices):
        LAB_REPORT = "lab_report", "Lab Report"
        IMAGING = "imaging", "Imaging"
        REFERRAL = "referral", "Referral Letter"
        INSURANCE = "insurance", "Insurance Document"
        CONSENT = "consent", "Consent Form"
        DISCHARGE = "discharge", "Discharge Summary"
        PRESCRIPTION = "prescription", "Prescription"
        ID_DOCUMENT = "id_document", "ID Document"
        OTHER = "other", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    health_record = models.ForeignKey(
        HealthRecord,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents",
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="uploaded_documents",
    )
    title = models.CharField(max_length=300)
    document_type = models.CharField(
        max_length=15, choices=DocumentType.choices, default=DocumentType.OTHER
    )
    file = models.FileField(upload_to="medical_documents/%Y/%m/%d/")
    original_filename = models.CharField(max_length=300)
    file_size = models.PositiveIntegerField(help_text="Size in bytes")
    mime_type = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    is_confidential = models.BooleanField(default=False)
    document_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.get_document_type_display()})"
