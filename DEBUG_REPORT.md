# The Warden - Debug Report
Generated: December 28, 2025

## Executive Summary

After a comprehensive review of the codebase, I found **3 critical issues**, **3 medium issues**, and **4 low priority issues**. The application is generally well-structured but has some dead code and potential blocking operations.

---

## File Structure

```
accountability_agent/
├── app/
│   ├── __init__.py
│   ├── auth.py              ✓ Clean
│   ├── calendar_service.py  ⚠️ Has blocking call
│   ├── config.py            ✓ Clean
│   ├── dashboard_html.py    ✓ Main dashboard (52KB)
│   ├── database.py          ✓ Clean
│   ├── db_models.py         ✓ Clean - 10 models defined
│   ├── init_settings.py     ✓ New - initializes persistent settings
│   ├── llm.py               ✓ Clean - full user context included
│   ├── main.py              ✓ Clean
│   ├── models.py            ⚠️ Some unused Pydantic models
│   ├── patterns.py          ✓ Clean - pattern detection
│   ├── scheduler.py         ✓ Clean - 4 scheduled jobs
│   ├── streaks.py           ✓ Clean
│   ├── telegram_bot.py      ✓ Clean
│   └── routers/
│       ├── __init__.py
│       ├── app_settings.py  ⚠️ Import inside function
│       ├── calendar.py      ✓ Clean
│       ├── checkins.py      ✓ Clean
│       ├── commitments.py   ✓ Clean
│       ├── goals.py         ✓ Clean
│       └── webhook.py       ✓ Clean
├── dashboard/
│   └── app.py               ❌ DEAD CODE - Streamlit dashboard not used
├── requirements.txt         ✓ Clean
├── Procfile                 ✓ Only runs FastAPI (not Streamlit)
└── .env                     ✓ Configuration
```

---

## CRITICAL/HIGH PRIORITY ISSUES

### 1. Dead Code - `dashboard/app.py` (521 lines)
**Location:** `/dashboard/app.py`
**Issue:** This is an old Streamlit dashboard that's no longer used. The Procfile only runs the FastAPI app which serves an embedded HTML dashboard via `dashboard_html.py`.
**Impact:** Confusion, maintenance burden, 521 lines of dead code
**Fix:** Delete the file and the `dashboard/` directory

### 2. Blocking Call in Calendar Service
**Location:** `app/calendar_service.py:69`
**Issue:**
```python
creds.refresh(Request())
```
This is a synchronous HTTP call inside an async function. It will block the event loop during token refresh.
**Impact:** Could cause request timeouts and degraded performance
**Fix:** Use `google-auth-httplib2` async variant or run in executor

### 3. Calendar Sync Deletes All Events
**Location:** `app/calendar_service.py:137`
**Issue:**
```python
await db.execute(delete(CalendarEvent))
```
Every sync deletes ALL calendar events before re-adding them. If the sync fails midway, you lose all event data.
**Impact:** Potential data loss
**Fix:** Use upsert logic (update existing, insert new, mark missing as deleted)

---

## MEDIUM PRIORITY ISSUES

### 4. Import Inside Function
**Location:** `app/routers/app_settings.py:155`
**Issue:**
```python
async def get_settings(...):
    import json  # Should be at top of file
```
**Impact:** Minor performance hit, non-standard practice
**Fix:** Move `import json` to file top

### 5. Dashboard Streak Display Not Verified
**Location:** `app/dashboard_html.py`
**Issue:** The dashboard calls `/settings/streaks` but I couldn't verify the UI properly displays streak data. The endpoint exists but the display logic may not be fully connected.
**Impact:** User may not see streak information
**Fix:** Verify streak display in dashboard UI

### 6. Missing Pattern Display in Dashboard
**Location:** `app/patterns.py` / `app/dashboard_html.py`
**Issue:** The `PatternDetector` class detects avoidance, silence, excuse, deferral, and consistency patterns. These are stored in the DB but the main dashboard doesn't seem to display them prominently.
**Impact:** User misses valuable behavioral insights
**Fix:** Add pattern display to dashboard overview

---

## LOW PRIORITY ISSUES

### 7. Unused Pydantic Models
**Location:** `app/models.py`
**Issue:** `ManualCheckInRequest` and `ScheduleConfigUpdate` models may not be actively used
**Impact:** Dead code
**Fix:** Verify usage and remove if unused

### 8. Debug Logging in Production
**Location:** `app/database.py:14`
**Issue:**
```python
echo=settings.debug
```
If `debug=True` in production, SQL queries will be logged (potential info leak)
**Impact:** Security/privacy concern
**Fix:** Ensure `DEBUG=False` in production env vars

### 9. Streamlit in requirements.txt
**Location:** `requirements.txt`
**Issue:** `streamlit==1.30.0`, `plotly==5.18.0`, `pandas==2.1.4` are only needed for the dead Streamlit dashboard
**Impact:** Larger Docker image, unused dependencies
**Fix:** Remove if deleting Streamlit dashboard

### 10. Hardcoded Timezone
**Location:** `app/llm.py:398`
**Issue:**
```python
tz = pytz.timezone("America/Phoenix")  # User's timezone
```
Timezone is hardcoded for commitment parsing but config has `settings.timezone`
**Impact:** Inconsistent timezone handling
**Fix:** Use `settings.timezone` instead of hardcoding

---

## THINGS THAT ARE WORKING WELL

✅ **Database Models** - Clean, normalized schema with 10 tables
✅ **Scheduler** - 4 jobs properly scheduled (daily checkin, weekly review, silence detector, deadline alerts)
✅ **API Structure** - Clean router separation (goals, commitments, checkins, calendar, webhook, settings)
✅ **Authentication** - Proper API key validation
✅ **LLM Integration** - Full user context in prompts, commitment parsing works
✅ **Telegram Integration** - Webhook setup, message parsing, response handling
✅ **Streak Tracking** - Response and completion streaks properly tracked
✅ **Error Handling** - Try/catch blocks in critical paths, rollback on failure

---

## RECOMMENDED FIX PLAN

### Phase 1: Quick Wins (< 30 min)
1. [ ] Delete `dashboard/` directory (dead code)
2. [ ] Move `import json` to top of `app_settings.py`
3. [ ] Remove Streamlit dependencies from `requirements.txt`
4. [ ] Fix hardcoded timezone in `llm.py`

### Phase 2: Important Fixes (1-2 hours)
5. [ ] Fix blocking call in `calendar_service.py` - use thread executor
6. [ ] Improve calendar sync to use upsert instead of delete-all
7. [ ] Add pattern display to dashboard

### Phase 3: Nice to Have
8. [ ] Audit and remove unused Pydantic models
9. [ ] Add more comprehensive error handling for calendar sync failures
10. [ ] Add dashboard section for viewing detected patterns

---

## COMMANDS TO VERIFY

```bash
# Check if all Python files compile
python3 -m py_compile app/*.py app/routers/*.py

# Check for unused imports
pip install autoflake
autoflake --check app/*.py

# Check for type issues
pip install mypy
mypy app/

# Test the API
curl http://localhost:8000/health
curl -H "X-API-Key: your-key" http://localhost:8000/api/checkins/stats
```

---

## DATABASE TABLES

| Table | Purpose | Status |
|-------|---------|--------|
| goals | Long-term goals | ✓ Used |
| commitments | Specific tasks/promises | ✓ Used |
| checkins | Check-in messages sent | ✓ Used |
| responses | User responses to check-ins | ✓ Used |
| patterns | Detected behavioral patterns | ⚠️ Not displayed |
| schedule_config | Schedule settings | ⚠️ Possibly unused |
| settings | App settings (model, prompt, calendar) | ✓ Used |
| chat_messages | Full conversation history | ✓ Used |
| calendar_events | Synced Google Calendar events | ✓ Used |
| streaks | Response and completion streaks | ✓ Used |
| pending_commitment_parses | NLP commitment parsing confirmations | ✓ Used |

---

## CONCLUSION

The codebase is generally well-structured and functional. The main issues are:
1. Dead Streamlit dashboard code that should be removed
2. A blocking HTTP call in the calendar service
3. Risky calendar sync that deletes all events

These are fixable with the plan above. The core functionality (Telegram integration, LLM responses, scheduling, tracking) is solid.
