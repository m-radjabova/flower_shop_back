import re
import unicodedata

from app.services.base import ServiceError


def normalize_phone_uz(phone_number: str) -> str:
    digits = "".join(char for char in phone_number if char.isdigit())
    if digits.startswith("998"):
        digits = digits[3:]
    if len(digits) != 9:
        raise ServiceError(400, "Telefon raqami noto'g'ri")
    return f"+998{digits}"


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", normalized.lower()).strip("-")
    slug = re.sub(r"-{2,}", "-", slug)
    if not slug:
        raise ServiceError(400, "Slug yaratib bo'lmadi")
    return slug


def normalize_instagram(value: str | None) -> str | None:
    if value is None:
        return None
    trimmed = value.strip()
    if not trimmed:
        return None
    if trimmed.startswith(("http://", "https://")):
        return trimmed
    return f"@{trimmed.lstrip('@')}"


def normalize_telegram(value: str | None) -> str | None:
    if value is None:
        return None
    trimmed = value.strip()
    if not trimmed:
        return None
    if trimmed.startswith(("http://", "https://")):
        return trimmed
    return f"@{trimmed.lstrip('@')}"
