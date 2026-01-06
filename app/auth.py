"""Authentication for The Warden API and Dashboard."""

import secrets
import time
import logging
from typing import Optional

from fastapi import HTTPException, Security, status, Request, Response, Cookie
from fastapi.security import APIKeyHeader
from app.config import get_settings
from app.security import (
    session_manager,
    login_rate_limiter,
    api_key_rate_limiter,
    request_logger,
    verify_password,
)

logger = logging.getLogger(__name__)
settings = get_settings()

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Session cookie name
SESSION_COOKIE_NAME = "warden_session"


def get_client_ip(request: Request) -> str:
    """Extract client IP from request, handling proxies."""
    # Check for forwarded headers (Railway, nginx, etc.)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # Take the first IP in the chain
        return forwarded.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # Fall back to direct connection
    return request.client.host if request.client else "unknown"


async def verify_api_key(
    request: Request,
    api_key: str = Security(api_key_header)
) -> str:
    """Verify the API key from request header with rate limiting."""
    client_ip = get_client_ip(request)
    start_time = time.time()

    # Check if IP is locked out
    locked, remaining = api_key_rate_limiter.is_locked_out(client_ip)
    if locked:
        request_logger.log(
            method=request.method,
            path=str(request.url.path),
            client_ip=client_ip,
            status_code=429,
            user_agent=request.headers.get("User-Agent"),
            auth_method="api_key",
            auth_success=False,
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many failed attempts. Try again in {remaining} seconds.",
        )

    if not api_key:
        request_logger.log(
            method=request.method,
            path=str(request.url.path),
            client_ip=client_ip,
            status_code=401,
            user_agent=request.headers.get("User-Agent"),
            auth_method="api_key",
            auth_success=False,
        )
        api_key_rate_limiter.record_attempt(client_ip, success=False)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Include X-API-Key header.",
        )

    if not secrets.compare_digest(api_key, settings.api_key):
        request_logger.log(
            method=request.method,
            path=str(request.url.path),
            client_ip=client_ip,
            status_code=403,
            user_agent=request.headers.get("User-Agent"),
            auth_method="api_key",
            auth_success=False,
        )
        api_key_rate_limiter.record_attempt(client_ip, success=False)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key.",
        )

    # Success - clear rate limit counter
    api_key_rate_limiter.record_attempt(client_ip, success=True)

    duration_ms = (time.time() - start_time) * 1000
    request_logger.log(
        method=request.method,
        path=str(request.url.path),
        client_ip=client_ip,
        status_code=200,
        user_agent=request.headers.get("User-Agent"),
        auth_method="api_key",
        auth_success=True,
        duration_ms=duration_ms,
    )

    return api_key


def verify_dashboard_session(
    request: Request,
    session_token: Optional[str] = Cookie(default=None, alias=SESSION_COOKIE_NAME),
) -> bool:
    """
    Verify dashboard session from cookie.

    Returns True if session is valid, False otherwise.
    Does NOT raise an exception - caller should handle redirect.
    """
    if not session_token:
        return False

    return session_manager.validate_session(session_token)


async def login_dashboard(
    request: Request,
    password: str,
) -> Optional[str]:
    """
    Attempt to log in to the dashboard.

    Returns session token on success, None on failure.
    """
    client_ip = get_client_ip(request)

    # Check if IP is locked out
    locked, remaining = login_rate_limiter.is_locked_out(client_ip)
    if locked:
        request_logger.log(
            method="POST",
            path="/login",
            client_ip=client_ip,
            status_code=429,
            user_agent=request.headers.get("User-Agent"),
            auth_method="password",
            auth_success=False,
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many failed login attempts. Try again in {remaining} seconds.",
        )

    # Check password
    if not settings.dashboard_password or not settings.dashboard_password_salt:
        # No password configured - check against API key as fallback
        is_valid = secrets.compare_digest(password, settings.api_key)
    else:
        is_valid = verify_password(
            password,
            settings.dashboard_password,
            settings.dashboard_password_salt
        )

    if not is_valid:
        login_rate_limiter.record_attempt(client_ip, success=False)
        request_logger.log(
            method="POST",
            path="/login",
            client_ip=client_ip,
            status_code=401,
            user_agent=request.headers.get("User-Agent"),
            auth_method="password",
            auth_success=False,
        )
        return None

    # Success - create session
    login_rate_limiter.record_attempt(client_ip, success=True)
    session_token = session_manager.create_session(client_ip)

    request_logger.log(
        method="POST",
        path="/login",
        client_ip=client_ip,
        status_code=200,
        user_agent=request.headers.get("User-Agent"),
        auth_method="password",
        auth_success=True,
    )

    return session_token


def logout_dashboard(session_token: str) -> None:
    """Invalidate a dashboard session."""
    if session_token:
        session_manager.invalidate_session(session_token)
