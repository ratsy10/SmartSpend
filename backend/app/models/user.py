import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Boolean, Time, Text, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True) # null for Google OAuth users
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    google_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="INR", server_default="INR")
    timezone: Mapped[str] = mapped_column(String(100), default="Asia/Kolkata", server_default="Asia/Kolkata")
    reminder_enabled: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    reminder_time: Mapped[Optional[datetime]] = mapped_column(Time, nullable=True) # e.g. 21:00 daily reminder
    onboarding_done: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    otp_code: Mapped[Optional[str]] = mapped_column(String(6), nullable=True)
    otp_expiry: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    push_subscription: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # JSON web push subscription
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
