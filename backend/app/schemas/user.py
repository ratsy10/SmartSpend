from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime, time
import uuid

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    currency: str = "INR"
    timezone: str = "Asia/Kolkata"

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: uuid.UUID
    avatar_url: Optional[str] = None
    reminder_enabled: bool
    reminder_time: Optional[time] = None
    onboarding_done: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    currency: Optional[str] = None
    reminder_enabled: Optional[bool] = None
    reminder_time: Optional[str] = None
