import uuid
from decimal import Decimal
from typing import List, Optional
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, cast, Numeric
from fastapi import HTTPException

from app.models.expense import Expense
from app.models.user import User
from app.models.budget import Budget
from app.schemas.expense import ExpenseCreate, ExpenseUpdate, ExpenseFilter, CategoryTotal

async def create_expense(db: AsyncSession, user: User, data: ExpenseCreate) -> Expense:
    expense = Expense(
        user_id=user.id,
        category_id=data.category_id,
        amount=data.amount,
        currency=data.currency,
        description=data.description,
        merchant=data.merchant,
        expense_date=data.expense_date,
        input_method=data.input_method,
        transcript=data.transcript,
        receipt_url=data.receipt_url,
        ai_confidence=data.ai_confidence,
        ai_raw_response=data.ai_raw_response,
        is_recurring=data.is_recurring,
        notes=data.notes
    )
    db.add(expense)
    await db.commit()
    await db.refresh(expense)
    
    # Check budget later
    await check_budget_after_expense(db, user, expense)
    
    return expense

async def get_expenses(db: AsyncSession, user_id: uuid.UUID, filters: ExpenseFilter, page: int = 1, limit: int = 20) -> tuple[List[Expense], int]:
    conditions = [Expense.user_id == user_id]
    
    if filters.start_date:
        conditions.append(Expense.expense_date >= filters.start_date)
    if filters.end_date:
        conditions.append(Expense.expense_date <= filters.end_date)
    if filters.category_id:
        conditions.append(Expense.category_id == filters.category_id)
    if filters.min_amount is not None:
        conditions.append(Expense.amount >= filters.min_amount)
    if filters.max_amount is not None:
        conditions.append(Expense.amount <= filters.max_amount)
        
    where_clause = and_(*conditions)
    
    # Count total
    count_stmt = select(func.count()).select_from(Expense).where(where_clause)
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0
    
    # Get paginated data
    offset = (page - 1) * limit
    stmt = select(Expense).where(where_clause).order_by(Expense.expense_date.desc(), Expense.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    expenses = result.scalars().all()
    
    return list(expenses), total

async def get_expense_by_id(db: AsyncSession, expense_id: uuid.UUID, user_id: uuid.UUID) -> Expense:
    stmt = select(Expense).where(Expense.id == expense_id, Expense.user_id == user_id)
    result = await db.execute(stmt)
    expense = result.scalar_one_or_none()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense

async def update_expense(db: AsyncSession, expense_id: uuid.UUID, user_id: uuid.UUID, data: ExpenseUpdate) -> Expense:
    expense = await get_expense_by_id(db, expense_id, user_id)
    
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(expense, key, value)
        
    await db.commit()
    await db.refresh(expense)
    
    # Check budget again in case amount or category changed
    await check_budget_after_expense(db, expense.user, expense)  # Assuming we can pass user or fetch it
    
    return expense

async def delete_expense(db: AsyncSession, expense_id: uuid.UUID, user_id: uuid.UUID) -> None:
    expense = await get_expense_by_id(db, expense_id, user_id)
    await db.delete(expense)
    await db.commit()

async def get_monthly_total(db: AsyncSession, user_id: uuid.UUID, year: int, month: int) -> Decimal:
    stmt = select(func.sum(Expense.amount)).where(
        Expense.user_id == user_id,
        func.extract('year', Expense.expense_date) == year,
        func.extract('month', Expense.expense_date) == month
    )
    result = await db.execute(stmt)
    total = result.scalar()
    return total or Decimal("0.00")

async def get_category_totals(db: AsyncSession, user_id: uuid.UUID, start_date: date, end_date: date) -> List[CategoryTotal]:
    stmt = select(Expense.category_id, func.sum(Expense.amount).label("total")).where(
        Expense.user_id == user_id,
        Expense.expense_date >= start_date,
        Expense.expense_date <= end_date
    ).group_by(Expense.category_id)
    
    result = await db.execute(stmt)
    totals = []
    for row in result:
        totals.append(CategoryTotal(category_id=row.category_id, total=row.total))
    return totals

async def check_budget_after_expense(db: AsyncSession, user: User, expense: Expense) -> None:
    # Get budget for category
    stmt = select(Budget).where(Budget.user_id == user.id, Budget.category_id == expense.category_id)
    result = await db.execute(stmt)
    budget = result.scalar_one_or_none()
    
    if not budget:
        return
        
    year = expense.expense_date.year
    month = expense.expense_date.month
    
    spent_stmt = select(func.sum(Expense.amount)).where(
        Expense.user_id == user.id,
        Expense.category_id == expense.category_id,
        func.extract('year', Expense.expense_date) == year,
        func.extract('month', Expense.expense_date) == month
    )
    spent_result = await db.execute(spent_stmt)
    spent = spent_result.scalar() or Decimal("0.00")
    
    pct = (spent / budget.monthly_limit) * 100 if budget.monthly_limit > 0 else Decimal("0")
    
    # Call notification service if thresholds crossed (to be implemented)
    from app.services import notification_service
    if pct >= 100 and budget.alert_at_100:
        await notification_service.send_budget_alert(db, user, str(expense.category_id), spent, budget.monthly_limit, pct)
    elif pct >= 80 and budget.alert_at_80:
        await notification_service.send_budget_alert(db, user, str(expense.category_id), spent, budget.monthly_limit, pct)
