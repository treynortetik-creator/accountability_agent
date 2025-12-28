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

    message_text = parsed["text"]
    logger.info(f"Received message: {message_text[:50]}...")

    # STEP 1: Save user message IMMEDIATELY (separate transaction)
    # This ensures user messages are ALWAYS saved, even if processing fails
    async with async_session_maker() as db:
        try:
            # Update response streak
            await update_response_streak(db)

            # Save user message to chat history
            user_chat_msg = ChatMessage(
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
                logger.info("Handled pending confirmation")
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
                logger.info("Parsed and handled commitment")
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

            # Send reply - use fallback if LLM didn't generate one
            reply = analysis.get("reply")
            if not reply:
                # Fallback reply when LLM fails or returns no reply
                reply = "Got it. What's next on the list?"
                logger.warning("LLM returned no reply, using fallback")

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
            logger.error(f"Failed to process webhook: {e}", exc_info=True)
            await db.rollback()

            # Try to send an error acknowledgment to the user
            try:
                error_reply = "Message received. Had a hiccup processing it, but I've got it logged."
                msg_id = await telegram_service.send_message(error_reply)
                # Save the error reply in a new transaction
                async with async_session_maker() as error_db:
                    error_chat_msg = ChatMessage(
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
    from app.config import get_settings

    settings = get_settings()
    if not settings.telegram_bot_token:
        raise HTTPException(status_code=400, detail="Telegram bot token not configured")

    # Build webhook URL from request
    base_url = str(request.base_url)
    if base_url.startswith("http://") and "localhost" not in base_url and "127.0.0.1" not in base_url:
        base_url = base_url.replace("http://", "https://", 1)
    webhook_url = f"{base_url}webhook/telegram"

    # Call Telegram API to set webhook
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://api.telegram.org/bot{settings.telegram_bot_token}/setWebhook",
            json={"url": webhook_url}
        )
        result = response.json()

    if result.get("ok"):
        return {"status": "success", "webhook_url": webhook_url, "telegram_response": result}
    else:
        return {"status": "error", "error": result.get("description"), "webhook_url": webhook_url}


@router.get("/status")
async def webhook_status():
    """Check current webhook status with Telegram."""
    import httpx
    from app.config import get_settings

    settings = get_settings()
    if not settings.telegram_bot_token:
        raise HTTPException(status_code=400, detail="Telegram bot token not configured")

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.telegram.org/bot{settings.telegram_bot_token}/getWebhookInfo"
        )
        result = response.json()

    return result
