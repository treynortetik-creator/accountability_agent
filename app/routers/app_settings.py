"""Settings API router."""

import httpx
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
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
    calendar = await get_setting(db, "google_calendar_token", "")

    return SettingsResponse(
        openrouter_model=model,
        system_prompt=prompt,
        google_calendar_connected=bool(calendar),
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
    result = await db.execute(
        select(ChatMessage)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
    )
    messages = result.scalars().all()
    return [
        ChatMessageResponse(
            id=m.id,
            role=m.role,
            content=m.content,
            message_type=m.message_type,
            created_at=m.created_at.isoformat(),
        )
        for m in reversed(messages)  # Return in chronological order
    ]
