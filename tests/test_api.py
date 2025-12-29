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
