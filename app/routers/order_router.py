from fastapi import APIRouter, Depends

from app.core.realtime import broadcast_order_event
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_user, get_current_user_optional
from app.dependencies.roles import require_roles
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.order import OrderCreate, OrderOut, OrderStatusUpdate
from app.services.order_service import OrderService

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("", response_model=OrderOut)
async def create_order(
    payload: OrderCreate,
    current_user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    order = OrderService(db).create_order(payload, current_user)
    await broadcast_order_event(order, 'order.created')
    return order


@router.get("/me", response_model=list[OrderOut])
def list_my_orders(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return OrderService(db).list_customer_orders(current_user)


@router.get("/shop/{shop_id}", response_model=list[OrderOut])
def list_shop_orders(
    shop_id: str,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.OWNER)),
    db: Session = Depends(get_db),
):
    return OrderService(db).list_shop_orders(shop_id, current_user)


@router.get("/{order_id}", response_model=OrderOut)
def get_order(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return OrderService(db).get_order(order_id, current_user, allow_owner_admin=True)


@router.patch("/{order_id}/status", response_model=OrderOut)
async def update_order_status(
    order_id: str,
    payload: OrderStatusUpdate,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.OWNER)),
    db: Session = Depends(get_db),
):
    order = OrderService(db).update_order_status(order_id, current_user, payload)
    await broadcast_order_event(order, 'order.updated')
    return order
