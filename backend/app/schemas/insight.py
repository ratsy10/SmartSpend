from pydantic import BaseModel, ConfigDict
from decimal import Decimal
from typing import Optional, List
from datetime import date, datetime
import uuid

class InsightBase(BaseModel):
    week_start: date
    type: str = "insight"
    content: str
    total_spent: Optional[Decimal] = None
    top_category: Optional[str] = None

class InsightResponse(InsightBase):
    id: uuid.UUID
    user_id: uuid.UUID
    generated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class PaginatedInsights(BaseModel):
    data: List[InsightResponse]
    total: int
    page: int
    pages: int
