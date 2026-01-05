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
from app.db_models import Settings, ChatMessage, CheckInSchedule, CheckInPrompt, ScheduledFollowup, MoodLog, User
from sqlalchemy import func
from app.llm import WARDEN_SYSTEM_PROMPT, DEFAULT_PROMPTS
from app.user_service import get_default_user

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


async def get_setting(db: AsyncSession, key: str, default: str = "", user: User = None) -> str:
    """Get a setting value from the database for a specific user."""
    if user is None:
        user = await get_default_user(db)
    result = await db.execute(
        select(Settings).where(Settings.user_id == user.id, Settings.key == key)
    )
    setting = result.scalar_one_or_none()
    return setting.value if setting else default


async def set_setting(db: AsyncSession, key: str, value: str, user: User = None) -> None:
    """Set a setting value in the database for a specific user."""
    if user is None:
        user = await get_default_user(db)
    result = await db.execute(
        select(Settings).where(Settings.user_id == user.id, Settings.key == key)
    )
    setting = result.scalar_one_or_none()
    if setting:
        setting.value = value
    else:
        setting = Settings(user_id=user.id, key=key, value=value)
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
    user = await get_default_user(db)

    # Get most recent messages, then reverse for chronological order
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.user_id == user.id)
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
            created_at=m.created_at.isoformat() + "Z",  # Add Z to indicate UTC
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

    # Get stored credentials
    result = await db.execute(select(Settings).where(Settings.key == "google_calendar_token"))
    setting = result.scalar_one_or_none()

    if not setting:
        await log_calendar_error("CalendarExchangeError", "No credentials saved in database")
        raise HTTPException(status_code=400, detail="No credentials saved")

    token_data = json.loads(setting.value)
    client_id = token_data.get("client_id")
    client_secret = token_data.get("client_secret")
    redirect_uri = token_data.get("redirect_uri", f"{request.base_url}api/calendar/callback")

    if not client_id or not client_secret:
        await log_calendar_error("CalendarExchangeError", "Missing client_id or client_secret")
        raise HTTPException(status_code=400, detail="Missing client credentials")

    logger.info(f"Exchanging OAuth code (length={len(data.code)}) with redirect_uri={redirect_uri}")

    # Exchange code for tokens
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
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

            logger.info(f"Google token response status: {response.status_code}")

            if response.status_code != 200:
                try:
                    error_data = response.json()
                except:
                    error_data = {"error": response.text}

                error_msg = error_data.get("error_description", error_data.get("error", "Token exchange failed"))
                logger.error(f"Google OAuth token exchange failed: {error_msg}")
                await log_calendar_error(
                    "CalendarTokenExchangeFailed",
                    error_msg,
                    {"status_code": response.status_code, "error_data": error_data, "redirect_uri": redirect_uri}
                )
                return {"status": "error", "error": error_msg}

            tokens = response.json()
            logger.info(f"Got tokens - access_token: {'yes' if tokens.get('access_token') else 'no'}, refresh_token: {'yes' if tokens.get('refresh_token') else 'no'}")

            # Save the tokens
            token_data["token"] = tokens.get("access_token")
            token_data["refresh_token"] = tokens.get("refresh_token")
            token_data["token_uri"] = "https://oauth2.googleapis.com/token"

            await set_setting(db, "google_calendar_token", json.dumps(token_data))
            # CRITICAL: Commit the tokens BEFORE trying to sync
            # Otherwise if sync fails, the transaction rolls back and tokens are lost
            await db.commit()
            logger.info("Saved and committed OAuth tokens to database")

            # Trigger initial calendar sync
            try:
                from app.calendar_service import calendar_service
                synced_count = await calendar_service.sync_events(db)
                logger.info(f"Initial calendar sync completed: {synced_count} events")
                return {"status": "connected", "message": f"Calendar connected! Synced {synced_count} events."}
            except Exception as sync_error:
                logger.warning(f"Initial calendar sync failed: {sync_error}", exc_info=True)
                await log_calendar_error(
                    "CalendarSyncError",
                    str(sync_error),
                    {"phase": "initial_sync"}
                )
                await db.commit()  # Commit the error log
                return {"status": "connected", "message": "Calendar connected. Sync will happen on next check-in."}

    except httpx.TimeoutException as e:
        logger.error(f"Timeout during token exchange: {e}")
        await log_calendar_error("CalendarExchangeTimeout", str(e))
        return {"status": "error", "error": "Request to Google timed out. Please try again."}
    except Exception as e:
        logger.error(f"Exception during token exchange: {e}", exc_info=True)
        await log_calendar_error("CalendarExchangeException", str(e))
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
    user = await get_default_user(db)

    result = await db.execute(
        select(CheckInSchedule)
        .where(CheckInSchedule.user_id == user.id)
        .order_by(CheckInSchedule.hour, CheckInSchedule.minute)
    )
    return result.scalars().all()


@router.post("/schedules", response_model=ScheduleResponse)
async def create_schedule(
    schedule: ScheduleCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Create a new check-in schedule."""
    user = await get_default_user(db)

    if schedule.hour < 0 or schedule.hour > 23:
        raise HTTPException(status_code=400, detail="Hour must be 0-23")
    if schedule.minute < 0 or schedule.minute > 59:
        raise HTTPException(status_code=400, detail="Minute must be 0-59")

    db_schedule = CheckInSchedule(
        user_id=user.id,
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
    user = await get_default_user(db)

    # Validate hour/minute if provided
    if update.hour is not None and (update.hour < 0 or update.hour > 23):
        raise HTTPException(status_code=400, detail="Hour must be 0-23")
    if update.minute is not None and (update.minute < 0 or update.minute > 59):
        raise HTTPException(status_code=400, detail="Minute must be 0-59")

    result = await db.execute(
        select(CheckInSchedule).where(
            CheckInSchedule.id == schedule_id,
            CheckInSchedule.user_id == user.id
        )
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
    user = await get_default_user(db)

    result = await db.execute(
        select(CheckInSchedule).where(
            CheckInSchedule.id == schedule_id,
            CheckInSchedule.user_id == user.id
        )
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
    user = await get_default_user(db)

    result = await db.execute(
        select(CheckInPrompt).where(CheckInPrompt.user_id == user.id)
    )
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
    user = await get_default_user(db)

    result = await db.execute(
        select(CheckInPrompt).where(
            CheckInPrompt.user_id == user.id,
            CheckInPrompt.prompt_type == prompt_type
        )
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
    user = await get_default_user(db)

    if prompt_type not in DEFAULT_PROMPTS:
        raise HTTPException(status_code=400, detail=f"Invalid prompt type. Must be one of: {list(DEFAULT_PROMPTS.keys())}")

    result = await db.execute(
        select(CheckInPrompt).where(
            CheckInPrompt.user_id == user.id,
            CheckInPrompt.prompt_type == prompt_type
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.prompt_template = update.prompt_template
        existing.is_custom = True
    else:
        new_prompt = CheckInPrompt(
            user_id=user.id,
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
    user = await get_default_user(db)

    result = await db.execute(
        select(CheckInPrompt).where(
            CheckInPrompt.user_id == user.id,
            CheckInPrompt.prompt_type == prompt_type
        )
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


# ============== Quiet Hours ==============

@router.get("/quiet-hours")
async def get_quiet_hours(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Get quiet hours settings."""
    from app.config import get_settings
    from app.telegram_bot import is_quiet_hours
    settings = get_settings()

    # Check if we have database overrides
    enabled = await get_setting(db, "quiet_hours_enabled", str(settings.quiet_hours_enabled))
    start_hour = await get_setting(db, "quiet_hours_start_hour", str(settings.quiet_hours_start_hour))
    start_minute = await get_setting(db, "quiet_hours_start_minute", str(settings.quiet_hours_start_minute))
    end_hour = await get_setting(db, "quiet_hours_end_hour", str(settings.quiet_hours_end_hour))
    end_minute = await get_setting(db, "quiet_hours_end_minute", str(settings.quiet_hours_end_minute))

    return {
        "enabled": enabled.lower() == "true",
        "start_hour": int(start_hour),
        "start_minute": int(start_minute),
        "end_hour": int(end_hour),
        "end_minute": int(end_minute),
        "currently_quiet": is_quiet_hours(),
    }


@router.put("/quiet-hours")
async def update_quiet_hours(
    enabled: Optional[bool] = None,
    start_hour: Optional[int] = None,
    start_minute: Optional[int] = None,
    end_hour: Optional[int] = None,
    end_minute: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Update quiet hours settings."""
    # Validate hour/minute ranges
    if start_hour is not None and (start_hour < 0 or start_hour > 23):
        raise HTTPException(status_code=400, detail="Start hour must be 0-23")
    if end_hour is not None and (end_hour < 0 or end_hour > 23):
        raise HTTPException(status_code=400, detail="End hour must be 0-23")
    if start_minute is not None and (start_minute < 0 or start_minute > 59):
        raise HTTPException(status_code=400, detail="Start minute must be 0-59")
    if end_minute is not None and (end_minute < 0 or end_minute > 59):
        raise HTTPException(status_code=400, detail="End minute must be 0-59")

    # Update each setting if provided
    if enabled is not None:
        await set_setting(db, "quiet_hours_enabled", str(enabled).lower())
    if start_hour is not None:
        await set_setting(db, "quiet_hours_start_hour", str(start_hour))
    if start_minute is not None:
        await set_setting(db, "quiet_hours_start_minute", str(start_minute))
    if end_hour is not None:
        await set_setting(db, "quiet_hours_end_hour", str(end_hour))
    if end_minute is not None:
        await set_setting(db, "quiet_hours_end_minute", str(end_minute))

    await db.commit()

    # Return updated values
    return {
        "status": "updated",
        "enabled": enabled if enabled is not None else None,
        "start_hour": start_hour if start_hour is not None else None,
        "start_minute": start_minute if start_minute is not None else None,
        "end_hour": end_hour if end_hour is not None else None,
        "end_minute": end_minute if end_minute is not None else None,
    }


class SendChatRequest(BaseModel):
    """Request model for sending a chat message from dashboard."""
    message: str


class SendChatResponse(BaseModel):
    """Response model for dashboard chat."""
    reply: str
    user_message_id: int
    warden_message_id: int


@router.post("/chat/send", response_model=SendChatResponse)
async def send_chat_message(
    request: SendChatRequest,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Send a chat message from the dashboard and get the Warden's reply.

    This processes messages the same way as Telegram, but without sending to Telegram.
    """
    from app.routers.webhook import (
        try_handle_completion,
        handle_pending_confirmation,
        try_parse_commitment,
    )
    from app.scheduler import get_context
    from app.llm import analyze_response
    from app.db_models import (
        CheckIn, Response, Commitment, CommitmentStatus,
        ScheduledFollowup, MoodLog
    )
    from app.streaks import update_response_streak
    import pytz

    # Get the default user for dashboard chat
    user = await get_default_user(db)
    if not user:
        raise HTTPException(status_code=500, detail="No user configured")

    message_text = request.message.strip()
    if not message_text:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Update response streak
    await update_response_streak(db)

    # Save user message to chat history
    user_chat_msg = ChatMessage(
        user_id=user.id,
        role="user",
        content=message_text,
        message_type="reply",
        telegram_message_id=None,  # No Telegram message for dashboard chat
    )
    db.add(user_chat_msg)
    await db.flush()  # Get the ID
    user_message_id = user_chat_msg.id

    # Check if this is a completion phrase ("done", "shipped", etc.)
    handled, reply = await try_handle_completion(db, message_text, user)
    if handled:
        if reply:
            warden_chat_msg = ChatMessage(
                user_id=user.id,
                role="warden",
                content=reply,
                message_type="completion",
                telegram_message_id=None,
            )
            db.add(warden_chat_msg)
            await db.flush()
            await db.commit()
            return SendChatResponse(
                reply=reply,
                user_message_id=user_message_id,
                warden_message_id=warden_chat_msg.id,
            )

    # Check if this is a confirmation response to a pending commitment
    handled, reply = await handle_pending_confirmation(db, message_text, user)
    if handled:
        if reply:
            warden_chat_msg = ChatMessage(
                user_id=user.id,
                role="warden",
                content=reply,
                message_type="commitment_confirm",
                telegram_message_id=None,
            )
            db.add(warden_chat_msg)
            await db.flush()
            await db.commit()
            return SendChatResponse(
                reply=reply,
                user_message_id=user_message_id,
                warden_message_id=warden_chat_msg.id,
            )

    # Build context for analysis
    context = await get_context(db)

    # Try to parse as a commitment first
    parsed_commitment, commit_reply = await try_parse_commitment(db, message_text, context)
    if parsed_commitment:
        if commit_reply:
            warden_chat_msg = ChatMessage(
                user_id=user.id,
                role="warden",
                content=commit_reply,
                message_type="commitment_confirm",
                telegram_message_id=None,
            )
            db.add(warden_chat_msg)
            await db.flush()
            await db.commit()
            return SendChatResponse(
                reply=commit_reply,
                user_message_id=user_message_id,
                warden_message_id=warden_chat_msg.id,
            )

    # Find the most recent unanswered check-in
    recent_checkin = await db.execute(
        select(CheckIn)
        .where(CheckIn.user_id == user.id)
        .where(CheckIn.response_received == False)
        .order_by(CheckIn.sent_at.desc())
        .limit(1)
    )
    checkin = recent_checkin.scalar_one_or_none()

    # Calculate days since last shipped
    last_shipped = await db.execute(
        select(Commitment)
        .where(Commitment.user_id == user.id)
        .where(Commitment.status == CommitmentStatus.COMPLETED)
        .order_by(Commitment.completed_at.desc())
        .limit(1)
    )
    last_shipped_commitment = last_shipped.scalar_one_or_none()
    if last_shipped_commitment and last_shipped_commitment.completed_at:
        days_since_shipped = (
            datetime.utcnow() - last_shipped_commitment.completed_at
        ).days
    else:
        days_since_shipped = "never"
    context["days_since_shipped"] = days_since_shipped

    # Fetch recent chat history for context
    chat_history_result = await db.execute(
        select(ChatMessage)
        .order_by(ChatMessage.created_at.desc())
        .limit(20)
    )
    chat_messages = list(reversed(chat_history_result.scalars().all()))
    chat_history = [
        {"role": msg.role, "content": msg.content}
        for msg in chat_messages
    ]

    # Analyze the response using LLM (with chat history)
    analysis = await analyze_response(message_text, context, chat_history)

    # Process memory update if provided
    memory_update = analysis.get("memory_update")
    if memory_update:
        memory_result = await db.execute(
            select(Settings).where(Settings.key == "llm_memory")
        )
        memory_setting = memory_result.scalar_one_or_none()
        current_memory = memory_setting.value if memory_setting else ""

        if isinstance(memory_update, str) and memory_update.strip():
            new_memory = memory_update.strip()
        elif isinstance(memory_update, dict):
            action = memory_update.get("action", "replace")
            content = memory_update.get("content", "").strip()

            if action == "append" and content:
                if current_memory:
                    new_memory = f"{current_memory}\n{content}"
                else:
                    new_memory = content
            elif action == "remove" and content:
                new_memory = current_memory.replace(content, "").strip()
                while "\n\n\n" in new_memory:
                    new_memory = new_memory.replace("\n\n\n", "\n\n")
            elif action == "replace" and content:
                new_memory = content
            else:
                new_memory = None
        else:
            new_memory = None

        if new_memory is not None:
            if memory_setting:
                memory_setting.value = new_memory
            else:
                db.add(Settings(key="llm_memory", value=new_memory))

    # Process scheduled follow-up if provided
    followup = analysis.get("schedule_followup")
    if followup and isinstance(followup, dict) and followup.get("topic"):
        tz = pytz.timezone("America/Phoenix")  # TODO: use settings timezone
        now = datetime.now(tz)
        when_str = followup.get("when", "tomorrow").lower()

        scheduled_time = (now + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)

        if "tomorrow" in when_str and "morning" not in when_str and "evening" not in when_str:
            scheduled_time = (now + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
        elif "tonight" in when_str or "this evening" in when_str:
            scheduled_time = now.replace(hour=19, minute=0, second=0, microsecond=0)
            if scheduled_time <= now:
                scheduled_time += timedelta(days=1)

        scheduled_time_utc = scheduled_time.astimezone(pytz.UTC).replace(tzinfo=None)

        db.add(ScheduledFollowup(
            topic=followup["topic"],
            reason=followup.get("reason"),
            scheduled_time=scheduled_time_utc,
        ))

    # Process mood assessment if provided
    mood = analysis.get("mood_assessment")
    if mood and isinstance(mood, dict):
        mood_score = mood.get("mood_score")
        energy_level = mood.get("energy_level")
        if mood_score or energy_level:
            db.add(MoodLog(
                mood_score=mood_score,
                energy_level=energy_level,
                detected_from="llm_analysis",
                notes=mood.get("notes"),
            ))

    # Create response record
    response = Response(
        check_in_id=checkin.id if checkin else None,
        message_text=message_text,
        telegram_message_id=None,  # No Telegram for dashboard
        received_at=datetime.utcnow(),
        detected_shipped=analysis.get("shipped"),
        detected_excuse=analysis.get("excuse"),
        detected_avoidance=analysis.get("avoidance"),
        analysis_notes=analysis.get("notes"),
    )
    db.add(response)

    # Mark check-in as responded if we found one
    if checkin:
        checkin.response_received = True
        checkin.responded_at = datetime.utcnow()

    # Get reply from analysis
    reply = analysis.get("reply")
    if not reply:
        reply = "Got it. What's next on the list?"

    # Save warden reply to chat history
    warden_chat_msg = ChatMessage(
        user_id=user.id,
        role="warden",
        content=reply,
        message_type="reply",
        telegram_message_id=None,
    )
    db.add(warden_chat_msg)
    await db.flush()

    await db.commit()

    return SendChatResponse(
        reply=reply,
        user_message_id=user_message_id,
        warden_message_id=warden_chat_msg.id,
    )
