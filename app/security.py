"""Security utilities for The Warden - session management, rate limiting, timezone helpers."""

import secrets
import hashlib
import time
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
from collections import defaultdict
import pytz

logger = logging.getLogger(__name__)


# =============================================================================
# SESSION MANAGEMENT
# =============================================================================

class SessionManager:
    """Simple in-memory session manager for single-user deployment."""

    def __init__(self, session_duration_days: int = 30):
        self._sessions: Dict[str, Tuple[datetime, str]] = {}  # token -> (expiry, ip)
        self.session_duration = timedelta(days=session_duration_days)

    def create_session(self, client_ip: str = "unknown") -> str:
        """Create a new session and return the token."""
        token = secrets.token_urlsafe(32)
        expiry = datetime.utcnow() + self.session_duration
        self._sessions[token] = (expiry, client_ip)
        logger.info(f"Session created for IP {client_ip}, expires {expiry}")
        return token

    def validate_session(self, token: str) -> bool:
        """Check if a session token is valid."""
        if not token or token not in self._sessions:
            return False

        expiry, _ = self._sessions[token]
        if datetime.utcnow() > expiry:
            # Session expired, clean it up
            del self._sessions[token]
            return False

        return True

    def invalidate_session(self, token: str) -> None:
        """Invalidate (logout) a session."""
        if token in self._sessions:
            del self._sessions[token]
            logger.info("Session invalidated")

    def cleanup_expired(self) -> int:
        """Remove all expired sessions. Returns count of removed sessions."""
        now = datetime.utcnow()
        expired = [t for t, (exp, _) in self._sessions.items() if now > exp]
        for token in expired:
            del self._sessions[token]
        return len(expired)


# Global session manager instance
session_manager = SessionManager()


# =============================================================================
# RATE LIMITING
# =============================================================================

class RateLimiter:
    """
    Simple in-memory rate limiter for protecting against brute force attacks.

    Uses a sliding window approach with configurable limits.
    """

    def __init__(
        self,
        max_attempts: int = 5,
        window_seconds: int = 300,  # 5 minutes
        lockout_seconds: int = 3600,  # 1 hour lockout after max failures
    ):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.lockout_seconds = lockout_seconds

        # Track attempts: key -> list of timestamps
        self._attempts: Dict[str, list] = defaultdict(list)
        # Track lockouts: key -> lockout_until timestamp
        self._lockouts: Dict[str, float] = {}

    def _cleanup_old_attempts(self, key: str) -> None:
        """Remove attempts outside the sliding window."""
        cutoff = time.time() - self.window_seconds
        self._attempts[key] = [t for t in self._attempts[key] if t > cutoff]

    def is_locked_out(self, key: str) -> Tuple[bool, Optional[int]]:
        """
        Check if a key is locked out.

        Returns (is_locked, seconds_remaining or None)
        """
        if key not in self._lockouts:
            return False, None

        lockout_until = self._lockouts[key]
        now = time.time()

        if now >= lockout_until:
            # Lockout expired, remove it
            del self._lockouts[key]
            self._attempts[key] = []  # Reset attempts too
            return False, None

        seconds_remaining = int(lockout_until - now)
        return True, seconds_remaining

    def record_attempt(self, key: str, success: bool = False) -> Tuple[bool, Optional[int]]:
        """
        Record an attempt (successful or failed).

        Args:
            key: The identifier (IP address, username, etc.)
            success: If True, clears the failure count

        Returns:
            (is_now_locked, seconds_until_unlock or None)
        """
        # Check if already locked out
        locked, remaining = self.is_locked_out(key)
        if locked:
            logger.warning(f"Rate limit: {key} attempted while locked out ({remaining}s remaining)")
            return True, remaining

        if success:
            # Successful attempt - clear the failure count
            self._attempts[key] = []
            return False, None

        # Record the failed attempt
        self._cleanup_old_attempts(key)
        self._attempts[key].append(time.time())

        # Check if we've exceeded the limit
        if len(self._attempts[key]) >= self.max_attempts:
            # Lock them out
            self._lockouts[key] = time.time() + self.lockout_seconds
            logger.warning(f"Rate limit: {key} locked out for {self.lockout_seconds}s after {self.max_attempts} failures")
            return True, self.lockout_seconds

        attempts_remaining = self.max_attempts - len(self._attempts[key])
        logger.info(f"Rate limit: {key} failed attempt ({attempts_remaining} remaining before lockout)")
        return False, None

    def get_status(self, key: str) -> Dict:
        """Get rate limit status for a key."""
        locked, remaining = self.is_locked_out(key)
        self._cleanup_old_attempts(key)

        return {
            "locked_out": locked,
            "lockout_remaining_seconds": remaining,
            "recent_failures": len(self._attempts.get(key, [])),
            "max_attempts": self.max_attempts,
            "window_seconds": self.window_seconds,
        }


# Global rate limiters
login_rate_limiter = RateLimiter(max_attempts=5, window_seconds=300, lockout_seconds=3600)
api_key_rate_limiter = RateLimiter(max_attempts=10, window_seconds=60, lockout_seconds=1800)


# =============================================================================
# TIMEZONE HELPERS
# =============================================================================

def to_naive_utc(dt: datetime) -> datetime:
    """
    Convert any datetime to a naive UTC datetime.

    This is the canonical way to handle datetimes in The Warden:
    - All datetimes in the database are naive UTC
    - This function handles both aware and naive inputs
    - Use this before any database storage or comparison

    Args:
        dt: A datetime (aware or naive). If naive, assumed to be UTC.

    Returns:
        A naive datetime in UTC.
    """
    if dt is None:
        return None

    if dt.tzinfo is not None:
        # Convert to UTC first, then strip timezone
        utc_dt = dt.astimezone(pytz.UTC)
        return utc_dt.replace(tzinfo=None)

    # Already naive, assume it's UTC
    return dt


def to_aware_utc(dt: datetime) -> datetime:
    """
    Convert any datetime to an aware UTC datetime.

    Args:
        dt: A datetime (aware or naive). If naive, assumed to be UTC.

    Returns:
        An aware datetime in UTC.
    """
    if dt is None:
        return None

    if dt.tzinfo is not None:
        return dt.astimezone(pytz.UTC)

    # Naive - assume it's UTC and make it aware
    return pytz.UTC.localize(dt)


def utc_now() -> datetime:
    """Get current time as naive UTC datetime."""
    return datetime.utcnow()


def localize_to_user_tz(dt: datetime, timezone_str: str) -> datetime:
    """
    Convert a naive UTC datetime to user's local timezone.

    Args:
        dt: Naive UTC datetime
        timezone_str: Timezone string like "America/Phoenix"

    Returns:
        Aware datetime in user's timezone
    """
    if dt is None:
        return None

    try:
        tz = pytz.timezone(timezone_str)
    except pytz.exceptions.UnknownTimeZoneError:
        logger.warning(f"Unknown timezone: {timezone_str}, using UTC")
        tz = pytz.UTC

    # Make it aware as UTC first
    utc_dt = pytz.UTC.localize(dt) if dt.tzinfo is None else dt.astimezone(pytz.UTC)

    # Convert to user's timezone
    return utc_dt.astimezone(tz)


def parse_datetime_to_naive_utc(
    dt_str: str,
    format_str: str = "%Y-%m-%d",
    source_tz_str: str = "UTC"
) -> datetime:
    """
    Parse a datetime string and convert to naive UTC.

    Args:
        dt_str: The datetime string to parse
        format_str: strptime format string
        source_tz_str: Timezone the string is assumed to be in

    Returns:
        Naive UTC datetime
    """
    parsed = datetime.strptime(dt_str, format_str)

    try:
        source_tz = pytz.timezone(source_tz_str)
    except pytz.exceptions.UnknownTimeZoneError:
        source_tz = pytz.UTC

    # Localize to source timezone, then convert to UTC
    localized = source_tz.localize(parsed)
    return to_naive_utc(localized)


def days_between(dt1: datetime, dt2: datetime) -> int:
    """
    Calculate days between two datetimes, handling timezone-aware and naive.

    Both are converted to naive UTC before comparison.
    """
    dt1_naive = to_naive_utc(dt1)
    dt2_naive = to_naive_utc(dt2)

    return abs((dt2_naive.date() - dt1_naive.date()).days)


def is_same_day(dt1: datetime, dt2: datetime, timezone_str: str = "UTC") -> bool:
    """
    Check if two datetimes are on the same calendar day in a given timezone.

    Args:
        dt1, dt2: Datetimes to compare (aware or naive UTC)
        timezone_str: Timezone to use for day comparison
    """
    dt1_local = localize_to_user_tz(to_naive_utc(dt1), timezone_str)
    dt2_local = localize_to_user_tz(to_naive_utc(dt2), timezone_str)

    return dt1_local.date() == dt2_local.date()


# =============================================================================
# REQUEST LOGGING
# =============================================================================

class RequestLogger:
    """Log requests for security monitoring."""

    def __init__(self, max_entries: int = 1000):
        self._logs: list = []
        self.max_entries = max_entries

    def log(
        self,
        method: str,
        path: str,
        client_ip: str,
        status_code: int,
        user_agent: str = None,
        auth_method: str = None,
        auth_success: bool = None,
        duration_ms: float = None,
    ) -> None:
        """Log a request."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "method": method,
            "path": path,
            "client_ip": client_ip,
            "status_code": status_code,
            "user_agent": user_agent,
            "auth_method": auth_method,
            "auth_success": auth_success,
            "duration_ms": duration_ms,
        }

        self._logs.append(entry)

        # Trim old entries
        if len(self._logs) > self.max_entries:
            self._logs = self._logs[-self.max_entries:]

        # Log suspicious activity
        if status_code == 403 or (auth_success is False):
            logger.warning(f"Security event: {method} {path} from {client_ip} - status={status_code}, auth_success={auth_success}")

    def get_recent(self, count: int = 100) -> list:
        """Get recent log entries."""
        return self._logs[-count:]

    def get_failures(self, count: int = 50) -> list:
        """Get recent failed auth attempts."""
        failures = [e for e in self._logs if e.get("auth_success") is False]
        return failures[-count:]

    def get_by_ip(self, ip: str, count: int = 50) -> list:
        """Get requests from a specific IP."""
        by_ip = [e for e in self._logs if e.get("client_ip") == ip]
        return by_ip[-count:]


# Global request logger
request_logger = RequestLogger()


# =============================================================================
# TELEGRAM REPLAY PROTECTION
# =============================================================================

class TelegramUpdateTracker:
    """
    Track processed Telegram update IDs to prevent replay attacks.

    Telegram update IDs are monotonically increasing, so we only need
    to track the highest processed ID.
    """

    def __init__(self, max_age_seconds: int = 300):
        self._highest_update_id: int = 0
        self._recent_ids: Dict[int, float] = {}  # update_id -> timestamp
        self.max_age_seconds = max_age_seconds

    def is_replay(self, update_id: int) -> bool:
        """
        Check if this update ID has already been processed or is too old.

        Returns True if this is a replay (should be rejected).
        """
        if update_id is None:
            return False  # Can't check, allow it

        # Clean up old entries
        self._cleanup()

        # Check if we've seen this exact ID recently
        if update_id in self._recent_ids:
            logger.warning(f"Telegram replay detected: update_id {update_id} already processed")
            return True

        # Check if this ID is older than our highest (replay of old message)
        if update_id < self._highest_update_id - 100:  # Allow some slack for out-of-order
            logger.warning(f"Telegram replay detected: update_id {update_id} < highest {self._highest_update_id}")
            return True

        return False

    def mark_processed(self, update_id: int) -> None:
        """Mark an update ID as processed."""
        if update_id is None:
            return

        self._recent_ids[update_id] = time.time()
        if update_id > self._highest_update_id:
            self._highest_update_id = update_id

    def _cleanup(self) -> None:
        """Remove old entries to prevent memory bloat."""
        cutoff = time.time() - self.max_age_seconds
        self._recent_ids = {
            uid: ts for uid, ts in self._recent_ids.items()
            if ts > cutoff
        }


# Global telegram update tracker
telegram_update_tracker = TelegramUpdateTracker()


# =============================================================================
# PASSWORD HASHING
# =============================================================================

def hash_password(password: str, salt: str = None) -> Tuple[str, str]:
    """
    Hash a password using PBKDF2.

    Returns (hash, salt) tuple.
    """
    if salt is None:
        salt = secrets.token_hex(16)

    hash_bytes = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000  # iterations
    )

    return hash_bytes.hex(), salt


def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    """Verify a password against a stored hash."""
    computed_hash, _ = hash_password(password, salt)
    return secrets.compare_digest(computed_hash, stored_hash)
