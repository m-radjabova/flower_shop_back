from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.roles import require_admin
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.support_chat import SupportChatOut, SupportChatPage, SupportMessageCreate, SupportMessagePage, SupportMessageOut
from app.schemas.upload import FileUploadOut
from app.services.support_chat_service import SupportChatService
from app.services.upload_service import UploadService

router = APIRouter(prefix="/support-chats", tags=["Support chats"])


@router.get("/me", response_model=SupportChatOut)
def get_my_support_chat(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.has_role(UserRole.OWNER):
        raise SupportChatService.forbidden("Faqat owner admin bilan yozisha oladi")
    service = SupportChatService(db)
    chat = service.get_or_create_owner_chat(current_user)
    return service.serialize_chat(chat, viewer_role=current_user.role)


@router.get("/me/messages", response_model=SupportMessagePage)
def get_my_support_messages(
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.has_role(UserRole.OWNER):
        raise SupportChatService.forbidden("Faqat owner admin bilan yozisha oladi")
    service = SupportChatService(db)
    chat = service.get_or_create_owner_chat(current_user)
    return service.list_messages(chat, limit=limit, offset=offset)


@router.post("/me/messages", response_model=SupportMessageOut)
async def send_my_support_message(
    payload: SupportMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.has_role(UserRole.OWNER):
        raise SupportChatService.forbidden("Faqat owner admin bilan yozisha oladi")
    service = SupportChatService(db)
    chat = service.get_or_create_owner_chat(current_user)
    result = await service.send_message(chat, current_user, payload)
    return result["message"]


@router.post("/me/attachments", response_model=FileUploadOut)
async def upload_my_support_attachment(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.has_role(UserRole.OWNER):
        raise SupportChatService.forbidden("Faqat owner fayl yubora oladi")
    return await UploadService(db).upload_chat_file(file)


@router.post("/me/read", response_model=SupportChatOut)
async def mark_my_support_chat_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.has_role(UserRole.OWNER):
        raise SupportChatService.forbidden("Faqat owner admin bilan yozisha oladi")
    service = SupportChatService(db)
    chat = service.get_or_create_owner_chat(current_user)
    return await service.mark_read(chat, current_user)


@router.get("", response_model=SupportChatPage)
def list_support_chats(
    limit: int = Query(default=30, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    search: str | None = Query(default=None, min_length=1, max_length=120),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return SupportChatService(db).list_admin_chats(limit=limit, offset=offset, search=search)


@router.get("/{owner_id}", response_model=SupportChatOut)
def get_support_chat(
    owner_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    service = SupportChatService(db)
    chat = service.get_admin_chat(owner_id)
    return service.serialize_chat(chat, viewer_role=current_user.role)


@router.get("/{owner_id}/messages", response_model=SupportMessagePage)
def get_support_chat_messages(
    owner_id: str,
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    service = SupportChatService(db)
    chat = service.get_admin_chat(owner_id)
    service.ensure_chat_access(chat, current_user)
    return service.list_messages(chat, limit=limit, offset=offset)


@router.post("/{owner_id}/messages", response_model=SupportMessageOut)
async def send_support_chat_message(
    owner_id: str,
    payload: SupportMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    service = SupportChatService(db)
    chat = service.get_admin_chat(owner_id)
    result = await service.send_message(chat, current_user, payload)
    return result["message"]


@router.post("/{owner_id}/attachments", response_model=FileUploadOut)
async def upload_support_chat_attachment(
    owner_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    SupportChatService(db).get_admin_chat(owner_id)
    return await UploadService(db).upload_chat_file(file)


@router.post("/{owner_id}/read", response_model=SupportChatOut)
async def mark_support_chat_read(
    owner_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    service = SupportChatService(db)
    chat = service.get_admin_chat(owner_id)
    return await service.mark_read(chat, current_user)
