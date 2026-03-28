"""Payment services -- Stripe integration."""
import logging

import stripe
from django.conf import settings
from django.utils import timezone

from .models import Payment, Refund

logger = logging.getLogger(__name__)


class StripePaymentService:
    """Service class for Stripe payment operations."""

    def __init__(self):
        stripe.api_key = settings.STRIPE_SECRET_KEY

    def create_payment_intent(self, user, appointment_id=None, consultation_id=None, payment_method="credit_card"):
        """Create a Stripe PaymentIntent and a local Payment record."""
        from apps.appointments.models import Appointment
        from apps.consultations.models import Consultation

        appointment = None
        consultation = None
        doctor = None
        amount = 0

        if appointment_id:
            try:
                appointment = Appointment.objects.select_related("doctor").get(
                    id=appointment_id, patient=user
                )
                doctor = appointment.doctor
                amount = float(appointment.fee)
            except Appointment.DoesNotExist:
                raise ValueError("Appointment not found or does not belong to you.")

        elif consultation_id:
            try:
                consultation = Consultation.objects.select_related("doctor").get(
                    id=consultation_id, patient=user
                )
                doctor = consultation.doctor
                if hasattr(doctor, "doctor_profile"):
                    amount = float(doctor.doctor_profile.consultation_fee)
            except Consultation.DoesNotExist:
                raise ValueError("Consultation not found or does not belong to you.")

        if amount <= 0:
            raise ValueError("Payment amount must be greater than zero.")

        # Create Stripe PaymentIntent
        amount_cents = int(amount * 100)
        try:
            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency="usd",
                metadata={
                    "user_id": str(user.id),
                    "appointment_id": str(appointment_id) if appointment_id else "",
                    "consultation_id": str(consultation_id) if consultation_id else "",
                },
                automatic_payment_methods={"enabled": True},
            )
        except stripe.error.StripeError as e:
            logger.error("Stripe error creating payment intent: %s", e)
            raise ValueError(f"Payment processing error: {str(e)}")

        # Create local payment record
        payment = Payment.objects.create(
            patient=user,
            doctor=doctor,
            appointment=appointment,
            consultation=consultation,
            amount=amount,
            payment_method=payment_method,
            status=Payment.Status.PROCESSING,
            stripe_payment_intent_id=intent.id,
            description=f"Payment for {'appointment' if appointment else 'consultation'}",
        )
        payment.calculate_payout()
        payment.save(update_fields=["platform_fee", "doctor_payout"])

        return {
            "payment_id": str(payment.id),
            "client_secret": intent.client_secret,
            "amount": amount,
            "currency": "usd",
        }

    def process_refund(self, refund):
        """Process a refund through Stripe."""
        payment = refund.payment
        if not payment.stripe_payment_intent_id:
            logger.warning("No Stripe payment intent for payment %s", payment.id)
            return

        amount_cents = int(float(refund.amount) * 100)
        try:
            stripe_refund = stripe.Refund.create(
                payment_intent=payment.stripe_payment_intent_id,
                amount=amount_cents,
            )
            refund.stripe_refund_id = stripe_refund.id
            refund.status = Refund.RefundStatus.COMPLETED
            refund.processed_at = timezone.now()
            refund.save(update_fields=[
                "stripe_refund_id", "status", "processed_at",
            ])

            # Update payment status
            total_refunded = sum(
                float(r.amount) for r in payment.refunds.filter(
                    status=Refund.RefundStatus.COMPLETED
                )
            )
            if total_refunded >= float(payment.amount):
                payment.status = Payment.Status.REFUNDED
            else:
                payment.status = Payment.Status.PARTIALLY_REFUNDED
            payment.save(update_fields=["status", "updated_at"])

            logger.info("Refund %s processed successfully.", refund.id)
        except stripe.error.StripeError as e:
            logger.error("Stripe refund error: %s", e)
            refund.status = Refund.RefundStatus.FAILED
            refund.notes = str(e)
            refund.save(update_fields=["status", "notes"])
            raise

    def handle_webhook(self, payload, sig_header):
        """Handle incoming Stripe webhook events."""
        webhook_secret = settings.STRIPE_WEBHOOK_SECRET

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
        except (ValueError, stripe.error.SignatureVerificationError) as e:
            logger.error("Stripe webhook verification failed: %s", e)
            raise ValueError("Invalid webhook signature.")

        event_type = event["type"]
        data = event["data"]["object"]

        if event_type == "payment_intent.succeeded":
            self._handle_payment_succeeded(data)
        elif event_type == "payment_intent.payment_failed":
            self._handle_payment_failed(data)
        elif event_type == "charge.refunded":
            self._handle_charge_refunded(data)

        logger.info("Handled Stripe webhook: %s", event_type)

    def _handle_payment_succeeded(self, data):
        """Mark payment as completed when Stripe confirms success."""
        try:
            payment = Payment.objects.get(stripe_payment_intent_id=data["id"])
            payment.status = Payment.Status.COMPLETED
            payment.stripe_charge_id = data.get("latest_charge", "")
            payment.paid_at = timezone.now()
            payment.receipt_url = data.get("charges", {}).get("data", [{}])[0].get("receipt_url", "")
            payment.save(update_fields=[
                "status", "stripe_charge_id", "paid_at",
                "receipt_url", "updated_at",
            ])
            logger.info("Payment %s completed.", payment.id)
        except Payment.DoesNotExist:
            logger.warning("Payment not found for intent %s", data["id"])

    def _handle_payment_failed(self, data):
        """Mark payment as failed."""
        try:
            payment = Payment.objects.get(stripe_payment_intent_id=data["id"])
            payment.status = Payment.Status.FAILED
            payment.save(update_fields=["status", "updated_at"])
            logger.info("Payment %s failed.", payment.id)
        except Payment.DoesNotExist:
            logger.warning("Payment not found for intent %s", data["id"])

    def _handle_charge_refunded(self, data):
        """Handle charge.refunded event from Stripe."""
        logger.info("Charge refunded: %s", data.get("id"))
