from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_user_optional
from app.dependencies.roles import require_roles
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.bouquet import BouquetCreate, BouquetOut, BouquetPage, BouquetUpdate
from app.services.bouquet_service import BouquetService

router = APIRouter(prefix="/bouquets", tags=["Bouquets"])


@router.get("", response_model=list[BouquetOut])
def list_bouquets(
    shop_id: str | None = None,
    category_id: str | None = None,
    search: str | None = None,
    include_hidden: bool = False,
    limit: int | None = Query(default=None, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    if include_hidden and (current_user is None or not current_user.has_role(UserRole.ADMIN)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")

    return BouquetService(db).list_bouquets(
        shop_id=shop_id,
        category_id=category_id,
        search=search,
        include_hidden=include_hidden,
        limit=limit,
        offset=offset,
    )


@router.get("/page", response_model=BouquetPage)
def list_bouquets_page(
    shop_id: str | None = None,
    category_id: str | None = None,
    search: str | None = None,
    include_hidden: bool = False,
    limit: int = Query(default=12, ge=1, le=48),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    if include_hidden and (current_user is None or not current_user.has_role(UserRole.ADMIN)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")

    return BouquetService(db).list_bouquets_page(
        shop_id=shop_id,
        category_id=category_id,
        search=search,
        include_hidden=include_hidden,
        limit=limit,
        offset=offset,
    )


@router.get("/manage/shop/{shop_id}", response_model=list[BouquetOut])
def list_managed_bouquets(
    shop_id: str,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.OWNER)),
    db: Session = Depends(get_db),
):
    return BouquetService(db).list_managed_bouquets(shop_id, current_user)


@router.get("/{bouquet_id}", response_model=BouquetOut)
def get_bouquet(bouquet_id: str, db: Session = Depends(get_db)):
    return BouquetService(db).get_bouquet(bouquet_id)


@router.post("", response_model=BouquetOut)
def create_bouquet(
    payload: BouquetCreate,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.OWNER)),
    db: Session = Depends(get_db),
):
    return BouquetService(db).create_bouquet(current_user, payload)


@router.patch("/{bouquet_id}", response_model=BouquetOut)
def update_bouquet(
    bouquet_id: str,
    payload: BouquetUpdate,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.OWNER)),
    db: Session = Depends(get_db),
):
    return BouquetService(db).update_bouquet(bouquet_id, current_user, payload)


@router.delete("/{bouquet_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_bouquet(
    bouquet_id: str,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.OWNER)),
    db: Session = Depends(get_db),
):
    BouquetService(db).delete_bouquet(bouquet_id, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
