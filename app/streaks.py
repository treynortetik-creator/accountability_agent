"""Streak tracking for The Warden."""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_models import Streak, CheckIn, Commitment, CommitmentStatus

logger = logging.getLogger(__name__)


async def get_or_create_streak(db: AsyncSession, streak_type: str) -> Streak:
    """Get or create a streak record."""
    result = await db.execute(
        select(Streak).where(Streak.streak_type == streak_type)
    )
    streak = result.scalar_one_or_none()

    if not streak:
        streak = Streak(
            streak_type=streak_type,
            current_count=0,
            best_count=0,
        )
        db.add(streak)
        await db.flush()

    return streak


async def update_response_streak(db: AsyncSession) -> Dict[str, Any]:
    """Update the response streak when user responds to a check-in.

    Call this when user responds to any check-in.
    Returns the updated streak info.
    """
    streak = await get_or_create_streak(db, "response")
    today = datetime.utcnow().date()

    if streak.last_activity_date:
        last_date = streak.last_activity_date.date()
        days_since = (today - last_date).days

        if days_since == 0:
            # Already responded today, no change
            pass
        elif days_since == 1:
            # Consecutive day - increment streak
            streak.current_count += 1
        else:
            # Streak broken - reset
            streak.current_count = 1
    else:
        # First response ever
        streak.current_count = 1

    # Update best if current is higher
    if streak.current_count > streak.best_count:
        streak.best_count = streak.current_count

    streak.last_activity_date = datetime.utcnow()
    streak.last_updated = datetime.utcnow()
    await db.flush()

    return {
        "type": "response",
        "current": streak.current_count,
        "best": streak.best_count,
    }


async def check_response_streak_broken(db: AsyncSession) -> bool:
    """Check if the response streak was broken (missed a day).

    Returns True if streak was broken since last check.
    """
    streak = await get_or_create_streak(db, "response")

    if not streak.last_activity_date:
        return False

    today = datetime.utcnow().date()
    last_date = streak.last_activity_date.date()
    days_since = (today - last_date).days

    # If more than 1 day since last response, streak is broken
    if days_since > 1 and streak.current_count > 0:
        old_count = streak.current_count
        streak.current_count = 0
        streak.last_updated = datetime.utcnow()
        await db.flush()
        logger.info(f"Response streak broken. Was {old_count} days.")
        return True

    return False


async def update_completion_streak(db: AsyncSession) -> Dict[str, Any]:
    """Update the weekly completion streak.

    Call this during weekly review to check if >80% was completed.
    Returns the updated streak info.
    """
    streak = await get_or_create_streak(db, "completion")

    # Calculate this week's completion rate
    week_ago = datetime.utcnow() - timedelta(days=7)

    # Count commitments created or due this week
    total_result = await db.execute(
        select(func.count(Commitment.id)).where(
            Commitment.created_at > week_ago
        )
    )
    total = total_result.scalar() or 0

    # Count completed this week
    completed_result = await db.execute(
        select(func.count(Commitment.id)).where(
            and_(
                Commitment.status == CommitmentStatus.COMPLETED,
                Commitment.completed_at > week_ago,
            )
        )
    )
    completed = completed_result.scalar() or 0

    # Calculate rate
    rate = (completed / total * 100) if total > 0 else 0

    # Check if this is a new week
    now = datetime.utcnow()
    is_new_week = True
    if streak.last_week_end:
        days_since_last = (now - streak.last_week_end).days
        is_new_week = days_since_last >= 7

    if is_new_week:
        if rate >= 80:
            # Met the goal - increment streak
            streak.current_count += 1
        else:
            # Didn't meet goal - reset streak
            streak.current_count = 0

        # Update best if current is higher
        if streak.current_count > streak.best_count:
            streak.best_count = streak.current_count

        streak.last_week_end = now
        streak.last_updated = now
        await db.flush()

    return {
        "type": "completion",
        "current": streak.current_count,
        "best": streak.best_count,
        "this_week_rate": round(rate, 1),
        "met_goal": rate >= 80,
    }


async def get_streak_context(db: AsyncSession) -> Dict[str, Any]:
    """Get streak context for LLM prompts and dashboard."""
    response_streak = await get_or_create_streak(db, "response")
    completion_streak = await get_or_create_streak(db, "completion")

    # Calculate current week's completion rate
    week_ago = datetime.utcnow() - timedelta(days=7)

    total_result = await db.execute(
        select(func.count(Commitment.id)).where(
            Commitment.created_at > week_ago
        )
    )
    total = total_result.scalar() or 0

    completed_result = await db.execute(
        select(func.count(Commitment.id)).where(
            and_(
                Commitment.status == CommitmentStatus.COMPLETED,
                Commitment.completed_at > week_ago,
            )
        )
    )
    completed = completed_result.scalar() or 0

    current_week_rate = (completed / total * 100) if total > 0 else 0

    return {
        "response_streak": {
            "current": response_streak.current_count,
            "best": response_streak.best_count,
        },
        "completion_streak": {
            "current": completion_streak.current_count,
            "best": completion_streak.best_count,
        },
        "current_week_completion_rate": round(current_week_rate, 1),
        "needs_for_streak": max(0, 80 - current_week_rate),  # How much more to maintain streak
    }


async def get_streak_message(db: AsyncSession) -> Optional[str]:
    """Generate a streak-related message snippet for The Warden to use.

    Returns a message snippet or None if nothing noteworthy.
    """
    context = await get_streak_context(db)

    messages = []

    # Response streak messages
    response_current = context["response_streak"]["current"]
    if response_current >= 7:
        messages.append(f"{response_current} day response streak - don't break it.")
    elif response_current >= 3:
        messages.append(f"{response_current} days responding in a row. Keep it up.")

    # Completion streak messages
    completion_current = context["completion_streak"]["current"]
    current_rate = context["current_week_completion_rate"]

    if completion_current > 0:
        if current_rate < 80:
            needed = context["needs_for_streak"]
            messages.append(f"You're at {current_rate:.0f}% this week. {needed:.0f}% more to keep your {completion_current}-week streak.")
        else:
            messages.append(f"On track for week {completion_current + 1} of your completion streak.")
    elif current_rate >= 80:
        messages.append("You could start a new completion streak this week.")

    return " ".join(messages) if messages else None
