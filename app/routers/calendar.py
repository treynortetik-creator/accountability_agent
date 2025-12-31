"""Google Calendar integration router."""

import logging
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from pydantic import BaseModel
import httpx

from app.database import get_db
from app.auth import verify_api_key
from app.db_models import CalendarEvent, Settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get("/callback", response_class=HTMLResponse)
async def oauth_callback(
    code: str = None,
    error: str = None,
):
    """Handle Google OAuth callback - displays the auth code for user to copy.

    Note: Auto-exchange was removed because the callback runs without auth context.
    User must copy the code and use the dashboard to complete setup.
    """
    if error:
        return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Authorization Failed</title>
            <style>
                body {{ font-family: system-ui, sans-serif; background: #1a1a2e; color: #eee;
                       display: flex; justify-content: center; align-items: center;
                       min-height: 100vh; margin: 0; }}
                .container {{ text-align: center; padding: 40px; background: #16213e;
                             border-radius: 12px; max-width: 500px; }}
                h1 {{ color: #ff6b6b; }}
                p {{ color: #aaa; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Authorization Failed</h1>
                <p>Error: {error}</p>
                <p>Please close this window and try again.</p>
            </div>
        </body>
        </html>
        """)

    if not code:
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>No Code Received</title>
            <style>
                body { font-family: system-ui, sans-serif; background: #1a1a2e; color: #eee;
                       display: flex; justify-content: center; align-items: center;
                       min-height: 100vh; margin: 0; }
                .container { text-align: center; padding: 40px; background: #16213e;
                             border-radius: 12px; max-width: 500px; }
                h1 { color: #ff6b6b; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>No Authorization Code</h1>
                <p>No authorization code was received. Please try again.</p>
            </div>
        </body>
        </html>
        """)

    # Return HTML that shows the code for manual entry
    return HTMLResponse(content=f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Authorization Successful</title>
        <style>
            body {{ font-family: system-ui, sans-serif; background: #1a1a2e; color: #eee;
                   display: flex; justify-content: center; align-items: center;
                   min-height: 100vh; margin: 0; }}
            .container {{ text-align: center; padding: 40px; background: #16213e;
                         border-radius: 12px; max-width: 600px; }}
            h1 {{ color: #4ecdc4; margin-bottom: 20px; }}
            .code-box {{ background: #0f0f23; padding: 15px; border-radius: 8px;
                        word-break: break-all; font-family: monospace; font-size: 12px;
                        margin: 20px 0; border: 1px solid #333; }}
            .success {{ color: #4ecdc4; font-size: 48px; margin-bottom: 10px; }}
            .instructions {{ color: #aaa; margin-top: 20px; }}
            button {{ background: #4ecdc4; color: #1a1a2e; border: none; padding: 12px 24px;
                     border-radius: 6px; cursor: pointer; font-size: 16px; font-weight: bold; }}
            button:hover {{ background: #3dbdb5; }}
            #status {{ margin-top: 15px; color: #4ecdc4; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="success">✓</div>
            <h1>Authorization Successful!</h1>
            <p>Copy this code and paste it in The Warden settings:</p>
            <div class="code-box" id="code">{code}</div>
            <button onclick="copyCode()">Copy Code</button>
            <p id="status"></p>
            <p class="instructions">After copying, close this window and paste the code in the authorization field.</p>
        </div>
        <script>
            function copyCode() {{
                const code = document.getElementById('code').textContent;
                navigator.clipboard.writeText(code).then(() => {{
                    document.getElementById('status').textContent = 'Copied to clipboard!';
                }});
            }}

            // Try to auto-send code to opener window
            if (window.opener) {{
                try {{
                    window.opener.postMessage({{ type: 'google-auth-code', code: '{code}' }}, '*');
                }} catch(e) {{
                    console.log('Could not send to opener:', e);
                }}
            }}
        </script>
    </body>
    </html>
    """)


class CalendarEventResponse(BaseModel):
    id: int
    google_event_id: str
    title: str
    description: Optional[str]
    start_time: str
    end_time: Optional[str]
    all_day: bool
    location: Optional[str]

    class Config:
        from_attributes = True


class CalendarConnectRequest(BaseModel):
    api_key: str  # Google Calendar API key


class CalendarSyncResponse(BaseModel):
    synced: int
    events: List[CalendarEventResponse]


async def get_calendar_api_key(db: AsyncSession) -> Optional[str]:
    """Get Google Calendar API key from settings."""
    result = await db.execute(select(Settings).where(Settings.key == "google_calendar_api_key"))
    setting = result.scalar_one_or_none()
    return setting.value if setting else None


@router.get("/status")
async def calendar_status(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Check if Google Calendar is connected."""
    from app.calendar_service import calendar_service
    is_configured = await calendar_service.is_configured(db)
    return {"connected": is_configured}


@router.post("/sync")
async def sync_calendar(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Manually trigger calendar sync from Google Calendar."""
    import json
    from app.calendar_service import calendar_service
    from app.user_service import get_default_user
    from app.db_models import ErrorLog

    async def log_calendar_error(error_type: str, error_msg: str, context: dict = None):
        """Log calendar errors to the database for visibility."""
        try:
            error_log = ErrorLog(
                error_type=error_type,
                error_message=error_msg,
                context=json.dumps(context) if context else None,
                source="google_calendar",
                user_message=None,
            )
            db.add(error_log)
            await db.flush()
        except Exception as log_err:
            logger.error(f"Failed to log calendar error: {log_err}")

    # Get user for multi-user support
    user = await get_default_user(db)

    # Check if OAuth token exists
    result = await db.execute(
        select(Settings).where(
            Settings.user_id == user.id,
            Settings.key == "google_calendar_token"
        )
    )
    token_setting = result.scalar_one_or_none()

    if not token_setting:
        # Also check without user_id for backwards compatibility
        result = await db.execute(
            select(Settings).where(Settings.key == "google_calendar_token")
        )
        token_setting = result.scalar_one_or_none()

    if not token_setting:
        await log_calendar_error("CalendarSyncError", "No OAuth token found in database")
        raise HTTPException(
            status_code=400,
            detail="Google Calendar OAuth not configured. You need to complete the OAuth flow to connect your calendar."
        )

    # Check token state
    try:
        token_data = json.loads(token_setting.value)
        has_token = bool(token_data.get("token"))
        has_refresh = bool(token_data.get("refresh_token"))
        logger.info(f"Calendar sync - has_token: {has_token}, has_refresh_token: {has_refresh}")

        if not has_token and not has_refresh:
            await log_calendar_error(
                "CalendarSyncError",
                "OAuth tokens are null - authorization code was never exchanged",
                {"client_id_present": bool(token_data.get("client_id"))}
            )
            raise HTTPException(
                status_code=400,
                detail="OAuth tokens missing. Please disconnect and reconnect your calendar."
            )
    except json.JSONDecodeError as e:
        await log_calendar_error("CalendarSyncError", f"Invalid token JSON: {e}")
        raise HTTPException(status_code=400, detail="Invalid calendar configuration")

    is_configured = await calendar_service.is_configured(db, user)
    if not is_configured:
        await log_calendar_error(
            "CalendarSyncError",
            "calendar_service.is_configured returned False",
            {"has_token": has_token, "has_refresh": has_refresh}
        )
        raise HTTPException(
            status_code=400,
            detail="Google Calendar credentials are invalid or expired. Please reconnect your calendar."
        )

    try:
        synced_count = await calendar_service.sync_events(db, user=user)
        logger.info(f"Calendar sync completed: {synced_count} events")
        if synced_count == 0:
            return {"status": "synced", "events_synced": 0, "message": "No events found in the next 14 days"}
        return {"status": "synced", "events_synced": synced_count}
    except Exception as e:
        logger.error(f"Calendar sync failed: {e}", exc_info=True)
        await log_calendar_error("CalendarSyncException", str(e), {"phase": "sync_events"})
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.get("/debug-sync")
async def debug_calendar_sync(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Debug endpoint to see exactly what's happening with calendar sync."""
    import json
    from app.user_service import get_default_user
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from datetime import timedelta
    import pytz
    from app.config import get_settings

    settings = get_settings()
    debug_info = {"steps": []}

    try:
        # Step 1: Get user
        user = await get_default_user(db)
        debug_info["steps"].append({"step": "get_user", "user_id": str(user.id)})

        # Step 2: Get token from database
        result = await db.execute(
            select(Settings).where(Settings.key == "google_calendar_token")
        )
        token_setting = result.scalar_one_or_none()

        if not token_setting:
            debug_info["error"] = "No token setting found in database"
            return debug_info

        token_data = json.loads(token_setting.value)
        debug_info["steps"].append({
            "step": "get_token",
            "has_client_id": bool(token_data.get("client_id")),
            "has_client_secret": bool(token_data.get("client_secret")),
            "has_token": bool(token_data.get("token")),
            "has_refresh_token": bool(token_data.get("refresh_token")),
            "token_preview": token_data.get("token", "")[:20] + "..." if token_data.get("token") else None,
        })

        if not token_data.get("token"):
            debug_info["error"] = "Access token is null"
            return debug_info

        # Step 3: Create credentials
        creds = Credentials(
            token=token_data.get('token'),
            refresh_token=token_data.get('refresh_token'),
            token_uri=token_data.get('token_uri', 'https://oauth2.googleapis.com/token'),
            client_id=token_data.get('client_id'),
            client_secret=token_data.get('client_secret'),
        )
        debug_info["steps"].append({
            "step": "create_credentials",
            "valid": creds.valid,
            "expired": creds.expired,
        })

        # Step 4: Build service and fetch events
        service = build('calendar', 'v3', credentials=creds)

        tz = pytz.timezone(settings.timezone)
        now = datetime.now(tz)
        time_min = now.isoformat()
        time_max = (now + timedelta(days=14)).isoformat()

        debug_info["steps"].append({
            "step": "fetch_events",
            "time_min": time_min,
            "time_max": time_max,
        })

        events_result = service.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=time_max,
            maxResults=100,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])
        debug_info["steps"].append({
            "step": "events_received",
            "count": len(events),
            "events": [
                {"title": e.get("summary", "No Title"), "start": e.get("start", {})}
                for e in events[:5]  # First 5 events
            ]
        })

        # Step 5: Check database
        db_result = await db.execute(select(CalendarEvent))
        db_events = db_result.scalars().all()
        debug_info["steps"].append({
            "step": "database_check",
            "events_in_db": len(db_events),
        })

        debug_info["success"] = True
        return debug_info

    except Exception as e:
        import traceback
        debug_info["error"] = str(e)
        debug_info["traceback"] = traceback.format_exc()
        return debug_info


@router.post("/connect")
async def connect_calendar(
    request: CalendarConnectRequest,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Connect Google Calendar with API key.

    Note: For a production app, OAuth2 would be preferred.
    This uses a simple API key approach for MVP.
    """
    # Test the API key
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://www.googleapis.com/calendar/v3/calendars/primary",
                params={"key": request.api_key},
            )
            # API key alone won't work for primary calendar, but we can validate format
            if response.status_code == 403 and "API key" in response.text:
                # This is expected - API keys need OAuth for user calendars
                pass
    except Exception as e:
        logger.warning(f"Calendar API test failed: {e}")

    # Save the API key
    result = await db.execute(select(Settings).where(Settings.key == "google_calendar_api_key"))
    setting = result.scalar_one_or_none()
    if setting:
        setting.value = request.api_key
    else:
        setting = Settings(key="google_calendar_api_key", value=request.api_key)
        db.add(setting)

    await db.flush()
    return {"status": "connected", "message": "API key saved. Note: Full calendar access requires OAuth2 setup."}


@router.delete("/disconnect")
async def disconnect_calendar(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Disconnect Google Calendar."""
    result = await db.execute(select(Settings).where(Settings.key == "google_calendar_api_key"))
    setting = result.scalar_one_or_none()
    if setting:
        await db.delete(setting)

    # Clear cached events
    await db.execute(select(CalendarEvent))
    events = (await db.execute(select(CalendarEvent))).scalars().all()
    for event in events:
        await db.delete(event)

    return {"status": "disconnected"}


@router.get("/events", response_model=List[CalendarEventResponse])
async def get_events(
    days_ahead: int = Query(default=7, le=30),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Get upcoming calendar events from cache."""
    now = datetime.utcnow()
    future = now + timedelta(days=days_ahead)

    result = await db.execute(
        select(CalendarEvent)
        .where(
            and_(
                CalendarEvent.start_time >= now,
                CalendarEvent.start_time <= future,
            )
        )
        .order_by(CalendarEvent.start_time)
    )
    events = result.scalars().all()

    return [
        CalendarEventResponse(
            id=e.id,
            google_event_id=e.google_event_id,
            title=e.title,
            description=e.description,
            start_time=e.start_time.isoformat(),
            end_time=e.end_time.isoformat() if e.end_time else None,
            all_day=e.all_day,
            location=e.location,
        )
        for e in events
    ]


@router.post("/events/manual")
async def add_manual_event(
    title: str,
    start_time: datetime,
    end_time: Optional[datetime] = None,
    description: Optional[str] = None,
    location: Optional[str] = None,
    all_day: bool = False,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Add a manual calendar event (not synced from Google)."""
    event = CalendarEvent(
        google_event_id=f"manual_{datetime.utcnow().timestamp()}",
        title=title,
        description=description,
        start_time=start_time,
        end_time=end_time,
        all_day=all_day,
        location=location,
    )
    db.add(event)
    await db.flush()
    await db.refresh(event)

    return CalendarEventResponse(
        id=event.id,
        google_event_id=event.google_event_id,
        title=event.title,
        description=event.description,
        start_time=event.start_time.isoformat(),
        end_time=event.end_time.isoformat() if event.end_time else None,
        all_day=event.all_day,
        location=event.location,
    )


@router.delete("/events/{event_id}")
async def delete_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Delete a calendar event."""
    result = await db.execute(select(CalendarEvent).where(CalendarEvent.id == event_id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    await db.delete(event)
    return {"status": "deleted"}


@router.get("/today")
async def get_today_events(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Get today's events for LLM context."""
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    result = await db.execute(
        select(CalendarEvent)
        .where(
            and_(
                CalendarEvent.start_time >= today_start,
                CalendarEvent.start_time < today_end,
            )
        )
        .order_by(CalendarEvent.start_time)
    )
    events = result.scalars().all()

    return {
        "date": today_start.date().isoformat(),
        "events": [
            {
                "title": e.title,
                "time": e.start_time.strftime("%H:%M") if not e.all_day else "All day",
                "location": e.location,
            }
            for e in events
        ],
    }
