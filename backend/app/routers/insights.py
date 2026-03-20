from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import uuid

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.insight import InsightResponse, PaginatedInsights
from app.services import insight_service

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
