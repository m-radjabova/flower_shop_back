from datetime import date
from typing import Literal

from pydantic import Field, field_validator

from app.schemas.common import ORMModel, TimestampedSchema

ImportantDateEventType = Literal["birthday", "anniversary", "custom"]


class ImportantDateBase(ORMModel):
    title: str = Field(min_length=2, max_length=120)
    event_type: ImportantDateEventType = "birthday"
    event_date: date
    note: str | None = Field(default=None, max_length=1000)

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Title is required")
        return normalized

    @field_validator("note")
    @classmethod
    def validate_note(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip()
        return normalized or None


class ImportantDateCreate(ImportantDateBase):
    pass


class ImportantDateUpdate(ORMModel):
    title: str | None = Field(default=None, min_length=2, max_length=120)
    event_type: ImportantDateEventType | None = None
    event_date: date | None = None
    note: str | None = Field(default=None, max_length=1000)

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip()
        if not normalized:
            raise ValueError("Title is required")
        return normalized

    @field_validator("note")
    @classmethod
    def validate_note(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip()
        return normalized or None


class ImportantDateOut(TimestampedSchema):
    user_id: str
    title: str
    event_type: ImportantDateEventType
    event_date: date
    note: str | None = None
