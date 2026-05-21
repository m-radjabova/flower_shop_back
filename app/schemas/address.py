from pydantic import Field

from app.schemas.common import ORMModel, TimestampedSchema


class AddressBase(ORMModel):
    title: str = Field(min_length=2, max_length=80)
    address_line: str = Field(min_length=5, max_length=255)
    city: str | None = Field(default=None, max_length=120)
    notes: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class AddressCreate(AddressBase):
    is_primary: bool = False


class AddressUpdate(ORMModel):
    title: str | None = Field(default=None, min_length=2, max_length=80)
    address_line: str | None = Field(default=None, min_length=5, max_length=255)
    city: str | None = Field(default=None, max_length=120)
    notes: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    is_primary: bool | None = None


class AddressOut(TimestampedSchema):
    user_id: str
    title: str
    address_line: str
    city: str | None = None
    notes: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    is_primary: bool
