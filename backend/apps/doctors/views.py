"""Views for the doctors app."""
from datetime import date, datetime, timedelta

from django.utils import timezone
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.models import DoctorProfile

from .models import DoctorReview, DoctorSchedule, Specialization
from .serializers import (
    DoctorReviewResponseSerializer,
    DoctorReviewSerializer,
    DoctorScheduleBulkSerializer,
    DoctorScheduleSerializer,
    SpecializationSerializer,
)


class IsDoctorOwner(permissions.BasePermission):
    """Only the doctor who owns the resource can modify it."""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if hasattr(obj, "doctor"):
            return obj.doctor.user == request.user
        return False


class SpecializationViewSet(viewsets.ReadOnlyModelViewSet):
    """List and retrieve sub-specializations."""

    queryset = Specialization.objects.filter(is_active=True).select_related("specialty")
    serializer_class = SpecializationSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = super().get_queryset()
        specialty_id = self.request.query_params.get("specialty")
        if specialty_id:
            qs = qs.filter(specialty_id=specialty_id)
        return qs


class DoctorScheduleViewSet(viewsets.ModelViewSet):
    """CRUD for doctor schedule entries."""

    serializer_class = DoctorScheduleSerializer
    permission_classes = [permissions.IsAuthenticated, IsDoctorOwner]

    def get_queryset(self):
        doctor_id = self.kwargs.get("doctor_id")
        if doctor_id:
            return DoctorSchedule.objects.filter(
                doctor_id=doctor_id, is_active=True
            ).select_related("doctor__user")
        if self.request.user.is_doctor:
            return DoctorSchedule.objects.filter(
                doctor=self.request.user.doctor_profile
            ).select_related("doctor__user")
        return DoctorSchedule.objects.none()

    def perform_create(self, serializer):
        serializer.save(doctor=self.request.user.doctor_profile)

    @action(detail=False, methods=["post"])
    def bulk_create(self, request):
        """Create multiple schedule entries at once."""
        if not request.user.is_doctor:
            return Response(
                {"detail": "Only doctors can create schedules."},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = DoctorScheduleBulkSerializer(
            data=request.data,
            context={"doctor": request.user.doctor_profile},
        )
        serializer.is_valid(raise_exception=True)
        schedules = serializer.save()
        return Response(
            DoctorScheduleSerializer(schedules, many=True).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["get"])
    def available_slots(self, request):
        """Return available time slots for a specific date."""
        doctor_id = request.query_params.get("doctor_id")
        target_date = request.query_params.get("date")

        if not doctor_id or not target_date:
            return Response(
                {"detail": "Both doctor_id and date are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            target_date = datetime.strptime(target_date, "%Y-%m-%d").date()
        except ValueError:
            return Response(
                {"detail": "Invalid date format. Use YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        day_of_week = target_date.weekday()
        schedules = DoctorSchedule.objects.filter(
            doctor_id=doctor_id,
            day_of_week=day_of_week,
            is_active=True,
        )

        # Filter by effective date range
        schedules = schedules.filter(
            models.Q(effective_from__isnull=True) | models.Q(effective_from__lte=target_date),
            models.Q(effective_until__isnull=True) | models.Q(effective_until__gte=target_date),
        )

        slots = []
        for schedule in schedules:
            current = datetime.combine(target_date, schedule.start_time)
            end = datetime.combine(target_date, schedule.end_time)
            slot_delta = timedelta(minutes=schedule.slot_duration_minutes)

            while current + slot_delta <= end:
                # Skip break time
                if schedule.break_start and schedule.break_end:
                    break_start = datetime.combine(target_date, schedule.break_start)
                    break_end = datetime.combine(target_date, schedule.break_end)
                    if break_start <= current < break_end:
                        current = break_end
                        continue

                slots.append({
                    "start_time": current.strftime("%H:%M"),
                    "end_time": (current + slot_delta).strftime("%H:%M"),
                    "schedule_id": str(schedule.id),
                    "consultation_types": schedule.consultation_types,
                })
                current += slot_delta

        return Response({"date": str(target_date), "slots": slots})


class DoctorReviewViewSet(viewsets.ModelViewSet):
    """CRUD for doctor reviews."""

    serializer_class = DoctorReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        doctor_id = self.kwargs.get("doctor_id")
        qs = DoctorReview.objects.select_related("doctor__user", "patient")
        if doctor_id:
            qs = qs.filter(doctor_id=doctor_id, is_approved=True)
        else:
            user = self.request.user
            if user.is_doctor:
                qs = qs.filter(doctor=user.doctor_profile)
            else:
                qs = qs.filter(patient=user)
        return qs

    def perform_create(self, serializer):
        serializer.save(patient=self.request.user)

    @action(detail=True, methods=["post"])
    def respond(self, request, pk=None):
        """Allow the doctor to respond to a review."""
        review = self.get_object()
        if review.doctor.user != request.user:
            return Response(
                {"detail": "Only the reviewed doctor can respond."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = DoctorReviewResponseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        review.doctor_response = serializer.validated_data["response"]
        review.doctor_responded_at = timezone.now()
        review.save(update_fields=["doctor_response", "doctor_responded_at", "updated_at"])

        return Response(DoctorReviewSerializer(review).data)

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """Return rating summary for a doctor."""
        doctor_id = request.query_params.get("doctor_id")
        if not doctor_id:
            if request.user.is_doctor:
                doctor_id = request.user.doctor_profile.id
            else:
                return Response(
                    {"detail": "doctor_id is required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        from django.db.models import Avg, Count

        reviews = DoctorReview.objects.filter(doctor_id=doctor_id, is_approved=True)
        summary = reviews.aggregate(
            total_reviews=Count("id"),
            avg_overall=Avg("overall_rating"),
            avg_punctuality=Avg("punctuality_rating"),
            avg_communication=Avg("communication_rating"),
            avg_knowledge=Avg("knowledge_rating"),
        )

        # Rating distribution
        distribution = {}
        for rating in range(1, 6):
            distribution[str(rating)] = reviews.filter(overall_rating=rating).count()

        summary["distribution"] = distribution
        return Response(summary)
