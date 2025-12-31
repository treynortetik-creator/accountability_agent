"""Telegram webhook router."""

import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Request, HTTPException
from sqlalchemy import select, and_
from app.database import async_session_maker
from app.db_models import CheckIn, Response, ChatMessage, Commitment, PendingCommitmentParse, CheckInType, CommitmentStatus, Settings as SettingsModel, ScheduledFollowup, MoodLog, ErrorLog, User
from app.telegram_bot import parse_telegram_update, telegram_service
from app.llm import analyze_response, parse_commitment
from app.scheduler import get_context
from app.streaks import update_response_streak
from app.config import get_settings
from app.user_service import get_or_create_user
import re
import pytz

settings = get_settings()

logger = logging.getLogger(__name__)


async def try_handle_completion(db, message_text: str, user: User) -> tuple[bool, str | None]:
    """Check if user is marking a commitment as complete.

    Handles phrases like:
    - "done", "finished", "completed", "shipped"
    - "done with X", "finished X", "shipped X"
    - "I finished the blog post"

    Returns (handled: bool, reply: str | None)
    """
    text_lower = message_text.lower().strip()

    # Simple completion phrases (marks most recent pending commitment)
    simple_completions = ["done", "finished", "completed", "shipped", "did it", "got it done"]

    # Check for simple completion
    is_simple_completion = text_lower in simple_completions

    # Check for completion with subject (e.g., "done with X", "finished X", "shipped the blog post")
    completion_patterns = [
        r"^(?:done|finished|completed|shipped)(?: with)?\s+(.+)$",
        r"^i (?:finished|completed|shipped|did)\s+(?:the\s+)?(.+)$",
        r"^(?:the\s+)?(.+)\s+is (?:done|finished|completed|shipped)$",
    ]

    subject = None
    for pattern in completion_patterns:
        match = re.match(pattern, text_lower)
        if match:
            subject = match.group(1).strip()
            break

    if not is_simple_completion and not subject:
        return False, None

    # Find the commitment to mark as complete
    if subject:
        # Try to find a commitment matching the subject
        result = await db.execute(
            select(Commitment).where(
                and_(
                    Commitment.user_id == user.id,
                    Commitment.status == CommitmentStatus.PENDING,
                    Commitment.title.ilike(f"%{subject}%"),
                )
            ).order_by(Commitment.created_at.desc()).limit(1)
        )
        commitment = result.scalar_one_or_none()

        if not commitment:
            # No matching commitment found, try fuzzy match on most recent
            result = await db.execute(
                select(Commitment).where(
                    Commitment.user_id == user.id,
                    Commitment.status == CommitmentStatus.PENDING
                ).order_by(Commitment.created_at.desc()).limit(5)
            )
            pending = result.scalars().all()

            # Simple word overlap check
            subject_words = set(subject.lower().split())
            for c in pending:
                title_words = set(c.title.lower().split())
                if subject_words & title_words:  # Any overlap
                    commitment = c
                    break

        if not commitment:
            return True, f"I don't see a commitment matching \"{subject}\". What exactly did you finish?"
    else:
        # Simple "done" - mark most recent pending commitment
        result = await db.execute(
            select(Commitment).where(
                Commitment.user_id == user.id,
                Commitment.status == CommitmentStatus.PENDING
            ).order_by(Commitment.due_date.asc().nullslast(), Commitment.created_at.desc()).limit(1)
        )
        commitment = result.scalar_one_or_none()

        if not commitment:
            return True, "Done with what? I don't see any pending commitments."

    # Mark as complete
    commitment.status = CommitmentStatus.COMPLETED
    commitment.completed_at = datetime.utcnow()
    await db.flush()

    # Generate an enthusiastic acknowledgment
    import random
    acknowledgments = [
        f"Hell yes! \"{commitment.title}\" is done! That's what I'm talking about. What's next?",
        f"Boom! \"{commitment.title}\" - shipped. Achievement unlocked. What else we killing today?",
        f"Nice! \"{commitment.title}\" is off the board. You're on a fucking roll. What's next?",
        f"\"{commitment.title}\" - done. *chef's kiss* What's the next quest?",
        f"LFG! \"{commitment.title}\" complete. The Force is strong with you today. What's next?",
    ]
    reply = random.choice(acknowledgments)

    return True, reply

router = APIRouter(prefix="/webhook", tags=["webhook"])


async def handle_pending_confirmation(db, message_text: str, user: User) -> tuple[bool, str | None]:
    """Check if user is confirming/rejecting a pending commitment parse.

    Returns (handled: bool, reply: str | None)
    """
    import json as json_module

    # Look for pending commitment parses
    result = await db.execute(
        select(PendingCommitmentParse).where(
            and_(
                PendingCommitmentParse.user_id == user.id,
                PendingCommitmentParse.status.in_(["pending", "breakdown_pending"]),
                PendingCommitmentParse.expires_at > datetime.utcnow(),
            )
        ).order_by(PendingCommitmentParse.created_at.desc()).limit(1)
    )
    pending = result.scalar_one_or_none()

    if not pending:
        return False, None

    text_lower = message_text.lower().strip()

    # Check for breakdown request (for large commitments)
    breakdown_phrases = ["break it down", "break it up", "smaller pieces", "break down", "split it", "decompose"]
    if pending.is_large and pending.suggested_breakdown and any(phrase in text_lower for phrase in breakdown_phrases):
        # Parse the breakdown suggestions
        try:
            breakdown_steps = json_module.loads(pending.suggested_breakdown)
        except:
            breakdown_steps = []

        if breakdown_steps:
            # Create sub-commitments for each step
            base_due = pending.parsed_due_date
            created_titles = []

            for i, step in enumerate(breakdown_steps):
                # Spread deadlines if there's a due date
                step_due = None
                if base_due and len(breakdown_steps) > 1:
                    # Distribute evenly before the main deadline
                    days_before = (len(breakdown_steps) - i) * 1  # 1 day per step
                    step_due = base_due - timedelta(days=days_before)
                    if step_due < datetime.utcnow():
                        step_due = datetime.utcnow() + timedelta(hours=i+1)  # At least stagger by hour

                commitment = Commitment(
                    user_id=user.id,
                    title=step,
                    description=f"Part of: {pending.parsed_title}",
                    due_date=step_due,
                    status=CommitmentStatus.PENDING,  # Explicitly set status
                )
                db.add(commitment)
                created_titles.append(step)

            pending.status = "confirmed"
            await db.commit()  # Commit immediately to persist
            logger.info(f"Created {len(created_titles)} breakdown commitments for: {pending.parsed_title}")

            titles_str = "\n".join(f"• {t}" for t in created_titles)
            return True, f"Done. I've broken \"{pending.parsed_title}\" into {len(created_titles)} steps:\n{titles_str}\n\nI'll track each one. Start with the first."

        # Fallback if no breakdown available
        return True, "I suggested breaking it down but don't have specific steps. Want to tell me how you'd split it?"

    # Check for confirmation
    if text_lower in ["yes", "y", "confirm", "correct", "yep", "yeah", "sure", "ok", "okay"]:
        # Create the commitment
        due_date = pending.parsed_due_date
        commitment = Commitment(
            user_id=user.id,
            title=pending.parsed_title,
            description=pending.parsed_description,
            due_date=due_date,
            status=CommitmentStatus.PENDING,  # Explicitly set status
        )
        db.add(commitment)

        # Mark pending as confirmed
        pending.status = "confirmed"
        await db.commit()  # Commit immediately to persist
        logger.info(f"Created commitment: {pending.parsed_title} (id={commitment.id})")

        if due_date:
            due_str = due_date.strftime('%A, %b %d')
            if due_date.hour != 0 or due_date.minute != 0:
                due_str += due_date.strftime(' at %I:%M %p').replace(' 0', ' ').lstrip('0')
            return True, f"Locked in! \"{pending.parsed_title}\" by {due_str}. You got this."
        else:
            return True, f"Done! \"{pending.parsed_title}\" is on the board. When do you think you'll knock this out?"

    # Check for rejection
    elif text_lower in ["no", "n", "wrong", "nope", "cancel", "nevermind", "never mind"]:
        pending.status = "rejected"
        await db.flush()
        return True, "No worries, scrapped. What were you actually going for?"

    # Not a confirmation response
    return False, None


async def try_parse_commitment(db, message_text: str, context: dict, user: User) -> tuple[bool, str | None]:
    """Try to parse a commitment from natural language.

    Returns (parsed: bool, reply: str | None)
    """
    # Parse the message
    parsed = await parse_commitment(message_text, context)

    if not parsed.get("is_commitment") or parsed.get("confidence", 0) < 0.6:
        return False, None

    # Create pending parse for confirmation
    # Parse date and time, defaulting to 12 PM if no time specified
    due_datetime = None
    if parsed.get("due_date"):
        try:
            due_datetime = datetime.strptime(parsed["due_date"], "%Y-%m-%d")

            # Handle time - default to 12:00 PM if not specified
            if parsed.get("due_time"):
                try:
                    time_parts = parsed["due_time"].split(":")
                    hour = int(time_parts[0])
                    minute = int(time_parts[1]) if len(time_parts) > 1 else 0
                    due_datetime = due_datetime.replace(hour=hour, minute=minute)
                except (ValueError, IndexError):
                    # If time parsing fails, default to 12 PM
                    due_datetime = due_datetime.replace(hour=12, minute=0)
            else:
                # No time specified, default to 12 PM
                due_datetime = due_datetime.replace(hour=12, minute=0)
        except ValueError:
            pass

    # Store breakdown info if this is a large commitment
    breakdown_json = None
    if parsed.get("is_large") and parsed.get("suggested_breakdown"):
        import json as json_module
        breakdown_json = json_module.dumps(parsed["suggested_breakdown"])

    pending = PendingCommitmentParse(
        user_id=user.id,
        original_message=message_text,
        parsed_title=parsed["title"],
        parsed_due_date=due_datetime,
        parsed_description=parsed.get("description"),
        suggested_breakdown=breakdown_json,
        is_large=parsed.get("is_large", False),
        expires_at=datetime.utcnow() + timedelta(hours=1),
    )
    db.add(pending)
    await db.flush()

    # Build conversational confirmation message
    if due_datetime:
        due_str = due_datetime.strftime('%A, %b %d')
        time_str = due_datetime.strftime('%I:%M %p').lstrip('0').replace(' 0', ' ')
        due_str += f" at {time_str}"
        confirmation = f'Cool, so "{parsed["title"]}" by {due_str}? Say yes and it\'s locked in.'
    else:
        confirmation = f'Got it - "{parsed["title"]}". No deadline though. Want me to track this one? (yes/no)'

    return True, confirmation


@router.post("/telegram")
async def telegram_webhook(request: Request):
    """Handle incoming Telegram messages."""
    try:
        update_data = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse webhook request: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # Parse the update
    parsed = parse_telegram_update(update_data)
    if not parsed:
        # Not a valid message for us, return OK anyway
        return {"ok": True}

    message_text = parsed["text"]
    chat_id = str(parsed.get("chat_id", ""))
    display_name = parsed.get("first_name") or parsed.get("username")
    logger.info(f"Received message from {chat_id}: {message_text[:50]}...")

    # STEP 1: Save user message IMMEDIATELY (separate transaction)
    # This ensures user messages are ALWAYS saved, even if processing fails
    async with async_session_maker() as db:
        try:
            # Get or create user from Telegram chat_id
            user = await get_or_create_user(db, chat_id, display_name)

            # Update response streak
            await update_response_streak(db, user)

            # Save user message to chat history
            user_chat_msg = ChatMessage(
                user_id=user.id,
                role="user",
                content=message_text,
                message_type="reply",
                telegram_message_id=parsed["message_id"],
            )
            db.add(user_chat_msg)
            await db.commit()
            logger.info(f"Saved user message to chat history: {parsed['message_id']}")
        except Exception as e:
            logger.error(f"Failed to save user message: {e}")
            # Continue processing anyway - we want to try to respond

    # STEP 2: Process the message and generate response (separate transaction)
    async with async_session_maker() as db:
        try:
            # Get user for this transaction
            user = await get_or_create_user(db, chat_id, display_name)

            # Check if user is marking a commitment as complete
            handled, reply = await try_handle_completion(db, message_text, user)
            if handled:
                if reply:
                    msg_id = await telegram_service.send_message(reply, ignore_quiet_hours=True)
                    warden_chat_msg = ChatMessage(
                        user_id=user.id,
                        role="warden",
                        content=reply,
                        message_type="completion_confirm",
                        telegram_message_id=msg_id,
                    )
                    db.add(warden_chat_msg)
                await db.commit()
                logger.info("Handled commitment completion")
                return {"ok": True}

            # Check if this is a confirmation response to a pending commitment
            handled, reply = await handle_pending_confirmation(db, message_text, user)
            if handled:
                if reply:
                    # Always respond to user messages, even during quiet hours
                    msg_id = await telegram_service.send_message(reply, ignore_quiet_hours=True)
                    warden_chat_msg = ChatMessage(
                        user_id=user.id,
                        role="warden",
                        content=reply,
                        message_type="commitment_confirm",
                        telegram_message_id=msg_id,
                    )
                    db.add(warden_chat_msg)
                await db.commit()
                logger.info("Handled pending confirmation")
                return {"ok": True}

            # Build context for analysis
            context = await get_context(db, user)

            # Try to parse as a commitment first
            parsed_commitment, commit_reply = await try_parse_commitment(db, message_text, context, user)
            if parsed_commitment:
                if commit_reply:
                    # Always respond to user messages, even during quiet hours
                    msg_id = await telegram_service.send_message(commit_reply, ignore_quiet_hours=True)
                    warden_chat_msg = ChatMessage(
                        user_id=user.id,
                        role="warden",
                        content=commit_reply,
                        message_type="commitment_confirm",
                        telegram_message_id=msg_id,
                    )
                    db.add(warden_chat_msg)
                await db.commit()
                logger.info("Parsed and handled commitment")
                return {"ok": True}

            # Find the most recent unanswered check-in for this user
            recent_checkin = await db.execute(
                select(CheckIn)
                .where(CheckIn.user_id == user.id, CheckIn.response_received == False)
                .order_by(CheckIn.sent_at.desc())
                .limit(1)
            )
            checkin = recent_checkin.scalar_one_or_none()

            # Calculate days since last shipped for this user
            from app.db_models import CommitmentStatus

            last_shipped = await db.execute(
                select(Commitment)
                .where(Commitment.user_id == user.id, Commitment.status == CommitmentStatus.COMPLETED)
                .order_by(Commitment.completed_at.desc())
                .limit(1)
            )
            last_shipped_commitment = last_shipped.scalar_one_or_none()
            if last_shipped_commitment and last_shipped_commitment.completed_at:
                days_since_shipped = (
                    datetime.utcnow() - last_shipped_commitment.completed_at
                ).days
            else:
                days_since_shipped = "never"
            context["days_since_shipped"] = days_since_shipped

            # Fetch recent chat history for context (for this user)
            chat_history_result = await db.execute(
                select(ChatMessage)
                .where(ChatMessage.user_id == user.id)
                .order_by(ChatMessage.created_at.desc())
                .limit(20)
            )
            chat_messages = list(reversed(chat_history_result.scalars().all()))
            chat_history = [
                {"role": msg.role, "content": msg.content}
                for msg in chat_messages
            ]

            # Analyze the response using LLM (with chat history)
            analysis = await analyze_response(message_text, context, chat_history)

            # Process memory update if provided
            memory_update = analysis.get("memory_update")
            if memory_update:
                # Handle both old format (string) and new format (dict with action)
                memory_result = await db.execute(
                    select(SettingsModel).where(
                        SettingsModel.user_id == user.id,
                        SettingsModel.key == "llm_memory"
                    )
                )
                memory_setting = memory_result.scalar_one_or_none()
                current_memory = memory_setting.value if memory_setting else ""

                if isinstance(memory_update, str) and memory_update.strip():
                    # Old format - treat as replace for backwards compatibility
                    new_memory = memory_update.strip()
                elif isinstance(memory_update, dict):
                    action = memory_update.get("action", "replace")
                    content = memory_update.get("content", "").strip()

                    if action == "append" and content:
                        # Add to existing memory with a newline separator
                        if current_memory:
                            new_memory = f"{current_memory}\n{content}"
                        else:
                            new_memory = content
                        logger.info(f"Appending to memory: {content[:50]}...")
                    elif action == "remove" and content:
                        # Remove specific content from memory
                        new_memory = current_memory.replace(content, "").strip()
                        # Clean up any double newlines
                        while "\n\n\n" in new_memory:
                            new_memory = new_memory.replace("\n\n\n", "\n\n")
                        logger.info(f"Removed from memory: {content[:50]}...")
                    elif action == "replace" and content:
                        # Full replacement
                        new_memory = content
                        logger.info("Replacing entire memory")
                    else:
                        new_memory = None
                else:
                    new_memory = None

                if new_memory is not None:
                    if memory_setting:
                        memory_setting.value = new_memory
                    else:
                        db.add(SettingsModel(user_id=user.id, key="llm_memory", value=new_memory))
                    logger.info("LLM memory updated")

            # Process scheduled follow-up if provided
            followup = analysis.get("schedule_followup")
            if followup and isinstance(followup, dict) and followup.get("topic"):
                # Parse the "when" field into a datetime
                tz = pytz.timezone(settings.timezone)  # Use configured timezone
                now = datetime.now(tz)
                when_str = followup.get("when", "tomorrow").lower()

                # Simple parsing for common patterns
                scheduled_time = now + timedelta(days=1)  # Default to tomorrow
                scheduled_time = scheduled_time.replace(hour=10, minute=0, second=0, microsecond=0)

                if "tonight" in when_str or "this evening" in when_str:
                    scheduled_time = now.replace(hour=19, minute=0, second=0, microsecond=0)
                    if scheduled_time <= now:
                        scheduled_time += timedelta(days=1)
                elif "tomorrow morning" in when_str:
                    scheduled_time = (now + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
                elif "tomorrow evening" in when_str or "tomorrow night" in when_str:
                    scheduled_time = (now + timedelta(days=1)).replace(hour=19, minute=0, second=0, microsecond=0)
                elif "in 2 days" in when_str or "in two days" in when_str:
                    scheduled_time = (now + timedelta(days=2)).replace(hour=10, minute=0, second=0, microsecond=0)
                elif "next week" in when_str:
                    scheduled_time = (now + timedelta(days=7)).replace(hour=10, minute=0, second=0, microsecond=0)
                elif "in a few hours" in when_str or "later today" in when_str:
                    scheduled_time = now + timedelta(hours=3)

                # Convert to UTC for storage
                scheduled_time_utc = scheduled_time.astimezone(pytz.UTC).replace(tzinfo=None)

                db.add(ScheduledFollowup(
                    user_id=user.id,
                    topic=followup["topic"],
                    reason=followup.get("reason"),
                    scheduled_time=scheduled_time_utc,
                ))
                logger.info(f"Scheduled follow-up on '{followup['topic']}' for {scheduled_time}")

            # Process mood assessment if provided
            mood = analysis.get("mood_assessment")
            if mood and isinstance(mood, dict):
                mood_score = mood.get("mood_score")
                energy_level = mood.get("energy_level")
                # Convert energy_level to string if it's an integer
                # Map: 1-2 = low, 3-4 = medium, 5 = high
                if isinstance(energy_level, int):
                    if energy_level <= 2:
                        energy_level = "low"
                    elif energy_level <= 4:
                        energy_level = "medium"
                    else:
                        energy_level = "high"
                elif energy_level is not None:
                    energy_level = str(energy_level)
                if mood_score or energy_level:
                    db.add(MoodLog(
                        user_id=user.id,
                        mood_score=mood_score,
                        energy_level=energy_level,
                        detected_from="llm_analysis",
                        notes=mood.get("notes"),
                    ))
                    logger.info(f"Logged mood: score={mood_score}, energy={energy_level}")

            # Process intensity adjustment if suggested
            suggested_intensity = analysis.get("suggested_intensity")
            if suggested_intensity and isinstance(suggested_intensity, int) and 1 <= suggested_intensity <= 5:
                intensity_result = await db.execute(
                    select(SettingsModel).where(
                        SettingsModel.user_id == user.id,
                        SettingsModel.key == "accountability_intensity"
                    )
                )
                intensity_setting = intensity_result.scalar_one_or_none()
                if intensity_setting:
                    current = int(intensity_setting.value)
                    if current != suggested_intensity:
                        intensity_setting.value = str(suggested_intensity)
                        logger.info(f"Adjusted accountability intensity: {current} -> {suggested_intensity}")
                else:
                    db.add(SettingsModel(user_id=user.id, key="accountability_intensity", value=str(suggested_intensity)))
                    logger.info(f"Set accountability intensity to {suggested_intensity}")

            # Create response record
            response = Response(
                user_id=user.id,
                check_in_id=checkin.id if checkin else None,
                message_text=message_text,
                telegram_message_id=parsed["message_id"],
                received_at=parsed.get("timestamp", datetime.utcnow()),
                detected_shipped=analysis.get("shipped"),
                detected_excuse=analysis.get("excuse"),
                detected_avoidance=analysis.get("avoidance"),
                analysis_notes=analysis.get("notes"),
            )
            db.add(response)

            # Mark check-in as responded if we found one
            if checkin:
                checkin.response_received = True
                checkin.responded_at = datetime.utcnow()

            # Send reply - use fallback if LLM didn't generate one
            reply = analysis.get("reply")
            if not reply:
                # Fallback reply when LLM fails or returns no reply
                reply = "Got it. What's next on the list?"
                logger.warning("LLM returned no reply, using fallback")

            # Always respond to user messages, even during quiet hours
            msg_id = await telegram_service.send_message(reply, ignore_quiet_hours=True)
            # Save warden reply to chat history
            warden_chat_msg = ChatMessage(
                user_id=user.id,
                role="warden",
                content=reply,
                message_type="reply",
                telegram_message_id=msg_id,
            )
            db.add(warden_chat_msg)

            await db.commit()

            logger.info("Processed incoming message successfully")
            return {"ok": True}

        except Exception as e:
            import traceback
            import json as json_module

            error_trace = traceback.format_exc()
            logger.error(f"Failed to process webhook: {e}", exc_info=True)
            await db.rollback()

            # Log the error to database for UI visibility
            try:
                async with async_session_maker() as error_db:
                    # Try to get user for error logging (may fail if user was the issue)
                    error_user = None
                    try:
                        error_user = await get_or_create_user(error_db, chat_id, display_name)
                    except Exception:
                        pass  # Log error without user_id

                    error_log = ErrorLog(
                        user_id=error_user.id if error_user else None,
                        error_type=type(e).__name__,
                        error_message=str(e),
                        stack_trace=error_trace,
                        context=json_module.dumps({
                            "message_id": parsed.get("message_id") if parsed else None,
                            "chat_id": parsed.get("chat_id") if parsed else None,
                        }),
                        source="webhook",
                        user_message=message_text,
                    )
                    error_db.add(error_log)
                    await error_db.commit()
                    logger.info(f"Error logged to database: {error_log.id}")
            except Exception as log_error:
                logger.error(f"Failed to log error to database: {log_error}")

            # Try to send an error acknowledgment to the user
            try:
                error_reply = "Message received. Had a hiccup processing it, but I've got it logged."
                # Always respond to user messages, even during quiet hours
                msg_id = await telegram_service.send_message(error_reply, ignore_quiet_hours=True)
                # Save the error reply in a new transaction
                async with async_session_maker() as error_db:
                    # Try to get user for chat message logging
                    error_user = None
                    try:
                        error_user = await get_or_create_user(error_db, chat_id, display_name)
                    except Exception:
                        pass  # Log without user_id

                    error_chat_msg = ChatMessage(
                        user_id=error_user.id if error_user else None,
                        role="warden",
                        content=error_reply,
                        message_type="error",
                        telegram_message_id=msg_id,
                    )
                    error_db.add(error_chat_msg)
                    await error_db.commit()
            except Exception as send_error:
                logger.error(f"Failed to send error reply: {send_error}")

            # Return OK so Telegram doesn't retry
            return {"ok": True, "error": str(e)}


@router.get("/health")
async def webhook_health():
    """Health check for webhook endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@router.post("/setup")
async def setup_webhook(request: Request):
    """Register webhook URL with Telegram."""
    import httpx
    import json as json_module
    import asyncio

    if not settings.telegram_bot_token:
        raise HTTPException(status_code=400, detail="Telegram bot token not configured")

    # Build webhook URL from request
    base_url = str(request.base_url)
    if base_url.startswith("http://") and "localhost" not in base_url and "127.0.0.1" not in base_url:
        base_url = base_url.replace("http://", "https://", 1)
    webhook_url = f"{base_url}webhook/telegram"

    logger.info(f"Setting up webhook with URL: {webhook_url}")

    # Retry logic for Railway's flaky network to Telegram
    max_retries = 3
    last_error = None

    for attempt in range(max_retries):
        try:
            # Use longer timeout (60s) for Railway's network latency
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"https://api.telegram.org/bot{settings.telegram_bot_token}/setWebhook",
                    json={"url": webhook_url}
                )
                result = response.json()

            if result.get("ok"):
                logger.info(f"Webhook setup successful: {webhook_url}")
                return {"status": "success", "webhook_url": webhook_url, "telegram_response": result}
            else:
                error_msg = result.get("description", "Unknown error")
                logger.error(f"Telegram rejected webhook setup: {error_msg}")
                await _log_webhook_error("WebhookSetupError", error_msg, {"webhook_url": webhook_url, "telegram_response": result})
                return {"status": "error", "error": error_msg, "webhook_url": webhook_url, "telegram_response": result}

        except httpx.TimeoutException as e:
            last_error = e
            logger.warning(f"Webhook setup timeout (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2.0 * (attempt + 1))  # Exponential backoff
            continue

        except httpx.RequestError as e:
            last_error = e
            logger.warning(f"Webhook setup network error (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2.0 * (attempt + 1))
            continue

        except Exception as e:
            error_msg = f"Unexpected error during webhook setup: {str(e)}"
            logger.error(error_msg, exc_info=True)
            await _log_webhook_error("WebhookSetupError", error_msg, {"webhook_url": webhook_url})
            return {"status": "error", "error": error_msg, "webhook_url": webhook_url}

    # All retries failed
    error_msg = f"Webhook setup failed after {max_retries} retries: {last_error}"
    logger.error(error_msg)
    await _log_webhook_error("WebhookSetupTimeout", error_msg, {"webhook_url": webhook_url, "retries": max_retries})
    return {"status": "error", "error": error_msg, "webhook_url": webhook_url}


async def _log_webhook_error(error_type: str, error_message: str, context: dict):
    """Log webhook errors to the database for UI visibility."""
    import json as json_module
    try:
        async with async_session_maker() as db:
            error_log = ErrorLog(
                error_type=error_type,
                error_message=error_message,
                context=json_module.dumps(context),
                source="webhook_setup",
                user_message=None,
            )
            db.add(error_log)
            await db.commit()
            logger.info(f"Logged webhook error to database: {error_type}")
    except Exception as log_error:
        logger.error(f"Failed to log webhook error to database: {log_error}")


@router.get("/status")
async def webhook_status():
    """Check current webhook status with Telegram."""
    import httpx
    import asyncio

    if not settings.telegram_bot_token:
        raise HTTPException(status_code=400, detail="Telegram bot token not configured")

    # Retry logic for Railway's flaky network
    max_retries = 3
    last_error = None

    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(
                    f"https://api.telegram.org/bot{settings.telegram_bot_token}/getWebhookInfo"
                )
                result = response.json()

            # Log any pending errors from Telegram
            if result.get("result", {}).get("last_error_message"):
                last_error_msg = result["result"]["last_error_message"]
                last_error_date = result["result"].get("last_error_date")
                logger.warning(f"Telegram webhook has pending error: {last_error_msg} (at {last_error_date})")
                await _log_webhook_error(
                    "WebhookDeliveryError",
                    last_error_msg,
                    {"last_error_date": last_error_date, "webhook_url": result["result"].get("url")}
                )

            return result

        except httpx.TimeoutException as e:
            last_error = e
            logger.warning(f"Webhook status timeout (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2.0 * (attempt + 1))
            continue

        except httpx.RequestError as e:
            last_error = e
            logger.warning(f"Webhook status network error (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2.0 * (attempt + 1))
            continue

        except Exception as e:
            error_msg = f"Unexpected error checking webhook status: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {"ok": False, "error": error_msg}

    # All retries failed
    error_msg = f"Webhook status check failed after {max_retries} retries: {last_error}"
    logger.error(error_msg)
    return {"ok": False, "error": error_msg}
