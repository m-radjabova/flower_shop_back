from decimal import Decimal

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
    SIZE_LABELS = {
        "small": "Small",
        "medium": "Medium",
        "large": "Large",
        "premium": "Premium",
    }

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

    def list_managed_bouquets(self, shop_id: str, current_user: User) -> list[Bouquet]:
        shop = self._get_managed_shop(shop_id, current_user)
        statement = (
            select(Bouquet)
            .options(selectinload(Bouquet.shop), selectinload(Bouquet.category))
            .where(Bouquet.shop_id == shop.id)
            .order_by(Bouquet.created_at.desc())
        )
        return list(self.db.execute(statement).scalars().all())

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
        normalized_search = search.strip().lower() if search else ""
        if normalized_search:
            query = f"%{normalized_search}%"
            statement = statement.outerjoin(Bouquet.category).outerjoin(Bouquet.shop)
            statement = statement.where(
                or_(
                    func.lower(Bouquet.name).like(query),
                    func.lower(Bouquet.slug).like(query),
                    func.lower(Bouquet.description).like(query),
                    func.lower(Bouquet.compound).like(query),
                    func.lower(Category.name).like(query),
                    func.lower(Category.slug).like(query),
                    func.lower(Shop.name).like(query),
                    func.lower(Shop.slug).like(query),
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
        size_options = self._normalize_size_options(payload.size_options, fallback_price=payload.price)
        addon_options = self._normalize_addon_options(payload.addon_options)
        primary_price, primary_image, normalized_images, size_summary = self._resolve_primary_bouquet_fields(
            size_options=size_options,
            fallback_price=payload.price,
            fallback_image=payload.image,
            fallback_images=payload.images,
            fallback_size=payload.size,
        )

        bouquet = Bouquet(
            shop_id=shop.id,
            category_id=payload.category_id,
            name=payload.name.strip(),
            slug=self._build_unique_slug(shop.id, payload.slug or payload.name),
            description=payload.description,
            compound=payload.compound,
            price=primary_price,
            old_price=payload.old_price,
            image=primary_image,
            images=normalized_images,
            size=size_summary,
            size_options=size_options,
            addon_options=addon_options,
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
        size_options_payload = data.get("size_options")
        addon_options_payload = data.get("addon_options")
        next_size_options = (
            self._normalize_size_options(size_options_payload, fallback_price=data.get("price") or bouquet.price)
            if size_options_payload is not None
            else list(bouquet.size_options or [])
        )
        next_addon_options = (
            self._normalize_addon_options(addon_options_payload)
            if addon_options_payload is not None
            else list(bouquet.addon_options or [])
        )
        fallback_images = data["images"] if "images" in data and data["images"] is not None else bouquet.images
        fallback_image = data.get("image") if data.get("image") else bouquet.image
        fallback_price = data.get("price") if data.get("price") is not None else bouquet.price
        fallback_size = data.get("size") if "size" in data else bouquet.size
        primary_price, primary_image, normalized_images, size_summary = self._resolve_primary_bouquet_fields(
            size_options=next_size_options,
            fallback_price=fallback_price,
            fallback_image=fallback_image,
            fallback_images=fallback_images,
            fallback_size=fallback_size,
        )

        for field in (
            "category_id",
            "description",
            "compound",
            "old_price",
            "stock",
            "status",
        ):
            if field in data:
                setattr(bouquet, field, data[field])

        bouquet.price = primary_price
        bouquet.image = primary_image
        bouquet.images = normalized_images
        bouquet.size = size_summary
        bouquet.size_options = next_size_options
        bouquet.addon_options = next_addon_options

        self.db.add(bouquet)
        self.commit()
        return self.get_bouquet(str(bouquet.id), include_hidden=True)

    def delete_bouquet(self, bouquet_id: str, current_user: User) -> None:
        bouquet = self.db.get(Bouquet, self.parse_uuid(bouquet_id, "Buket ID"))
        if not bouquet:
            raise self.not_found("Buket")
        self._get_managed_shop(str(bouquet.shop_id), current_user)
        self.db.delete(bouquet)
        self.commit()

    def _normalize_images(self, cover_image: str | None, images: list[str] | None) -> list[str]:
        normalized: list[str] = []
        for image in [cover_image, *(images or [])]:
            if image and image not in normalized:
                normalized.append(image)
        return normalized

    def _normalize_size_options(self, size_options, fallback_price) -> list[dict]:
        normalized: list[dict] = []
        for option in size_options or []:
            item = option.model_dump() if hasattr(option, "model_dump") else dict(option)
            item["label"] = (item.get("label") or self.SIZE_LABELS.get(item["key"], item["key"])).strip()
            item["image"] = item["image"].strip()
            if not item["image"]:
                raise self.bad_request("Har bir size uchun rasm kerak")
            item["price"] = self._json_decimal(item["price"])
            normalized.append(item)
        if normalized:
            order_map = {key: index for index, key in enumerate(self.SIZE_LABELS)}
            normalized.sort(key=lambda item: order_map.get(item["key"], 999))
            return normalized
        return []

    def _normalize_addon_options(self, addon_options) -> list[dict]:
        normalized: list[dict] = []
        for index, option in enumerate(addon_options or []):
            item = option.model_dump() if hasattr(option, "model_dump") else dict(option)
            item_id = (item.get("id") or f"addon_{index + 1}").strip().lower().replace(" ", "_")
            item_name = item["name"].strip()
            item_image = item["image"].strip()
            if not item_name:
                raise self.bad_request("Add-on nomi bo'sh bo'lmasligi kerak")
            if not item_image:
                raise self.bad_request("Har bir add-on uchun rasm kerak")
            normalized.append(
                {
                    "id": item_id,
                    "name": item_name,
                    "price": self._json_decimal(item["price"]),
                    "image": item_image,
                }
            )
        return normalized

    def _resolve_primary_bouquet_fields(
        self,
        *,
        size_options: list[dict],
        fallback_price,
        fallback_image: str | None,
        fallback_images: list[str] | None,
        fallback_size: str | None,
    ):
        if size_options:
            primary = next((item for item in size_options if item["key"] == "medium"), size_options[0])
            normalized_images = self._normalize_images(
                primary["image"],
                [item["image"] for item in size_options] + list(fallback_images or []),
            )
            size_summary = ", ".join(item["label"] for item in size_options)
            return primary["price"], primary["image"], normalized_images, size_summary

        normalized_images = self._normalize_images(fallback_image, fallback_images)
        if not normalized_images:
            raise self.bad_request("Kamida bitta rasm kerak")
        return fallback_price, normalized_images[0], normalized_images, fallback_size

    def _json_decimal(self, value) -> str:
        return format(Decimal(str(value)), "f")

    def _get_managed_shop(self, shop_id: str, current_user: User) -> Shop:
        shop = self.db.get(Shop, self.parse_uuid(shop_id, "Do'kon ID"))
        if not shop:
            raise self.not_found("Do'kon")
        if current_user.has_role(UserRole.ADMIN):
            return shop
        if not current_user.has_role(UserRole.OWNER) or shop.owner_id != current_user.id:
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
