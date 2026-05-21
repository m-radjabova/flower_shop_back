from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_user
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
):
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
):
    return BouquetService(db).list_bouquets_page(
        shop_id=shop_id,
        category_id=category_id,
        search=search,
        include_hidden=include_hidden,
        limit=limit,
        offset=offset,
    )


@router.get("/{bouquet_id}", response_model=BouquetOut)
def get_bouquet(bouquet_id: str, db: Session = Depends(get_db)):
    return BouquetService(db).get_bouquet(bouquet_id)


@router.post("", response_model=BouquetOut)
def create_bouquet(
    payload: BouquetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return BouquetService(db).create_bouquet(current_user, payload)


@router.patch("/{bouquet_id}", response_model=BouquetOut)
def update_bouquet(
    bouquet_id: str,
    payload: BouquetUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return BouquetService(db).update_bouquet(bouquet_id, current_user, payload)
