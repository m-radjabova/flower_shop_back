from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.important_date import ImportantDateCreate, ImportantDateOut, ImportantDateUpdate
from app.services.important_date_service import ImportantDateService

router = APIRouter(prefix="/important-dates", tags=["Important Dates"])


@router.get("/me", response_model=list[ImportantDateOut])
def list_my_important_dates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ImportantDateService(db).list_for_user(current_user)


@router.post("/me", response_model=ImportantDateOut, status_code=status.HTTP_201_CREATED)
def create_my_important_date(
    payload: ImportantDateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ImportantDateService(db).create_for_user(current_user, payload)


@router.patch("/me/{important_date_id}", response_model=ImportantDateOut)
def update_my_important_date(
    important_date_id: str,
    payload: ImportantDateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ImportantDateService(db).update_for_user(current_user, important_date_id, payload)


@router.delete("/me/{important_date_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_important_date(
    important_date_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ImportantDateService(db).delete_for_user(current_user, important_date_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
