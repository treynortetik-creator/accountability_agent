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
    WEEKLY_PLANNING = "weekly_planning"
    ESCALATION = "escalation"
    DEADLINE_ALERT = "deadline_alert"
    DEADLINE_REMINDER = "deadline_reminder"  # 90-min reminder
    MANUAL = "manual"
    COMMITMENT_CONFIRM = "commitment_confirm"


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
    is_ooo = Column(Boolean, default=False)  # Out of office/vacation
    last_synced = Column(DateTime, default=datetime.utcnow)


class Streak(Base):
    """Track user streaks for gamification."""

    __tablename__ = "streaks"

    id = Column(Integer, primary_key=True, index=True)
    streak_type = Column(String(50), nullable=False)  # 'response' or 'completion'
    current_count = Column(Integer, default=0)
    best_count = Column(Integer, default=0)
    last_updated = Column(DateTime, default=datetime.utcnow)
    last_activity_date = Column(DateTime, nullable=True)  # For daily response streak
    last_week_end = Column(DateTime, nullable=True)  # For weekly completion streak


class PendingCommitmentParse(Base):
    """Temporary storage for commitments parsed from natural language awaiting confirmation."""

    __tablename__ = "pending_commitment_parses"

    id = Column(Integer, primary_key=True, index=True)
    original_message = Column(Text, nullable=False)
    parsed_title = Column(String(255), nullable=False)
    parsed_due_date = Column(DateTime, nullable=True)
    parsed_description = Column(Text, nullable=True)
    confirmation_message_id = Column(String(100), nullable=True)
    status = Column(String(20), default="pending")  # pending, confirmed, rejected, breakdown_pending
    suggested_breakdown = Column(Text, nullable=True)  # JSON array of breakdown steps
    is_large = Column(Boolean, default=False)  # Whether this was flagged as a large commitment
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # Auto-expire after some time


class CheckInSchedule(Base):
    """Custom check-in schedules configured by the user."""

    __tablename__ = "checkin_schedules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)  # e.g., "Morning Check-in", "Mid-day Reminder"
    check_in_type = Column(String(50), nullable=False)  # daily_checkin, custom, reminder
    hour = Column(Integer, nullable=False)  # 0-23
    minute = Column(Integer, default=0)  # 0-59
    days_of_week = Column(String(50), nullable=True)  # e.g., "mon,tue,wed,thu,fri" or null for every day
    prompt_template = Column(Text, nullable=True)  # Custom prompt, null means use default
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CheckInPrompt(Base):
    """Customizable prompts for different check-in types."""

    __tablename__ = "checkin_prompts"

    id = Column(Integer, primary_key=True, index=True)
    prompt_type = Column(String(50), unique=True, nullable=False)  # daily_checkin, weekly_review, escalation, etc.
    prompt_template = Column(Text, nullable=False)
    is_custom = Column(Boolean, default=False)  # True if user has customized it
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ScheduledFollowup(Base):
    """Scheduled follow-up messages for specific topics."""

    __tablename__ = "scheduled_followups"

    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String(255), nullable=False)
    reason = Column(Text, nullable=True)
    scheduled_time = Column(DateTime, nullable=False)
    status = Column(String(20), default="pending")  # pending, sent, cancelled
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class MoodLog(Base):
    """Track detected mood and energy levels over time."""

    __tablename__ = "mood_logs"

    id = Column(Integer, primary_key=True, index=True)
    mood_score = Column(Integer, nullable=True)  # 1-10 scale
    energy_level = Column(String(20), nullable=True)  # low, medium, high
    detected_from = Column(String(50), nullable=True)  # llm_analysis, user_input, etc.
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ErrorLog(Base):
    """Track application errors for debugging and monitoring."""

    __tablename__ = "error_logs"

    id = Column(Integer, primary_key=True, index=True)
    error_type = Column(String(100), nullable=False)  # Exception class name
    error_message = Column(Text, nullable=False)
    stack_trace = Column(Text, nullable=True)
    context = Column(Text, nullable=True)  # JSON with additional context
    source = Column(String(100), nullable=True)  # webhook, scheduler, etc.
    user_message = Column(Text, nullable=True)  # The message that triggered the error
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ResponseTiming(Base):
    """Track response timing patterns for personalized thresholds."""

    __tablename__ = "response_timings"

    id = Column(Integer, primary_key=True, index=True)
    check_in_id = Column(Integer, ForeignKey("checkins.id"), nullable=True)
    response_time_minutes = Column(Integer, nullable=True)  # Time to respond in minutes
    did_respond = Column(Boolean, default=False)
    day_of_week = Column(Integer, nullable=True)  # 0=Monday, 6=Sunday
    hour_of_day = Column(Integer, nullable=True)  # 0-23
    created_at = Column(DateTime, default=datetime.utcnow)


class WeeklyInsight(Base):
    """Store weekly insights and metrics summaries."""

    __tablename__ = "weekly_insights"

    id = Column(Integer, primary_key=True, index=True)
    week_start = Column(DateTime, nullable=False)
    week_end = Column(DateTime, nullable=False)
    summary = Column(Text, nullable=True)  # LLM-generated summary
    metrics = Column(Text, nullable=True)  # JSON with metrics data
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
