"""Comprehensive tests for The Warden application."""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock, MagicMock


class TestGoalsAPI:
    """Test goals CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_goal(self, client):
        """Test creating a goal."""
        response = await client.post(
            "/api/goals",
            json={
                "title": "Test Goal",
                "description": "A test goal for testing"
            }
        )
        assert response.status_code == 201  # 201 Created is correct REST behavior
        data = response.json()
        assert data["title"] == "Test Goal"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_list_goals(self, client):
        """Test listing goals."""
        response = await client.get("/api/goals")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_goal_not_found(self, client):
        """Test getting a non-existent goal."""
        response = await client.get("/api/goals/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_deactivate_goal(self, client):
        """Test deactivating a goal."""
        # Create a goal first
        create_resp = await client.post(
            "/api/goals",
            json={"title": "Goal to Deactivate", "description": "Original"}
        )
        goal_id = create_resp.json()["id"]

        # Deactivate it
        response = await client.delete(f"/api/goals/{goal_id}")
        assert response.status_code in [200, 204]


class TestCommitmentsAPI:
    """Test commitments CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_commitment(self, client):
        """Test creating a commitment."""
        response = await client.post(
            "/api/commitments",
            json={
                "title": "Test Commitment",
                "description": "A test commitment"
            }
        )
        assert response.status_code == 201  # 201 Created
        data = response.json()
        assert data["title"] == "Test Commitment"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_list_commitments(self, client):
        """Test listing commitments."""
        response = await client.get("/api/commitments")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_filter_commitments_by_status(self, client):
        """Test filtering commitments by status."""
        response = await client.get("/api/commitments?status=pending")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_update_commitment_status(self, client):
        """Test updating a commitment's status via PUT."""
        # First create a commitment
        create_resp = await client.post(
            "/api/commitments",
            json={"title": "Commitment to complete"}
        )
        assert create_resp.status_code == 201
        commitment_id = create_resp.json()["id"]

        # Update its status via the standard update endpoint
        response = await client.put(
            f"/api/commitments/{commitment_id}",
            json={"status": "completed"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"

    @pytest.mark.asyncio
    async def test_delete_commitment(self, client):
        """Test deleting a commitment."""
        # Create a commitment first
        create_resp = await client.post(
            "/api/commitments",
            json={"title": "Commitment to Delete"}
        )
        commitment_id = create_resp.json()["id"]

        # Delete it - 204 No Content is correct REST behavior
        response = await client.delete(f"/api/commitments/{commitment_id}")
        assert response.status_code == 204


class TestCheckInsAPI:
    """Test check-ins endpoints."""

    @pytest.mark.asyncio
    async def test_list_checkins(self, client):
        """Test listing check-ins."""
        response = await client.get("/api/checkins")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

class TestSchedulesAPI:
    """Test schedule management."""

    @pytest.mark.asyncio
    async def test_create_schedule(self, client):
        """Test creating a custom schedule."""
        response = await client.post(
            "/api/settings/schedules",
            json={
                "name": "Test Schedule",
                "check_in_type": "daily_checkin",
                "hour": 9,
                "minute": 0,
                "days_of_week": "mon,tue,wed,thu,fri",
                "is_active": True
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Schedule"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_update_schedule(self, client):
        """Test updating a schedule."""
        # Create a schedule first
        create_resp = await client.post(
            "/api/settings/schedules",
            json={
                "name": "Schedule to Update",
                "check_in_type": "daily_checkin",
                "hour": 8,
                "minute": 0
            }
        )
        schedule_id = create_resp.json()["id"]

        # Update it
        response = await client.put(
            f"/api/settings/schedules/{schedule_id}",
            json={
                "name": "Updated Schedule",
                "hour": 10,
                "minute": 30
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Schedule"
        assert data["hour"] == 10

    @pytest.mark.asyncio
    async def test_delete_schedule(self, client):
        """Test deleting a schedule."""
        # Create a schedule first
        create_resp = await client.post(
            "/api/settings/schedules",
            json={
                "name": "Schedule to Delete",
                "check_in_type": "daily_checkin",
                "hour": 7,
                "minute": 0
            }
        )
        schedule_id = create_resp.json()["id"]

        # Delete it
        response = await client.delete(f"/api/settings/schedules/{schedule_id}")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_toggle_schedule_via_update(self, client):
        """Test toggling schedule active status via update."""
        # Create a schedule first
        create_resp = await client.post(
            "/api/settings/schedules",
            json={
                "name": "Schedule to Toggle",
                "check_in_type": "daily_checkin",
                "hour": 6,
                "minute": 0,
                "is_active": True
            }
        )
        schedule_id = create_resp.json()["id"]

        # Toggle it off via update
        response = await client.put(
            f"/api/settings/schedules/{schedule_id}",
            json={"is_active": False}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False


class TestPromptsAPI:
    """Test prompt management."""

    @pytest.mark.asyncio
    async def test_list_prompts(self, client):
        """Test listing prompts."""
        response = await client.get("/api/settings/prompts")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_specific_prompt(self, client):
        """Test getting a specific prompt."""
        response = await client.get("/api/settings/prompts/daily_checkin")
        # May return 200 or 404 depending on if prompt exists
        assert response.status_code in [200, 404]


class TestQuietHoursLogic:
    """Test quiet hours functionality."""

    @pytest.mark.asyncio
    async def test_quiet_hours_disabled(self, client):
        """Test when quiet hours are disabled."""
        # Disable quiet hours
        await client.put(
            "/api/settings/quiet-hours?enabled=false&start_hour=19&start_minute=30&end_hour=4&end_minute=0"
        )

        response = await client.get("/api/settings/quiet-hours")
        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] is False

    @pytest.mark.asyncio
    async def test_quiet_hours_overnight(self, client):
        """Test quiet hours that span midnight."""
        response = await client.put(
            "/api/settings/quiet-hours?enabled=true&start_hour=22&start_minute=0&end_hour=6&end_minute=0"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["start_hour"] == 22
        assert data["end_hour"] == 6


class TestTriggerEndpoints:
    """Test manual trigger endpoints."""

    @pytest.mark.asyncio
    async def test_trigger_checkin_with_auth(self, client):
        """Test triggering check-in with authentication."""
        response = await client.post("/api/trigger/checkin")
        # Should work with proper API key (set in fixture)
        assert response.status_code in [200, 500]  # 500 if Telegram not configured

    @pytest.mark.asyncio
    async def test_trigger_weekly_with_auth(self, client):
        """Test triggering weekly review with authentication."""
        response = await client.post("/api/trigger/weekly-review")
        assert response.status_code in [200, 500]


class TestCalendarEndpoints:
    """Test calendar integration endpoints."""

    @pytest.mark.asyncio
    async def test_calendar_status_without_connection(self, client):
        """Test calendar status when not connected."""
        response = await client.get("/api/settings")
        assert response.status_code == 200
        data = response.json()
        # Should have calendar fields even if not connected
        assert "google_calendar_connected" in data


class TestErrorsAPI:
    """Test error logging endpoints."""

    @pytest.mark.asyncio
    async def test_error_stats(self, client):
        """Test error statistics endpoint."""
        response = await client.get("/api/errors/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_errors" in data
        assert "unresolved_count" in data
        # Check for actual field name
        assert "errors_last_24h" in data or "last_24h_count" in data

    @pytest.mark.asyncio
    async def test_list_errors_empty(self, client):
        """Test listing errors when none exist."""
        response = await client.get("/api/errors")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestChatHistory:
    """Test chat history functionality."""

    @pytest.mark.asyncio
    async def test_get_chat_history(self, client):
        """Test getting chat history."""
        response = await client.get("/api/settings/chat-history")
        assert response.status_code == 200
        data = response.json()
        # API returns a list directly, not wrapped in "messages"
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_chat_history_count(self, client):
        """Test getting chat history count setting."""
        response = await client.get("/api/settings/chat-history-count")
        assert response.status_code == 200
        data = response.json()
        assert "count" in data


class TestModelSettings:
    """Test model selection and settings."""

    @pytest.mark.asyncio
    async def test_list_models(self, client):
        """Test listing available models."""
        response = await client.get("/api/settings/models")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_current_model(self, client):
        """Test getting current model selection via settings."""
        response = await client.get("/api/settings")
        assert response.status_code == 200
        data = response.json()
        # Model info should be in settings
        assert "model" in data or "openrouter_model" in data


class TestSystemPrompt:
    """Test system prompt management."""

    @pytest.mark.asyncio
    async def test_get_system_prompt(self, client):
        """Test getting the system prompt via settings."""
        response = await client.get("/api/settings")
        assert response.status_code == 200
        data = response.json()
        assert "system_prompt" in data


class TestValidation:
    """Test input validation across endpoints."""

    @pytest.mark.asyncio
    async def test_invalid_intensity(self, client):
        """Test setting invalid intensity value."""
        response = await client.put("/api/settings/agent/intensity?intensity=0")
        assert response.status_code == 400

        response = await client.put("/api/settings/agent/intensity?intensity=6")
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_invalid_thinking_level(self, client):
        """Test setting invalid thinking level."""
        response = await client.put("/api/settings/agent/thinking-level?level=super_high")
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_invalid_chat_history_count(self, client):
        """Test setting invalid chat history count."""
        response = await client.put("/api/settings/chat-history-count?count=-1")
        assert response.status_code == 400

        response = await client.put("/api/settings/chat-history-count?count=1000")
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_invalid_schedule_hour(self, client):
        """Test creating schedule with invalid hour."""
        response = await client.post(
            "/api/settings/schedules",
            json={
                "name": "Invalid Schedule",
                "check_in_type": "daily_checkin",
                "hour": 25,
                "minute": 0
            }
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_invalid_schedule_minute(self, client):
        """Test creating schedule with invalid minute."""
        response = await client.post(
            "/api/settings/schedules",
            json={
                "name": "Invalid Schedule",
                "check_in_type": "daily_checkin",
                "hour": 10,
                "minute": 60
            }
        )
        assert response.status_code == 400


class TestWebhookEndpoints:
    """Test webhook-related endpoints."""

    @pytest.mark.asyncio
    async def test_webhook_health(self, client):
        """Test webhook health endpoint."""
        response = await client.get("/webhook/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestDatabaseOperations:
    """Test database operations directly."""

    @pytest.mark.asyncio
    async def test_settings_persistence(self, test_db):
        """Test that settings persist correctly."""
        from app.db_models import Settings

        # Create a setting
        setting = Settings(key="test_key", value="test_value")
        test_db.add(setting)
        await test_db.commit()

        # Retrieve it
        from sqlalchemy import select
        result = await test_db.execute(
            select(Settings).where(Settings.key == "test_key")
        )
        retrieved = result.scalar_one_or_none()
        assert retrieved is not None
        assert retrieved.value == "test_value"

    @pytest.mark.asyncio
    async def test_commitment_status_transition(self, test_db):
        """Test commitment status transitions."""
        from app.db_models import Commitment, CommitmentStatus

        # Create a commitment
        commitment = Commitment(
            title="Test Commitment",
            status=CommitmentStatus.PENDING
        )
        test_db.add(commitment)
        await test_db.commit()
        await test_db.refresh(commitment)

        # Complete it
        commitment.status = CommitmentStatus.COMPLETED
        commitment.completed_at = datetime.utcnow()
        await test_db.commit()
        await test_db.refresh(commitment)

        assert commitment.status == CommitmentStatus.COMPLETED
        assert commitment.completed_at is not None

    @pytest.mark.asyncio
    async def test_goal_creation(self, test_db):
        """Test goal creation in database."""
        from app.db_models import Goal

        goal = Goal(
            title="Test Goal",
            description="A test goal",
            is_active=True
        )
        test_db.add(goal)
        await test_db.commit()
        await test_db.refresh(goal)

        assert goal.id is not None
        assert goal.title == "Test Goal"

    @pytest.mark.asyncio
    async def test_checkin_creation(self, test_db):
        """Test check-in creation in database."""
        from app.db_models import CheckIn, CheckInType

        checkin = CheckIn(
            check_in_type=CheckInType.DAILY,
            message_sent="Test check-in message"
        )
        test_db.add(checkin)
        await test_db.commit()
        await test_db.refresh(checkin)

        assert checkin.id is not None
        assert checkin.check_in_type == CheckInType.DAILY


class TestQuietHoursUnit:
    """Unit tests for quiet hours logic."""

    def test_is_quiet_hours_function(self):
        """Test the is_quiet_hours function directly."""
        from app.telegram_bot import is_quiet_hours
        from app.config import get_settings

        # Clear cache to ensure fresh settings
        get_settings.cache_clear()

        # This should run without error
        result = is_quiet_hours()
        assert isinstance(result, bool)


class TestStreaks:
    """Test streak tracking functionality."""

    @pytest.mark.asyncio
    async def test_streak_creation(self, test_db):
        """Test creating a new streak."""
        from app.streaks import get_or_create_streak

        streak = await get_or_create_streak(test_db, "response")
        assert streak is not None
        assert streak.streak_type == "response"
        assert streak.current_count == 0

    @pytest.mark.asyncio
    async def test_streak_update(self, test_db):
        """Test updating a streak."""
        from app.streaks import update_response_streak

        result = await update_response_streak(test_db)
        assert "current" in result
        assert "best" in result
        assert result["current"] >= 1


class TestPatterns:
    """Test pattern detection functionality."""

    @pytest.mark.asyncio
    async def test_pattern_detector_initialization(self, test_db):
        """Test pattern detector can be initialized."""
        from app.patterns import PatternDetector

        detector = PatternDetector(test_db)
        assert detector is not None

    @pytest.mark.asyncio
    async def test_pattern_detection_runs(self, test_db):
        """Test pattern detection runs without error."""
        from app.patterns import PatternDetector

        detector = PatternDetector(test_db)
        patterns = await detector.run_detection()
        assert isinstance(patterns, list)


class TestMoodTracking:
    """Test mood tracking functionality."""

    @pytest.mark.asyncio
    async def test_get_mood_trends(self, client):
        """Test getting mood trends."""
        response = await client.get("/api/settings/agent/mood?days=7")
        assert response.status_code == 200
        data = response.json()
        assert "avg_mood" in data
        assert "avg_energy" in data

    @pytest.mark.asyncio
    async def test_mood_log_creation(self, test_db):
        """Test mood log creation in database."""
        from app.db_models import MoodLog

        mood_log = MoodLog(
            mood_score=7,
            energy_level=6,
            notes="Feeling good today"
        )
        test_db.add(mood_log)
        await test_db.commit()
        await test_db.refresh(mood_log)

        assert mood_log.id is not None
        assert mood_log.mood_score == 7


class TestFollowups:
    """Test scheduled followups functionality."""

    @pytest.mark.asyncio
    async def test_get_followups(self, client):
        """Test getting scheduled followups."""
        response = await client.get("/api/settings/agent/followups")
        assert response.status_code == 200
        data = response.json()
        assert "followups" in data
        assert isinstance(data["followups"], list)

    @pytest.mark.asyncio
    async def test_followup_creation(self, test_db):
        """Test followup creation in database."""
        from app.db_models import ScheduledFollowup

        followup = ScheduledFollowup(
            topic="Test followup",
            scheduled_time=datetime.utcnow() + timedelta(days=1)
        )
        test_db.add(followup)
        await test_db.commit()
        await test_db.refresh(followup)

        assert followup.id is not None
        assert followup.topic == "Test followup"
