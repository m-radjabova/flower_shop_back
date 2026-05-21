from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.address import AddressCreate, AddressOut, AddressUpdate
from app.services.address_service import AddressService

router = APIRouter(prefix="/addresses", tags=["Addresses"])


@router.get("/me", response_model=list[AddressOut])
def list_my_addresses(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return AddressService(db).list_my_addresses(current_user)


@router.post("/me", response_model=AddressOut)
def create_my_address(payload: AddressCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return AddressService(db).create_address(current_user, payload)


@router.patch("/me/{address_id}", response_model=AddressOut)
def update_my_address(address_id: str, payload: AddressUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return AddressService(db).update_address(address_id, current_user, payload)


@router.delete("/me/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_address(address_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    AddressService(db).delete_address(address_id, current_user)


@router.patch("/me/{address_id}/primary", response_model=AddressOut)
def set_primary_address(address_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return AddressService(db).set_primary(address_id, current_user)
