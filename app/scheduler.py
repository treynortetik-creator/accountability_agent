"""Scheduled jobs for The Warden using APScheduler."""

import json
import logging
from datetime import datetime, timedelta
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.config import get_settings
from app.database import async_session_maker
from app.security import to_naive_utc, utc_now
from app.db_models import (
    Goal,
    Commitment,
    CommitmentStatus,
    CheckIn,
    CheckInType,
    Pattern,
    ChatMessage,
    CheckInSchedule,
    Settings,
    ScheduledFollowup,
    MoodLog,
    ResponseTiming,
    WeeklyInsight,
    ErrorLog,
    User,
    GitHubRepo,
    GitHubCommit,
)
from app.github_service import fetch_github_commits, GitHubAPIError
from app.telegram_bot import telegram_service
from app.llm import generate_message
from app.patterns import PatternDetector
from app.streaks import get_streak_context, update_response_streak, update_completion_streak, check_response_streak_broken
from app.calendar_service import calendar_service
from app.user_service import get_all_active_users, get_default_user

logger = logging.getLogger(__name__)
settings = get_settings()


async def log_scheduler_error(job_name: str, error: Exception, user_id=None):
    """Log a scheduler error to the database for UI visibility."""
    import traceback
    try:
        async with async_session_maker() as db:
            error_log = ErrorLog(
                user_id=user_id,
                error_type=type(error).__name__,
                error_message=str(error),
                stack_trace=traceback.format_exc(),
                context=json.dumps({"job_name": job_name}),
                source="scheduler",
            )
            db.add(error_log)
            await db.commit()
            logger.info(f"Scheduler error logged to database for job: {job_name}")
    except Exception as log_error:
        logger.error(f"Failed to log scheduler error to database: {log_error}")

# Global scheduler instance
scheduler = AsyncIOScheduler()


async def get_context(db: AsyncSession, user: User = None) -> dict:
    """Build context dict for LLM calls.

    Args:
        db: Database session
        user: User to build context for. If None, uses default user.
    """
    # Get user if not provided
    if user is None:
        user = await get_default_user(db)

    # Get active goals for this user
    goals_result = await db.execute(
        select(Goal).where(Goal.user_id == user.id, Goal.is_active == True)
    )
    goals = [{"id": g.id, "title": g.title} for g in goals_result.scalars().all()]

    # Get pending commitments for this user
    pending_result = await db.execute(
        select(Commitment).where(
            Commitment.user_id == user.id,
            Commitment.status == CommitmentStatus.PENDING
        )
    )
    pending = [
        {
            "id": c.id,
            "title": c.title,
            "due_date": c.due_date.isoformat() if c.due_date else None,
            "deferred_count": c.deferred_count,
        }
        for c in pending_result.scalars().all()
    ]

    # Get recently completed (last 7 days) for this user
    week_ago = utc_now() - timedelta(days=7)
    completed_result = await db.execute(
        select(Commitment).where(
            and_(
                Commitment.user_id == user.id,
                Commitment.status == CommitmentStatus.COMPLETED,
                Commitment.completed_at > week_ago,
            )
        )
    )
    completed = [
        {"id": c.id, "title": c.title}
        for c in completed_result.scalars().all()
    ]

    # Get upcoming deadlines (next 48 hours) for this user
    now = utc_now()
    deadline_cutoff = now + timedelta(hours=settings.deadline_alert_hours)
    deadline_result = await db.execute(
        select(Commitment).where(
            and_(
                Commitment.user_id == user.id,
                Commitment.status == CommitmentStatus.PENDING,
                Commitment.due_date.isnot(None),
                Commitment.due_date > now,
                Commitment.due_date <= deadline_cutoff,
            )
        )
    )
    upcoming_deadlines = []
    for c in deadline_result.scalars().all():
        # Use to_naive_utc for consistent datetime handling
        due = to_naive_utc(c.due_date)
        upcoming_deadlines.append({
            "id": c.id,
            "title": c.title,
            "due_date": c.due_date.isoformat(),
            "hours_until": (due - now).total_seconds() / 3600,
        })

    # Get active patterns for this user
    patterns_result = await db.execute(
        select(Pattern).where(Pattern.user_id == user.id, Pattern.is_active == True)
    )
    patterns = [
        {"type": p.pattern_type, "description": p.description, "severity": p.severity}
        for p in patterns_result.scalars().all()
    ]

    # Get days since last response for this user
    last_response = await db.execute(
        select(CheckIn)
        .where(CheckIn.user_id == user.id, CheckIn.response_received == True)
        .order_by(CheckIn.responded_at.desc())
        .limit(1)
    )
    last_responded = last_response.scalar_one_or_none()
    days_since_response = 0
    if last_responded and last_responded.responded_at:
        responded = to_naive_utc(last_responded.responded_at)
        days_since_response = (utc_now() - responded).days

    # Calculate completion rate (last 30 days) for this user
    month_ago = utc_now() - timedelta(days=30)
    total_result = await db.execute(
        select(func.count(Commitment.id)).where(
            Commitment.user_id == user.id,
            Commitment.created_at > month_ago
        )
    )
    total_month = total_result.scalar() or 0

    completed_month_result = await db.execute(
        select(func.count(Commitment.id)).where(
            and_(
                Commitment.user_id == user.id,
                Commitment.status == CommitmentStatus.COMPLETED,
                Commitment.completed_at > month_ago,
            )
        )
    )
    completed_month = completed_month_result.scalar() or 0
    completion_rate = (completed_month / total_month * 100) if total_month > 0 else 0

    # Get streak context for this user
    streaks = await get_streak_context(db, user)

    # Get calendar context for this user
    calendar_ctx = await calendar_service.get_calendar_context(db, user)

    # Get chat history count setting (default 15) for this user
    chat_count_result = await db.execute(
        select(Settings).where(
            Settings.user_id == user.id,
            Settings.key == "chat_history_count"
        )
    )
    chat_count_setting = chat_count_result.scalar_one_or_none()
    chat_history_count = int(chat_count_setting.value) if chat_count_setting else 15

    # Get recent chat history for this user
    chat_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.user_id == user.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(chat_history_count)
    )
    chat_messages = list(reversed(chat_result.scalars().all()))  # Oldest first
    chat_history = [
        {"role": m.role, "content": m.content, "timestamp": m.created_at.isoformat()}
        for m in chat_messages
    ]

    # Get LLM memory for this user
    memory_result = await db.execute(
        select(Settings).where(
            Settings.user_id == user.id,
            Settings.key == "llm_memory"
        )
    )
    memory_setting = memory_result.scalar_one_or_none()
    llm_memory = memory_setting.value if memory_setting else ""

    # Get user profile for this user
    profile_result = await db.execute(
        select(Settings).where(
            Settings.user_id == user.id,
            Settings.key == "user_profile"
        )
    )
    profile_setting = profile_result.scalar_one_or_none()
    user_profile = {}
    if profile_setting:
        import json
        try:
            user_profile = json.loads(profile_setting.value)
        except json.JSONDecodeError:
            user_profile = {"personal": [], "work": [], "health": [], "other": []}

    # Get accountability intensity (default 3 = balanced) for this user
    intensity_result = await db.execute(
        select(Settings).where(
            Settings.user_id == user.id,
            Settings.key == "accountability_intensity"
        )
    )
    intensity_setting = intensity_result.scalar_one_or_none()
    accountability_intensity = int(intensity_setting.value) if intensity_setting else 3

    # Get pending scheduled follow-ups for this user (so AI doesn't create duplicates)
    followups_result = await db.execute(
        select(ScheduledFollowup).where(
            ScheduledFollowup.user_id == user.id,
            ScheduledFollowup.status == "pending"
        ).order_by(ScheduledFollowup.scheduled_time)
    )
    scheduled_followups = [
        {
            "id": f.id,
            "topic": f.topic,
            "reason": f.reason,
            "scheduled_time": f.scheduled_time.isoformat() if f.scheduled_time else None,
        }
        for f in followups_result.scalars().all()
    ]

    # Get recent GitHub activity for this user
    github_commits_result = await db.execute(
        select(GitHubCommit)
        .options(selectinload(GitHubCommit.repo))
        .where(GitHubCommit.user_id == user.id)
        .order_by(GitHubCommit.committed_at.desc())
        .limit(20)
    )
    github_activity = [
        {
            "repo": commit.repo.repo_name,
            "message": commit.commit_message,
            "date": commit.committed_at.strftime("%Y-%m-%d"),
        }
        for commit in github_commits_result.scalars().all()
    ]

    # Calculate days since last commit
    days_since_commit = None
    if github_activity:
        last_commit_date = datetime.strptime(github_activity[0]["date"], "%Y-%m-%d")
        days_since_commit = (utc_now().date() - last_commit_date.date()).days

    return {
        "goals": goals,
        "pending_commitments": pending,
        "completed_commitments": completed,
        "upcoming_deadlines": upcoming_deadlines,
        "patterns": patterns,
        "days_since_response": days_since_response,
        "completion_rate": round(completion_rate, 1),
        "streaks": streaks,
        "calendar": calendar_ctx,
        "chat_history": chat_history,
        "llm_memory": llm_memory,
        "user_profile": user_profile,
        "accountability_intensity": accountability_intensity,
        "scheduled_followups": scheduled_followups,
        "github_activity": github_activity,
        "days_since_commit": days_since_commit,
    }


async def daily_checkin_job():
    """Send daily morning check-in to all active users."""
    logger.info("Running daily check-in job")

    async with async_session_maker() as db:
        try:
            # Get all active users
            users = await get_all_active_users(db)
            if not users:
                logger.warning("No active users found, skipping daily check-in")
                return

            for user in users:
                try:
                    # Check if user is OOO today - skip check-in if so
                    if await calendar_service.is_configured(db, user):
                        if await calendar_service.is_ooo_today(db, user):
                            logger.info(f"User {user.id} is OOO today, skipping daily check-in")
                            continue

                    # Check if response streak was broken
                    await check_response_streak_broken(db, user)

                    context = await get_context(db, user)

                    # Generate message
                    message = await generate_message("daily_checkin", context)

                    # Send via Telegram to user's chat
                    msg_id = await telegram_service.send_check_in(message, chat_id=user.telegram_chat_id)

                    # Record check-in
                    checkin = CheckIn(
                        user_id=user.id,
                        check_in_type=CheckInType.DAILY,
                        message_sent=message,
                        telegram_message_id=msg_id,
                    )
                    db.add(checkin)

                    # Save to chat history
                    chat_msg = ChatMessage(
                        user_id=user.id,
                        role="warden",
                        content=message,
                        message_type="daily_checkin",
                        telegram_message_id=msg_id,
                    )
                    db.add(chat_msg)

                    # Run pattern detection for this user
                    detector = PatternDetector(db, user)
                    new_patterns = await detector.run_detection()
                    if new_patterns:
                        logger.info(f"Detected {len(new_patterns)} new patterns for user {user.id}")

                    # Deactivate old patterns
                    await detector.deactivate_old_patterns()

                    # Commit after each successful user to prevent partial failures
                    await db.commit()
                    logger.info(f"Daily check-in sent to user {user.id}")

                except Exception as user_error:
                    logger.error(f"Daily check-in failed for user {user.id}: {user_error}", exc_info=True)
                    await db.rollback()  # Rollback the failed user's changes
                    await log_scheduler_error("daily_checkin", user_error, user.id)
                    continue

            logger.info("Daily check-in job completed")

        except Exception as e:
            logger.error(f"Daily check-in failed: {e}", exc_info=True)
            await db.rollback()
            await log_scheduler_error("daily_checkin", e)


async def weekly_review_job():
    """Send weekly review on Sunday evening, followed by planning prompt."""
    logger.info("Running weekly review job")

    async with async_session_maker() as db:
        try:
            # Get all active users
            users = await get_all_active_users(db)
            if not users:
                logger.warning("No active users found, skipping weekly review")
                return

            for user in users:
                try:
                    # Update completion streak first for this user
                    streak_result = await update_completion_streak(db, user)
                    logger.info(f"Completion streak updated for user {user.id}: {streak_result}")

                    context = await get_context(db, user)

                    # Add weekly-specific stats
                    week_ago = utc_now() - timedelta(days=7)

                    # Weekly completions for this user
                    completed_result = await db.execute(
                        select(func.count(Commitment.id)).where(
                            and_(
                                Commitment.user_id == user.id,
                                Commitment.status == CommitmentStatus.COMPLETED,
                                Commitment.completed_at > week_ago,
                            )
                        )
                    )
                    context["weekly_completed"] = completed_result.scalar() or 0

                    # Weekly failures/deferrals for this user
                    failed_result = await db.execute(
                        select(func.count(Commitment.id)).where(
                            and_(
                                Commitment.user_id == user.id,
                                Commitment.status.in_(
                                    [CommitmentStatus.FAILED, CommitmentStatus.DEFERRED]
                                ),
                                Commitment.updated_at > week_ago,
                            )
                        )
                    )
                    context["weekly_failed"] = failed_result.scalar() or 0

                    # Weekly response rate for this user
                    checkins_result = await db.execute(
                        select(CheckIn).where(
                            CheckIn.user_id == user.id,
                            CheckIn.sent_at > week_ago
                        )
                    )
                    checkins = checkins_result.scalars().all()
                    if checkins:
                        responded = sum(1 for c in checkins if c.response_received)
                        context["weekly_response_rate"] = round(responded / len(checkins) * 100, 1)
                    else:
                        context["weekly_response_rate"] = 0

                    # Generate review message (now includes planning prompt at the end)
                    message = await generate_message("weekly_review", context)

                    # Send via Telegram to user's chat
                    msg_id = await telegram_service.send_weekly_review(message, chat_id=user.telegram_chat_id)

                    # Record check-in
                    checkin = CheckIn(
                        user_id=user.id,
                        check_in_type=CheckInType.WEEKLY_REVIEW,
                        message_sent=message,
                        telegram_message_id=msg_id,
                    )
                    db.add(checkin)

                    # Save to chat history
                    chat_msg = ChatMessage(
                        user_id=user.id,
                        role="warden",
                        content=message,
                        message_type="weekly_review",
                        telegram_message_id=msg_id,
                    )
                    db.add(chat_msg)

                    # Commit after each successful user
                    await db.commit()
                    logger.info(f"Weekly review sent to user {user.id}")

                except Exception as user_error:
                    logger.error(f"Weekly review failed for user {user.id}: {user_error}", exc_info=True)
                    await db.rollback()
                    await log_scheduler_error("weekly_review", user_error, user.id)
                    continue

            logger.info("Weekly review job completed")

        except Exception as e:
            logger.error(f"Weekly review failed: {e}", exc_info=True)
            await db.rollback()
            await log_scheduler_error("weekly_review", e)


async def silence_detector_job():
    """Check for unanswered check-ins and escalate with personalized timing."""
    logger.info("Running silence detector job")

    async with async_session_maker() as db:
        try:
            # Get all active users
            users = await get_all_active_users(db)
            if not users:
                logger.warning("No active users found, skipping silence detection")
                return

            for user in users:
                try:
                    # Find last check-in for this user
                    last_checkin_result = await db.execute(
                        select(CheckIn)
                        .where(CheckIn.user_id == user.id)
                        .order_by(CheckIn.sent_at.desc())
                        .limit(1)
                    )
                    last_checkin = last_checkin_result.scalar_one_or_none()

                    if not last_checkin:
                        logger.info(f"No check-ins found for user {user.id}, skipping silence detection")
                        continue

                    # If last check-in was answered, no escalation needed
                    if last_checkin.response_received:
                        logger.info(f"Last check-in was answered for user {user.id}, no escalation needed")
                        continue

                    # Calculate hours since last check-in
                    # Use to_naive_utc for consistent datetime handling
                    sent_at = to_naive_utc(last_checkin.sent_at)
                    hours_since = (utc_now() - sent_at).total_seconds() / 3600

                    # ENHANCED: Calculate personalized threshold based on user's typical response time
                    avg_response_result = await db.execute(
                        select(func.avg(ResponseTiming.response_time_minutes)).where(
                            and_(
                                ResponseTiming.user_id == user.id,
                                ResponseTiming.did_respond == True,
                            )
                        )
                    )
                    avg_response_minutes = avg_response_result.scalar()

                    # Use personalized threshold if we have enough data, otherwise use default
                    if avg_response_minutes and avg_response_minutes > 0:
                        # If they usually respond in X minutes, alert after 3x that time (minimum 2 hours)
                        personalized_threshold_hours = max(2, (avg_response_minutes * 3) / 60)
                        # But don't exceed the configured maximum
                        threshold_hours = min(personalized_threshold_hours, settings.silence_threshold_hours)
                        logger.info(f"Using personalized silence threshold for user {user.id}: {threshold_hours:.1f}h (avg response: {avg_response_minutes:.0f}min)")
                    else:
                        threshold_hours = settings.silence_threshold_hours

                    if hours_since < threshold_hours:
                        logger.info(f"Only {hours_since:.1f} hours since last check-in for user {user.id}, under threshold ({threshold_hours:.1f}h)")
                        continue

                    # Check if we already escalated recently (within 12 hours) for this user
                    twelve_hours_ago = utc_now() - timedelta(hours=12)
                    recent_escalation = await db.execute(
                        select(CheckIn).where(
                            and_(
                                CheckIn.user_id == user.id,
                                CheckIn.check_in_type == CheckInType.ESCALATION,
                                CheckIn.sent_at > twelve_hours_ago,
                            )
                        )
                    )
                    if recent_escalation.scalar_one_or_none():
                        logger.info(f"Already escalated recently for user {user.id}, skipping")
                        continue

                    # Time to escalate
                    context = await get_context(db, user)
                    context["hours_since_response"] = hours_since
                    context["last_checkin_answered"] = False
                    # Add personalized context
                    if avg_response_minutes and avg_response_minutes > 0:
                        context["usual_response_time"] = f"{int(avg_response_minutes)} minutes"
                        context["silence_is_unusual"] = hours_since > (avg_response_minutes * 2 / 60)
                    else:
                        context["usual_response_time"] = "unknown"
                        context["silence_is_unusual"] = False

                    message = await generate_message("escalation", context)
                    msg_id = await telegram_service.send_escalation(message, chat_id=user.telegram_chat_id)

                    # Record escalation
                    checkin = CheckIn(
                        user_id=user.id,
                        check_in_type=CheckInType.ESCALATION,
                        message_sent=message,
                        telegram_message_id=msg_id,
                    )
                    db.add(checkin)

                    # Save to chat history
                    chat_msg = ChatMessage(
                        user_id=user.id,
                        role="warden",
                        content=message,
                        message_type="escalation",
                        telegram_message_id=msg_id,
                    )
                    db.add(chat_msg)

                    # Commit after each successful user
                    await db.commit()
                    logger.info(f"Escalation sent to user {user.id} after {hours_since:.1f} hours of silence")

                except Exception as user_error:
                    logger.error(f"Silence detection failed for user {user.id}: {user_error}", exc_info=True)
                    await db.rollback()
                    await log_scheduler_error("silence_detector", user_error, user.id)
                    continue

            logger.info("Silence detector job completed")

        except Exception as e:
            logger.error(f"Silence detector failed: {e}", exc_info=True)
            await db.rollback()
            await log_scheduler_error("silence_detector", e)


async def commitment_reminder_job():
    """Send 90-minute reminders for upcoming commitment deadlines."""
    logger.info("Running commitment reminder job")

    async with async_session_maker() as db:
        try:
            # Get all active users
            users = await get_all_active_users(db)
            if not users:
                logger.warning("No active users found, skipping commitment reminders")
                return

            import pytz
            import random
            tz = pytz.timezone(settings.timezone)
            now = datetime.now(tz)
            # Convert to naive UTC for database comparison
            now_utc = utc_now()

            # Find commitments due in the next 90-105 minutes (15-min window to catch them)
            reminder_start = now_utc + timedelta(minutes=75)
            reminder_end = now_utc + timedelta(minutes=105)

            for user in users:
                try:
                    result = await db.execute(
                        select(Commitment).where(
                            and_(
                                Commitment.user_id == user.id,
                                Commitment.status == CommitmentStatus.PENDING,
                                Commitment.due_date.isnot(None),
                                Commitment.due_date >= reminder_start,
                                Commitment.due_date <= reminder_end,
                            )
                        )
                    )
                    upcoming = result.scalars().all()

                    for commitment in upcoming:
                        # Check if we already sent a reminder for this commitment for this user
                        two_hours_ago = utc_now() - timedelta(hours=2)
                        recent_reminder = await db.execute(
                            select(CheckIn).where(
                                and_(
                                    CheckIn.user_id == user.id,
                                    CheckIn.check_in_type == CheckInType.DEADLINE_REMINDER,
                                    CheckIn.sent_at > two_hours_ago,
                                    CheckIn.message_sent.contains(commitment.title),
                                )
                            )
                        )
                        if recent_reminder.scalar_one_or_none():
                            continue

                        # Calculate time until due
                        # Use to_naive_utc for consistent datetime handling
                        due = to_naive_utc(commitment.due_date)
                        minutes_until = (due - now_utc).total_seconds() / 60
                        due_time_str = commitment.due_date.strftime('%I:%M %p').lstrip('0')

                        # Generate a conversational reminder
                        reminder_messages = [
                            f"Heads up - \"{commitment.title}\" is due at {due_time_str}. That's about 90 minutes from now. Where are you on this?",
                            f"Clock's ticking on \"{commitment.title}\" - due at {due_time_str}. You've got about 90 minutes. Status?",
                            f"Just checking in on \"{commitment.title}\" - it's coming up at {due_time_str}. Are you on track or do we need to talk about this?",
                        ]
                        message = random.choice(reminder_messages)

                        msg_id = await telegram_service.send_message(message, chat_id=user.telegram_chat_id)

                        # Record reminder
                        checkin = CheckIn(
                            user_id=user.id,
                            check_in_type=CheckInType.DEADLINE_REMINDER,
                            message_sent=message,
                            telegram_message_id=msg_id,
                        )
                        db.add(checkin)

                        # Save to chat history
                        chat_msg = ChatMessage(
                            user_id=user.id,
                            role="warden",
                            content=message,
                            message_type="deadline_reminder",
                            telegram_message_id=msg_id,
                        )
                        db.add(chat_msg)

                        logger.info(f"Sent 90-min reminder for user {user.id}: {commitment.title}")

                    # Commit after each successful user
                    await db.commit()

                except Exception as user_error:
                    logger.error(f"Commitment reminder failed for user {user.id}: {user_error}", exc_info=True)
                    await db.rollback()
                    await log_scheduler_error("commitment_reminder", user_error, user.id)
                    continue

            logger.info("Commitment reminder job completed")

        except Exception as e:
            logger.error(f"Commitment reminder failed: {e}", exc_info=True)
            await db.rollback()
            await log_scheduler_error("commitment_reminder", e)


async def deadline_alert_job():
    """Check for upcoming deadlines and send alerts."""
    logger.info("Running deadline alert job")

    async with async_session_maker() as db:
        try:
            # Get all active users
            users = await get_all_active_users(db)
            if not users:
                logger.warning("No active users found, skipping deadline alerts")
                return

            now = utc_now()
            deadline_cutoff = now + timedelta(hours=settings.deadline_alert_hours)
            total_processed = 0

            for user in users:
                try:
                    # Find commitments with upcoming deadlines for this user
                    result = await db.execute(
                        select(Commitment).where(
                            and_(
                                Commitment.user_id == user.id,
                                Commitment.status == CommitmentStatus.PENDING,
                                Commitment.due_date.isnot(None),
                                Commitment.due_date > now,
                                Commitment.due_date <= deadline_cutoff,
                            )
                        )
                    )
                    upcoming = result.scalars().all()

                    for commitment in upcoming:
                        # Check if we already alerted for this commitment recently for this user
                        day_ago = utc_now() - timedelta(hours=24)
                        recent_alert = await db.execute(
                            select(CheckIn).where(
                                and_(
                                    CheckIn.user_id == user.id,
                                    CheckIn.check_in_type == CheckInType.DEADLINE_ALERT,
                                    CheckIn.sent_at > day_ago,
                                    CheckIn.message_sent.contains(commitment.title),
                                )
                            )
                        )
                        if recent_alert.scalar_one_or_none():
                            continue

                        # Use to_naive_utc for consistent datetime handling
                        due = to_naive_utc(commitment.due_date)
                        hours_until = (due - now).total_seconds() / 3600

                        context = await get_context(db, user)
                        context["deadline_commitment"] = {
                            "id": commitment.id,
                            "title": commitment.title,
                            "due_date": commitment.due_date.isoformat(),
                            "deferred_count": commitment.deferred_count,
                        }
                        context["hours_until_due"] = round(hours_until, 1)

                        message = await generate_message("deadline_alert", context)
                        msg_id = await telegram_service.send_deadline_alert(message, chat_id=user.telegram_chat_id)

                        # Record alert
                        checkin = CheckIn(
                            user_id=user.id,
                            check_in_type=CheckInType.DEADLINE_ALERT,
                            message_sent=message,
                            telegram_message_id=msg_id,
                        )
                        db.add(checkin)

                        # Save to chat history
                        chat_msg = ChatMessage(
                            user_id=user.id,
                            role="warden",
                            content=message,
                            message_type="deadline_alert",
                            telegram_message_id=msg_id,
                        )
                        db.add(chat_msg)

                        total_processed += 1

                    # Commit after each successful user
                    await db.commit()

                except Exception as user_error:
                    logger.error(f"Deadline alert failed for user {user.id}: {user_error}", exc_info=True)
                    await db.rollback()
                    await log_scheduler_error("deadline_alert", user_error, user.id)
                    continue

            logger.info(f"Deadline alert job completed, processed {total_processed} upcoming deadlines")

        except Exception as e:
            logger.error(f"Deadline alert failed: {e}", exc_info=True)
            await db.rollback()
            await log_scheduler_error("deadline_alert", e)


async def scheduled_followup_job():
    """Check for and send pending follow-ups."""
    logger.info("Checking for scheduled follow-ups")

    async with async_session_maker() as db:
        try:
            # Get the default user for multi-user support
            user = await get_default_user(db)

            now = utc_now()

            # Find pending follow-ups that are due
            result = await db.execute(
                select(ScheduledFollowup).where(
                    and_(
                        ScheduledFollowup.status == "pending",
                        ScheduledFollowup.scheduled_time <= now,
                    )
                )
            )
            followups = result.scalars().all()

            for followup in followups:
                # Generate a message about the topic
                context = await get_context(db, user)
                context["followup_topic"] = followup.topic
                context["followup_reason"] = followup.reason

                message = await generate_message("followup", context)
                msg_id = await telegram_service.send_message(message)

                # Mark as sent
                followup.status = "sent"
                followup.sent_at = utc_now()

                # Record in check-in table
                checkin = CheckIn(
                    user_id=user.id,
                    check_in_type=CheckInType.MANUAL,
                    message_sent=message,
                    telegram_message_id=msg_id,
                )
                db.add(checkin)

                # Save to chat history
                chat_msg = ChatMessage(
                    user_id=user.id,
                    role="warden",
                    content=message,
                    message_type="followup",
                    telegram_message_id=msg_id,
                )
                db.add(chat_msg)

                logger.info(f"Sent follow-up on '{followup.topic}'")

            await db.commit()
            if followups:
                logger.info(f"Processed {len(followups)} follow-ups")

        except Exception as e:
            logger.error(f"Follow-up job failed: {e}", exc_info=True)
            await db.rollback()
            await log_scheduler_error("scheduled_followup", e)


async def weekly_insights_job():
    """Generate and send weekly insights on Sunday evening."""
    logger.info("Generating weekly insights")

    async with async_session_maker() as db:
        try:
            # Get the default user for multi-user support
            user = await get_default_user(db)

            # Calculate week range (Monday to Sunday)
            tz = pytz.timezone(settings.timezone)
            now = datetime.now(tz)
            week_end = now.replace(hour=23, minute=59, second=59, microsecond=0)
            week_start = week_end - timedelta(days=6)
            week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)

            # Convert to UTC for queries using to_naive_utc
            week_start_utc = to_naive_utc(week_start)
            week_end_utc = to_naive_utc(week_end)

            # Check if we already generated insights for this week
            existing = await db.execute(
                select(WeeklyInsight).where(
                    and_(
                        WeeklyInsight.week_start >= week_start_utc - timedelta(hours=12),
                        WeeklyInsight.week_start <= week_start_utc + timedelta(hours=12),
                    )
                )
            )
            if existing.scalar_one_or_none():
                logger.info("Weekly insights already generated for this week")
                return

            # Gather metrics for the week
            # Commitments created
            created_result = await db.execute(
                select(func.count(Commitment.id)).where(
                    Commitment.created_at.between(week_start_utc, week_end_utc)
                )
            )
            commitments_created = created_result.scalar() or 0

            # Commitments completed
            completed_result = await db.execute(
                select(func.count(Commitment.id)).where(
                    and_(
                        Commitment.status == CommitmentStatus.COMPLETED,
                        Commitment.completed_at.between(week_start_utc, week_end_utc),
                    )
                )
            )
            commitments_completed = completed_result.scalar() or 0

            # Response rate
            checkins_result = await db.execute(
                select(CheckIn).where(
                    CheckIn.sent_at.between(week_start_utc, week_end_utc)
                )
            )
            checkins = checkins_result.scalars().all()
            response_rate = 0
            if checkins:
                responded = sum(1 for c in checkins if c.response_received)
                response_rate = round(responded / len(checkins) * 100, 1)

            # Average mood (if tracked)
            mood_result = await db.execute(
                select(func.avg(MoodLog.mood_score)).where(
                    MoodLog.created_at.between(week_start_utc, week_end_utc)
                )
            )
            avg_mood = mood_result.scalar()
            avg_mood = round(avg_mood, 1) if avg_mood else None

            # Build metrics
            metrics = {
                "commitments_created": commitments_created,
                "commitments_completed": commitments_completed,
                "completion_rate": round(commitments_completed / commitments_created * 100, 1) if commitments_created > 0 else 0,
                "response_rate": response_rate,
                "avg_mood": avg_mood,
            }

            # Get context for LLM to generate insights
            context = await get_context(db, user)
            context["weekly_metrics"] = metrics
            context["week_start"] = week_start.strftime("%B %d")
            context["week_end"] = week_end.strftime("%B %d")

            message = await generate_message("weekly_insights", context)
            msg_id = await telegram_service.send_message(message)

            # Save insight
            insight = WeeklyInsight(
                user_id=user.id,
                week_start=week_start_utc,
                week_end=week_end_utc,
                summary=message,
                metrics=json.dumps(metrics),
                sent_at=utc_now(),
            )
            db.add(insight)

            # Record check-in
            checkin = CheckIn(
                user_id=user.id,
                check_in_type=CheckInType.WEEKLY_REVIEW,
                message_sent=message,
                telegram_message_id=msg_id,
            )
            db.add(checkin)

            # Save to chat history
            chat_msg = ChatMessage(
                user_id=user.id,
                role="warden",
                content=message,
                message_type="weekly_insights",
                telegram_message_id=msg_id,
            )
            db.add(chat_msg)

            await db.commit()
            logger.info("Weekly insights generated and sent")

        except Exception as e:
            logger.error(f"Weekly insights job failed: {e}", exc_info=True)
            await db.rollback()
            await log_scheduler_error("weekly_insights", e)


async def github_poll_job():
    """Fetch recent commits from configured GitHub repositories."""
    logger.info("Running GitHub poll job")

    async with async_session_maker() as db:
        try:
            # Get all active users
            users = await get_all_active_users(db)
            if not users:
                return

            for user in users:
                try:
                    # Get GitHub PAT from settings
                    pat_result = await db.execute(
                        select(Settings).where(
                            Settings.user_id == user.id,
                            Settings.key == "github_pat"
                        )
                    )
                    pat_setting = pat_result.scalar_one_or_none()
                    if not pat_setting or not pat_setting.value:
                        continue  # GitHub not configured for this user

                    # Get retention days setting
                    retention_result = await db.execute(
                        select(Settings).where(
                            Settings.user_id == user.id,
                            Settings.key == "github_retention_days"
                        )
                    )
                    retention_setting = retention_result.scalar_one_or_none()
                    retention_days = int(retention_setting.value) if retention_setting else 7

                    # Get enabled repos
                    repos_result = await db.execute(
                        select(GitHubRepo).where(
                            GitHubRepo.user_id == user.id,
                            GitHubRepo.enabled == True
                        )
                    )
                    repos = repos_result.scalars().all()

                    for repo in repos:
                        try:
                            commits = await fetch_github_commits(
                                pat_setting.value,
                                repo.repo_owner,
                                repo.repo_name,
                                since_days=retention_days
                            )

                            # Store new commits (avoid duplicates by checking committed_at + message)
                            for commit_data in commits:
                                # Convert timezone-aware datetime to naive (UTC) for database storage
                                committed_at = to_naive_utc(commit_data["committed_at"])

                                # Check if commit already exists
                                existing = await db.execute(
                                    select(GitHubCommit).where(
                                        GitHubCommit.repo_id == repo.id,
                                        GitHubCommit.committed_at == committed_at,
                                        GitHubCommit.commit_message == commit_data["message"]
                                    )
                                )
                                if existing.scalar_one_or_none():
                                    continue

                                new_commit = GitHubCommit(
                                    user_id=user.id,
                                    repo_id=repo.id,
                                    commit_message=commit_data["message"],
                                    committed_at=committed_at,
                                )
                                db.add(new_commit)

                            # Reset failure count on success
                            repo.consecutive_failures = 0
                            repo.last_error = None
                            repo.last_error_at = None

                            logger.info(f"Fetched {len(commits)} commits from {repo.repo_owner}/{repo.repo_name}")

                        except GitHubAPIError as e:
                            repo.consecutive_failures += 1
                            repo.last_error = str(e.message)
                            repo.last_error_at = utc_now()

                            logger.warning(f"GitHub API error for {repo.repo_owner}/{repo.repo_name}: {e.message}")

                            # Notify user after 3 consecutive failures
                            if repo.consecutive_failures >= 3:
                                await telegram_service.send_message(
                                    f"Hey, I've been trying to check your GitHub activity but something's wrong. "
                                    f"Failed 3 times on {repo.repo_owner}/{repo.repo_name}: {e.message}. "
                                    f"Might want to check your access token. I've paused monitoring that repo for now.",
                                    chat_id=user.telegram_chat_id
                                )
                                repo.enabled = False
                                logger.warning(f"Disabled repo {repo.repo_owner}/{repo.repo_name} after 3 failures")

                    await db.commit()

                except Exception as e:
                    logger.error(f"GitHub poll failed for user {user.id}: {e}", exc_info=True)
                    await log_scheduler_error("github_poll", e, user_id=user.id)

        except Exception as e:
            logger.error(f"GitHub poll job failed: {e}", exc_info=True)
            await log_scheduler_error("github_poll", e)


async def github_cleanup_job():
    """Remove commits older than retention period."""
    logger.info("Running GitHub cleanup job")

    async with async_session_maker() as db:
        try:
            users = await get_all_active_users(db)
            if not users:
                return

            for user in users:
                # Get retention days setting
                retention_result = await db.execute(
                    select(Settings).where(
                        Settings.user_id == user.id,
                        Settings.key == "github_retention_days"
                    )
                )
                retention_setting = retention_result.scalar_one_or_none()
                retention_days = int(retention_setting.value) if retention_setting else 7

                cutoff = utc_now() - timedelta(days=retention_days)

                # Delete old commits
                from sqlalchemy import delete
                result = await db.execute(
                    delete(GitHubCommit).where(
                        GitHubCommit.user_id == user.id,
                        GitHubCommit.committed_at < cutoff
                    )
                )
                deleted_count = result.rowcount

                if deleted_count > 0:
                    logger.info(f"Cleaned up {deleted_count} old GitHub commits for user {user.id}")

            await db.commit()

        except Exception as e:
            logger.error(f"GitHub cleanup job failed: {e}", exc_info=True)
            await log_scheduler_error("github_cleanup", e)


async def schedule_github_poll():
    """Schedule or reschedule the GitHub poll job based on user settings."""
    async with async_session_maker() as db:
        try:
            user = await get_default_user(db)

            # Get poll time settings
            hour_result = await db.execute(
                select(Settings).where(
                    Settings.user_id == user.id,
                    Settings.key == "github_poll_hour"
                )
            )
            minute_result = await db.execute(
                select(Settings).where(
                    Settings.user_id == user.id,
                    Settings.key == "github_poll_minute"
                )
            )

            hour_setting = hour_result.scalar_one_or_none()
            minute_setting = minute_result.scalar_one_or_none()

            poll_hour = int(hour_setting.value) if hour_setting else 3
            poll_minute = int(minute_setting.value) if minute_setting else 30

            tz = pytz.timezone(settings.timezone)

            # Remove existing job if present
            try:
                scheduler.remove_job("github_poll")
            except Exception:
                pass

            # Add job with configured time
            scheduler.add_job(
                github_poll_job,
                CronTrigger(hour=poll_hour, minute=poll_minute, timezone=tz),
                id="github_poll",
                replace_existing=True,
            )
            logger.info(f"Scheduled GitHub poll at {poll_hour}:{poll_minute:02d}")

        except Exception as e:
            logger.error(f"Failed to schedule GitHub poll: {e}", exc_info=True)


def setup_scheduler():
    """Configure and start the scheduler."""
    tz = pytz.timezone(settings.timezone)

    # NOTE: Daily check-ins and weekly reviews are now managed via custom schedules
    # in the database (checkin_schedules table). The hardcoded jobs were removed to
    # prevent duplicate check-ins. Use the dashboard Settings > Check-in Schedules
    # to configure check-in times.
    logger.info("Check-ins managed via custom schedules (checkin_schedules table)")

    # Silence detector every 12 hours
    scheduler.add_job(
        silence_detector_job,
        IntervalTrigger(hours=12),
        id="silence_detector",
        replace_existing=True,
    )
    logger.info("Scheduled silence detector every 12 hours")

    # Deadline alerts every 6 hours
    scheduler.add_job(
        deadline_alert_job,
        IntervalTrigger(hours=6),
        id="deadline_alerts",
        replace_existing=True,
    )
    logger.info("Scheduled deadline alerts every 6 hours")

    # 90-minute commitment reminders - check every 15 minutes
    scheduler.add_job(
        commitment_reminder_job,
        IntervalTrigger(minutes=15),
        id="commitment_reminders",
        replace_existing=True,
    )
    logger.info("Scheduled commitment reminders every 15 minutes")

    # Scheduled follow-ups - check every 5 minutes for due follow-ups
    scheduler.add_job(
        scheduled_followup_job,
        IntervalTrigger(minutes=5),
        id="scheduled_followups",
        replace_existing=True,
    )
    logger.info("Scheduled follow-up checker every 5 minutes")

    # GitHub cleanup - daily at 4:00 AM (after poll typically runs at 3:30 AM)
    scheduler.add_job(
        github_cleanup_job,
        CronTrigger(hour=4, minute=0, timezone=tz),
        id="github_cleanup",
        replace_existing=True,
    )
    logger.info("Scheduled GitHub cleanup at 4:00 AM")

    # NOTE: GitHub poll job is scheduled dynamically based on user settings
    # Call schedule_github_poll() after startup to set up the poll schedule

    scheduler.start()
    logger.info("Scheduler started")


def shutdown_scheduler():
    """Shutdown the scheduler gracefully."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler shutdown")


async def reschedule_jobs(config: dict):
    """Reschedule jobs with new configuration.

    NOTE: Daily check-ins and weekly reviews are now managed via custom schedules
    in the database (checkin_schedules table). Use reload_custom_schedules() or
    the dashboard Settings > Check-in Schedules to modify check-in times.

    This function is kept for backwards compatibility but no longer reschedules
    hardcoded jobs. Use reload_custom_schedules() instead.
    """
    logger.info("reschedule_jobs called - use reload_custom_schedules() for custom schedules")


async def custom_schedule_job(schedule_id: int, schedule_name: str, prompt_template: str = None):
    """Execute a custom scheduled check-in job."""
    async with async_session_maker() as db:
        try:
            # Get the default user for multi-user support
            user = await get_default_user(db)

            # Build context for the message
            context = await get_context(db, user)

            # Generate message using the custom prompt or default
            message = await generate_message(
                "daily_checkin",
                context,
                custom_instruction=prompt_template
            )

            if message:
                # Send via Telegram
                msg_id = await telegram_service.send_message(message)

                # Record the check-in
                checkin = CheckIn(
                    user_id=user.id,
                    check_in_type=CheckInType.DAILY,
                    message_sent=message,
                    telegram_message_id=msg_id,
                )
                db.add(checkin)

                # Record in chat history
                chat_msg = ChatMessage(
                    user_id=user.id,
                    role="warden",
                    content=message,
                    message_type="custom_checkin",
                    telegram_message_id=msg_id,
                )
                db.add(chat_msg)

                await db.commit()
                logger.info(f"Custom schedule '{schedule_name}' executed successfully")
            else:
                logger.warning(f"Custom schedule '{schedule_name}' generated no message")

        except Exception as e:
            logger.error(f"Error executing custom schedule '{schedule_name}': {e}", exc_info=True)
            await db.rollback()
            await log_scheduler_error(f"custom_schedule_{schedule_name}", e)


async def load_custom_schedules_on_startup():
    """Load custom check-in schedules from database and register them with the scheduler."""
    async with async_session_maker() as db:
        try:
            result = await db.execute(
                select(CheckInSchedule).where(CheckInSchedule.is_active == True)
            )
            schedules = result.scalars().all()

            tz = pytz.timezone(settings.timezone)

            for schedule in schedules:
                job_id = f"custom_schedule_{schedule.id}"

                # Parse days of week
                if schedule.days_of_week:
                    days = schedule.days_of_week.lower().split(",")
                    day_map = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}
                    day_of_week = ",".join(str(day_map.get(d.strip(), 0)) for d in days)
                else:
                    day_of_week = "*"  # Every day

                # Register the job
                scheduler.add_job(
                    custom_schedule_job,
                    CronTrigger(
                        day_of_week=day_of_week,
                        hour=schedule.hour,
                        minute=schedule.minute or 0,
                        timezone=tz,
                    ),
                    id=job_id,
                    args=[schedule.id, schedule.name, schedule.prompt_template],
                    replace_existing=True,
                )
                logger.info(f"Loaded custom schedule: {schedule.name} at {schedule.hour}:{schedule.minute or 0:02d}")

            logger.info(f"Loaded {len(schedules)} custom schedules")

        except Exception as e:
            logger.error(f"Error loading custom schedules: {e}")


async def reload_custom_schedules():
    """Reload all custom schedules from database (called when schedules are modified)."""
    # Remove existing custom schedule jobs
    for job in scheduler.get_jobs():
        if job.id.startswith("custom_schedule_"):
            scheduler.remove_job(job.id)
            logger.debug(f"Removed job: {job.id}")

    # Reload from database
    await load_custom_schedules_on_startup()
