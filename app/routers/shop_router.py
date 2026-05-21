from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.shop import ShopCreate, ShopOut, ShopUpdate
from app.services.shop_service import ShopService

router = APIRouter(prefix="/shops", tags=["Shops"])


@router.get("", response_model=list[ShopOut])
def list_shops(
    city: str | None = None,
    search: str | None = None,
    include_inactive: bool = False,
    owner_id: str | None = None,
    db: Session = Depends(get_db),
):
    return ShopService(db).list_shops(
        city=city,
        search=search,
        include_inactive=include_inactive,
        owner_id=owner_id,
    )


@router.get("/me", response_model=list[ShopOut])
def list_my_shops(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return ShopService(db).list_shops(include_inactive=True, owner_id=str(current_user.id))


@router.get("/{slug}", response_model=ShopOut)
def get_shop(slug: str, db: Session = Depends(get_db)):
    return ShopService(db).get_shop_by_slug(slug)


@router.post("", response_model=ShopOut)
def create_shop(
    payload: ShopCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ShopService(db).create_shop(current_user, payload)


@router.patch("/{shop_id}", response_model=ShopOut)
def update_shop(
    shop_id: str,
    payload: ShopUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ShopService(db).update_shop(shop_id, current_user, payload)
