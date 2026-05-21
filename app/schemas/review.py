from uuid import UUID

from pydantic import Field

from app.schemas.common import ORMModel, TimestampedSchema


class ReviewCreate(ORMModel):
    shop_id: UUID
    bouquet_id: UUID | None = None
    order_id: UUID | None = None
    rating: int = Field(ge=1, le=5)
    text: str | None = None
    image: str | None = Field(default=None, max_length=500)


class ReviewModerationUpdate(ORMModel):
    is_approved: bool | None = None
    is_verified: bool | None = None


class ReviewUserSummary(ORMModel):
    id: UUID
    full_name: str


class ReviewOut(TimestampedSchema):
    user_id: UUID
    shop_id: UUID
    bouquet_id: UUID | None = None
    order_id: UUID | None = None
    rating: int
    text: str | None = None
    image: str | None = None
    is_approved: bool
    is_verified: bool
    user: ReviewUserSummary
