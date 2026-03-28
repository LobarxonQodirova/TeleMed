"""Views for the payments app."""
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import InsuranceClaim, Payment, Refund
from .serializers import (
    CreatePaymentIntentSerializer,
    InsuranceClaimSerializer,
    PaymentListSerializer,
    PaymentSerializer,
    RefundSerializer,
)
from .services import StripePaymentService


class PaymentViewSet(viewsets.ModelViewSet):
    """CRUD and workflow for payments."""

    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        user = self.request.user
        qs = Payment.objects.select_related(
            "patient", "doctor", "appointment", "consultation"
        ).prefetch_related("refunds")

        if user.is_doctor:
            qs = qs.filter(doctor=user)
        else:
            qs = qs.filter(patient=user)

        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    def get_serializer_class(self):
        if self.action == "list":
            return PaymentListSerializer
        return PaymentSerializer

    @action(detail=False, methods=["post"])
    def create_intent(self, request):
        """Create a Stripe payment intent for an appointment or consultation."""
        serializer = CreatePaymentIntentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = StripePaymentService()
        try:
            result = service.create_payment_intent(
                user=request.user,
                appointment_id=serializer.validated_data.get("appointment_id"),
                consultation_id=serializer.validated_data.get("consultation_id"),
                payment_method=serializer.validated_data.get("payment_method", "credit_card"),
            )
            return Response(result, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def request_refund(self, request, id=None):
        """Request a refund for a payment."""
        payment = self.get_object()
        if payment.status != Payment.Status.COMPLETED:
            return Response(
                {"detail": "Only completed payments can be refunded."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        amount = request.data.get("amount", payment.amount)
        reason = request.data.get("reason", "other")

        refund = Refund.objects.create(
            payment=payment,
            amount=amount,
            reason=reason,
            reason_detail=request.data.get("reason_detail", ""),
        )

        service = StripePaymentService()
        try:
            service.process_refund(refund)
        except Exception:
            pass  # Refund stays pending for manual processing

        return Response(RefundSerializer(refund).data, status=status.HTTP_201_CREATED)


class InsuranceClaimViewSet(viewsets.ModelViewSet):
    """CRUD for insurance claims."""

    serializer_class = InsuranceClaimSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = InsuranceClaim.objects.select_related("payment__patient", "payment__doctor")
        if user.is_doctor:
            qs = qs.filter(payment__doctor=user)
        else:
            qs = qs.filter(payment__patient=user)
        return qs


class StripeWebhookView(APIView):
    """Handle Stripe webhook events."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        service = StripePaymentService()
        try:
            service.handle_webhook(
                payload=request.body,
                sig_header=request.META.get("HTTP_STRIPE_SIGNATURE", ""),
            )
            return Response({"status": "ok"})
        except ValueError:
            return Response(
                {"detail": "Invalid payload."},
                status=status.HTTP_400_BAD_REQUEST,
            )
