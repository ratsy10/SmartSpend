from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

from app.config import settings

# SQLAlchemy engine & session maker
engine = create_async_engine(
    settings.database_url,
    echo=settings.app_env == "development",
    future=True,
    pool_pre_ping=True,
)

async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
)

from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function to yield database sessions.
    """
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
