"""Settings API router."""

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
from app.db_models import Settings, ChatMessage
from app.llm import WARDEN_SYSTEM_PROMPT

router = APIRouter(prefix="/settings", tags=["settings"])

# Cache for OpenRouter models
_models_cache = {
    "models": [],
    "last_fetch": None,
    "cache_duration": timedelta(hours=1)
}


async def fetch_openrouter_models() -> List[dict]:
    """Fetch all available models from OpenRouter API."""
    global _models_cache

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
    import json

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
