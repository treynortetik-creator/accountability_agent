"""Telegram webhook router."""

import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Request, HTTPException
from sqlalchemy import select, and_
from app.database import async_session_maker
from app.db_models import CheckIn, Response, ChatMessage, Commitment, PendingCommitmentParse, CheckInType
from app.telegram_bot import parse_telegram_update, telegram_service
from app.llm import analyze_response, parse_commitment
from app.scheduler import get_context
from app.streaks import update_response_streak

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["webhook"])


async def handle_pending_confirmation(db, message_text: str) -> tuple[bool, str | None]:
    """Check if user is confirming/rejecting a pending commitment parse.

    Returns (handled: bool, reply: str | None)
    """
    # Look for pending commitment parses
    result = await db.execute(
        select(PendingCommitmentParse).where(
            and_(
                PendingCommitmentParse.status == "pending",
                PendingCommitmentParse.expires_at > datetime.utcnow(),
            )
        ).order_by(PendingCommitmentParse.created_at.desc()).limit(1)
    )
    pending = result.scalar_one_or_none()

    if not pending:
        return False, None

    text_lower = message_text.lower().strip()

    # Check for confirmation
    if text_lower in ["yes", "y", "confirm", "correct", "yep", "yeah", "sure", "ok", "okay"]:
        # Create the commitment
        due_date = pending.parsed_due_date
        commitment = Commitment(
            title=pending.parsed_title,
            description=pending.parsed_description,
            due_date=due_date,
        )
        db.add(commitment)

        # Mark pending as confirmed
        pending.status = "confirmed"
        await db.flush()

        due_str = f" (due {due_date.strftime('%A, %b %d')})" if due_date else ""
        return True, f"Locked in: {pending.parsed_title}{due_str}. No excuses."

    # Check for rejection
    elif text_lower in ["no", "n", "wrong", "nope", "cancel", "nevermind", "never mind"]:
        pending.status = "rejected"
        await db.flush()
        return True, "Fine, dropped it. What did you actually mean?"

    # Not a confirmation response
    return False, None


async def try_parse_commitment(db, message_text: str, context: dict) -> tuple[bool, str | None]:
    """Try to parse a commitment from natural language.

    Returns (parsed: bool, reply: str | None)
    """
    # Parse the message
    parsed = await parse_commitment(message_text, context)

    if not parsed.get("is_commitment") or parsed.get("confidence", 0) < 0.6:
        return False, None

    # Create pending parse for confirmation
    due_date = None
    if parsed.get("due_date"):
        try:
            due_date = datetime.strptime(parsed["due_date"], "%Y-%m-%d")
        except ValueError:
            pass

    pending = PendingCommitmentParse(
        original_message=message_text,
        parsed_title=parsed["title"],
        parsed_due_date=due_date,
        parsed_description=parsed.get("description"),
        expires_at=datetime.utcnow() + timedelta(hours=1),
    )
    db.add(pending)
    await db.flush()

    # Build confirmation message
    due_str = f" by {due_date.strftime('%A, %b %d')}" if due_date else ""
    confirmation = f'Got it: "{parsed["title"]}"{due_str}. Confirm? (yes/no)'

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

    logger.info(f"Received message: {parsed['text'][:50]}...")

    async with async_session_maker() as db:
        try:
            message_text = parsed["text"]

            # Update response streak
            await update_response_streak(db)

            # Save user message to chat history first
            user_chat_msg = ChatMessage(
                role="user",
                content=message_text,
                message_type="reply",
                telegram_message_id=parsed["message_id"],
            )
            db.add(user_chat_msg)

            # Check if this is a confirmation response to a pending commitment
            handled, reply = await handle_pending_confirmation(db, message_text)
            if handled:
                if reply:
                    msg_id = await telegram_service.send_message(reply)
                    warden_chat_msg = ChatMessage(
                        role="warden",
                        content=reply,
                        message_type="commitment_confirm",
                        telegram_message_id=msg_id,
                    )
                    db.add(warden_chat_msg)
                await db.commit()
                return {"ok": True}

            # Build context for analysis
            context = await get_context(db)

            # Try to parse as a commitment first
            parsed_commitment, commit_reply = await try_parse_commitment(db, message_text, context)
            if parsed_commitment:
                if commit_reply:
                    msg_id = await telegram_service.send_message(commit_reply)
                    warden_chat_msg = ChatMessage(
                        role="warden",
                        content=commit_reply,
                        message_type="commitment_confirm",
                        telegram_message_id=msg_id,
                    )
                    db.add(warden_chat_msg)
                await db.commit()
                return {"ok": True}

            # Find the most recent unanswered check-in
            recent_checkin = await db.execute(
                select(CheckIn)
                .where(CheckIn.response_received == False)
                .order_by(CheckIn.sent_at.desc())
                .limit(1)
            )
            checkin = recent_checkin.scalar_one_or_none()

            # Calculate days since last shipped
            from app.db_models import CommitmentStatus
            from sqlalchemy import func

            last_shipped = await db.execute(
                select(Commitment)
                .where(Commitment.status == CommitmentStatus.COMPLETED)
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

            # Analyze the response using LLM
            analysis = await analyze_response(message_text, context)

            # Create response record
            response = Response(
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

            # Send reply if the LLM generated one
            reply = analysis.get("reply")
            if reply:
                msg_id = await telegram_service.send_message(reply)
                # Save warden reply to chat history
                warden_chat_msg = ChatMessage(
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
            logger.error(f"Failed to process webhook: {e}")
            await db.rollback()
            # Return OK anyway so Telegram doesn't retry
            return {"ok": True, "error": str(e)}


@router.get("/health")
async def webhook_health():
    """Health check for webhook endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
