"""Admin configuration for appointments app."""
from django.contrib import admin

from .models import Appointment, Cancellation, TimeSlot


class CancellationInline(admin.StackedInline):
    model = Cancellation
    extra = 0
    readonly_fields = ["cancelled_at"]


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = [
        "doctor", "date", "start_time", "end_time",
        "status", "current_bookings", "max_bookings",
    ]
    list_filter = ["status", "date"]
    search_fields = ["doctor__first_name", "doctor__last_name"]
    date_hierarchy = "date"
    raw_id_fields = ["doctor", "schedule"]


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = [
        "id", "patient", "doctor", "appointment_type",
        "consultation_mode", "status", "scheduled_date",
        "scheduled_time", "fee", "created_at",
    ]
    list_filter = [
        "status", "appointment_type", "consultation_mode",
        "scheduled_date", "created_at",
    ]
    search_fields = [
        "patient__first_name", "patient__last_name",
        "doctor__first_name", "doctor__last_name",
        "reason",
    ]
    raw_id_fields = ["patient", "doctor", "time_slot"]
    date_hierarchy = "scheduled_date"
    readonly_fields = ["created_at", "updated_at"]
    inlines = [CancellationInline]


@admin.register(Cancellation)
class CancellationAdmin(admin.ModelAdmin):
    list_display = [
        "appointment", "cancelled_by", "cancelled_by_user",
        "reason", "is_late_cancellation", "refund_requested",
        "cancelled_at",
    ]
    list_filter = ["cancelled_by", "reason", "is_late_cancellation", "refund_requested"]
    search_fields = ["reason_detail"]
    raw_id_fields = ["appointment", "cancelled_by_user"]
    readonly_fields = ["cancelled_at"]
