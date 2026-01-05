"""Error log API router."""

import logging
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel
from app.database import get_db
from app.auth import verify_api_key
from app.db_models import ErrorLog

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/errors", tags=["errors"])


class ErrorLogResponse(BaseModel):
    id: int
    error_type: str
    error_message: str
    stack_trace: Optional[str]
    context: Optional[str]
    source: Optional[str]
    user_message: Optional[str]
    resolved: bool
    resolved_at: Optional[str]
    created_at: str

    model_config = {"from_attributes": True}


class ErrorLogSummary(BaseModel):
    id: int
    error_type: str
    error_message: str
    source: Optional[str]
    resolved: bool
    created_at: str

    model_config = {"from_attributes": True}


class ErrorStats(BaseModel):
    total_errors: int
    unresolved_count: int
    resolved_count: int
    errors_last_24h: int
    most_common_type: Optional[str]


@router.get("", response_model=List[ErrorLogSummary])
async def list_errors(
    limit: int = 50,
    unresolved_only: bool = False,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """List error logs, most recent first."""
    query = select(ErrorLog).order_by(desc(ErrorLog.created_at)).limit(limit)

    if unresolved_only:
        query = query.where(ErrorLog.resolved == False)

    result = await db.execute(query)
    errors = result.scalars().all()

    return [
        ErrorLogSummary(
            id=e.id,
            error_type=e.error_type,
            error_message=e.error_message[:200] + "..." if len(e.error_message) > 200 else e.error_message,
            source=e.source,
            resolved=e.resolved,
            created_at=e.created_at.isoformat(),
        )
        for e in errors
    ]


@router.get("/stats", response_model=ErrorStats)
async def get_error_stats(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Get error statistics."""
    from sqlalchemy import func
    from datetime import timedelta

    # Total count
    total_result = await db.execute(select(func.count(ErrorLog.id)))
    total = total_result.scalar() or 0

    # Unresolved count
    unresolved_result = await db.execute(
        select(func.count(ErrorLog.id)).where(ErrorLog.resolved == False)
    )
    unresolved = unresolved_result.scalar() or 0

    # Last 24 hours
    yesterday = datetime.utcnow() - timedelta(hours=24)
    recent_result = await db.execute(
        select(func.count(ErrorLog.id)).where(ErrorLog.created_at >= yesterday)
    )
    recent = recent_result.scalar() or 0

    # Most common error type
    type_result = await db.execute(
        select(ErrorLog.error_type, func.count(ErrorLog.id).label('count'))
        .group_by(ErrorLog.error_type)
        .order_by(desc('count'))
        .limit(1)
    )
    type_row = type_result.first()
    most_common = type_row[0] if type_row else None

    return ErrorStats(
        total_errors=total,
        unresolved_count=unresolved,
        resolved_count=total - unresolved,
        errors_last_24h=recent,
        most_common_type=most_common,
    )


@router.get("/{error_id}", response_model=ErrorLogResponse)
async def get_error(
    error_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Get a specific error log with full details."""
    result = await db.execute(
        select(ErrorLog).where(ErrorLog.id == error_id)
    )
    error = result.scalar_one_or_none()

    if not error:
        raise HTTPException(status_code=404, detail="Error not found")

    return ErrorLogResponse(
        id=error.id,
        error_type=error.error_type,
        error_message=error.error_message,
        stack_trace=error.stack_trace,
        context=error.context,
        source=error.source,
        user_message=error.user_message,
        resolved=error.resolved,
        resolved_at=error.resolved_at.isoformat() if error.resolved_at else None,
        created_at=error.created_at.isoformat(),
    )


@router.post("/{error_id}/resolve")
async def resolve_error(
    error_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Mark an error as resolved."""
    result = await db.execute(
        select(ErrorLog).where(ErrorLog.id == error_id)
    )
    error = result.scalar_one_or_none()

    if not error:
        raise HTTPException(status_code=404, detail="Error not found")

    error.resolved = True
    error.resolved_at = datetime.utcnow()
    await db.commit()

    return {"status": "resolved", "id": error_id}


@router.post("/resolve-all")
async def resolve_all_errors(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Mark all unresolved errors as resolved."""
    from sqlalchemy import update

    result = await db.execute(
        update(ErrorLog)
        .where(ErrorLog.resolved == False)
        .values(resolved=True, resolved_at=datetime.utcnow())
    )
    await db.commit()

    return {"status": "resolved", "count": result.rowcount}


@router.delete("/{error_id}")
async def delete_error(
    error_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Delete an error log."""
    result = await db.execute(
        select(ErrorLog).where(ErrorLog.id == error_id)
    )
    error = result.scalar_one_or_none()

    if not error:
        raise HTTPException(status_code=404, detail="Error not found")

    await db.delete(error)
    await db.commit()

    return {"status": "deleted", "id": error_id}


@router.delete("")
async def clear_resolved_errors(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Delete all resolved error logs."""
    from sqlalchemy import delete

    result = await db.execute(
        delete(ErrorLog).where(ErrorLog.resolved == True)
    )
    await db.commit()

    return {"status": "cleared", "count": result.rowcount}
