"""Serializers for the prescriptions app."""
from rest_framework import serializers

from .models import Dosage, Medication, Prescription, PrescriptionRefill


class MedicationSerializer(serializers.ModelSerializer):
    form_display = serializers.CharField(source="get_form_display", read_only=True)

    class Meta:
        model = Medication
        fields = [
            "id", "name", "generic_name", "brand_names", "drug_class",
            "form", "form_display", "strength", "requires_prescription",
            "is_controlled", "contraindications", "side_effects",
            "is_active",
        ]
        read_only_fields = ["id"]


class DosageSerializer(serializers.ModelSerializer):
    medication_info = MedicationSerializer(source="medication", read_only=True)
    frequency_display = serializers.CharField(
        source="get_frequency_display", read_only=True
    )
    route_display = serializers.CharField(source="get_route_display", read_only=True)

    class Meta:
        model = Dosage
        fields = [
            "id", "prescription", "medication", "medication_info",
            "dosage_amount", "frequency", "frequency_display",
            "route", "route_display", "duration_days", "quantity",
            "take_with_food", "special_instructions",
            "start_date", "end_date", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class PrescriptionRefillSerializer(serializers.ModelSerializer):
    requested_by_name = serializers.CharField(
        source="requested_by.get_full_name", read_only=True
    )
    approved_by_name = serializers.CharField(
        source="approved_by.get_full_name", read_only=True, default=None
    )

    class Meta:
        model = PrescriptionRefill
        fields = [
            "id", "prescription", "refill_number", "status",
            "requested_by", "requested_by_name",
            "approved_by", "approved_by_name",
            "pharmacy", "denial_reason", "notes",
            "requested_at", "approved_at", "dispensed_at", "picked_up_at",
        ]
        read_only_fields = [
            "id", "requested_by", "refill_number",
            "requested_at", "approved_at", "dispensed_at", "picked_up_at",
        ]


class PrescriptionSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source="doctor.get_full_name", read_only=True)
    patient_name = serializers.CharField(source="patient.get_full_name", read_only=True)
    dosages = DosageSerializer(many=True, read_only=True)
    refills = PrescriptionRefillSerializer(many=True, read_only=True)
    is_expired = serializers.ReadOnlyField()
    refills_remaining = serializers.ReadOnlyField()

    class Meta:
        model = Prescription
        fields = [
            "id", "consultation", "doctor", "patient",
            "doctor_name", "patient_name", "prescription_number",
            "status", "diagnosis", "notes", "pharmacy_notes",
            "valid_from", "valid_until", "is_refillable",
            "max_refills", "refills_used", "refills_remaining",
            "is_expired", "signed_at", "dispensed_at",
            "dosages", "refills", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "prescription_number", "refills_used",
            "signed_at", "dispensed_at", "created_at", "updated_at",
        ]

    def create(self, validated_data):
        validated_data["doctor"] = self.context["request"].user
        return super().create(validated_data)


class PrescriptionListSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source="doctor.get_full_name", read_only=True)
    patient_name = serializers.CharField(source="patient.get_full_name", read_only=True)
    medication_count = serializers.SerializerMethodField()

    class Meta:
        model = Prescription
        fields = [
            "id", "doctor_name", "patient_name", "prescription_number",
            "status", "diagnosis", "valid_from", "valid_until",
            "is_refillable", "medication_count", "created_at",
        ]

    def get_medication_count(self, obj):
        return obj.dosages.count()
