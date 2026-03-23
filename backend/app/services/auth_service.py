from datetime import datetime, timedelta, timezone
from typing import Optional
import uuid

from fastapi import HTTPException

from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.models.user import User
from app.schemas.auth import LoginRequest
from app.schemas.user import UserCreate

from fastapi.concurrency import run_in_threadpool
import bcrypt

async def verify_password(plain_password: str, hashed_password: str) -> bool:
    return await run_in_threadpool(
        bcrypt.checkpw,
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )

async def get_password_hash(password: str) -> str:
    hash_bytes = await run_in_threadpool(
        bcrypt.hashpw,
        password.encode('utf-8'),
        bcrypt.gensalt()
    )
    return hash_bytes.decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def create_user(db: AsyncSession, user_create: UserCreate) -> User:
    db_user = await get_user_by_email(db, user_create.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_pwd = await get_password_hash(user_create.password)
    new_user = User(
        email=user_create.email,
        full_name=user_create.full_name,
        hashed_password=hashed_pwd,
        currency=user_create.currency,
        timezone=user_create.timezone
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

async def authenticate_user(db: AsyncSession, login_data: LoginRequest) -> User:
    user = await get_user_by_email(db, login_data.email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    is_valid = await verify_password(login_data.password, user.hashed_password)
    if not user.hashed_password or not is_valid:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return user

async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
