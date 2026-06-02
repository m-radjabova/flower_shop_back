import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import OrderStatus, PaymentStatus, sql_enum


class Order(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "orders"

    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    shop_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("shops.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_name: Mapped[str] = mapped_column(String(120), nullable=False)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    delivery_method: Mapped[str] = mapped_column(String(50), nullable=False)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payment_method: Mapped[str] = mapped_column(String(50), nullable=False)
    payment_status: Mapped[PaymentStatus] = mapped_column(
        sql_enum(PaymentStatus, "payment_status"),
        nullable=False,
        default=PaymentStatus.PENDING,
        server_default=PaymentStatus.PENDING.value,
    )
    status: Mapped[OrderStatus] = mapped_column(
        sql_enum(OrderStatus, "order_status"),
        nullable=False,
        default=OrderStatus.NEW,
        server_default=OrderStatus.NEW.value,
    )
    total_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    user = relationship("User", back_populates="orders")
    shop = relationship("Shop", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="order")


class OrderItem(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "order_items"

    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    bouquet_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("bouquets.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    bouquet_name: Mapped[str] = mapped_column(String(150), nullable=False)
    bouquet_image: Mapped[str | None] = mapped_column(String(500), nullable=True)
    selected_size: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    selected_addons: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False)
    total_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    order = relationship("Order", back_populates="items")
    bouquet = relationship("Bouquet", back_populates="order_items")
