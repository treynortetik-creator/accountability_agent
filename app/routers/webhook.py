"""Telegram webhook router."""

import logging
from datetime import datetime
from fastapi import APIRouter, Request, HTTPException
from sqlalchemy import select, and_
from app.database import async_session_maker
from app.db_models import CheckIn, Response
from app.telegram_bot import parse_telegram_update, telegram_service
from app.llm import analyze_response
from app.scheduler import get_context

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["webhook"])


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
            # Find the most recent unanswered check-in
            recent_checkin = await db.execute(
                select(CheckIn)
                .where(CheckIn.response_received == False)
                .order_by(CheckIn.sent_at.desc())
                .limit(1)
            )
            checkin = recent_checkin.scalar_one_or_none()

            # Build context for analysis
            context = await get_context(db)

            # Calculate days since last shipped
            from app.db_models import Commitment, CommitmentStatus
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
            analysis = await analyze_response(parsed["text"], context)

            # Create response record
            response = Response(
                check_in_id=checkin.id if checkin else None,
                message_text=parsed["text"],
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

            await db.commit()

            # Send reply if the LLM generated one
            reply = analysis.get("reply")
            if reply:
                await telegram_service.send_message(reply)

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
