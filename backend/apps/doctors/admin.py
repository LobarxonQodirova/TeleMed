"""Admin configuration for doctors app."""
from django.contrib import admin

from .models import DoctorReview, DoctorSchedule, Specialization


@admin.register(Specialization)
class SpecializationAdmin(admin.ModelAdmin):
    list_display = ["name", "specialty", "is_active", "created_at"]
    list_filter = ["specialty", "is_active"]
    search_fields = ["name", "specialty__name"]


@admin.register(DoctorSchedule)
class DoctorScheduleAdmin(admin.ModelAdmin):
    list_display = [
        "doctor", "day_of_week", "start_time", "end_time",
        "slot_duration_minutes", "max_patients", "is_active",
    ]
    list_filter = ["day_of_week", "is_active", "slot_duration_minutes"]
    search_fields = ["doctor__user__first_name", "doctor__user__last_name"]
    raw_id_fields = ["doctor"]


@admin.register(DoctorReview)
class DoctorReviewAdmin(admin.ModelAdmin):
    list_display = [
        "doctor", "patient", "overall_rating", "is_anonymous",
        "is_approved", "created_at",
    ]
    list_filter = ["overall_rating", "is_approved", "is_anonymous", "created_at"]
    search_fields = [
        "doctor__user__first_name", "doctor__user__last_name",
        "patient__first_name", "patient__last_name",
        "comment",
    ]
    raw_id_fields = ["doctor", "patient", "consultation"]
    readonly_fields = ["created_at", "updated_at"]
