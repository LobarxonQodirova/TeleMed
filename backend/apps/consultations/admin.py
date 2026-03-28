"""Admin configuration for consultations app."""
from django.contrib import admin

from .models import Consultation, ConsultationFile, ConsultationNote, VideoSession


class ConsultationNoteInline(admin.TabularInline):
    model = ConsultationNote
    extra = 0
    fields = ["author", "note_type", "content", "is_private", "created_at"]
    readonly_fields = ["created_at"]


class VideoSessionInline(admin.TabularInline):
    model = VideoSession
    extra = 0
    fields = ["session_token", "status", "started_at", "ended_at"]
    readonly_fields = ["session_token", "started_at", "ended_at"]


class ConsultationFileInline(admin.TabularInline):
    model = ConsultationFile
    extra = 0
    fields = ["original_name", "file_type", "file_size", "uploaded_by", "created_at"]
    readonly_fields = ["file_size", "created_at"]


@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = [
        "id", "doctor", "patient", "consultation_type", "status",
        "scheduled_at", "started_at", "ended_at", "duration_minutes",
    ]
    list_filter = ["status", "consultation_type", "scheduled_at", "created_at"]
    search_fields = [
        "doctor__first_name", "doctor__last_name",
        "patient__first_name", "patient__last_name",
        "chief_complaint", "diagnosis",
    ]
    raw_id_fields = ["doctor", "patient", "appointment"]
    readonly_fields = ["created_at", "updated_at"]
    date_hierarchy = "scheduled_at"
    inlines = [ConsultationNoteInline, VideoSessionInline, ConsultationFileInline]


@admin.register(ConsultationNote)
class ConsultationNoteAdmin(admin.ModelAdmin):
    list_display = ["consultation", "author", "note_type", "is_private", "created_at"]
    list_filter = ["note_type", "is_private", "created_at"]
    search_fields = ["content", "subjective", "assessment"]
    raw_id_fields = ["consultation", "author"]


@admin.register(VideoSession)
class VideoSessionAdmin(admin.ModelAdmin):
    list_display = [
        "session_token", "consultation", "status",
        "started_at", "ended_at", "created_at",
    ]
    list_filter = ["status", "created_at"]
    search_fields = ["session_token"]
    readonly_fields = ["session_token", "created_at"]


@admin.register(ConsultationFile)
class ConsultationFileAdmin(admin.ModelAdmin):
    list_display = [
        "original_name", "consultation", "uploaded_by",
        "file_type", "file_size", "created_at",
    ]
    list_filter = ["file_type", "created_at"]
    search_fields = ["original_name", "description"]
    readonly_fields = ["file_size", "created_at"]
