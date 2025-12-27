"""Telegram bot integration for The Warden."""

import logging
from datetime import datetime
from telegram import Bot, Update
from telegram.constants import ParseMode
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class TelegramService:
    """Service for sending and receiving Telegram messages."""

    def __init__(self):
        self.bot = Bot(token=settings.telegram_bot_token) if settings.telegram_bot_token else None
        self.chat_id = settings.telegram_chat_id

    async def send_message(self, text: str, parse_mode: str = None) -> str | None:
        """Send a message to the configured chat.

        Returns the message ID if successful, None otherwise.
        """
        if not self.bot or not self.chat_id:
            logger.warning("Telegram not configured, skipping message send")
            return None

        try:
            message = await self.bot.send_message(
                chat_id=self.chat_id,
                text=text,
                parse_mode=parse_mode or ParseMode.MARKDOWN,
            )
            logger.info(f"Sent Telegram message: {message.message_id}")
            return str(message.message_id)
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            # Try without markdown if it fails
            try:
                message = await self.bot.send_message(
                    chat_id=self.chat_id,
                    text=text,
                )
                return str(message.message_id)
            except Exception as e2:
                logger.error(f"Failed to send plain Telegram message: {e2}")
                return None

    async def send_check_in(self, message: str) -> str | None:
        """Send a check-in message."""
        return await self.send_message(message)

    async def send_escalation(self, message: str) -> str | None:
        """Send an escalation message (more urgent)."""
        # Could add emoji or formatting for urgency
        return await self.send_message(f"⚠️ {message}")

    async def send_weekly_review(self, message: str) -> str | None:
        """Send the weekly review message."""
        return await self.send_message(f"📊 WEEKLY REVIEW\n\n{message}")

    async def send_deadline_alert(self, message: str) -> str | None:
        """Send a deadline alert."""
        return await self.send_message(f"⏰ {message}")


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
