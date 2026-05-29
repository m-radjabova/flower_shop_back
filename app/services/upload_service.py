import base64
import re
from uuid import uuid4

import httpx
from fastapi import UploadFile

from app.core.config import settings
from app.schemas.upload import ImageUploadOut
from app.services.base import BaseService


class UploadService(BaseService):
    allowed_content_types = {"image/jpeg", "image/png", "image/webp", "image/gif"}
    max_file_size = 6 * 1024 * 1024

    async def upload_image(self, file: UploadFile, folder: str = "/flower-shop/reviews") -> ImageUploadOut:
        if not settings.IMAGEKIT_PRIVATE_KEY:
            raise self.bad_request("ImageKit private key sozlanmagan")
        if file.content_type not in self.allowed_content_types:
            raise self.bad_request("Faqat JPG, PNG, WEBP yoki GIF rasm yuklash mumkin")

        content = await file.read()
        if not content:
            raise self.bad_request("Rasm fayli bo'sh")
        if len(content) > self.max_file_size:
            raise self.bad_request("Rasm hajmi 6MB dan oshmasligi kerak")

        safe_filename = self._safe_filename(file.filename or "review-image")
        encoded_file = base64.b64encode(content).decode("utf-8")

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "https://upload.imagekit.io/api/v1/files/upload",
                data={
                    "file": encoded_file,
                    "fileName": f"{uuid4().hex}-{safe_filename}",
                    "folder": folder,
                    "useUniqueFileName": "true",
                },
                auth=(settings.IMAGEKIT_PRIVATE_KEY, ""),
            )

        if response.status_code >= 400:
            raise self.bad_request("Rasmni ImageKit'ga yuklab bo'lmadi")

        data = response.json()
        return ImageUploadOut(
            url=data["url"],
            file_id=data["fileId"],
            name=data["name"],
            thumbnail_url=data.get("thumbnailUrl"),
        )

    async def delete_image(self, file_id: str, *, ignore_missing: bool = False) -> None:
        if not file_id:
            return
        if not settings.IMAGEKIT_PRIVATE_KEY:
            raise self.bad_request("ImageKit private key sozlanmagan")

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.delete(
                f"https://api.imagekit.io/v1/files/{file_id}",
                auth=(settings.IMAGEKIT_PRIVATE_KEY, ""),
            )

        if response.status_code == 404 and ignore_missing:
            return

        if response.status_code >= 400:
            raise self.bad_request("ImageKit'dan rasmni o'chirib bo'lmadi")

    @staticmethod
    def _safe_filename(filename: str) -> str:
        name = filename.strip().replace(" ", "-").lower()
        return re.sub(r"[^a-z0-9._-]", "", name) or "image"
