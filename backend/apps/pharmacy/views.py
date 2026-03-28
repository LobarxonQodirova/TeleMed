"""Views for the pharmacy app."""
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import DeliveryOrder, PharmacyPartner
from .serializers import (
    DeliveryOrderSerializer,
    PharmacyPartnerListSerializer,
    PharmacyPartnerSerializer,
)


class PharmacyPartnerViewSet(viewsets.ReadOnlyModelViewSet):
    """List and retrieve pharmacy partners."""

    queryset = PharmacyPartner.objects.filter(is_active=True, is_verified=True)
    serializer_class = PharmacyPartnerSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ["name", "city", "state"]

    def get_serializer_class(self):
        if self.action == "list":
            return PharmacyPartnerListSerializer
        return PharmacyPartnerSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        city = self.request.query_params.get("city")
        if city:
            qs = qs.filter(city__icontains=city)
        state = self.request.query_params.get("state")
        if state:
            qs = qs.filter(state__icontains=state)
        delivery = self.request.query_params.get("delivery")
        if delivery and delivery.lower() == "true":
            qs = qs.filter(offers_delivery=True)
        insurance = self.request.query_params.get("insurance")
        if insurance and insurance.lower() == "true":
            qs = qs.filter(accepts_insurance=True)
        return qs


class DeliveryOrderViewSet(viewsets.ModelViewSet):
    """CRUD and workflow for delivery orders."""

    serializer_class = DeliveryOrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        user = self.request.user
        qs = DeliveryOrder.objects.select_related(
            "prescription", "pharmacy", "patient"
        )
        if user.is_doctor:
            qs = qs.filter(prescription__doctor=user)
        else:
            qs = qs.filter(patient=user)

        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    @action(detail=True, methods=["post"])
    def confirm(self, request, id=None):
        """Pharmacy confirms the order."""
        order = self.get_object()
        if order.status != DeliveryOrder.Status.PENDING:
            return Response(
                {"detail": "Only pending orders can be confirmed."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        order.status = DeliveryOrder.Status.CONFIRMED
        order.confirmed_at = timezone.now()
        order.save(update_fields=["status", "confirmed_at", "updated_at"])
        return Response({"message": "Order confirmed."})

    @action(detail=True, methods=["post"])
    def mark_ready(self, request, id=None):
        """Mark order as ready for pickup."""
        order = self.get_object()
        order.status = DeliveryOrder.Status.READY_FOR_PICKUP
        order.prepared_at = timezone.now()
        order.save(update_fields=["status", "prepared_at", "updated_at"])
        return Response({"message": "Order is ready for pickup."})

    @action(detail=True, methods=["post"])
    def ship(self, request, id=None):
        """Mark order as shipped/out for delivery."""
        order = self.get_object()
        tracking = request.data.get("tracking_number", "")
        order.status = DeliveryOrder.Status.OUT_FOR_DELIVERY
        order.shipped_at = timezone.now()
        if tracking:
            order.tracking_number = tracking
        order.save(update_fields=["status", "shipped_at", "tracking_number", "updated_at"])
        return Response({"message": "Order shipped.", "tracking_number": order.tracking_number})

    @action(detail=True, methods=["post"])
    def deliver(self, request, id=None):
        """Mark order as delivered."""
        order = self.get_object()
        order.status = DeliveryOrder.Status.DELIVERED
        order.delivered_at = timezone.now()
        order.actual_delivery = timezone.now()
        order.save(update_fields=["status", "delivered_at", "actual_delivery", "updated_at"])
        return Response({"message": "Order delivered."})

    @action(detail=True, methods=["post"])
    def cancel(self, request, id=None):
        """Cancel a delivery order."""
        order = self.get_object()
        if order.status in (DeliveryOrder.Status.DELIVERED, DeliveryOrder.Status.CANCELLED):
            return Response(
                {"detail": "Cannot cancel a delivered or already cancelled order."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        order.status = DeliveryOrder.Status.CANCELLED
        order.save(update_fields=["status", "updated_at"])
        return Response({"message": "Order cancelled."})
