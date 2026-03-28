"""Models for the patients app -- medical profile, allergies, and insurance."""
import uuid

from django.conf import settings
from django.db import models


class Patient(models.Model):
    """Extended patient record linking to the base user and medical details."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="patient_record"
    )
    medical_record_number = models.CharField(
        max_length=20, unique=True, blank=True, null=True,
        help_text="Auto-generated medical record number",
    )
    primary_physician = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="primary_patients",
    )
    preferred_pharmacy = models.ForeignKey(
        "pharmacy.PharmacyPartner",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="preferred_patients",
    )
    advance_directive = models.BooleanField(
        default=False, help_text="Whether patient has an advance directive on file"
    )
    consent_telemedicine = models.BooleanField(
        default=True, help_text="Patient consent for telemedicine services"
    )
    consent_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, help_text="Internal notes about the patient")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Patient {self.medical_record_number or self.user.get_full_name()}"

    def save(self, *args, **kwargs):
        if not self.medical_record_number:
            last = Patient.objects.order_by("-created_at").first()
            if last and last.medical_record_number:
                num = int(last.medical_record_number.replace("MRN-", "")) + 1
            else:
                num = 10001
            self.medical_record_number = f"MRN-{num}"
        super().save(*args, **kwargs)


class MedicalProfile(models.Model):
    """Detailed medical history and conditions for a patient."""

    class BloodType(models.TextChoices):
        A_POS = "A+", "A+"
        A_NEG = "A-", "A-"
        B_POS = "B+", "B+"
        B_NEG = "B-", "B-"
        AB_POS = "AB+", "AB+"
        AB_NEG = "AB-", "AB-"
        O_POS = "O+", "O+"
        O_NEG = "O-", "O-"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.OneToOneField(
        Patient, on_delete=models.CASCADE, related_name="medical_profile"
    )
    blood_type = models.CharField(max_length=5, choices=BloodType.choices, blank=True)
    height_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    weight_kg = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    bmi = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    chronic_conditions = models.JSONField(
        default=list, blank=True,
        help_text='List of chronic conditions, e.g. ["Diabetes", "Hypertension"]',
    )
    past_surgeries = models.JSONField(
        default=list, blank=True,
        help_text='List of past surgeries with dates',
    )
    family_history = models.JSONField(
        default=list, blank=True,
        help_text='Family medical history entries',
    )
    current_medications = models.JSONField(
        default=list, blank=True,
        help_text='Currently active medications',
    )
    immunizations = models.JSONField(
        default=list, blank=True,
        help_text='Immunization records',
    )
    lifestyle_smoking = models.CharField(
        max_length=20, blank=True,
        choices=[("never", "Never"), ("former", "Former"), ("current", "Current")],
    )
    lifestyle_alcohol = models.CharField(
        max_length=20, blank=True,
        choices=[("none", "None"), ("occasional", "Occasional"), ("moderate", "Moderate"), ("heavy", "Heavy")],
    )
    lifestyle_exercise = models.CharField(
        max_length=20, blank=True,
        choices=[("sedentary", "Sedentary"), ("light", "Light"), ("moderate", "Moderate"), ("active", "Active")],
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Medical profile for {self.patient}"

    def calculate_bmi(self):
        """Calculate BMI from height and weight."""
        if self.height_cm and self.weight_kg and self.height_cm > 0:
            height_m = float(self.height_cm) / 100
            self.bmi = round(float(self.weight_kg) / (height_m ** 2), 1)
        return self.bmi

    def save(self, *args, **kwargs):
        self.calculate_bmi()
        super().save(*args, **kwargs)


class Allergy(models.Model):
    """Individual allergy record for a patient."""

    class Severity(models.TextChoices):
        MILD = "mild", "Mild"
        MODERATE = "moderate", "Moderate"
        SEVERE = "severe", "Severe"
        LIFE_THREATENING = "life_threatening", "Life-Threatening"

    class AllergyType(models.TextChoices):
        DRUG = "drug", "Drug"
        FOOD = "food", "Food"
        ENVIRONMENTAL = "environmental", "Environmental"
        INSECT = "insect", "Insect"
        LATEX = "latex", "Latex"
        OTHER = "other", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="allergies"
    )
    allergen = models.CharField(max_length=200)
    allergy_type = models.CharField(
        max_length=20, choices=AllergyType.choices, default=AllergyType.OTHER
    )
    severity = models.CharField(
        max_length=20, choices=Severity.choices, default=Severity.MILD
    )
    reaction = models.TextField(blank=True, help_text="Description of allergic reaction")
    diagnosed_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "allergies"
        ordering = ["-severity", "allergen"]
        unique_together = ["patient", "allergen"]

    def __str__(self):
        return f"{self.allergen} ({self.get_severity_display()}) - {self.patient}"


class InsuranceInfo(models.Model):
    """Insurance information for a patient."""

    class PlanType(models.TextChoices):
        HMO = "hmo", "HMO"
        PPO = "ppo", "PPO"
        EPO = "epo", "EPO"
        POS = "pos", "POS"
        HDHP = "hdhp", "HDHP"
        MEDICARE = "medicare", "Medicare"
        MEDICAID = "medicaid", "Medicaid"
        OTHER = "other", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="insurance_records"
    )
    provider_name = models.CharField(max_length=200)
    plan_type = models.CharField(
        max_length=20, choices=PlanType.choices, default=PlanType.PPO
    )
    policy_number = models.CharField(max_length=50)
    group_number = models.CharField(max_length=50, blank=True)
    member_id = models.CharField(max_length=50)
    subscriber_name = models.CharField(max_length=200)
    subscriber_relationship = models.CharField(
        max_length=20, default="self",
        choices=[("self", "Self"), ("spouse", "Spouse"), ("child", "Child"), ("other", "Other")],
    )
    coverage_start = models.DateField()
    coverage_end = models.DateField(null=True, blank=True)
    copay_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    deductible_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deductible_met = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_primary = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    verification_status = models.CharField(
        max_length=20, default="pending",
        choices=[("pending", "Pending"), ("verified", "Verified"), ("denied", "Denied")],
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_primary", "-coverage_start"]
        verbose_name_plural = "insurance info"

    def __str__(self):
        return f"{self.provider_name} - {self.policy_number} ({self.patient})"

    @property
    def is_coverage_active(self):
        from datetime import date
        today = date.today()
        if self.coverage_end:
            return self.coverage_start <= today <= self.coverage_end and self.is_active
        return self.coverage_start <= today and self.is_active
