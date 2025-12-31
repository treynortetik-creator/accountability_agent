"""Database connection and session management for The Warden."""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool, NullPool
from app.config import get_settings
from app.db_models import Base

settings = get_settings()


def get_engine_kwargs():
    """Get engine configuration based on database type."""
    database_url = settings.database_url

    # Check if we're using SQLite (for local dev/testing)
    if database_url.startswith("sqlite"):
        return {
            "echo": settings.debug,
            "connect_args": {"check_same_thread": False},
            "poolclass": StaticPool,
        }

    # PostgreSQL configuration (for Supabase/production)
    # Use NullPool for serverless environments like Railway
    # CRITICAL: Disable prepared statements for Supabase pooler (Supavisor) compatibility
    # Supavisor uses transaction pooling which doesn't support prepared statements
    return {
        "echo": settings.debug,
        "poolclass": NullPool,  # Better for serverless - no persistent connections
        "connect_args": {
            "statement_cache_size": 0,  # Disable prepared statement cache for pooler
        },
    }


# Create async engine with appropriate configuration
engine = create_async_engine(
    settings.database_url,
    **get_engine_kwargs()
)

# Create async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def init_db():
    """Initialize the database, creating all tables.

    Note: For Supabase, tables are managed via migrations.
    This is primarily used for local SQLite development.
    """
    import logging
    logger = logging.getLogger(__name__)

    # Log database connection type for debugging
    db_type = "postgresql" if "postgresql" in settings.database_url else "sqlite"
    logger.info(f"Initializing database connection (type: {db_type})")

    # Only create tables if using SQLite (local dev)
    if settings.database_url.startswith("sqlite"):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    else:
        # For PostgreSQL, verify connection works
        try:
            from sqlalchemy import text
            async with engine.connect() as conn:
                result = await conn.execute(text("SELECT 1"))
                logger.info("Database connection verified successfully")
        except Exception as e:
            logger.error(f"Database connection FAILED: {type(e).__name__}: {e}")
            raise


async def get_db() -> AsyncSession:
    """Dependency to get database session."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
