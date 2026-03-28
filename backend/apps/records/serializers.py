"""Serializers for the records app."""
from rest_framework import serializers

from .models import Document, HealthRecord, LabResult, Vitals


class VitalsSerializer(serializers.ModelSerializer):
    blood_pressure = serializers.ReadOnlyField()
    bmi = serializers.ReadOnlyField()
    recorded_by_name = serializers.CharField(
        source="recorded_by.get_full_name", read_only=True, default=None
    )

    class Meta:
        model = Vitals
        fields = [
            "id", "patient", "health_record", "consultation",
            "recorded_by", "recorded_by_name",
            "temperature_f", "heart_rate",
            "blood_pressure_systolic", "blood_pressure_diastolic",
            "blood_pressure", "respiratory_rate", "oxygen_saturation",
            "weight_kg", "height_cm", "blood_glucose",
            "pain_level", "bmi", "notes", "recorded_at", "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def create(self, validated_data):
        if "recorded_by" not in validated_data:
            validated_data["recorded_by"] = self.context["request"].user
        return super().create(validated_data)


class LabResultSerializer(serializers.ModelSerializer):
    ordered_by_name = serializers.CharField(
        source="ordered_by.get_full_name", read_only=True, default=None
    )
    reviewed_by_name = serializers.CharField(
        source="reviewed_by.get_full_name", read_only=True, default=None
    )
    abnormal_display = serializers.CharField(
        source="get_abnormal_flag_display", read_only=True
    )

    class Meta:
        model = LabResult
        fields = [
            "id", "patient", "health_record", "ordered_by",
            "ordered_by_name", "test_name", "test_code", "category",
            "result_value", "result_unit", "reference_range",
            "abnormal_flag", "abnormal_display", "result_status",
            "lab_name", "specimen_type", "collected_at", "resulted_at",
            "notes", "is_critical",
            "reviewed_by", "reviewed_by_name", "reviewed_at",
            "created_at",
        ]
        read_only_fields = ["id", "reviewed_by", "reviewed_at", "created_at"]


class DocumentSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(
        source="uploaded_by.get_full_name", read_only=True, default=None
    )
    type_display = serializers.CharField(
        source="get_document_type_display", read_only=True
    )

    class Meta:
        model = Document
        fields = [
            "id", "patient", "health_record", "uploaded_by",
            "uploaded_by_name", "title", "document_type", "type_display",
            "file", "original_filename", "file_size", "mime_type",
            "description", "is_confidential", "document_date",
            "created_at",
        ]
        read_only_fields = ["id", "uploaded_by", "file_size", "created_at"]

    def create(self, validated_data):
        validated_data["uploaded_by"] = self.context["request"].user
        file_obj = validated_data.get("file")
        if file_obj:
            validated_data["file_size"] = file_obj.size
            if not validated_data.get("original_filename"):
                validated_data["original_filename"] = file_obj.name
            validated_data["mime_type"] = getattr(file_obj, "content_type", "")
        return super().create(validated_data)


class HealthRecordSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(
        source="doctor.get_full_name", read_only=True, default=None
    )
    patient_name = serializers.CharField(
        source="patient.get_full_name", read_only=True
    )
    vitals = VitalsSerializer(many=True, read_only=True)
    lab_results = LabResultSerializer(many=True, read_only=True)
    documents = DocumentSerializer(many=True, read_only=True)
    type_display = serializers.CharField(
        source="get_record_type_display", read_only=True
    )

    class Meta:
        model = HealthRecord
        fields = [
            "id", "patient", "patient_name", "doctor", "doctor_name",
            "consultation", "record_type", "type_display",
            "title", "summary", "details", "diagnosis_codes",
            "is_confidential", "record_date",
            "vitals", "lab_results", "documents",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def create(self, validated_data):
        if "doctor" not in validated_data:
            user = self.context["request"].user
            if user.is_doctor:
                validated_data["doctor"] = user
        return super().create(validated_data)


class HealthRecordListSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(
        source="doctor.get_full_name", read_only=True, default=None
    )
    type_display = serializers.CharField(
        source="get_record_type_display", read_only=True
    )

    class Meta:
        model = HealthRecord
        fields = [
            "id", "patient", "doctor_name", "record_type",
            "type_display", "title", "record_date",
            "is_confidential", "created_at",
        ]
