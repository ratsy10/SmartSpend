from fastapi import APIRouter, Depends, Query, Path, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import uuid

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.insight import InsightResponse, PaginatedInsights
from app.services import insight_service, ai_service, expense_service, budget_service, category_service
from app.schemas.expense import ExpenseFilter
from datetime import date

router = APIRouter(prefix="/insights", tags=["insights"])

@router.get("", response_model=PaginatedInsights)
async def get_insights(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    insights, total = await insight_service.get_insights(db, current_user.id, page, limit)
    pages = (total + limit - 1) // limit if limit > 0 else 1
    return {
        "data": insights,
        "total": total,
        "page": page,
        "pages": pages
    }

from typing import List, Optional

@router.get("/latest", response_model=Optional[InsightResponse])
async def get_latest_insight(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await insight_service.get_latest_insight(db, current_user.id)

@router.get("/suggestions", response_model=List[InsightResponse])
async def get_suggestions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await insight_service.get_suggestions(db, current_user.id)

@router.delete("/suggestions/{id}")
async def dismiss_suggestion(
    id: uuid.UUID = Path(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await insight_service.dismiss_suggestion(db, id, current_user.id)
    return {"detail": "Suggestion dismissed"}

@router.post("/generate", response_model=list)
async def generate_ai_insights(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    today = date.today()
    start_of_month = today.replace(day=1)
    
    # Pack up the user's spending data context
    filters = ExpenseFilter(start_date=start_of_month, end_date=today)
    expenses, _ = await expense_service.get_expenses(db, current_user.id, filters, 1, 100)
    budgets = await budget_service.get_budgets(db, current_user.id)
    categories = await category_service.get_categories(db)
    cat_map = {c.id: c.name for c in categories}
    
    transactions_data = []
    for e in expenses:
        transactions_data.append({
            "amount": float(e.amount),
            "category": cat_map.get(e.category_id, "Unknown"),
            "date": str(e.expense_date),
            "merchant": e.merchant
        })
        
    budgets_data = []
    for b in budgets:
        budgets_data.append({
            "category": cat_map.get(b.category_id, "Unknown"),
            "limit": float(b.monthly_limit)
        })
        
    currency = current_user.currency or "USD"
    insights = await ai_service.generate_financial_insights(
        str(current_user.id), 
        currency,
        transactions_data, 
        budgets_data
    )
    
    if not insights:
        return [{
            "type": "optimization", 
            "title": "Analysis Pending", 
            "message": "We could not securely parse insights for your data at this moment. Please keep tracking expenses and try again later."
        }]
        
    return insights
