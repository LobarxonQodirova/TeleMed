"""URL configuration for patients app."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "patients"

router = DefaultRouter()
router.register(r"", views.PatientViewSet, basename="patient")

urlpatterns = [
    path("medical-profile/", views.MedicalProfileView.as_view(), name="medical-profile"),
    path("allergies/", views.AllergyViewSet.as_view({"get": "list", "post": "create"}), name="allergies"),
    path("allergies/<uuid:pk>/", views.AllergyViewSet.as_view({"get": "retrieve", "put": "update", "delete": "destroy"}), name="allergy-detail"),
    path("insurance/", views.InsuranceInfoViewSet.as_view({"get": "list", "post": "create"}), name="insurance-list"),
    path("insurance/<uuid:pk>/", views.InsuranceInfoViewSet.as_view({"get": "retrieve", "put": "update", "delete": "destroy"}), name="insurance-detail"),
    path("insurance/<uuid:pk>/set-primary/", views.InsuranceInfoViewSet.as_view({"post": "set_primary"}), name="insurance-set-primary"),
    path("", include(router.urls)),
]
