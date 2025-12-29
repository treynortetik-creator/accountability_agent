"""Test that all modules import correctly without errors."""

import pytest


class TestImports:
    """Test that all app modules can be imported."""

    def test_import_db_models(self):
        """Test db_models imports."""
        from app.db_models import (
            Base, Goal, Commitment, CommitmentStatus, CheckIn, CheckInType,
            Response, Pattern, ChatMessage, CheckInSchedule, Settings,
            CheckInPrompt, ScheduledFollowup, MoodLog, ErrorLog,
            ResponseTiming, WeeklyInsight
        )
        assert Base is not None
        assert Settings is not None
        assert ScheduledFollowup is not None
        assert MoodLog is not None
        assert ErrorLog is not None
        assert ResponseTiming is not None
        assert WeeklyInsight is not None

    def test_import_scheduler(self):
        """Test scheduler imports - this was the failing module."""
        from app.scheduler import (
            daily_checkin_job, weekly_review_job, get_context,
            setup_scheduler, shutdown_scheduler
        )
        assert daily_checkin_job is not None
        assert weekly_review_job is not None
        assert get_context is not None

    def test_import_webhook(self):
        """Test webhook imports."""
        from app.routers.webhook import router
        assert router is not None

    def test_import_errors(self):
        """Test errors router imports."""
        from app.routers.errors import router
        assert router is not None

    def test_import_llm(self):
        """Test LLM module imports."""
        from app.llm import generate_message, analyze_response, parse_commitment
        assert generate_message is not None
        assert analyze_response is not None
        assert parse_commitment is not None

    def test_import_telegram(self):
        """Test telegram module imports."""
        from app.telegram_bot import telegram_service, parse_telegram_update
        assert telegram_service is not None
        assert parse_telegram_update is not None

    def test_import_main(self):
        """Test main app imports."""
        from app.main import app
        assert app is not None

    def test_import_all_routers(self):
        """Test all routers import correctly."""
        from app.routers import goals, commitments, checkins, webhook, app_settings, calendar, errors
        assert goals.router is not None
        assert commitments.router is not None
        assert checkins.router is not None
        assert webhook.router is not None
        assert app_settings.router is not None
        assert calendar.router is not None
        assert errors.router is not None
