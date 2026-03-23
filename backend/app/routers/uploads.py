from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from app.dependencies import get_current_user
from app.models.user import User
from app.services import storage_service

router = APIRouter(prefix="/uploads", tags=["uploads"])

# Allowed file types for receipt uploads (development mode allows more flexibility)
ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "application/pdf"
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB max

@router.post("")
async def upload_general_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    # ✅ Production validation - development allows any reasonable type/size
    production = (storage_service.settings.app_env == "production") if storage_service else False
    
    try:
        content_type = file.content_type.lower()
        filename_lower = file.filename.lower()
        
        # Check allowed types in production, allow more flexibility in dev
        if production and content_type not in ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"File type '{file.content_type}' is not allowed. Only images (JPEG/PNG) and PDFs are permitted."
            )
        
        # Check file size
        if file.size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum allowed is {MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        bytes_data = await file.read()
        url = await storage_service.upload_file(bytes_data, file.filename, file.content_type)
        return {"url": url}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
