"""Models for the prescriptions app."""
import uuid

from django.conf import settings
from django.db import models


class Medication(models.Model):
    """Reference table for medications."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    generic_name = models.CharField(max_length=200, blank=True)
    brand_names = models.JSONField(default=list, blank=True)
    drug_class = models.CharField(max_length=150, blank=True)
    form = models.CharField(
        max_length=30,
        choices=[
            ("tablet", "Tablet"), ("capsule", "Capsule"),
            ("liquid", "Liquid"), ("injection", "Injection"),
            ("topical", "Topical"), ("inhaler", "Inhaler"),
            ("drops", "Drops"), ("patch", "Patch"), ("other", "Other"),
        ],
        default="tablet",
    )
    strength = models.CharField(max_length=50, blank=True, help_text="e.g., 500mg, 10ml")
    requires_prescription = models.BooleanField(default=True)
    is_controlled = models.BooleanField(default=False)
    contraindications = models.JSONField(default=list, blank=True)
    side_effects = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        unique_together = ["name", "strength", "form"]

    def __str__(self):
        return f"{self.name} {self.strength} ({self.get_form_display()})"


class Prescription(models.Model):
    """A prescription issued by a doctor to a patient."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ACTIVE = "active", "Active"
        DISPENSED = "dispensed", "Dispensed"
        EXPIRED = "expired", "Expired"
        CANCELLED = "cancelled", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    consultation = models.ForeignKey(
        "consultations.Consultation",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="prescriptions",
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="issued_prescriptions",
    )
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="prescriptions",
    )
    prescription_number = models.CharField(max_length=20, unique=True, blank=True)
    status = models.CharField(
        max_length=15, choices=Status.choices, default=Status.DRAFT
    )
    diagnosis = models.TextField(blank=True)
    notes = models.TextField(blank=True, help_text="Additional instructions")
    pharmacy_notes = models.TextField(blank=True)
    valid_from = models.DateField(auto_now_add=True)
    valid_until = models.DateField(null=True, blank=True)
    is_refillable = models.BooleanField(default=False)
    max_refills = models.PositiveIntegerField(default=0)
    refills_used = models.PositiveIntegerField(default=0)
    signed_at = models.DateTimeField(null=True, blank=True)
    dispensed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["patient", "status"]),
            models.Index(fields=["doctor", "status"]),
        ]

    def __str__(self):
        return f"Rx {self.prescription_number} - {self.patient.get_full_name()}"

    def save(self, *args, **kwargs):
        if not self.prescription_number:
            import random
            import string
            self.prescription_number = "RX-" + "".join(
                random.choices(string.digits, k=8)
            )
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        from datetime import date
        if self.valid_until:
            return date.today() > self.valid_until
        return False

    @property
    def refills_remaining(self):
        return max(0, self.max_refills - self.refills_used)


class Dosage(models.Model):
    """Dosage information for a medication in a prescription."""

    class Frequency(models.TextChoices):
        ONCE_DAILY = "once_daily", "Once daily"
        TWICE_DAILY = "twice_daily", "Twice daily"
        THREE_DAILY = "three_daily", "Three times daily"
        FOUR_DAILY = "four_daily", "Four times daily"
        EVERY_4H = "every_4h", "Every 4 hours"
        EVERY_6H = "every_6h", "Every 6 hours"
        EVERY_8H = "every_8h", "Every 8 hours"
        EVERY_12H = "every_12h", "Every 12 hours"
        AS_NEEDED = "as_needed", "As needed"
        WEEKLY = "weekly", "Weekly"
        BIWEEKLY = "biweekly", "Biweekly"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    prescription = models.ForeignKey(
        Prescription, on_delete=models.CASCADE, related_name="dosages"
    )
    medication = models.ForeignKey(
        Medication, on_delete=models.CASCADE, related_name="dosages"
    )
    dosage_amount = models.CharField(max_length=50, help_text="e.g., 1 tablet, 5ml")
    frequency = models.CharField(
        max_length=20, choices=Frequency.choices, default=Frequency.ONCE_DAILY
    )
    route = models.CharField(
        max_length=20, default="oral",
        choices=[
            ("oral", "Oral"), ("topical", "Topical"),
            ("intravenous", "Intravenous"), ("intramuscular", "Intramuscular"),
            ("subcutaneous", "Subcutaneous"), ("inhalation", "Inhalation"),
            ("ophthalmic", "Ophthalmic"), ("otic", "Otic"),
            ("rectal", "Rectal"), ("sublingual", "Sublingual"),
        ],
    )
    duration_days = models.PositiveIntegerField(
        null=True, blank=True, help_text="Duration in days"
    )
    quantity = models.PositiveIntegerField(default=1, help_text="Total quantity to dispense")
    take_with_food = models.BooleanField(default=False)
    special_instructions = models.TextField(blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.medication.name} - {self.dosage_amount} {self.get_frequency_display()}"


class PrescriptionRefill(models.Model):
    """Tracks refill requests and dispensing for prescriptions."""

    class Status(models.TextChoices):
        REQUESTED = "requested", "Requested"
        APPROVED = "approved", "Approved"
        DENIED = "denied", "Denied"
        DISPENSED = "dispensed", "Dispensed"
        PICKED_UP = "picked_up", "Picked Up"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    prescription = models.ForeignKey(
        Prescription, on_delete=models.CASCADE, related_name="refills"
    )
    refill_number = models.PositiveIntegerField()
    status = models.CharField(
        max_length=15, choices=Status.choices, default=Status.REQUESTED
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="refill_requests",
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="refill_approvals",
    )
    pharmacy = models.ForeignKey(
        "pharmacy.PharmacyPartner",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="refills",
    )
    denial_reason = models.TextField(blank=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    dispensed_at = models.DateTimeField(null=True, blank=True)
    picked_up_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-requested_at"]
        unique_together = ["prescription", "refill_number"]

    def __str__(self):
        return f"Refill #{self.refill_number} for {self.prescription}"

    def save(self, *args, **kwargs):
        if not self.refill_number:
            last = PrescriptionRefill.objects.filter(
                prescription=self.prescription
            ).order_by("-refill_number").first()
            self.refill_number = (last.refill_number + 1) if last else 1
        super().save(*args, **kwargs)

        if self.status == self.Status.DISPENSED:
            self.prescription.refills_used = PrescriptionRefill.objects.filter(
                prescription=self.prescription,
                status=self.Status.DISPENSED,
            ).count()
            self.prescription.save(update_fields=["refills_used"])
