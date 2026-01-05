"""GitHub integration API router."""

import logging
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from app.database import get_db
from app.auth import verify_api_key
from app.db_models import Settings, GitHubRepo, GitHubCommit, User
from app.github_service import validate_github_token, fetch_user_repos, GitHubAPIError
from app.user_service import get_default_user
from app.scheduler import schedule_github_poll

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/github", tags=["github"])


# Pydantic Models
class GitHubSettingsResponse(BaseModel):
    enabled: bool
    has_token: bool
    poll_hour: int
    poll_minute: int
    retention_days: int
    repos: List[dict]


class GitHubTokenUpdate(BaseModel):
    token: str


class GitHubRepoAdd(BaseModel):
    owner: str
    name: str


class GitHubScheduleUpdate(BaseModel):
    hour: int
    minute: int


class GitHubRetentionUpdate(BaseModel):
    days: int


class GitHubCommitResponse(BaseModel):
    id: int
    repo_name: str
    commit_message: str
    committed_at: str

    model_config = {"from_attributes": True}


# Helper functions
async def get_setting(db: AsyncSession, user: User, key: str, default: str = "") -> str:
    """Get a setting value from the database."""
    result = await db.execute(
        select(Settings).where(Settings.user_id == user.id, Settings.key == key)
    )
    setting = result.scalar_one_or_none()
    return setting.value if setting else default


async def set_setting(db: AsyncSession, user: User, key: str, value: str) -> None:
    """Set a setting value in the database."""
    result = await db.execute(
        select(Settings).where(Settings.user_id == user.id, Settings.key == key)
    )
    setting = result.scalar_one_or_none()
    if setting:
        setting.value = value
    else:
        setting = Settings(user_id=user.id, key=key, value=value)
        db.add(setting)
    await db.flush()


# Endpoints
@router.get("", response_model=GitHubSettingsResponse)
async def get_github_settings(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Get GitHub integration settings."""
    user = await get_default_user(db)

    token = await get_setting(db, user, "github_pat", "")
    poll_hour = int(await get_setting(db, user, "github_poll_hour", "3"))
    poll_minute = int(await get_setting(db, user, "github_poll_minute", "30"))
    retention_days = int(await get_setting(db, user, "github_retention_days", "7"))

    # Get repos
    repos_result = await db.execute(
        select(GitHubRepo).where(GitHubRepo.user_id == user.id)
    )
    repos = [
        {
            "id": r.id,
            "owner": r.repo_owner,
            "name": r.repo_name,
            "full_name": f"{r.repo_owner}/{r.repo_name}",
            "enabled": r.enabled,
            "consecutive_failures": r.consecutive_failures,
            "last_error": r.last_error,
        }
        for r in repos_result.scalars().all()
    ]

    return GitHubSettingsResponse(
        enabled=bool(token and repos),
        has_token=bool(token),
        poll_hour=poll_hour,
        poll_minute=poll_minute,
        retention_days=retention_days,
        repos=repos,
    )


@router.post("/token")
async def set_github_token(
    update: GitHubTokenUpdate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Set or update the GitHub Personal Access Token."""
    user = await get_default_user(db)

    # Validate the token first
    is_valid, message = await validate_github_token(update.token)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Invalid token: {message}")

    await set_setting(db, user, "github_pat", update.token)
    await db.commit()

    # Reschedule the GitHub poll job
    await schedule_github_poll()

    return {"status": "success", "message": message}


@router.delete("/token")
async def remove_github_token(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Remove the GitHub Personal Access Token."""
    user = await get_default_user(db)

    result = await db.execute(
        select(Settings).where(
            Settings.user_id == user.id,
            Settings.key == "github_pat"
        )
    )
    setting = result.scalar_one_or_none()
    if setting:
        await db.delete(setting)
        await db.commit()

    return {"status": "success", "message": "GitHub token removed"}


@router.get("/token/test")
async def test_github_token(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Test the current GitHub token."""
    user = await get_default_user(db)
    token = await get_setting(db, user, "github_pat", "")

    if not token:
        raise HTTPException(status_code=400, detail="No GitHub token configured")

    is_valid, message = await validate_github_token(token)
    return {"valid": is_valid, "message": message}


@router.get("/repos/available")
async def list_available_repos(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """List repositories available to add (from GitHub)."""
    user = await get_default_user(db)
    token = await get_setting(db, user, "github_pat", "")

    if not token:
        raise HTTPException(status_code=400, detail="No GitHub token configured")

    try:
        repos = await fetch_user_repos(token)

        # Get already added repos
        added_result = await db.execute(
            select(GitHubRepo).where(GitHubRepo.user_id == user.id)
        )
        added_repos = {f"{r.repo_owner}/{r.repo_name}" for r in added_result.scalars().all()}

        # Filter out already added repos
        available = [r for r in repos if r["full_name"] not in added_repos]

        return {"repos": available}

    except GitHubAPIError as e:
        raise HTTPException(status_code=400, detail=str(e.message))


@router.post("/repos")
async def add_github_repo(
    repo: GitHubRepoAdd,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Add a repository to monitor."""
    user = await get_default_user(db)

    # Check if already exists
    existing = await db.execute(
        select(GitHubRepo).where(
            GitHubRepo.user_id == user.id,
            GitHubRepo.repo_owner == repo.owner,
            GitHubRepo.repo_name == repo.name,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Repository already added")

    new_repo = GitHubRepo(
        user_id=user.id,
        repo_owner=repo.owner,
        repo_name=repo.name,
        enabled=True,
    )
    db.add(new_repo)
    await db.commit()

    return {"status": "success", "id": new_repo.id}


@router.delete("/repos/{repo_id}")
async def remove_github_repo(
    repo_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Remove a repository from monitoring."""
    user = await get_default_user(db)

    result = await db.execute(
        select(GitHubRepo).where(
            GitHubRepo.id == repo_id,
            GitHubRepo.user_id == user.id,
        )
    )
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    await db.delete(repo)
    await db.commit()

    return {"status": "success"}


@router.put("/repos/{repo_id}/toggle")
async def toggle_github_repo(
    repo_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Toggle a repository's enabled status."""
    user = await get_default_user(db)

    result = await db.execute(
        select(GitHubRepo).where(
            GitHubRepo.id == repo_id,
            GitHubRepo.user_id == user.id,
        )
    )
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    repo.enabled = not repo.enabled
    # Reset failure count when re-enabling
    if repo.enabled:
        repo.consecutive_failures = 0
        repo.last_error = None
        repo.last_error_at = None

    await db.commit()

    return {"status": "success", "enabled": repo.enabled}


@router.put("/schedule")
async def update_poll_schedule(
    update: GitHubScheduleUpdate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Update the GitHub poll schedule."""
    user = await get_default_user(db)

    if update.hour < 0 or update.hour > 23:
        raise HTTPException(status_code=400, detail="Hour must be 0-23")
    if update.minute < 0 or update.minute > 59:
        raise HTTPException(status_code=400, detail="Minute must be 0-59")

    await set_setting(db, user, "github_poll_hour", str(update.hour))
    await set_setting(db, user, "github_poll_minute", str(update.minute))
    await db.commit()

    # Reschedule the job
    await schedule_github_poll()

    return {"status": "success", "hour": update.hour, "minute": update.minute}


@router.put("/retention")
async def update_retention(
    update: GitHubRetentionUpdate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Update the commit retention period."""
    user = await get_default_user(db)

    if update.days < 1 or update.days > 30:
        raise HTTPException(status_code=400, detail="Retention must be 1-30 days")

    await set_setting(db, user, "github_retention_days", str(update.days))
    await db.commit()

    return {"status": "success", "days": update.days}


@router.get("/commits", response_model=List[GitHubCommitResponse])
async def get_recent_commits(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Get recent commits across all monitored repos."""
    user = await get_default_user(db)

    result = await db.execute(
        select(GitHubCommit)
        .join(GitHubRepo)
        .where(GitHubCommit.user_id == user.id)
        .order_by(GitHubCommit.committed_at.desc())
        .limit(limit)
    )

    commits = []
    for commit in result.scalars().all():
        commits.append(GitHubCommitResponse(
            id=commit.id,
            repo_name=commit.repo.repo_name,
            commit_message=commit.commit_message,
            committed_at=commit.committed_at.isoformat(),
        ))

    return commits


@router.post("/poll")
async def trigger_poll(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Manually trigger a GitHub poll."""
    from app.scheduler import github_poll_job

    try:
        await github_poll_job()
        return {"status": "success", "message": "GitHub poll completed"}
    except Exception as e:
        logger.error(f"Manual GitHub poll failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
