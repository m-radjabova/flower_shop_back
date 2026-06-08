from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable

from fastapi import WebSocket

from app.models.order import Order
from app.models.support_chat import SupportChat, SupportMessage
from app.schemas.order import OrderOut
from app.schemas.support_chat import SupportRealtimePayload


@dataclass(slots=True)
class RealtimeMessage:
    event: str
    order: dict


class RealtimeManager:
    def __init__(self) -> None:
        self._channels: dict[str, dict[int, WebSocket]] = defaultdict(dict)
        self._socket_channels: dict[int, set[str]] = {}

    async def connect(self, websocket: WebSocket, channels: Iterable[str]) -> None:
        await websocket.accept()
        websocket_id = id(websocket)
        channel_set = self._socket_channels.setdefault(websocket_id, set())
        for channel in channels:
            if not channel:
                continue
            self._channels[channel][websocket_id] = websocket
            channel_set.add(channel)

    def disconnect(self, websocket: WebSocket) -> None:
        websocket_id = id(websocket)
        channels = self._socket_channels.pop(websocket_id, set())
        for channel in channels:
            subscribers = self._channels.get(channel)
            if not subscribers:
                continue
            subscribers.pop(websocket_id, None)
            if not subscribers:
                self._channels.pop(channel, None)

    async def broadcast(self, channel: str, message: dict) -> None:
        subscribers = list(self._channels.get(channel, {}).items())
        for websocket_id, websocket in subscribers:
            try:
                await websocket.send_json(message)
            except Exception:
                self._channels.get(channel, {}).pop(websocket_id, None)
                self._socket_channels.get(websocket_id, set()).discard(channel)

    async def broadcast_many(self, channels: Iterable[str], message: dict) -> None:
        sent: set[int] = set()
        for channel in channels:
            subscribers = list(self._channels.get(channel, {}).items())
            for websocket_id, websocket in subscribers:
                if websocket_id in sent:
                    continue
                try:
                    await websocket.send_json(message)
                except Exception:
                    self._channels.get(channel, {}).pop(websocket_id, None)
                    self._socket_channels.get(websocket_id, set()).discard(channel)
                sent.add(websocket_id)


realtime_manager = RealtimeManager()


def build_order_message(order: Order, event: str) -> RealtimeMessage:
    order_out = OrderOut.model_validate(order).model_dump(mode='json')
    return RealtimeMessage(event=event, order=order_out)


async def broadcast_order_event(order: Order, event: str) -> None:
    message = build_order_message(order, event)
    channels = {'role:admin'}

    user_id = message.order.get('user_id')
    if user_id:
        channels.add(f'user:{user_id}')

    shop_id = message.order.get('shop_id')
    if shop_id:
        channels.add(f'shop:{shop_id}')

    await realtime_manager.broadcast_many(channels, {
        'event': message.event,
        'order': message.order,
    })


def _serialize_support_message(message: SupportMessage | None) -> dict | None:
    if not message:
        return None

    return {
        "id": message.id,
        "chat_id": message.chat_id,
        "sender_id": message.sender_id,
        "sender_role": message.sender.role,
        "body": message.body,
        "attachment_url": message.attachment_url,
        "attachment_file_id": message.attachment_file_id,
        "attachment_name": message.attachment_name,
        "attachment_content_type": message.attachment_content_type,
        "attachment_size": message.attachment_size,
        "is_read_by_owner": message.is_read_by_owner,
        "is_read_by_admin": message.is_read_by_admin,
        "sender": {
            "id": message.sender.id,
            "full_name": message.sender.full_name,
            "email": message.sender.email,
            "role": message.sender.role,
            "avatar_url": message.sender.avatar_url,
        },
        "created_at": message.created_at,
        "updated_at": message.updated_at,
    }


def _serialize_support_chat(chat: SupportChat, message: SupportMessage | None = None) -> dict:
    messages = sorted(chat.messages, key=lambda item: item.created_at)
    last_message = message or (messages[-1] if messages else None)
    return {
        "id": chat.id,
        "owner_id": chat.owner_id,
        "owner": {
            "id": chat.owner.id,
            "full_name": chat.owner.full_name,
            "email": chat.owner.email,
            "phone": chat.owner.phone,
            "avatar_url": chat.owner.avatar_url,
        },
        "last_message": _serialize_support_message(last_message),
        "unread_count": 0,
        "created_at": chat.created_at,
        "updated_at": chat.updated_at,
    }


async def broadcast_support_chat_event(
    chat: SupportChat,
    message: SupportMessage | None,
    event: str,
) -> None:
    payload = SupportRealtimePayload(
        event=event,
        chat=_serialize_support_chat(chat, message),
        message=_serialize_support_message(message),
        emitted_at=chat.updated_at,
    ).model_dump(mode="json")
    await realtime_manager.broadcast_many(
        {f"support:owner:{chat.owner_id}", "support:admin"},
        payload,
    )
