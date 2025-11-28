"""Pytest configuration and fixtures for Good Shepherd tests."""

from __future__ import annotations

import asyncio
import os
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.database.models import Base
from backend.processing.api_main import app


# Use a test database
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://goodshepherd:goodshepherd@localhost:5432/goodshepherd_test",
)


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create a test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a database session for each test."""
    session_factory = async_sessionmaker(test_engine, expire_on_commit=False)

    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async HTTP client for testing the API."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_event_data() -> dict:
    """Sample event data for testing."""
    return {
        "title": "Test Security Alert",
        "summary": "A test security event for unit testing purposes.",
        "category": "security",
        "region": "europe",
        "source_url": "https://example.com/feed",
        "link": "https://example.com/article/123",
        "confidence": 0.85,
        "geocode": {"lat": 50.0, "lon": 10.0, "display_name": "Germany"},
        "verification_status": "pending",
        "credibility_score": 0.7,
        "threat_level": "medium",
    }


@pytest.fixture
def sample_alert_rule_data() -> dict:
    """Sample alert rule data for testing."""
    return {
        "name": "Test Alert Rule",
        "description": "A test alert rule for unit testing.",
        "regions": ["europe", "asia"],
        "categories": ["security", "political"],
        "minimum_threat": "medium",
        "minimum_credibility": 0.6,
        "lookback_minutes": 60,
        "priority": "high",
        "auto_ack": False,
    }
