"""WebSocket routing for the consultations app."""
from django.urls import re_path

from .consumers import ConsultationConsumer

websocket_urlpatterns = [
    re_path(
        r"ws/consultation/(?P<consultation_id>[0-9a-f-]+)/$",
        ConsultationConsumer.as_asgi(),
    ),
]
