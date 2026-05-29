from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.models.bouquet import Bouquet
from app.models.enums import BouquetStatus, UserRole
from app.models.order import Order, OrderItem
from app.models.shop import Shop
from app.models.user import User
from app.schemas.order import OrderCreate, OrderStatusUpdate
from app.services.base import BaseService
from app.services.referral_service import REFERRAL_REWARD_AMOUNT
from app.utils.formatters import normalize_phone_uz


class OrderService(BaseService):
    def create_order(self, payload: OrderCreate, current_user: User | None = None) -> Order:
        shop = self.db.get(Shop, payload.shop_id)
        if not shop:
            raise self.not_found("Do'kon")
        is_first_customer_order = False
        if current_user:
            existing_order_count = self.db.execute(
                select(func.count(Order.id)).where(Order.user_id == current_user.id)
            ).scalar_one()
            is_first_customer_order = existing_order_count == 0

        total_price = Decimal("0")
        items: list[OrderItem] = []
        for item in payload.items:
            bouquet = self.db.get(Bouquet, item.bouquet_id) if item.bouquet_id else None
            if item.bouquet_id and not bouquet:
                raise self.not_found("Buket")
            if bouquet and bouquet.shop_id != shop.id:
                raise self.bad_request("Buket boshqa do'konga tegishli")
            if bouquet and bouquet.stock < item.quantity:
                raise self.bad_request(f"{bouquet.name} uchun omborda yetarli qoldiq yo'q")

            unit_price = bouquet.price if bouquet else item.price
            item_total = unit_price * item.quantity
            total_price += item_total
            items.append(
                OrderItem(
                    bouquet_id=bouquet.id if bouquet else item.bouquet_id,
                    bouquet_name=bouquet.name if bouquet else item.bouquet_name.strip(),
                    bouquet_image=bouquet.image if bouquet else item.bouquet_image,
                    price=unit_price,
                    quantity=item.quantity,
                    total_price=item_total,
                )
            )
            if bouquet:
                bouquet.stock -= item.quantity
                if bouquet.stock <= 0:
                    bouquet.stock = 0
                    bouquet.status = BouquetStatus.SOLD_OUT
                self.db.add(bouquet)

        order = Order(
            user_id=current_user.id if current_user else None,
            shop_id=shop.id,
            customer_name=payload.customer_name.strip(),
            phone=normalize_phone_uz(payload.phone),
            email=payload.email.strip().lower() if payload.email else None,
            delivery_method=payload.delivery_method.strip(),
            address=payload.address.strip() if payload.address else None,
            payment_method=payload.payment_method.strip(),
            note=payload.note,
            total_price=total_price,
            items=items,
        )
        self.db.add(order)

        if (
            current_user
            and current_user.referred_by_id
            and not current_user.referral_reward_granted
            and is_first_customer_order
        ):
            referrer = self.db.get(User, current_user.referred_by_id)
            current_user.referral_reward_granted = True
            current_user.referral_bonus_balance += REFERRAL_REWARD_AMOUNT
            self.db.add(current_user)
            if referrer:
                referrer.referral_bonus_balance += REFERRAL_REWARD_AMOUNT
                self.db.add(referrer)

        self.commit()
        return self._load_order(order.id)

    def list_customer_orders(self, current_user: User) -> list[Order]:
        statement = (
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.user_id == current_user.id)
            .order_by(Order.created_at.desc())
        )
        return list(self.db.execute(statement).scalars().all())

    def list_shop_orders(self, shop_id: str, current_user: User) -> list[Order]:
        shop = self.db.get(Shop, self.parse_uuid(shop_id, "Do'kon ID"))
        if not shop:
            raise self.not_found("Do'kon")
        if not current_user.has_role(UserRole.ADMIN) and shop.owner_id != current_user.id:
            raise self.forbidden("Bu do'kon buyurtmalarini ko'ra olmaysiz")

        statement = (
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.shop_id == shop.id)
            .order_by(Order.created_at.desc())
        )
        return list(self.db.execute(statement).scalars().all())

    def get_order(self, order_id: str, current_user: User | None, allow_owner_admin: bool = False) -> Order:
        statement = (
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.id == self.parse_uuid(order_id, "Buyurtma ID"))
        )
        order = self.db.execute(statement).scalar_one_or_none()
        if not order:
            raise self.not_found("Buyurtma")

        if current_user is None:
            raise self.forbidden("Avtorizatsiya kerak")

        if order.user_id == current_user.id:
            return order

        if allow_owner_admin:
            shop = self.db.get(Shop, order.shop_id)
            if current_user.has_role(UserRole.ADMIN) or (shop and shop.owner_id == current_user.id):
                return order

        raise self.forbidden("Bu buyurtmaga ruxsat yo'q")

    def update_order_status(self, order_id: str, current_user: User, payload: OrderStatusUpdate) -> Order:
        order = self.get_order(order_id, current_user=current_user, allow_owner_admin=True)
        shop = self.db.get(Shop, order.shop_id)
        if not current_user.has_role(UserRole.ADMIN) and shop and shop.owner_id != current_user.id:
            raise self.forbidden("Faqat shop owner yoki admin yangilay oladi")

        if payload.status is not None:
            order.status = payload.status
        if payload.payment_status is not None:
            order.payment_status = payload.payment_status

        self.db.add(order)
        self.commit()
        return self.get_order(order_id, current_user=current_user, allow_owner_admin=True)

    def _load_order(self, order_id) -> Order:
        statement = select(Order).options(selectinload(Order.items)).where(Order.id == order_id)
        return self.db.execute(statement).scalar_one()
