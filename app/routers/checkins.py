"""Check-ins and responses API router."""

from typing import List
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
)
from app.config import get_settings
from app.user_service import get_default_user

router = APIRouter(prefix="/checkins", tags=["checkins"])
settings = get_settings()


@router.get("", response_model=List[CheckInResponse])
async def list_checkins(
    limit: int = Query(default=20, le=100),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """List recent check-ins."""
    user = await get_default_user(db)

    query = (
        select(CheckIn)
        .where(CheckIn.user_id == user.id)
        .order_by(CheckIn.sent_at.desc())
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/responses", response_model=List[UserResponseResponse])
async def list_responses(
    limit: int = Query(default=20, le=100),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """List recent responses."""
    user = await get_default_user(db)

    query = (
        select(Response)
        .where(Response.user_id == user.id)
        .order_by(Response.received_at.desc())
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/patterns", response_model=List[PatternResponse])
async def list_patterns(
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """List detected patterns."""
    user = await get_default_user(db)

    query = select(Pattern).where(Pattern.user_id == user.id)
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
    user = await get_default_user(db)

    # Commitment stats
    total_result = await db.execute(
        select(func.count(Commitment.id)).where(Commitment.user_id == user.id)
    )
    total_commitments = total_result.scalar() or 0

    completed_result = await db.execute(
        select(func.count(Commitment.id)).where(
            Commitment.user_id == user.id,
            Commitment.status == CommitmentStatus.COMPLETED
        )
    )
    completed_commitments = completed_result.scalar() or 0

    failed_result = await db.execute(
        select(func.count(Commitment.id)).where(
            Commitment.user_id == user.id,
            Commitment.status == CommitmentStatus.FAILED
        )
    )
    failed_commitments = failed_result.scalar() or 0

    pending_result = await db.execute(
        select(func.count(Commitment.id)).where(
            Commitment.user_id == user.id,
            Commitment.status == CommitmentStatus.PENDING
        )
    )
    pending_commitments = pending_result.scalar() or 0

    completion_rate = (
        completed_commitments / total_commitments if total_commitments > 0 else 0.0
    )

    # Check-in stats
    checkin_result = await db.execute(
        select(func.count(CheckIn.id)).where(CheckIn.user_id == user.id)
    )
    total_checkins = checkin_result.scalar() or 0

    responded_result = await db.execute(
        select(func.count(CheckIn.id)).where(
            CheckIn.user_id == user.id,
            CheckIn.response_received == True
        )
    )
    responded_checkins = responded_result.scalar() or 0

    response_rate = responded_checkins / total_checkins if total_checkins > 0 else 0.0

    # Calculate average response time
    avg_response_time = None
    checkins_with_response = await db.execute(
        select(CheckIn).where(
            CheckIn.user_id == user.id,
            CheckIn.response_received == True,
            CheckIn.responded_at.isnot(None)
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
        select(Pattern).where(
            Pattern.user_id == user.id,
            Pattern.is_active == True
        )
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
