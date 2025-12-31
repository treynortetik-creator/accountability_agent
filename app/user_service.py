"""User management service for The Warden."""

from typing import Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db_models import User
from app.config import get_settings

settings = get_settings()


async def get_or_create_user(
    db: AsyncSession,
    telegram_chat_id: str,
    display_name: Optional[str] = None
) -> User:
    """Get an existing user by telegram_chat_id or create a new one.

    Args:
        db: Database session
        telegram_chat_id: The Telegram chat ID
        display_name: Optional display name for new users

    Returns:
        The User object
    """
    # Try to find existing user
    result = await db.execute(
        select(User).where(User.telegram_chat_id == telegram_chat_id)
    )
    user = result.scalar_one_or_none()

    if user:
        return user

    # Create new user
    user = User(
        telegram_chat_id=telegram_chat_id,
        display_name=display_name,
        timezone=settings.timezone,
    )
    db.add(user)
    await db.flush()  # Get the ID without committing
    return user


async def get_user_by_telegram_id(
    db: AsyncSession,
    telegram_chat_id: str
) -> Optional[User]:
    """Get a user by their Telegram chat ID.

    Args:
        db: Database session
        telegram_chat_id: The Telegram chat ID

    Returns:
        The User object or None if not found
    """
    result = await db.execute(
        select(User).where(User.telegram_chat_id == telegram_chat_id)
    )
    return result.scalar_one_or_none()


async def get_user_by_id(
    db: AsyncSession,
    user_id: UUID
) -> Optional[User]:
    """Get a user by their UUID.

    Args:
        db: Database session
        user_id: The user's UUID

    Returns:
        The User object or None if not found
    """
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()


async def get_default_user(db: AsyncSession) -> User:
    """Get the default user based on TELEGRAM_CHAT_ID from settings.

    This is a convenience method for single-user mode where the telegram
    chat ID is configured via environment variable.

    Args:
        db: Database session

    Returns:
        The User object (created if doesn't exist)
    """
    if not settings.telegram_chat_id:
        raise ValueError("TELEGRAM_CHAT_ID not configured in environment")

    return await get_or_create_user(db, settings.telegram_chat_id)


async def get_all_active_users(db: AsyncSession) -> list[User]:
    """Get all active users.

    Args:
        db: Database session

    Returns:
        List of active User objects
    """
    result = await db.execute(
        select(User).where(User.is_active == True)
    )
    return list(result.scalars().all())
