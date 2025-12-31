# Deploying The Warden to Railway with Supabase

## Database Migration Complete

The Supabase database (project: `dztlwgrlvppxxrfgrfsq`) has been configured with:
- 18 tables with multi-user support
- Row Level Security (RLS) enabled on all tables
- Proper indexes for performance
- PostgreSQL-native types (UUID, JSONB, TIMESTAMPTZ)

## Railway Environment Variables

Set these in your Railway project:

```bash
# Database - USE THE POOLER CONNECTION (port 6543 for IPv4 compatibility)
DATABASE_URL=postgresql+asyncpg://postgres.dztlwgrlvppxxrfgrfsq:[YOUR-PASSWORD]@aws-0-us-west-1.pooler.supabase.com:6543/postgres

# Get your password from Supabase Dashboard:
# Settings > Database > Connection string > URI
# The password is the part after the colon and before the @ symbol

# Telegram
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id
TELEGRAM_WEBHOOK_URL=https://your-app.railway.app/webhook/telegram

# LLM
OPENROUTER_API_KEY=your-openrouter-key
OPENROUTER_MODEL=google/gemini-2.5-flash

# API Auth
API_KEY=your-secure-api-key

# Optional
TIMEZONE=America/Phoenix
DEBUG=false
```

## Important: IPv4 Compatibility

Railway doesn't natively support IPv6. Supabase's **direct connection** (port 5432) uses IPv6.

**Solution**: Use Supabase's **Supavisor connection pooler** on port **6543**:
- This provides IPv4 support
- Works with Railway out of the box
- Better for serverless environments anyway

The connection string format:
```
postgresql+asyncpg://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
```

## Getting Your Supabase Password

1. Go to https://supabase.com/dashboard/project/dztlwgrlvppxxrfgrfsq/settings/database
2. Click "Connection string"
3. Copy the URI and extract your password
4. Or click "Reset database password" if you need a new one

## Deploying to Railway

1. **Push your code to GitHub** (if not already)

2. **Create a new Railway project**
   - Connect your GitHub repo
   - Railway will auto-detect Python/FastAPI

3. **Add environment variables** (see above)

4. **Deploy**
   - Railway will install dependencies from `requirements.txt`
   - The app will start automatically

5. **Set up Telegram webhook**
   - Once deployed, visit: `https://your-app.railway.app/webhook/setup`
   - This registers your webhook with Telegram

## Verifying the Deployment

1. **Health check**: `GET https://your-app.railway.app/health`
2. **Webhook status**: `GET https://your-app.railway.app/webhook/status`
3. **Dashboard**: `https://your-app.railway.app/dashboard`

## Database Tables Created

| Table | Purpose |
|-------|---------|
| users | Multi-user support with telegram_chat_id |
| goals | Long-term goals |
| commitments | Tasks and commitments |
| checkins | Messages sent by The Warden |
| responses | User replies to check-ins |
| patterns | Behavioral patterns detected |
| streaks | Gamification tracking |
| settings | User-specific configuration |
| chat_messages | Conversation history |
| checkin_schedules | Custom check-in times |
| checkin_prompts | Custom prompts per check-in type |
| mood_logs | Mood and energy tracking |
| calendar_events | Google Calendar cache |
| pending_commitment_parses | Awaiting confirmation |
| scheduled_followups | Scheduled follow-ups |
| response_timings | Response time analytics |
| weekly_insights | Weekly summaries |
| error_logs | Error tracking |

## Multi-User Support

The app now supports multiple users. Each user is identified by their `telegram_chat_id`. When a message comes in via Telegram:
1. The webhook extracts the chat ID
2. Gets or creates the user record
3. All queries are filtered by `user_id`

For API endpoints (dashboard, etc.), the user is determined by the `TELEGRAM_CHAT_ID` environment variable.

## Notes

- The app still works locally with SQLite for development
- Just don't set DATABASE_URL, or set it to `sqlite+aiosqlite:///./warden.db`
- PostgreSQL enum types are created in the database, not by SQLAlchemy
- JSONB is used for structured data (evidence, metrics, etc.)
