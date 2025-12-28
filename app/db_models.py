"""SQLAlchemy database models for The Warden."""

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Boolean,
    ForeignKey,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship, declarative_base
import enum

Base = declarative_base()


class CommitmentStatus(enum.Enum):
    """Status of a commitment."""

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    DEFERRED = "deferred"


class CheckInType(enum.Enum):
    """Type of check-in message."""

    DAILY = "daily"
    WEEKLY_REVIEW = "weekly_review"
    ESCALATION = "escalation"
    DEADLINE_ALERT = "deadline_alert"
    MANUAL = "manual"


class Goal(Base):
    """Long-term goals being worked toward."""

    __tablename__ = "goals"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    target_date = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    commitments = relationship("Commitment", back_populates="goal")


class Commitment(Base):
    """Specific commitments/tasks tied to goals."""

    __tablename__ = "commitments"

    id = Column(Integer, primary_key=True, index=True)
    goal_id = Column(Integer, ForeignKey("goals.id"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(DateTime, nullable=True)
    status = Column(
        SQLEnum(CommitmentStatus), default=CommitmentStatus.PENDING, nullable=False
    )
    completed_at = Column(DateTime, nullable=True)
    deferred_count = Column(Integer, default=0)  # Track how many times deferred
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    goal = relationship("Goal", back_populates="commitments")


class CheckIn(Base):
    """Check-in messages sent by The Warden."""

    __tablename__ = "checkins"

    id = Column(Integer, primary_key=True, index=True)
    check_in_type = Column(SQLEnum(CheckInType), nullable=False)
    message_sent = Column(Text, nullable=False)  # What The Warden said
    telegram_message_id = Column(String(100), nullable=True)
    sent_at = Column(DateTime, default=datetime.utcnow)
    response_received = Column(Boolean, default=False)
    responded_at = Column(DateTime, nullable=True)

    # Relationships
    responses = relationship("Response", back_populates="check_in")


class Response(Base):
    """User responses to check-ins."""

    __tablename__ = "responses"

    id = Column(Integer, primary_key=True, index=True)
    check_in_id = Column(Integer, ForeignKey("checkins.id"), nullable=True)
    message_text = Column(Text, nullable=False)
    telegram_message_id = Column(String(100), nullable=True)
    received_at = Column(DateTime, default=datetime.utcnow)

    # LLM analysis of the response
    detected_shipped = Column(Boolean, nullable=True)  # Did they ship something?
    detected_excuse = Column(Boolean, nullable=True)  # Is this an excuse?
    detected_avoidance = Column(Boolean, nullable=True)  # Signs of avoidance?
    analysis_notes = Column(Text, nullable=True)  # LLM's notes

    # Relationships
    check_in = relationship("CheckIn", back_populates="responses")


class Pattern(Base):
    """Detected behavioral patterns over time."""

    __tablename__ = "patterns"

    id = Column(Integer, primary_key=True, index=True)
    pattern_type = Column(
        String(50), nullable=False
    )  # avoidance, silence, excuse, consistency
    description = Column(Text, nullable=False)
    evidence = Column(Text, nullable=True)  # JSON of supporting data
    severity = Column(Integer, default=1)  # 1-5 scale
    detected_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)  # Still relevant?


class ScheduleConfig(Base):
    """Configurable schedule settings."""

    __tablename__ = "schedule_config"

    id = Column(Integer, primary_key=True, index=True)
    config_key = Column(String(50), unique=True, nullable=False)
    config_value = Column(String(255), nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Settings(Base):
    """Application settings stored in database."""

    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ChatMessage(Base):
    """Chat messages for conversation history."""

    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    role = Column(String(20), nullable=False)  # 'warden' or 'user'
    content = Column(Text, nullable=False)
    message_type = Column(String(50), nullable=True)  # check-in type or 'reply'
    telegram_message_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class CalendarEvent(Base):
    """Cached calendar events from Google Calendar."""

    __tablename__ = "calendar_events"

    id = Column(Integer, primary_key=True, index=True)
    google_event_id = Column(String(255), unique=True, nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    all_day = Column(Boolean, default=False)
    location = Column(String(500), nullable=True)
    last_synced = Column(DateTime, default=datetime.utcnow)
