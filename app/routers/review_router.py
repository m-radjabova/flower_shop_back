from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.review import ReviewCreate, ReviewModerationUpdate, ReviewOut
from app.services.review_service import ReviewService

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.get("", response_model=list[ReviewOut])
def list_reviews(
    shop_id: str | None = None,
    bouquet_id: str | None = None,
    db: Session = Depends(get_db),
):
    return ReviewService(db).list_reviews(shop_id=shop_id, bouquet_id=bouquet_id)


@router.get("/me", response_model=list[ReviewOut])
def list_my_reviews(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ReviewService(db).list_my_reviews(str(current_user.id))


@router.post("", response_model=ReviewOut)
def create_review(
    payload: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ReviewService(db).create_review(current_user, payload)


@router.patch("/{review_id}/moderate", response_model=ReviewOut)
def moderate_review(
    review_id: str,
    payload: ReviewModerationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ReviewService(db).moderate_review(review_id, current_user, payload)
