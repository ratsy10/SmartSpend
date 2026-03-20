import io
import base64
import uuid
from datetime import datetime
from fastapi import UploadFile, HTTPException
from PIL import Image

from app.services import ai_service, storage_service

MAX_IMAGE_SIZE = 1600

async def process_receipt_upload(file: UploadFile, user):
    if not file.content_type.startswith("image/") and file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Invalid file type. Only images and PDFs are supported.")
        
    file_bytes = await file.read()
    
    # Process image with Pillow
    try:
        img = Image.open(io.BytesIO(file_bytes))
        
        # Convert to RGB if it's not (e.g. RGBA for PNG)
        if img.mode != 'RGB':
            img = img.convert('RGB')
            
        # Resize if too large
        if max(img.width, img.height) > MAX_IMAGE_SIZE:
            img.thumbnail((MAX_IMAGE_SIZE, MAX_IMAGE_SIZE), Image.Resampling.LANCZOS)
            
        # Save to buffer as JPEG
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=85)
        processed_bytes = buffer.getvalue()
        mime_type = "image/jpeg"
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Image processing failed: {str(e)}")
        
    # Upload to storage
    filename = f"receipts/{user.id}/{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}.jpg"
    try:
        receipt_url = await storage_service.upload_file(processed_bytes, filename, mime_type)
    except Exception:
        # Fallback if storage fails
        receipt_url = None
        
    # Convert to base64 for Gemini
    base64_img = base64.b64encode(processed_bytes).decode('utf-8')
    
    # Call AI service
    parsed_data = await ai_service.parse_receipt_image(base64_img, mime_type, user.currency)
    
    return parsed_data, receipt_url
