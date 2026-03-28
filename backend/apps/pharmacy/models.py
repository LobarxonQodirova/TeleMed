"""Models for the pharmacy app."""
import uuid

from django.conf import settings
from django.db import models


class PharmacyPartner(models.Model):
    """Partner pharmacy for prescription fulfillment."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    license_number = models.CharField(max_length=50, unique=True)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=10)
    country = models.CharField(max_length=100, default="US")
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    operating_hours = models.JSONField(
        default=dict, blank=True,
        help_text='e.g. {"monday": {"open": "08:00", "close": "20:00"}}',
    )
    accepts_insurance = models.BooleanField(default=True)
    offers_delivery = models.BooleanField(default=False)
    delivery_radius_km = models.DecimalField(
        max_digits=5, decimal_places=1, null=True, blank=True
    )
    delivery_fee = models.DecimalField(
        max_digits=6, decimal_places=2, default=0
    )
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "pharmacy partners"

    def __str__(self):
        return f"{self.name} - {self.city}, {self.state}"


class DeliveryOrder(models.Model):
    """Prescription delivery order from a pharmacy."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        PREPARING = "preparing", "Preparing"
        READY_FOR_PICKUP = "ready_for_pickup", "Ready for Pickup"
        OUT_FOR_DELIVERY = "out_for_delivery", "Out for Delivery"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"
        FAILED = "failed", "Failed"

    class DeliveryType(models.TextChoices):
        PICKUP = "pickup", "In-Store Pickup"
        DELIVERY = "delivery", "Home Delivery"
        MAIL = "mail", "Mail Order"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    prescription = models.ForeignKey(
        "prescriptions.Prescription",
        on_delete=models.CASCADE,
        related_name="delivery_orders",
    )
    pharmacy = models.ForeignKey(
        PharmacyPartner,
        on_delete=models.CASCADE,
        related_name="delivery_orders",
    )
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="delivery_orders",
    )
    order_number = models.CharField(max_length=20, unique=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    delivery_type = models.CharField(
        max_length=10, choices=DeliveryType.choices, default=DeliveryType.PICKUP
    )
    delivery_address = models.TextField(blank=True)
    delivery_instructions = models.TextField(blank=True)
    delivery_fee = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    medication_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    insurance_covered = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    patient_copay = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tracking_number = models.CharField(max_length=100, blank=True)
    estimated_delivery = models.DateTimeField(null=True, blank=True)
    actual_delivery = models.DateTimeField(null=True, blank=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    prepared_at = models.DateTimeField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order {self.order_number} - {self.pharmacy.name} ({self.status})"

    def save(self, *args, **kwargs):
        if not self.order_number:
            import random
            import string
            self.order_number = "DEL-" + "".join(random.choices(string.digits, k=8))
        super().save(*args, **kwargs)

    @property
    def total_cost(self):
        return self.medication_cost + self.delivery_fee - self.insurance_covered
