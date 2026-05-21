from app.schemas.common import ORMModel


class ImageUploadOut(ORMModel):
    url: str
    file_id: str
    name: str
    thumbnail_url: str | None = None
