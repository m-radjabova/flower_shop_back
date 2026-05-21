from decimal import Decimal
from uuid import UUID

from pydantic import Field, model_validator

from app.models.enums import BouquetStatus
from app.schemas.category import CategorySummary
from app.schemas.common import ORMModel, TimestampedSchema
from app.schemas.shop import ShopSummary


class BouquetCreate(ORMModel):
    shop_id: UUID
    category_id: UUID | None = None
    name: str = Field(min_length=2, max_length=150)
    slug: str | None = Field(default=None, min_length=2, max_length=180)
    description: str | None = None
    compound: str | None = None
    price: Decimal = Field(ge=0)
    old_price: Decimal | None = Field(default=None, ge=0)
    image: str | None = Field(default=None, min_length=1, max_length=500)
    images: list[str] = Field(default_factory=list)
    size: str | None = Field(default=None, max_length=50)
    stock: int = Field(default=0, ge=0)
    status: BouquetStatus = BouquetStatus.ACTIVE

    @model_validator(mode="after")
    def require_at_least_one_image(self):
        if not self.image and not self.images:
            raise ValueError("Kamida bitta rasm kerak")
        return self


class BouquetUpdate(ORMModel):
    category_id: UUID | None = None
    name: str | None = Field(default=None, min_length=2, max_length=150)
    slug: str | None = Field(default=None, min_length=2, max_length=180)
    description: str | None = None
    compound: str | None = None
    price: Decimal | None = Field(default=None, ge=0)
    old_price: Decimal | None = Field(default=None, ge=0)
    image: str | None = Field(default=None, min_length=1, max_length=500)
    images: list[str] | None = None
    size: str | None = Field(default=None, max_length=50)
    stock: int | None = Field(default=None, ge=0)
    status: BouquetStatus | None = None


class BouquetOut(TimestampedSchema):
    shop_id: UUID
    category_id: UUID | None = None
    name: str
    slug: str
    description: str | None = None
    compound: str | None = None
    price: Decimal
    old_price: Decimal | None = None
    image: str
    images: list[str] = Field(default_factory=list)
    size: str | None = None
    stock: int
    status: BouquetStatus
    rating: Decimal
    reviews_count: int
    shop: ShopSummary
    category: CategorySummary | None = None


class BouquetPage(ORMModel):
    items: list[BouquetOut]
    total: int
    limit: int
    offset: int
    has_more: bool


class BouquetSummary(ORMModel):
    id: UUID
    name: str
    slug: str
    image: str
    images: list[str] = Field(default_factory=list)
    price: Decimal
    old_price: Decimal | None = None
    stock: int
    status: BouquetStatus
    rating: Decimal
    reviews_count: int
