"""Configuration and environment variables for The Warden."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App settings
    app_name: str = "The Warden"
    debug: bool = False

    # Auth
    api_key: str = "change-me-in-production"

    # Telegram
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""  # Your personal chat ID
    telegram_webhook_url: str = ""  # e.g., https://your-app.railway.app/webhook/telegram
    telegram_webhook_secret: str = ""  # Secret token for webhook validation

    # OpenRouter
    openrouter_api_key: str = ""
    openrouter_model: str = "google/gemini-2.5-flash"  # Default model - fast and capable

    # Database - supports SQLite (local) or PostgreSQL (Supabase)
    # For Supabase: postgresql+asyncpg://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
    # For local dev: sqlite+aiosqlite:///./warden.db
    database_url: str = "sqlite+aiosqlite:///./warden.db"

    # Timezone
    timezone: str = "America/Phoenix"

    # Check-in schedule (24h format)
    daily_checkin_hour: int = 4
    daily_checkin_minute: int = 15
    weekly_review_day: str = "sun"  # Day of week
    weekly_review_hour: int = 18
    weekly_review_minute: int = 0

    # Escalation
    silence_threshold_hours: int = 18
    deadline_alert_hours: int = 48

    # Quiet hours (no messages during this window)
    quiet_hours_enabled: bool = True
    quiet_hours_start_hour: int = 19  # 7:00 PM
    quiet_hours_start_minute: int = 30  # 7:30 PM
    quiet_hours_end_hour: int = 4  # 4:00 AM
    quiet_hours_end_minute: int = 0

    # Google Calendar (optional - for persistent config)
    gcal_client_id: str = ""
    gcal_client_secret: str = ""

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
