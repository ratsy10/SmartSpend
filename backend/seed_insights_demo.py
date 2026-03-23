"""
Seed script for the insights-rich demo account: insights@example.com
Creates 3 months of hand-crafted transaction data with deliberate spending patterns:

PATTERNS EMBEDDED:
1. FOOD ESCALATION: Food spending increases ~30% month-over-month (Jan: ~6k, Feb: ~8k, Mar: ~11k)
   → Insight: "Your food spending has increased 83% over the last 3 months"
2. WEEKEND SPLURGES: Entertainment spending is heavily concentrated on Fri/Sat/Sun
   → Insight: "68% of your entertainment spending happens on weekends"
3. SUBSCRIPTION CREEP: New subscriptions added each month (Jan: 3, Feb: 4, Mar: 6)
   → Insight: "Your subscription costs have doubled from ₹1,200 to ₹2,700 in 3 months"
4. LATE-NIGHT ORDERING: Many food expenses are from delivery apps (Swiggy/Zomato)
   → Insight: "You order food delivery 4x/week on average spending ₹450/order"
5. SHOPPING SPIKE: One large shopping binge per month that dominates the category
   → Insight: "Single-day shopping sprees account for 60% of your shopping budget"
6. TRANSPORT DECLINE: Transport costs drop as user switches to WFH
   → Insight: "Great job! Transport spending dropped 45% as you commute less"
7. COFFEE ADDICTION: Daily Starbucks/cafe visits, very consistent
   → Insight: "You spend ₹180/day on coffee, totaling ₹5,400/month"
8. BUDGET BREACHES: Food and Entertainment consistently break 80%+ thresholds
"""

import asyncio
import uuid
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
import bcrypt


def d(year, month, day):
    """Helper to create dates quickly."""
    return date(year, month, day)


async def seed_insights_account():
    async with async_session_maker() as session:
        # ─── Create or Reset User ───
        user_email = "insights@example.com"
        user_stmt = select(User).where(User.email == user_email)
        user_result = await session.execute(user_stmt)
        user = user_result.scalar_one_or_none()

        hashed_pw = bcrypt.hashpw("demo1234".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        if not user:
            print(f"Creating insights demo user {user_email}...")
            user = User(
                email=user_email,
                hashed_password=hashed_pw,
                full_name="Arjun Mehta",
                currency="INR",
                onboarding_done=True,
                is_verified=True
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
        else:
            print(f"User {user_email} exists. Wiping old data...")
            for model in [Expense, Insight, Budget]:
                await session.execute(delete(model).where(model.user_id == user.id))
            await session.commit()

        # ─── Get Categories ───
        cat_stmt = select(Category)
        cat_result = await session.execute(cat_stmt)
        categories = cat_result.scalars().all()
        cat_map = {c.name.lower(): c for c in categories}

        if not cat_map:
            print("ERROR: No categories found. Start the app first to seed categories.")
            return

        print(f"Found categories: {list(cat_map.keys())}")

        # ─── Create Budgets (deliberately tight to trigger alerts) ───
        budgets = [
            Budget(user_id=user.id, category_id=cat_map["food"].id, monthly_limit=Decimal("8000"), alert_at_80=True, alert_at_100=True),
            Budget(user_id=user.id, category_id=cat_map["transport"].id, monthly_limit=Decimal("4000"), alert_at_80=True, alert_at_100=True),
            Budget(user_id=user.id, category_id=cat_map["entertainment"].id, monthly_limit=Decimal("5000"), alert_at_80=True, alert_at_100=True),
            Budget(user_id=user.id, category_id=cat_map["shopping"].id, monthly_limit=Decimal("7000"), alert_at_80=True, alert_at_100=True),
            Budget(user_id=user.id, category_id=cat_map["subscriptions"].id, monthly_limit=Decimal("2000"), alert_at_80=True, alert_at_100=True),
        ]
        session.add_all(budgets)
        print("Budgets created.")

        # ─────────────────────────────────────────────
        # HAND-CRAFTED EXPENSES (Jan, Feb, Mar 2026)
        # ─────────────────────────────────────────────
        expenses = []

        def add(cat, amount, merchant, exp_date, desc, method="manual"):
            expenses.append(Expense(
                user_id=user.id,
                category_id=cat_map[cat].id,
                amount=Decimal(str(amount)),
                currency="INR",
                merchant=merchant,
                expense_date=exp_date,
                description=desc,
                input_method=method
            ))

        # ═══════════════════════════════════════════════
        # JANUARY 2026 — Baseline Month (controlled)
        # Food: ~₹6,200 | Transport: ~₹3,600 | Entertainment: ~₹3,800
        # Shopping: ~₹4,500 | Subscriptions: ₹1,200
        # ═══════════════════════════════════════════════

        # --- FOOD (Jan) - moderate, some coffee addiction starts ---
        add("food", 180, "Starbucks", d(2026,1,2), "Morning latte", "voice")
        add("food", 160, "Starbucks", d(2026,1,3), "Cappuccino + muffin")
        add("food", 185, "Starbucks", d(2026,1,5), "Morning coffee")
        add("food", 450, "Swiggy", d(2026,1,4), "Late night biryani order", "voice")
        add("food", 320, "Subway", d(2026,1,6), "Lunch sub combo")
        add("food", 175, "Starbucks", d(2026,1,7), "Morning latte")
        add("food", 520, "Zomato", d(2026,1,8), "Pizza delivery for dinner")
        add("food", 190, "Starbucks", d(2026,1,9), "Coffee & cookie")
        add("food", 380, "Local Dhaba", d(2026,1,10), "Team lunch")
        add("food", 170, "Starbucks", d(2026,1,12), "Morning coffee")
        add("food", 480, "Swiggy", d(2026,1,13), "Chinese takeout")
        add("food", 175, "Starbucks", d(2026,1,14), "Morning latte")
        add("food", 290, "Haldirams", d(2026,1,15), "Snacks & sweets")
        add("food", 185, "Starbucks", d(2026,1,16), "Cappuccino")
        add("food", 550, "Zomato", d(2026,1,18), "Weekend dinner delivery", "voice")
        add("food", 180, "Starbucks", d(2026,1,19), "Morning coffee")
        add("food", 340, "Dominos", d(2026,1,21), "Pizza night")
        add("food", 175, "Starbucks", d(2026,1,22), "Coffee")
        add("food", 430, "Swiggy", d(2026,1,25), "Late night rolls", "voice")
        add("food", 185, "Starbucks", d(2026,1,27), "Latte")
        add("food", 280, "Local Cafe", d(2026,1,29), "Brunch with friend")
        add("food", 170, "Starbucks", d(2026,1,30), "Morning coffee")

        # --- TRANSPORT (Jan) - regular commuter ---
        add("transport", 250, "Uber", d(2026,1,2), "Office commute")
        add("transport", 220, "Ola", d(2026,1,3), "Morning ride to work")
        add("transport", 280, "Uber", d(2026,1,5), "Office commute")
        add("transport", 180, "Metro", d(2026,1,6), "Metro pass reload")
        add("transport", 350, "Uber", d(2026,1,8), "Late night cab home")
        add("transport", 240, "Ola", d(2026,1,10), "Office ride")
        add("transport", 200, "Metro", d(2026,1,12), "Metro rides")
        add("transport", 280, "Uber", d(2026,1,14), "Cab to client meeting")
        add("transport", 190, "Ola", d(2026,1,16), "Return from office")
        add("transport", 300, "Uber", d(2026,1,19), "Airport drop - friend")
        add("transport", 250, "Uber", d(2026,1,21), "Office commute")
        add("transport", 220, "Ola", d(2026,1,23), "Office ride")
        add("transport", 180, "Metro", d(2026,1,26), "Metro")
        add("transport", 160, "Rapido", d(2026,1,28), "Quick bike ride")

        # --- ENTERTAINMENT (Jan) - weekend-heavy pattern ---
        # Weekday
        add("entertainment", 199, "Hotstar", d(2026,1,5), "Monthly subscription")
        # Weekend splurges
        add("entertainment", 850, "PVR Cinemas", d(2026,1,4), "Movie night (Sat)")  # Saturday
        add("entertainment", 650, "Bowling Alley", d(2026,1,11), "Sunday bowling")  # Sunday
        add("entertainment", 400, "Steam", d(2026,1,10), "New game purchase (Sat)")  # Saturday
        add("entertainment", 750, "PVR Cinemas", d(2026,1,18), "Movie + popcorn (Sun)")  # Sunday
        add("entertainment", 350, "YouTube Premium", d(2026,1,20), "Annual family plan")
        add("entertainment", 600, "Board Game Cafe", d(2026,1,25), "Sunday game night")  # Sunday

        # --- SHOPPING (Jan) - one spike + scattered small ---
        add("shopping", 450, "Amazon", d(2026,1,3), "Phone case & charger")
        add("shopping", 2800, "Myntra", d(2026,1,11), "Winter sale shopping spree")  # BIG SPIKE
        add("shopping", 350, "Amazon", d(2026,1,15), "Books")
        add("shopping", 580, "Big Bazaar", d(2026,1,20), "Household supplies")
        add("shopping", 320, "Amazon", d(2026,1,28), "USB hub")

        # --- SUBSCRIPTIONS (Jan) - 3 services = ₹1,197 ---
        add("subscriptions", 499, "Netflix", d(2026,1,1), "Monthly Netflix")
        add("subscriptions", 119, "Spotify", d(2026,1,1), "Monthly Spotify")
        add("subscriptions", 579, "Gym Membership", d(2026,1,1), "January gym")

        # ═══════════════════════════════════════════════
        # FEBRUARY 2026 — Spending Starts Climbing
        # Food: ~₹8,400 (+35%) | Transport: ~₹2,800 (-22% WFH starts)
        # Entertainment: ~₹4,600 | Shopping: ~₹5,800 | Subscriptions: ₹1,697 (+1 new)
        # ═══════════════════════════════════════════════

        # --- FOOD (Feb) - escalation begins, more delivery ---
        add("food", 185, "Starbucks", d(2026,2,2), "Morning coffee")
        add("food", 620, "Swiggy", d(2026,2,2), "Late night butter chicken", "voice")
        add("food", 180, "Starbucks", d(2026,2,3), "Latte")
        add("food", 550, "Zomato", d(2026,2,4), "Sushi delivery")
        add("food", 185, "Starbucks", d(2026,2,5), "Coffee + croissant")
        add("food", 480, "Swiggy", d(2026,2,6), "Thai food delivery", "voice")
        add("food", 190, "Starbucks", d(2026,2,7), "Morning coffee")
        add("food", 380, "Local Cafe", d(2026,2,8), "Brunch")
        add("food", 175, "Starbucks", d(2026,2,9), "Cappuccino")
        add("food", 520, "Zomato", d(2026,2,10), "Burger night delivery")
        add("food", 185, "Starbucks", d(2026,2,11), "Morning latte")
        add("food", 650, "Swiggy", d(2026,2,12), "Friends dinner order", "voice")
        add("food", 180, "Starbucks", d(2026,2,13), "Coffee")
        add("food", 1200, "Barbeque Nation", d(2026,2,14), "Valentine's Day dinner")  # SPLURGE
        add("food", 190, "Starbucks", d(2026,2,16), "Post-Valentine coffee")
        add("food", 470, "Swiggy", d(2026,2,17), "Paneer tikka delivery")
        add("food", 180, "Starbucks", d(2026,2,18), "Morning coffee")
        add("food", 380, "Dominos", d(2026,2,19), "Pizza for two")
        add("food", 185, "Starbucks", d(2026,2,20), "Latte")
        add("food", 530, "Zomato", d(2026,2,21), "Weekend dinner")
        add("food", 175, "Starbucks", d(2026,2,23), "Coffee")
        add("food", 420, "Swiggy", d(2026,2,24), "Late night noodles", "voice")
        add("food", 185, "Starbucks", d(2026,2,25), "Morning coffee")
        add("food", 350, "Local Dhaba", d(2026,2,26), "Lunch")
        add("food", 180, "Starbucks", d(2026,2,27), "Cappuccino")
        add("food", 480, "Swiggy", d(2026,2,28), "End of month treat", "voice")

        # --- TRANSPORT (Feb) - declining, more WFH ---
        add("transport", 280, "Uber", d(2026,2,2), "Office commute")
        add("transport", 200, "Metro", d(2026,2,4), "Metro ride")
        add("transport", 260, "Ola", d(2026,2,6), "Office cab")
        add("transport", 350, "Uber", d(2026,2,8), "Weekend outing ride")
        add("transport", 180, "Rapido", d(2026,2,10), "Quick market trip")
        add("transport", 240, "Uber", d(2026,2,14), "Valentine's dinner ride")
        add("transport", 200, "Metro", d(2026,2,17), "Metro")
        add("transport", 280, "Ola", d(2026,2,20), "Office visit")
        add("transport", 190, "Uber", d(2026,2,23), "Grocery run cab")
        add("transport", 320, "Uber", d(2026,2,27), "Client meeting cab")

        # --- ENTERTAINMENT (Feb) - still weekend heavy ---
        add("entertainment", 199, "Hotstar", d(2026,2,5), "Monthly subscription")
        add("entertainment", 950, "PVR Cinemas", d(2026,2,7), "Saturday movie IMAX")  # Saturday
        add("entertainment", 500, "Board Game Cafe", d(2026,2,8), "Sunday games")  # Sunday
        add("entertainment", 800, "Concert Tickets", d(2026,2,14), "Valentine's live music (Sat)")  # Saturday
        add("entertainment", 350, "Steam", d(2026,2,15), "Game expansion DLC (Sun)")  # Sunday
        add("entertainment", 700, "PVR Cinemas", d(2026,2,21), "Saturday movie date")  # Saturday
        add("entertainment", 450, "Escape Room", d(2026,2,22), "Sunday team activity")  # Sunday
        add("entertainment", 650, "Comedy Club", d(2026,2,28), "Saturday standup show")  # Saturday

        # --- SHOPPING (Feb) - another spike month ---
        add("shopping", 380, "Amazon", d(2026,2,3), "Bluetooth earbuds")
        add("shopping", 3500, "Flipkart", d(2026,2,8), "Electronics sale - smartwatch")  # BIG SPIKE
        add("shopping", 280, "Amazon", d(2026,2,12), "Kitchen gadgets")
        add("shopping", 650, "H&M", d(2026,2,14), "Valentine outfit")
        add("shopping", 420, "Amazon", d(2026,2,20), "Desk lamp & organizer")
        add("shopping", 560, "Big Bazaar", d(2026,2,25), "Monthly household groceries")

        # --- SUBSCRIPTIONS (Feb) - 4 services = ₹1,697 (+ChatGPT) ---
        add("subscriptions", 499, "Netflix", d(2026,2,1), "Monthly Netflix")
        add("subscriptions", 119, "Spotify", d(2026,2,1), "Monthly Spotify")
        add("subscriptions", 579, "Gym Membership", d(2026,2,1), "February gym")
        add("subscriptions", 500, "ChatGPT Plus", d(2026,2,1), "New subscription - ChatGPT")

        # ═══════════════════════════════════════════════
        # MARCH 2026 — Peak Spending (1st-23rd only, today is Mar 23)
        # Food: ~₹10,800 (+29% 🔥) | Transport: ~₹2,000 (-29% full WFH)
        # Entertainment: ~₹5,200 | Shopping: ~₹8,500 (!!!) | Subscriptions: ₹2,697 (+2 new)
        # ═══════════════════════════════════════════════

        # --- FOOD (Mar) - full escalation, daily coffee + heavy delivery ---
        add("food", 195, "Starbucks", d(2026,3,1), "Morning coffee")
        add("food", 680, "Swiggy", d(2026,3,1), "Midnight cravings biryani", "voice")
        add("food", 190, "Starbucks", d(2026,3,2), "Morning latte")
        add("food", 580, "Zomato", d(2026,3,2), "Sushi again")
        add("food", 195, "Starbucks", d(2026,3,3), "Coffee + sandwich")
        add("food", 750, "Swiggy", d(2026,3,4), "Expensive Thai food order", "voice")
        add("food", 190, "Starbucks", d(2026,3,5), "Morning coffee")
        add("food", 520, "Zomato", d(2026,3,5), "Pasta delivery")
        add("food", 195, "Starbucks", d(2026,3,6), "Cappuccino")
        add("food", 620, "Swiggy", d(2026,3,7), "North Indian feast delivery", "voice")
        add("food", 190, "Starbucks", d(2026,3,8), "Weekend coffee")
        add("food", 850, "Mainland China", d(2026,3,8), "Dinner out with family")
        add("food", 195, "Starbucks", d(2026,3,9), "Morning latte")
        add("food", 480, "Swiggy", d(2026,3,10), "Rolls & kebabs", "voice")
        add("food", 190, "Starbucks", d(2026,3,11), "Coffee")
        add("food", 550, "Zomato", d(2026,3,11), "Pizza + wings combo")
        add("food", 195, "Starbucks", d(2026,3,12), "Morning coffee")
        add("food", 720, "Swiggy", d(2026,3,13), "Holi party food order", "voice")
        add("food", 190, "Starbucks", d(2026,3,14), "Coffee")
        add("food", 480, "Zomato", d(2026,3,15), "Burgers delivery")
        add("food", 195, "Starbucks", d(2026,3,16), "Morning latte")
        add("food", 580, "Swiggy", d(2026,3,17), "Korean food delivery", "voice")
        add("food", 190, "Starbucks", d(2026,3,18), "Coffee + cookies")
        add("food", 650, "Zomato", d(2026,3,19), "Japanese ramen + gyoza")
        add("food", 195, "Starbucks", d(2026,3,20), "Friday latte")
        add("food", 1500, "Taj Restaurant", d(2026,3,21), "Birthday dinner splurge")  # MEGA SPLURGE
        add("food", 190, "Starbucks", d(2026,3,22), "Morning coffee")
        add("food", 580, "Swiggy", d(2026,3,23), "Sunday delivery", "voice")

        # --- TRANSPORT (Mar) - minimal, almost fully WFH ---
        add("transport", 320, "Uber", d(2026,3,2), "Rare office visit")
        add("transport", 180, "Rapido", d(2026,3,5), "Market run")
        add("transport", 250, "Uber", d(2026,3,8), "Family outing ride")
        add("transport", 200, "Ola", d(2026,3,12), "Doctor appointment")
        add("transport", 280, "Uber", d(2026,3,16), "Client meeting")
        add("transport", 380, "Uber", d(2026,3,21), "Birthday dinner cab")
        add("transport", 190, "Rapido", d(2026,3,23), "Quick errand")

        # --- ENTERTAINMENT (Mar) - weekend domination continues ---
        add("entertainment", 199, "Hotstar", d(2026,3,1), "Monthly subscription")
        add("entertainment", 1100, "PVR Cinemas", d(2026,3,1), "IMAX premiere Sunday")  # Sunday
        add("entertainment", 600, "Board Game Cafe", d(2026,3,7), "Saturday games marathon")  # Saturday
        add("entertainment", 450, "Steam", d(2026,3,8), "Game sale Sunday")  # Sunday
        add("entertainment", 950, "Live Concert", d(2026,3,14), "Saturday concert tickets")  # Saturday
        add("entertainment", 500, "Karaoke Bar", d(2026,3,15), "Sunday karaoke night")  # Sunday
        add("entertainment", 800, "PVR Cinemas", d(2026,3,21), "Saturday blockbuster")  # Saturday
        add("entertainment", 600, "Theme Park", d(2026,3,22), "Sunday adventure park")  # Sunday

        # --- SHOPPING (Mar) - biggest spike yet ---
        add("shopping", 5200, "Flipkart", d(2026,3,5), "New tablet purchase")  # MEGA SPIKE
        add("shopping", 480, "Amazon", d(2026,3,8), "Tablet cover & stylus")
        add("shopping", 750, "H&M", d(2026,3,12), "Spring wardrobe refresh")
        add("shopping", 380, "Amazon", d(2026,3,15), "Books bundle")
        add("shopping", 620, "IKEA", d(2026,3,18), "Desk organizers")
        add("shopping", 1100, "Myntra", d(2026,3,21), "Birthday outfit shopping")

        # --- SUBSCRIPTIONS (Mar) - 6 services = ₹2,697 (2 new: iCloud + Notion) ---
        add("subscriptions", 499, "Netflix", d(2026,3,1), "Monthly Netflix")
        add("subscriptions", 119, "Spotify", d(2026,3,1), "Monthly Spotify")
        add("subscriptions", 579, "Gym Membership", d(2026,3,1), "March gym (haven't gone)")
        add("subscriptions", 500, "ChatGPT Plus", d(2026,3,1), "Monthly ChatGPT")
        add("subscriptions", 750, "iCloud Storage", d(2026,3,1), "New - 2TB iCloud plan")
        add("subscriptions", 250, "Notion Pro", d(2026,3,1), "New - Notion workspace")

        session.add_all(expenses)
        print(f"Created {len(expenses)} expenses across 3 months.")

        # ─── Pre-Generated Insights ───
        print("Creating pre-generated insights...")

        insights = [
            Insight(
                user_id=user.id,
                type="insight",
                week_start=d(2026,3,17),
                content="📈 **Food spending is skyrocketing.** You spent ₹6,200 in January, ₹8,400 in February, and you're already at ₹10,800 in March. That's a **74% increase** in just 3 months. Delivery apps (Swiggy & Zomato) account for ₹4,200 this month alone.",
                top_category="food",
                total_spent=Decimal("25400")
            ),
            Insight(
                user_id=user.id,
                type="suggestion",
                week_start=d(2026,3,10),
                content="☕ **Coffee habit alert:** You've visited Starbucks **22 times** this month, spending an average of ₹190 per visit. That's roughly ₹5,500/month — more than many people's entire food budget. Switching to home-brewed coffee 3 days/week could save you **₹2,800/month**.",
                top_category="food",
                total_spent=Decimal("5500")
            ),
            Insight(
                user_id=user.id,
                type="insight",
                week_start=d(2026,3,3),
                content="🎮 **Weekend warrior pattern detected.** A striking **72% of your entertainment spending** happens between Friday and Sunday. Your average weekend entertainment spend is ₹1,400 compared to just ₹200 on weekdays.",
                top_category="entertainment",
                total_spent=Decimal("5200")
            ),
            Insight(
                user_id=user.id,
                type="suggestion",
                week_start=d(2026,2,24),
                content="📱 **Subscription creep warning!** You started January with 3 subscriptions (₹1,197/mo). Now you have **6 subscriptions costing ₹2,697/mo** — a 125% increase. Your **Gym Membership (₹579/mo)** shows no correlated activity. Canceling unused subscriptions could save ₹829/month.",
                top_category="subscriptions",
                total_spent=Decimal("2697")
            ),
            Insight(
                user_id=user.id,
                type="insight",
                week_start=d(2026,2,17),
                content="🛍️ **Impulse shopping pattern:** In each of the last 3 months, a single shopping day accounts for **55-65% of your total shopping spend**. January's ₹2,800 Myntra spree, February's ₹3,500 Flipkart haul, and March's ₹5,200 tablet purchase. Consider implementing a 48-hour cooling-off period before big purchases.",
                top_category="shopping",
                total_spent=Decimal("18800")
            ),
            Insight(
                user_id=user.id,
                type="suggestion",
                week_start=d(2026,2,10),
                content="🚗 **Great news on transport!** Your commute spending dropped **45% from January (₹3,600) to March (₹2,000)** as you've shifted to working from home. You're saving roughly ₹1,600/month — consider redirecting this into your savings!",
                top_category="transport",
                total_spent=Decimal("2000")
            ),
            Insight(
                user_id=user.id,
                type="insight",
                week_start=d(2026,1,27),
                content="🌙 **Late-night food delivery habit:** Over the last 3 months, you've placed **18 delivery orders after 9 PM**, averaging ₹520 per order. These late-night orders cost 15-20% more than daytime equivalents due to surge pricing and impulse ordering.",
                top_category="food",
                total_spent=Decimal("9360")
            ),
            Insight(
                user_id=user.id,
                type="suggestion",
                week_start=d(2026,1,20),
                content="💡 **Budget optimization tip:** Your Food budget is set at ₹8,000 but you've exceeded it 2 out of 3 months. Meanwhile, your Transport budget (₹4,000) is consistently underutilized at ~50%. Consider reallocating ₹2,000 from Transport to Food for a more realistic budget.",
                top_category="food",
                total_spent=Decimal("8000")
            ),
        ]

        session.add_all(insights)
        await session.commit()
        print(f"Created {len(insights)} AI insights.")

        # ─── Summary ───
        total_spent = sum(e.amount for e in expenses)
        print(f"\n{'='*50}")
        print(f"✅ Insights Demo Account Ready!")
        print(f"   Email: {user_email}")
        print(f"   Password: (set via OTP or direct DB)")
        print(f"   Total Expenses: {len(expenses)}")
        print(f"   Total Spent: ₹{total_spent:,.2f}")
        print(f"   Months: January - March 2026")
        print(f"   Insights: {len(insights)}")
        print(f"{'='*50}")


if __name__ == "__main__":
    asyncio.run(seed_insights_account())
