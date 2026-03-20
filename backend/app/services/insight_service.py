import uuid
from typing import List

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.insight import Insight

async def get_insights(db: AsyncSession, user_id: uuid.UUID, page: int = 1, limit: int = 20) -> tuple[List[Insight], int]:
    count_stmt = select(func.count()).select_from(Insight).where(Insight.user_id == user_id, Insight.type == "insight")
    result_count = await db.execute(count_stmt)
    total = result_count.scalar() or 0
    
    offset = (page - 1) * limit
    stmt = select(Insight).where(Insight.user_id == user_id, Insight.type == "insight").order_by(Insight.week_start.desc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    
    return list(result.scalars().all()), total

async def get_latest_insight(db: AsyncSession, user_id: uuid.UUID) -> Insight:
    stmt = select(Insight).where(Insight.user_id == user_id, Insight.type == "insight").order_by(Insight.week_start.desc()).limit(1)
    result = await db.execute(stmt)
    insight = result.scalar_one_or_none()
    
    if not insight:
        return None
    return insight

async def get_suggestions(db: AsyncSession, user_id: uuid.UUID) -> List[Insight]:
    stmt = select(Insight).where(Insight.user_id == user_id, Insight.type == "suggestion").order_by(Insight.generated_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()

async def dismiss_suggestion(db: AsyncSession, suggestion_id: uuid.UUID, user_id: uuid.UUID) -> None:
    stmt = select(Insight).where(Insight.id == suggestion_id, Insight.user_id == user_id, Insight.type == "suggestion")
    result = await db.execute(stmt)
    suggestion = result.scalar_one_or_none()
    
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
        
    await db.delete(suggestion)
    await db.commit()
