"""Telegram bot integration for The Warden."""

import logging
from datetime import datetime, time
import pytz
import httpx
from telegram import Bot, Update
from telegram.constants import ParseMode
from telegram.request import HTTPXRequest
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Configure timeout for Telegram API calls (in seconds)
TELEGRAM_CONNECT_TIMEOUT = 10.0
TELEGRAM_READ_TIMEOUT = 30.0
TELEGRAM_WRITE_TIMEOUT = 30.0


def is_quiet_hours() -> bool:
    """Check if current time is within quiet hours.

    Quiet hours span from start time to end time (crossing midnight).
    Default: 7:30 PM to 4:00 AM (no messages during sleep/wind-down).

    Note: This is a sync function for convenience. For database-stored settings,
    the values are read at startup and cached in config.
    """
    if not settings.quiet_hours_enabled:
        return False

    try:
        tz = pytz.timezone(settings.timezone)
        now = datetime.now(tz)
        current_time = now.time()

        start = time(settings.quiet_hours_start_hour, settings.quiet_hours_start_minute)
        end = time(settings.quiet_hours_end_hour, settings.quiet_hours_end_minute)

        # Handle overnight quiet hours (e.g., 7:30 PM to 4:00 AM)
        if start > end:
            # Quiet hours span midnight
            return current_time >= start or current_time < end
        else:
            # Quiet hours within same day
            return start <= current_time < end
    except Exception as e:
        logger.error(f"Error checking quiet hours: {e}")
        return False


async def is_quiet_hours_async() -> bool:
    """Async version that checks database settings for quiet hours."""
    from app.database import async_session_maker
    from sqlalchemy import select
    from app.db_models import Settings as SettingsModel

    try:
        async with async_session_maker() as db:
            # Check for database overrides
            enabled_result = await db.execute(
                select(SettingsModel).where(SettingsModel.key == "quiet_hours_enabled")
            )
            enabled_setting = enabled_result.scalar_one_or_none()
            enabled = enabled_setting.value.lower() == "true" if enabled_setting else settings.quiet_hours_enabled

            if not enabled:
                return False

            # Get time settings from DB or fall back to config
            start_hour_result = await db.execute(
                select(SettingsModel).where(SettingsModel.key == "quiet_hours_start_hour")
            )
            start_hour_setting = start_hour_result.scalar_one_or_none()
            start_hour = int(start_hour_setting.value) if start_hour_setting else settings.quiet_hours_start_hour

            start_min_result = await db.execute(
                select(SettingsModel).where(SettingsModel.key == "quiet_hours_start_minute")
            )
            start_min_setting = start_min_result.scalar_one_or_none()
            start_minute = int(start_min_setting.value) if start_min_setting else settings.quiet_hours_start_minute

            end_hour_result = await db.execute(
                select(SettingsModel).where(SettingsModel.key == "quiet_hours_end_hour")
            )
            end_hour_setting = end_hour_result.scalar_one_or_none()
            end_hour = int(end_hour_setting.value) if end_hour_setting else settings.quiet_hours_end_hour

            end_min_result = await db.execute(
                select(SettingsModel).where(SettingsModel.key == "quiet_hours_end_minute")
            )
            end_min_setting = end_min_result.scalar_one_or_none()
            end_minute = int(end_min_setting.value) if end_min_setting else settings.quiet_hours_end_minute

            tz = pytz.timezone(settings.timezone)
            now = datetime.now(tz)
            current_time = now.time()

            start = time(start_hour, start_minute)
            end = time(end_hour, end_minute)

            # Handle overnight quiet hours
            if start > end:
                return current_time >= start or current_time < end
            else:
                return start <= current_time < end

    except Exception as e:
        logger.error(f"Error checking quiet hours (async): {e}")
        return False


class TelegramService:
    """Service for sending and receiving Telegram messages."""

    def __init__(self):
        self.chat_id = settings.telegram_chat_id
        self.bot = None
        if settings.telegram_bot_token:
            # Configure HTTPX request with proper timeouts
            request = HTTPXRequest(
                connect_timeout=TELEGRAM_CONNECT_TIMEOUT,
                read_timeout=TELEGRAM_READ_TIMEOUT,
                write_timeout=TELEGRAM_WRITE_TIMEOUT,
            )
            self.bot = Bot(token=settings.telegram_bot_token, request=request)

    async def send_message(
        self, text: str, parse_mode: str = None, ignore_quiet_hours: bool = False, chat_id: str = None
    ) -> str | None:
        """Send a message to the configured chat.

        Args:
            text: Message text to send
            parse_mode: Telegram parse mode (default: None for plain text, most reliable)
            ignore_quiet_hours: If True, send even during quiet hours (for replies)
            chat_id: Override the default chat_id (for multi-user support)

        Returns the message ID if successful, None otherwise.
        """
        target_chat_id = chat_id or self.chat_id
        if not self.bot or not target_chat_id:
            logger.warning("Telegram not configured, skipping message send")
            return None

        # Check quiet hours (but always allow responses to user messages)
        if not ignore_quiet_hours and await is_quiet_hours_async():
            logger.info(f"Quiet hours active, skipping scheduled message")
            return None

        # Log what we're about to send for debugging
        text_preview = text[:100] + "..." if len(text) > 100 else text
        logger.info(f"Attempting to send Telegram message to chat_id={target_chat_id}: {text_preview}")

        # Try sending with retry on timeout
        max_retries = 3
        last_error = None

        for attempt in range(max_retries):
            try:
                message = await self.bot.send_message(
                    chat_id=target_chat_id,
                    text=text,
                )
                logger.info(f"Sent Telegram message (plain): {message.message_id}")
                return str(message.message_id)
            except httpx.TimeoutException as e:
                last_error = e
                logger.warning(f"Telegram send timeout (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    # Brief pause before retry
                    import asyncio
                    await asyncio.sleep(1.0 * (attempt + 1))  # Exponential backoff
                continue
            except Exception as e:
                logger.error(f"Failed to send plain Telegram message: {e}", exc_info=True)
                await self._log_send_error(text, str(e))
                return None

        # All retries failed
        logger.error(f"All {max_retries} Telegram send attempts failed: {last_error}")
        await self._log_send_error(text, f"Timeout after {max_retries} retries: {last_error}")
        return None

    async def _log_send_error(self, message_text: str, error_message: str):
        """Log Telegram send errors to the database for UI visibility."""
        try:
            from app.database import async_session_maker
            from app.db_models import ErrorLog
            import json

            async with async_session_maker() as db:
                error_log = ErrorLog(
                    error_type="TelegramSendError",
                    error_message=error_message,
                    context=json.dumps({
                        "chat_id": self.chat_id,
                        "message_preview": message_text[:200] if message_text else None,
                    }),
                    source="telegram_bot",
                    user_message=None,
                )
                db.add(error_log)
                await db.commit()
                logger.info(f"Logged Telegram send error to database")
        except Exception as log_error:
            logger.error(f"Failed to log send error to database: {log_error}")

    async def send_check_in(self, message: str, chat_id: str = None) -> str | None:
        """Send a check-in message."""
        return await self.send_message(message, chat_id=chat_id)

    async def send_escalation(self, message: str, chat_id: str = None) -> str | None:
        """Send an escalation message (more urgent)."""
        # Could add emoji or formatting for urgency
        return await self.send_message(f"⚠️ {message}", chat_id=chat_id)

    async def send_weekly_review(self, message: str, chat_id: str = None) -> str | None:
        """Send the weekly review message."""
        return await self.send_message(f"📊 WEEKLY REVIEW\n\n{message}", chat_id=chat_id)

    async def send_deadline_alert(self, message: str, chat_id: str = None) -> str | None:
        """Send a deadline alert."""
        return await self.send_message(f"⏰ {message}", chat_id=chat_id)


# Global instance
telegram_service = TelegramService()


def parse_telegram_update(update_data: dict) -> dict | None:
    """Parse incoming Telegram webhook update.

    Returns dict with message info or None if not a valid message.
    """
    try:
        update = Update.de_json(update_data, None)

        if not update.message or not update.message.text:
            return None

        # Verify it's from our configured chat
        if str(update.message.chat_id) != settings.telegram_chat_id:
            logger.warning(
                f"Received message from unauthorized chat: {update.message.chat_id}"
            )
            return None

        return {
            "message_id": str(update.message.message_id),
            "chat_id": str(update.message.chat_id),
            "text": update.message.text,
            "timestamp": update.message.date or datetime.utcnow(),
            "from_user": update.message.from_user.username if update.message.from_user else None,
        }
    except Exception as e:
        logger.error(f"Failed to parse Telegram update: {e}")
        return None
