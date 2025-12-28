"""Scheduled jobs for The Warden using APScheduler."""

import logging
import json
from datetime import datetime, timedelta
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import get_settings
from app.database import async_session_maker
from app.db_models import (
    Goal,
    Commitment,
    CommitmentStatus,
    CheckIn,
    CheckInType,
    Pattern,
    ChatMessage,
    CheckInSchedule,
)
from app.telegram_bot import telegram_service
from app.llm import generate_message
from app.patterns import PatternDetector
from app.streaks import get_streak_context, update_response_streak, update_completion_streak, check_response_streak_broken
from app.calendar_service import calendar_service

logger = logging.getLogger(__name__)
settings = get_settings()

# Global scheduler instance
scheduler = AsyncIOScheduler()


async def get_context(db: AsyncSession) -> dict:
    """Build context dict for LLM calls."""
    # Get active goals
    goals_result = await db.execute(
        select(Goal).where(Goal.is_active == True)
    )
    goals = [{"id": g.id, "title": g.title} for g in goals_result.scalars().all()]

    # Get pending commitments
    pending_result = await db.execute(
        select(Commitment).where(Commitment.status == CommitmentStatus.PENDING)
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

    # Get recently completed (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    completed_result = await db.execute(
        select(Commitment).where(
            and_(
                Commitment.status == CommitmentStatus.COMPLETED,
                Commitment.completed_at > week_ago,
            )
        )
    )
    completed = [
        {"id": c.id, "title": c.title}
        for c in completed_result.scalars().all()
    ]

    # Get upcoming deadlines (next 48 hours)
    now = datetime.utcnow()
    deadline_cutoff = now + timedelta(hours=settings.deadline_alert_hours)
    deadline_result = await db.execute(
        select(Commitment).where(
            and_(
                Commitment.status == CommitmentStatus.PENDING,
                Commitment.due_date.isnot(None),
                Commitment.due_date > now,
                Commitment.due_date <= deadline_cutoff,
            )
        )
    )
    upcoming_deadlines = [
        {
            "id": c.id,
            "title": c.title,
            "due_date": c.due_date.isoformat(),
            "hours_until": (c.due_date - now).total_seconds() / 3600,
        }
        for c in deadline_result.scalars().all()
    ]

    # Get active patterns
    patterns_result = await db.execute(
        select(Pattern).where(Pattern.is_active == True)
    )
    patterns = [
        {"type": p.pattern_type, "description": p.description, "severity": p.severity}
        for p in patterns_result.scalars().all()
    ]

    # Get days since last response
    last_response = await db.execute(
        select(CheckIn)
        .where(CheckIn.response_received == True)
        .order_by(CheckIn.responded_at.desc())
        .limit(1)
    )
    last_responded = last_response.scalar_one_or_none()
    days_since_response = 0
    if last_responded and last_responded.responded_at:
        days_since_response = (datetime.utcnow() - last_responded.responded_at).days

    # Calculate completion rate (last 30 days)
    month_ago = datetime.utcnow() - timedelta(days=30)
    total_result = await db.execute(
        select(func.count(Commitment.id)).where(Commitment.created_at > month_ago)
    )
    total_month = total_result.scalar() or 0

    completed_month_result = await db.execute(
        select(func.count(Commitment.id)).where(
            and_(
                Commitment.status == CommitmentStatus.COMPLETED,
                Commitment.completed_at > month_ago,
            )
        )
    )
    completed_month = completed_month_result.scalar() or 0
    completion_rate = (completed_month / total_month * 100) if total_month > 0 else 0

    # Get streak context
    streaks = await get_streak_context(db)

    # Get calendar context
    calendar_ctx = await calendar_service.get_calendar_context(db)

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
    }


async def daily_checkin_job():
    """Send daily morning check-in."""
    logger.info("Running daily check-in job")

    async with async_session_maker() as db:
        try:
            # Check if user is OOO today - skip check-in if so
            if await calendar_service.is_configured(db):
                if await calendar_service.is_ooo_today(db):
                    logger.info("User is OOO today, skipping daily check-in")
                    return

            # Check if response streak was broken
            await check_response_streak_broken(db)

            context = await get_context(db)

            # Generate message
            message = await generate_message("daily_checkin", context)

            # Send via Telegram
            msg_id = await telegram_service.send_check_in(message)

            # Record check-in
            checkin = CheckIn(
                check_in_type=CheckInType.DAILY,
                message_sent=message,
                telegram_message_id=msg_id,
            )
            db.add(checkin)

            # Save to chat history
            chat_msg = ChatMessage(
                role="warden",
                content=message,
                message_type="daily_checkin",
                telegram_message_id=msg_id,
            )
            db.add(chat_msg)

            # Run pattern detection
            detector = PatternDetector(db)
            new_patterns = await detector.run_detection()
            if new_patterns:
                logger.info(f"Detected {len(new_patterns)} new patterns")

            # Deactivate old patterns
            await detector.deactivate_old_patterns()

            await db.commit()
            logger.info("Daily check-in sent successfully")

        except Exception as e:
            logger.error(f"Daily check-in failed: {e}")
            await db.rollback()


async def weekly_review_job():
    """Send weekly review on Sunday evening, followed by planning prompt."""
    logger.info("Running weekly review job")

    async with async_session_maker() as db:
        try:
            # Update completion streak first
            streak_result = await update_completion_streak(db)
            logger.info(f"Completion streak updated: {streak_result}")

            context = await get_context(db)

            # Add weekly-specific stats
            week_ago = datetime.utcnow() - timedelta(days=7)

            # Weekly completions
            completed_result = await db.execute(
                select(func.count(Commitment.id)).where(
                    and_(
                        Commitment.status == CommitmentStatus.COMPLETED,
                        Commitment.completed_at > week_ago,
                    )
                )
            )
            context["weekly_completed"] = completed_result.scalar() or 0

            # Weekly failures/deferrals
            failed_result = await db.execute(
                select(func.count(Commitment.id)).where(
                    and_(
                        Commitment.status.in_(
                            [CommitmentStatus.FAILED, CommitmentStatus.DEFERRED]
                        ),
                        Commitment.updated_at > week_ago,
                    )
                )
            )
            context["weekly_failed"] = failed_result.scalar() or 0

            # Weekly response rate
            checkins_result = await db.execute(
                select(CheckIn).where(CheckIn.sent_at > week_ago)
            )
            checkins = checkins_result.scalars().all()
            if checkins:
                responded = sum(1 for c in checkins if c.response_received)
                context["weekly_response_rate"] = round(responded / len(checkins) * 100, 1)
            else:
                context["weekly_response_rate"] = 0

            # Generate review message (now includes planning prompt at the end)
            message = await generate_message("weekly_review", context)

            # Send via Telegram
            msg_id = await telegram_service.send_weekly_review(message)

            # Record check-in
            checkin = CheckIn(
                check_in_type=CheckInType.WEEKLY_REVIEW,
                message_sent=message,
                telegram_message_id=msg_id,
            )
            db.add(checkin)

            # Save to chat history
            chat_msg = ChatMessage(
                role="warden",
                content=message,
                message_type="weekly_review",
                telegram_message_id=msg_id,
            )
            db.add(chat_msg)

            await db.commit()

            logger.info("Weekly review sent successfully")

        except Exception as e:
            logger.error(f"Weekly review failed: {e}")
            await db.rollback()


async def silence_detector_job():
    """Check for unanswered check-ins and escalate."""
    logger.info("Running silence detector job")

    async with async_session_maker() as db:
        try:
            # Find last check-in
            last_checkin_result = await db.execute(
                select(CheckIn).order_by(CheckIn.sent_at.desc()).limit(1)
            )
            last_checkin = last_checkin_result.scalar_one_or_none()

            if not last_checkin:
                logger.info("No check-ins found, skipping silence detection")
                return

            # If last check-in was answered, no escalation needed
            if last_checkin.response_received:
                logger.info("Last check-in was answered, no escalation needed")
                return

            # Calculate hours since last check-in
            hours_since = (datetime.utcnow() - last_checkin.sent_at).total_seconds() / 3600

            if hours_since < settings.silence_threshold_hours:
                logger.info(f"Only {hours_since:.1f} hours since last check-in, under threshold")
                return

            # Check if we already escalated recently (within 12 hours)
            twelve_hours_ago = datetime.utcnow() - timedelta(hours=12)
            recent_escalation = await db.execute(
                select(CheckIn).where(
                    and_(
                        CheckIn.check_in_type == CheckInType.ESCALATION,
                        CheckIn.sent_at > twelve_hours_ago,
                    )
                )
            )
            if recent_escalation.scalar_one_or_none():
                logger.info("Already escalated recently, skipping")
                return

            # Time to escalate
            context = await get_context(db)
            context["hours_since_response"] = hours_since
            context["last_checkin_answered"] = False

            message = await generate_message("escalation", context)
            msg_id = await telegram_service.send_escalation(message)

            # Record escalation
            checkin = CheckIn(
                check_in_type=CheckInType.ESCALATION,
                message_sent=message,
                telegram_message_id=msg_id,
            )
            db.add(checkin)

            # Save to chat history
            chat_msg = ChatMessage(
                role="warden",
                content=message,
                message_type="escalation",
                telegram_message_id=msg_id,
            )
            db.add(chat_msg)

            await db.commit()

            logger.info(f"Escalation sent after {hours_since:.1f} hours of silence")

        except Exception as e:
            logger.error(f"Silence detector failed: {e}")
            await db.rollback()


async def commitment_reminder_job():
    """Send 90-minute reminders for upcoming commitment deadlines."""
    logger.info("Running commitment reminder job")

    async with async_session_maker() as db:
        try:
            import pytz
            tz = pytz.timezone(settings.timezone)
            now = datetime.now(tz)
            # Convert to naive UTC for database comparison
            now_utc = datetime.utcnow()

            # Find commitments due in the next 90-105 minutes (15-min window to catch them)
            reminder_start = now_utc + timedelta(minutes=75)
            reminder_end = now_utc + timedelta(minutes=105)

            result = await db.execute(
                select(Commitment).where(
                    and_(
                        Commitment.status == CommitmentStatus.PENDING,
                        Commitment.due_date.isnot(None),
                        Commitment.due_date >= reminder_start,
                        Commitment.due_date <= reminder_end,
                    )
                )
            )
            upcoming = result.scalars().all()

            for commitment in upcoming:
                # Check if we already sent a reminder for this commitment
                two_hours_ago = datetime.utcnow() - timedelta(hours=2)
                recent_reminder = await db.execute(
                    select(CheckIn).where(
                        and_(
                            CheckIn.check_in_type == CheckInType.DEADLINE_REMINDER,
                            CheckIn.sent_at > two_hours_ago,
                            CheckIn.message_sent.contains(commitment.title),
                        )
                    )
                )
                if recent_reminder.scalar_one_or_none():
                    continue

                # Calculate time until due
                minutes_until = (commitment.due_date - now_utc).total_seconds() / 60
                due_time_str = commitment.due_date.strftime('%I:%M %p').lstrip('0')

                # Generate a conversational reminder
                reminder_messages = [
                    f"Heads up - \"{commitment.title}\" is due at {due_time_str}. That's about 90 minutes from now. Where are you on this?",
                    f"Clock's ticking on \"{commitment.title}\" - due at {due_time_str}. You've got about 90 minutes. Status?",
                    f"Just checking in on \"{commitment.title}\" - it's coming up at {due_time_str}. Are you on track or do we need to talk about this?",
                ]
                import random
                message = random.choice(reminder_messages)

                msg_id = await telegram_service.send_message(message)

                # Record reminder
                checkin = CheckIn(
                    check_in_type=CheckInType.DEADLINE_REMINDER,
                    message_sent=message,
                    telegram_message_id=msg_id,
                )
                db.add(checkin)

                # Save to chat history
                chat_msg = ChatMessage(
                    role="warden",
                    content=message,
                    message_type="deadline_reminder",
                    telegram_message_id=msg_id,
                )
                db.add(chat_msg)

                logger.info(f"Sent 90-min reminder for: {commitment.title}")

            await db.commit()

        except Exception as e:
            logger.error(f"Commitment reminder failed: {e}")
            await db.rollback()


async def deadline_alert_job():
    """Check for upcoming deadlines and send alerts."""
    logger.info("Running deadline alert job")

    async with async_session_maker() as db:
        try:
            now = datetime.utcnow()
            deadline_cutoff = now + timedelta(hours=settings.deadline_alert_hours)

            # Find commitments with upcoming deadlines
            result = await db.execute(
                select(Commitment).where(
                    and_(
                        Commitment.status == CommitmentStatus.PENDING,
                        Commitment.due_date.isnot(None),
                        Commitment.due_date > now,
                        Commitment.due_date <= deadline_cutoff,
                    )
                )
            )
            upcoming = result.scalars().all()

            for commitment in upcoming:
                # Check if we already alerted for this commitment recently
                day_ago = datetime.utcnow() - timedelta(hours=24)
                recent_alert = await db.execute(
                    select(CheckIn).where(
                        and_(
                            CheckIn.check_in_type == CheckInType.DEADLINE_ALERT,
                            CheckIn.sent_at > day_ago,
                            CheckIn.message_sent.contains(commitment.title),
                        )
                    )
                )
                if recent_alert.scalar_one_or_none():
                    continue

                hours_until = (commitment.due_date - now).total_seconds() / 3600

                context = await get_context(db)
                context["deadline_commitment"] = {
                    "id": commitment.id,
                    "title": commitment.title,
                    "due_date": commitment.due_date.isoformat(),
                    "deferred_count": commitment.deferred_count,
                }
                context["hours_until_due"] = round(hours_until, 1)

                message = await generate_message("deadline_alert", context)
                msg_id = await telegram_service.send_deadline_alert(message)

                # Record alert
                checkin = CheckIn(
                    check_in_type=CheckInType.DEADLINE_ALERT,
                    message_sent=message,
                    telegram_message_id=msg_id,
                )
                db.add(checkin)

                # Save to chat history
                chat_msg = ChatMessage(
                    role="warden",
                    content=message,
                    message_type="deadline_alert",
                    telegram_message_id=msg_id,
                )
                db.add(chat_msg)

            await db.commit()
            logger.info(f"Processed {len(upcoming)} upcoming deadlines")

        except Exception as e:
            logger.error(f"Deadline alert failed: {e}")
            await db.rollback()


def setup_scheduler():
    """Configure and start the scheduler."""
    tz = pytz.timezone(settings.timezone)

    # Daily check-in at configured time
    scheduler.add_job(
        daily_checkin_job,
        CronTrigger(
            hour=settings.daily_checkin_hour,
            minute=settings.daily_checkin_minute,
            timezone=tz,
        ),
        id="daily_checkin",
        replace_existing=True,
    )
    logger.info(
        f"Scheduled daily check-in at {settings.daily_checkin_hour}:{settings.daily_checkin_minute:02d} {settings.timezone}"
    )

    # Weekly review on Sunday evening
    day_map = {"sun": 6, "mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5}
    day_of_week = day_map.get(settings.weekly_review_day.lower(), 6)

    scheduler.add_job(
        weekly_review_job,
        CronTrigger(
            day_of_week=day_of_week,
            hour=settings.weekly_review_hour,
            minute=settings.weekly_review_minute,
            timezone=tz,
        ),
        id="weekly_review",
        replace_existing=True,
    )
    logger.info(
        f"Scheduled weekly review on {settings.weekly_review_day} at {settings.weekly_review_hour}:{settings.weekly_review_minute:02d}"
    )

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

    scheduler.start()
    logger.info("Scheduler started")


def shutdown_scheduler():
    """Shutdown the scheduler gracefully."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler shutdown")


async def reschedule_jobs(config: dict):
    """Reschedule jobs with new configuration.

    Args:
        config: Dict with schedule configuration keys:
            - daily_checkin_hour
            - daily_checkin_minute
            - weekly_review_day
            - weekly_review_hour
            - weekly_review_minute
    """
    tz = pytz.timezone(settings.timezone)
    day_map = {"sun": 6, "mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5}

    # Reschedule daily check-in
    daily_hour = config.get("daily_checkin_hour", settings.daily_checkin_hour)
    daily_minute = config.get("daily_checkin_minute", settings.daily_checkin_minute)

    scheduler.reschedule_job(
        "daily_checkin",
        trigger=CronTrigger(
            hour=daily_hour,
            minute=daily_minute,
            timezone=tz,
        ),
    )
    logger.info(f"Rescheduled daily check-in to {daily_hour}:{daily_minute:02d}")

    # Reschedule weekly review
    weekly_day = config.get("weekly_review_day", settings.weekly_review_day)
    weekly_hour = config.get("weekly_review_hour", settings.weekly_review_hour)
    weekly_minute = config.get("weekly_review_minute", settings.weekly_review_minute)
    day_of_week = day_map.get(weekly_day.lower(), 6)

    scheduler.reschedule_job(
        "weekly_review",
        trigger=CronTrigger(
            day_of_week=day_of_week,
            hour=weekly_hour,
            minute=weekly_minute,
            timezone=tz,
        ),
    )
    logger.info(f"Rescheduled weekly review to {weekly_day} at {weekly_hour}:{weekly_minute:02d}")
