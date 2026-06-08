import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class SupportChat(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "support_chats"
    __table_args__ = (
        UniqueConstraint("owner_id", name="uq_support_chats_owner_id"),
    )

    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    owner = relationship("User", foreign_keys=[owner_id], back_populates="support_chats")
    messages = relationship(
        "SupportMessage",
        back_populates="chat",
        cascade="all, delete-orphan",
        order_by="SupportMessage.created_at",
    )


class SupportMessage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "support_messages"

    chat_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("support_chats.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sender_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    attachment_url: Mapped[str | None] = mapped_column(String(700), nullable=True)
    attachment_file_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    attachment_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    attachment_content_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    attachment_size: Mapped[int | None] = mapped_column(nullable=True)
    is_read_by_owner: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    is_read_by_admin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")

    chat = relationship("SupportChat", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id])
