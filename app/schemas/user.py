from decimal import Decimal

from pydantic import Field, field_validator

from app.models.enums import UserRole
from app.schemas.common import ORMModel, TimestampedSchema, validate_app_email


class UserBase(ORMModel):
    full_name: str = Field(min_length=3, max_length=120)
    email: str
    phone: str | None = Field(default=None, min_length=7, max_length=32)
    avatar_url: str | None = None
    referral_code: str | None = None
    referral_bonus_balance: Decimal = Field(default=0)
    roles: list[UserRole] = Field(default_factory=list)
    is_active: bool = True

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return validate_app_email(value)


class UserUpdate(ORMModel):
    full_name: str | None = Field(default=None, min_length=3, max_length=120)
    email: str | None = None
    phone: str | None = Field(default=None, min_length=7, max_length=32)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return validate_app_email(value)


class AdminUserUpdate(ORMModel):
    full_name: str | None = Field(default=None, min_length=3, max_length=120)
    email: str | None = None
    phone: str | None = Field(default=None, min_length=7, max_length=32)
    roles: list[UserRole] | None = None
    is_active: bool | None = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return validate_app_email(value)

    @field_validator("roles")
    @classmethod
    def validate_roles(cls, value: list[UserRole] | None) -> list[UserRole] | None:
        if value is None:
            return value
        unique_roles = list(dict.fromkeys(value))
        if not unique_roles:
            raise ValueError("At least one role is required")
        return unique_roles


class ChangePasswordSchema(ORMModel):
    current_password: str
    new_password: str = Field(min_length=6, max_length=128)


class UserOut(TimestampedSchema, UserBase):
    pass


class UserPage(ORMModel):
    items: list[UserOut]
    total: int
    limit: int
    offset: int
