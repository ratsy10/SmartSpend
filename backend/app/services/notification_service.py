import json
import logging
from typing import List
import uuid
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pywebpush import webpush, WebPushException

from app.config import settings
from app.models.notification import Notification
from app.models.user import User

logger = logging.getLogger(__name__)

async def send_web_push(user: User, title: str, body: str, url: str = "/dashboard"):
    if not user.push_subscription:
        return
        
    try:
        sub_info = json.loads(user.push_subscription)
        webpush(
            subscription_info=sub_info,
            data=json.dumps({
                "title": title,
                "body": body,
                "url": url
            }),
            vapid_private_key=settings.vapid_private_key,
            vapid_claims={"sub": settings.vapid_email}
        )
    except WebPushException as ex:
        logger.error(f"Web push failed: {repr(ex)}")
        # If subscription exprired/invalid, we could clear it here
        if ex.response and ex.response.status_code in [404, 410]:
            pass
    except Exception as e:
        logger.error(f"Web push error: {e}")

async def create_notification(db: AsyncSession, user_id: uuid.UUID, type_name: str, title: str, body: str, data: dict = None) -> Notification:
    notification = Notification(
        user_id=user_id,
        type=type_name,
        title=title,
        body=body,
        data=data or {}
    )
    db.add(notification)
    await db.commit()
    await db.refresh(notification)
    return notification

async def send_budget_alert(db: AsyncSession, user: User, category_id: str, spent: Decimal, limit: Decimal, percentage: Decimal):
    # Check if we already sent this specific alert recently to avoid spam? 
    # For now, we will just send it if called
    is_exceeded = percentage >= 100
    type_name = 'budget_exceeded' if is_exceeded else 'budget_warning'
    title = f"Budget {'Exceeded' if is_exceeded else 'Warning'}"
    body = f"You've spent {settings.currency if not user.currency else user.currency}{spent:.2f} ({percentage:.0f}%) of your {limit:.2f} budget."
    
    await create_notification(db, user.id, type_name, title, body, {
        "category_id": category_id,
        "spent": float(spent),
        "limit": float(limit),
        "percentage": float(percentage)
    })
    
    await send_web_push(user, title, body, "/budgets")

async def send_daily_reminder(db: AsyncSession, user: User):
    title = "Time to log!"
    body = "Don't forget to log today's expenses!"
    
    await create_notification(db, user.id, 'daily_reminder', title, body)
    await send_web_push(user, title, body, "/expenses/add")

async def send_weekly_insight_notification(db: AsyncSession, user: User, insight_preview: str):
    title = "Weekly Insight Ready"
    body = "Your weekly spending summary is ready. " + insight_preview[:50] + "..."
    
    await create_notification(db, user.id, 'weekly_insight', title, body)
    await send_web_push(user, title, body, "/analytics")

async def mark_as_read(db: AsyncSession, notification_id: uuid.UUID, user_id: uuid.UUID):
    stmt = select(Notification).where(Notification.id == notification_id, Notification.user_id == user_id)
    result = await db.execute(stmt)
    notification = result.scalar_one_or_none()
    
    if notification:
        notification.is_read = True
        await db.commit()

async def get_user_notifications(db: AsyncSession, user_id: uuid.UUID, unread_only: bool = False) -> List[Notification]:
    stmt = select(Notification).where(Notification.user_id == user_id)
    if unread_only:
        stmt = stmt.where(Notification.is_read == False)
    stmt = stmt.order_by(Notification.created_at.desc())
    
    result = await db.execute(stmt)
    return result.scalars().all()
