# AcoutaBilly - The Warden (Accountability Agent)

## Project Overview
An AI-powered accountability agent that helps users stay on track with their goals through Telegram check-ins, commitment tracking, and behavioral pattern analysis.

## Supabase MCP Configuration

### CRITICAL: Which Database to Use

| Project Name | Project Ref | Purpose | USE FOR THIS PROJECT? |
|--------------|-------------|---------|----------------------|
| **The Warden** | `dztlwgrlvppxxrfgrfsq` | Accountability Agent database | **YES - USE THIS ONE** |
| **Still** | `tvlvnplhybumuoiflthb` | Content Creation Engine (separate project) | **NO - NEVER TOUCH** |

**Current Issue**: The MCP is connected to "Still" (`tvlvnplhybumuoiflthb`) but should be connected to "The Warden" (`dztlwgrlvppxxrfgrfsq`).

To fix, update the MCP config:
```
https://mcp.supabase.com/mcp?project_ref=dztlwgrlvppxxrfgrfsq
```

## Tech Stack
- **Backend**: FastAPI (Python)
- **Database**: SQLite (local) / Supabase (production migration planned)
- **Frontend**: Embedded HTML dashboard in `dashboard_html.py`
- **Messaging**: Telegram Bot API
- **AI**: OpenRouter API for LLM calls

## Key Files
- `app/main.py` - FastAPI application entry point
- `app/dashboard_html.py` - Single-file HTML dashboard
- `app/routers/` - API route handlers
- `app/db_models.py` - SQLAlchemy models
- `app/scheduler.py` - APScheduler for check-ins
- `app/llm.py` - LLM integration

## Commands
```bash
# Activate virtual environment
source venv/bin/activate

# Run tests
python -m pytest tests/test_comprehensive.py -v

# Run with test environment
TESTING=true DATABASE_URL="sqlite+aiosqlite:///:memory:" \
TELEGRAM_BOT_TOKEN="test" TELEGRAM_CHAT_ID="123" \
OPENROUTER_API_KEY="test" API_KEY="test_api_key" \
python -m pytest tests/ -v
```

## API Endpoints (Key)
- `GET /api/goals` - List goals
- `GET /api/commitments` - List commitments
- `GET /api/checkins` - List check-ins
- `GET /api/settings/schedules` - List check-in schedules (new flexible system)
- `POST /api/trigger/checkin` - Manual check-in trigger

## Recent Changes
- Removed duplicate "Check-in Schedule" (singular) feature - now only "Check-in Schedules" (plural) exists
- Old `/checkins/schedule` endpoint removed in favor of `/settings/schedules`

## Code Style
- Python with type hints
- Pydantic models for validation
- Async SQLAlchemy for database operations
