"""Views for the prescriptions app."""
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Dosage, Medication, Prescription, PrescriptionRefill
from .serializers import (
    DosageSerializer,
    MedicationSerializer,
    PrescriptionListSerializer,
    PrescriptionRefillSerializer,
    PrescriptionSerializer,
)


class MedicationViewSet(viewsets.ReadOnlyModelViewSet):
    """List and search available medications."""

    queryset = Medication.objects.filter(is_active=True)
    serializer_class = MedicationSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ["name", "generic_name", "drug_class"]


class PrescriptionViewSet(viewsets.ModelViewSet):
    """CRUD + workflow for prescriptions."""

    serializer_class = PrescriptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        user = self.request.user
        qs = Prescription.objects.select_related("doctor", "patient").prefetch_related(
            "dosages__medication", "refills"
        )
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
            return PrescriptionListSerializer
        return PrescriptionSerializer

    @action(detail=True, methods=["post"])
    def sign(self, request, id=None):
        """Doctor signs/activates the prescription."""
        prescription = self.get_object()
        if request.user != prescription.doctor:
            return Response(
                {"detail": "Only the prescribing doctor can sign."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if prescription.status != Prescription.Status.DRAFT:
            return Response(
                {"detail": "Only draft prescriptions can be signed."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not prescription.dosages.exists():
            return Response(
                {"detail": "Prescription must have at least one medication."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        prescription.status = Prescription.Status.ACTIVE
        prescription.signed_at = timezone.now()
        prescription.save(update_fields=["status", "signed_at", "updated_at"])

        return Response({"message": "Prescription signed and activated."})

    @action(detail=True, methods=["post"])
    def cancel(self, request, id=None):
        """Cancel a prescription."""
        prescription = self.get_object()
        if request.user != prescription.doctor:
            return Response(
                {"detail": "Only the prescribing doctor can cancel."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if prescription.status in (
            Prescription.Status.DISPENSED,
            Prescription.Status.CANCELLED,
        ):
            return Response(
                {"detail": "Cannot cancel a dispensed or already cancelled prescription."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        prescription.status = Prescription.Status.CANCELLED
        prescription.save(update_fields=["status", "updated_at"])
        return Response({"message": "Prescription cancelled."})

    @action(detail=True, methods=["post"])
    def request_refill(self, request, id=None):
        """Patient requests a refill for a prescription."""
        prescription = self.get_object()
        if request.user != prescription.patient:
            return Response(
                {"detail": "Only the patient can request refills."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if not prescription.is_refillable:
            return Response(
                {"detail": "This prescription is not refillable."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if prescription.refills_remaining <= 0:
            return Response(
                {"detail": "No refills remaining."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        refill = PrescriptionRefill.objects.create(
            prescription=prescription,
            requested_by=request.user,
        )
        return Response(
            PrescriptionRefillSerializer(refill).data,
            status=status.HTTP_201_CREATED,
        )


class DosageViewSet(viewsets.ModelViewSet):
    """CRUD for dosages within a prescription."""

    serializer_class = DosageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        prescription_id = self.kwargs.get("prescription_id")
        return Dosage.objects.filter(
            prescription_id=prescription_id
        ).select_related("medication")

    def perform_create(self, serializer):
        serializer.save(prescription_id=self.kwargs["prescription_id"])


class PrescriptionRefillViewSet(viewsets.ModelViewSet):
    """Manage refill requests for prescriptions."""

    serializer_class = PrescriptionRefillSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = PrescriptionRefill.objects.select_related(
            "prescription__doctor", "prescription__patient",
            "requested_by", "approved_by",
        )
        if user.is_doctor:
            qs = qs.filter(prescription__doctor=user)
        else:
            qs = qs.filter(requested_by=user)
        return qs

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        """Doctor approves a refill request."""
        refill = self.get_object()
        if request.user != refill.prescription.doctor:
            return Response(
                {"detail": "Only the prescribing doctor can approve refills."},
                status=status.HTTP_403_FORBIDDEN,
            )
        refill.status = PrescriptionRefill.Status.APPROVED
        refill.approved_by = request.user
        refill.approved_at = timezone.now()
        refill.save(update_fields=["status", "approved_by", "approved_at"])
        return Response(PrescriptionRefillSerializer(refill).data)

    @action(detail=True, methods=["post"])
    def deny(self, request, pk=None):
        """Doctor denies a refill request."""
        refill = self.get_object()
        if request.user != refill.prescription.doctor:
            return Response(
                {"detail": "Only the prescribing doctor can deny refills."},
                status=status.HTTP_403_FORBIDDEN,
            )
        refill.status = PrescriptionRefill.Status.DENIED
        refill.approved_by = request.user
        refill.denial_reason = request.data.get("reason", "")
        refill.save(update_fields=["status", "approved_by", "denial_reason"])
        return Response(PrescriptionRefillSerializer(refill).data)
