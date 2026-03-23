import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import asyncio
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
import uuid
import random

from app.database import async_session_maker
from app.models.user import User
from app.models.expense import Expense
from app.models.category import Category
from app.models.budget import Budget
from app.services.auth_service import get_password_hash

MERCHANTS = {
    "Food": ["Starbucks", "McDonalds", "Zomato", "Swiggy", "Domino's", "Local Grocery", "Whole Foods", "Trader Joe's"],
    "Transport": ["Uber", "Lyft", "Metro", "Gas Station", "Train Ticket", "City Bus"],
    "Entertainment": ["Netflix", "Spotify", "Movie Theater", "Steam Games", "Concert Tickets"],
    "Shopping": ["Amazon", "Target", "Walmart", "H&M", "Zara", "Apple Store"],
    "Bills": ["Electric Bill", "Water Bill", "Internet Provider", "Phone Plan"],
    "Health": ["Pharmacy", "Gym Membership", "Doctor Visit"],
    "Travel": ["Delta Airlines", "Airbnb", "Hotel", "Train Line"],
    "Education": ["Udemy", "Coursera", "Textbook", "Library Fee"]
}

async def generate():
    async with async_session_maker() as session:
        # 1. Create User
        email = "demo@example.com"
        password = "password123"
        
        stmt = select(User).where(User.email == email)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            user = User(
                email=email,
                full_name="Demo User",
                hashed_password=get_password_hash(password),
                currency="INR",
                is_verified=True,
                timezone="Asia/Kolkata"
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            print(f"Created user {email} / {password}")
        else:
            print(f"User {email} already exists. Using existing.")

        # 2. Fetch Categories
        stmt = select(Category)
        result = await session.execute(stmt)
        categories = result.scalars().all()
        if not categories:
            print("No categories found! Please start main.py first to seed them.")
            return

        # 3. Generate category budgets
        print("Generating budgets per category...")
        for cat in categories:
            stmt = select(Budget).where(Budget.user_id == user.id, Budget.category_id == cat.id)
            res = await session.execute(stmt)
            if not res.scalar_one_or_none():
                limit = random.randint(60, 200) * 100
                budget = Budget(
                    user_id=user.id,
                    category_id=cat.id,
                    monthly_limit=float(limit)
                )
                session.add(budget)
        
        await session.commit()

        # 4. Generate 2-4 daily transactions for exactly the last 90 days
        print("Starting transaction generation for the last 90 days...")
        today = datetime.now(timezone.utc)
        total_expenses = 0
        
        # Determine date range
        start_date = today - timedelta(days=90)
        
        # Loop exactly 90 days
        for day_offset in range(91):
            current_date = start_date + timedelta(days=day_offset)
            
            # Generate 2 to 4 expenses per day
            num_tx = random.randint(2, 4)
            for _ in range(num_tx):
                # Randomize time within the day
                hour = random.randint(8, 22)
                minute = random.randint(0, 59)
                tx_date = current_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                cat = random.choice(categories)
                merchant_list = MERCHANTS.get(cat.name)
                merchant = random.choice(merchant_list) if merchant_list else "Misc Store"
                
                # Vary amount logically (Food 50-800, Shopping 500-5000, etc)
                if cat.name == "Food":
                    amount = random.randint(5, 80) * 10
                elif cat.name == "Shopping":
                    amount = random.randint(10, 100) * 50
                elif cat.name == "Bills":
                    amount = random.randint(5, 30) * 100
                elif cat.name == "Transport":
                    amount = random.randint(2, 20) * 20
                else:
                    amount = random.randint(10, 50) * 10
                
                expense = Expense(
                    user_id=user.id,
                    amount=float(amount),
                    currency=user.currency,
                    category_id=cat.id,
                    merchant=merchant,
                    description=f"{merchant} Purchase",
                    input_method="manual",
                    expense_date=tx_date,
                    notes=f"Auto-generated mock transaction",
                    created_at=tx_date
                )
                session.add(expense)
                total_expenses += 1
                
            # commit in batches of days to avoid massive single transaction blocks
            if day_offset % 10 == 0:
                await session.commit()
                
        await session.commit()
        print(f"Successfully generated {total_expenses} mock transactions for account {email} with password: {password}")

if __name__ == '__main__':
    asyncio.run(generate())
