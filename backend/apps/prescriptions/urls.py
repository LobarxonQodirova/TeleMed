"""URL configuration for prescriptions app."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "prescriptions"

router = DefaultRouter()
router.register(r"medications", views.MedicationViewSet, basename="medication")
router.register(r"refills", views.PrescriptionRefillViewSet, basename="refill")
router.register(r"", views.PrescriptionViewSet, basename="prescription")

urlpatterns = [
    path(
        "<uuid:prescription_id>/dosages/",
        views.DosageViewSet.as_view({"get": "list", "post": "create"}),
        name="prescription-dosages",
    ),
    path(
        "<uuid:prescription_id>/dosages/<uuid:pk>/",
        views.DosageViewSet.as_view({
            "get": "retrieve", "put": "update",
            "patch": "partial_update", "delete": "destroy",
        }),
        name="prescription-dosage-detail",
    ),
    path("", include(router.urls)),
]
