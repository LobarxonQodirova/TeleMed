"""Serializers for the patients app."""
from rest_framework import serializers

from .models import Allergy, InsuranceInfo, MedicalProfile, Patient


class AllergySerializer(serializers.ModelSerializer):
    severity_display = serializers.CharField(
        source="get_severity_display", read_only=True
    )
    type_display = serializers.CharField(
        source="get_allergy_type_display", read_only=True
    )

    class Meta:
        model = Allergy
        fields = [
            "id", "patient", "allergen", "allergy_type", "type_display",
            "severity", "severity_display", "reaction", "diagnosed_date",
            "is_active", "notes", "created_at",
        ]
        read_only_fields = ["id", "patient", "created_at"]

    def create(self, validated_data):
        validated_data["patient"] = self.context["patient"]
        return super().create(validated_data)


class InsuranceInfoSerializer(serializers.ModelSerializer):
    is_coverage_active = serializers.ReadOnlyField()
    plan_type_display = serializers.CharField(
        source="get_plan_type_display", read_only=True
    )

    class Meta:
        model = InsuranceInfo
        fields = [
            "id", "patient", "provider_name", "plan_type", "plan_type_display",
            "policy_number", "group_number", "member_id",
            "subscriber_name", "subscriber_relationship",
            "coverage_start", "coverage_end",
            "copay_amount", "deductible_amount", "deductible_met",
            "is_primary", "is_active", "is_coverage_active",
            "verification_status", "verified_at",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "patient", "verification_status", "verified_at",
            "created_at", "updated_at",
        ]

    def create(self, validated_data):
        validated_data["patient"] = self.context["patient"]
        return super().create(validated_data)


class MedicalProfileSerializer(serializers.ModelSerializer):
    bmi = serializers.ReadOnlyField()

    class Meta:
        model = MedicalProfile
        fields = [
            "id", "patient", "blood_type", "height_cm", "weight_kg", "bmi",
            "chronic_conditions", "past_surgeries", "family_history",
            "current_medications", "immunizations",
            "lifestyle_smoking", "lifestyle_alcohol", "lifestyle_exercise",
            "updated_at",
        ]
        read_only_fields = ["id", "patient", "updated_at"]


class PatientSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.get_full_name", read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)
    medical_profile = MedicalProfileSerializer(read_only=True)
    allergies = AllergySerializer(many=True, read_only=True)
    active_insurance = serializers.SerializerMethodField()

    class Meta:
        model = Patient
        fields = [
            "id", "user", "user_name", "user_email",
            "medical_record_number", "primary_physician",
            "preferred_pharmacy", "advance_directive",
            "consent_telemedicine", "consent_date", "notes",
            "medical_profile", "allergies", "active_insurance",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "user", "medical_record_number", "created_at", "updated_at",
        ]

    def get_active_insurance(self, obj):
        primary = obj.insurance_records.filter(is_primary=True, is_active=True).first()
        if primary:
            return InsuranceInfoSerializer(primary).data
        return None


class PatientListSerializer(serializers.ModelSerializer):
    """Lightweight patient serializer for list views."""

    user_name = serializers.CharField(source="user.get_full_name", read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = Patient
        fields = [
            "id", "user", "user_name", "user_email",
            "medical_record_number", "consent_telemedicine",
            "created_at",
        ]
