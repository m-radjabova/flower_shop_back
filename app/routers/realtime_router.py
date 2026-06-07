from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect

from app.core.realtime import realtime_manager
from app.core.database import SessionLocal
from app.dependencies.auth import _resolve_user_from_token
from app.models.enums import UserRole
from app.models.shop import Shop

router = APIRouter(tags=['Realtime'])


@router.websocket('/ws/orders')
async def orders_websocket(
    websocket: WebSocket,
    token: str | None = Query(default=None),
    scope: str = Query(default='me'),
    shop_id: str | None = Query(default=None),
):
    db = SessionLocal()
    try:
        user = _resolve_user_from_token(token, db)
        if not user:
            await websocket.close(code=4401)
            return

        channels: list[str] = []
        if scope == 'me':
            channels.append(f'user:{user.id}')
        elif scope == 'admin':
            if not user.has_role(UserRole.ADMIN):
                await websocket.close(code=4403)
                return
            channels.append('role:admin')
        elif scope == 'shop':
            if not shop_id:
                await websocket.close(code=1008)
                return
            try:
                shop_uuid = UUID(shop_id)
            except ValueError:
                await websocket.close(code=1008)
                return

            shop = db.get(Shop, shop_uuid)
            if not shop:
                await websocket.close(code=1008)
                return
            if not user.has_role(UserRole.ADMIN) and shop.owner_id != user.id:
                await websocket.close(code=4403)
                return
            channels.append(f'shop:{shop.id}')
        else:
            await websocket.close(code=1008)
            return
    except HTTPException as exc:
        close_code = 4403 if exc.status_code == 403 else 4401
        await websocket.close(code=close_code)
        return
    finally:
        db.close()

    await realtime_manager.connect(websocket, channels)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        realtime_manager.disconnect(websocket)
