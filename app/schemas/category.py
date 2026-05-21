from uuid import UUID

from pydantic import Field

from app.schemas.common import ORMModel, TimestampedSchema


class CategoryCreate(ORMModel):
    name: str = Field(min_length=2, max_length=100)
    slug: str | None = Field(default=None, min_length=2, max_length=120)
    image: str | None = Field(default=None, max_length=500)
    is_active: bool = True


class CategoryUpdate(ORMModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    slug: str | None = Field(default=None, min_length=2, max_length=120)
    image: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None


class CategoryOut(TimestampedSchema):
    name: str
    slug: str
    image: str | None = None
    is_active: bool


class CategorySummary(ORMModel):
    id: UUID
    name: str
    slug: str
