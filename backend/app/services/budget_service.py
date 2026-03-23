import uuid
from typing import List

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.budget import Budget
from app.schemas.budget import BudgetCreate, BudgetUpdate

async def create_budget(db: AsyncSession, user_id: uuid.UUID, data: BudgetCreate) -> Budget:
    budget = Budget(
        user_id=user_id,
        category_id=data.category_id,
        monthly_limit=data.monthly_limit,
        alert_at_80=data.alert_at_80,
        alert_at_100=data.alert_at_100
    )
    db.add(budget)
    try:
        await db.commit()
        await db.refresh(budget)
        return budget
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Budget for this category already exists")

async def get_budgets(db: AsyncSession, user_id: uuid.UUID) -> List[Budget]:
    stmt = select(Budget).where(Budget.user_id == user_id)
    result = await db.execute(stmt)
    return result.scalars().all()

async def get_budget(db: AsyncSession, budget_id: uuid.UUID, user_id: uuid.UUID) -> Budget:
    stmt = select(Budget).where(Budget.id == budget_id, Budget.user_id == user_id)
    result = await db.execute(stmt)
    budget = result.scalar_one_or_none()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    return budget

async def update_budget(db: AsyncSession, budget_id: uuid.UUID, user_id: uuid.UUID, data: BudgetUpdate) -> Budget:
    budget = await get_budget(db, budget_id, user_id)
    
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(budget, key, value)
        
    await db.commit()
    await db.refresh(budget)
    
    # Run the same check calculation that expense_service does, in case lowering 
    # the budget caused the user to cross the 80% or 100% threshold retroactively.
    from sqlalchemy import func
    from datetime import date
    from app.models.expense import Expense
    from app.services import notification_service
    from app.models.user import User

    today = date.today()
    user_stmt = select(User).where(User.id == user_id)
    user_result = await db.execute(user_stmt)
    user = user_result.scalar_one_or_none()

    if user:
        spent_stmt = select(func.sum(Expense.amount)).where(
            Expense.user_id == user_id,
            Expense.category_id == budget.category_id,
            func.extract('year', Expense.expense_date) == today.year,
            func.extract('month', Expense.expense_date) == today.month
        )
        spent_result = await db.execute(spent_stmt)
        spent = spent_result.scalar() or 0
        
        pct = (spent / budget.monthly_limit) * 100 if budget.monthly_limit > 0 else 0
        
        if pct >= 100 and budget.alert_at_100:
            await notification_service.send_budget_alert(db, user, str(budget.category_id), spent, budget.monthly_limit, pct)
        elif pct >= 80 and budget.alert_at_80:
            await notification_service.send_budget_alert(db, user, str(budget.category_id), spent, budget.monthly_limit, pct)

    return budget

async def delete_budget(db: AsyncSession, budget_id: uuid.UUID, user_id: uuid.UUID) -> None:
    budget = await get_budget(db, budget_id, user_id)
    await db.delete(budget)
    await db.commit()
