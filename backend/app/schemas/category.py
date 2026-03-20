from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
import uuid

class CategoryBase(BaseModel):
    name: str
    icon: str
    color: str

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    is_active: Optional[bool] = None

class CategoryResponse(CategoryBase):
    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    is_custom: bool
    is_active: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
