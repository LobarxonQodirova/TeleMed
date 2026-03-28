"""Views for the patients app."""
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Allergy, InsuranceInfo, MedicalProfile, Patient
from .serializers import (
    AllergySerializer,
    InsuranceInfoSerializer,
    MedicalProfileSerializer,
    PatientListSerializer,
    PatientSerializer,
)


class IsPatientOwnerOrDoctor(permissions.BasePermission):
    """Allow access to the patient themselves or their treating doctor."""

    def has_object_permission(self, request, view, obj):
        user = request.user
        if hasattr(obj, "user"):
            return obj.user == user or user.is_doctor
        if hasattr(obj, "patient"):
            return obj.patient.user == user or user.is_doctor
        return False


class PatientViewSet(viewsets.ModelViewSet):
    """CRUD for patient records. Doctors can view their patients."""

    serializer_class = PatientSerializer
    permission_classes = [permissions.IsAuthenticated, IsPatientOwnerOrDoctor]
    lookup_field = "id"

    def get_queryset(self):
        user = self.request.user
        qs = Patient.objects.select_related(
            "user", "medical_profile", "primary_physician"
        ).prefetch_related("allergies", "insurance_records")

        if user.is_doctor:
            return qs
        return qs.filter(user=user)

    def get_serializer_class(self):
        if self.action == "list":
            return PatientListSerializer
        return PatientSerializer

    @action(detail=False, methods=["get", "put", "patch"])
    def me(self, request):
        """Get or update the current patient's record."""
        if not request.user.is_patient:
            return Response(
                {"detail": "Only patients can access this endpoint."},
                status=status.HTTP_403_FORBIDDEN,
            )
        patient, created = Patient.objects.get_or_create(user=request.user)
        if request.method == "GET":
            return Response(PatientSerializer(patient).data)

        serializer = PatientSerializer(patient, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class MedicalProfileView(generics.RetrieveUpdateAPIView):
    """Retrieve or update a patient's medical profile."""

    serializer_class = MedicalProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsPatientOwnerOrDoctor]

    def get_object(self):
        patient = Patient.objects.get(user=self.request.user)
        profile, _ = MedicalProfile.objects.get_or_create(patient=patient)
        return profile


class AllergyViewSet(viewsets.ModelViewSet):
    """CRUD for patient allergies."""

    serializer_class = AllergySerializer
    permission_classes = [permissions.IsAuthenticated, IsPatientOwnerOrDoctor]

    def get_queryset(self):
        user = self.request.user
        if user.is_patient:
            return Allergy.objects.filter(patient__user=user)
        patient_id = self.kwargs.get("patient_id")
        if patient_id:
            return Allergy.objects.filter(patient_id=patient_id)
        return Allergy.objects.none()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.request.user.is_patient:
            patient, _ = Patient.objects.get_or_create(user=self.request.user)
            context["patient"] = patient
        return context


class InsuranceInfoViewSet(viewsets.ModelViewSet):
    """CRUD for patient insurance records."""

    serializer_class = InsuranceInfoSerializer
    permission_classes = [permissions.IsAuthenticated, IsPatientOwnerOrDoctor]

    def get_queryset(self):
        user = self.request.user
        if user.is_patient:
            return InsuranceInfo.objects.filter(patient__user=user)
        patient_id = self.kwargs.get("patient_id")
        if patient_id:
            return InsuranceInfo.objects.filter(patient_id=patient_id)
        return InsuranceInfo.objects.none()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.request.user.is_patient:
            patient, _ = Patient.objects.get_or_create(user=self.request.user)
            context["patient"] = patient
        return context

    @action(detail=True, methods=["post"])
    def set_primary(self, request, pk=None):
        """Set an insurance record as the primary one."""
        insurance = self.get_object()
        InsuranceInfo.objects.filter(
            patient=insurance.patient, is_primary=True
        ).update(is_primary=False)
        insurance.is_primary = True
        insurance.save(update_fields=["is_primary", "updated_at"])
        return Response(InsuranceInfoSerializer(insurance).data)
