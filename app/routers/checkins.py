"""Check-ins and responses API router."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.auth import verify_api_key
from app.db_models import CheckIn, Response, Commitment, CommitmentStatus, Pattern
from app.models import (
    CheckInResponse,
    UserResponseResponse,
    PatternResponse,
    StatsResponse,
    ScheduleConfigResponse,
    ScheduleConfigUpdate,
)
from app.config import get_settings

router = APIRouter(prefix="/checkins", tags=["checkins"])
settings = get_settings()


@router.get("", response_model=List[CheckInResponse])
async def list_checkins(
    limit: int = Query(default=20, le=100),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """List recent check-ins."""
    query = select(CheckIn).order_by(CheckIn.sent_at.desc()).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/responses", response_model=List[UserResponseResponse])
async def list_responses(
    limit: int = Query(default=20, le=100),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """List recent responses."""
    query = select(Response).order_by(Response.received_at.desc()).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/patterns", response_model=List[PatternResponse])
async def list_patterns(
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """List detected patterns."""
    query = select(Pattern)
    if active_only:
        query = query.where(Pattern.is_active == True)
    query = query.order_by(Pattern.detected_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Get accountability statistics."""
    # Commitment stats
    total_result = await db.execute(select(func.count(Commitment.id)))
    total_commitments = total_result.scalar() or 0

    completed_result = await db.execute(
        select(func.count(Commitment.id)).where(
            Commitment.status == CommitmentStatus.COMPLETED
        )
    )
    completed_commitments = completed_result.scalar() or 0

    failed_result = await db.execute(
        select(func.count(Commitment.id)).where(
            Commitment.status == CommitmentStatus.FAILED
        )
    )
    failed_commitments = failed_result.scalar() or 0

    pending_result = await db.execute(
        select(func.count(Commitment.id)).where(
            Commitment.status == CommitmentStatus.PENDING
        )
    )
    pending_commitments = pending_result.scalar() or 0

    completion_rate = (
        completed_commitments / total_commitments if total_commitments > 0 else 0.0
    )

    # Check-in stats
    checkin_result = await db.execute(select(func.count(CheckIn.id)))
    total_checkins = checkin_result.scalar() or 0

    responded_result = await db.execute(
        select(func.count(CheckIn.id)).where(CheckIn.response_received == True)
    )
    responded_checkins = responded_result.scalar() or 0

    response_rate = responded_checkins / total_checkins if total_checkins > 0 else 0.0

    # Calculate average response time
    avg_response_time = None
    checkins_with_response = await db.execute(
        select(CheckIn).where(
            CheckIn.response_received == True, CheckIn.responded_at.isnot(None)
        )
    )
    checkins_list = checkins_with_response.scalars().all()
    if checkins_list:
        total_hours = sum(
            (c.responded_at - c.sent_at).total_seconds() / 3600
            for c in checkins_list
            if c.responded_at and c.sent_at
        )
        avg_response_time = total_hours / len(checkins_list)

    # Active patterns
    patterns_result = await db.execute(
        select(Pattern).where(Pattern.is_active == True)
    )
    active_patterns = [
        PatternResponse.model_validate(p) for p in patterns_result.scalars().all()
    ]

    return StatsResponse(
        total_commitments=total_commitments,
        completed_commitments=completed_commitments,
        failed_commitments=failed_commitments,
        pending_commitments=pending_commitments,
        completion_rate=completion_rate,
        total_checkins=total_checkins,
        response_rate=response_rate,
        average_response_time_hours=avg_response_time,
        active_patterns=active_patterns,
    )


@router.get("/schedule", response_model=ScheduleConfigResponse)
async def get_schedule(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Get current schedule configuration."""
    from app.db_models import Settings as SettingsModel
    import json

    # Try to get from database first
    result = await db.execute(
        select(SettingsModel).where(SettingsModel.key == "schedule_config")
    )
    schedule_setting = result.scalar_one_or_none()

    if schedule_setting:
        config = json.loads(schedule_setting.value)
        return ScheduleConfigResponse(
            daily_checkin_hour=config.get("daily_checkin_hour", settings.daily_checkin_hour),
            daily_checkin_minute=config.get("daily_checkin_minute", settings.daily_checkin_minute),
            weekly_review_day=config.get("weekly_review_day", settings.weekly_review_day),
            weekly_review_hour=config.get("weekly_review_hour", settings.weekly_review_hour),
            weekly_review_minute=config.get("weekly_review_minute", settings.weekly_review_minute),
        )

    # Fall back to env vars
    return ScheduleConfigResponse(
        daily_checkin_hour=settings.daily_checkin_hour,
        daily_checkin_minute=settings.daily_checkin_minute,
        weekly_review_day=settings.weekly_review_day,
        weekly_review_hour=settings.weekly_review_hour,
        weekly_review_minute=settings.weekly_review_minute,
    )


@router.put("/schedule", response_model=ScheduleConfigResponse)
async def update_schedule(
    schedule_update: ScheduleConfigUpdate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Update schedule configuration and restart scheduler jobs."""
    from app.db_models import Settings as SettingsModel
    from app.scheduler import reschedule_jobs
    import json

    # Get current config
    result = await db.execute(
        select(SettingsModel).where(SettingsModel.key == "schedule_config")
    )
    schedule_setting = result.scalar_one_or_none()

    if schedule_setting:
        current_config = json.loads(schedule_setting.value)
    else:
        current_config = {
            "daily_checkin_hour": settings.daily_checkin_hour,
            "daily_checkin_minute": settings.daily_checkin_minute,
            "weekly_review_day": settings.weekly_review_day,
            "weekly_review_hour": settings.weekly_review_hour,
            "weekly_review_minute": settings.weekly_review_minute,
        }

    # Update with provided values
    update_data = schedule_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            current_config[key] = value

    # Save to database
    if schedule_setting:
        schedule_setting.value = json.dumps(current_config)
    else:
        new_setting = SettingsModel(key="schedule_config", value=json.dumps(current_config))
        db.add(new_setting)

    await db.flush()

    # Reschedule jobs with new times
    await reschedule_jobs(current_config)

    return ScheduleConfigResponse(**current_config)
