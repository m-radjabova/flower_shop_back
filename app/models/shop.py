import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import ShopStatus, sql_enum


class Shop(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "shops"

    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    slug: Mapped[str] = mapped_column(String(180), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    logo: Mapped[str | None] = mapped_column(String(500), nullable=True)
    banner: Mapped[str | None] = mapped_column(String(500), nullable=True)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    latitude: Mapped[str | None] = mapped_column(String(32), nullable=True)
    longitude: Mapped[str | None] = mapped_column(String(32), nullable=True)
    instagram: Mapped[str | None] = mapped_column(String(255), nullable=True)
    telegram: Mapped[str | None] = mapped_column(String(255), nullable=True)
    working_hours: Mapped[str | None] = mapped_column(String(255), nullable=True)
    rating: Mapped[Decimal] = mapped_column(Numeric(2, 1), nullable=False, default=Decimal("0.0"), server_default="0")
    reviews_count: Mapped[int] = mapped_column(nullable=False, default=0, server_default="0")
    status: Mapped[ShopStatus] = mapped_column(
        sql_enum(ShopStatus, "shop_status"),
        nullable=False,
        default=ShopStatus.PENDING,
        server_default=ShopStatus.PENDING.value,
    )

    owner = relationship("User", back_populates="shops")
    bouquets = relationship("Bouquet", back_populates="shop", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="shop", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="shop", cascade="all, delete-orphan")
