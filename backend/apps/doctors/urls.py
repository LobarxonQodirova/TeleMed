"""URL configuration for doctors app."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "doctors"

router = DefaultRouter()
router.register(r"specializations", views.SpecializationViewSet, basename="specialization")
router.register(r"schedules", views.DoctorScheduleViewSet, basename="schedule")
router.register(r"reviews", views.DoctorReviewViewSet, basename="review")

urlpatterns = [
    path(
        "<uuid:doctor_id>/schedules/",
        views.DoctorScheduleViewSet.as_view({"get": "list"}),
        name="doctor-schedules",
    ),
    path(
        "<uuid:doctor_id>/reviews/",
        views.DoctorReviewViewSet.as_view({"get": "list", "post": "create"}),
        name="doctor-reviews",
    ),
    path("", include(router.urls)),
]
