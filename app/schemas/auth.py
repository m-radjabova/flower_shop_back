from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.common import validate_app_email


class LoginSchema(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: str
    password: str = Field(min_length=6, max_length=128)

    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return validate_app_email(value)


class RegisterSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)

    full_name: str
    email: str
    phone: str = Field(alias="phone_number", min_length=7, max_length=32)
    referral_code: str | None = Field(default=None, min_length=4, max_length=32)
    password: str = Field(min_length=6, max_length=128)
    confirm_password: str = Field(min_length=6, max_length=128)

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 3:
            raise ValueError("To'liq ism kamida 3 ta belgi bo'lishi kerak")
        return normalized

    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return validate_app_email(value)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Parol bo'sh bo'lishi mumkin emas")
        return value

    @field_validator("confirm_password")
    @classmethod
    def validate_confirm_password(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Parol tasdig'i bo'sh bo'lishi mumkin emas")
        return value

    @field_validator("phone", mode="before")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Telefon raqami bo'sh bo'lishi mumkin emas")
        return normalized

    @field_validator("referral_code")
    @classmethod
    def validate_referral_code(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip().upper()
        return normalized or None

    @model_validator(mode="after")
    def validate_passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Parollar mos emas")
        return self


class RefreshSchema(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"
