from uuid import UUID

from pydantic import Field

from app.models.enums import ShopApplicationStatus
from app.schemas.common import ORMModel, TimestampedSchema
from app.schemas.user import UserOut


class ShopApplicationCreate(ORMModel):
    shop_name: str = Field(min_length=2, max_length=150)
    owner_full_name: str | None = Field(default=None, min_length=3, max_length=120)
    phone: str = Field(min_length=7, max_length=32)
    city: str | None = Field(default=None, max_length=80)
    address: str = Field(min_length=3, max_length=255)
    latitude: str | None = Field(default=None, max_length=32)
    longitude: str | None = Field(default=None, max_length=32)
    description: str | None = None
    instagram: str | None = Field(default=None, max_length=255)
    telegram: str | None = Field(default=None, max_length=255)
    logo: str | None = Field(default=None, max_length=500)
    banner: str | None = Field(default=None, max_length=500)


class ShopApplicationReview(ORMModel):
    status: ShopApplicationStatus
    admin_comment: str | None = None


class ShopApplicationApplicant(ORMModel):
    id: UUID
    full_name: str
    email: str
    phone: str | None = None


class ShopApplicationOut(TimestampedSchema):
    user_id: UUID
    shop_name: str
    phone: str
    city: str | None = None
    address: str
    latitude: str | None = None
    longitude: str | None = None
    description: str | None = None
    instagram: str | None = None
    telegram: str | None = None
    logo: str | None = None
    banner: str | None = None
    status: ShopApplicationStatus
    admin_comment: str | None = None
    user: ShopApplicationApplicant


class ShopApplicationStatusOut(TimestampedSchema):
    user_id: UUID
    shop_name: str
    phone: str
    city: str | None = None
    address: str
    latitude: str | None = None
    longitude: str | None = None
    description: str | None = None
    instagram: str | None = None
    telegram: str | None = None
    logo: str | None = None
    banner: str | None = None
    status: ShopApplicationStatus
    admin_comment: str | None = None


class ShopApplicationSubmitResponse(ORMModel):
    application: ShopApplicationStatusOut
    user: UserOut
