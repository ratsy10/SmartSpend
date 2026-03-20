import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from sqlalchemy import String, Boolean, Text, DateTime, Date, Numeric, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=False)
    category: Mapped["Category"] = relationship("Category", lazy="joined")
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="INR", server_default="INR")
    description: Mapped[str] = mapped_column(Text, nullable=False)
    merchant: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    expense_date: Mapped[date] = mapped_column(Date, nullable=False, default=datetime.today) # DATE NOT NULL DEFAULT CURRENT_DATE
    input_method: Mapped[str] = mapped_column(String(20), nullable=False) # 'voice' | 'receipt' | 'manual'
    transcript: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # original voice transcript
    receipt_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # S3 URL of uploaded receipt image
    ai_confidence: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2), nullable=True) # 0.00-1.00
    ai_raw_response: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True) # store full Gemini response
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
