# Security and Compatibility Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix critical SQLite/PostgreSQL compatibility issues and security vulnerabilities identified in code review.

**Architecture:** Replace PostgreSQL-specific types with SQLAlchemy dialect-agnostic equivalents, add proper security controls to authentication and webhook endpoints, fix multi-user isolation issues.

**Tech Stack:** Python/FastAPI, SQLAlchemy 2.0, Pydantic v2

---

## Task 1: Fix JSONB → JSON Compatibility (P0 Critical)

**Files:**
- Modify: `app/db_models.py:18,192,294,388,428`

**Step 1: Update import statement**

Replace:
```python
from sqlalchemy.dialects.postgresql import UUID, JSONB
```

With:
```python
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import JSON
```

**Step 2: Replace JSONB with JSON in all columns**

Line 192 - Pattern.evidence:
```python
evidence = Column(JSON, nullable=True)  # Structured supporting data
```

Line 294 - PendingCommitmentParse.suggested_breakdown:
```python
suggested_breakdown = Column(JSON, nullable=True)  # JSON array of breakdown steps
```

Line 388 - ErrorLog.context:
```python
context = Column(JSON, nullable=True)  # JSON with additional context
```

Line 428 - WeeklyInsight.metrics:
```python
metrics = Column(JSON, nullable=True)  # JSON with metrics data
```

**Step 3: Run import test to verify no syntax errors**

Run: `./venv/bin/python -m pytest tests/test_imports.py -v`
Expected: All 8 tests PASS

**Step 4: Start server to verify database initializes**

Run: `./venv/bin/python -c "from app.database import init_db; import asyncio; asyncio.run(init_db())"`
Expected: No JSONB compilation errors

**Step 5: Commit**

```bash
git add app/db_models.py
git commit -m "fix: replace PostgreSQL JSONB with dialect-agnostic JSON for SQLite compatibility"
```

---

## Task 2: Remove Debug Endpoints (P0 Critical)

**Files:**
- Modify: `app/main.py:127-167`

**Step 1: Remove both debug endpoints**

Delete these entire functions (lines 127-167):
- `debug_auth()` - exposes partial API key
- `debug_db()` - exposes database connection details

**Step 2: Run server health check**

Run: `curl -s http://localhost:8765/debug/auth`
Expected: `{"detail":"Not Found"}` (404)

**Step 3: Commit**

```bash
git add app/main.py
git commit -m "security: remove debug endpoints that exposed sensitive configuration"
```

---

## Task 3: Fix CORS Configuration (P0 Critical)

**Files:**
- Modify: `app/main.py:74-80`

**Step 1: Update CORS middleware**

Replace:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

With:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else [
        "https://your-production-domain.com",  # TODO: Configure in settings
    ],
    allow_credentials=False,  # Never use credentials with wildcard origins
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["X-API-Key", "Content-Type"],
)
```

**Step 2: Verify server starts**

Run: `./venv/bin/python -c "from app.main import app; print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add app/main.py
git commit -m "security: fix CORS to disable credentials with wildcard origins"
```

---

## Task 4: Fix Timing-Safe API Key Comparison (P1 High)

**Files:**
- Modify: `app/auth.py:1,20`

**Step 1: Add secrets import**

Add at line 1:
```python
import secrets
```

**Step 2: Replace string comparison with constant-time comparison**

Replace line 20:
```python
    if api_key != settings.api_key:
```

With:
```python
    if not secrets.compare_digest(api_key, settings.api_key):
```

**Step 3: Run import test**

Run: `./venv/bin/python -c "from app.auth import verify_api_key; print('OK')"`
Expected: `OK`

**Step 4: Commit**

```bash
git add app/auth.py
git commit -m "security: use constant-time comparison for API key to prevent timing attacks"
```

---

## Task 5: Add Telegram Webhook Secret Validation (P1 High)

**Files:**
- Modify: `app/config.py` (add setting)
- Modify: `app/routers/webhook.py:299-310`

**Step 1: Add webhook secret to config**

In `app/config.py`, add after line 20:
```python
telegram_webhook_secret: str = ""  # Secret token for webhook validation
```

**Step 2: Add validation to webhook endpoint**

In `app/routers/webhook.py`, update the telegram_webhook function. After line 299, add validation:

```python
@router.post("/telegram")
async def telegram_webhook(request: Request):
    """Handle incoming Telegram messages."""
    # Validate webhook secret if configured
    if settings.telegram_webhook_secret:
        secret_header = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if not secrets.compare_digest(secret_header, settings.telegram_webhook_secret):
            logger.warning("Invalid webhook secret token received")
            raise HTTPException(status_code=403, detail="Invalid secret token")

    try:
        update_data = await request.json()
    # ... rest of function
```

**Step 3: Add secrets import to webhook.py**

Add at top of file:
```python
import secrets
```

**Step 4: Run import test**

Run: `./venv/bin/python -c "from app.routers.webhook import router; print('OK')"`
Expected: `OK`

**Step 5: Commit**

```bash
git add app/config.py app/routers/webhook.py
git commit -m "security: add Telegram webhook secret validation to prevent forged requests"
```

---

## Task 6: Fix Dashboard Chat Missing User Parameter (P1 High)

**Files:**
- Modify: `app/routers/app_settings.py:1070-1200`

**Step 1: Add user service import**

At top of file, add:
```python
from app.user_service import get_default_user
```

**Step 2: Get user at start of send_chat_message**

After line 1095 (inside the function, after getting db), add:
```python
    # Get the default user for dashboard chat
    user = await get_default_user(db)
    if not user:
        raise HTTPException(status_code=500, detail="No user configured")
```

**Step 3: Add user_id to ChatMessage objects**

Update line 1102-1107:
```python
    user_chat_msg = ChatMessage(
        user_id=user.id,  # ADD THIS
        role="user",
        content=message_text,
        message_type="reply",
        telegram_message_id=None,
    )
```

**Step 4: Pass user to try_handle_completion**

Update line 1113:
```python
    handled, reply = await try_handle_completion(db, message_text, user)
```

**Step 5: Add user_id to warden ChatMessage (line 1116-1121)**

```python
            warden_chat_msg = ChatMessage(
                user_id=user.id,  # ADD THIS
                role="warden",
                content=reply,
                message_type="completion",
                telegram_message_id=None,
            )
```

**Step 6: Pass user to handle_pending_confirmation**

Update line 1132:
```python
    handled, reply = await handle_pending_confirmation(db, message_text, user)
```

**Step 7: Add user_id to all other ChatMessage instances in function**

Search for all `ChatMessage(` in the function and add `user_id=user.id,` to each.

**Step 8: Run import test**

Run: `./venv/bin/python -c "from app.routers.app_settings import router; print('OK')"`
Expected: `OK`

**Step 9: Commit**

```bash
git add app/routers/app_settings.py
git commit -m "fix: add user parameter to dashboard chat functions for multi-user support"
```

---

## Task 7: Add Database Indexes (P2 Medium)

**Files:**
- Modify: `app/db_models.py`

**Step 1: Add index to Commitment.status**

Line ~110, update:
```python
    status = Column(
        SQLEnum(
            CommitmentStatus,
            name="commitment_status",
            create_type=False,
            values_callable=lambda x: [e.value for e in x]
        ),
        default=CommitmentStatus.PENDING,
        nullable=False,
        index=True,  # ADD THIS
    )
```

**Step 2: Add index to Commitment.due_date**

Line ~109:
```python
    due_date = Column(DateTime, nullable=True, index=True)  # ADD index=True
```

**Step 3: Add index to CheckIn.response_received**

Line ~149:
```python
    response_received = Column(Boolean, default=False, index=True)  # ADD index=True
```

**Step 4: Add index to CheckIn.sent_at**

Line ~148:
```python
    sent_at = Column(DateTime, default=datetime.utcnow, index=True)  # ADD index=True
```

**Step 5: Add index to Settings.key**

Line ~211:
```python
    key = Column(Text, nullable=False, index=True)  # ADD index=True
```

**Step 6: Run import test**

Run: `./venv/bin/python -m pytest tests/test_imports.py -v`
Expected: All 8 tests PASS

**Step 7: Commit**

```bash
git add app/db_models.py
git commit -m "perf: add database indexes to frequently queried columns"
```

---

## Task 8: Fix Pydantic Deprecations (P2 Medium)

**Files:**
- Modify: `app/config.py:56-58`
- Modify: `app/models.py` (multiple locations)
- Modify: `app/routers/errors.py:19,35`
- Modify: `app/routers/app_settings.py:114,514`
- Modify: `app/routers/calendar.py:138`

**Step 1: Fix config.py**

Replace lines 56-58:
```python
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
```

With:
```python
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }
```

**Step 2: Fix models.py - Replace all `class Config` with `model_config`**

For each Pydantic model with `class Config: orm_mode = True`, replace with:
```python
    model_config = {"from_attributes": True}
```

Models to update: GoalResponse, CommitmentResponse, CheckInResponse, UserResponseResponse, PatternResponse

**Step 3: Fix routers/errors.py**

Replace `class Config: orm_mode = True` with `model_config = {"from_attributes": True}` in ErrorLogResponse and ErrorLogSummary.

**Step 4: Fix routers/app_settings.py**

Replace `class Config: orm_mode = True` with `model_config = {"from_attributes": True}` in ChatMessageResponse and ScheduleResponse.

**Step 5: Fix routers/calendar.py**

Replace `class Config: orm_mode = True` with `model_config = {"from_attributes": True}` in CalendarEventResponse.

**Step 6: Run import tests**

Run: `./venv/bin/python -m pytest tests/test_imports.py -v 2>&1 | grep -c "PydanticDeprecatedSince20"`
Expected: `0` (no deprecation warnings)

**Step 7: Commit**

```bash
git add app/config.py app/models.py app/routers/errors.py app/routers/app_settings.py app/routers/calendar.py
git commit -m "refactor: update Pydantic models from deprecated class Config to model_config"
```

---

## Task 9: Fix Scheduler User Isolation (P2 Medium)

**Files:**
- Modify: `app/scheduler.py`

**Step 1: Update silence_detector_job to iterate all users**

Find the `silence_detector_job` function and wrap the logic to iterate through all active users, similar to how `daily_checkin_job` does it.

**Step 2: Update commitment_reminder_job to iterate all users**

Same pattern - iterate through all active users.

**Step 3: Update deadline_alert_job to iterate all users**

Same pattern - iterate through all active users.

**Step 4: Run import test**

Run: `./venv/bin/python -c "from app.scheduler import silence_detector_job; print('OK')"`
Expected: `OK`

**Step 5: Commit**

```bash
git add app/scheduler.py
git commit -m "fix: add user isolation to scheduler jobs for multi-tenant support"
```

---

## Task 10: Run Full Test Suite

**Step 1: Run all tests**

Run: `./venv/bin/python -m pytest tests/ -v --tb=short 2>&1 | tail -50`
Expected: Most tests should now pass (some may need additional fixes)

**Step 2: Start server and verify health**

Run: `./venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8765 &`
Run: `sleep 3 && curl -s http://localhost:8765/health`
Expected: `{"status":"healthy","scheduler":"running"}`

**Step 3: Final commit**

```bash
git add -A
git commit -m "test: verify all fixes working"
```

---

## Summary

| Task | Priority | Risk | Effort |
|------|----------|------|--------|
| 1. JSONB → JSON | P0 | Low | 5 min |
| 2. Remove debug endpoints | P0 | Low | 5 min |
| 3. Fix CORS | P0 | Low | 5 min |
| 4. Timing-safe API key | P1 | Low | 5 min |
| 5. Webhook validation | P1 | Medium | 15 min |
| 6. Dashboard chat user | P1 | Medium | 20 min |
| 7. Database indexes | P2 | Low | 10 min |
| 8. Pydantic deprecations | P2 | Low | 15 min |
| 9. Scheduler user isolation | P2 | High | 30 min |
| 10. Full test suite | - | - | 10 min |

**Total estimated time:** ~2 hours
