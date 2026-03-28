"""Serializers for consultations app."""
from rest_framework import serializers

from apps.accounts.serializers import UserSerializer

from .models import Consultation, ConsultationFile, ConsultationNote, VideoSession


class ConsultationNoteSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.get_full_name", read_only=True)

    class Meta:
        model = ConsultationNote
        fields = [
            "id", "consultation", "author", "author_name", "note_type",
            "subjective", "objective", "assessment", "plan",
            "content", "is_private", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "author", "created_at", "updated_at"]

    def create(self, validated_data):
        validated_data["author"] = self.context["request"].user
        return super().create(validated_data)


class ConsultationFileSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(
        source="uploaded_by.get_full_name", read_only=True
    )

    class Meta:
        model = ConsultationFile
        fields = [
            "id", "consultation", "uploaded_by", "uploaded_by_name",
            "file", "original_name", "file_type", "file_size",
            "description", "created_at",
        ]
        read_only_fields = ["id", "uploaded_by", "file_size", "created_at"]

    def create(self, validated_data):
        validated_data["uploaded_by"] = self.context["request"].user
        file_obj = validated_data["file"]
        validated_data["file_size"] = file_obj.size
        if not validated_data.get("original_name"):
            validated_data["original_name"] = file_obj.name
        return super().create(validated_data)


class VideoSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoSession
        fields = [
            "id", "consultation", "session_token", "status",
            "started_at", "ended_at", "doctor_joined_at",
            "patient_joined_at", "created_at",
        ]
        read_only_fields = [
            "id", "session_token", "started_at", "ended_at",
            "doctor_joined_at", "patient_joined_at", "created_at",
        ]


class ConsultationSerializer(serializers.ModelSerializer):
    doctor_info = UserSerializer(source="doctor", read_only=True)
    patient_info = UserSerializer(source="patient", read_only=True)
    notes = ConsultationNoteSerializer(many=True, read_only=True)
    actual_duration = serializers.ReadOnlyField()

    class Meta:
        model = Consultation
        fields = [
            "id", "appointment", "doctor", "patient",
            "doctor_info", "patient_info",
            "consultation_type", "status", "chief_complaint",
            "diagnosis", "treatment_plan", "follow_up_required",
            "follow_up_date", "scheduled_at", "started_at", "ended_at",
            "duration_minutes", "actual_duration", "queue_position",
            "notes", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "started_at", "ended_at", "duration_minutes",
            "queue_position", "created_at", "updated_at",
        ]


class ConsultationListSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source="doctor.get_full_name", read_only=True)
    patient_name = serializers.CharField(source="patient.get_full_name", read_only=True)

    class Meta:
        model = Consultation
        fields = [
            "id", "doctor", "patient", "doctor_name", "patient_name",
            "consultation_type", "status", "chief_complaint",
            "scheduled_at", "started_at", "ended_at", "queue_position",
            "created_at",
        ]
