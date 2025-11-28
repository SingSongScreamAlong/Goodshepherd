"""Async SQLAlchemy session management."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from .config import DatabaseSettings
from .models import Base

_settings = DatabaseSettings.from_env()
_engine: AsyncEngine = create_async_engine(_settings.url, echo=_settings.echo)
_session_factory = async_sessionmaker(_engine, expire_on_commit=False)


async def init_database() -> None:
    """Initialize database schema if it does not yet exist."""

    async with _engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    """Provide a transactional scope around a series of operations."""

    session: AsyncSession = _session_factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency that yields an async session."""

    async with session_scope() as session:
        yield session
