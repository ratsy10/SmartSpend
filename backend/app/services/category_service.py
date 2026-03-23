from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.category import Category

SYSTEM_CATEGORIES = [
    {"name": "Food", "icon": "utensils", "color": "#f59e0b"},
    {"name": "Transport", "icon": "car", "color": "#3b82f6"},
    {"name": "Entertainment", "icon": "film", "color": "#8b5cf6"},
    {"name": "Rent", "icon": "home", "color": "#ef4444"},
    {"name": "Shopping", "icon": "shopping-bag", "color": "#ec4899"},
    {"name": "Health", "icon": "activity", "color": "#10b981"},
    {"name": "Education", "icon": "book-open", "color": "#06b6d4"},
    {"name": "Electricity", "icon": "lightbulb", "color": "#eab308"},
    {"name": "Utilities", "icon": "zap", "color": "#6b7280"},
    {"name": "Miscellaneous", "icon": "box", "color": "#84cc16"},
    {"name": "Subscriptions", "icon": "repeat", "color": "#a855f7"},
]

async def seed_categories(db: AsyncSession):
    # Check if there are system categories
    stmt = select(Category).where(Category.user_id.is_(None))
    result = await db.execute(stmt)
    existing_categories = result.scalars().all()
    
    existing_names = [cat.name for cat in existing_categories]
    
    new_categories = []
    for sys_cat in SYSTEM_CATEGORIES:
        if sys_cat["name"] not in existing_names:
            category = Category(
                name=sys_cat["name"],
                icon=sys_cat["icon"],
                color=sys_cat["color"],
                is_custom=False,
                is_active=True
            )
            new_categories.append(category)
            
    if new_categories:
        db.add_all(new_categories)
        await db.commit()

async def get_categories(db: AsyncSession, user_id=None):
    from sqlalchemy import or_
    if user_id:
        stmt = select(Category).where(
            or_(Category.user_id.is_(None), Category.user_id == user_id)
        ).where(Category.is_active == True)
    else:
        stmt = select(Category).where(Category.is_active == True)
        
    result = await db.execute(stmt)
    return result.scalars().all()
