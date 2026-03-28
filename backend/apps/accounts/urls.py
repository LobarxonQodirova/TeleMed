"""URL configuration for accounts app."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

app_name = "accounts"

router = DefaultRouter()
router.register(r"doctors", views.DoctorProfileViewSet, basename="doctor")
router.register(r"specialties", views.SpecialtyViewSet, basename="specialty")

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="register"),
    path("register/doctor/", views.DoctorRegisterView.as_view(), name="register-doctor"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("me/", views.MeView.as_view(), name="me"),
    path("change-password/", views.ChangePasswordView.as_view(), name="change-password"),
    path("patient-profile/", views.PatientProfileView.as_view(), name="patient-profile"),
    path("", include(router.urls)),
]
