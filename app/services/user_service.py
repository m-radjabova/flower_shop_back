from uuid import UUID

from fastapi import UploadFile
from sqlalchemy import or_, func, select

from app.core.security import hash_password, verify_password
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.user import AdminUserUpdate, ChangePasswordSchema, UserUpdate
from app.services.base import BaseService, ServiceError
from app.services.upload_service import UploadService
from app.utils.formatters import normalize_phone_uz


class UserService(BaseService):
    def get_user_by_id(self, user_id: str) -> User:
        try:
            user_uuid = UUID(str(user_id))
        except ValueError as exc:
            raise self.bad_request("Foydalanuvchi id noto'g'ri") from exc

        user = self.db.get(User, user_uuid)
        if not user:
            raise self.not_found("Foydalanuvchi")
        return user

    def get_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email.strip().lower())
        return self.db.execute(statement).scalar_one_or_none()

    def get_by_phone_number(self, phone_number: str) -> User | None:
        statement = select(User).where(User.phone == phone_number.strip())
        return self.db.execute(statement).scalar_one_or_none()

    def create_admin(self, full_name: str, email: str, password: str) -> User:
        return self._create_user(
            full_name=full_name,
            email=email,
            password=password,
            roles=[UserRole.ADMIN, UserRole.CUSTOMER],
        )

    def list_users(self, limit: int = 15, offset: int = 0, search: str | None = None) -> dict:
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

        total_statement = select(func.count()).select_from(User)
        if filters:
            total_statement = total_statement.where(*filters)
        total = self.db.execute(total_statement).scalar_one()

        statement = select(User)
        if filters:
            statement = statement.where(*filters)
        statement = statement.order_by(User.created_at.desc()).offset(offset).limit(limit)
        items = list(self.db.execute(statement).scalars().all())
        return {
            "items": items,
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    def update_current_user(self, current_user: User, payload: UserUpdate) -> User:
        data = payload.model_dump(exclude_unset=True)
        if "email" in data:
            data["email"] = data["email"].strip().lower()
            self._ensure_email_available(data["email"], exclude_user_id=current_user.id)
        if "phone" in data and data["phone"] is not None:
            data["phone"] = normalize_phone_uz(data["phone"])
            self._ensure_phone_number_available(data["phone"], exclude_user_id=current_user.id)
        if "full_name" in data and data["full_name"] is not None:
            data["full_name"] = data["full_name"].strip()
        if "roles" in data and data["roles"] is not None:
            data["roles"] = list(dict.fromkeys(data["roles"]))

        for field, value in data.items():
            setattr(current_user, field, value)

        self.db.add(current_user)
        self.commit()
        return self.refresh(current_user)

    def change_my_password(self, current_user: User, payload: ChangePasswordSchema) -> User:
        if not verify_password(payload.current_password, current_user.password_hash):
            raise self.bad_request("Joriy parol noto'g'ri")

        current_user.password_hash = hash_password(payload.new_password)
        current_user.refresh_token_hash = None
        self.db.add(current_user)
        self.commit()
        return self.refresh(current_user)

    async def upload_my_avatar(self, current_user: User, file: UploadFile) -> User:
        old_avatar_file_id = current_user.avatar_file_id
        uploaded = await UploadService(self.db).upload_image(file, folder="/flower-shop/avatars")

        current_user.avatar_url = uploaded.url
        current_user.avatar_file_id = uploaded.file_id
        self.db.add(current_user)
        self.commit()
        refreshed_user = self.refresh(current_user)

        if old_avatar_file_id and old_avatar_file_id != uploaded.file_id:
            try:
                await UploadService(self.db).delete_image(old_avatar_file_id, ignore_missing=True)
            except ServiceError:
                # Avatar already points to the new image; old orphan cleanup can fail silently.
                pass

        return refreshed_user

    async def delete_my_avatar(self, current_user: User) -> User:
        avatar_file_id = current_user.avatar_file_id
        if avatar_file_id:
            await UploadService(self.db).delete_image(avatar_file_id, ignore_missing=True)

        current_user.avatar_url = None
        current_user.avatar_file_id = None
        self.db.add(current_user)
        self.commit()
        return self.refresh(current_user)

    def admin_update_user(self, user_id: str, payload: AdminUserUpdate) -> User:
        user = self.get_user_by_id(user_id)
        data = payload.model_dump(exclude_unset=True)
        if "email" in data and data["email"] is not None:
            data["email"] = data["email"].strip().lower()
            self._ensure_email_available(data["email"], exclude_user_id=user.id)
        if "phone" in data and data["phone"] is not None:
            data["phone"] = normalize_phone_uz(data["phone"])
            self._ensure_phone_number_available(data["phone"], exclude_user_id=user.id)
        if "full_name" in data and data["full_name"] is not None:
            data["full_name"] = data["full_name"].strip()

        for field, value in data.items():
            setattr(user, field, value)

        self.db.add(user)
        self.commit()
        return self.refresh(user)

    def _create_user(self, full_name: str, email: str, password: str, roles: list[UserRole]) -> User:
        normalized_email = email.strip().lower()
        self._ensure_email_available(normalized_email)

        user = User(
            full_name=full_name.strip(),
            email=normalized_email,
            password_hash=hash_password(password),
            roles=list(dict.fromkeys(roles)) or [UserRole.CUSTOMER],
        )
        self.db.add(user)
        self.commit()
        return self.refresh(user)

    def _ensure_email_available(self, email: str, exclude_user_id=None) -> None:
        existing_user = self.get_by_email(email)
        if existing_user and existing_user.id != exclude_user_id:
            raise self.bad_request("Bu email allaqachon mavjud")

    def _ensure_phone_number_available(self, phone_number: str, exclude_user_id=None) -> None:
        existing_user = self.get_by_phone_number(phone_number)
        if existing_user and existing_user.id != exclude_user_id:
            raise self.bad_request("Bu telefon raqami allaqachon mavjud")
