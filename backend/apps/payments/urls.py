"""URL configuration for payments app."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "payments"

router = DefaultRouter()
router.register(r"claims", views.InsuranceClaimViewSet, basename="claim")
router.register(r"", views.PaymentViewSet, basename="payment")

urlpatterns = [
    path("webhook/stripe/", views.StripeWebhookView.as_view(), name="stripe-webhook"),
    path("", include(router.urls)),
]
