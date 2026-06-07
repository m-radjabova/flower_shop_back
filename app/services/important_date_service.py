from sqlalchemy import func, select

from app.models.important_date import ImportantDate
from app.models.user import User
from app.schemas.important_date import ImportantDateCreate, ImportantDateUpdate
from app.services.base import BaseService


class ImportantDateService(BaseService):
    MAX_DATES_PER_USER = 24

    def list_for_user(self, current_user: User) -> list[ImportantDate]:
        statement = (
            select(ImportantDate)
            .where(ImportantDate.user_id == current_user.id)
            .order_by(ImportantDate.created_at.desc())
        )
        return list(self.db.execute(statement).scalars().all())

    def create_for_user(self, current_user: User, payload: ImportantDateCreate) -> ImportantDate:
        count_statement = select(func.count()).select_from(ImportantDate).where(ImportantDate.user_id == current_user.id)
        total = self.db.execute(count_statement).scalar_one()
        if total >= self.MAX_DATES_PER_USER:
            raise self.bad_request("Muhim sanalar limiti tugagan")

        important_date = ImportantDate(
            user_id=current_user.id,
            title=payload.title,
            event_type=payload.event_type,
            event_date=payload.event_date,
            note=payload.note,
        )
        self.db.add(important_date)
        self.commit()
        return self.refresh(important_date)

    def update_for_user(self, current_user: User, important_date_id: str, payload: ImportantDateUpdate) -> ImportantDate:
        important_date = self._get_for_user(current_user, important_date_id)
        data = payload.model_dump(exclude_unset=True)

        for field, value in data.items():
            setattr(important_date, field, value)

        self.db.add(important_date)
        self.commit()
        return self.refresh(important_date)

    def delete_for_user(self, current_user: User, important_date_id: str) -> None:
        important_date = self._get_for_user(current_user, important_date_id)
        self.db.delete(important_date)
        self.commit()

    def _get_for_user(self, current_user: User, important_date_id: str) -> ImportantDate:
        important_date_uuid = self.parse_uuid(important_date_id, "Muhim sana ID")
        statement = select(ImportantDate).where(
            ImportantDate.id == important_date_uuid,
            ImportantDate.user_id == current_user.id,
        )
        important_date = self.db.execute(statement).scalar_one_or_none()
        if not important_date:
            raise self.not_found("Muhim sana")
        return important_date
