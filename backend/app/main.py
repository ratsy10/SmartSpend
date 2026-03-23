from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware

import os
import time
from collections import defaultdict

from app.config import settings
from app.routers import auth, categories, expenses, analytics, budgets, notifications, uploads, insights

from app.database import async_session_maker, engine, Base
from app.services.category_service import seed_categories
from app.scheduler import start_scheduler, stop_scheduler

# Import all models so Base.metadata.create_all() picks them up
import app.models.user       # noqa: F401
import app.models.category   # noqa: F401
import app.models.expense    # noqa: F401
import app.models.budget     # noqa: F401
import app.models.insight    # noqa: F401


import redis.asyncio as aioredis

class RateLimiter(BaseHTTPMiddleware):
    def __init__(self, app, max_requests=10, window_seconds=300):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)

    async def dispatch(self, request, call_next):
        path = request.url.path
        ip = request.client.host if request.client else "unknown"
        
        # Apply rate limiting to sensitive endpoints only in production
        sensitive_paths = [
            "/api/v1/auth/register",
            "/api/v1/auth/login",
            "/api/v1/auth/refresh",
            "/api/v1/expenses",
            "/api/v1/analytics", 
            "/api/v1/budgets",
            "/api/v1/uploads",
            "/api/v1/notifications"
        ]
        
        # Only apply rate limiting in production
        if settings.app_env == "production" and any(path.startswith(p) for p in sensitive_paths):
            key = f"rate_limit:{ip}:{path}"
            current_time = time.time()
            
            # Setup pipelined zset sliding window
            pipeline = self.redis_client.pipeline()
            # Clear requests older than window
            pipeline.zremrangebyscore(key, 0, current_time - self.window_seconds)
            # Add current request
            pipeline.zadd(key, {str(current_time): current_time})
            # Count requests
            pipeline.zcard(key)
            # Expire key to prevent memory leaks in redis
            pipeline.expire(key, self.window_seconds)
            
            # Execute atomically
            results = await pipeline.execute()
            request_count = results[2]
            
            if request_count > self.max_requests:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many requests. Please try again later."},
                    headers={"Retry-After": str(self.window_seconds)}
                )
        
        response = await call_next(request)
        return response


def get_csp_header():
    """Get Content-Security-Policy header. Production mode uses stricter policy."""
    if settings.app_env == "production":
        return (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "img-src 'self' https: data: blob:; "
            "font-src 'self' https://fonts.gstatic.com; "
            "frame-ancestors 'none'; "
            "form-action 'self'; "
            "upgrade-insecure-requests; "
        )
    else:
        # Development mode: relaxed CSP for easier development
        return (
            "default-src 'self' 'unsafe-inline' data: blob:; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob: https://storage.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "connect-src 'self' http://localhost:8000 https://*.googleapis.com; "
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    # On startup — create tables if they don't exist (safe for production first deploy)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_session_maker() as session:
        await seed_categories(session)
    start_scheduler()
    yield
    # On shutdown
    stop_scheduler()

app = FastAPI(
    title="SmartSpend API",
    lifespan=lifespan,
)

# Add CSP headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    if settings.app_env == "production":
        response.headers["Content-Security-Policy"] = get_csp_header()
    return response

# Add rate limiting in production only (must be at module level, not inside a dispatch function)
if settings.app_env == "production":
    app.add_middleware(RateLimiter, max_requests=10, window_seconds=300)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"] if settings.app_env == "production" else ["*"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept", "Origin"]
        if settings.app_env == "production"
        else ["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(categories.router, prefix="/api/v1")
app.include_router(expenses.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(budgets.router, prefix="/api/v1")
app.include_router(notifications.router, prefix="/api/v1")
app.include_router(uploads.router, prefix="/api/v1")
app.include_router(insights.router, prefix="/api/v1")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # FIX 3: Remove .body to prevent leaking sensitive request data
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )

@app.get("/health")
async def health_check():
    return {"status": "ok"}
