from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.referral import ReferralSummaryOut
from app.services.referral_service import ReferralService

router = APIRouter(prefix="/referrals", tags=["Referrals"])


@router.get("/me", response_model=ReferralSummaryOut)
def get_my_referral_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ReferralService(db).get_my_summary(current_user)
