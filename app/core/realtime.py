from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable

from fastapi import WebSocket

from app.models.order import Order
from app.schemas.order import OrderOut


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
