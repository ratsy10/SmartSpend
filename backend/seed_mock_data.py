import asyncio
import uuid
import random
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from decimal import Decimal

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker, engine, Base
from app.models.user import User
from app.models.category import Category
from app.models.budget import Budget
from app.models.expense import Expense
from app.models.insight import Insight

async def seed_data():
    async with async_session_maker() as session:
        # Create a mock user
        user_email = "demo@example.com"
        user_stmt = select(User).where(User.email == user_email)
        user_result = await session.execute(user_stmt)
        user = user_result.scalar_one_or_none()
        
        if not user:
            print(f"Creating mock user {user_email}...")
            user = User(
                email=user_email,
                full_name="Demo User",
                currency="INR",
                onboarding_done=True
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
        else:
            print(f"User {user_email} already exists. Cleaning up old mock data...")
            # Clean up old expenses, budgets and insights for this user
            for model in [Expense, Insight, Budget]:
                await session.execute(delete(model).where(model.user_id == user.id))
            await session.commit()
            
        # Get Categories
        cat_stmt = select(Category)
        cat_result = await session.execute(cat_stmt)
        categories = cat_result.scalars().all()
        if not categories:
            print("No categories found. Please ensure app startup seeds categories first.")
            return

        cat_map = {c.name.lower(): c for c in categories}
        
        print("Creating budgets...")
        budgets = [
            Budget(user_id=user.id, category_id=cat_map["food"].id, monthly_limit=Decimal("8000")),
            Budget(user_id=user.id, category_id=cat_map["transport"].id, monthly_limit=Decimal("3000")),
            Budget(user_id=user.id, category_id=cat_map["entertainment"].id, monthly_limit=Decimal("5000")),
            Budget(user_id=user.id, category_id=cat_map["shopping"].id, monthly_limit=Decimal("6000")),
            Budget(user_id=user.id, category_id=cat_map["subscriptions"].id, monthly_limit=Decimal("1500"))
        ]
        session.add_all(budgets)
        
        print("Creating expenses for the last 6 months...")
        today = date.today()
        expenses = []
        
        merchants = {
            "food": ["Starbucks", "Subway", "Local Cafe", "Whole Foods", "Trader Joe's", "Dominos"],
            "transport": ["Uber", "Lyft", "Metro", "Gas Station"],
            "entertainment": ["AMC Theaters", "Steam"],
            "subscriptions": ["Netflix", "Spotify", "Amazon Prime", "Gym Membership", "Patreon"],
            "shopping": ["Amazon", "Target", "H&M", "IKEA"]
        }
        
        for m in range(6):
            target_date = today - relativedelta(months=m)
            days_in_month = (target_date + relativedelta(months=1, day=1) - timedelta(days=1)).day
            num_expenses = random.randint(15, 30)
            
            for _ in range(num_expenses):
                day = random.randint(1, days_in_month)
                exp_date = target_date.replace(day=day)
                # Don't create future expenses in the current month
                if exp_date > today:
                    continue
                    
                cat_name = random.choice(list(merchants.keys()))
                category = cat_map[cat_name]
                merchant = random.choice(merchants[cat_name])
                
                # Random amount between 100 and 2500
                amount = Decimal(str(round(random.uniform(100.0, 2500.0), 2)))
                
                expenses.append(Expense(
                    user_id=user.id,
                    category_id=category.id,
                    amount=amount,
                    currency="INR",
                    merchant=merchant,
                    expense_date=exp_date,
                    description=f"{merchant} purchase",
                    input_method="manual"
                ))
                
        session.add_all(expenses)
        
        print("Creating insights...")
        insight1 = Insight(
            user_id=user.id,
            type="suggestion",
            week_start=today,
            content="You spent 25% more on dining this week compared to your average. Consider cooking at home to stay within budget.",
            top_category="food"
        )
        session.add(insight1)
        await session.flush()
        
        insight2 = Insight(
            user_id=user.id,
            type="insight",
            week_start=today,
            content="You haven't used your Premium Gym Membership in 2 months. Canceling could save you ₹4,500/mo.",
            top_category="entertainment"
        )
        session.add(insight2)
        
        await session.commit()
        print(f"Successfully seeded database! Login with {user_email}")

if __name__ == "__main__":
    asyncio.run(seed_data())
