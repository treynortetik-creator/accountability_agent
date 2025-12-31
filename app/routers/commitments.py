"""Commitments API router."""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.auth import verify_api_key
from app.db_models import Commitment, CommitmentStatus
from app.models import CommitmentCreate, CommitmentUpdate, CommitmentResponse
from app.user_service import get_default_user

router = APIRouter(prefix="/commitments", tags=["commitments"])


@router.get("", response_model=List[CommitmentResponse])
async def list_commitments(
    status_filter: Optional[CommitmentStatus] = None,
    goal_id: Optional[int] = None,
    limit: int = Query(default=50, le=200),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """List commitments with optional filters."""
    user = await get_default_user(db)

    query = select(Commitment).where(Commitment.user_id == user.id)

    if status_filter:
        query = query.where(Commitment.status == status_filter)
    if goal_id:
        query = query.where(Commitment.goal_id == goal_id)

    query = query.order_by(Commitment.created_at.desc()).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=CommitmentResponse, status_code=status.HTTP_201_CREATED)
async def create_commitment(
    commitment: CommitmentCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Create a new commitment."""
    user = await get_default_user(db)

    db_commitment = Commitment(user_id=user.id, **commitment.model_dump())
    db.add(db_commitment)
    await db.flush()
    await db.refresh(db_commitment)
    return db_commitment


@router.get("/{commitment_id}", response_model=CommitmentResponse)
async def get_commitment(
    commitment_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Get a specific commitment."""
    user = await get_default_user(db)

    result = await db.execute(
        select(Commitment).where(
            Commitment.id == commitment_id,
            Commitment.user_id == user.id
        )
    )
    commitment = result.scalar_one_or_none()
    if not commitment:
        raise HTTPException(status_code=404, detail="Commitment not found")
    return commitment


@router.patch("/{commitment_id}", response_model=CommitmentResponse)
@router.put("/{commitment_id}", response_model=CommitmentResponse)
async def update_commitment(
    commitment_id: int,
    commitment_update: CommitmentUpdate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Update a commitment."""
    user = await get_default_user(db)

    result = await db.execute(
        select(Commitment).where(
            Commitment.id == commitment_id,
            Commitment.user_id == user.id
        )
    )
    commitment = result.scalar_one_or_none()
    if not commitment:
        raise HTTPException(status_code=404, detail="Commitment not found")

    update_data = commitment_update.model_dump(exclude_unset=True)

    # Handle status changes
    if "status" in update_data:
        new_status = update_data["status"]
        if new_status == CommitmentStatus.COMPLETED:
            commitment.completed_at = datetime.utcnow()
        elif new_status == CommitmentStatus.DEFERRED:
            commitment.deferred_count += 1

    for field, value in update_data.items():
        setattr(commitment, field, value)

    await db.flush()
    await db.refresh(commitment)
    return commitment


@router.post("/{commitment_id}/complete", response_model=CommitmentResponse)
async def complete_commitment(
    commitment_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Mark a commitment as completed."""
    user = await get_default_user(db)

    result = await db.execute(
        select(Commitment).where(
            Commitment.id == commitment_id,
            Commitment.user_id == user.id
        )
    )
    commitment = result.scalar_one_or_none()
    if not commitment:
        raise HTTPException(status_code=404, detail="Commitment not found")

    commitment.status = CommitmentStatus.COMPLETED
    commitment.completed_at = datetime.utcnow()

    await db.flush()
    await db.refresh(commitment)
    return commitment


@router.post("/{commitment_id}/fail", response_model=CommitmentResponse)
async def fail_commitment(
    commitment_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Mark a commitment as failed."""
    user = await get_default_user(db)

    result = await db.execute(
        select(Commitment).where(
            Commitment.id == commitment_id,
            Commitment.user_id == user.id
        )
    )
    commitment = result.scalar_one_or_none()
    if not commitment:
        raise HTTPException(status_code=404, detail="Commitment not found")

    commitment.status = CommitmentStatus.FAILED

    await db.flush()
    await db.refresh(commitment)
    return commitment


@router.post("/{commitment_id}/defer", response_model=CommitmentResponse)
async def defer_commitment(
    commitment_id: int,
    new_due_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Defer a commitment (tracks deferral count)."""
    user = await get_default_user(db)

    result = await db.execute(
        select(Commitment).where(
            Commitment.id == commitment_id,
            Commitment.user_id == user.id
        )
    )
    commitment = result.scalar_one_or_none()
    if not commitment:
        raise HTTPException(status_code=404, detail="Commitment not found")

    commitment.status = CommitmentStatus.DEFERRED
    commitment.deferred_count += 1
    if new_due_date:
        commitment.due_date = new_due_date

    await db.flush()
    await db.refresh(commitment)
    return commitment


@router.delete("/{commitment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_commitment(
    commitment_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Delete a commitment."""
    user = await get_default_user(db)

    result = await db.execute(
        select(Commitment).where(
            Commitment.id == commitment_id,
            Commitment.user_id == user.id
        )
    )
    commitment = result.scalar_one_or_none()
    if not commitment:
        raise HTTPException(status_code=404, detail="Commitment not found")

    await db.delete(commitment)
