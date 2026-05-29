import uuid
from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Numeric, String, text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import UserRole, sql_enum


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    phone: Mapped[str | None] = mapped_column(String(32), unique=True, nullable=True, index=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    avatar_file_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    referral_code: Mapped[str | None] = mapped_column(String(32), unique=True, nullable=True, index=True)
    referred_by_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    referral_reward_granted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    referral_bonus_balance: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0, server_default="0")
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    roles: Mapped[list[UserRole]] = mapped_column(
        ARRAY(sql_enum(UserRole, "user_role")),
        nullable=False,
        default=lambda: [UserRole.CUSTOMER],
        server_default=text("ARRAY['customer']::user_role[]"),
    )
    refresh_token_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    shops = relationship("Shop", back_populates="owner")
    orders = relationship("Order", back_populates="user")
    reviews = relationship("Review", back_populates="user")
    addresses = relationship("Address", back_populates="user", cascade="all, delete-orphan")
    referred_by = relationship("User", remote_side="User.id", back_populates="referred_users")
    referred_users = relationship("User", back_populates="referred_by")

    def has_role(self, role: UserRole) -> bool:
        return role in (self.roles or [])

    def has_any_role(self, *roles: UserRole) -> bool:
        return any(role in (self.roles or []) for role in roles)
