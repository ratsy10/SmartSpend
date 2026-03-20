from pydantic import BaseModel, ConfigDict, confloat
from typing import Optional, Any
from datetime import date, datetime
from decimal import Decimal
import uuid

class ExpenseBase(BaseModel):
    category_id: uuid.UUID
    amount: Decimal
    currency: str = "INR"
    description: str
    merchant: Optional[str] = None
    expense_date: date
    input_method: str
    transcript: Optional[str] = None
    receipt_url: Optional[str] = None
    ai_confidence: Optional[Decimal] = None
    ai_raw_response: Optional[Any] = None
    is_recurring: bool = False
    notes: Optional[str] = None

class ExpenseCreate(ExpenseBase):
    pass

class ExpenseUpdate(BaseModel):
    category_id: Optional[uuid.UUID] = None
    amount: Optional[Decimal] = None
    currency: Optional[str] = None
    description: Optional[str] = None
    merchant: Optional[str] = None
    expense_date: Optional[date] = None
    notes: Optional[str] = None
    is_recurring: Optional[bool] = None

from app.schemas.category import CategoryResponse

class ExpenseResponse(ExpenseBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    category: CategoryResponse
    
    model_config = ConfigDict(from_attributes=True)

class ExpenseFilter(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    category_id: Optional[uuid.UUID] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None

class ExpenseParseResult(BaseModel):
    amount: float
    currency: str
    category: str
    description: str
    merchant: Optional[str] = None
    expense_date: date
    confidence: float
    notes: Optional[str] = None
    
class CategoryTotal(BaseModel):
    category_id: uuid.UUID
    total: Decimal
    
class PaginatedExpenses(BaseModel):
    data: list[ExpenseResponse]
    total: int
    page: int
    pages: int
