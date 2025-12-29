"""Pytest configuration and fixtures for The Warden tests."""

import os
import sys
import asyncio
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from httpx import AsyncClient, ASGITransport

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set test environment BEFORE importing app modules
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["TELEGRAM_BOT_TOKEN"] = "test_token"
os.environ["TELEGRAM_CHAT_ID"] = "test_chat_id"
os.environ["OPENROUTER_API_KEY"] = "test_key"
os.environ["API_KEY"] = "test_api_key"  # Match the auth header we'll send


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def test_engine():
    """Create a test database engine."""
    from app.db_models import Base

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def test_db(test_engine):
    """Create a test database session."""
    async_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def app():
    """Create test FastAPI app instance."""
    # Clear the settings cache to pick up test env vars
    from app.config import get_settings
    get_settings.cache_clear()

    from app.main import app as fastapi_app
    from app.database import engine
    from app.db_models import Base

    # Override the database for tests
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield fastapi_app

    # Clear cache after tests
    get_settings.cache_clear()


@pytest_asyncio.fixture
async def client(app):
    """Create an async test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"X-API-Key": "test_api_key"}  # Match API_KEY env var
    ) as client:
        yield client
