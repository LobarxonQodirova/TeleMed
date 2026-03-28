"""Admin configuration for accounts app."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import DoctorProfile, PatientProfile, Specialty, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = [
        "email", "username", "first_name", "last_name",
        "role", "is_verified", "is_active", "created_at",
    ]
    list_filter = ["role", "is_verified", "is_active", "created_at"]
    search_fields = ["email", "username", "first_name", "last_name"]
    ordering = ["-created_at"]
    fieldsets = BaseUserAdmin.fieldsets + (
        ("TeleMed Fields", {
            "fields": ("role", "phone", "avatar", "date_of_birth", "is_verified"),
        }),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("TeleMed Fields", {
            "fields": ("email", "first_name", "last_name", "role"),
        }),
    )


@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = [
        "user", "license_number", "qualification",
        "experience_years", "consultation_fee", "average_rating",
        "is_available", "is_accepting_patients",
    ]
    list_filter = [
        "is_available", "is_accepting_patients",
        "specialties", "experience_years",
    ]
    search_fields = [
        "user__first_name", "user__last_name",
        "license_number", "qualification",
    ]
    filter_horizontal = ["specialties"]
    readonly_fields = ["average_rating", "total_reviews", "total_consultations"]


@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "gender", "blood_group", "city", "insurance_provider"]
    list_filter = ["gender", "blood_group"]
    search_fields = ["user__first_name", "user__last_name", "insurance_id"]


@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "is_active", "created_at"]
    list_filter = ["is_active"]
    search_fields = ["name"]
    prepopulated_fields = {"slug": ("name",)}
