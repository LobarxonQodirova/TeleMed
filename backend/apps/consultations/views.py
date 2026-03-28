"""Views for consultations app."""
import uuid
from datetime import timedelta

from django.db.models import Q
from django.utils import timezone
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Consultation, ConsultationFile, ConsultationNote, VideoSession
from .serializers import (
    ConsultationFileSerializer,
    ConsultationListSerializer,
    ConsultationNoteSerializer,
    ConsultationSerializer,
    VideoSessionSerializer,
)
from .tasks import send_consultation_reminder


class IsConsultationParticipant(permissions.BasePermission):
    """Allow access only to the doctor or patient in the consultation."""

    def has_object_permission(self, request, view, obj):
        return request.user in (obj.doctor, obj.patient)


class ConsultationViewSet(viewsets.ModelViewSet):
    """CRUD + workflow actions for consultations."""

    serializer_class = ConsultationSerializer
    permission_classes = [permissions.IsAuthenticated, IsConsultationParticipant]
    lookup_field = "id"

    def get_queryset(self):
        user = self.request.user
        qs = Consultation.objects.select_related("doctor", "patient", "appointment")
        if user.is_doctor:
            qs = qs.filter(doctor=user)
        else:
            qs = qs.filter(patient=user)

        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)

        date_from = self.request.query_params.get("date_from")
        if date_from:
            qs = qs.filter(scheduled_at__date__gte=date_from)

        date_to = self.request.query_params.get("date_to")
        if date_to:
            qs = qs.filter(scheduled_at__date__lte=date_to)
        return qs

    def get_serializer_class(self):
        if self.action == "list":
            return ConsultationListSerializer
        return ConsultationSerializer

    @action(detail=True, methods=["post"])
    def join_waiting_room(self, request, id=None):
        """Patient joins the waiting room."""
        consultation = self.get_object()
        if request.user != consultation.patient:
            return Response(
                {"detail": "Only the patient can join the waiting room."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if consultation.status not in (Consultation.Status.SCHEDULED,):
            return Response(
                {"detail": "Cannot join waiting room at this stage."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        waiting = Consultation.objects.filter(
            doctor=consultation.doctor,
            status=Consultation.Status.WAITING,
        ).count()
        consultation.status = Consultation.Status.WAITING
        consultation.queue_position = waiting + 1
        consultation.save(update_fields=["status", "queue_position", "updated_at"])

        return Response({
            "message": "You have joined the waiting room.",
            "queue_position": consultation.queue_position,
        })

    @action(detail=True, methods=["post"])
    def start(self, request, id=None):
        """Doctor starts the consultation."""
        consultation = self.get_object()
        if request.user != consultation.doctor:
            return Response(
                {"detail": "Only the doctor can start the consultation."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if consultation.status not in (
            Consultation.Status.SCHEDULED,
            Consultation.Status.WAITING,
        ):
            return Response(
                {"detail": "Consultation cannot be started from its current status."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        now = timezone.now()
        session_token = str(uuid.uuid4())
        consultation.status = Consultation.Status.IN_PROGRESS
        consultation.started_at = now
        consultation.queue_position = None
        consultation.save(
            update_fields=["status", "started_at", "queue_position", "updated_at"]
        )

        video_session = VideoSession.objects.create(
            consultation=consultation,
            session_token=session_token,
            status=VideoSession.Status.ACTIVE,
            started_at=now,
            doctor_joined_at=now,
        )

        # Shift queue positions for remaining waiting patients
        Consultation.objects.filter(
            doctor=consultation.doctor,
            status=Consultation.Status.WAITING,
            queue_position__gt=0,
        ).update(queue_position=models.F("queue_position") - 1)

        return Response({
            "message": "Consultation started.",
            "session_token": session_token,
            "video_session": VideoSessionSerializer(video_session).data,
        })

    @action(detail=True, methods=["post"])
    def end(self, request, id=None):
        """End an active consultation."""
        consultation = self.get_object()
        if consultation.status != Consultation.Status.IN_PROGRESS:
            return Response(
                {"detail": "Consultation is not currently in progress."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        now = timezone.now()
        consultation.status = Consultation.Status.COMPLETED
        consultation.ended_at = now
        if consultation.started_at:
            delta = now - consultation.started_at
            consultation.duration_minutes = int(delta.total_seconds() / 60)
        consultation.save(
            update_fields=["status", "ended_at", "duration_minutes", "updated_at"]
        )

        # End active video sessions
        VideoSession.objects.filter(
            consultation=consultation,
            status=VideoSession.Status.ACTIVE,
        ).update(status=VideoSession.Status.ENDED, ended_at=now)

        # Increment doctor's consultation count
        if hasattr(consultation.doctor, "doctor_profile"):
            profile = consultation.doctor.doctor_profile
            profile.total_consultations += 1
            profile.save(update_fields=["total_consultations"])

        return Response({"message": "Consultation ended.", "duration_minutes": consultation.duration_minutes})

    @action(detail=True, methods=["post"])
    def cancel(self, request, id=None):
        """Cancel a scheduled consultation."""
        consultation = self.get_object()
        if consultation.status not in (
            Consultation.Status.SCHEDULED,
            Consultation.Status.WAITING,
        ):
            return Response(
                {"detail": "Only scheduled or waiting consultations can be cancelled."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        consultation.status = Consultation.Status.CANCELLED
        consultation.save(update_fields=["status", "updated_at"])
        return Response({"message": "Consultation cancelled."})

    @action(detail=True, methods=["get"])
    def queue_status(self, request, id=None):
        """Return the queue position for a waiting consultation."""
        consultation = self.get_object()
        if consultation.status != Consultation.Status.WAITING:
            return Response({"queue_position": None, "estimated_wait": None})
        position = Consultation.objects.filter(
            doctor=consultation.doctor,
            status=Consultation.Status.WAITING,
            created_at__lt=consultation.created_at,
        ).count() + 1
        estimated_wait = position * 15  # rough estimate: 15 min per patient
        return Response({
            "queue_position": position,
            "estimated_wait_minutes": estimated_wait,
        })


class ConsultationNoteViewSet(viewsets.ModelViewSet):
    """CRUD for consultation notes."""

    serializer_class = ConsultationNoteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        consultation_id = self.kwargs.get("consultation_id")
        qs = ConsultationNote.objects.filter(consultation_id=consultation_id)
        user = self.request.user
        if not user.is_doctor:
            qs = qs.filter(is_private=False)
        return qs

    def perform_create(self, serializer):
        serializer.save(
            author=self.request.user,
            consultation_id=self.kwargs["consultation_id"],
        )


class ConsultationFileViewSet(viewsets.ModelViewSet):
    """Upload and list files for a consultation."""

    serializer_class = ConsultationFileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        consultation_id = self.kwargs.get("consultation_id")
        return ConsultationFile.objects.filter(consultation_id=consultation_id)

    def perform_create(self, serializer):
        serializer.save(
            uploaded_by=self.request.user,
            consultation_id=self.kwargs["consultation_id"],
        )
