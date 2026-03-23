from typing import List
import os
from secrets import token_urlsafe
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    # ✅ FIX 1: Auto-generate secure random secret key if not provided (32 bytes = 43+ chars)
    secret_key: str = os.getenv("SECRET_KEY", token_urlsafe(32))
    algorithm: str = "HS256"  # ⚠️ Keep hardcoded to HS256 only (prevent alg confusion attacks)
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30
    
    database_url: str
    redis_url: str
    
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = os.getenv("GOOGLE_REDIRECT_URI", "")
    
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    
    storage_endpoint_url: str = ""
    storage_access_key: str = ""
    storage_secret_key: str = ""
    storage_bucket_name: str = "smartspend-receipts"
    storage_public_url: str = ""
    
    vapid_private_key: str = ""
    vapid_public_key: str = ""
    vapid_email: str = ""
    
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 465
    smtp_user: str = ""
    smtp_password: str = ""
    
    allowed_origins: str = os.getenv("ALLOWED_ORIGINS", "")

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        extra="ignore"
    )

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

settings = Settings()
