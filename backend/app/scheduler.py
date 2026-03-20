import logging
from datetime import datetime, date, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select, func, and_

from app.database import async_session_maker
from app.models.user import User
from app.services import notification_service, ai_service
from app.models.expense import Expense
from app.models.insight import Insight

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

async def job_daily_reminders():
    # Job 1: Daily reminders
    # Schedule: every day at 5-minute intervals, check users where:
    # reminder_enabled=True AND reminder_time matches current time (±2 min) AND timezone
    now_utc = datetime.utcnow()
    
    async with async_session_maker() as db:
        stmt = select(User).where(User.reminder_enabled == True, User.reminder_time.is_not(None))
        result = await db.execute(stmt)
        users = result.scalars().all()
        
        for user in users:
            # Simplistic time-check: In production, use proper pytz timezone converting
            # Assuming reminder_time is stored as UTC for now or skipping complex TZ math for dummy
            target_time = user.reminder_time
            if target_time.hour == now_utc.hour and abs(target_time.minute - now_utc.minute) <= 2:
                await notification_service.send_daily_reminder(db, user)

async def job_weekly_insights():
    # Job 2: Weekly insights
    # Schedule: every Monday at 09:00 UTC
    today = date.today()
    last_week_start = today - timedelta(days=today.weekday() + 7)  # Monday of last week
    last_week_end = last_week_start + timedelta(days=6)
    
    async with async_session_maker() as db:
        stmt = select(User)
        result = await db.execute(stmt)
        users = result.scalars().all()
        
        for user in users:
            # Compute last week's expense data
            exp_stmt = select(Expense.category_id, func.sum(Expense.amount).label("total")).where(
                Expense.user_id == user.id,
                Expense.expense_date >= last_week_start,
                Expense.expense_date <= last_week_end
            ).group_by(Expense.category_id)
            exp_res = await db.execute(exp_stmt)
            
            data = {}
            for row in exp_res.all():
                data[str(row.category_id)] = float(row.total)
                
            total_spent = sum(data.values())
            
            insight_text = await ai_service.generate_weekly_insight(user.id, data)
            
            insight = Insight(
                user_id=user.id,
                week_start=last_week_start,
                type="insight",
                content=insight_text,
                total_spent=total_spent
            )
            db.add(insight)
            await db.commit()
            
            await notification_service.send_weekly_insight_notification(db, user, insight_text)

def start_scheduler():
    scheduler.add_job(job_daily_reminders, 'interval', minutes=5, id='daily_reminders_job')
    scheduler.add_job(job_weekly_insights, 'cron', day_of_week='mon', hour=9, id='weekly_insights_job')
    # Job 3 can be added similarly
    if not scheduler.running:
        scheduler.start()
        logger.info("Scheduler started.")

def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped.")
