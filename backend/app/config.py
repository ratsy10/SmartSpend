from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30
    
    database_url: str
    redis_url: str
    
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/v1/auth/google/callback"
    
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
    
    allowed_origins: str = "http://localhost:5173,http://localhost:8000"

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        extra="ignore"
    )

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


settings = Settings()
