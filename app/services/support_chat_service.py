from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload

from app.core.realtime import broadcast_support_chat_event
from app.models.enums import UserRole
from app.models.support_chat import SupportChat, SupportMessage
from app.models.user import User
from app.schemas.support_chat import SupportMessageCreate
from app.services.base import BaseService


class SupportChatService(BaseService):
    def get_or_create_owner_chat(self, owner: User) -> SupportChat:
        chat = self.db.execute(
            select(SupportChat)
            .options(selectinload(SupportChat.owner), selectinload(SupportChat.messages).selectinload(SupportMessage.sender))
            .where(SupportChat.owner_id == owner.id)
        ).scalar_one_or_none()

        if chat:
            return chat

        chat = SupportChat(owner_id=owner.id)
        self.db.add(chat)
        self.commit()
        return self._get_chat(chat.id)

    def list_admin_chats(self, limit: int = 30, offset: int = 0, search: str | None = None) -> dict:
        normalized_search = search.strip() if search else ""
        filters = []
        if normalized_search:
            pattern = f"%{normalized_search}%"
            filters.append(
                or_(
                    User.full_name.ilike(pattern),
                    User.email.ilike(pattern),
                    User.phone.ilike(pattern),
                )
            )

        total_statement = select(func.count()).select_from(SupportChat).join(User, SupportChat.owner_id == User.id)
        if filters:
            total_statement = total_statement.where(*filters)
        total = self.db.execute(total_statement).scalar_one()

        statement = (
            select(SupportChat)
            .join(User, SupportChat.owner_id == User.id)
            .options(selectinload(SupportChat.owner), selectinload(SupportChat.messages).selectinload(SupportMessage.sender))
            .order_by(SupportChat.updated_at.desc())
            .offset(offset)
            .limit(limit)
        )
        if filters:
            statement = statement.where(*filters)

        chats = list(self.db.execute(statement).scalars().all())
        return {
            "items": [self.serialize_chat(chat, viewer_role=UserRole.ADMIN) for chat in chats],
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    def get_admin_chat(self, owner_id: str) -> SupportChat:
        owner_uuid = self.parse_uuid(owner_id, "Owner ID")
        owner = self.db.get(User, owner_uuid)
        if not owner or not owner.has_role(UserRole.OWNER):
            raise self.not_found("Owner")

        chat = self.db.execute(
            select(SupportChat)
            .options(selectinload(SupportChat.owner), selectinload(SupportChat.messages).selectinload(SupportMessage.sender))
            .where(SupportChat.owner_id == owner_uuid)
        ).scalar_one_or_none()
        if chat:
            return chat

        chat = SupportChat(owner_id=owner_uuid)
        self.db.add(chat)
        self.commit()
        return self._get_chat(chat.id)

    def list_messages(self, chat: SupportChat, limit: int = 100, offset: int = 0) -> dict:
        total = self.db.execute(
            select(func.count()).select_from(SupportMessage).where(SupportMessage.chat_id == chat.id)
        ).scalar_one()
        messages = list(
            self.db.execute(
                select(SupportMessage)
                .options(selectinload(SupportMessage.sender))
                .where(SupportMessage.chat_id == chat.id)
                .order_by(SupportMessage.created_at.asc())
                .offset(offset)
                .limit(limit)
            ).scalars().all()
        )
        return {
            "items": [self.serialize_message(message) for message in messages],
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    async def send_message(self, chat: SupportChat, sender: User, payload: SupportMessageCreate) -> dict:
        body = payload.body.strip()
        has_attachment = bool(payload.attachment_url and payload.attachment_file_id)
        if not body and not has_attachment:
            raise self.bad_request("Xabar yoki fayl yuboring")

        is_owner_sender = sender.id == chat.owner_id
        message = SupportMessage(
            chat_id=chat.id,
            sender_id=sender.id,
            body=body,
            attachment_url=payload.attachment_url,
            attachment_file_id=payload.attachment_file_id,
            attachment_name=payload.attachment_name,
            attachment_content_type=payload.attachment_content_type,
            attachment_size=payload.attachment_size,
            is_read_by_owner=is_owner_sender,
            is_read_by_admin=sender.has_role(UserRole.ADMIN),
        )
        chat.updated_at = datetime.now(UTC)
        self.db.add(message)
        self.db.add(chat)
        self.commit()

        refreshed_chat = self._get_chat(chat.id)
        refreshed_message = self.db.execute(
            select(SupportMessage)
            .options(selectinload(SupportMessage.sender))
            .where(SupportMessage.id == message.id)
        ).scalar_one()

        result = {
            "chat": self.serialize_chat(refreshed_chat, viewer_role=sender.role),
            "message": self.serialize_message(refreshed_message),
        }
        await broadcast_support_chat_event(refreshed_chat, refreshed_message, "support.message.created")
        return result

    async def mark_read(self, chat: SupportChat, viewer: User) -> dict:
        messages = list(
            self.db.execute(
                select(SupportMessage)
                .where(SupportMessage.chat_id == chat.id)
            ).scalars().all()
        )

        changed = False
        if viewer.has_role(UserRole.ADMIN):
            for message in messages:
                if not message.is_read_by_admin:
                    message.is_read_by_admin = True
                    self.db.add(message)
                    changed = True
        else:
            for message in messages:
                if not message.is_read_by_owner:
                    message.is_read_by_owner = True
                    self.db.add(message)
                    changed = True

        if changed:
            self.commit()
            chat = self._get_chat(chat.id)
            await broadcast_support_chat_event(chat, None, "support.chat.read")

        return self.serialize_chat(chat, viewer_role=viewer.role)

    def ensure_chat_access(self, chat: SupportChat, user: User) -> None:
        if user.has_role(UserRole.ADMIN):
            return
        if user.has_role(UserRole.OWNER) and chat.owner_id == user.id:
            return
        raise self.forbidden("Chatga ruxsat yo'q")

    def serialize_chat(self, chat: SupportChat, viewer_role: UserRole) -> dict:
        messages = sorted(chat.messages, key=lambda message: message.created_at)
        last_message = messages[-1] if messages else None
        if viewer_role == UserRole.ADMIN:
            unread_count = sum(1 for message in messages if not message.is_read_by_admin)
        else:
            unread_count = sum(1 for message in messages if not message.is_read_by_owner)

        return {
            "id": chat.id,
            "owner_id": chat.owner_id,
            "owner": {
                "id": chat.owner.id,
                "full_name": chat.owner.full_name,
                "email": chat.owner.email,
                "phone": chat.owner.phone,
                "avatar_url": chat.owner.avatar_url,
            },
            "last_message": self.serialize_message(last_message) if last_message else None,
            "unread_count": unread_count,
            "created_at": chat.created_at,
            "updated_at": chat.updated_at,
        }

    @staticmethod
    def serialize_message(message: SupportMessage | None) -> dict | None:
        if not message:
            return None

        return {
            "id": message.id,
            "chat_id": message.chat_id,
            "sender_id": message.sender_id,
            "sender_role": message.sender.role,
            "body": message.body,
            "attachment_url": message.attachment_url,
            "attachment_file_id": message.attachment_file_id,
            "attachment_name": message.attachment_name,
            "attachment_content_type": message.attachment_content_type,
            "attachment_size": message.attachment_size,
            "is_read_by_owner": message.is_read_by_owner,
            "is_read_by_admin": message.is_read_by_admin,
            "sender": {
                "id": message.sender.id,
                "full_name": message.sender.full_name,
                "email": message.sender.email,
                "role": message.sender.role,
                "avatar_url": message.sender.avatar_url,
            },
            "created_at": message.created_at,
            "updated_at": message.updated_at,
        }

    def _get_chat(self, chat_id: UUID) -> SupportChat:
        return self.db.execute(
            select(SupportChat)
            .options(selectinload(SupportChat.owner), selectinload(SupportChat.messages).selectinload(SupportMessage.sender))
            .where(SupportChat.id == chat_id)
        ).scalar_one()
