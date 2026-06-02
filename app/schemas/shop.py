from decimal import Decimal
from uuid import UUID

from pydantic import Field

from app.models.enums import ShopStatus
from app.schemas.common import ORMModel, TimestampedSchema


class ShopCreate(ORMModel):
    name: str = Field(min_length=2, max_length=150)
    slug: str | None = Field(default=None, min_length=2, max_length=180)
    description: str | None = None
    logo: str | None = Field(default=None, max_length=500)
    banner: str | None = Field(default=None, max_length=500)
    phone: str = Field(min_length=7, max_length=32)
    address: str = Field(min_length=3, max_length=255)
    city: str | None = Field(default=None, max_length=80)
    latitude: str | None = Field(default=None, max_length=32)
    longitude: str | None = Field(default=None, max_length=32)
    instagram: str | None = Field(default=None, max_length=255)
    telegram: str | None = Field(default=None, max_length=255)
    working_hours: str | None = Field(default=None, max_length=255)
    status: ShopStatus = ShopStatus.PENDING


class ShopUpdate(ORMModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    slug: str | None = Field(default=None, min_length=2, max_length=180)
    description: str | None = None
    logo: str | None = Field(default=None, max_length=500)
    banner: str | None = Field(default=None, max_length=500)
    phone: str | None = Field(default=None, min_length=7, max_length=32)
    address: str | None = Field(default=None, min_length=3, max_length=255)
    city: str | None = Field(default=None, max_length=80)
    latitude: str | None = Field(default=None, max_length=32)
    longitude: str | None = Field(default=None, max_length=32)
    instagram: str | None = Field(default=None, max_length=255)
    telegram: str | None = Field(default=None, max_length=255)
    working_hours: str | None = Field(default=None, max_length=255)
    status: ShopStatus | None = None


class ShopOwnerSummary(ORMModel):
    id: UUID
    full_name: str
    email: str
    phone: str | None = None


class ShopOut(TimestampedSchema):
    owner_id: UUID
    name: str
    slug: str
    description: str | None = None
    logo: str | None = None
    banner: str | None = None
    phone: str
    address: str
    city: str | None = None
    latitude: str | None = None
    longitude: str | None = None
    instagram: str | None = None
    telegram: str | None = None
    working_hours: str | None = None
    rating: Decimal
    reviews_count: int
    status: ShopStatus
    owner: ShopOwnerSummary


class ShopSummary(ORMModel):
    id: UUID
    name: str
    slug: str
    logo: str | None = None
    city: str | None = None
    instagram: str | None = None
    telegram: str | None = None
    rating: Decimal
    reviews_count: int
    status: ShopStatus
