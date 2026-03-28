"""Models for the payments app."""
import uuid

from django.conf import settings
from django.db import models


class Payment(models.Model):
    """Payment record for a consultation or appointment."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        REFUNDED = "refunded", "Refunded"
        PARTIALLY_REFUNDED = "partially_refunded", "Partially Refunded"

    class PaymentMethod(models.TextChoices):
        CREDIT_CARD = "credit_card", "Credit Card"
        DEBIT_CARD = "debit_card", "Debit Card"
        INSURANCE = "insurance", "Insurance"
        WALLET = "wallet", "Wallet"
        BANK_TRANSFER = "bank_transfer", "Bank Transfer"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="payments",
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_payments",
    )
    appointment = models.ForeignKey(
        "appointments.Appointment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments",
    )
    consultation = models.ForeignKey(
        "consultations.Consultation",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments",
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")
    payment_method = models.CharField(
        max_length=15, choices=PaymentMethod.choices, default=PaymentMethod.CREDIT_CARD
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, unique=True, null=True)
    stripe_charge_id = models.CharField(max_length=255, blank=True)
    description = models.CharField(max_length=500, blank=True)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    platform_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    doctor_payout = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    receipt_url = models.URLField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["patient", "status"]),
            models.Index(fields=["doctor", "status"]),
        ]

    def __str__(self):
        return f"Payment {self.id} - ${self.amount} ({self.status})"

    @property
    def total_amount(self):
        return self.amount + self.tax_amount

    def calculate_payout(self, platform_fee_percent=10):
        """Calculate doctor payout after platform fee."""
        self.platform_fee = self.amount * platform_fee_percent / 100
        self.doctor_payout = self.amount - self.platform_fee
        return self.doctor_payout


class InsuranceClaim(models.Model):
    """Insurance claim associated with a payment."""

    class ClaimStatus(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"
        UNDER_REVIEW = "under_review", "Under Review"
        APPROVED = "approved", "Approved"
        PARTIALLY_APPROVED = "partially_approved", "Partially Approved"
        DENIED = "denied", "Denied"
        APPEALED = "appealed", "Appealed"
        PAID = "paid", "Paid"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment = models.OneToOneField(
        Payment, on_delete=models.CASCADE, related_name="insurance_claim"
    )
    claim_number = models.CharField(max_length=50, unique=True)
    insurance_provider = models.CharField(max_length=200)
    policy_number = models.CharField(max_length=50)
    member_id = models.CharField(max_length=50)
    diagnosis_codes = models.JSONField(default=list, blank=True)
    procedure_codes = models.JSONField(default=list, blank=True)
    claimed_amount = models.DecimalField(max_digits=10, decimal_places=2)
    approved_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    patient_responsibility = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    status = models.CharField(
        max_length=20, choices=ClaimStatus.choices, default=ClaimStatus.SUBMITTED
    )
    denial_reason = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    eob_document = models.FileField(
        upload_to="insurance_eob/%Y/%m/", blank=True, null=True,
        help_text="Explanation of Benefits document",
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"Claim {self.claim_number} - {self.insurance_provider} ({self.status})"


class Refund(models.Model):
    """Refund record linked to a payment."""

    class RefundStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    class RefundReason(models.TextChoices):
        CANCELLATION = "cancellation", "Appointment Cancellation"
        NO_SHOW_DOCTOR = "no_show_doctor", "Doctor No-Show"
        TECHNICAL_ISSUE = "technical_issue", "Technical Issue"
        DISSATISFIED = "dissatisfied", "Patient Dissatisfied"
        DUPLICATE = "duplicate", "Duplicate Payment"
        OTHER = "other", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment = models.ForeignKey(
        Payment, on_delete=models.CASCADE, related_name="refunds"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.CharField(
        max_length=20, choices=RefundReason.choices, default=RefundReason.OTHER
    )
    reason_detail = models.TextField(blank=True)
    status = models.CharField(
        max_length=15, choices=RefundStatus.choices, default=RefundStatus.PENDING
    )
    stripe_refund_id = models.CharField(max_length=255, blank=True)
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="processed_refunds",
    )
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-requested_at"]

    def __str__(self):
        return f"Refund ${self.amount} for Payment {self.payment_id} ({self.status})"

    @property
    def is_full_refund(self):
        return self.amount == self.payment.amount
