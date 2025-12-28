"""Google Calendar integration router."""

import logging
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from pydantic import BaseModel
import httpx

from app.database import get_db
from app.auth import verify_api_key
from app.db_models import CalendarEvent, Settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/calendar", tags=["calendar"])


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
    api_key = await get_calendar_api_key(db)
    return {"connected": bool(api_key)}


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
