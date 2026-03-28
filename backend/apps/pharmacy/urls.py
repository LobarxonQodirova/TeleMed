"""URL configuration for pharmacy app."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "pharmacy"

router = DefaultRouter()
router.register(r"partners", views.PharmacyPartnerViewSet, basename="pharmacy-partner")
router.register(r"orders", views.DeliveryOrderViewSet, basename="delivery-order")

urlpatterns = [
    path("", include(router.urls)),
]
