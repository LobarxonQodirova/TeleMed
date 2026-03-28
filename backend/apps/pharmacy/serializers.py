"""Serializers for the pharmacy app."""
from rest_framework import serializers

from .models import DeliveryOrder, PharmacyPartner


class PharmacyPartnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = PharmacyPartner
        fields = [
            "id", "name", "license_number", "phone", "email", "website",
            "address", "city", "state", "zip_code", "country",
            "latitude", "longitude", "operating_hours",
            "accepts_insurance", "offers_delivery",
            "delivery_radius_km", "delivery_fee",
            "is_active", "is_verified", "rating",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "is_verified", "rating", "created_at", "updated_at"]


class PharmacyPartnerListSerializer(serializers.ModelSerializer):
    class Meta:
        model = PharmacyPartner
        fields = [
            "id", "name", "phone", "city", "state",
            "offers_delivery", "accepts_insurance", "rating",
        ]


class DeliveryOrderSerializer(serializers.ModelSerializer):
    pharmacy_name = serializers.CharField(source="pharmacy.name", read_only=True)
    patient_name = serializers.CharField(source="patient.get_full_name", read_only=True)
    prescription_number = serializers.CharField(
        source="prescription.prescription_number", read_only=True
    )
    total_cost = serializers.ReadOnlyField()

    class Meta:
        model = DeliveryOrder
        fields = [
            "id", "prescription", "prescription_number",
            "pharmacy", "pharmacy_name",
            "patient", "patient_name",
            "order_number", "status", "delivery_type",
            "delivery_address", "delivery_instructions",
            "delivery_fee", "medication_cost",
            "insurance_covered", "patient_copay", "total_cost",
            "tracking_number", "estimated_delivery", "actual_delivery",
            "confirmed_at", "prepared_at", "shipped_at", "delivered_at",
            "notes", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "patient", "order_number",
            "confirmed_at", "prepared_at", "shipped_at", "delivered_at",
            "created_at", "updated_at",
        ]

    def create(self, validated_data):
        validated_data["patient"] = self.context["request"].user
        return super().create(validated_data)
