import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, JSON, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import BouquetStatus, sql_enum


class Bouquet(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "bouquets"
    __table_args__ = (
        UniqueConstraint("shop_id", "slug", name="uq_bouquets_shop_slug"),
    )

    shop_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("shops.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    slug: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    compound: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    old_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    image: Mapped[str] = mapped_column(String(500), nullable=False)
    images: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    size: Mapped[str | None] = mapped_column(String(50), nullable=True)
    stock: Mapped[int] = mapped_column(nullable=False, default=0, server_default="0")
    status: Mapped[BouquetStatus] = mapped_column(
        sql_enum(BouquetStatus, "bouquet_status"),
        nullable=False,
        default=BouquetStatus.ACTIVE,
        server_default=BouquetStatus.ACTIVE.value,
    )
    rating: Mapped[Decimal] = mapped_column(Numeric(2, 1), nullable=False, default=Decimal("0.0"), server_default="0")
    reviews_count: Mapped[int] = mapped_column(nullable=False, default=0, server_default="0")

    shop = relationship("Shop", back_populates="bouquets")
    category = relationship("Category", back_populates="bouquets")
    reviews = relationship("Review", back_populates="bouquet")
    order_items = relationship("OrderItem", back_populates="bouquet")
