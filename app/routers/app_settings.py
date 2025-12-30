"""Settings API router."""

import json
import logging
import httpx

logger = logging.getLogger(__name__)
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from app.database import get_db
from app.auth import verify_api_key
from app.db_models import Settings, ChatMessage, CheckInSchedule, CheckInPrompt, ScheduledFollowup, MoodLog
from sqlalchemy import func
from app.llm import WARDEN_SYSTEM_PROMPT, DEFAULT_PROMPTS

router = APIRouter(prefix="/settings", tags=["settings"])

# Cache for OpenRouter models
_models_cache = {
    "models": [],
    "last_fetch": None,
    "cache_duration": timedelta(hours=1)
}


async def fetch_openrouter_models() -> List[dict]:
    """Fetch all available models from OpenRouter API."""
    # Return cached if still valid
    if (_models_cache["last_fetch"] and
        datetime.now() - _models_cache["last_fetch"] < _models_cache["cache_duration"] and
        _models_cache["models"]):
        return _models_cache["models"]

    try:
        async with httpx.AsyncClient() as client:
            # OpenRouter's model list is public, no auth needed
            response = await client.get(
                "https://openrouter.ai/api/v1/models",
                timeout=15.0
            )
            response.raise_for_status()
            data = response.json()

            models = []
            for model in data.get("data", []):
                model_id = model.get("id", "")
                name = model.get("name", model_id)

                # Extract provider from model ID (e.g., "openai/gpt-4" -> "OpenAI")
                provider = model_id.split("/")[0].title() if "/" in model_id else "Unknown"

                # Calculate cost indicator based on pricing
                pricing = model.get("pricing", {})
                prompt_cost = float(pricing.get("prompt", "0") or "0")

                if prompt_cost == 0:
                    cost = "Free"
                elif prompt_cost < 0.0001:
                    cost = "$"
                elif prompt_cost < 0.001:
                    cost = "$$"
                elif prompt_cost < 0.01:
                    cost = "$$$"
                else:
                    cost = "$$$$"

                models.append({
                    "id": model_id,
                    "name": name,
                    "provider": provider,
                    "cost": cost,
                    "context_length": model.get("context_length", 0),
                    "description": model.get("description", "")
                })

            # Sort by provider, then by name
            models.sort(key=lambda x: (x["provider"].lower(), x["name"].lower()))

            # Update cache
            _models_cache["models"] = models
            _models_cache["last_fetch"] = datetime.now()

            return models

    except Exception as e:
        # If fetch fails and we have cached data, return that
        if _models_cache["models"]:
            return _models_cache["models"]
        # Otherwise return a minimal fallback list
        return [
            {"id": "google/gemini-flash-1.5", "name": "Gemini Flash 1.5", "provider": "Google", "cost": "$", "context_length": 0, "description": ""},
            {"id": "openai/gpt-4o-mini", "name": "GPT-4o Mini", "provider": "OpenAI", "cost": "$", "context_length": 0, "description": ""},
            {"id": "anthropic/claude-3-haiku", "name": "Claude 3 Haiku", "provider": "Anthropic", "cost": "$", "context_length": 0, "description": ""},
        ]


class SettingUpdate(BaseModel):
    value: str


class SettingsResponse(BaseModel):
    openrouter_model: str
    system_prompt: str
    google_calendar_connected: bool
    gcal_client_id: Optional[str] = None
    gcal_client_secret: Optional[str] = None


class ChatMessageResponse(BaseModel):
    id: int
    role: str
    content: str
    message_type: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


async def get_setting(db: AsyncSession, key: str, default: str = "") -> str:
    """Get a setting value from the database."""
    result = await db.execute(select(Settings).where(Settings.key == key))
    setting = result.scalar_one_or_none()
    return setting.value if setting else default


async def set_setting(db: AsyncSession, key: str, value: str) -> None:
    """Set a setting value in the database."""
    result = await db.execute(select(Settings).where(Settings.key == key))
    setting = result.scalar_one_or_none()
    if setting:
        setting.value = value
    else:
        setting = Settings(key=key, value=value)
        db.add(setting)
    await db.flush()


@router.get("/models")
async def list_models(_: str = Depends(verify_api_key)):
    """List all available LLM models from OpenRouter."""
    return await fetch_openrouter_models()


@router.get("", response_model=SettingsResponse)
async def get_settings(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Get current settings."""
    model = await get_setting(db, "openrouter_model", "google/gemini-flash-1.5")
    prompt = await get_setting(db, "system_prompt", WARDEN_SYSTEM_PROMPT)
    calendar_json = await get_setting(db, "google_calendar_token", "")

    # Parse calendar credentials
    gcal_client_id = None
    gcal_client_secret = None
    calendar_connected = False

    if calendar_json:
        try:
            cal_data = json.loads(calendar_json)
            gcal_client_id = cal_data.get("client_id")
            gcal_client_secret = cal_data.get("client_secret")
            # Connected if we have tokens (not just credentials)
            calendar_connected = bool(cal_data.get("token") and cal_data.get("refresh_token"))
        except json.JSONDecodeError:
            pass

    return SettingsResponse(
        openrouter_model=model,
        system_prompt=prompt,
        google_calendar_connected=calendar_connected,
        gcal_client_id=gcal_client_id,
        gcal_client_secret=gcal_client_secret,
    )


@router.put("/model")
async def update_model(
    update: SettingUpdate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Update the LLM model."""
    if not update.value or "/" not in update.value:
        raise HTTPException(
            status_code=400,
            detail="Invalid model ID format. Must be provider/model-name"
        )

    await set_setting(db, "openrouter_model", update.value)
    return {"status": "updated", "model": update.value}


@router.put("/prompt")
async def update_prompt(
    update: SettingUpdate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Update the system prompt."""
    if len(update.value) < 50:
        raise HTTPException(status_code=400, detail="Prompt too short (min 50 chars)")

    await set_setting(db, "system_prompt", update.value)
    return {"status": "updated", "prompt_length": len(update.value)}


@router.get("/prompt/default")
async def get_default_prompt(_: str = Depends(verify_api_key)):
    """Get the default system prompt."""
    return {"prompt": WARDEN_SYSTEM_PROMPT}


@router.post("/prompt/reset")
async def reset_prompt(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Reset prompt to default."""
    await set_setting(db, "system_prompt", WARDEN_SYSTEM_PROMPT)
    return {"status": "reset", "prompt": WARDEN_SYSTEM_PROMPT}


@router.get("/chat-history", response_model=List[ChatMessageResponse])
async def get_chat_history(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Get chat message history."""
    # Get most recent messages, then reverse for chronological order
    result = await db.execute(
        select(ChatMessage)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
    )
    messages = list(reversed(result.scalars().all()))  # Reverse for oldest-first display
    return [
        ChatMessageResponse(
            id=m.id,
            role=m.role,
            content=m.content,
            message_type=m.message_type,
            created_at=m.created_at.isoformat(),
        )
        for m in messages
    ]


@router.get("/streaks")
async def get_streaks(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Get current streak information."""
    from app.streaks import get_streak_context
    return await get_streak_context(db)


class CalendarCredentials(BaseModel):
    client_id: str
    client_secret: str


class AuthCodeExchange(BaseModel):
    code: str


CALENDAR_SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']


@router.post("/calendar/credentials")
async def save_calendar_credentials(
    creds: CalendarCredentials,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Save Google Calendar OAuth credentials (client_id and client_secret)."""
    import json

    token_data = {
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "token": None,
        "refresh_token": None,
    }

    await set_setting(db, "google_calendar_token", json.dumps(token_data))

    return {"status": "saved", "message": "Credentials saved. Now authorize with Google."}


@router.get("/calendar/auth-url")
async def get_calendar_auth_url(
    request: Request,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Generate Google OAuth authorization URL."""
    import json
    from urllib.parse import urlencode

    # Get stored credentials
    result = await db.execute(select(Settings).where(Settings.key == "google_calendar_token"))
    setting = result.scalar_one_or_none()

    if not setting:
        raise HTTPException(status_code=400, detail="No credentials saved. Save client_id and client_secret first.")

    token_data = json.loads(setting.value)
    client_id = token_data.get("client_id")

    if not client_id:
        raise HTTPException(status_code=400, detail="No client_id found")

    # Build redirect URI from request
    # Railway terminates SSL at load balancer, so base_url shows http
    # Force https for production redirect URIs
    base_url = str(request.base_url)
    if base_url.startswith("http://") and "localhost" not in base_url and "127.0.0.1" not in base_url:
        base_url = base_url.replace("http://", "https://", 1)
    redirect_uri = f"{base_url}api/calendar/callback"

    # Build auth URL
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(CALENDAR_SCOPES),
        "access_type": "offline",
        "prompt": "consent",
    }

    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"

    # Store redirect_uri for later use
    token_data["redirect_uri"] = redirect_uri
    await set_setting(db, "google_calendar_token", json.dumps(token_data))

    return {"auth_url": auth_url, "redirect_uri": redirect_uri}


@router.post("/calendar/exchange-code")
async def exchange_calendar_code(
    data: AuthCodeExchange,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Exchange authorization code for tokens."""
    import json

    # Get stored credentials
    result = await db.execute(select(Settings).where(Settings.key == "google_calendar_token"))
    setting = result.scalar_one_or_none()

    if not setting:
        raise HTTPException(status_code=400, detail="No credentials saved")

    token_data = json.loads(setting.value)
    client_id = token_data.get("client_id")
    client_secret = token_data.get("client_secret")
    redirect_uri = token_data.get("redirect_uri", f"{request.base_url}api/calendar/callback")

    if not client_id or not client_secret:
        raise HTTPException(status_code=400, detail="Missing client credentials")

    # Exchange code for tokens
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "code": data.code,
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri,
                },
            )

            if response.status_code != 200:
                error_data = response.json()
                return {"status": "error", "error": error_data.get("error_description", "Token exchange failed")}

            tokens = response.json()

            # Save the tokens
            token_data["token"] = tokens.get("access_token")
            token_data["refresh_token"] = tokens.get("refresh_token")
            token_data["token_uri"] = "https://oauth2.googleapis.com/token"

            await set_setting(db, "google_calendar_token", json.dumps(token_data))

            # Trigger initial calendar sync
            try:
                from app.calendar_service import calendar_service
                synced_count = await calendar_service.sync_events(db)
                return {"status": "connected", "message": f"Calendar connected! Synced {synced_count} events."}
            except Exception as sync_error:
                logger.warning(f"Initial calendar sync failed: {sync_error}")
                return {"status": "connected", "message": "Calendar connected. Sync will happen on next check-in."}

    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.delete("/calendar/credentials")
async def delete_calendar_credentials(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Remove Google Calendar credentials."""
    result = await db.execute(select(Settings).where(Settings.key == "google_calendar_token"))
    setting = result.scalar_one_or_none()

    if setting:
        await db.delete(setting)
        await db.flush()

    return {"status": "deleted", "message": "Calendar credentials removed"}


# ============== Check-in Schedules ==============

class ScheduleCreate(BaseModel):
    name: str
    check_in_type: str = "custom"
    hour: int
    minute: int = 0
    days_of_week: Optional[str] = None  # e.g., "mon,tue,wed,thu,fri"
    prompt_template: Optional[str] = None
    is_active: bool = True


class ScheduleUpdate(BaseModel):
    name: Optional[str] = None
    hour: Optional[int] = None
    minute: Optional[int] = None
    days_of_week: Optional[str] = None
    prompt_template: Optional[str] = None
    is_active: Optional[bool] = None


class ScheduleResponse(BaseModel):
    id: int
    name: str
    check_in_type: str
    hour: int
    minute: int
    days_of_week: Optional[str]
    prompt_template: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True


@router.get("/schedules", response_model=List[ScheduleResponse])
async def list_schedules(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """List all check-in schedules."""
    result = await db.execute(
        select(CheckInSchedule).order_by(CheckInSchedule.hour, CheckInSchedule.minute)
    )
    return result.scalars().all()


@router.post("/schedules", response_model=ScheduleResponse)
async def create_schedule(
    schedule: ScheduleCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Create a new check-in schedule."""
    if schedule.hour < 0 or schedule.hour > 23:
        raise HTTPException(status_code=400, detail="Hour must be 0-23")
    if schedule.minute < 0 or schedule.minute > 59:
        raise HTTPException(status_code=400, detail="Minute must be 0-59")

    db_schedule = CheckInSchedule(
        name=schedule.name,
        check_in_type=schedule.check_in_type,
        hour=schedule.hour,
        minute=schedule.minute,
        days_of_week=schedule.days_of_week,
        prompt_template=schedule.prompt_template,
        is_active=schedule.is_active,
    )
    db.add(db_schedule)
    await db.commit()
    await db.refresh(db_schedule)

    # Reload scheduler with new schedules
    from app.scheduler import reload_custom_schedules
    await reload_custom_schedules()

    return db_schedule


@router.put("/schedules/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: int,
    update: ScheduleUpdate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Update a check-in schedule."""
    result = await db.execute(
        select(CheckInSchedule).where(CheckInSchedule.id == schedule_id)
    )
    schedule = result.scalar_one_or_none()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    update_data = update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(schedule, field, value)

    await db.commit()
    await db.refresh(schedule)

    # Reload scheduler
    from app.scheduler import reload_custom_schedules
    await reload_custom_schedules()

    return schedule


@router.delete("/schedules/{schedule_id}")
async def delete_schedule(
    schedule_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Delete a check-in schedule."""
    result = await db.execute(
        select(CheckInSchedule).where(CheckInSchedule.id == schedule_id)
    )
    schedule = result.scalar_one_or_none()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    await db.delete(schedule)
    await db.commit()

    # Reload scheduler
    from app.scheduler import reload_custom_schedules
    await reload_custom_schedules()

    return {"status": "deleted"}


# ============== Check-in Prompts ==============

class PromptResponse(BaseModel):
    prompt_type: str
    prompt_template: str
    is_custom: bool
    is_default_available: bool


class PromptUpdate(BaseModel):
    prompt_template: str


@router.get("/prompts")
async def list_prompts(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """List all check-in prompts (custom and defaults)."""
    result = await db.execute(select(CheckInPrompt))
    custom_prompts = {p.prompt_type: p for p in result.scalars().all()}

    # Combine with defaults
    prompts = []
    for prompt_type, default_template in DEFAULT_PROMPTS.items():
        custom = custom_prompts.get(prompt_type)
        prompts.append({
            "prompt_type": prompt_type,
            "prompt_template": custom.prompt_template if custom else default_template,
            "is_custom": bool(custom),
            "is_default_available": True,
        })

    return prompts


@router.get("/prompts/{prompt_type}")
async def get_prompt(
    prompt_type: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Get a specific prompt."""
    result = await db.execute(
        select(CheckInPrompt).where(CheckInPrompt.prompt_type == prompt_type)
    )
    custom = result.scalar_one_or_none()

    default = DEFAULT_PROMPTS.get(prompt_type)
    if not custom and not default:
        raise HTTPException(status_code=404, detail="Prompt type not found")

    return {
        "prompt_type": prompt_type,
        "prompt_template": custom.prompt_template if custom else default,
        "is_custom": bool(custom),
        "default_template": default,
    }


@router.put("/prompts/{prompt_type}")
async def update_prompt_template(
    prompt_type: str,
    update: PromptUpdate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Update or create a custom prompt."""
    if prompt_type not in DEFAULT_PROMPTS:
        raise HTTPException(status_code=400, detail=f"Invalid prompt type. Must be one of: {list(DEFAULT_PROMPTS.keys())}")

    result = await db.execute(
        select(CheckInPrompt).where(CheckInPrompt.prompt_type == prompt_type)
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.prompt_template = update.prompt_template
        existing.is_custom = True
    else:
        new_prompt = CheckInPrompt(
            prompt_type=prompt_type,
            prompt_template=update.prompt_template,
            is_custom=True,
        )
        db.add(new_prompt)

    await db.commit()
    return {"status": "updated", "prompt_type": prompt_type}


@router.post("/prompts/{prompt_type}/reset")
async def reset_prompt_template(
    prompt_type: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Reset a prompt to its default."""
    result = await db.execute(
        select(CheckInPrompt).where(CheckInPrompt.prompt_type == prompt_type)
    )
    existing = result.scalar_one_or_none()

    if existing:
        await db.delete(existing)
        await db.commit()

    default = DEFAULT_PROMPTS.get(prompt_type, "")
    return {"status": "reset", "prompt_template": default}


# =============================================================================
# Memory Endpoints
# =============================================================================

@router.put("/memory")
async def update_memory(
    update: SettingUpdate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Update the LLM memory/context."""
    await set_setting(db, "llm_memory", update.value)
    await db.commit()
    return {"status": "updated", "memory_length": len(update.value)}


@router.get("/memory")
async def get_memory(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Get the current LLM memory."""
    memory = await get_setting(db, "llm_memory", "")
    return {"memory": memory}


@router.delete("/memory")
async def clear_memory(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Clear the LLM memory."""
    await set_setting(db, "llm_memory", "")
    await db.commit()
    return {"status": "cleared"}


@router.get("/chat-history-count")
async def get_chat_history_count(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Get how many chat messages the LLM sees in context."""
    count = await get_setting(db, "chat_history_count", "15")
    return {"count": int(count)}


@router.put("/chat-history-count")
async def update_chat_history_count(
    count: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Update how many chat messages the LLM sees in context."""
    if count < 0 or count > 100:
        raise HTTPException(status_code=400, detail="Count must be between 0 and 100")
    await set_setting(db, "chat_history_count", str(count))
    await db.commit()
    return {"status": "updated", "count": count}


# =============================================================================
# Agent Intelligence Endpoints
# =============================================================================

@router.get("/agent/intensity")
async def get_intensity(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Get current accountability intensity level (1-5)."""
    intensity = await get_setting(db, "accountability_intensity", "3")
    return {"intensity": int(intensity)}


@router.put("/agent/intensity")
async def update_intensity(
    intensity: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Update accountability intensity level (1-5)."""
    if intensity < 1 or intensity > 5:
        raise HTTPException(status_code=400, detail="Intensity must be between 1 and 5")
    await set_setting(db, "accountability_intensity", str(intensity))
    await db.commit()
    return {"status": "updated", "intensity": intensity}


@router.get("/agent/thinking-level")
async def get_thinking_level(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Get current thinking level for LLM."""
    level = await get_setting(db, "thinking_level", "medium")
    return {"thinking_level": level}


@router.put("/agent/thinking-level")
async def update_thinking_level(
    level: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Update thinking level for LLM."""
    valid_levels = ["off", "minimal", "low", "medium", "high"]
    if level not in valid_levels:
        raise HTTPException(status_code=400, detail=f"Level must be one of: {', '.join(valid_levels)}")
    await set_setting(db, "thinking_level", level)
    await db.commit()
    return {"status": "updated", "thinking_level": level}


@router.get("/agent/mood")
async def get_mood_trend(
    days: int = 7,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Get mood trends over the specified number of days."""
    cutoff = datetime.utcnow() - timedelta(days=days)

    result = await db.execute(
        select(
            func.avg(MoodLog.mood_score).label("avg_mood"),
            func.count(MoodLog.id).label("count")
        ).where(MoodLog.created_at >= cutoff)
    )
    row = result.one()

    # Calculate average energy (need to convert string to number)
    energy_result = await db.execute(
        select(MoodLog.energy_level).where(
            MoodLog.created_at >= cutoff,
            MoodLog.energy_level.isnot(None)
        )
    )
    energy_levels = [r[0] for r in energy_result.all()]

    # Convert energy levels to numeric for averaging
    energy_map = {"low": 1, "medium": 2, "high": 3}
    if energy_levels:
        numeric_energy = [energy_map.get(e, 2) for e in energy_levels]
        avg_energy = sum(numeric_energy) / len(numeric_energy)
    else:
        avg_energy = None

    return {
        "avg_mood": float(row.avg_mood) if row.avg_mood else None,
        "avg_energy": avg_energy,
        "entries": row.count,
        "days": days
    }


@router.get("/agent/followups")
async def get_followups(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Get pending scheduled follow-ups."""
    result = await db.execute(
        select(ScheduledFollowup)
        .where(ScheduledFollowup.status == "pending")
        .order_by(ScheduledFollowup.scheduled_time)
    )
    followups = result.scalars().all()

    return {
        "followups": [
            {
                "id": f.id,
                "topic": f.topic,
                "reason": f.reason,
                "scheduled_time": f.scheduled_time.isoformat() if f.scheduled_time else None,
                "created_at": f.created_at.isoformat() if f.created_at else None
            }
            for f in followups
        ]
    }


@router.delete("/agent/followups/{followup_id}")
async def cancel_followup(
    followup_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Cancel a scheduled follow-up."""
    result = await db.execute(
        select(ScheduledFollowup).where(ScheduledFollowup.id == followup_id)
    )
    followup = result.scalar_one_or_none()

    if not followup:
        raise HTTPException(status_code=404, detail="Follow-up not found")

    followup.status = "cancelled"
    await db.commit()

    return {"status": "cancelled", "id": followup_id}
