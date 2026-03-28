"""Serializers for accounts app."""
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import DoctorProfile, PatientProfile, Specialty

User = get_user_model()


class SpecialtySerializer(serializers.ModelSerializer):
    doctor_count = serializers.SerializerMethodField()

    class Meta:
        model = Specialty
        fields = ["id", "name", "slug", "description", "icon", "doctor_count"]

    def get_doctor_count(self, obj):
        return obj.doctors.filter(is_available=True).count()


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "email", "username", "first_name", "last_name",
            "full_name", "role", "phone", "avatar", "date_of_birth",
            "is_verified", "created_at",
        ]
        read_only_fields = ["id", "email", "role", "is_verified", "created_at"]

    def get_full_name(self, obj):
        return obj.get_full_name()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=[("patient", "Patient"), ("doctor", "Doctor")])

    class Meta:
        model = User
        fields = [
            "email", "username", "first_name", "last_name",
            "password", "password_confirm", "role", "phone",
        ]

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        if user.role == User.Role.PATIENT:
            PatientProfile.objects.create(user=user)
        return user


class DoctorRegistrationSerializer(RegisterSerializer):
    license_number = serializers.CharField(max_length=50)
    qualification = serializers.CharField(max_length=255)
    specialty_ids = serializers.ListField(
        child=serializers.UUIDField(), write_only=True, required=False
    )

    class Meta(RegisterSerializer.Meta):
        fields = RegisterSerializer.Meta.fields + [
            "license_number", "qualification", "specialty_ids",
        ]

    def create(self, validated_data):
        license_number = validated_data.pop("license_number")
        qualification = validated_data.pop("qualification")
        specialty_ids = validated_data.pop("specialty_ids", [])
        validated_data["role"] = User.Role.DOCTOR

        user = User.objects.create_user(**validated_data)
        profile = DoctorProfile.objects.create(
            user=user,
            license_number=license_number,
            qualification=qualification,
        )
        if specialty_ids:
            specialties = Specialty.objects.filter(id__in=specialty_ids)
            profile.specialties.set(specialties)
        return user


class PatientProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = PatientProfile
        fields = [
            "id", "user", "gender", "blood_group", "height_cm", "weight_kg",
            "allergies", "chronic_conditions", "current_medications",
            "emergency_contact_name", "emergency_contact_phone",
            "insurance_provider", "insurance_id",
            "address", "city", "state", "country",
        ]
        read_only_fields = ["id"]


class DoctorProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    specialties = SpecialtySerializer(many=True, read_only=True)
    specialty_ids = serializers.ListField(
        child=serializers.UUIDField(), write_only=True, required=False
    )

    class Meta:
        model = DoctorProfile
        fields = [
            "id", "user", "specialties", "specialty_ids",
            "license_number", "license_expiry", "qualification",
            "experience_years", "bio", "consultation_fee", "follow_up_fee",
            "average_rating", "total_reviews", "total_consultations",
            "is_available", "is_accepting_patients", "languages",
            "hospital_affiliation", "address", "city", "state", "country",
        ]
        read_only_fields = [
            "id", "average_rating", "total_reviews", "total_consultations",
        ]

    def update(self, instance, validated_data):
        specialty_ids = validated_data.pop("specialty_ids", None)
        instance = super().update(instance, validated_data)
        if specialty_ids is not None:
            specialties = Specialty.objects.filter(id__in=specialty_ids)
            instance.specialties.set(specialties)
        return instance


class DoctorListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for doctor listings."""

    full_name = serializers.CharField(source="user.get_full_name")
    avatar = serializers.ImageField(source="user.avatar")
    specialties = SpecialtySerializer(many=True, read_only=True)

    class Meta:
        model = DoctorProfile
        fields = [
            "id", "full_name", "avatar", "specialties",
            "qualification", "experience_years", "consultation_fee",
            "average_rating", "total_reviews", "is_available",
            "city", "state", "hospital_affiliation",
        ]


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value
