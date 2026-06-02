from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload

from app.models.enums import ShopStatus, UserRole
from app.models.shop import Shop
from app.models.user import User
from app.schemas.shop import ShopCreate, ShopUpdate
from app.services.base import BaseService
from app.utils.formatters import normalize_instagram, normalize_phone_uz, normalize_telegram, slugify


class ShopService(BaseService):
    def list_shops(
        self,
        city: str | None = None,
        search: str | None = None,
        include_inactive: bool = False,
        owner_id: str | None = None,
    ) -> list[Shop]:
        statement = select(Shop).options(selectinload(Shop.owner)).order_by(Shop.created_at.desc())

        if not include_inactive:
            statement = statement.where(Shop.status == ShopStatus.ACTIVE)
        if city:
            statement = statement.where(func.lower(Shop.city) == city.strip().lower())
        if search:
            query = f"%{search.strip().lower()}%"
            statement = statement.where(
                or_(
                    func.lower(Shop.name).like(query),
                    func.lower(Shop.description).like(query),
                    func.lower(Shop.city).like(query),
                )
            )
        if owner_id:
            statement = statement.where(Shop.owner_id == self.parse_uuid(owner_id, "Owner ID"))

        return list(self.db.execute(statement).scalars().all())

    def get_shop_by_slug(self, slug: str, include_hidden: bool = False) -> Shop:
        statement = (
            select(Shop)
            .options(selectinload(Shop.owner))
            .where(func.lower(Shop.slug) == slug.strip().lower())
        )
        shop = self.db.execute(statement).scalar_one_or_none()
        if not shop:
            raise self.not_found("Do'kon")
        if not include_hidden and shop.status != ShopStatus.ACTIVE:
            raise self.not_found("Do'kon")
        return shop

    def create_shop(self, current_user: User, payload: ShopCreate) -> Shop:
        if not current_user.has_any_role(UserRole.ADMIN, UserRole.OWNER):
            raise self.forbidden("Faqat owner yoki admin do'kon yarata oladi")

        shop = Shop(
            owner_id=current_user.id,
            name=payload.name.strip(),
            slug=self._build_unique_slug(payload.slug or payload.name),
            description=payload.description,
            logo=payload.logo,
            banner=payload.banner,
            phone=normalize_phone_uz(payload.phone),
            address=payload.address.strip(),
            city=payload.city.strip() if payload.city else None,
            latitude=payload.latitude,
            longitude=payload.longitude,
            instagram=normalize_instagram(payload.instagram),
            telegram=normalize_telegram(payload.telegram),
            working_hours=payload.working_hours,
            status=payload.status if current_user.has_role(UserRole.ADMIN) else ShopStatus.PENDING,
        )
        self.db.add(shop)
        self.commit()
        return self._get_shop_for_response(shop.id)

    def update_shop(self, shop_id: str, current_user: User, payload: ShopUpdate) -> Shop:
        shop = self._get_owned_or_admin_shop(shop_id, current_user)
        data = payload.model_dump(exclude_unset=True)

        if "name" in data and data["name"] is not None:
            shop.name = data["name"].strip()
            if "slug" not in data:
                shop.slug = self._build_unique_slug(shop.name, exclude_id=shop.id)
        if "slug" in data and data["slug"] is not None:
            shop.slug = self._build_unique_slug(data["slug"], exclude_id=shop.id)
        if "phone" in data and data["phone"] is not None:
            shop.phone = normalize_phone_uz(data["phone"])
        if "address" in data and data["address"] is not None:
            shop.address = data["address"].strip()
        if "city" in data:
            shop.city = data["city"].strip() if data["city"] else None
        if "instagram" in data:
            shop.instagram = normalize_instagram(data["instagram"])
        if "telegram" in data:
            shop.telegram = normalize_telegram(data["telegram"])
        if "status" in data and data["status"] is not None:
            if not current_user.has_role(UserRole.ADMIN):
                raise self.forbidden("Faqat admin statusni o'zgartira oladi")
            shop.status = data["status"]

        for field in ("description", "logo", "banner", "latitude", "longitude", "working_hours"):
            if field in data:
                setattr(shop, field, data[field])

        self.db.add(shop)
        self.commit()
        return self._get_shop_for_response(shop.id)

    def _get_owned_or_admin_shop(self, shop_id: str, current_user: User) -> Shop:
        shop = self.db.get(Shop, self.parse_uuid(shop_id, "Do'kon ID"))
        if not shop:
            raise self.not_found("Do'kon")
        if current_user.has_role(UserRole.ADMIN):
            return shop
        if shop.owner_id != current_user.id:
            raise self.forbidden("Bu do'kon sizga tegishli emas")
        return shop

    def _get_shop_for_response(self, shop_id) -> Shop:
        statement = select(Shop).options(selectinload(Shop.owner)).where(Shop.id == shop_id)
        return self.db.execute(statement).scalar_one()

    def _build_unique_slug(self, value: str, exclude_id=None) -> str:
        base_slug = slugify(value.strip())
        slug = base_slug
        counter = 2
        while True:
            statement = select(Shop).where(func.lower(Shop.slug) == slug.lower())
            existing = self.db.execute(statement).scalar_one_or_none()
            if existing is None or existing.id == exclude_id:
                return slug
            slug = f"{base_slug}-{counter}"
            counter += 1
