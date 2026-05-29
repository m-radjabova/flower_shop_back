from decimal import Decimal

from app.schemas.common import ORMModel


class ReferralFriendOut(ORMModel):
    id: str
    full_name: str
    email: str
    reward_granted: bool


class ReferralSummaryOut(ORMModel):
    referral_code: str
    invite_count: int
    pending_referrals: int
    successful_referrals: int
    bonus_balance: Decimal
    reward_amount: Decimal
    referred_friends: list[ReferralFriendOut]
