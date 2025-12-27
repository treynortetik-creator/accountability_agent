# The Warden 🔒

A personal accountability agent that checks in on your commitments, tracks what you deliver, identifies avoidance patterns, and calls you out via Telegram.

## Features

- **Daily Check-ins**: Morning check-ins asking what you shipped and what you're committing to
- **Weekly Reviews**: Sunday evening summaries of completion rate and patterns
- **Pattern Detection**: Identifies avoidance, silence, excuse-making, and consistency
- **Escalation**: Calls you out if you go dark (no response within 18 hours)
- **Deadline Alerts**: Reminders 48 hours before due dates
- **LLM-Powered**: Contextual, direct responses based on your history

## Personality

The Warden is blunt, doesn't sugarcoat, uses occasional profanity, and calls out bullshit. It doesn't celebrate showing up - that's baseline. It references specific past commitments when you're being avoidant.

## Tech Stack

- **Backend**: Python + FastAPI
- **Database**: SQLite
- **Scheduler**: APScheduler
- **LLM**: OpenRouter API (Gemini Flash / GPT-4o-mini)
- **Messaging**: Telegram Bot API
- **Dashboard**: Streamlit
- **Deployment**: Railway

## Setup

### 1. Clone and Install

```bash
git clone <your-repo>
cd accountability_agent
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your values
```

### 3. Create Telegram Bot

1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot` and follow prompts
3. Copy the bot token to `TELEGRAM_BOT_TOKEN`
4. Message [@userinfobot](https://t.me/userinfobot) to get your chat ID
5. Copy your chat ID to `TELEGRAM_CHAT_ID`

### 4. Get OpenRouter API Key

1. Go to [OpenRouter](https://openrouter.ai/keys)
2. Create an API key
3. Copy to `OPENROUTER_API_KEY`

### 5. Run Locally

```bash
# Start the API server
uvicorn app.main:app --reload

# In another terminal, start the dashboard
streamlit run dashboard/app.py
```

### 6. Set Telegram Webhook

After deploying or using ngrok for local testing:

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=<YOUR_WEBHOOK_URL>/webhook/telegram"
```

## Deploy to Railway

1. Push your code to GitHub
2. Create a new project on [Railway](https://railway.app)
3. Connect your GitHub repo
4. Add environment variables in Railway dashboard
5. Deploy!

Railway will automatically:
- Build using Nixpacks
- Run the Procfile command
- Provide a public URL

After deployment, set your Telegram webhook to the Railway URL.

## API Endpoints

### Goals
- `GET /api/goals` - List goals
- `POST /api/goals` - Create goal
- `GET /api/goals/{id}` - Get goal
- `PATCH /api/goals/{id}` - Update goal
- `DELETE /api/goals/{id}` - Delete goal

### Commitments
- `GET /api/commitments` - List commitments
- `POST /api/commitments` - Create commitment
- `GET /api/commitments/{id}` - Get commitment
- `PATCH /api/commitments/{id}` - Update commitment
- `POST /api/commitments/{id}/complete` - Mark complete
- `POST /api/commitments/{id}/fail` - Mark failed
- `POST /api/commitments/{id}/defer` - Defer commitment
- `DELETE /api/commitments/{id}` - Delete commitment

### Check-ins & Stats
- `GET /api/checkins` - List check-ins
- `GET /api/checkins/responses` - List responses
- `GET /api/checkins/patterns` - List detected patterns
- `GET /api/checkins/stats` - Get statistics
- `GET /api/checkins/schedule` - Get schedule config

### Triggers (for testing)
- `POST /api/trigger/checkin` - Trigger daily check-in
- `POST /api/trigger/weekly-review` - Trigger weekly review

All API endpoints (except webhook) require `X-API-Key` header.

## Dashboard

Access the Streamlit dashboard at `http://localhost:8501` (local) or deploy separately.

Dashboard features:
- View commitment history and completion rates
- Add/edit goals and commitments
- See detected patterns
- View check-in history
- Trigger manual check-ins

## Schedule

Default schedule (America/Phoenix timezone):
- **Daily Check-in**: 4:15 AM
- **Weekly Review**: Sunday 6:00 PM
- **Silence Detection**: Every 12 hours
- **Deadline Alerts**: Every 6 hours (48h before due)

Adjust in environment variables.

## License

MIT
