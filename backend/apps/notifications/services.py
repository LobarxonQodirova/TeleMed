"""Notification service for creating and dispatching notifications."""
import logging

from django.conf import settings

from .models import Notification

logger = logging.getLogger(__name__)


class NotificationService:
    """Centralized service for creating and sending notifications."""

    def create_notification(
        self,
        recipient,
        notification_type,
        title,
        message,
        data=None,
        channel="in_app",
        send_email=False,
    ):
        """Create a notification and optionally dispatch it."""
        notification = Notification.objects.create(
            recipient=recipient,
            notification_type=notification_type,
            channel=channel,
            title=title,
            message=message,
            data=data or {},
        )

        if send_email or channel == "email":
            from .tasks import send_email_notification
            send_email_notification.delay(str(notification.id))

        logger.info(
            "Created notification '%s' for user %s",
            notification_type,
            recipient.email,
        )
        return notification

    def notify_appointment_confirmed(self, appointment):
        """Notify patient when their appointment is confirmed."""
        self.create_notification(
            recipient=appointment.patient,
            notification_type="appointment_confirmed",
            title="Appointment Confirmed",
            message=(
                f"Your appointment with Dr. {appointment.doctor.get_full_name()} "
                f"on {appointment.scheduled_date} at {appointment.scheduled_time} "
                f"has been confirmed."
            ),
            data={"appointment_id": str(appointment.id)},
            send_email=True,
        )

    def notify_appointment_cancelled(self, appointment, cancelled_by):
        """Notify both parties when an appointment is cancelled."""
        other_party = (
            appointment.patient
            if cancelled_by == appointment.doctor
            else appointment.doctor
        )
        self.create_notification(
            recipient=other_party,
            notification_type="appointment_cancelled",
            title="Appointment Cancelled",
            message=(
                f"Your appointment on {appointment.scheduled_date} at "
                f"{appointment.scheduled_time} has been cancelled by "
                f"{cancelled_by.get_full_name()}."
            ),
            data={"appointment_id": str(appointment.id)},
            send_email=True,
        )

    def notify_consultation_started(self, consultation):
        """Notify the patient that the doctor is ready."""
        self.create_notification(
            recipient=consultation.patient,
            notification_type="consultation_started",
            title="Doctor is Ready",
            message=(
                f"Dr. {consultation.doctor.get_full_name()} is ready for your "
                f"consultation. Please join now."
            ),
            data={"consultation_id": str(consultation.id)},
        )

    def notify_prescription_ready(self, prescription):
        """Notify the patient that a prescription has been issued."""
        self.create_notification(
            recipient=prescription.patient,
            notification_type="prescription_ready",
            title="New Prescription",
            message=(
                f"Dr. {prescription.doctor.get_full_name()} has issued a new "
                f"prescription ({prescription.prescription_number}). "
                f"View it in your records."
            ),
            data={"prescription_id": str(prescription.id)},
            send_email=True,
        )

    def notify_refill_approved(self, refill):
        """Notify patient that a refill request was approved."""
        self.create_notification(
            recipient=refill.requested_by,
            notification_type="refill_approved",
            title="Refill Approved",
            message=(
                f"Your refill request for prescription "
                f"{refill.prescription.prescription_number} has been approved."
            ),
            data={"prescription_id": str(refill.prescription.id)},
            send_email=True,
        )

    def notify_refill_denied(self, refill):
        """Notify patient that a refill request was denied."""
        self.create_notification(
            recipient=refill.requested_by,
            notification_type="refill_denied",
            title="Refill Denied",
            message=(
                f"Your refill request for prescription "
                f"{refill.prescription.prescription_number} has been denied. "
                f"Reason: {refill.denial_reason or 'Not specified'}"
            ),
            data={"prescription_id": str(refill.prescription.id)},
            send_email=True,
        )

    def notify_lab_results_available(self, lab_result):
        """Notify patient that lab results are available."""
        self.create_notification(
            recipient=lab_result.patient,
            notification_type="lab_results",
            title="Lab Results Available",
            message=(
                f"Your lab results for '{lab_result.test_name}' are now available. "
                f"View them in your health records."
            ),
            data={"lab_result_id": str(lab_result.id)},
            send_email=True,
        )

    def notify_payment_received(self, payment):
        """Notify doctor of payment received."""
        self.create_notification(
            recipient=payment.doctor,
            notification_type="payment_received",
            title="Payment Received",
            message=(
                f"Payment of ${payment.amount} received from "
                f"{payment.patient.get_full_name()}."
            ),
            data={"payment_id": str(payment.id)},
        )

    def notify_delivery_update(self, delivery_order):
        """Notify patient of delivery order status update."""
        self.create_notification(
            recipient=delivery_order.patient,
            notification_type="delivery_update",
            title=f"Delivery Update: {delivery_order.get_status_display()}",
            message=(
                f"Your prescription delivery (Order #{delivery_order.order_number}) "
                f"status has been updated to: {delivery_order.get_status_display()}."
            ),
            data={"order_id": str(delivery_order.id)},
        )

    def notify_new_review(self, review):
        """Notify doctor of a new review."""
        self.create_notification(
            recipient=review.doctor.user,
            notification_type="new_review",
            title="New Review Received",
            message=(
                f"You received a new {review.overall_rating}-star review"
                f"{' from ' + review.patient.get_full_name() if not review.is_anonymous else ''}."
            ),
            data={"review_id": str(review.id)},
        )

    @staticmethod
    def get_unread_count(user):
        """Return the count of unread notifications for a user."""
        return Notification.objects.filter(
            recipient=user, is_read=False
        ).count()

    @staticmethod
    def mark_all_read(user):
        """Mark all notifications as read for a user."""
        from django.utils import timezone
        Notification.objects.filter(
            recipient=user, is_read=False
        ).update(is_read=True, read_at=timezone.now())
