from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.models.enums import UserRole
from app.schemas.common import ORMModel, TimestampedSchema


class SupportSenderOut(ORMModel):
    id: UUID
    full_name: str
    email: str
    role: UserRole
    avatar_url: str | None = None


class SupportMessageCreate(ORMModel):
    body: str = Field(default="", max_length=3000)
    attachment_url: str | None = Field(default=None, max_length=700)
    attachment_file_id: str | None = Field(default=None, max_length=255)
    attachment_name: str | None = Field(default=None, max_length=255)
    attachment_content_type: str | None = Field(default=None, max_length=120)
    attachment_size: int | None = Field(default=None, ge=0)


class SupportMessageOut(TimestampedSchema):
    chat_id: UUID
    sender_id: UUID
    sender_role: UserRole
    body: str
    attachment_url: str | None = None
    attachment_file_id: str | None = None
    attachment_name: str | None = None
    attachment_content_type: str | None = None
    attachment_size: int | None = None
    is_read_by_owner: bool
    is_read_by_admin: bool
    sender: SupportSenderOut


class SupportChatOwnerOut(ORMModel):
    id: UUID
    full_name: str
    email: str
    phone: str | None = None
    avatar_url: str | None = None


class SupportChatOut(TimestampedSchema):
    owner_id: UUID
    owner: SupportChatOwnerOut
    last_message: SupportMessageOut | None = None
    unread_count: int = 0


class SupportChatPage(ORMModel):
    items: list[SupportChatOut]
    total: int
    limit: int
    offset: int


class SupportMessagePage(ORMModel):
    items: list[SupportMessageOut]
    total: int
    limit: int
    offset: int


class SupportRealtimePayload(ORMModel):
    event: str
    chat: SupportChatOut
    message: SupportMessageOut | None = None
    emitted_at: datetime
