"""Views for accounts app."""
from django.contrib.auth import get_user_model
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import DoctorProfile, PatientProfile, Specialty
from .serializers import (
    ChangePasswordSerializer,
    DoctorListSerializer,
    DoctorProfileSerializer,
    DoctorRegistrationSerializer,
    PatientProfileSerializer,
    RegisterSerializer,
    SpecialtySerializer,
    UserSerializer,
)

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """Register a new patient user."""

    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "message": "Registration successful.",
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class DoctorRegisterView(generics.CreateAPIView):
    """Register a new doctor user."""

    serializer_class = DoctorRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "message": "Doctor registration successful. Pending verification.",
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(TokenObtainPairView):
    """JWT token pair login endpoint."""

    permission_classes = [permissions.AllowAny]


class MeView(generics.RetrieveUpdateAPIView):
    """Retrieve or update the current user."""

    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class ChangePasswordView(generics.UpdateAPIView):
    """Change password for the authenticated user."""

    serializer_class = ChangePasswordSerializer

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save()
        return Response({"message": "Password updated successfully."})


class DoctorProfileViewSet(viewsets.ModelViewSet):
    """ViewSet for doctor profiles -- search, filter, retrieve."""

    serializer_class = DoctorProfileSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        "user__first_name", "user__last_name",
        "qualification", "hospital_affiliation", "city",
    ]
    ordering_fields = [
        "average_rating", "experience_years", "consultation_fee", "total_reviews",
    ]
    ordering = ["-average_rating"]
    lookup_field = "id"

    def get_queryset(self):
        qs = DoctorProfile.objects.select_related("user").prefetch_related("specialties")
        specialty = self.request.query_params.get("specialty")
        if specialty:
            qs = qs.filter(specialties__slug=specialty)
        min_rating = self.request.query_params.get("min_rating")
        if min_rating:
            qs = qs.filter(average_rating__gte=min_rating)
        available = self.request.query_params.get("available")
        if available and available.lower() == "true":
            qs = qs.filter(is_available=True, is_accepting_patients=True)
        city = self.request.query_params.get("city")
        if city:
            qs = qs.filter(city__icontains=city)
        fee_max = self.request.query_params.get("fee_max")
        if fee_max:
            qs = qs.filter(consultation_fee__lte=fee_max)
        return qs

    def get_serializer_class(self):
        if self.action == "list":
            return DoctorListSerializer
        return DoctorProfileSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def update(self, request, *args, **kwargs):
        profile = self.get_object()
        if profile.user != request.user:
            return Response(
                {"detail": "You can only update your own profile."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().update(request, *args, **kwargs)

    @action(detail=False, methods=["get"])
    def my_profile(self, request):
        """Return the authenticated doctor's own profile."""
        if not request.user.is_doctor:
            return Response(
                {"detail": "Only doctors have doctor profiles."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        profile = DoctorProfile.objects.get(user=request.user)
        return Response(DoctorProfileSerializer(profile).data)


class PatientProfileView(generics.RetrieveUpdateAPIView):
    """Retrieve or update the authenticated patient's profile."""

    serializer_class = PatientProfileSerializer

    def get_object(self):
        profile, _ = PatientProfile.objects.get_or_create(user=self.request.user)
        return profile


class SpecialtyViewSet(viewsets.ReadOnlyModelViewSet):
    """List and retrieve specialties."""

    queryset = Specialty.objects.filter(is_active=True)
    serializer_class = SpecialtySerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "slug"
