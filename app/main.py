"""Main FastAPI application for The Warden."""

import logging
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, Depends, Request, Form, Cookie
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from app.config import get_settings
from app.database import init_db
from app.auth import (
    verify_api_key,
    login_dashboard,
    logout_dashboard,
    verify_dashboard_session,
    SESSION_COOKIE_NAME,
    get_client_ip,
)
from app.security import request_logger, session_manager
from app.scheduler import setup_scheduler, shutdown_scheduler, daily_checkin_job, load_custom_schedules_on_startup, schedule_github_poll
from app.routers import goals, commitments, checkins, webhook, app_settings, calendar, errors, github
from app.models import ManualCheckInRequest
from app.dashboard_html import DASHBOARD_HTML
from app.login_html import LOGIN_HTML

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
    # Startup - wrap in try/except so app starts even if init fails
    # This allows healthcheck to pass so we can see logs
    startup_error = None
    try:
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
        await load_custom_schedules_on_startup()
        await schedule_github_poll()
        logger.info("The Warden is now watching.")
    except Exception as e:
        startup_error = e
        logger.error(f"STARTUP FAILED: {type(e).__name__}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        # Store error for /health endpoint
        app.state.startup_error = str(e)

    yield

    # Shutdown
    try:
        shutdown_scheduler()
        logger.info("The Warden has shut down.")
    except Exception as e:
        logger.error(f"Shutdown error: {e}")


app = FastAPI(
    title="The Warden",
    description="Personal accountability agent that calls out your bullshit",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify explicit origins
    allow_credentials=False,  # Never use credentials with wildcard origins
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["X-API-Key", "Content-Type"],
)

# Include routers
app.include_router(goals.router, prefix="/api")
app.include_router(commitments.router, prefix="/api")
app.include_router(checkins.router, prefix="/api")
app.include_router(app_settings.router, prefix="/api")
app.include_router(calendar.router, prefix="/api")
app.include_router(errors.router, prefix="/api")
app.include_router(github.router, prefix="/api")
app.include_router(webhook.router)


# =============================================================================
# Authentication Routes
# =============================================================================

@app.get("/", response_class=RedirectResponse)
async def root():
    """Redirect to dashboard (which will redirect to login if not authenticated)."""
    return RedirectResponse(url="/dashboard")


@app.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request,
    session_token: Optional[str] = Cookie(default=None, alias=SESSION_COOKIE_NAME),
):
    """Serve the login page (or redirect to dashboard if already logged in)."""
    # If already logged in, redirect to dashboard
    if session_token and session_manager.validate_session(session_token):
        return RedirectResponse(url="/dashboard", status_code=302)

    return HTMLResponse(content=LOGIN_HTML)


@app.post("/login")
async def handle_login(
    request: Request,
    password: str = Form(...),
):
    """Process login form submission."""
    session_token = await login_dashboard(request, password)

    if not session_token:
        return JSONResponse(
            status_code=401,
            content={"detail": "Invalid password"}
        )

    # Create response with session cookie
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_token,
        httponly=True,
        secure=True,  # Only send over HTTPS
        samesite="lax",
        max_age=30 * 24 * 60 * 60,  # 30 days
    )

    return response


@app.get("/logout")
async def handle_logout(
    session_token: Optional[str] = Cookie(default=None, alias=SESSION_COOKIE_NAME),
):
    """Log out and invalidate session."""
    logout_dashboard(session_token)

    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie(SESSION_COOKIE_NAME)

    return response


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    session_token: Optional[str] = Cookie(default=None, alias=SESSION_COOKIE_NAME),
):
    """Serve the HTML dashboard (protected by session auth)."""
    # Check if session is valid
    if not session_token or not session_manager.validate_session(session_token):
        # Log the access attempt
        request_logger.log(
            method="GET",
            path="/dashboard",
            client_ip=get_client_ip(request),
            status_code=302,
            user_agent=request.headers.get("User-Agent"),
            auth_method="session",
            auth_success=False,
        )
        return RedirectResponse(url="/login", status_code=302)

    return HTMLResponse(content=DASHBOARD_HTML)


# =============================================================================
# API and Health Routes
# =============================================================================

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
    startup_error = getattr(app.state, 'startup_error', None)
    if startup_error:
        return {
            "status": "unhealthy",
            "startup_error": startup_error,
            "scheduler": "not started"
        }
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


# =============================================================================
# Security Monitoring Routes (protected by API key)
# =============================================================================

@app.get("/api/security/logs")
async def get_security_logs(
    count: int = 100,
    _: str = Depends(verify_api_key),
):
    """Get recent security/request logs."""
    return {
        "logs": request_logger.get_recent(count),
        "failures": request_logger.get_failures(50),
    }


@app.get("/api/security/sessions")
async def get_active_sessions(_: str = Depends(verify_api_key)):
    """Get count of active sessions."""
    session_manager.cleanup_expired()
    return {
        "active_sessions": len(session_manager._sessions),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
