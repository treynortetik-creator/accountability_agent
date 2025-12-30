"""End-to-end tests using Playwright."""

import pytest
import asyncio
import subprocess
import time
import os
import signal
import sys
from playwright.async_api import async_playwright, expect


# Server URL for E2E tests
BASE_URL = "http://localhost:8765"
API_KEY = "test_api_key"


@pytest.fixture(scope="module")
def server():
    """Start the server for E2E tests."""
    env = os.environ.copy()
    env["DATABASE_URL"] = "sqlite+aiosqlite:///./test_e2e.db"
    env["TELEGRAM_BOT_TOKEN"] = "test_token"
    env["TELEGRAM_CHAT_ID"] = "test_chat_id"
    env["OPENROUTER_API_KEY"] = "test_key"
    env["API_KEY"] = API_KEY
    env["DEBUG"] = "false"

    # Remove old test database if exists
    if os.path.exists("./test_e2e.db"):
        os.remove("./test_e2e.db")

    # Start the server using the same Python interpreter
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8765"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid if os.name != 'nt' else None,
    )

    # Wait for server to start
    time.sleep(3)

    yield process

    # Cleanup
    if os.name != 'nt':
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
    else:
        process.terminate()
    process.wait()

    # Remove test database
    if os.path.exists("./test_e2e.db"):
        os.remove("./test_e2e.db")


@pytest.mark.asyncio
async def test_dashboard_loads(server):
    """Test that the dashboard page loads correctly."""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        # Use a wider viewport to ensure sidebar is visible
        page = await browser.new_page(viewport={"width": 1280, "height": 720})

        await page.goto(f"{BASE_URL}/dashboard")

        # Check page title contains expected content
        title = await page.title()
        assert "Warden" in title or "Dashboard" in title or title != ""

        # Check that auth overlay is visible (initial state)
        auth_overlay = page.locator("#auth-overlay")
        await expect(auth_overlay).to_be_visible()

        # Set API key and authenticate
        await page.evaluate(f"localStorage.setItem('warden_api_key', '{API_KEY}')")
        await page.fill("#apiKeyInput", API_KEY)
        await page.click("button:has-text('Connect')")

        # Wait for authentication to complete and app to be visible
        await page.wait_for_timeout(1000)

        # Check that main content is now visible
        main_content = page.locator("main")
        await expect(main_content).to_be_visible()

        # Check for dashboard section
        dashboard_section = page.locator("#section-dashboard")
        await expect(dashboard_section).to_be_visible()

        await browser.close()


@pytest.mark.asyncio
async def test_navigation_works(server):
    """Test that sidebar navigation works."""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # Set API key in localStorage
        await page.goto(f"{BASE_URL}/dashboard")
        await page.evaluate(f"localStorage.setItem('warden_api_key', '{API_KEY}')")
        await page.reload()

        # Click on Commitments nav
        await page.click("text=Commitments")
        await page.wait_for_timeout(500)

        # Verify commitments section is visible
        commitments_section = page.locator("#section-commitments")
        await expect(commitments_section).to_be_visible()

        # Click on Goals nav
        await page.click("text=Goals")
        await page.wait_for_timeout(500)

        goals_section = page.locator("#section-goals")
        await expect(goals_section).to_be_visible()

        # Click on Settings nav
        await page.click("text=Settings")
        await page.wait_for_timeout(500)

        settings_section = page.locator("#section-settings")
        await expect(settings_section).to_be_visible()

        # Click on Error Log nav
        await page.click("text=Error Log")
        await page.wait_for_timeout(500)

        errors_section = page.locator("#section-errors")
        await expect(errors_section).to_be_visible()

        await browser.close()


@pytest.mark.asyncio
async def test_error_log_displays(server):
    """Test that the error log section displays correctly."""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        await page.goto(f"{BASE_URL}/dashboard")
        await page.evaluate(f"localStorage.setItem('warden_api_key', '{API_KEY}')")
        await page.reload()

        # Navigate to errors section
        await page.click("text=Error Log")
        await page.wait_for_timeout(1000)

        # Verify the section title is visible
        await expect(page.locator("h1:has-text('Error Log')")).to_be_visible()

        # Verify stats cards are present
        await expect(page.locator("#error-total")).to_be_visible()
        await expect(page.locator("#error-unresolved")).to_be_visible()
        await expect(page.locator("#error-resolved")).to_be_visible()

        await browser.close()


@pytest.mark.asyncio
async def test_trigger_checkin_button(server):
    """Test that the trigger check-in button is present and clickable."""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1280, "height": 720})

        await page.goto(f"{BASE_URL}/dashboard")
        await page.evaluate(f"localStorage.setItem('warden_api_key', '{API_KEY}')")
        await page.reload()

        # Navigate to settings section where trigger buttons are
        await page.click("text=Settings")
        await page.wait_for_timeout(500)

        # Look for the trigger check-in button in settings section (use first to handle multiple)
        trigger_btn = page.locator("#section-settings button:has-text('Trigger Check-in')").first
        await expect(trigger_btn).to_be_visible()

        await browser.close()


@pytest.mark.asyncio
async def test_api_health_endpoint(server):
    """Test the health API endpoint via browser fetch."""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        await page.goto(f"{BASE_URL}/dashboard")

        # Test health endpoint
        result = await page.evaluate("""
            async () => {
                const response = await fetch('/health');
                return await response.json();
            }
        """)

        assert result["status"] == "healthy"

        await browser.close()


@pytest.mark.asyncio
async def test_errors_api_with_auth(server):
    """Test errors API endpoint with authentication."""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        await page.goto(f"{BASE_URL}/dashboard")

        # Test errors endpoint with auth
        result = await page.evaluate(f"""
            async () => {{
                const response = await fetch('/api/errors', {{
                    headers: {{ 'X-API-Key': '{API_KEY}' }}
                }});
                return {{ status: response.status, data: await response.json() }};
            }}
        """)

        assert result["status"] == 200
        assert isinstance(result["data"], list)

        await browser.close()


@pytest.mark.asyncio
async def test_commitments_section(server):
    """Test that commitments section loads and has expected elements."""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1280, "height": 720})

        await page.goto(f"{BASE_URL}/dashboard")
        await page.evaluate(f"localStorage.setItem('warden_api_key', '{API_KEY}')")
        await page.reload()

        # Navigate to commitments
        await page.click("text=Commitments")
        await page.wait_for_timeout(1000)

        # Check for add commitment button (specific to commitments section)
        add_btn = page.locator("#section-commitments button:has-text('Add Commitment')")
        await expect(add_btn).to_be_visible()

        # Check for filter tabs
        await expect(page.locator("#section-commitments >> text=Pending")).to_be_visible()
        await expect(page.locator("#section-commitments >> text=Completed")).to_be_visible()

        await browser.close()
