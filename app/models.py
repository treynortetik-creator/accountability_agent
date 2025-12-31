"""Pydantic models for API request/response validation."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from app.db_models import CommitmentStatus, CheckInType


# ============ Goal Models ============


class GoalCreate(BaseModel):
    """Create a new goal."""

    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    target_date: Optional[datetime] = None


class GoalUpdate(BaseModel):
    """Update an existing goal."""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    target_date: Optional[datetime] = None
    is_active: Optional[bool] = None


class GoalResponse(BaseModel):
    """Goal response model."""

    id: int
    title: str
    description: Optional[str]
    target_date: Optional[datetime]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============ Commitment Models ============


class CommitmentCreate(BaseModel):
    """Create a new commitment."""

    goal_id: Optional[int] = None
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    due_date: Optional[datetime] = None


class CommitmentUpdate(BaseModel):
    """Update an existing commitment."""

    goal_id: Optional[int] = None
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    status: Optional[CommitmentStatus] = None


class CommitmentResponse(BaseModel):
    """Commitment response model."""

    id: int
    goal_id: Optional[int]
    title: str
    description: Optional[str]
    due_date: Optional[datetime]
    status: CommitmentStatus
    completed_at: Optional[datetime]
    deferred_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============ Check-In Models ============


class CheckInResponse(BaseModel):
    """Check-in response model."""

    id: int
    check_in_type: CheckInType
    message_sent: str
    sent_at: datetime
    response_received: bool
    responded_at: Optional[datetime]

    class Config:
        from_attributes = True


# ============ Response Models ============


class UserResponseCreate(BaseModel):
    """Create a user response (from Telegram)."""

    message_text: str
    telegram_message_id: Optional[str] = None


class UserResponseResponse(BaseModel):
    """User response model."""

    id: int
    check_in_id: Optional[int]
    message_text: str
    received_at: datetime
    detected_shipped: Optional[bool]
    detected_excuse: Optional[bool]
    detected_avoidance: Optional[bool]
    analysis_notes: Optional[str]

    class Config:
        from_attributes = True


# ============ Pattern Models ============


class PatternResponse(BaseModel):
    """Pattern response model."""

    id: int
    pattern_type: str
    description: str
    evidence: Optional[str]
    severity: int
    detected_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


# ============ Stats Models ============


class StatsResponse(BaseModel):
    """Statistics response model."""

    total_commitments: int
    completed_commitments: int
    failed_commitments: int
    pending_commitments: int
    completion_rate: float
    total_checkins: int
    response_rate: float
    average_response_time_hours: Optional[float]
    active_patterns: List[PatternResponse]


# ============ Manual Check-In Models ============


class ManualCheckInRequest(BaseModel):
    """Trigger a manual check-in."""

    message: Optional[str] = None  # Optional custom message
