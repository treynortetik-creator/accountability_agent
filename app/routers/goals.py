"""Goals API router."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.auth import verify_api_key
from app.db_models import Goal
from app.models import GoalCreate, GoalUpdate, GoalResponse
from app.user_service import get_default_user

router = APIRouter(prefix="/goals", tags=["goals"])


@router.get("", response_model=List[GoalResponse])
async def list_goals(
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """List all goals for the current user."""
    user = await get_default_user(db)

    query = select(Goal).where(Goal.user_id == user.id)
    if active_only:
        query = query.where(Goal.is_active == True)
    query = query.order_by(Goal.created_at.desc())

    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
async def create_goal(
    goal: GoalCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Create a new goal."""
    user = await get_default_user(db)

    db_goal = Goal(user_id=user.id, **goal.model_dump())
    db.add(db_goal)
    await db.flush()
    await db.refresh(db_goal)
    return db_goal


@router.get("/{goal_id}", response_model=GoalResponse)
async def get_goal(
    goal_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Get a specific goal."""
    user = await get_default_user(db)

    result = await db.execute(
        select(Goal).where(Goal.id == goal_id, Goal.user_id == user.id)
    )
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    return goal


@router.patch("/{goal_id}", response_model=GoalResponse)
async def update_goal(
    goal_id: int,
    goal_update: GoalUpdate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Update a goal."""
    user = await get_default_user(db)

    result = await db.execute(
        select(Goal).where(Goal.id == goal_id, Goal.user_id == user.id)
    )
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    update_data = goal_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(goal, field, value)

    await db.flush()
    await db.refresh(goal)
    return goal


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_goal(
    goal_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Delete a goal (soft delete - marks as inactive)."""
    user = await get_default_user(db)

    result = await db.execute(
        select(Goal).where(Goal.id == goal_id, Goal.user_id == user.id)
    )
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    goal.is_active = False
    await db.flush()
