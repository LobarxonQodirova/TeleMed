"""Admin configuration for records app."""
from django.contrib import admin

from .models import Document, HealthRecord, LabResult, Vitals


class VitalsInline(admin.TabularInline):
    model = Vitals
    extra = 0
    fields = [
        "temperature_f", "heart_rate", "blood_pressure_systolic",
        "blood_pressure_diastolic", "oxygen_saturation", "recorded_at",
    ]
    readonly_fields = ["created_at"]


class LabResultInline(admin.TabularInline):
    model = LabResult
    extra = 0
    fields = [
        "test_name", "result_value", "result_unit",
        "abnormal_flag", "result_status",
    ]


class DocumentInline(admin.TabularInline):
    model = Document
    extra = 0
    fields = ["title", "document_type", "file", "created_at"]
    readonly_fields = ["created_at"]


@admin.register(HealthRecord)
class HealthRecordAdmin(admin.ModelAdmin):
    list_display = [
        "title", "patient", "doctor", "record_type",
        "record_date", "is_confidential", "created_at",
    ]
    list_filter = ["record_type", "is_confidential", "record_date"]
    search_fields = [
        "title", "summary",
        "patient__first_name", "patient__last_name",
    ]
    raw_id_fields = ["patient", "doctor", "consultation"]
    date_hierarchy = "record_date"
    inlines = [VitalsInline, LabResultInline, DocumentInline]


@admin.register(Vitals)
class VitalsAdmin(admin.ModelAdmin):
    list_display = [
        "patient", "temperature_f", "heart_rate",
        "blood_pressure_systolic", "blood_pressure_diastolic",
        "oxygen_saturation", "recorded_at",
    ]
    list_filter = ["recorded_at"]
    search_fields = ["patient__first_name", "patient__last_name"]
    raw_id_fields = ["patient", "recorded_by", "health_record", "consultation"]


@admin.register(LabResult)
class LabResultAdmin(admin.ModelAdmin):
    list_display = [
        "test_name", "patient", "result_value", "result_unit",
        "abnormal_flag", "result_status", "is_critical",
        "created_at",
    ]
    list_filter = ["result_status", "abnormal_flag", "is_critical", "category"]
    search_fields = ["test_name", "test_code", "patient__first_name"]
    raw_id_fields = ["patient", "ordered_by", "reviewed_by", "health_record"]


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = [
        "title", "patient", "document_type", "file_size",
        "is_confidential", "created_at",
    ]
    list_filter = ["document_type", "is_confidential"]
    search_fields = ["title", "description", "patient__first_name"]
    raw_id_fields = ["patient", "uploaded_by", "health_record"]
