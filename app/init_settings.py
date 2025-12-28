"""Initialize persistent settings from environment variables."""

import logging
import json
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_models import Settings
from app.config import get_settings

logger = logging.getLogger(__name__)
config = get_settings()

# Hardcoded Google Calendar credentials (for persistence across deploys)
GCAL_CLIENT_ID = "REDACTED"
GCAL_CLIENT_SECRET = "REDACTED"


async def init_calendar_credentials(db: AsyncSession, base_url: str = None) -> bool:
    """Initialize Google Calendar credentials if not already set up.

    Returns True if calendar is configured (existing or newly set up).
    """
    try:
        # Check if already configured with valid tokens
        result = await db.execute(
            select(Settings).where(Settings.key == "google_calendar_token")
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

        # Set up initial credentials from hardcoded values or env vars
        client_id = config.gcal_client_id or GCAL_CLIENT_ID
        client_secret = config.gcal_client_secret or GCAL_CLIENT_SECRET

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
            setting = Settings(key="google_calendar_token", value=json.dumps(token_data))
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
        result = await db.execute(
            select(Settings).where(Settings.key == "system_prompt")
        )
        existing = result.scalar_one_or_none()

        if not existing:
            setting = Settings(key="system_prompt", value=WARDEN_SYSTEM_PROMPT)
            db.add(setting)
            await db.flush()
            logger.info("System prompt initialized in database")
        else:
            # Update to latest version
            existing.value = WARDEN_SYSTEM_PROMPT
            await db.flush()
            logger.info("System prompt updated to latest version")

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


async def initialize_all(db: AsyncSession, base_url: str = None) -> dict:
    """Initialize all persistent settings.

    Call this during application startup.
    """
    results = {
        "system_prompt": False,
        "calendar": False,
        "telegram_webhook": False,
    }

    # Initialize system prompt
    await init_system_prompt(db)
    results["system_prompt"] = True

    # Initialize calendar credentials
    results["calendar"] = await init_calendar_credentials(db, base_url)

    # Initialize Telegram webhook (if base_url provided)
    if base_url:
        results["telegram_webhook"] = await init_telegram_webhook(base_url)

    logger.info(f"Initialization complete: {results}")
    return results
