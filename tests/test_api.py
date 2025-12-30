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
