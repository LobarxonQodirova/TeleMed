"""Admin configuration for patients app."""
from django.contrib import admin

from .models import Allergy, InsuranceInfo, MedicalProfile, Patient


class AllergyInline(admin.TabularInline):
    model = Allergy
    extra = 0
    fields = ["allergen", "allergy_type", "severity", "is_active"]


class InsuranceInline(admin.StackedInline):
    model = InsuranceInfo
    extra = 0
    fields = [
        "provider_name", "plan_type", "policy_number", "member_id",
        "coverage_start", "coverage_end", "is_primary", "is_active",
        "verification_status",
    ]


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = [
        "user", "medical_record_number", "primary_physician",
        "consent_telemedicine", "created_at",
    ]
    list_filter = ["consent_telemedicine", "advance_directive", "created_at"]
    search_fields = [
        "user__first_name", "user__last_name", "user__email",
        "medical_record_number",
    ]
    raw_id_fields = ["user", "primary_physician", "preferred_pharmacy"]
    inlines = [AllergyInline, InsuranceInline]
    readonly_fields = ["medical_record_number", "created_at", "updated_at"]


@admin.register(MedicalProfile)
class MedicalProfileAdmin(admin.ModelAdmin):
    list_display = [
        "patient", "blood_type", "height_cm", "weight_kg", "bmi",
        "lifestyle_smoking", "updated_at",
    ]
    list_filter = ["blood_type", "lifestyle_smoking", "lifestyle_alcohol"]
    search_fields = ["patient__user__first_name", "patient__user__last_name"]
    readonly_fields = ["bmi", "updated_at"]


@admin.register(Allergy)
class AllergyAdmin(admin.ModelAdmin):
    list_display = ["allergen", "patient", "allergy_type", "severity", "is_active"]
    list_filter = ["allergy_type", "severity", "is_active"]
    search_fields = ["allergen", "patient__user__first_name"]


@admin.register(InsuranceInfo)
class InsuranceInfoAdmin(admin.ModelAdmin):
    list_display = [
        "provider_name", "patient", "plan_type", "policy_number",
        "is_primary", "is_active", "verification_status",
    ]
    list_filter = ["plan_type", "is_primary", "is_active", "verification_status"]
    search_fields = ["provider_name", "policy_number", "patient__user__first_name"]
    readonly_fields = ["created_at", "updated_at", "verified_at"]
