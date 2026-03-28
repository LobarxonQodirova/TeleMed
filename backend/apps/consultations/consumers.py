"""WebSocket consumer for WebRTC signaling in consultations."""
import json
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebSocketConsumer
from django.utils import timezone

from .models import Consultation, VideoSession

logger = logging.getLogger(__name__)


class ConsultationConsumer(AsyncJsonWebSocketConsumer):
    """
    WebSocket consumer for real-time consultation communication.

    Handles WebRTC signaling (offer, answer, ICE candidates),
    chat messages, and consultation status updates.
    """

    async def connect(self):
        self.consultation_id = self.scope["url_route"]["kwargs"]["consultation_id"]
        self.room_group_name = f"consultation_{self.consultation_id}"
        self.user = self.scope["user"]

        if self.user.is_anonymous:
            await self.close(code=4001)
            return

        # Verify user is a participant
        is_participant = await self.is_consultation_participant()
        if not is_participant:
            await self.close(code=4003)
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # Notify the room that a user joined
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "user_joined",
                "user_id": str(self.user.id),
                "user_name": self.user.get_full_name(),
                "role": self.user.role,
            },
        )

        await self.update_join_time()

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "user_left",
                    "user_id": str(self.user.id),
                    "user_name": self.user.get_full_name(),
                    "role": self.user.role,
                },
            )
            await self.channel_layer.group_discard(
                self.room_group_name, self.channel_name
            )

    async def receive_json(self, content):
        """Route incoming messages by type."""
        msg_type = content.get("type")

        handlers = {
            "webrtc_offer": self.handle_webrtc_offer,
            "webrtc_answer": self.handle_webrtc_answer,
            "webrtc_ice_candidate": self.handle_ice_candidate,
            "chat_message": self.handle_chat_message,
            "typing": self.handle_typing,
            "consultation_status": self.handle_status_update,
        }

        handler = handlers.get(msg_type)
        if handler:
            await handler(content)
        else:
            await self.send_json({"type": "error", "message": f"Unknown type: {msg_type}"})

    # ── WebRTC signaling ────────────────────────────────────────────────────

    async def handle_webrtc_offer(self, content):
        """Forward WebRTC offer to the other participant."""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "webrtc_offer",
                "offer": content["offer"],
                "sender_id": str(self.user.id),
            },
        )

    async def handle_webrtc_answer(self, content):
        """Forward WebRTC answer to the other participant."""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "webrtc_answer",
                "answer": content["answer"],
                "sender_id": str(self.user.id),
            },
        )

    async def handle_ice_candidate(self, content):
        """Forward ICE candidate to the other participant."""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "webrtc_ice_candidate",
                "candidate": content["candidate"],
                "sender_id": str(self.user.id),
            },
        )

    # ── Chat ────────────────────────────────────────────────────────────────

    async def handle_chat_message(self, content):
        """Broadcast chat message to the consultation room."""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": content["message"],
                "sender_id": str(self.user.id),
                "sender_name": self.user.get_full_name(),
                "timestamp": timezone.now().isoformat(),
            },
        )

    async def handle_typing(self, content):
        """Broadcast typing indicator."""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "typing",
                "user_id": str(self.user.id),
                "is_typing": content.get("is_typing", True),
            },
        )

    async def handle_status_update(self, content):
        """Handle consultation status changes (e.g., end call)."""
        new_status = content.get("status")
        if new_status:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "consultation_status",
                    "status": new_status,
                    "changed_by": str(self.user.id),
                },
            )

    # ── Group message handlers (send to individual WebSocket) ───────────

    async def user_joined(self, event):
        if event["user_id"] != str(self.user.id):
            await self.send_json(event)

    async def user_left(self, event):
        if event["user_id"] != str(self.user.id):
            await self.send_json(event)

    async def webrtc_offer(self, event):
        if event["sender_id"] != str(self.user.id):
            await self.send_json(event)

    async def webrtc_answer(self, event):
        if event["sender_id"] != str(self.user.id):
            await self.send_json(event)

    async def webrtc_ice_candidate(self, event):
        if event["sender_id"] != str(self.user.id):
            await self.send_json(event)

    async def chat_message(self, event):
        await self.send_json(event)

    async def typing(self, event):
        if event["user_id"] != str(self.user.id):
            await self.send_json(event)

    async def consultation_status(self, event):
        await self.send_json(event)

    # ── Database helpers ────────────────────────────────────────────────────

    @database_sync_to_async
    def is_consultation_participant(self):
        try:
            consultation = Consultation.objects.get(id=self.consultation_id)
            return self.user in (consultation.doctor, consultation.patient)
        except Consultation.DoesNotExist:
            return False

    @database_sync_to_async
    def update_join_time(self):
        try:
            session = VideoSession.objects.filter(
                consultation_id=self.consultation_id,
                status=VideoSession.Status.ACTIVE,
            ).latest("created_at")
        except VideoSession.DoesNotExist:
            return

        now = timezone.now()
        if self.user.is_doctor and not session.doctor_joined_at:
            session.doctor_joined_at = now
            session.save(update_fields=["doctor_joined_at"])
        elif self.user.is_patient and not session.patient_joined_at:
            session.patient_joined_at = now
            session.save(update_fields=["patient_joined_at"])
