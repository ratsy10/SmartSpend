from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import date
from decimal import Decimal

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.analytics import MonthlySummary, MonthlyTotal, CategoryBreakdown, DailyTotal, BudgetStatus
from app.services import analytics_service

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/summary", response_model=MonthlySummary)
async def get_summary(
    year: int = Query(...),
    month: int = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await analytics_service.get_monthly_summary(db, current_user.id, year, month)

@router.get("/trend", response_model=List[MonthlyTotal])
async def get_trend(
    months: int = Query(6, ge=1, le=24),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await analytics_service.get_spending_trend(db, current_user.id, months)

@router.get("/breakdown", response_model=List[CategoryBreakdown])
async def get_breakdown(
    start_date: date = Query(...),
    end_date: date = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await analytics_service.get_category_breakdown(db, current_user.id, start_date, end_date)

@router.get("/daily", response_model=List[DailyTotal])
async def get_daily(
    year: int = Query(...),
    month: int = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await analytics_service.get_daily_spending(db, current_user.id, year, month)

@router.get("/budget-status", response_model=List[BudgetStatus])
async def get_budget_status(
    year: int = Query(...),
    month: int = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await analytics_service.get_budget_status(db, current_user.id, year, month)
