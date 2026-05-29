from decimal import Decimal
from secrets import token_urlsafe

from sqlalchemy import func, select

from app.models.user import User
from app.schemas.referral import ReferralFriendOut, ReferralSummaryOut
from app.services.base import BaseService


REFERRAL_REWARD_AMOUNT = Decimal("10.00")


class ReferralService(BaseService):
    def get_my_summary(self, current_user: User) -> ReferralSummaryOut:
        referral_code = self.ensure_referral_code(current_user)

        referred_users = list(
            self.db.execute(
                select(User)
                .where(User.referred_by_id == current_user.id)
                .order_by(User.created_at.desc())
            ).scalars().all()
        )

        successful_referrals = sum(1 for user in referred_users if user.referral_reward_granted)
        pending_referrals = len(referred_users) - successful_referrals

        return ReferralSummaryOut(
            referral_code=referral_code,
            invite_count=len(referred_users),
            pending_referrals=pending_referrals,
            successful_referrals=successful_referrals,
            bonus_balance=current_user.referral_bonus_balance,
            reward_amount=REFERRAL_REWARD_AMOUNT,
            referred_friends=[
                ReferralFriendOut(
                    id=str(user.id),
                    full_name=user.full_name,
                    email=user.email,
                    reward_granted=user.referral_reward_granted,
                )
                for user in referred_users[:5]
            ],
        )

    def get_referrer_by_code(self, referral_code: str | None) -> User | None:
        normalized_code = (referral_code or "").strip().upper()
        if not normalized_code:
            return None

        return self.db.execute(
            select(User).where(func.upper(User.referral_code) == normalized_code)
        ).scalar_one_or_none()

    def ensure_referral_code(self, user: User) -> str:
        if user.referral_code:
            return user.referral_code

        user.referral_code = self.generate_referral_code()
        self.db.add(user)
        self.commit()
        self.refresh(user)
        return user.referral_code

    def generate_referral_code(self) -> str:
        while True:
            candidate = f"FLW-{token_urlsafe(6).upper().replace('-', '').replace('_', '')[:8]}"
            exists = self.db.execute(select(User.id).where(User.referral_code == candidate)).scalar_one_or_none()
            if exists is None:
                return candidate
