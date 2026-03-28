"""Serializers for the doctors app."""
from rest_framework import serializers

from apps.accounts.serializers import DoctorProfileSerializer, UserSerializer

from .models import DoctorReview, DoctorSchedule, Specialization


class SpecializationSerializer(serializers.ModelSerializer):
    specialty_name = serializers.CharField(source="specialty.name", read_only=True)

    class Meta:
        model = Specialization
        fields = ["id", "specialty", "specialty_name", "name", "description", "is_active"]
        read_only_fields = ["id"]


class DoctorScheduleSerializer(serializers.ModelSerializer):
    day_name = serializers.CharField(source="get_day_of_week_display", read_only=True)
    total_slots = serializers.ReadOnlyField()
    doctor_name = serializers.CharField(
        source="doctor.user.get_full_name", read_only=True
    )

    class Meta:
        model = DoctorSchedule
        fields = [
            "id", "doctor", "doctor_name", "day_of_week", "day_name",
            "start_time", "end_time", "slot_duration_minutes", "max_patients",
            "is_active", "break_start", "break_end", "consultation_types",
            "effective_from", "effective_until", "total_slots",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        start_time = attrs.get("start_time")
        end_time = attrs.get("end_time")
        if start_time and end_time and start_time >= end_time:
            raise serializers.ValidationError(
                {"end_time": "End time must be after start time."}
            )

        break_start = attrs.get("break_start")
        break_end = attrs.get("break_end")
        if break_start and break_end:
            if break_start >= break_end:
                raise serializers.ValidationError(
                    {"break_end": "Break end must be after break start."}
                )
            if start_time and (break_start < start_time):
                raise serializers.ValidationError(
                    {"break_start": "Break must start within schedule hours."}
                )
            if end_time and (break_end > end_time):
                raise serializers.ValidationError(
                    {"break_end": "Break must end within schedule hours."}
                )
        return attrs


class DoctorReviewSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    doctor_name = serializers.CharField(
        source="doctor.user.get_full_name", read_only=True
    )

    class Meta:
        model = DoctorReview
        fields = [
            "id", "doctor", "patient", "patient_name", "doctor_name",
            "consultation", "overall_rating", "punctuality_rating",
            "communication_rating", "knowledge_rating",
            "title", "comment", "is_anonymous", "is_approved",
            "doctor_response", "doctor_responded_at",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "patient", "is_approved",
            "doctor_response", "doctor_responded_at",
            "created_at", "updated_at",
        ]

    def get_patient_name(self, obj):
        if obj.is_anonymous:
            return "Anonymous"
        return obj.patient.get_full_name()

    def create(self, validated_data):
        validated_data["patient"] = self.context["request"].user
        return super().create(validated_data)


class DoctorReviewResponseSerializer(serializers.Serializer):
    """Serializer for a doctor responding to a review."""

    response = serializers.CharField(max_length=2000)


class DoctorScheduleBulkSerializer(serializers.Serializer):
    """Serializer for creating multiple schedule entries at once."""

    schedules = DoctorScheduleSerializer(many=True)

    def create(self, validated_data):
        doctor = self.context["doctor"]
        schedules = []
        for schedule_data in validated_data["schedules"]:
            schedule_data["doctor"] = doctor
            schedules.append(DoctorSchedule(**schedule_data))
        return DoctorSchedule.objects.bulk_create(schedules)
