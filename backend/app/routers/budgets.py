from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import uuid
from datetime import date

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.budget import BudgetCreate, BudgetUpdate, BudgetResponse
from app.schemas.analytics import BudgetStatus
from app.services import budget_service, analytics_service

router = APIRouter(prefix="/budgets", tags=["budgets"])

@router.get("", response_model=List[BudgetResponse])
async def get_budgets(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await budget_service.get_budgets(db, current_user.id)

@router.post("", response_model=BudgetResponse)
async def create_budget(
    data: BudgetCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await budget_service.create_budget(db, current_user.id, data)

@router.get("/status", response_model=List[BudgetStatus])
async def get_budget_status(
    year: int = Query(default_factory=lambda: date.today().year),
    month: int = Query(default_factory=lambda: date.today().month),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await analytics_service.get_budget_status(db, current_user.id, year, month)

@router.get("/{budget_id}", response_model=BudgetResponse)
async def get_budget(
    budget_id: uuid.UUID = Path(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await budget_service.get_budget(db, budget_id, current_user.id)

@router.put("/{budget_id}", response_model=BudgetResponse)
async def update_budget(
    data: BudgetUpdate,
    budget_id: uuid.UUID = Path(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await budget_service.update_budget(db, budget_id, current_user.id, data)

@router.delete("/{budget_id}")
async def delete_budget(
    budget_id: uuid.UUID = Path(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await budget_service.delete_budget(db, budget_id, current_user.id)
    return {"detail": "Budget deleted"}
