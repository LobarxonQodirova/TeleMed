"""WebSocket URL routing for TeleMed."""
from django.urls import re_path

from apps.consultations.consumers import ConsultationConsumer

websocket_urlpatterns = [
    re_path(
        r"ws/consultation/(?P<consultation_id>\d+)/$",
        ConsultationConsumer.as_asgi(),
    ),
]
