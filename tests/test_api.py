"""Test API endpoints."""

import pytest
import pytest_asyncio


class TestHealthEndpoint:
    """Test health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """Test /health returns healthy status."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestTriggerEndpoints:
    """Test trigger endpoints."""

    @pytest.mark.asyncio
    async def test_trigger_checkin_requires_auth(self, client):
        """Test trigger checkin requires API key."""
        # Remove the API key header
        client.headers.pop("X-API-Key", None)
        response = await client.post("/api/trigger/checkin")
        # Should fail auth
        assert response.status_code in [401, 403, 422]

    @pytest.mark.asyncio
    async def test_trigger_weekly_review_requires_auth(self, client):
        """Test trigger weekly review requires API key."""
        client.headers.pop("X-API-Key", None)
        response = await client.post("/api/trigger/weekly-review")
        assert response.status_code in [401, 403, 422]


class TestErrorsEndpoint:
    """Test errors API endpoints."""

    @pytest.mark.asyncio
    async def test_list_errors(self, client):
        """Test listing errors."""
        response = await client.get("/api/errors")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_error_stats(self, client):
        """Test error stats endpoint."""
        response = await client.get("/api/errors/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_errors" in data
        assert "unresolved_count" in data


class TestDashboard:
    """Test dashboard endpoint."""

    @pytest.mark.asyncio
    async def test_dashboard_loads(self, client):
        """Test dashboard HTML loads."""
        response = await client.get("/dashboard")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")


class TestChatHistoryCount:
    """Test chat history count settings endpoints."""

    @pytest.mark.asyncio
    async def test_get_chat_history_count(self, client):
        """Test getting chat history count."""
        response = await client.get("/api/settings/chat-history-count")
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert isinstance(data["count"], int)

    @pytest.mark.asyncio
    async def test_update_chat_history_count(self, client):
        """Test updating chat history count."""
        response = await client.put("/api/settings/chat-history-count?count=25")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "updated"
        assert data["count"] == 25

    @pytest.mark.asyncio
    async def test_update_chat_history_count_invalid(self, client):
        """Test updating chat history count with invalid value."""
        response = await client.put("/api/settings/chat-history-count?count=200")
        assert response.status_code == 400


class TestSettingsMemory:
    """Test memory settings endpoints."""

    @pytest.mark.asyncio
    async def test_get_memory(self, client):
        """Test getting LLM memory."""
        response = await client.get("/api/settings/memory")
        assert response.status_code == 200
        data = response.json()
        assert "memory" in data

    @pytest.mark.asyncio
    async def test_update_memory(self, client):
        """Test updating LLM memory."""
        response = await client.put(
            "/api/settings/memory",
            json={"value": "Test memory content"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "updated"

    @pytest.mark.asyncio
    async def test_clear_memory(self, client):
        """Test clearing LLM memory."""
        response = await client.delete("/api/settings/memory")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cleared"


class TestAgentSettings:
    """Test agent intelligence settings endpoints."""

    @pytest.mark.asyncio
    async def test_get_intensity(self, client):
        """Test getting accountability intensity."""
        response = await client.get("/api/settings/agent/intensity")
        assert response.status_code == 200
        data = response.json()
        assert "intensity" in data
        assert 1 <= data["intensity"] <= 5

    @pytest.mark.asyncio
    async def test_update_intensity(self, client):
        """Test updating accountability intensity."""
        response = await client.put("/api/settings/agent/intensity?intensity=4")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "updated"
        assert data["intensity"] == 4

    @pytest.mark.asyncio
    async def test_update_intensity_invalid(self, client):
        """Test updating intensity with invalid value."""
        response = await client.put("/api/settings/agent/intensity?intensity=10")
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_get_thinking_level(self, client):
        """Test getting thinking level."""
        response = await client.get("/api/settings/agent/thinking-level")
        assert response.status_code == 200
        data = response.json()
        assert "thinking_level" in data

    @pytest.mark.asyncio
    async def test_update_thinking_level(self, client):
        """Test updating thinking level."""
        response = await client.put("/api/settings/agent/thinking-level?level=high")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "updated"
        assert data["thinking_level"] == "high"

    @pytest.mark.asyncio
    async def test_update_thinking_level_invalid(self, client):
        """Test updating thinking level with invalid value."""
        response = await client.put("/api/settings/agent/thinking-level?level=invalid")
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_get_mood(self, client):
        """Test getting mood trends."""
        response = await client.get("/api/settings/agent/mood?days=7")
        assert response.status_code == 200
        data = response.json()
        assert "avg_mood" in data
        assert "avg_energy" in data
        assert "days" in data

    @pytest.mark.asyncio
    async def test_get_followups(self, client):
        """Test getting scheduled followups."""
        response = await client.get("/api/settings/agent/followups")
        assert response.status_code == 200
        data = response.json()
        assert "followups" in data
        assert isinstance(data["followups"], list)


class TestQuietHours:
    """Test quiet hours endpoints."""

    @pytest.mark.asyncio
    async def test_get_quiet_hours(self, client):
        """Test getting quiet hours settings."""
        response = await client.get("/api/settings/quiet-hours")
        assert response.status_code == 200
        data = response.json()
        assert "enabled" in data
        assert "start_hour" in data
        assert "start_minute" in data
        assert "end_hour" in data
        assert "end_minute" in data
        assert "currently_quiet" in data

    @pytest.mark.asyncio
    async def test_update_quiet_hours(self, client):
        """Test updating quiet hours settings."""
        response = await client.put(
            "/api/settings/quiet-hours?enabled=true&start_hour=22&start_minute=0&end_hour=6&end_minute=30"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "updated"
        assert data["enabled"] is True
        assert data["start_hour"] == 22

    @pytest.mark.asyncio
    async def test_update_quiet_hours_invalid(self, client):
        """Test updating quiet hours with invalid values."""
        response = await client.put(
            "/api/settings/quiet-hours?enabled=true&start_hour=25&start_minute=0&end_hour=6&end_minute=0"
        )
        assert response.status_code == 400


class TestScheduleEdit:
    """Test schedule edit endpoints."""

    @pytest.mark.asyncio
    async def test_get_schedules(self, client):
        """Test getting schedules list."""
        response = await client.get("/api/settings/schedules")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
