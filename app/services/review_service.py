from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.bouquet import Bouquet
from app.models.enums import BouquetStatus, UserRole
from app.models.order import Order
from app.models.review import Review
from app.models.shop import Shop
from app.models.user import User
from app.schemas.review import ReviewCreate, ReviewModerationUpdate
from app.services.base import BaseService


class ReviewService(BaseService):
    def list_my_reviews(self, user_id: str) -> list[Review]:
        statement = (
            select(Review)
            .options(selectinload(Review.user))
            .where(Review.user_id == self.parse_uuid(user_id, "User ID"))
            .order_by(Review.created_at.desc())
        )
        return list(self.db.execute(statement).scalars().all())

    def list_reviews(self, shop_id: str | None = None, bouquet_id: str | None = None) -> list[Review]:
        statement = (
            select(Review)
            .options(selectinload(Review.user), selectinload(Review.bouquet))
            .where(Review.is_approved.is_(True))
            .order_by(Review.created_at.desc())
        )
        if shop_id:
            statement = statement.where(Review.shop_id == self.parse_uuid(shop_id, "Do'kon ID"))
        if bouquet_id:
            statement = statement.where(Review.bouquet_id == self.parse_uuid(bouquet_id, "Buket ID"))
        return list(self.db.execute(statement).scalars().all())

    def list_managed_reviews(self, shop_id: str, current_user: User) -> list[Review]:
        shop = self.db.get(Shop, self.parse_uuid(shop_id, "Do'kon ID"))
        if not shop:
            raise self.not_found("Do'kon")
        if not current_user.has_role(UserRole.ADMIN) and shop.owner_id != current_user.id:
            raise self.forbidden("Bu reviewlarni ko'ra olmaysiz")

        statement = (
            select(Review)
            .options(selectinload(Review.user), selectinload(Review.bouquet))
            .where(Review.shop_id == shop.id)
            .order_by(Review.created_at.desc())
        )
        return list(self.db.execute(statement).scalars().all())

    def create_review(self, current_user: User, payload: ReviewCreate) -> Review:
        shop = self.db.get(Shop, payload.shop_id)
        if not shop:
            raise self.not_found("Do'kon")

        bouquet = self.db.get(Bouquet, payload.bouquet_id) if payload.bouquet_id else None
        if payload.bouquet_id and not bouquet:
            raise self.not_found("Buket")
        if bouquet and bouquet.shop_id != shop.id:
            raise self.bad_request("Buket tanlangan do'konga tegishli emas")

        order = self.db.get(Order, payload.order_id) if payload.order_id else None
        if payload.order_id and not order:
            raise self.not_found("Buyurtma")
        if order and order.user_id != current_user.id:
            raise self.forbidden("Faqat o'zingizning buyurtmangizga review qoldira olasiz")
        if order and order.shop_id != shop.id:
            raise self.bad_request("Buyurtma tanlangan do'konga tegishli emas")

        review = Review(
            user_id=current_user.id,
            shop_id=shop.id,
            bouquet_id=bouquet.id if bouquet else None,
            order_id=order.id if order else None,
            rating=payload.rating,
            text=payload.text,
            image=payload.image,
            is_approved=False,
            is_verified=order is not None,
        )
        self.db.add(review)
        self.commit()
        self._recalculate_ratings(shop.id, bouquet.id if bouquet else None)
        return self.get_review(str(review.id))

    def moderate_review(self, review_id: str, current_user: User, payload: ReviewModerationUpdate) -> Review:
        review = self.db.get(Review, self.parse_uuid(review_id, "Review ID"))
        if not review:
            raise self.not_found("Review")

        shop = self.db.get(Shop, review.shop_id)
        if not current_user.has_role(UserRole.ADMIN) and shop and shop.owner_id != current_user.id:
            raise self.forbidden("Bu reviewni boshqara olmaysiz")

        if payload.is_approved is not None:
            review.is_approved = payload.is_approved
        if payload.is_verified is not None:
            review.is_verified = payload.is_verified

        self.db.add(review)
        self.commit()
        self._recalculate_ratings(review.shop_id, review.bouquet_id)
        return self.get_review(review_id)

    def get_review(self, review_id: str) -> Review:
        statement = (
            select(Review)
            .options(selectinload(Review.user))
            .where(Review.id == self.parse_uuid(review_id, "Review ID"))
        )
        review = self.db.execute(statement).scalar_one_or_none()
        if not review:
            raise self.not_found("Review")
        return review

    def _recalculate_ratings(self, shop_id, bouquet_id) -> None:
        shop_reviews = self.list_reviews(shop_id=str(shop_id))
        shop = self.db.get(Shop, shop_id)
        if shop:
            if shop_reviews:
                shop.reviews_count = len(shop_reviews)
                shop.rating = self._average_rating(shop_reviews)
            else:
                shop.reviews_count = 0
                shop.rating = Decimal("0.0")
            self.db.add(shop)

        if bouquet_id:
            bouquet_reviews = self.list_reviews(bouquet_id=str(bouquet_id))
            bouquet = self.db.get(Bouquet, bouquet_id)
            if bouquet:
                if bouquet_reviews:
                    bouquet.reviews_count = len(bouquet_reviews)
                    bouquet.rating = self._average_rating(bouquet_reviews)
                else:
                    bouquet.reviews_count = 0
                    bouquet.rating = Decimal("0.0")
                    if bouquet.stock > 0 and bouquet.status == BouquetStatus.SOLD_OUT:
                        bouquet.status = BouquetStatus.ACTIVE
                self.db.add(bouquet)
        self.commit()

    @staticmethod
    def _average_rating(reviews: list[Review]) -> Decimal:
        average = Decimal(sum(review.rating for review in reviews)) / Decimal(len(reviews))
        return average.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
