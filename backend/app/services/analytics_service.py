import uuid
from decimal import Decimal
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.models.expense import Expense
from app.models.budget import Budget
from app.models.category import Category
from app.schemas.analytics import MonthlySummary, MonthlyTotal, CategoryBreakdown, DailyTotal, BudgetStatus

async def get_monthly_summary(db: AsyncSession, user_id: uuid.UUID, year: int, month: int) -> MonthlySummary:
    # Basic bounds
    start_date = date(year, month, 1)
    end_date = start_date + relativedelta(months=1, days=-1)
    
    # Last month total
    last_month_start = start_date - relativedelta(months=1)
    last_month_end = start_date - relativedelta(days=1)
    
    spent_stmt = select(func.sum(Expense.amount)).where(
        Expense.user_id == user_id,
        Expense.expense_date >= start_date,
        Expense.expense_date <= end_date
    )
    spent_res = await db.execute(spent_stmt)
    total_spent = spent_res.scalar() or Decimal("0.00")
    
    last_spent_stmt = select(func.sum(Expense.amount)).where(
        Expense.user_id == user_id,
        Expense.expense_date >= last_month_start,
        Expense.expense_date <= last_month_end
    )
    last_spent_res = await db.execute(last_spent_stmt)
    last_total_spent = last_spent_res.scalar() or Decimal("0.00")
    
    vs_last_month = Decimal("0.00")
    if last_total_spent > 0:
        vs_last_month = ((total_spent - last_total_spent) / last_total_spent) * Decimal("100.0")
        
    # Budget used pct
    budget_stmt = select(func.sum(Budget.monthly_limit)).where(Budget.user_id == user_id)
    budget_res = await db.execute(budget_stmt)
    total_budget = budget_res.scalar() or Decimal("0.00")
    
    budget_pct = Decimal("0.00")
    if total_budget > 0:
        budget_pct = (total_spent / total_budget) * Decimal("100.0")
        
    # Categories
    cat_stmt = select(Category.id, Category.name, func.sum(Expense.amount).label("amount")).join(
        Category, Category.id == Expense.category_id
    ).where(
        Expense.user_id == user_id,
        Expense.expense_date >= start_date,
        Expense.expense_date <= end_date
    ).group_by(Category.id, Category.name)
    
    cat_res = await db.execute(cat_stmt)
    by_category = []
    
    for row in cat_res.all():
        pct = (row.amount / total_spent) * Decimal("100.0") if total_spent > 0 else Decimal("0.00")
        by_category.append(CategoryBreakdown(
            category_id=row.id,
            category_name=row.name,
            amount=row.amount,
            percentage=round(pct, 2)
        ))
        
    tx_count_stmt = select(func.count(Expense.id)).where(
        Expense.user_id == user_id,
        Expense.expense_date >= start_date,
        Expense.expense_date <= end_date
    )
    tx_count_res = await db.execute(tx_count_stmt)
    transaction_count = tx_count_res.scalar() or 0
        
    return MonthlySummary(
        total_spent=round(total_spent, 2),
        total_budget=round(total_budget, 2),
        budget_used_pct=round(budget_pct, 2),
        vs_last_month=round(vs_last_month, 2),
        transaction_count=transaction_count,
        by_category=by_category
    )

async def get_spending_trend(db: AsyncSession, user_id: uuid.UUID, months: int = 6) -> List[MonthlyTotal]:
    start_date = date.today().replace(day=1) - relativedelta(months=months - 1)
    
    month_expr = func.to_char(Expense.expense_date, 'YYYY-MM')
    stmt = select(
        month_expr.label("month"),
        func.sum(Expense.amount).label("total")
    ).where(
        Expense.user_id == user_id,
        Expense.expense_date >= start_date
    ).group_by(
        month_expr
    ).order_by(month_expr)
    
    result = await db.execute(stmt)
    
    data_dict = {row.month: row.total for row in result.all()}
    
    trend = []
    for i in range(months):
        m_date = start_date + relativedelta(months=i)
        m_str = m_date.strftime("%Y-%m")
        trend.append(MonthlyTotal(
            month=m_str,
            total=data_dict.get(m_str, Decimal("0.00"))
        ))
        
    return trend

async def get_category_breakdown(db: AsyncSession, user_id: uuid.UUID, start_date: date, end_date: date) -> List[CategoryBreakdown]:
    spent_stmt = select(func.sum(Expense.amount)).where(
        Expense.user_id == user_id,
        Expense.expense_date >= start_date,
        Expense.expense_date <= end_date
    )
    spent_res = await db.execute(spent_stmt)
    total_spent = spent_res.scalar() or Decimal("0.00")
    
    if total_spent == 0:
        return []

    cat_stmt = select(Category.id, Category.name, func.sum(Expense.amount).label("amount")).join(
        Category, Category.id == Expense.category_id
    ).where(
        Expense.user_id == user_id,
        Expense.expense_date >= start_date,
        Expense.expense_date <= end_date
    ).group_by(Category.id, Category.name)
    
    cat_res = await db.execute(cat_stmt)
    by_category = []
    for row in cat_res.all():
        pct = (row.amount / total_spent) * Decimal("100.0")
        by_category.append(CategoryBreakdown(
            category_id=row.id,
            category_name=row.name,
            amount=row.amount,
            percentage=round(pct, 2)
        ))
        
    return by_category

async def get_daily_spending(db: AsyncSession, user_id: uuid.UUID, year: int, month: int) -> List[DailyTotal]:
    start_date = date(year, month, 1)
    end_date = start_date + relativedelta(months=1, days=-1)
    
    stmt = select(
        Expense.expense_date,
        func.sum(Expense.amount).label("total")
    ).where(
        Expense.user_id == user_id,
        Expense.expense_date >= start_date,
        Expense.expense_date <= end_date
    ).group_by(Expense.expense_date).order_by(Expense.expense_date)
    
    result = await db.execute(stmt)
    
    daily = []
    for row in result.all():
        daily.append(DailyTotal(
            date=row.expense_date.isoformat(),
            total=row.total
        ))
        
    return daily

async def get_budget_status(db: AsyncSession, user_id: uuid.UUID, year: int, month: int) -> List[BudgetStatus]:
    start_date = date(year, month, 1)
    end_date = start_date + relativedelta(months=1, days=-1)
    
    stmt = select(
        Budget.id,
        Budget.category_id,
        Category.name.label("category_name"),
        Budget.monthly_limit
    ).join(
        Category, Category.id == Budget.category_id
    ).where(
        Budget.user_id == user_id
    )
    
    budgets_res = await db.execute(stmt)
    budgets = budgets_res.all()
    
    statuses = []
    for bg in budgets:
        spent_stmt = select(func.sum(Expense.amount)).where(
            Expense.user_id == user_id,
            Expense.category_id == bg.category_id,
            Expense.expense_date >= start_date,
            Expense.expense_date <= end_date
        )
        spent_res = await db.execute(spent_stmt)
        spent = spent_res.scalar() or Decimal("0.00")
        
        remaining = bg.monthly_limit - spent
        pct = (spent / bg.monthly_limit) * Decimal("100.0") if bg.monthly_limit > 0 else Decimal("0.00")
        
        statuses.append(BudgetStatus(
            id=bg.id,
            category_id=bg.category_id,
            category_name=bg.category_name,
            limit=bg.monthly_limit,
            spent=spent,
            remaining=remaining,
            percentage=round(pct, 2)
        ))
        
    return statuses
