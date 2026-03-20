from pydantic import BaseModel, ConfigDict
from decimal import Decimal
from typing import Optional
from datetime import datetime
import uuid

class BudgetBase(BaseModel):
    category_id: uuid.UUID
    monthly_limit: Decimal
    alert_at_80: bool = True
    alert_at_100: bool = True

class BudgetCreate(BudgetBase):
    pass

class BudgetUpdate(BaseModel):
    monthly_limit: Optional[Decimal] = None
    alert_at_80: Optional[bool] = None
    alert_at_100: Optional[bool] = None

class BudgetResponse(BudgetBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
