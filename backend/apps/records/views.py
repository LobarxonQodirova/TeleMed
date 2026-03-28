"""Views for the records app."""
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Document, HealthRecord, LabResult, Vitals
from .serializers import (
    DocumentSerializer,
    HealthRecordListSerializer,
    HealthRecordSerializer,
    LabResultSerializer,
    VitalsSerializer,
)


class IsRecordOwnerOrDoctor(permissions.BasePermission):
    """Allow patient to access their own records, or doctors to access any."""

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_doctor:
            return True
        return obj.patient == user


class HealthRecordViewSet(viewsets.ModelViewSet):
    """CRUD for health records."""

    serializer_class = HealthRecordSerializer
    permission_classes = [permissions.IsAuthenticated, IsRecordOwnerOrDoctor]
    lookup_field = "id"

    def get_queryset(self):
        user = self.request.user
        qs = HealthRecord.objects.select_related(
            "patient", "doctor", "consultation"
        ).prefetch_related("vitals", "lab_results", "documents")

        if not user.is_doctor:
            qs = qs.filter(patient=user, is_confidential=False)
        else:
            patient_id = self.request.query_params.get("patient_id")
            if patient_id:
                qs = qs.filter(patient_id=patient_id)

        record_type = self.request.query_params.get("type")
        if record_type:
            qs = qs.filter(record_type=record_type)

        date_from = self.request.query_params.get("date_from")
        if date_from:
            qs = qs.filter(record_date__gte=date_from)

        date_to = self.request.query_params.get("date_to")
        if date_to:
            qs = qs.filter(record_date__lte=date_to)

        return qs

    def get_serializer_class(self):
        if self.action == "list":
            return HealthRecordListSerializer
        return HealthRecordSerializer


class VitalsViewSet(viewsets.ModelViewSet):
    """CRUD for vitals records."""

    serializer_class = VitalsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Vitals.objects.select_related("patient", "recorded_by")

        if not user.is_doctor:
            qs = qs.filter(patient=user)
        else:
            patient_id = self.request.query_params.get("patient_id")
            if patient_id:
                qs = qs.filter(patient_id=patient_id)

        return qs

    @action(detail=False, methods=["get"])
    def latest(self, request):
        """Return the most recent vitals for the current user or a specified patient."""
        patient_id = request.query_params.get("patient_id")
        if patient_id and request.user.is_doctor:
            vital = Vitals.objects.filter(patient_id=patient_id).first()
        else:
            vital = Vitals.objects.filter(patient=request.user).first()

        if not vital:
            return Response({"detail": "No vitals found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(VitalsSerializer(vital).data)

    @action(detail=False, methods=["get"])
    def trends(self, request):
        """Return vitals trends (last 10 readings) for a patient."""
        patient_id = request.query_params.get("patient_id")
        if patient_id and request.user.is_doctor:
            vitals = Vitals.objects.filter(patient_id=patient_id)[:10]
        else:
            vitals = Vitals.objects.filter(patient=request.user)[:10]

        return Response(VitalsSerializer(vitals, many=True).data)


class LabResultViewSet(viewsets.ModelViewSet):
    """CRUD for lab results."""

    serializer_class = LabResultSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = LabResult.objects.select_related("patient", "ordered_by", "reviewed_by")

        if not user.is_doctor:
            qs = qs.filter(patient=user, result_status="completed")
        else:
            patient_id = self.request.query_params.get("patient_id")
            if patient_id:
                qs = qs.filter(patient_id=patient_id)

        return qs

    @action(detail=True, methods=["post"])
    def review(self, request, pk=None):
        """Doctor marks a lab result as reviewed."""
        lab = self.get_object()
        if not request.user.is_doctor:
            return Response(
                {"detail": "Only doctors can review lab results."},
                status=status.HTTP_403_FORBIDDEN,
            )
        lab.reviewed_by = request.user
        lab.reviewed_at = timezone.now()
        lab.save(update_fields=["reviewed_by", "reviewed_at"])
        return Response(LabResultSerializer(lab).data)


class DocumentViewSet(viewsets.ModelViewSet):
    """Upload and manage medical documents."""

    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Document.objects.select_related("patient", "uploaded_by")

        if not user.is_doctor:
            qs = qs.filter(patient=user, is_confidential=False)
        else:
            patient_id = self.request.query_params.get("patient_id")
            if patient_id:
                qs = qs.filter(patient_id=patient_id)

        doc_type = self.request.query_params.get("type")
        if doc_type:
            qs = qs.filter(document_type=doc_type)

        return qs
