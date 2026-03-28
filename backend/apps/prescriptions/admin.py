"""Admin configuration for prescriptions app."""
from django.contrib import admin

from .models import Dosage, Medication, Prescription, PrescriptionRefill


class DosageInline(admin.TabularInline):
    model = Dosage
    extra = 1
    raw_id_fields = ["medication"]


class RefillInline(admin.TabularInline):
    model = PrescriptionRefill
    extra = 0
    readonly_fields = ["requested_at", "approved_at", "dispensed_at", "picked_up_at"]


@admin.register(Medication)
class MedicationAdmin(admin.ModelAdmin):
    list_display = [
        "name", "generic_name", "drug_class", "form",
        "strength", "requires_prescription", "is_controlled", "is_active",
    ]
    list_filter = ["form", "requires_prescription", "is_controlled", "is_active"]
    search_fields = ["name", "generic_name", "drug_class"]


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = [
        "prescription_number", "doctor", "patient", "status",
        "valid_from", "valid_until", "is_refillable",
        "refills_used", "max_refills", "created_at",
    ]
    list_filter = ["status", "is_refillable", "created_at"]
    search_fields = [
        "prescription_number", "doctor__first_name", "doctor__last_name",
        "patient__first_name", "patient__last_name", "diagnosis",
    ]
    raw_id_fields = ["doctor", "patient", "consultation"]
    readonly_fields = ["prescription_number", "created_at", "updated_at"]
    inlines = [DosageInline, RefillInline]


@admin.register(Dosage)
class DosageAdmin(admin.ModelAdmin):
    list_display = [
        "medication", "prescription", "dosage_amount",
        "frequency", "route", "duration_days", "quantity",
    ]
    list_filter = ["frequency", "route"]
    raw_id_fields = ["prescription", "medication"]


@admin.register(PrescriptionRefill)
class PrescriptionRefillAdmin(admin.ModelAdmin):
    list_display = [
        "prescription", "refill_number", "status",
        "requested_by", "approved_by", "requested_at",
    ]
    list_filter = ["status"]
    raw_id_fields = ["prescription", "requested_by", "approved_by", "pharmacy"]
    readonly_fields = ["requested_at", "approved_at", "dispensed_at", "picked_up_at"]
