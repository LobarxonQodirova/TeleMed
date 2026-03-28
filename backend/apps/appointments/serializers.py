"""Serializers for the appointments app."""
from datetime import date, datetime, timedelta

from django.utils import timezone
from rest_framework import serializers

from .models import Appointment, Cancellation, TimeSlot


class TimeSlotSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source="doctor.get_full_name", read_only=True)
    is_bookable = serializers.ReadOnlyField()

    class Meta:
        model = TimeSlot
        fields = [
            "id", "doctor", "doctor_name", "schedule", "date",
            "start_time", "end_time", "status", "max_bookings",
            "current_bookings", "is_bookable", "consultation_types",
            "created_at",
        ]
        read_only_fields = ["id", "current_bookings", "created_at"]


class CancellationSerializer(serializers.ModelSerializer):
    cancelled_by_name = serializers.CharField(
        source="cancelled_by_user.get_full_name", read_only=True
    )

    class Meta:
        model = Cancellation
        fields = [
            "id", "appointment", "cancelled_by", "cancelled_by_user",
            "cancelled_by_name", "reason", "reason_detail",
            "refund_requested", "refund_amount", "is_late_cancellation",
            "cancelled_at",
        ]
        read_only_fields = [
            "id", "cancelled_by_user", "is_late_cancellation",
            "cancelled_at",
        ]


class AppointmentSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.get_full_name", read_only=True)
    doctor_name = serializers.CharField(source="doctor.get_full_name", read_only=True)
    scheduled_datetime = serializers.ReadOnlyField()
    cancellation = CancellationSerializer(read_only=True)
    time_slot_info = TimeSlotSerializer(source="time_slot", read_only=True)

    class Meta:
        model = Appointment
        fields = [
            "id", "patient", "doctor", "patient_name", "doctor_name",
            "time_slot", "time_slot_info", "appointment_type",
            "consultation_mode", "status",
            "scheduled_date", "scheduled_time", "scheduled_datetime",
            "duration_minutes", "reason", "symptoms", "notes",
            "doctor_notes", "is_first_visit", "reminder_sent",
            "confirmed_at", "checked_in_at", "fee",
            "cancellation", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "patient", "status", "reminder_sent",
            "confirmed_at", "checked_in_at",
            "created_at", "updated_at",
        ]

    def validate(self, attrs):
        scheduled_date = attrs.get("scheduled_date")
        if scheduled_date and scheduled_date < date.today():
            raise serializers.ValidationError(
                {"scheduled_date": "Cannot book appointments in the past."}
            )

        doctor = attrs.get("doctor")
        scheduled_time = attrs.get("scheduled_time")
        if doctor and scheduled_date and scheduled_time:
            existing = Appointment.objects.filter(
                doctor=doctor,
                scheduled_date=scheduled_date,
                scheduled_time=scheduled_time,
                status__in=["pending", "confirmed"],
            )
            if self.instance:
                existing = existing.exclude(id=self.instance.id)
            if existing.exists():
                raise serializers.ValidationError(
                    {"scheduled_time": "This time slot is already booked."}
                )
        return attrs

    def create(self, validated_data):
        validated_data["patient"] = self.context["request"].user
        # Set fee from doctor profile
        doctor = validated_data["doctor"]
        if hasattr(doctor, "doctor_profile"):
            appt_type = validated_data.get("appointment_type", "initial")
            if appt_type == "follow_up":
                validated_data["fee"] = doctor.doctor_profile.follow_up_fee
            else:
                validated_data["fee"] = doctor.doctor_profile.consultation_fee
        return super().create(validated_data)


class AppointmentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for appointment listings."""

    patient_name = serializers.CharField(source="patient.get_full_name", read_only=True)
    doctor_name = serializers.CharField(source="doctor.get_full_name", read_only=True)

    class Meta:
        model = Appointment
        fields = [
            "id", "patient_name", "doctor_name", "appointment_type",
            "consultation_mode", "status", "scheduled_date",
            "scheduled_time", "duration_minutes", "fee", "created_at",
        ]


class RescheduleSerializer(serializers.Serializer):
    """Serializer for rescheduling an appointment."""

    new_date = serializers.DateField()
    new_time = serializers.TimeField()
    reason = serializers.CharField(max_length=500, required=False, default="")

    def validate_new_date(self, value):
        if value < date.today():
            raise serializers.ValidationError("Cannot reschedule to a past date.")
        return value
