from fastapi import APIRouter, Depends, Query, Path, UploadFile, File, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import date
from decimal import Decimal
import uuid

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.expense import ExpenseCreate, ExpenseUpdate, ExpenseResponse, ExpenseFilter, PaginatedExpenses, ExpenseParseResult
from app.services import expense_service, ai_service, ocr_service

router = APIRouter(prefix="/expenses", tags=["expenses"])

@router.get("", response_model=PaginatedExpenses)
async def get_expenses(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    category_id: Optional[uuid.UUID] = Query(None),
    min_amount: Optional[Decimal] = Query(None),
    max_amount: Optional[Decimal] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    filters = ExpenseFilter(
        start_date=start_date,
        end_date=end_date,
        category_id=category_id,
        min_amount=min_amount,
        max_amount=max_amount
    )
    expenses, total = await expense_service.get_expenses(db, current_user.id, filters, page, limit)
    
    pages = (total + limit - 1) // limit if limit > 0 else 1
    return {
        "data": expenses,
        "total": total,
        "page": page,
        "pages": pages
    }

@router.post("", response_model=ExpenseResponse)
async def create_expense(
    data: ExpenseCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    expense = await expense_service.create_expense(db, current_user, data)
    return expense

@router.get("/{expense_id}", response_model=ExpenseResponse)
async def get_expense(
    expense_id: uuid.UUID = Path(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    expense = await expense_service.get_expense_by_id(db, expense_id, current_user.id)
    return expense

@router.put("/{expense_id}", response_model=ExpenseResponse)
async def update_expense(
    data: ExpenseUpdate,
    expense_id: uuid.UUID = Path(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    expense = await expense_service.update_expense(db, expense_id, current_user.id, data)
    return expense

@router.delete("/{expense_id}")
async def delete_expense(
    expense_id: uuid.UUID = Path(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await expense_service.delete_expense(db, expense_id, current_user.id)
    return {"detail": "Expense deleted"}

@router.post("/parse-voice", response_model=ExpenseParseResult)
async def parse_voice(
    transcript: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    parsed = await ai_service.parse_voice_transcript(transcript, current_user.currency)
    return ExpenseParseResult(**parsed)

@router.post("/parse-receipt")
async def parse_receipt(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    parsed_data, receipt_url = await ocr_service.process_receipt_upload(file, current_user)
    parsed_data["receipt_url"] = receipt_url
    return parsed_data
