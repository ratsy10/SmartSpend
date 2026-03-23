from fastapi import APIRouter, Depends, HTTPException, Response, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis
from jose import jwt, JWTError
import httpx

from app.database import get_db
from app.dependencies import get_current_user, get_redis
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse
from app.schemas.auth import LoginRequest, Token, GoogleTokenRequest
from app.services import auth_service
from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

def set_refresh_cookie(response: Response, refresh_token: str):
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.app_env == "production",
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60
    )

from fastapi import APIRouter, Depends, HTTPException, Response, Request, status, BackgroundTasks

@router.post("/register")
async def register(user_data: UserCreate, response: Response, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    user = await auth_service.create_user(db, user_data)
    
    import random
    import string
    from datetime import datetime, timedelta, timezone
    from app.services.email_service import send_otp_email
    
    otp = ''.join(random.choices(string.digits, k=6))
    user.otp_code = otp
    user.otp_expiry = datetime.now(timezone.utc) + timedelta(minutes=10)
    
    await db.commit()
    
    # Try sending OTP email; if SMTP fails (e.g., blocked on free cloud tiers), auto-verify
    email_sent = send_otp_email(user.email, otp)
    if not email_sent:
        user.is_verified = True
        await db.commit()
        return {"message": "Account created successfully.", "require_verification": False}
    
    return {"message": "Account created. Please check your email for the verification code.", "require_verification": True}

@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    user = await auth_service.authenticate_user(db, login_data)
    
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Email not verified. Please verify your account.")
        
    access_token = auth_service.create_access_token({"sub": str(user.id)})
    refresh_token = auth_service.create_refresh_token({"sub": str(user.id)})
    
    set_refresh_cookie(response, refresh_token)
    return {"access_token": access_token, "token_type": "bearer"}

from pydantic import BaseModel
class VerifyOTPRequest(BaseModel):
    email: str
    otp_code: str

@router.post("/verify-otp", response_model=Token)
async def verify_otp(request_data: VerifyOTPRequest, response: Response, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    from datetime import datetime, timezone
    
    stmt = select(User).where(User.email == request_data.email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.is_verified:
        raise HTTPException(status_code=400, detail="Account already verified")
    if user.otp_code != request_data.otp_code:
        raise HTTPException(status_code=400, detail="Invalid OTP code")
    if user.otp_expiry and user.otp_expiry < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="OTP code expired")
        
    user.is_verified = True
    user.otp_code = None
    user.otp_expiry = None
    await db.commit()
    
    access_token = auth_service.create_access_token({"sub": str(user.id)})
    refresh_token = auth_service.create_refresh_token({"sub": str(user.id)})
    
    set_refresh_cookie(response, refresh_token)
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/refresh", response_model=Token)
async def refresh_token(request: Request, response: Response, db: AsyncSession = Depends(get_db), redis_client: redis.Redis = Depends(get_redis)):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")
        
    # Check if blacklisted
    is_blacklisted = await redis_client.get(f"bl_{refresh_token}")
    if is_blacklisted:
        raise HTTPException(status_code=401, detail="Token has been revoked")
        
    try:
        payload = jwt.decode(refresh_token, settings.secret_key, algorithms=[settings.algorithm])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
        
    # Rotate token
    await redis_client.setex(f"bl_{refresh_token}", settings.refresh_token_expire_days * 24 * 60 * 60, "true")
    
    access_token = auth_service.create_access_token({"sub": user_id})
    new_refresh_token = auth_service.create_refresh_token({"sub": user_id})
    set_refresh_cookie(response, new_refresh_token)
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/logout")
async def logout(request: Request, response: Response, redis_client: redis.Redis = Depends(get_redis)):
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        await redis_client.setex(f"bl_{refresh_token}", settings.refresh_token_expire_days * 24 * 60 * 60, "true")
    response.delete_cookie("refresh_token")
    return {"detail": "Successfully logged out"}

from fastapi.responses import RedirectResponse

@router.get("/login/google")
async def login_google():
    url = f"https://accounts.google.com/o/oauth2/v2/auth?response_type=code&client_id={settings.google_client_id}&redirect_uri={settings.google_redirect_uri}&scope=openid%20profile%20email&access_type=offline"
    return RedirectResponse(url=url)

@router.get("/google/callback")
async def google_callback(code: str, response: Response, db: AsyncSession = Depends(get_db)):
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": settings.google_client_id,
        "client_secret": settings.google_client_secret,
        "redirect_uri": settings.google_redirect_uri,
        "grant_type": "authorization_code",
    }
    async with httpx.AsyncClient() as client:
        r = await client.post(token_url, data=data)
        if r.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to exchange Google token")
        access_token_google = r.json().get("access_token")
        
        r2 = await client.get(f"https://www.googleapis.com/oauth2/v3/userinfo?access_token={access_token_google}")
        google_user = r2.json()
        
    email = google_user.get("email")
    google_id = google_user.get("sub")
    name = google_user.get("name")
    avatar = google_user.get("picture")
    
    from sqlalchemy import select
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        user = User(
            email=email,
            full_name=name,
            google_id=google_id,
            avatar_url=avatar
        )
        db.add(user)
    else:
        user.google_id = google_id
        if not user.avatar_url:
            user.avatar_url = avatar
            
    await db.commit()
    await db.refresh(user)
    
    access_token = auth_service.create_access_token({"sub": str(user.id)})
    refresh_token = auth_service.create_refresh_token({"sub": str(user.id)})
    
    frontend_url = f"{settings.frontend_url}/oauth-callback"
    redirect_response = RedirectResponse(url=f"{frontend_url}?token={access_token}")
    set_refresh_cookie(redirect_response, refresh_token)
    return redirect_response

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

from app.schemas.user import UserUpdate

@router.put("/me", response_model=UserResponse)
async def update_me(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    from datetime import time
    update_data = data.model_dump(exclude_unset=True)
    
    for k, v in update_data.items():
        if k == 'reminder_time' and v:
            h, m, s = map(int, v.split(':'))
            setattr(current_user, k, time(h, m, s))
        else:
            setattr(current_user, k, v)
            
    await db.commit()
    await db.refresh(current_user)
    return current_user
