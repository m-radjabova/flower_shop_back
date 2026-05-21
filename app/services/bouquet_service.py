from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload

from app.models.bouquet import Bouquet
from app.models.category import Category
from app.models.enums import BouquetStatus, UserRole
from app.models.shop import Shop
from app.models.user import User
from app.schemas.bouquet import BouquetCreate, BouquetUpdate
from app.services.base import BaseService
from app.utils.formatters import slugify


class BouquetService(BaseService):
    def list_bouquets(
        self,
        shop_id: str | None = None,
        category_id: str | None = None,
        search: str | None = None,
        include_hidden: bool = False,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[Bouquet]:
        statement = self._filtered_bouquet_statement(
            shop_id=shop_id,
            category_id=category_id,
            search=search,
            include_hidden=include_hidden,
        ).order_by(Bouquet.created_at.desc())
        if offset:
            statement = statement.offset(offset)
        if limit:
            statement = statement.limit(limit)
        return list(self.db.execute(statement).scalars().all())

    def list_bouquets_page(
        self,
        shop_id: str | None = None,
        category_id: str | None = None,
        search: str | None = None,
        include_hidden: bool = False,
        limit: int = 12,
        offset: int = 0,
    ) -> dict:
        base_statement = self._filtered_bouquet_statement(
            shop_id=shop_id,
            category_id=category_id,
            search=search,
            include_hidden=include_hidden,
            include_relationships=False,
        )
        total = self.db.execute(
            select(func.count()).select_from(base_statement.order_by(None).subquery())
        ).scalar_one()
        items_statement = self._filtered_bouquet_statement(
            shop_id=shop_id,
            category_id=category_id,
            search=search,
            include_hidden=include_hidden,
        ).order_by(Bouquet.created_at.desc()).offset(offset).limit(limit)
        items = list(self.db.execute(items_statement).scalars().all())

        return {
            "items": items,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + len(items) < total,
        }

    def _filtered_bouquet_statement(
        self,
        shop_id: str | None = None,
        category_id: str | None = None,
        search: str | None = None,
        include_hidden: bool = False,
        include_relationships: bool = True,
    ):
        statement = select(Bouquet)
        if include_relationships:
            statement = statement.options(selectinload(Bouquet.shop), selectinload(Bouquet.category))
        if shop_id:
            statement = statement.where(Bouquet.shop_id == self.parse_uuid(shop_id, "Do'kon ID"))
        if category_id:
            statement = statement.where(Bouquet.category_id == self.parse_uuid(category_id, "Kategoriya ID"))
        if not include_hidden:
            statement = statement.where(Bouquet.status == BouquetStatus.ACTIVE)
        if search:
            query = f"%{search.strip().lower()}%"
            statement = statement.where(
                or_(
                    func.lower(Bouquet.name).like(query),
                    func.lower(Bouquet.description).like(query),
                    func.lower(Bouquet.compound).like(query),
                )
            )
        return statement

    def get_bouquet(self, bouquet_id: str, include_hidden: bool = False) -> Bouquet:
        statement = (
            select(Bouquet)
            .options(selectinload(Bouquet.shop), selectinload(Bouquet.category))
            .where(Bouquet.id == self.parse_uuid(bouquet_id, "Buket ID"))
        )
        bouquet = self.db.execute(statement).scalar_one_or_none()
        if not bouquet:
            raise self.not_found("Buket")
        if not include_hidden and bouquet.status != BouquetStatus.ACTIVE:
            raise self.not_found("Buket")
        return bouquet

    def create_bouquet(self, current_user: User, payload: BouquetCreate) -> Bouquet:
        shop = self._get_managed_shop(payload.shop_id, current_user)
        if payload.category_id:
            self._ensure_category_exists(payload.category_id)

        bouquet = Bouquet(
            shop_id=shop.id,
            category_id=payload.category_id,
            name=payload.name.strip(),
            slug=self._build_unique_slug(shop.id, payload.slug or payload.name),
            description=payload.description,
            compound=payload.compound,
            price=payload.price,
            old_price=payload.old_price,
            image=payload.image or payload.images[0],
            images=self._normalize_images(payload.image, payload.images),
            size=payload.size,
            stock=payload.stock,
            status=payload.status,
        )
        self.db.add(bouquet)
        self.commit()
        return self.get_bouquet(str(bouquet.id), include_hidden=True)

    def update_bouquet(self, bouquet_id: str, current_user: User, payload: BouquetUpdate) -> Bouquet:
        bouquet = self.db.get(Bouquet, self.parse_uuid(bouquet_id, "Buket ID"))
        if not bouquet:
            raise self.not_found("Buket")
        self._get_managed_shop(str(bouquet.shop_id), current_user)

        data = payload.model_dump(exclude_unset=True)
        if "category_id" in data and data["category_id"] is not None:
            self._ensure_category_exists(data["category_id"])
        if "name" in data and data["name"] is not None:
            bouquet.name = data["name"].strip()
            if "slug" not in data:
                bouquet.slug = self._build_unique_slug(bouquet.shop_id, bouquet.name, exclude_id=bouquet.id)
        if "slug" in data and data["slug"] is not None:
            bouquet.slug = self._build_unique_slug(bouquet.shop_id, data["slug"], exclude_id=bouquet.id)

        if "images" in data and data["images"] is not None:
            bouquet.images = self._normalize_images(data.get("image") or bouquet.image, data["images"])
            if "image" not in data and bouquet.images:
                bouquet.image = bouquet.images[0]
        elif "image" in data and data["image"] is not None:
            bouquet.images = self._normalize_images(data["image"], bouquet.images)

        for field in (
            "category_id",
            "description",
            "compound",
            "price",
            "old_price",
            "image",
            "size",
            "stock",
            "status",
        ):
            if field in data:
                setattr(bouquet, field, data[field])

        self.db.add(bouquet)
        self.commit()
        return self.get_bouquet(str(bouquet.id), include_hidden=True)

    def _normalize_images(self, cover_image: str | None, images: list[str] | None) -> list[str]:
        normalized: list[str] = []
        for image in [cover_image, *(images or [])]:
            if image and image not in normalized:
                normalized.append(image)
        return normalized

    def _get_managed_shop(self, shop_id: str, current_user: User) -> Shop:
        shop = self.db.get(Shop, self.parse_uuid(shop_id, "Do'kon ID"))
        if not shop:
            raise self.not_found("Do'kon")
        if current_user.role == UserRole.ADMIN:
            return shop
        if current_user.role != UserRole.OWNER or shop.owner_id != current_user.id:
            raise self.forbidden("Bu do'kon uchun ruxsat yo'q")
        return shop

    def _ensure_category_exists(self, category_id) -> None:
        category = self.db.get(Category, category_id)
        if not category:
            raise self.not_found("Kategoriya")

    def _build_unique_slug(self, shop_id, value: str, exclude_id=None) -> str:
        base_slug = slugify(value.strip())
        slug = base_slug
        counter = 2
        while True:
            statement = select(Bouquet).where(Bouquet.shop_id == shop_id, func.lower(Bouquet.slug) == slug.lower())
            existing = self.db.execute(statement).scalar_one_or_none()
            if existing is None or existing.id == exclude_id:
                return slug
            slug = f"{base_slug}-{counter}"
            counter += 1
