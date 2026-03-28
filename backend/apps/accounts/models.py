"""User, profile, and specialty models for TeleMed."""
import uuid

from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class Specialty(models.Model):
    """Medical specialty (e.g., Cardiology, Dermatology)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Icon class name")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "specialties"
        ordering = ["name"]

    def __str__(self):
        return self.name


class User(AbstractUser):
    """Custom user model supporting doctor, patient, and admin roles."""

    class Role(models.TextChoices):
        PATIENT = "patient", "Patient"
        DOCTOR = "doctor", "Doctor"
        ADMIN = "admin", "Admin"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.PATIENT)
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to="avatars/%Y/%m/", blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"

    @property
    def is_doctor(self):
        return self.role == self.Role.DOCTOR

    @property
    def is_patient(self):
        return self.role == self.Role.PATIENT


class DoctorProfile(models.Model):
    """Extended profile for doctor users."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="doctor_profile")
    specialties = models.ManyToManyField(Specialty, related_name="doctors", blank=True)
    license_number = models.CharField(max_length=50, unique=True)
    license_expiry = models.DateField(null=True, blank=True)
    qualification = models.CharField(max_length=255)
    experience_years = models.PositiveIntegerField(default=0)
    bio = models.TextField(blank=True)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    follow_up_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    average_rating = models.DecimalField(
        max_digits=3, decimal_places=2, default=0,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
    )
    total_reviews = models.PositiveIntegerField(default=0)
    total_consultations = models.PositiveIntegerField(default=0)
    is_available = models.BooleanField(default=True)
    is_accepting_patients = models.BooleanField(default=True)
    languages = models.JSONField(default=list, blank=True)
    hospital_affiliation = models.CharField(max_length=255, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default="US")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-average_rating"]

    def __str__(self):
        return f"Dr. {self.user.get_full_name()} - {self.qualification}"

    def update_rating(self):
        """Recalculate average rating from reviews."""
        from apps.reviews.models import DoctorReview

        reviews = DoctorReview.objects.filter(doctor=self, is_approved=True)
        if reviews.exists():
            avg = reviews.aggregate(avg=models.Avg("overall_rating"))["avg"]
            self.average_rating = round(avg, 2)
            self.total_reviews = reviews.count()
        else:
            self.average_rating = 0
            self.total_reviews = 0
        self.save(update_fields=["average_rating", "total_reviews"])


class PatientProfile(models.Model):
    """Extended profile for patient users."""

    class BloodGroup(models.TextChoices):
        A_POS = "A+", "A+"
        A_NEG = "A-", "A-"
        B_POS = "B+", "B+"
        B_NEG = "B-", "B-"
        AB_POS = "AB+", "AB+"
        AB_NEG = "AB-", "AB-"
        O_POS = "O+", "O+"
        O_NEG = "O-", "O-"

    class Gender(models.TextChoices):
        MALE = "male", "Male"
        FEMALE = "female", "Female"
        OTHER = "other", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="patient_profile")
    gender = models.CharField(max_length=10, choices=Gender.choices, blank=True)
    blood_group = models.CharField(max_length=5, choices=BloodGroup.choices, blank=True)
    height_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    weight_kg = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    allergies = models.TextField(blank=True, help_text="Comma-separated list of allergies")
    chronic_conditions = models.TextField(blank=True)
    current_medications = models.TextField(blank=True)
    emergency_contact_name = models.CharField(max_length=150, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    insurance_provider = models.CharField(max_length=150, blank=True)
    insurance_id = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default="US")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Patient: {self.user.get_full_name()}"
