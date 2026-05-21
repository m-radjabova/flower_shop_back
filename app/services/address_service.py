from sqlalchemy import select

from app.models.address import Address
from app.models.user import User
from app.schemas.address import AddressCreate, AddressUpdate
from app.services.base import BaseService


class AddressService(BaseService):
    def list_my_addresses(self, current_user: User) -> list[Address]:
        statement = (
            select(Address)
            .where(Address.user_id == current_user.id)
            .order_by(Address.is_primary.desc(), Address.updated_at.desc())
        )
        return list(self.db.execute(statement).scalars().all())

    def create_address(self, current_user: User, payload: AddressCreate) -> Address:
        if payload.is_primary:
            self._unset_primary(current_user.id)

        address = Address(
            user_id=current_user.id,
            title=payload.title,
            address_line=payload.address_line,
            city=payload.city,
            notes=payload.notes,
            latitude=payload.latitude,
            longitude=payload.longitude,
            is_primary=payload.is_primary,
        )
        self.db.add(address)
        self.commit()
        return self.refresh(address)

    def update_address(self, address_id: str, current_user: User, payload: AddressUpdate) -> Address:
        address = self._get_owned_address(address_id, current_user)

        if payload.is_primary is True:
            self._unset_primary(current_user.id)

        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(address, key, value)

        self.db.add(address)
        self.commit()
        return self.refresh(address)

    def delete_address(self, address_id: str, current_user: User) -> None:
        address = self._get_owned_address(address_id, current_user)
        self.db.delete(address)
        self.commit()

    def set_primary(self, address_id: str, current_user: User) -> Address:
        address = self._get_owned_address(address_id, current_user)
        self._unset_primary(current_user.id)
        address.is_primary = True
        self.db.add(address)
        self.commit()
        return self.refresh(address)

    def _get_owned_address(self, address_id: str, current_user: User) -> Address:
        address = self.db.get(Address, self.parse_uuid(address_id, "Address ID"))
        if not address or address.user_id != current_user.id:
            raise self.not_found("Address")
        return address

    def _unset_primary(self, user_id) -> None:
        statement = select(Address).where(Address.user_id == user_id, Address.is_primary.is_(True))
        primary_list = list(self.db.execute(statement).scalars().all())
        for item in primary_list:
            item.is_primary = False
            self.db.add(item)
