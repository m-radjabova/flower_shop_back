from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.models.enums import ShopApplicationStatus, ShopStatus, UserRole
from app.models.shop import Shop
from app.models.shop_application import ShopApplication
from app.models.user import User
from app.schemas.shop_application import ShopApplicationCreate, ShopApplicationReview
from app.services.base import BaseService
from app.utils.formatters import normalize_instagram, normalize_phone_uz, normalize_telegram, slugify


class ShopApplicationService(BaseService):
    def list_applications(self) -> list[ShopApplication]:
        statement = (
            select(ShopApplication)
            .options(selectinload(ShopApplication.user))
            .order_by(ShopApplication.created_at.desc())
        )
        return list(self.db.execute(statement).scalars().all())

    def get_latest_for_user(self, current_user: User) -> ShopApplication | None:
        statement = (
            select(ShopApplication)
            .where(ShopApplication.user_id == current_user.id)
            .order_by(ShopApplication.created_at.desc())
            .limit(1)
        )
        return self.db.execute(statement).scalar_one_or_none()

    def submit_application(self, current_user: User, payload: ShopApplicationCreate) -> tuple[ShopApplication, User]:
        self._validate_user_can_apply(current_user)

        latest_application = self.get_latest_for_user(current_user)
        if latest_application and latest_application.status == ShopApplicationStatus.PENDING:
            raise self.bad_request("Sizda allaqachon ko'rib chiqilayotgan ariza mavjud")

        owner_name = (payload.owner_full_name or current_user.full_name).strip()
        if owner_name != current_user.full_name:
            current_user.full_name = owner_name

        normalized_phone = normalize_phone_uz(payload.phone)
        if current_user.phone != normalized_phone:
            current_user.phone = normalized_phone

        application = ShopApplication(
            user_id=current_user.id,
            shop_name=payload.shop_name.strip(),
            phone=normalized_phone,
            city=payload.city.strip() if payload.city else None,
            address=payload.address.strip(),
            latitude=payload.latitude,
            longitude=payload.longitude,
            description=payload.description.strip() if payload.description else None,
            instagram=normalize_instagram(payload.instagram),
            telegram=normalize_telegram(payload.telegram),
            logo=payload.logo,
            banner=payload.banner,
            status=ShopApplicationStatus.PENDING,
            admin_comment=None,
        )

        self.db.add(current_user)
        self.db.add(application)
        self.commit()
        self.refresh(current_user)
        return self._get_application(application.id), current_user

    def review_application(self, application_id: str, payload: ShopApplicationReview) -> ShopApplication:
        application = self._get_application(application_id)
        if application.status != ShopApplicationStatus.PENDING:
            raise self.bad_request("Bu ariza allaqachon ko'rib chiqilgan")

        if payload.status not in (ShopApplicationStatus.APPROVED, ShopApplicationStatus.REJECTED):
            raise self.bad_request("Ariza faqat approved yoki rejected bo'lishi mumkin")

        application.admin_comment = payload.admin_comment.strip() if payload.admin_comment else None
        application.status = payload.status

        if payload.status == ShopApplicationStatus.APPROVED:
            user = application.user
            if not user.has_role(UserRole.OWNER):
                user.role = UserRole.OWNER
                self.db.add(user)

            if not self._user_has_shop(user.id):
                shop = Shop(
                    owner_id=user.id,
                    name=application.shop_name,
                    slug=self._build_unique_shop_slug(application.shop_name),
                    description=application.description,
                    logo=application.logo,
                    banner=application.banner,
                    phone=application.phone,
                    address=application.address,
                    city=application.city,
                    latitude=application.latitude,
                    longitude=application.longitude,
                    instagram=application.instagram,
                    telegram=application.telegram,
                    status=ShopStatus.ACTIVE,
                )
                self.db.add(shop)

        self.db.add(application)
        self.commit()
        return self._get_application(application.id)

    def _get_application(self, application_id) -> ShopApplication:
        statement = (
            select(ShopApplication)
            .options(selectinload(ShopApplication.user))
            .where(ShopApplication.id == self.parse_uuid(application_id, "Ariza ID"))
        )
        application = self.db.execute(statement).scalar_one_or_none()
        if not application:
            raise self.not_found("Ariza")
        return application

    def _user_has_shop(self, user_id) -> bool:
        statement = select(Shop.id).where(Shop.owner_id == user_id).limit(1)
        return self.db.execute(statement).scalar_one_or_none() is not None

    def _validate_user_can_apply(self, current_user: User) -> None:
        if current_user.has_role(UserRole.ADMIN):
            raise self.bad_request("Admin hisobidan shop arizasi yuborib bo'lmaydi")
        if current_user.has_role(UserRole.OWNER):
            raise self.bad_request("Siz allaqachon owner hisobidasiz")
        if current_user.has_role(UserRole.COURIER):
            raise self.bad_request("Courier hisobidan shop arizasi yuborib bo'lmaydi")
        if self._user_has_shop(current_user.id):
            raise self.bad_request("Sizning shopingiz allaqachon mavjud")

    def _build_unique_shop_slug(self, value: str) -> str:
        base_slug = slugify(value.strip())
        slug = base_slug
        counter = 2

        while True:
            statement = select(Shop).where(func.lower(Shop.slug) == slug.lower())
            existing = self.db.execute(statement).scalar_one_or_none()
            if existing is None:
                return slug
            slug = f"{base_slug}-{counter}"
            counter += 1
