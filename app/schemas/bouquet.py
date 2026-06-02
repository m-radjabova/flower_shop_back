from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import Field, model_validator

from app.models.enums import BouquetStatus
from app.schemas.category import CategorySummary
from app.schemas.common import ORMModel, TimestampedSchema
from app.schemas.shop import ShopSummary


SizeKey = Literal["small", "medium", "large", "premium"]


class BouquetSizeOption(ORMModel):
    key: SizeKey
    label: str = Field(min_length=2, max_length=50)
    price: Decimal = Field(ge=0)
    image: str = Field(min_length=1, max_length=500)


class BouquetAddonOption(ORMModel):
    id: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=2, max_length=80)
    price: Decimal = Field(ge=0)
    image: str = Field(min_length=1, max_length=500)


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
    size_options: list[BouquetSizeOption] = Field(default_factory=list, max_length=4)
    addon_options: list[BouquetAddonOption] = Field(default_factory=list, max_length=3)
    stock: int = Field(default=0, ge=0)
    status: BouquetStatus = BouquetStatus.ACTIVE

    @model_validator(mode="after")
    def require_at_least_one_image(self):
        if not self.image and not self.images and not any(option.image for option in self.size_options):
            raise ValueError("Kamida bitta rasm kerak")
        return self

    @model_validator(mode="after")
    def validate_unique_options(self):
        size_keys = [option.key for option in self.size_options]
        addon_ids = [option.id.strip().lower() for option in self.addon_options]
        if len(size_keys) != len(set(size_keys)):
            raise ValueError("Size optionlar takrorlanmasligi kerak")
        if len(addon_ids) != len(set(addon_ids)):
            raise ValueError("Add-on IDlar takrorlanmasligi kerak")
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
    size_options: list[BouquetSizeOption] | None = Field(default=None, max_length=4)
    addon_options: list[BouquetAddonOption] | None = Field(default=None, max_length=3)
    stock: int | None = Field(default=None, ge=0)
    status: BouquetStatus | None = None

    @model_validator(mode="after")
    def validate_unique_options(self):
        if self.size_options is not None:
            size_keys = [option.key for option in self.size_options]
            if len(size_keys) != len(set(size_keys)):
                raise ValueError("Size optionlar takrorlanmasligi kerak")
        if self.addon_options is not None:
            addon_ids = [option.id.strip().lower() for option in self.addon_options]
            if len(addon_ids) != len(set(addon_ids)):
                raise ValueError("Add-on IDlar takrorlanmasligi kerak")
        return self


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
    size_options: list[BouquetSizeOption] = Field(default_factory=list)
    addon_options: list[BouquetAddonOption] = Field(default_factory=list)
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
