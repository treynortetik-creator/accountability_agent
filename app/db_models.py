"""SQLAlchemy database models for The Warden."""

from datetime import datetime
from typing import Optional
import uuid
from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    String,
    Text,
    DateTime,
    Boolean,
    ForeignKey,
    Enum as SQLEnum,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import JSON
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


class User(Base):
    """Users table for multi-tenant support."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    telegram_chat_id = Column(Text, unique=True, nullable=False)
    display_name = Column(Text, nullable=True)
    timezone = Column(Text, default="America/Phoenix")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    goals = relationship("Goal", back_populates="user", cascade="all, delete-orphan")
    commitments = relationship("Commitment", back_populates="user", cascade="all, delete-orphan")
    checkins = relationship("CheckIn", back_populates="user", cascade="all, delete-orphan")
    responses = relationship("Response", back_populates="user", cascade="all, delete-orphan")
    patterns = relationship("Pattern", back_populates="user", cascade="all, delete-orphan")
    streaks = relationship("Streak", back_populates="user", cascade="all, delete-orphan")
    mood_logs = relationship("MoodLog", back_populates="user", cascade="all, delete-orphan")
    response_timings = relationship("ResponseTiming", back_populates="user", cascade="all, delete-orphan")
    weekly_insights = relationship("WeeklyInsight", back_populates="user", cascade="all, delete-orphan")
    settings = relationship("Settings", back_populates="user", cascade="all, delete-orphan")
    checkin_schedules = relationship("CheckInSchedule", back_populates="user", cascade="all, delete-orphan")
    checkin_prompts = relationship("CheckInPrompt", back_populates="user", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="user", cascade="all, delete-orphan")
    calendar_events = relationship("CalendarEvent", back_populates="user", cascade="all, delete-orphan")
    pending_parses = relationship("PendingCommitmentParse", back_populates="user", cascade="all, delete-orphan")
    scheduled_followups = relationship("ScheduledFollowup", back_populates="user", cascade="all, delete-orphan")
    error_logs = relationship("ErrorLog", back_populates="user")
    github_repos = relationship("GitHubRepo", back_populates="user", cascade="all, delete-orphan")
    github_commits = relationship("GitHubCommit", back_populates="user", cascade="all, delete-orphan")


class Goal(Base):
    """Long-term goals being worked toward."""

    __tablename__ = "goals"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    target_date = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="goals")
    commitments = relationship("Commitment", back_populates="goal")


class Commitment(Base):
    """Specific commitments/tasks tied to goals."""

    __tablename__ = "commitments"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    goal_id = Column(BigInteger, ForeignKey("goals.id", ondelete="SET NULL"), nullable=True)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(DateTime, nullable=True, index=True)
    status = Column(
        SQLEnum(
            CommitmentStatus,
            name="commitment_status",
            create_type=False,
            values_callable=lambda x: [e.value for e in x]
        ),
        default=CommitmentStatus.PENDING,
        nullable=False
    )
    completed_at = Column(DateTime, nullable=True)
    deferred_count = Column(Integer, default=0)  # Track how many times deferred
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="commitments")
    goal = relationship("Goal", back_populates="commitments")


class CheckIn(Base):
    """Check-in messages sent by The Warden."""

    __tablename__ = "checkins"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    check_in_type = Column(
        SQLEnum(
            CheckInType,
            name="checkin_type",
            create_type=False,
            values_callable=lambda x: [e.value for e in x]
        ),
        nullable=False
    )
    message_sent = Column(Text, nullable=False)  # What The Warden said
    telegram_message_id = Column(Text, nullable=True)
    sent_at = Column(DateTime, default=datetime.utcnow, index=True)
    response_received = Column(Boolean, default=False, index=True)
    responded_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="checkins")
    responses = relationship("Response", back_populates="check_in")
    response_timings = relationship("ResponseTiming", back_populates="check_in")


class Response(Base):
    """User responses to check-ins."""

    __tablename__ = "responses"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    check_in_id = Column(BigInteger, ForeignKey("checkins.id", ondelete="SET NULL"), nullable=True)
    message_text = Column(Text, nullable=False)
    telegram_message_id = Column(Text, nullable=True)
    received_at = Column(DateTime, default=datetime.utcnow)

    # LLM analysis of the response
    detected_shipped = Column(Boolean, nullable=True)  # Did they ship something?
    detected_excuse = Column(Boolean, nullable=True)  # Is this an excuse?
    detected_avoidance = Column(Boolean, nullable=True)  # Signs of avoidance?
    analysis_notes = Column(Text, nullable=True)  # LLM's notes

    # Relationships
    user = relationship("User", back_populates="responses")
    check_in = relationship("CheckIn", back_populates="responses")


class Pattern(Base):
    """Detected behavioral patterns over time."""

    __tablename__ = "patterns"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    pattern_type = Column(
        Text, nullable=False
    )  # avoidance, silence, excuse, consistency
    description = Column(Text, nullable=False)
    evidence = Column(JSON, nullable=True)  # Structured supporting data
    severity = Column(Integer, default=1)  # 1-5 scale
    detected_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)  # Still relevant?

    # Relationships
    user = relationship("User", back_populates="patterns")


class Settings(Base):
    """Application settings stored in database."""

    __tablename__ = "settings"
    __table_args__ = (
        UniqueConstraint("user_id", "key", name="settings_user_id_key_unique"),
    )

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    key = Column(Text, nullable=False, index=True)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="settings")


class ChatMessage(Base):
    """Chat messages for conversation history."""

    __tablename__ = "chat_messages"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(Text, nullable=False)  # 'warden' or 'user'
    content = Column(Text, nullable=False)
    message_type = Column(Text, nullable=True)  # check-in type or 'reply'
    telegram_message_id = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="chat_messages")


class CalendarEvent(Base):
    """Cached calendar events from Google Calendar."""

    __tablename__ = "calendar_events"
    __table_args__ = (
        UniqueConstraint("user_id", "google_event_id", name="calendar_events_user_google_unique"),
    )

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    google_event_id = Column(Text, nullable=False)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    all_day = Column(Boolean, default=False)
    location = Column(Text, nullable=True)
    is_ooo = Column(Boolean, default=False)  # Out of office/vacation
    last_synced = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="calendar_events")


class Streak(Base):
    """Track user streaks for gamification."""

    __tablename__ = "streaks"
    __table_args__ = (
        UniqueConstraint("user_id", "streak_type", name="streaks_user_type_unique"),
    )

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    streak_type = Column(Text, nullable=False)  # 'response' or 'completion'
    current_count = Column(Integer, default=0)
    best_count = Column(Integer, default=0)
    last_updated = Column(DateTime, default=datetime.utcnow)
    last_activity_date = Column(DateTime, nullable=True)  # For daily response streak
    last_week_end = Column(DateTime, nullable=True)  # For weekly completion streak

    # Relationships
    user = relationship("User", back_populates="streaks")


class PendingCommitmentParse(Base):
    """Temporary storage for commitments parsed from natural language awaiting confirmation."""

    __tablename__ = "pending_commitment_parses"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    original_message = Column(Text, nullable=False)
    parsed_title = Column(Text, nullable=False)
    parsed_due_date = Column(DateTime, nullable=True)
    parsed_description = Column(Text, nullable=True)
    confirmation_message_id = Column(Text, nullable=True)
    status = Column(Text, default="pending")  # pending, confirmed, rejected, breakdown_pending
    suggested_breakdown = Column(JSON, nullable=True)  # JSON array of breakdown steps
    is_large = Column(Boolean, default=False)  # Whether this was flagged as a large commitment
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # Auto-expire after some time

    # Relationships
    user = relationship("User", back_populates="pending_parses")


class CheckInSchedule(Base):
    """Custom check-in schedules configured by the user."""

    __tablename__ = "checkin_schedules"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(Text, nullable=False)  # e.g., "Morning Check-in", "Mid-day Reminder"
    check_in_type = Column(Text, nullable=False)  # daily_checkin, custom, reminder
    hour = Column(Integer, nullable=False)  # 0-23
    minute = Column(Integer, default=0)  # 0-59
    days_of_week = Column(Text, nullable=True)  # e.g., "mon,tue,wed,thu,fri" or null for every day
    prompt_template = Column(Text, nullable=True)  # Custom prompt, null means use default
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="checkin_schedules")


class CheckInPrompt(Base):
    """Customizable prompts for different check-in types."""

    __tablename__ = "checkin_prompts"
    __table_args__ = (
        UniqueConstraint("user_id", "prompt_type", name="checkin_prompts_user_type_unique"),
    )

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    prompt_type = Column(Text, nullable=False)  # daily_checkin, weekly_review, escalation, etc.
    prompt_template = Column(Text, nullable=False)
    is_custom = Column(Boolean, default=False)  # True if user has customized it
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="checkin_prompts")


class ScheduledFollowup(Base):
    """Scheduled follow-up messages for specific topics."""

    __tablename__ = "scheduled_followups"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    topic = Column(Text, nullable=False)
    reason = Column(Text, nullable=True)
    scheduled_time = Column(DateTime, nullable=False)
    status = Column(Text, default="pending")  # pending, sent, cancelled
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="scheduled_followups")


class MoodLog(Base):
    """Track detected mood and energy levels over time."""

    __tablename__ = "mood_logs"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    mood_score = Column(Integer, nullable=True)  # 1-10 scale
    energy_level = Column(Text, nullable=True)  # low, medium, high
    detected_from = Column(Text, nullable=True)  # llm_analysis, user_input, etc.
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="mood_logs")


class ErrorLog(Base):
    """Track application errors for debugging and monitoring."""

    __tablename__ = "error_logs"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    error_type = Column(Text, nullable=False)  # Exception class name
    error_message = Column(Text, nullable=False)
    stack_trace = Column(Text, nullable=True)
    context = Column(JSON, nullable=True)  # JSON with additional context
    source = Column(Text, nullable=True)  # webhook, scheduler, etc.
    user_message = Column(Text, nullable=True)  # The message that triggered the error
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="error_logs")


class ResponseTiming(Base):
    """Track response timing patterns for personalized thresholds."""

    __tablename__ = "response_timings"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    check_in_id = Column(BigInteger, ForeignKey("checkins.id", ondelete="SET NULL"), nullable=True)
    response_time_minutes = Column(Integer, nullable=True)  # Time to respond in minutes
    did_respond = Column(Boolean, default=False)
    day_of_week = Column(Integer, nullable=True)  # 0=Monday, 6=Sunday
    hour_of_day = Column(Integer, nullable=True)  # 0-23
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="response_timings")
    check_in = relationship("CheckIn", back_populates="response_timings")


class WeeklyInsight(Base):
    """Store weekly insights and metrics summaries."""

    __tablename__ = "weekly_insights"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    week_start = Column(DateTime, nullable=False)
    week_end = Column(DateTime, nullable=False)
    summary = Column(Text, nullable=True)  # LLM-generated summary
    metrics = Column(JSON, nullable=True)  # JSON with metrics data
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="weekly_insights")


class GitHubRepo(Base):
    """Configured GitHub repositories to monitor."""

    __tablename__ = "github_repos"
    __table_args__ = (
        UniqueConstraint("user_id", "repo_owner", "repo_name", name="github_repos_user_owner_name_unique"),
    )

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    repo_owner = Column(Text, nullable=False)
    repo_name = Column(Text, nullable=False)
    enabled = Column(Boolean, default=True)
    consecutive_failures = Column(Integer, default=0)
    last_error = Column(Text, nullable=True)
    last_error_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="github_repos")
    commits = relationship("GitHubCommit", back_populates="repo", cascade="all, delete-orphan")


class GitHubCommit(Base):
    """Fetched commit history from GitHub."""

    __tablename__ = "github_commits"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    repo_id = Column(BigInteger, ForeignKey("github_repos.id", ondelete="CASCADE"), nullable=False)
    commit_message = Column(Text, nullable=False)
    committed_at = Column(DateTime, nullable=False)
    fetched_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="github_commits")
    repo = relationship("GitHubRepo", back_populates="commits")
