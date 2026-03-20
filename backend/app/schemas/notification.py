from pydantic import BaseModel, ConfigDict
from typing import Optional, Any
from datetime import datetime
import uuid

class NotificationBase(BaseModel):
    type: str # 'budget_warning' | 'budget_exceeded' | 'daily_reminder' | 'weekly_insight'
    title: str
    body: str
    data: Optional[dict] = None

class NotificationCreate(NotificationBase):
    pass

class NotificationResponse(NotificationBase):
    id: uuid.UUID
    user_id: uuid.UUID
    is_read: bool
    sent_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PushSubscription(BaseModel):
    endpoint: str
    keys: dict
