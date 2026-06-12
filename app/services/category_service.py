from sqlalchemy import func, select

from app.core.config import settings
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.services.base import BaseService
from app.utils.formatters import slugify


class CategoryService(BaseService):
    def list_categories(self, active_only: bool) -> list[Category]:
        statement = select(Category).order_by(Category.name.asc())
        if active_only:
            statement = statement.where(Category.is_active.is_(True))
        return list(self.db.execute(statement).scalars().all())

    def create_category(self, payload: CategoryCreate) -> Category:
        slug = self._build_unique_slug(payload.slug or payload.name)
        category = Category(
            name=payload.name.strip(),
            slug=slug,
            description=self._normalize_description(payload.description),
            image=self._normalize_category_image(payload.image, required=True),
            is_active=payload.is_active,
        )
        self.db.add(category)
        self.commit()
        return self.refresh(category)

    def update_category(self, category_id: str, payload: CategoryUpdate) -> Category:
        category = self.get_category(category_id)
        data = payload.model_dump(exclude_unset=True)
        if "name" in data and data["name"] is not None:
            category.name = data["name"].strip()
        if "description" in data:
            category.description = self._normalize_description(data["description"])
        if "image" in data:
            category.image = self._normalize_category_image(data["image"], required=True)
        if "is_active" in data and data["is_active"] is not None:
            category.is_active = data["is_active"]
        if "slug" in data and data["slug"] is not None:
            category.slug = self._build_unique_slug(data["slug"], exclude_id=category.id)
        elif "name" in data and data["name"] is not None:
            category.slug = self._build_unique_slug(category.name, exclude_id=category.id)

        self.db.add(category)
        self.commit()
        return self.refresh(category)

    def get_category(self, category_id: str) -> Category:
        category = self.db.get(Category, self.parse_uuid(category_id, "Kategoriya ID"))
        if not category:
            raise self.not_found("Kategoriya")
        return category

    def _build_unique_slug(self, value: str, exclude_id=None) -> str:
        base_slug = slugify(value.strip())
        slug = base_slug
        counter = 2
        while True:
            statement = select(Category).where(func.lower(Category.slug) == slug.lower())
            existing = self.db.execute(statement).scalar_one_or_none()
            if existing is None or existing.id == exclude_id:
                return slug
            slug = f"{base_slug}-{counter}"
            counter += 1

    def _normalize_category_image(self, image: str | None, *, required: bool) -> str | None:
        normalized = (image or "").strip()
        if required and not normalized:
            raise self.bad_request("Category rasmi majburiy")
        if not normalized:
            return None

        imagekit_base = settings.IMAGEKIT_URL_ENDPOINT.strip().rstrip("/")
        if imagekit_base and not normalized.startswith(f"{imagekit_base}/"):
            raise self.bad_request("Category rasmi faqat upload orqali ImageKit'dan bo'lishi kerak")

        return normalized

    def _normalize_description(self, description: str | None) -> str | None:
        normalized = (description or "").strip()
        return normalized or None
