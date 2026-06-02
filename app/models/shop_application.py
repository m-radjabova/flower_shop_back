import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import ShopApplicationStatus, sql_enum


class ShopApplication(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "shop_applications"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    shop_name: Mapped[str] = mapped_column(String(150), nullable=False)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)
    city: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    latitude: Mapped[str | None] = mapped_column(String(32), nullable=True)
    longitude: Mapped[str | None] = mapped_column(String(32), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    instagram: Mapped[str | None] = mapped_column(String(255), nullable=True)
    telegram: Mapped[str | None] = mapped_column(String(255), nullable=True)
    logo: Mapped[str | None] = mapped_column(String(500), nullable=True)
    banner: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[ShopApplicationStatus] = mapped_column(
        sql_enum(ShopApplicationStatus, "shop_application_status"),
        nullable=False,
        default=ShopApplicationStatus.PENDING,
        server_default=ShopApplicationStatus.PENDING.value,
    )
    admin_comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    user = relationship("User", back_populates="shop_applications")
