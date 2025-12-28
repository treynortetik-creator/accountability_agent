"""Settings API router."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from app.database import get_db
from app.auth import verify_api_key
from app.db_models import Settings, ChatMessage
from app.llm import WARDEN_SYSTEM_PROMPT

router = APIRouter(prefix="/settings", tags=["settings"])

# Available OpenRouter models
AVAILABLE_MODELS = [
    {"id": "google/gemini-flash-1.5", "name": "Gemini Flash 1.5", "provider": "Google", "cost": "$"},
    {"id": "google/gemini-pro-1.5", "name": "Gemini Pro 1.5", "provider": "Google", "cost": "$$"},
    {"id": "openai/gpt-4o-mini", "name": "GPT-4o Mini", "provider": "OpenAI", "cost": "$"},
    {"id": "openai/gpt-4o", "name": "GPT-4o", "provider": "OpenAI", "cost": "$$$"},
    {"id": "anthropic/claude-3-haiku", "name": "Claude 3 Haiku", "provider": "Anthropic", "cost": "$"},
    {"id": "anthropic/claude-3.5-sonnet", "name": "Claude 3.5 Sonnet", "provider": "Anthropic", "cost": "$$"},
    {"id": "meta-llama/llama-3.1-70b-instruct", "name": "Llama 3.1 70B", "provider": "Meta", "cost": "$"},
    {"id": "mistralai/mistral-large", "name": "Mistral Large", "provider": "Mistral", "cost": "$$"},
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
    """List available LLM models."""
    return AVAILABLE_MODELS


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
    valid_models = [m["id"] for m in AVAILABLE_MODELS]
    if update.value not in valid_models:
        raise HTTPException(status_code=400, detail=f"Invalid model. Choose from: {valid_models}")

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
