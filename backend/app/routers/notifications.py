from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import uuid
import json

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.notification import Notification
from app.schemas.notification import NotificationResponse, PushSubscription
from app.services import notification_service
from sqlalchemy import select

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.get("", response_model=List[NotificationResponse])
async def get_notifications(
    unread_only: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await notification_service.get_user_notifications(db, current_user.id, unread_only)

@router.post("/subscribe")
async def subscribe_push(
    subscription: PushSubscription,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    current_user.push_subscription = json.dumps(subscription.model_dump())
    await db.commit()
    return {"detail": "Subscription saved"}

@router.put("/{notification_id}/read")
async def mark_read(
    notification_id: uuid.UUID = Path(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await notification_service.mark_as_read(db, notification_id, current_user.id)
    return {"detail": "Marked as read"}

@router.put("/read-all")
async def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Notification).where(Notification.user_id == current_user.id, Notification.is_read == False)
    result = await db.execute(stmt)
    notifications = result.scalars().all()
    
    for n in notifications:
        n.is_read = True
        
    await db.commit()
    return {"detail": "All marked as read"}
