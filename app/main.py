"""Main FastAPI application for The Warden."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from app.config import get_settings
from app.database import init_db
from app.auth import verify_api_key
from app.scheduler import setup_scheduler, shutdown_scheduler, daily_checkin_job
from app.routers import goals, commitments, checkins, webhook, app_settings, calendar
from app.models import ManualCheckInRequest
from app.dashboard_html import DASHBOARD_HTML

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting The Warden...")
    await init_db()
    logger.info("Database initialized")

    # Initialize persistent settings
    from app.database import async_session_maker
    from app.init_settings import initialize_all
    async with async_session_maker() as db:
        await initialize_all(db)
        await db.commit()
    logger.info("Persistent settings initialized")

    setup_scheduler()
    logger.info("The Warden is now watching.")
    yield
    # Shutdown
    shutdown_scheduler()
    logger.info("The Warden has shut down.")


app = FastAPI(
    title="The Warden",
    description="Personal accountability agent that calls out your bullshit",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(goals.router, prefix="/api")
app.include_router(commitments.router, prefix="/api")
app.include_router(checkins.router, prefix="/api")
app.include_router(app_settings.router, prefix="/api")
app.include_router(calendar.router, prefix="/api")
app.include_router(webhook.router)


@app.get("/", response_class=RedirectResponse)
async def root():
    """Redirect to dashboard."""
    return RedirectResponse(url="/dashboard")


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Serve the HTML dashboard."""
    return HTMLResponse(content=DASHBOARD_HTML)


@app.get("/api/status")
async def api_status():
    """API status endpoint."""
    return {
        "name": "The Warden",
        "status": "watching",
        "message": "What have you shipped today?",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "scheduler": "running"}


@app.post("/api/trigger/checkin")
async def trigger_checkin(
    request: ManualCheckInRequest = None,
    _: str = Depends(verify_api_key),
):
    """Manually trigger a check-in (for testing)."""
    await daily_checkin_job()
    return {"status": "triggered", "message": "Check-in sent"}


@app.post("/api/trigger/weekly-review")
async def trigger_weekly_review(
    _: str = Depends(verify_api_key),
):
    """Manually trigger weekly review (for testing)."""
    from app.scheduler import weekly_review_job

    await weekly_review_job()
    return {"status": "triggered", "message": "Weekly review sent"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
