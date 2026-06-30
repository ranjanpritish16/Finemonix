from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from backend.config import get_settings

settings = get_settings()

# Async engine — uses asyncpg driver (postgresql+asyncpg://...)
# Used by FastAPI (single long-lived event loop) via get_db().
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
)

# Session factory
async_session_maker = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yields an async DB session per request."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def make_task_engine():
    """
    Creates a fresh async engine + session maker, scoped to a single
    asyncio loop. Use this inside Celery tasks instead of the global
    `engine`/`async_session_maker` above.

    Celery spins up a new event loop per task (via asyncio.run), and
    pooled asyncpg connections can't be reused across different loops —
    reusing the global engine across tasks causes intermittent
    "Event loop is closed" / "attached to a different loop" crashes.

    Always pair with `await task_engine.dispose()` in a finally block
    once the task's DB work is done, to avoid leaking connections.
    """
    task_engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        pool_pre_ping=True,
    )
    task_session_maker = async_sessionmaker(
        task_engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )
    return task_engine, task_session_maker