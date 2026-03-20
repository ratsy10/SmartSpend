from pydantic import BaseModel
from decimal import Decimal
from typing import List, Optional
from datetime import date
import uuid

class CategoryBreakdown(BaseModel):
    category_id: uuid.UUID
    category_name: str
    amount: Decimal
    percentage: Decimal

class MonthlySummary(BaseModel):
    total_spent: Decimal
    total_budget: Decimal
    budget_used_pct: Decimal
    vs_last_month: Decimal
    by_category: List[CategoryBreakdown]

class MonthlyTotal(BaseModel):
    month: str
    total: Decimal

class DailyTotal(BaseModel):
    date: str
    total: Decimal

class BudgetStatus(BaseModel):
    id: uuid.UUID
    category_id: uuid.UUID
    category_name: str
    limit: Decimal
    spent: Decimal
    remaining: Decimal
    percentage: Decimal
