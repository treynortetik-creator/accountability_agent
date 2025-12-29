"""Google Calendar integration for The Warden."""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import pytz

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from sqlalchemy import select, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_models import CalendarEvent, Settings
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# OAuth scopes needed
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

# Keywords that indicate OOO/vacation
OOO_KEYWORDS = ['ooo', 'out of office', 'vacation', 'holiday', 'pto', 'off', 'travel', 'traveling', 'away']


class CalendarService:
    """Service for Google Calendar integration."""

    def __init__(self):
        self._service = None
        self._credentials = None

    async def is_configured(self, db: AsyncSession) -> bool:
        """Check if Google Calendar is configured with valid credentials."""
        try:
            creds = await self._get_credentials(db)
            return creds is not None and creds.valid
        except Exception:
            return False

    async def _get_credentials(self, db: AsyncSession) -> Optional[Credentials]:
        """Get and refresh credentials from database."""
        try:
            # Get stored token
            result = await db.execute(
                select(Settings).where(Settings.key == "google_calendar_token")
            )
            token_setting = result.scalar_one_or_none()

            if not token_setting:
                return None

            token_data = json.loads(token_setting.value)
            creds = Credentials(
                token=token_data.get('token'),
                refresh_token=token_data.get('refresh_token'),
                token_uri=token_data.get('token_uri', 'https://oauth2.googleapis.com/token'),
                client_id=token_data.get('client_id'),
                client_secret=token_data.get('client_secret'),
                scopes=SCOPES
            )

            # Refresh if expired
            if creds.expired and creds.refresh_token:
                # Wrap blocking refresh call in thread to avoid blocking event loop
                await asyncio.to_thread(creds.refresh, Request())
                # Save refreshed token
                await self._save_credentials(db, creds, token_data.get('client_id'), token_data.get('client_secret'))

            return creds

        except Exception as e:
            logger.error(f"Failed to get calendar credentials: {e}")
            return None

    async def _save_credentials(self, db: AsyncSession, creds: Credentials, client_id: str, client_secret: str):
        """Save credentials to database."""
        token_data = {
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': client_id,
            'client_secret': client_secret,
        }

        result = await db.execute(
            select(Settings).where(Settings.key == "google_calendar_token")
        )
        setting = result.scalar_one_or_none()

        if setting:
            setting.value = json.dumps(token_data)
        else:
            setting = Settings(key="google_calendar_token", value=json.dumps(token_data))
            db.add(setting)

        await db.flush()

    def _get_service(self, creds: Credentials):
        """Get or create the Calendar API service."""
        if self._service is None or self._credentials != creds:
            self._service = build('calendar', 'v3', credentials=creds)
            self._credentials = creds
        return self._service

    async def sync_events(self, db: AsyncSession, days_ahead: int = 14) -> int:
        """Sync calendar events from Google Calendar."""
        creds = await self._get_credentials(db)
        if not creds:
            return 0

        try:
            service = self._get_service(creds)

            # Calculate time range
            tz = pytz.timezone(settings.timezone)
            now = datetime.now(tz)
            time_min = now.isoformat()
            time_max = (now + timedelta(days=days_ahead)).isoformat()

            # Fetch events
            events_result = service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                maxResults=100,
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            events = events_result.get('items', [])

            # Track Google event IDs from this sync
            google_event_ids = set()
            synced_count = 0

            # Upsert logic: update existing events or insert new ones
            for event in events:
                google_event_id = event['id']
                google_event_ids.add(google_event_id)

                start = event.get('start', {})
                end = event.get('end', {})

                # Determine if all-day event
                all_day = 'date' in start

                if all_day:
                    start_time = datetime.strptime(start['date'], '%Y-%m-%d')
                    end_time = datetime.strptime(end['date'], '%Y-%m-%d') if 'date' in end else None
                else:
                    start_time = datetime.fromisoformat(start['dateTime'].replace('Z', '+00:00'))
                    end_time = datetime.fromisoformat(end['dateTime'].replace('Z', '+00:00')) if 'dateTime' in end else None

                # Check if this is an OOO event
                title = event.get('summary', '').lower()
                description = event.get('description', '').lower()
                is_ooo = any(kw in title or kw in description for kw in OOO_KEYWORDS)

                # Also check event status (tentative events marked as OOO)
                if event.get('eventType') == 'outOfOffice':
                    is_ooo = True

                # Check if event already exists
                result = await db.execute(
                    select(CalendarEvent).where(CalendarEvent.google_event_id == google_event_id)
                )
                existing_event = result.scalar_one_or_none()

                if existing_event:
                    # Update existing event
                    existing_event.title = event.get('summary', 'No Title')
                    existing_event.description = event.get('description')
                    existing_event.start_time = start_time
                    existing_event.end_time = end_time
                    existing_event.all_day = all_day
                    existing_event.location = event.get('location')
                    existing_event.is_ooo = is_ooo
                else:
                    # Insert new event
                    cal_event = CalendarEvent(
                        google_event_id=google_event_id,
                        title=event.get('summary', 'No Title'),
                        description=event.get('description'),
                        start_time=start_time,
                        end_time=end_time,
                        all_day=all_day,
                        location=event.get('location'),
                        is_ooo=is_ooo,
                    )
                    db.add(cal_event)

                synced_count += 1

            # Delete events that were removed from Google Calendar
            # (events not in the current sync response)
            # NOTE: Only delete if we synced events from Google.
            # If google_event_ids is empty, preserve existing events to avoid
            # data loss in case of API errors or network issues.
            if google_event_ids:
                await db.execute(
                    delete(CalendarEvent).where(
                        CalendarEvent.google_event_id.not_in(google_event_ids)
                    )
                )

            await db.flush()
            logger.info(f"Synced {synced_count} calendar events")
            return synced_count

        except HttpError as e:
            logger.error(f"Google Calendar API error: {e}")
            return 0
        except Exception as e:
            logger.error(f"Failed to sync calendar: {e}")
            return 0

    async def get_upcoming_events(self, db: AsyncSession, hours_ahead: int = 2) -> List[CalendarEvent]:
        """Get events happening in the next N hours."""
        tz = pytz.timezone(settings.timezone)
        now = datetime.now(tz).replace(tzinfo=None)
        cutoff = now + timedelta(hours=hours_ahead)

        result = await db.execute(
            select(CalendarEvent).where(
                and_(
                    CalendarEvent.start_time >= now,
                    CalendarEvent.start_time <= cutoff,
                    CalendarEvent.all_day == False,
                )
            ).order_by(CalendarEvent.start_time)
        )
        return result.scalars().all()

    async def is_ooo_today(self, db: AsyncSession) -> bool:
        """Check if there's an all-day OOO event today."""
        tz = pytz.timezone(settings.timezone)
        today = datetime.now(tz).date()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())

        result = await db.execute(
            select(CalendarEvent).where(
                and_(
                    CalendarEvent.all_day == True,
                    CalendarEvent.is_ooo == True,
                    CalendarEvent.start_time <= today_end,
                    CalendarEvent.end_time >= today_start if CalendarEvent.end_time else True,
                )
            )
        )
        return result.scalar_one_or_none() is not None

    async def get_weekly_meeting_hours(self, db: AsyncSession) -> float:
        """Calculate total meeting hours in the past week."""
        tz = pytz.timezone(settings.timezone)
        now = datetime.now(tz).replace(tzinfo=None)
        week_ago = now - timedelta(days=7)

        result = await db.execute(
            select(CalendarEvent).where(
                and_(
                    CalendarEvent.start_time >= week_ago,
                    CalendarEvent.start_time <= now,
                    CalendarEvent.all_day == False,
                )
            )
        )
        events = result.scalars().all()

        total_hours = 0.0
        for event in events:
            if event.end_time:
                duration = (event.end_time - event.start_time).total_seconds() / 3600
                total_hours += duration

        return round(total_hours, 1)

    async def get_calendar_context(self, db: AsyncSession) -> Dict[str, Any]:
        """Get calendar context for LLM prompts."""
        is_configured = await self.is_configured(db)

        if not is_configured:
            return {
                "calendar_configured": False,
                "upcoming_meetings": [],
                "is_ooo_today": False,
                "weekly_meeting_hours": 0,
            }

        # Sync events first (if not synced recently)
        await self.sync_events(db)

        upcoming = await self.get_upcoming_events(db, hours_ahead=2)
        is_ooo = await self.is_ooo_today(db)
        meeting_hours = await self.get_weekly_meeting_hours(db)

        return {
            "calendar_configured": True,
            "upcoming_meetings": [
                {
                    "title": e.title,
                    "start_time": e.start_time.isoformat(),
                    "duration_minutes": (e.end_time - e.start_time).total_seconds() / 60 if e.end_time else None,
                }
                for e in upcoming
            ],
            "is_ooo_today": is_ooo,
            "weekly_meeting_hours": meeting_hours,
        }


# Global service instance
calendar_service = CalendarService()
