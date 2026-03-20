import boto3
from botocore.exceptions import ClientError
from app.config import settings
import logging

logger = logging.getLogger(__name__)

def get_s3_client():
    if not settings.storage_access_key:
        return None
        
    return boto3.client(
        's3',
        endpoint_url=settings.storage_endpoint_url,
        aws_access_key_id=settings.storage_access_key,
        aws_secret_access_key=settings.storage_secret_key,
    )

async def upload_file(file_bytes: bytes, filename: str, content_type: str) -> str:
    s3_client = get_s3_client()
    
    # If not configured, just return a dummy URL for local development
    if not s3_client:
        logger.warning("Storage is not configured. Returning dummy URL.")
        return f"http://localhost:8000/mock-storage/{filename}"
        
    try:
        s3_client.put_object(
            Bucket=settings.storage_bucket_name,
            Key=filename,
            Body=file_bytes,
            ContentType=content_type,
            ACL='public-read' # Assuming public-read, otherwise use pre-signed URLs
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
