from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
import uuid

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse

router = APIRouter(prefix="/categories", tags=["categories"])

@router.get("", response_model=List[CategoryResponse])
async def get_categories(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Category).where(
        or_(Category.user_id.is_(None), Category.user_id == current_user.id)
    ).where(Category.is_active == True)
    
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("", response_model=CategoryResponse)
async def create_category(
    category_data: CategoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    new_category = Category(
        user_id=current_user.id,
        name=category_data.name,
        icon=category_data.icon,
        color=category_data.color,
        is_custom=True,
        is_active=True
    )
    db.add(new_category)
    await db.commit()
    await db.refresh(new_category)
    return new_category

@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: uuid.UUID,
    category_data: CategoryUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Category).where(Category.id == category_id, Category.user_id == current_user.id)
    result = await db.execute(stmt)
    category = result.scalar_one_or_none()
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found or not customizable")
        
    for key, value in category_data.model_dump(exclude_unset=True).items():
        setattr(category, key, value)
        
    await db.commit()
    await db.refresh(category)
    return category

@router.delete("/{category_id}")
async def delete_category(
    category_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Category).where(Category.id == category_id, Category.user_id == current_user.id)
    result = await db.execute(stmt)
    category = result.scalar_one_or_none()
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found or not customizable")
        
    # Soft delete
    category.is_active = False
    await db.commit()
    
    return {"detail": "Category deleted"}
