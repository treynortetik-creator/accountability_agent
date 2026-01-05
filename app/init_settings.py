"""Initialize persistent settings from environment variables."""

import logging
import json
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_models import Settings, CheckInSchedule
from app.config import get_settings
from app.user_service import get_default_user

logger = logging.getLogger(__name__)
config = get_settings()

# Google Calendar credentials from environment variables only (no hardcoding for security)
# User can configure these in the dashboard Settings page


async def init_calendar_credentials(db: AsyncSession, base_url: str = None) -> bool:
    """Initialize Google Calendar credentials if not already set up.

    Returns True if calendar is configured (existing or newly set up).
    """
    try:
        # Get default user for settings
        user = await get_default_user(db)

        # Check if already configured with valid tokens
        result = await db.execute(
            select(Settings).where(Settings.user_id == user.id, Settings.key == "google_calendar_token")
        )
        existing = result.scalar_one_or_none()

        if existing:
            token_data = json.loads(existing.value)
            # Check if we have both client credentials and tokens
            if token_data.get("token") and token_data.get("refresh_token"):
                logger.info("Google Calendar already configured with tokens")
                return True
            # Have credentials but no tokens - need to re-auth
            if token_data.get("client_id") and token_data.get("client_secret"):
                logger.info("Google Calendar has credentials but needs authorization")
                return False

        # Set up initial credentials from env vars only
        client_id = config.gcal_client_id
        client_secret = config.gcal_client_secret

        if not client_id or not client_secret:
            logger.info("No Google Calendar credentials configured")
            return False

        # Save credentials to database
        token_data = {
            "client_id": client_id,
            "client_secret": client_secret,
        }

        if existing:
            existing.value = json.dumps(token_data)
        else:
            setting = Settings(user_id=user.id, key="google_calendar_token", value=json.dumps(token_data))
            db.add(setting)

        await db.flush()
        logger.info("Google Calendar credentials initialized - authorization required")
        return False

    except Exception as e:
        logger.error(f"Failed to initialize calendar credentials: {e}")
        return False


async def init_system_prompt(db: AsyncSession) -> None:
    """Ensure system prompt is saved to database."""
    from app.llm import WARDEN_SYSTEM_PROMPT

    try:
        # Get default user for settings
        user = await get_default_user(db)

        result = await db.execute(
            select(Settings).where(Settings.user_id == user.id, Settings.key == "system_prompt")
        )
        existing = result.scalar_one_or_none()

        if not existing:
            # Only create if no system prompt exists
            setting = Settings(user_id=user.id, key="system_prompt", value=WARDEN_SYSTEM_PROMPT)
            db.add(setting)
            await db.flush()
            logger.info("System prompt initialized in database")
        else:
            # DO NOT overwrite - user may have customized the prompt
            logger.info("System prompt already exists in database (not overwriting)")

    except Exception as e:
        logger.error(f"Failed to initialize system prompt: {e}")


async def init_telegram_webhook(base_url: str) -> bool:
    """Set up Telegram webhook if not already configured."""
    if not config.telegram_bot_token:
        logger.info("No Telegram bot token configured")
        return False

    try:
        # Check current webhook
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.telegram.org/bot{config.telegram_bot_token}/getWebhookInfo"
            )
            info = response.json()

            if info.get("ok") and info.get("result", {}).get("url"):
                current_url = info["result"]["url"]
                expected_url = f"{base_url}webhook/telegram"
                if current_url == expected_url:
                    logger.info(f"Telegram webhook already configured: {current_url}")
                    return True

            # Set up webhook
            webhook_url = f"{base_url}webhook/telegram"
            response = await client.post(
                f"https://api.telegram.org/bot{config.telegram_bot_token}/setWebhook",
                json={"url": webhook_url}
            )
            result = response.json()

            if result.get("ok"):
                logger.info(f"Telegram webhook configured: {webhook_url}")
                return True
            else:
                logger.error(f"Failed to set Telegram webhook: {result}")
                return False

    except Exception as e:
        logger.error(f"Failed to initialize Telegram webhook: {e}")
        return False


async def init_default_schedules(db: AsyncSession) -> None:
    """Initialize default check-in schedules if none exist."""
    try:
        # Get default user for schedules
        user = await get_default_user(db)

        # Check if any schedules exist for this user
        result = await db.execute(select(CheckInSchedule).where(CheckInSchedule.user_id == user.id))
        existing = result.scalars().all()

        if existing:
            logger.info(f"Found {len(existing)} existing check-in schedules")
            return

        # No schedules exist - create defaults
        default_schedules = [
            CheckInSchedule(
                user_id=user.id,
                name="Morning Check-in",
                check_in_type="daily_checkin",
                hour=4,
                minute=15,
                days_of_week="mon,tue,wed,thu,fri",
                is_active=True,
            ),
            CheckInSchedule(
                user_id=user.id,
                name="Weekly Review",
                check_in_type="weekly_review",
                hour=19,
                minute=0,
                days_of_week="sun",
                is_active=True,
            ),
        ]

        for schedule in default_schedules:
            db.add(schedule)

        await db.flush()
        logger.info(f"Created {len(default_schedules)} default check-in schedules")

    except Exception as e:
        logger.error(f"Failed to initialize default schedules: {e}")


async def initialize_all(db: AsyncSession, base_url: str = None) -> dict:
    """Initialize all persistent settings.

    Call this during application startup.
    """
    results = {
        "system_prompt": False,
        "calendar": False,
        "telegram_webhook": False,
        "schedules": False,
    }

    # Initialize system prompt
    await init_system_prompt(db)
    results["system_prompt"] = True

    # Initialize calendar credentials
    results["calendar"] = await init_calendar_credentials(db, base_url)

    # Initialize default check-in schedules
    await init_default_schedules(db)
    results["schedules"] = True

    # Initialize Telegram webhook (if base_url provided)
    if base_url:
        results["telegram_webhook"] = await init_telegram_webhook(base_url)

    logger.info(f"Initialization complete: {results}")
    return results
