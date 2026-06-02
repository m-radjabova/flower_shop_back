from decimal import Decimal
from uuid import UUID

from pydantic import Field

from app.models.enums import OrderStatus, PaymentStatus
from app.schemas.bouquet import BouquetAddonOption, BouquetSizeOption
from app.schemas.common import ORMModel, TimestampedSchema


class OrderItemCreate(ORMModel):
    bouquet_id: UUID | None = None
    bouquet_name: str = Field(min_length=2, max_length=150)
    bouquet_image: str | None = Field(default=None, max_length=500)
    selected_size: BouquetSizeOption | None = None
    selected_addons: list[BouquetAddonOption] = Field(default_factory=list, max_length=3)
    price: Decimal = Field(ge=0)
    quantity: int = Field(gt=0)


class OrderCreate(ORMModel):
    shop_id: UUID
    customer_name: str = Field(min_length=2, max_length=120)
    phone: str = Field(min_length=7, max_length=32)
    email: str | None = None
    delivery_method: str = Field(min_length=2, max_length=50)
    address: str | None = Field(default=None, max_length=255)
    payment_method: str = Field(min_length=2, max_length=50)
    note: str | None = None
    items: list[OrderItemCreate] = Field(min_length=1)


class OrderStatusUpdate(ORMModel):
    status: OrderStatus | None = None
    payment_status: PaymentStatus | None = None


class OrderItemOut(ORMModel):
    id: UUID
    order_id: UUID
    bouquet_id: UUID | None = None
    bouquet_name: str
    bouquet_image: str | None = None
    selected_size: BouquetSizeOption | None = None
    selected_addons: list[BouquetAddonOption] = Field(default_factory=list)
    price: Decimal
    quantity: int
    total_price: Decimal


class OrderOut(TimestampedSchema):
    user_id: UUID | None = None
    shop_id: UUID
    customer_name: str
    phone: str
    email: str | None = None
    delivery_method: str
    address: str | None = None
    payment_method: str
    payment_status: PaymentStatus
    status: OrderStatus
    total_price: Decimal
    note: str | None = None
    items: list[OrderItemOut]
