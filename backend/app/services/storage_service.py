import boto3
from botocore.exceptions import ClientError
from app.config import settings
import logging
import mimetypes
from datetime import timedelta, datetime

logger = logging.getLogger(__name__)

# Allowed file types for receipt uploads
ALLOWED_CONTENT_TYPES = {
    "image/jpeg", 
    "image/png", 
    "application/pdf"
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB max

def get_s3_client():
    if not settings.storage_access_key:
        return None
        
    return boto3.client(
        's3',
        endpoint_url=settings.storage_endpoint_url,
        aws_access_key_id=settings.storage_access_key,
        aws_secret_key=settings.storage_secret_key,
    )

async def upload_file(file_bytes: bytes, filename: str, content_type: str) -> str:
    s3_client = get_s3_client()
    
    # If not configured, just return a dummy URL for local development
    if not s3_client:
        logger.warning("Storage is not configured. Returning dummy URL.")
        return f"http://localhost:8000/mock-storage/{filename}"
        
    try:
        # Validate file type (development mode allows more flexibility)
        production = settings.app_env == "production"
        
        if production and content_type not in ALLOWED_CONTENT_TYPES:
            logger.error(f"Rejected upload with disallowed content type: {content_type}")
            raise ValueError("Invalid file type for receipt")
            
        # Use private ACL by default, switch to public-read only if needed (pre-signed URLs)
        acl = "private"  # ✅ Default to private for security
        
        s3_client.put_object(
            Bucket=settings.storage_bucket_name,
            Key=filename,
            Body=file_bytes,
            ContentType=content_type,
            ACL=acl  # ✅ Private by default in both dev and prod
        )
        
        return f"{settings.storage_public_url}/{filename}"
    except ClientError as e:
        logger.error(f"S3 Upload failed: {e}")
        raise e

async def delete_file(file_url: str) -> None:
    s3_client = get_s3_client()
    if not s3_client or file_url.startswith("http://localhost:8000/"):
        return
        
    try:
        key = file_url.split("/")[-1]
        s3_client.delete_object(
            Bucket=settings.storage_bucket_name,
            Key=key
        )
    except ClientError as e:
        logger.error(f"S3 Delete failed: {e}")
