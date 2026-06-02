from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.roles import require_admin
from app.models.user import User
from app.schemas.shop_application import (
    ShopApplicationCreate,
    ShopApplicationOut,
    ShopApplicationReview,
    ShopApplicationStatusOut,
    ShopApplicationSubmitResponse,
)
from app.services.shop_application_service import ShopApplicationService

router = APIRouter(prefix="/shop-applications", tags=["Shop Applications"])


@router.get("", response_model=list[ShopApplicationOut])
def list_shop_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return ShopApplicationService(db).list_applications()


@router.get("/me/latest", response_model=ShopApplicationStatusOut | None)
def get_my_latest_shop_application(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ShopApplicationService(db).get_latest_for_user(current_user)


@router.post("", response_model=ShopApplicationSubmitResponse)
def create_shop_application(
    payload: ShopApplicationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    application, user = ShopApplicationService(db).submit_application(current_user, payload)
    return {"application": application, "user": user}


@router.patch("/{application_id}/review", response_model=ShopApplicationOut)
def review_shop_application(
    application_id: str,
    payload: ShopApplicationReview,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return ShopApplicationService(db).review_application(application_id, payload)
