"""URL configuration for records app."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "records"

router = DefaultRouter()
router.register(r"health-records", views.HealthRecordViewSet, basename="health-record")
router.register(r"vitals", views.VitalsViewSet, basename="vitals")
router.register(r"lab-results", views.LabResultViewSet, basename="lab-result")
router.register(r"documents", views.DocumentViewSet, basename="document")

urlpatterns = [
    path("", include(router.urls)),
]
