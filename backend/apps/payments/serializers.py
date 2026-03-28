"""Serializers for the payments app."""
from rest_framework import serializers

from .models import InsuranceClaim, Payment, Refund


class RefundSerializer(serializers.ModelSerializer):
    is_full_refund = serializers.ReadOnlyField()
    processed_by_name = serializers.CharField(
        source="processed_by.get_full_name", read_only=True, default=None
    )

    class Meta:
        model = Refund
        fields = [
            "id", "payment", "amount", "reason", "reason_detail",
            "status", "stripe_refund_id", "processed_by",
            "processed_by_name", "is_full_refund",
            "requested_at", "processed_at", "notes",
        ]
        read_only_fields = [
            "id", "stripe_refund_id", "processed_by",
            "requested_at", "processed_at",
        ]


class InsuranceClaimSerializer(serializers.ModelSerializer):
    class Meta:
        model = InsuranceClaim
        fields = [
            "id", "payment", "claim_number", "insurance_provider",
            "policy_number", "member_id", "diagnosis_codes",
            "procedure_codes", "claimed_amount", "approved_amount",
            "patient_responsibility", "status", "denial_reason",
            "submitted_at", "reviewed_at", "paid_at",
            "eob_document", "notes", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "claim_number", "approved_amount",
            "patient_responsibility", "status", "denial_reason",
            "submitted_at", "reviewed_at", "paid_at",
            "created_at", "updated_at",
        ]


class PaymentSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.get_full_name", read_only=True)
    doctor_name = serializers.CharField(source="doctor.get_full_name", read_only=True)
    total_amount = serializers.ReadOnlyField()
    refunds = RefundSerializer(many=True, read_only=True)
    insurance_claim = InsuranceClaimSerializer(read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id", "patient", "patient_name", "doctor", "doctor_name",
            "appointment", "consultation",
            "amount", "currency", "total_amount", "tax_amount",
            "platform_fee", "doctor_payout",
            "payment_method", "status",
            "stripe_payment_intent_id", "description",
            "receipt_url", "metadata",
            "refunds", "insurance_claim",
            "paid_at", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "status", "stripe_payment_intent_id",
            "stripe_charge_id", "platform_fee", "doctor_payout",
            "receipt_url", "paid_at", "created_at", "updated_at",
        ]


class PaymentListSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.get_full_name", read_only=True)
    doctor_name = serializers.CharField(source="doctor.get_full_name", read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id", "patient_name", "doctor_name",
            "amount", "currency", "payment_method",
            "status", "paid_at", "created_at",
        ]


class CreatePaymentIntentSerializer(serializers.Serializer):
    """Serializer for creating a Stripe payment intent."""

    appointment_id = serializers.UUIDField(required=False)
    consultation_id = serializers.UUIDField(required=False)
    payment_method = serializers.ChoiceField(
        choices=Payment.PaymentMethod.choices,
        default="credit_card",
    )

    def validate(self, attrs):
        if not attrs.get("appointment_id") and not attrs.get("consultation_id"):
            raise serializers.ValidationError(
                "Either appointment_id or consultation_id is required."
            )
        return attrs
