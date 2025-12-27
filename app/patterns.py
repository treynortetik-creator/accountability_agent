"""Pattern detection for The Warden."""

import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.db_models import (
    Commitment,
    CommitmentStatus,
    CheckIn,
    Response,
    Pattern,
)

logger = logging.getLogger(__name__)


class PatternDetector:
    """Detects behavioral patterns from user data."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def run_detection(self) -> List[Dict[str, Any]]:
        """Run all pattern detection algorithms.

        Returns list of newly detected patterns.
        """
        detected = []

        # Run each detection
        detected.extend(await self._detect_avoidance_pattern())
        detected.extend(await self._detect_silence_pattern())
        detected.extend(await self._detect_excuse_pattern())
        detected.extend(await self._detect_deferral_pattern())
        detected.extend(await self._detect_consistency_pattern())

        return detected

    async def _detect_avoidance_pattern(self) -> List[Dict[str, Any]]:
        """Detect when user is avoiding hard/tedious tasks."""
        detected = []

        # Look for commitments that have been pending for a long time
        week_ago = datetime.utcnow() - timedelta(days=7)
        result = await self.db.execute(
            select(Commitment).where(
                and_(
                    Commitment.status == CommitmentStatus.PENDING,
                    Commitment.created_at < week_ago,
                )
            )
        )
        old_pending = result.scalars().all()

        if len(old_pending) >= 3:
            # Check if this pattern was already detected recently
            recent_check = datetime.utcnow() - timedelta(days=3)
            existing = await self.db.execute(
                select(Pattern).where(
                    and_(
                        Pattern.pattern_type == "avoidance",
                        Pattern.detected_at > recent_check,
                        Pattern.is_active == True,
                    )
                )
            )
            if not existing.scalar_one_or_none():
                titles = [c.title for c in old_pending[:5]]
                pattern = Pattern(
                    pattern_type="avoidance",
                    description=f"Avoiding {len(old_pending)} tasks for over a week",
                    evidence=json.dumps({"stale_commitments": titles}),
                    severity=min(len(old_pending), 5),
                )
                self.db.add(pattern)
                detected.append({
                    "type": "avoidance",
                    "description": pattern.description,
                    "severity": pattern.severity,
                })

        return detected

    async def _detect_silence_pattern(self) -> List[Dict[str, Any]]:
        """Detect when user is going silent on check-ins."""
        detected = []

        # Count unanswered check-ins in the last week
        week_ago = datetime.utcnow() - timedelta(days=7)
        result = await self.db.execute(
            select(CheckIn).where(
                and_(
                    CheckIn.sent_at > week_ago,
                    CheckIn.response_received == False,
                )
            )
        )
        unanswered = result.scalars().all()

        total_result = await self.db.execute(
            select(func.count(CheckIn.id)).where(CheckIn.sent_at > week_ago)
        )
        total_recent = total_result.scalar() or 0

        if total_recent >= 3 and len(unanswered) >= total_recent * 0.5:
            # More than 50% unanswered
            recent_check = datetime.utcnow() - timedelta(days=3)
            existing = await self.db.execute(
                select(Pattern).where(
                    and_(
                        Pattern.pattern_type == "silence",
                        Pattern.detected_at > recent_check,
                        Pattern.is_active == True,
                    )
                )
            )
            if not existing.scalar_one_or_none():
                pattern = Pattern(
                    pattern_type="silence",
                    description=f"Ignoring check-ins: {len(unanswered)}/{total_recent} unanswered this week",
                    evidence=json.dumps({
                        "unanswered_count": len(unanswered),
                        "total_count": total_recent,
                    }),
                    severity=min(len(unanswered), 5),
                )
                self.db.add(pattern)
                detected.append({
                    "type": "silence",
                    "description": pattern.description,
                    "severity": pattern.severity,
                })

        return detected

    async def _detect_excuse_pattern(self) -> List[Dict[str, Any]]:
        """Detect when user is making too many excuses."""
        detected = []

        # Count responses flagged as excuses in last 2 weeks
        two_weeks_ago = datetime.utcnow() - timedelta(days=14)
        result = await self.db.execute(
            select(func.count(Response.id)).where(
                and_(
                    Response.received_at > two_weeks_ago,
                    Response.detected_excuse == True,
                )
            )
        )
        excuse_count = result.scalar() or 0

        if excuse_count >= 5:
            recent_check = datetime.utcnow() - timedelta(days=7)
            existing = await self.db.execute(
                select(Pattern).where(
                    and_(
                        Pattern.pattern_type == "excuse",
                        Pattern.detected_at > recent_check,
                        Pattern.is_active == True,
                    )
                )
            )
            if not existing.scalar_one_or_none():
                pattern = Pattern(
                    pattern_type="excuse",
                    description=f"Making excuses: {excuse_count} excuse-laden responses in 2 weeks",
                    evidence=json.dumps({"excuse_count": excuse_count}),
                    severity=min(excuse_count // 2, 5),
                )
                self.db.add(pattern)
                detected.append({
                    "type": "excuse",
                    "description": pattern.description,
                    "severity": pattern.severity,
                })

        return detected

    async def _detect_deferral_pattern(self) -> List[Dict[str, Any]]:
        """Detect when user is deferring the same tasks repeatedly."""
        detected = []

        # Find commitments deferred multiple times
        result = await self.db.execute(
            select(Commitment).where(Commitment.deferred_count >= 2)
        )
        chronic_deferrals = result.scalars().all()

        if chronic_deferrals:
            for commitment in chronic_deferrals:
                if commitment.deferred_count >= 3:
                    # Check for existing pattern on this commitment
                    existing = await self.db.execute(
                        select(Pattern).where(
                            and_(
                                Pattern.pattern_type == "deferral",
                                Pattern.evidence.contains(str(commitment.id)),
                                Pattern.is_active == True,
                            )
                        )
                    )
                    if not existing.scalar_one_or_none():
                        pattern = Pattern(
                            pattern_type="deferral",
                            description=f"Serial deferral: '{commitment.title}' deferred {commitment.deferred_count} times",
                            evidence=json.dumps({
                                "commitment_id": commitment.id,
                                "commitment_title": commitment.title,
                                "deferral_count": commitment.deferred_count,
                            }),
                            severity=min(commitment.deferred_count, 5),
                        )
                        self.db.add(pattern)
                        detected.append({
                            "type": "deferral",
                            "description": pattern.description,
                            "severity": pattern.severity,
                        })

        return detected

    async def _detect_consistency_pattern(self) -> List[Dict[str, Any]]:
        """Detect positive consistency (shipping regularly)."""
        detected = []

        # Count completions in the last 2 weeks
        two_weeks_ago = datetime.utcnow() - timedelta(days=14)
        result = await self.db.execute(
            select(func.count(Commitment.id)).where(
                and_(
                    Commitment.status == CommitmentStatus.COMPLETED,
                    Commitment.completed_at > two_weeks_ago,
                )
            )
        )
        completed_count = result.scalar() or 0

        # Check response rate
        checkin_result = await self.db.execute(
            select(CheckIn).where(CheckIn.sent_at > two_weeks_ago)
        )
        checkins = checkin_result.scalars().all()
        response_rate = (
            sum(1 for c in checkins if c.response_received) / len(checkins)
            if checkins
            else 0
        )

        # If shipping consistently and responding well, note it
        if completed_count >= 7 and response_rate >= 0.8:
            recent_check = datetime.utcnow() - timedelta(days=7)
            existing = await self.db.execute(
                select(Pattern).where(
                    and_(
                        Pattern.pattern_type == "consistency",
                        Pattern.detected_at > recent_check,
                        Pattern.is_active == True,
                    )
                )
            )
            if not existing.scalar_one_or_none():
                pattern = Pattern(
                    pattern_type="consistency",
                    description=f"Consistent execution: {completed_count} items shipped, {response_rate*100:.0f}% response rate",
                    evidence=json.dumps({
                        "completed_count": completed_count,
                        "response_rate": response_rate,
                    }),
                    severity=1,  # Low severity = positive pattern
                )
                self.db.add(pattern)
                detected.append({
                    "type": "consistency",
                    "description": pattern.description,
                    "severity": pattern.severity,
                })

        return detected

    async def get_active_patterns(self) -> List[Pattern]:
        """Get all currently active patterns."""
        result = await self.db.execute(
            select(Pattern).where(Pattern.is_active == True).order_by(
                Pattern.severity.desc(), Pattern.detected_at.desc()
            )
        )
        return result.scalars().all()

    async def deactivate_old_patterns(self, days: int = 14):
        """Deactivate patterns older than specified days."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        result = await self.db.execute(
            select(Pattern).where(
                and_(
                    Pattern.is_active == True,
                    Pattern.detected_at < cutoff,
                )
            )
        )
        old_patterns = result.scalars().all()

        for pattern in old_patterns:
            pattern.is_active = False

        return len(old_patterns)
