from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.config import settings
from app.routers import auth, categories, expenses, analytics, budgets, notifications, uploads, insights

from app.database import async_session_maker
from app.services.category_service import seed_categories
from app.scheduler import start_scheduler, stop_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    # On startup
    async with async_session_maker() as session:
        await seed_categories(session)
    start_scheduler()
    yield
    # On shutdown
    stop_scheduler()

app = FastAPI(
    title="SmartSpend API",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
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
