"""Views for the appointments app."""
from datetime import date, datetime, timedelta

from django.db.models import Q
from django.utils import timezone
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Appointment, Cancellation, TimeSlot
from .serializers import (
    AppointmentListSerializer,
    AppointmentSerializer,
    CancellationSerializer,
    RescheduleSerializer,
    TimeSlotSerializer,
)


class IsAppointmentParticipant(permissions.BasePermission):
    """Only the patient or doctor in the appointment can access it."""

    def has_object_permission(self, request, view, obj):
        return request.user in (obj.patient, obj.doctor)


class TimeSlotViewSet(viewsets.ModelViewSet):
    """CRUD for time slots."""

    serializer_class = TimeSlotSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = TimeSlot.objects.select_related("doctor")
        doctor_id = self.request.query_params.get("doctor_id")
        if doctor_id:
            qs = qs.filter(doctor_id=doctor_id)
        target_date = self.request.query_params.get("date")
        if target_date:
            qs = qs.filter(date=target_date)
        available_only = self.request.query_params.get("available")
        if available_only and available_only.lower() == "true":
            qs = qs.filter(status=TimeSlot.SlotStatus.AVAILABLE)
        # Don't show past slots
        qs = qs.filter(date__gte=date.today())
        return qs

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        if self.request.user.is_doctor:
            serializer.save(doctor=self.request.user)
        else:
            serializer.save()

    @action(detail=False, methods=["post"])
    def generate(self, request):
        """Generate time slots from a doctor's schedule for a date range."""
        from apps.doctors.models import DoctorSchedule

        if not request.user.is_doctor:
            return Response(
                {"detail": "Only doctors can generate slots."},
                status=status.HTTP_403_FORBIDDEN,
            )

        start_date = request.data.get("start_date")
        end_date = request.data.get("end_date")

        if not start_date or not end_date:
            return Response(
                {"detail": "start_date and end_date are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            return Response(
                {"detail": "Invalid date format. Use YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if end_date < start_date:
            return Response(
                {"detail": "end_date must be after start_date."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        schedules = DoctorSchedule.objects.filter(
            doctor=request.user.doctor_profile, is_active=True
        )

        created_slots = []
        current_date = start_date
        while current_date <= end_date:
            day_schedules = schedules.filter(day_of_week=current_date.weekday())
            for schedule in day_schedules:
                current_time = datetime.combine(current_date, schedule.start_time)
                end_time = datetime.combine(current_date, schedule.end_time)
                delta = timedelta(minutes=schedule.slot_duration_minutes)

                while current_time + delta <= end_time:
                    if schedule.break_start and schedule.break_end:
                        break_s = datetime.combine(current_date, schedule.break_start)
                        break_e = datetime.combine(current_date, schedule.break_end)
                        if break_s <= current_time < break_e:
                            current_time = break_e
                            continue

                    slot, created = TimeSlot.objects.get_or_create(
                        doctor=request.user,
                        date=current_date,
                        start_time=current_time.time(),
                        defaults={
                            "end_time": (current_time + delta).time(),
                            "schedule": schedule,
                            "max_bookings": schedule.max_patients,
                            "consultation_types": schedule.consultation_types,
                        },
                    )
                    if created:
                        created_slots.append(slot)
                    current_time += delta
            current_date += timedelta(days=1)

        return Response(
            {
                "message": f"Generated {len(created_slots)} time slots.",
                "slots": TimeSlotSerializer(created_slots, many=True).data,
            },
            status=status.HTTP_201_CREATED,
        )


class AppointmentViewSet(viewsets.ModelViewSet):
    """CRUD + workflow actions for appointments."""

    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsAppointmentParticipant]
    lookup_field = "id"

    def get_queryset(self):
        user = self.request.user
        qs = Appointment.objects.select_related("patient", "doctor", "time_slot")

        if user.is_doctor:
            qs = qs.filter(doctor=user)
        else:
            qs = qs.filter(patient=user)

        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)

        date_from = self.request.query_params.get("date_from")
        if date_from:
            qs = qs.filter(scheduled_date__gte=date_from)

        date_to = self.request.query_params.get("date_to")
        if date_to:
            qs = qs.filter(scheduled_date__lte=date_to)

        appt_type = self.request.query_params.get("type")
        if appt_type:
            qs = qs.filter(appointment_type=appt_type)

        return qs

    def get_serializer_class(self):
        if self.action == "list":
            return AppointmentListSerializer
        return AppointmentSerializer

    @action(detail=True, methods=["post"])
    def confirm(self, request, id=None):
        """Doctor confirms an appointment."""
        appointment = self.get_object()
        if request.user != appointment.doctor:
            return Response(
                {"detail": "Only the doctor can confirm appointments."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if appointment.status != Appointment.Status.PENDING:
            return Response(
                {"detail": "Only pending appointments can be confirmed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        appointment.status = Appointment.Status.CONFIRMED
        appointment.confirmed_at = timezone.now()
        appointment.save(update_fields=["status", "confirmed_at", "updated_at"])

        return Response({"message": "Appointment confirmed.", "status": appointment.status})

    @action(detail=True, methods=["post"])
    def check_in(self, request, id=None):
        """Patient checks in for an appointment."""
        appointment = self.get_object()
        if request.user != appointment.patient:
            return Response(
                {"detail": "Only the patient can check in."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if appointment.status != Appointment.Status.CONFIRMED:
            return Response(
                {"detail": "Only confirmed appointments can be checked in."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        appointment.status = Appointment.Status.CHECKED_IN
        appointment.checked_in_at = timezone.now()
        appointment.save(update_fields=["status", "checked_in_at", "updated_at"])

        return Response({"message": "Checked in successfully.", "status": appointment.status})

    @action(detail=True, methods=["post"])
    def cancel(self, request, id=None):
        """Cancel an appointment."""
        appointment = self.get_object()
        if appointment.status in (
            Appointment.Status.COMPLETED,
            Appointment.Status.CANCELLED,
        ):
            return Response(
                {"detail": "Cannot cancel a completed or already cancelled appointment."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = CancellationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cancelled_by = "doctor" if request.user == appointment.doctor else "patient"
        Cancellation.objects.create(
            appointment=appointment,
            cancelled_by=cancelled_by,
            cancelled_by_user=request.user,
            reason=serializer.validated_data.get("reason", "other"),
            reason_detail=serializer.validated_data.get("reason_detail", ""),
            refund_requested=serializer.validated_data.get("refund_requested", False),
        )

        appointment.status = Appointment.Status.CANCELLED
        appointment.save(update_fields=["status", "updated_at"])

        # Free up the time slot
        if appointment.time_slot:
            slot = appointment.time_slot
            slot.current_bookings = max(0, slot.current_bookings - 1)
            if slot.current_bookings == 0:
                slot.status = TimeSlot.SlotStatus.AVAILABLE
            slot.save(update_fields=["current_bookings", "status"])

        return Response({"message": "Appointment cancelled."})

    @action(detail=True, methods=["post"])
    def reschedule(self, request, id=None):
        """Reschedule an appointment."""
        appointment = self.get_object()
        if appointment.status in (
            Appointment.Status.COMPLETED,
            Appointment.Status.CANCELLED,
        ):
            return Response(
                {"detail": "Cannot reschedule a completed or cancelled appointment."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = RescheduleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Free old time slot
        if appointment.time_slot:
            old_slot = appointment.time_slot
            old_slot.current_bookings = max(0, old_slot.current_bookings - 1)
            if old_slot.current_bookings == 0:
                old_slot.status = TimeSlot.SlotStatus.AVAILABLE
            old_slot.save(update_fields=["current_bookings", "status"])

        appointment.scheduled_date = serializer.validated_data["new_date"]
        appointment.scheduled_time = serializer.validated_data["new_time"]
        appointment.status = Appointment.Status.RESCHEDULED
        appointment.time_slot = None
        appointment.save(update_fields=[
            "scheduled_date", "scheduled_time", "status", "time_slot", "updated_at"
        ])

        return Response({
            "message": "Appointment rescheduled.",
            "new_date": str(appointment.scheduled_date),
            "new_time": str(appointment.scheduled_time),
        })

    @action(detail=False, methods=["get"])
    def upcoming(self, request):
        """Return the next 5 upcoming appointments."""
        today = date.today()
        qs = self.get_queryset().filter(
            scheduled_date__gte=today,
            status__in=["pending", "confirmed", "checked_in"],
        ).order_by("scheduled_date", "scheduled_time")[:5]
        return Response(AppointmentListSerializer(qs, many=True).data)
