from fastapi import APIRouter, Depends, UploadFile, File
from app.dependencies import get_current_user
from app.models.user import User
from app.services import storage_service

router = APIRouter(prefix="/uploads", tags=["uploads"])

@router.post("")
async def upload_general_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    bytes_data = await file.read()
    url = await storage_service.upload_file(bytes_data, file.filename, file.content_type)
    return {"url": url}
