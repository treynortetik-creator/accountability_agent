# GitHub Integration for The Warden

**Date:** 2026-01-05
**Status:** Draft - Pending Approval

---

## Overview

Give The Warden awareness of your coding activity across configured GitHub repositories. This enables informed accountability check-ins, pattern recognition, and commitment verification without the Warden being annoying about it.

### Use Cases

1. **Proactive accountability** - Warden notices you haven't pushed in 2+ days and nudges you
2. **Context for conversations** - When you chat, Warden knows what you've been working on
3. **Progress tracking** - Warden tracks commit frequency/patterns over time
4. **Commitment verification** - When you say "I'll finish the API by Friday," Warden checks if commits match

---

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Repos | 2-3 specific, configurable | Avoids noise from old/archived projects |
| Auth | Personal Access Token | Simple, user-controlled, read-only scope |
| Data fetch | Polling (not webhooks) | Simpler, fits existing scheduler, no new endpoints |
| Poll frequency | Configurable (default 3:30 AM) | Once daily before morning check-in |
| Data stored | Commit message, timestamp, repo | Minimal - no SHA, branch, file counts |
| Retention | 7 days rolling, configurable | Prevents context bloat (3-5 commits/day = 21-35 max) |
| Behavior | Only proactive when noteworthy | Avoids being annoying; context always available |
| Errors | Notify on persistent failures | Silent on one-off blips, alert if token expires |

---

## Data Model

### New Tables

```sql
-- Configured repositories to monitor
CREATE TABLE github_repos (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    repo_owner TEXT NOT NULL,        -- e.g., "treynortetik-creator"
    repo_name TEXT NOT NULL,         -- e.g., "accountability_agent"
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, repo_owner, repo_name)
);

-- Fetched commit history
CREATE TABLE github_commits (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    repo_id BIGINT NOT NULL REFERENCES github_repos(id) ON DELETE CASCADE,
    commit_message TEXT NOT NULL,
    committed_at TIMESTAMPTZ NOT NULL,
    fetched_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for efficient queries
CREATE INDEX idx_github_commits_user_date ON github_commits(user_id, committed_at DESC);
```

### Settings Keys (stored in existing `settings` table)

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `github_pat` | string (encrypted) | null | Personal Access Token |
| `github_poll_hour` | int | 3 | Hour to poll (0-23) |
| `github_poll_minute` | int | 30 | Minute to poll (0-59) |
| `github_retention_days` | int | 7 | Days to keep commit history |

---

## Scheduler Jobs

### 1. GitHub Polling Job

Runs at configured time (default 3:30 AM). For each enabled repo:

```python
async def github_poll_job():
    """Fetch recent commits from configured GitHub repos."""
    async with async_session_maker() as db:
        user = await get_default_user(db)

        # Get GitHub PAT from settings
        pat = await get_setting(db, user, "github_pat")
        if not pat:
            return  # Not configured

        # Get enabled repos
        repos = await get_enabled_repos(db, user)

        for repo in repos:
            try:
                commits = await fetch_github_commits(
                    pat, repo.repo_owner, repo.repo_name
                )
                await store_new_commits(db, user, repo, commits)
            except GitHubAPIError as e:
                await handle_github_error(db, user, repo, e)

        await db.commit()
```

### 2. GitHub Cleanup Job

Runs daily after polling. Prunes commits older than retention period:

```python
async def github_cleanup_job():
    """Remove commits older than retention period."""
    async with async_session_maker() as db:
        user = await get_default_user(db)
        retention_days = await get_setting(db, user, "github_retention_days", 7)
        cutoff = datetime.utcnow() - timedelta(days=retention_days)

        await db.execute(
            delete(GitHubCommit).where(
                GitHubCommit.user_id == user.id,
                GitHubCommit.committed_at < cutoff
            )
        )
        await db.commit()
```

---

## GitHub API Integration

### Service Module: `app/github_service.py`

```python
import httpx
from datetime import datetime, timedelta

GITHUB_API_BASE = "https://api.github.com"

async def fetch_github_commits(
    pat: str,
    owner: str,
    repo: str,
    since_days: int = 7
) -> list[dict]:
    """Fetch commits from GitHub API."""
    since = (datetime.utcnow() - timedelta(days=since_days)).isoformat() + "Z"

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{GITHUB_API_BASE}/repos/{owner}/{repo}/commits",
            params={"since": since, "per_page": 100},
            headers={
                "Authorization": f"Bearer {pat}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=30.0,
        )
        response.raise_for_status()

        return [
            {
                "message": c["commit"]["message"].split("\n")[0],  # First line only
                "committed_at": c["commit"]["committer"]["date"],
            }
            for c in response.json()
        ]
```

---

## LLM Context Integration

### Additions to `get_context()` in `scheduler.py`

```python
# In get_context() function, add:

# Get recent GitHub activity
github_commits = await db.execute(
    select(GitHubCommit)
    .join(GitHubRepo)
    .where(GitHubCommit.user_id == user.id)
    .order_by(GitHubCommit.committed_at.desc())
    .limit(20)  # Last 20 commits max for context
)
github_activity = [
    {
        "repo": commit.repo.repo_name,
        "message": commit.commit_message,
        "date": commit.committed_at.strftime("%Y-%m-%d"),
    }
    for commit in github_commits.scalars().all()
]

# Calculate days since last commit
last_commit = github_activity[0] if github_activity else None
days_since_commit = None
if last_commit:
    last_date = datetime.strptime(last_commit["date"], "%Y-%m-%d")
    days_since_commit = (datetime.utcnow().date() - last_date.date()).days

# Add to context dict
context["github_activity"] = github_activity
context["days_since_commit"] = days_since_commit
```

### New Prompt Template (editable in Check-in Prompts UI)

Add to `DEFAULT_PROMPTS` in `llm.py`:

```python
"github_context": """GitHub Activity Context:
If the user has recent GitHub commits, you're aware of what they've been working on.
Use this to provide informed accountability - you can reference specific repos or
the general nature of their commits when relevant.

Only mention GitHub activity when:
- It's been 2+ days since their last commit (noteworthy silence)
- They claim to have worked on something but there are no matching commits
- You're celebrating productivity (high commit activity)
- It's directly relevant to a commitment they made

Don't spam about commits every check-in. Use this context naturally, not robotically."""
```

---

## UI Components

### Settings Tab Addition

Add a "GitHub Integration" section to the Settings tab:

```
┌─────────────────────────────────────────────────────────────┐
│ GITHUB INTEGRATION                                    [OFF] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Personal Access Token                                       │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ ghp_xxxxxxxxxxxxxxxxxxxx                          [👁]  │ │
│ └─────────────────────────────────────────────────────────┘ │
│ Generate at: github.com/settings/tokens (read-only scope)  │
│                                                             │
│ Monitored Repositories                                      │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ ☑ treynortetik-creator/accountability_agent             │ │
│ │ ☑ treynortetik-creator/other-project                    │ │
│ │ ☐ treynortetik-creator/archived-thing                   │ │
│ │                                              [+ Add Repo]│ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Poll Schedule                                               │
│ Time: [03]:[30]  (before your morning check-in)            │
│                                                             │
│ Data Retention                                              │
│ Keep last [ 7 ▼] days of commit history                    │
│                                                             │
│                                         [Test Connection]   │
└─────────────────────────────────────────────────────────────┘
```

### Dashboard Widget

Add a small "Recent Activity" widget to the main dashboard:

```
┌──────────────────────────────────────┐
│ GITHUB ACTIVITY              [⟳ 3h] │
├──────────────────────────────────────┤
│ accountability_agent                 │
│   • fix: json import        today    │
│   • fix: weekly_review      today    │
│   • fix: daily_checkin      today    │
│                                      │
│ other-project                        │
│   • feat: new feature       2d ago   │
│                                      │
│ 7 commits in last 7 days             │
└──────────────────────────────────────┘
```

---

## Error Handling

### Failure Tracking

Track consecutive failures per repo:

```python
# In github_repos table, add:
consecutive_failures INT DEFAULT 0
last_error TEXT
last_error_at TIMESTAMPTZ
```

### Error Flow

```
GitHub API call fails
       │
       ▼
┌─────────────────┐
│ Increment       │
│ consecutive_    │
│ failures        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     No      ┌─────────────────┐
│ failures >= 3?  │────────────▶│ Log to ErrorLog │
└────────┬────────┘             │ (silent)        │
         │ Yes                  └─────────────────┘
         ▼
┌─────────────────┐
│ Send Telegram   │
│ notification    │
│ to user         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Disable repo    │
│ until fixed     │
└─────────────────┘
```

### Notification Message

```
"Hey, I've been trying to check your GitHub activity but something's wrong.
Failed 3 times on [repo_name]: [error_message].
Might want to check your access token. I've paused monitoring that repo for now."
```

---

## Implementation Plan

### Phase 1: Core Infrastructure
1. Create database migrations for `github_repos` and `github_commits` tables
2. Add settings keys for GitHub configuration
3. Create `github_service.py` with API integration

### Phase 2: Scheduler Integration
4. Add `github_poll_job` to scheduler
5. Add `github_cleanup_job` to scheduler
6. Integrate with `get_context()` for LLM awareness

### Phase 3: UI - Settings
7. Add GitHub Integration section to Settings tab
8. Implement repo add/remove/toggle functionality
9. Add PAT storage (encrypted) and test connection

### Phase 4: UI - Dashboard Widget
10. Add Recent Activity widget to dashboard
11. Style to match cyberpunk theme

### Phase 5: Polish
12. Add `github_context` prompt template to Check-in Prompts
13. Test error handling and notifications
14. Documentation

---

## Environment Variables

Add to Railway:

| Variable | Description |
|----------|-------------|
| None required | PAT stored in database settings |

The PAT is stored in the database `settings` table (key: `github_pat`) rather than as an environment variable because:
- User can update it via UI without redeploying
- Follows existing pattern for user-configurable settings
- Could support multi-user in future

---

## Security Considerations

1. **PAT Scope**: User generates token with `repo:read` scope only (or `public_repo` for public repos)
2. **Storage**: PAT stored in database, displayed masked in UI
3. **Transmission**: All GitHub API calls over HTTPS
4. **Access**: Only the authenticated user can view/modify their GitHub settings

---

## Testing Checklist

- [ ] PAT validation (test connection button)
- [ ] Successful commit fetch and storage
- [ ] Retention cleanup works correctly
- [ ] Context injection includes GitHub data
- [ ] Warden references commits naturally in check-ins
- [ ] Error handling notifies after 3 failures
- [ ] UI displays commit history correctly
- [ ] Adding/removing repos works
- [ ] Poll schedule respects configured time
