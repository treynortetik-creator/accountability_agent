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
    db: AsyncSession = Depends(get_db),
):
    """Handle Google OAuth callback - automatically exchanges code for tokens."""
    import json

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

    # Try to automatically exchange the code for tokens
    exchange_result = None
    exchange_error = None

    try:
        # Get stored OAuth config
        result = await db.execute(
            select(Settings).where(Settings.key == "google_calendar_token")
        )
        token_setting = result.scalar_one_or_none()

        if token_setting:
            token_data = json.loads(token_setting.value)
            client_id = token_data.get('client_id')
            client_secret = token_data.get('client_secret')
            redirect_uri = token_data.get('redirect_uri', 'https://example.invalid/api/calendar/callback')

            if client_id and client_secret:
                # Exchange code for tokens
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        "https://oauth2.googleapis.com/token",
                        data={
                            "code": code,
                            "client_id": client_id,
                            "client_secret": client_secret,
                            "redirect_uri": redirect_uri,
                            "grant_type": "authorization_code",
                        }
                    )

                    if response.status_code == 200:
                        tokens = response.json()
                        # Save tokens
                        token_data['token'] = tokens.get('access_token')
                        token_data['refresh_token'] = tokens.get('refresh_token')
                        token_data['token_uri'] = 'https://oauth2.googleapis.com/token'
                        token_setting.value = json.dumps(token_data)
                        await db.commit()
                        exchange_result = "success"
                        logger.info("Successfully exchanged OAuth code for tokens via callback")
                    else:
                        error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                        exchange_error = error_data.get('error_description', error_data.get('error', 'Unknown error'))
                        logger.error(f"Token exchange failed: {exchange_error}")
            else:
                exchange_error = "Missing client credentials in database"
        else:
            exchange_error = "No OAuth configuration found"
    except Exception as e:
        exchange_error = str(e)
        logger.error(f"Error during token exchange: {e}")

    # Return success or failure page
    if exchange_result == "success":
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Calendar Connected!</title>
            <style>
                body { font-family: system-ui, sans-serif; background: #1a1a2e; color: #eee;
                       display: flex; justify-content: center; align-items: center;
                       min-height: 100vh; margin: 0; }
                .container { text-align: center; padding: 40px; background: #16213e;
                             border-radius: 12px; max-width: 500px; }
                h1 { color: #4ecdc4; margin-bottom: 20px; }
                .success { color: #4ecdc4; font-size: 64px; margin-bottom: 10px; }
                p { color: #aaa; margin: 15px 0; }
                .note { font-size: 14px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="success">✓</div>
                <h1>Google Calendar Connected!</h1>
                <p>Your calendar has been successfully connected to The Warden.</p>
                <p class="note">You can close this window and return to the dashboard.</p>
                <p class="note">Click "Sync Google Calendar" to fetch your events.</p>
            </div>
            <script>
                // Notify opener window if available
                if (window.opener) {
                    try {
                        window.opener.postMessage({ type: 'google-auth-success' }, '*');
                    } catch(e) {}
                }
            </script>
        </body>
        </html>
        """)
    else:
        # Show error with fallback to manual code copy
        return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Authorization Issue</title>
            <style>
                body {{ font-family: system-ui, sans-serif; background: #1a1a2e; color: #eee;
                       display: flex; justify-content: center; align-items: center;
                       min-height: 100vh; margin: 0; }}
                .container {{ text-align: center; padding: 40px; background: #16213e;
                             border-radius: 12px; max-width: 600px; }}
                h1 {{ color: #ffa500; margin-bottom: 20px; }}
                .warning {{ color: #ffa500; font-size: 48px; margin-bottom: 10px; }}
                .error {{ color: #ff6b6b; background: #2a1a2e; padding: 10px; border-radius: 6px;
                         margin: 15px 0; font-size: 14px; }}
                .code-box {{ background: #0f0f23; padding: 15px; border-radius: 8px;
                            word-break: break-all; font-family: monospace; font-size: 12px;
                            margin: 20px 0; border: 1px solid #333; }}
                p {{ color: #aaa; }}
                button {{ background: #4ecdc4; color: #1a1a2e; border: none; padding: 12px 24px;
                         border-radius: 6px; cursor: pointer; font-size: 16px; font-weight: bold;
                         margin-top: 10px; }}
                button:hover {{ background: #3dbdb5; }}
                #status {{ margin-top: 15px; color: #4ecdc4; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="warning">⚠️</div>
                <h1>Automatic Setup Failed</h1>
                <div class="error">Error: {exchange_error}</div>
                <p>You can still complete the setup manually. Copy this code:</p>
                <div class="code-box" id="code">{code}</div>
                <button onclick="copyCode()">Copy Code</button>
                <p id="status"></p>
                <p>Use the API endpoint POST /api/calendar/exchange-code with this code.</p>
            </div>
            <script>
                function copyCode() {{
                    const code = document.getElementById('code').textContent;
                    navigator.clipboard.writeText(code).then(() => {{
                        document.getElementById('status').textContent = 'Copied to clipboard!';
                    }});
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


class OAuthExchangeRequest(BaseModel):
    code: str  # The authorization code from Google OAuth callback


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
    from app.calendar_service import calendar_service
    from app.user_service import get_default_user

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
        raise HTTPException(
            status_code=400,
            detail="Google Calendar OAuth not configured. You need to complete the OAuth flow to connect your calendar."
        )

    is_configured = await calendar_service.is_configured(db, user)
    if not is_configured:
        raise HTTPException(
            status_code=400,
            detail="Google Calendar credentials are invalid or expired. Please reconnect your calendar."
        )

    try:
        synced_count = await calendar_service.sync_events(db, user=user)
        if synced_count == 0:
            return {"status": "synced", "events_synced": 0, "message": "No events found in the next 14 days"}
        return {"status": "synced", "events_synced": synced_count}
    except Exception as e:
        logger.error(f"Calendar sync failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.post("/exchange-code")
async def exchange_oauth_code(
    request: OAuthExchangeRequest,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Exchange OAuth authorization code for access tokens.

    This completes the OAuth flow by:
    1. Getting the stored client_id and client_secret
    2. Exchanging the auth code for access_token and refresh_token
    3. Saving the tokens to the database
    """
    import json
    from app.user_service import get_default_user

    user = await get_default_user(db)

    # Get existing OAuth config (should have client_id and client_secret)
    result = await db.execute(
        select(Settings).where(
            Settings.user_id == user.id,
            Settings.key == "google_calendar_token"
        )
    )
    token_setting = result.scalar_one_or_none()

    # Also check without user_id for backwards compatibility
    if not token_setting:
        result = await db.execute(
            select(Settings).where(Settings.key == "google_calendar_token")
        )
        token_setting = result.scalar_one_or_none()

    if not token_setting:
        raise HTTPException(
            status_code=400,
            detail="No OAuth configuration found. Please configure client_id and client_secret first."
        )

    try:
        token_data = json.loads(token_setting.value)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid token configuration in database")

    client_id = token_data.get('client_id')
    client_secret = token_data.get('client_secret')
    redirect_uri = token_data.get('redirect_uri')

    if not client_id or not client_secret:
        raise HTTPException(
            status_code=400,
            detail="Missing client_id or client_secret in OAuth configuration"
        )

    # Exchange the code for tokens
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": request.code,
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uri": redirect_uri or "https://example.invalid/api/calendar/callback",
                    "grant_type": "authorization_code",
                }
            )

            if response.status_code != 200:
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                error_msg = error_data.get('error_description', error_data.get('error', response.text))
                logger.error(f"Google OAuth token exchange failed: {response.status_code} - {error_msg}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to exchange code: {error_msg}"
                )

            tokens = response.json()

    except httpx.RequestError as e:
        logger.error(f"Network error during token exchange: {e}")
        raise HTTPException(status_code=500, detail=f"Network error: {str(e)}")

    # Update token data with the new tokens
    token_data['token'] = tokens.get('access_token')
    token_data['refresh_token'] = tokens.get('refresh_token')
    token_data['token_uri'] = 'https://oauth2.googleapis.com/token'

    # Save updated tokens
    token_setting.value = json.dumps(token_data)
    await db.flush()
    await db.commit()

    logger.info(f"Successfully exchanged OAuth code for tokens")

    return {
        "status": "success",
        "message": "OAuth tokens saved successfully. You can now sync your calendar.",
        "has_access_token": bool(tokens.get('access_token')),
        "has_refresh_token": bool(tokens.get('refresh_token')),
    }


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
