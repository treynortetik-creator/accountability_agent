"""GitHub API integration for The Warden."""

import logging
from datetime import datetime, timedelta
from typing import Optional
import httpx

logger = logging.getLogger(__name__)

GITHUB_API_BASE = "https://api.github.com"


class GitHubAPIError(Exception):
    """Custom exception for GitHub API errors."""

    def __init__(self, message: str, status_code: int = None, response_body: str = None):
        self.message = message
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(self.message)


async def fetch_github_commits(
    pat: str,
    owner: str,
    repo: str,
    since_days: int = 7,
) -> list[dict]:
    """Fetch commits from GitHub API.

    Args:
        pat: Personal Access Token for GitHub
        owner: Repository owner (username or org)
        repo: Repository name
        since_days: How many days back to fetch commits

    Returns:
        List of commit dicts with message and committed_at

    Raises:
        GitHubAPIError: If the API request fails
    """
    since = (datetime.utcnow() - timedelta(days=since_days)).isoformat() + "Z"

    try:
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

            if response.status_code == 401:
                raise GitHubAPIError(
                    "Invalid or expired GitHub token",
                    status_code=401,
                    response_body=response.text,
                )
            elif response.status_code == 403:
                raise GitHubAPIError(
                    "GitHub API rate limit exceeded or access forbidden",
                    status_code=403,
                    response_body=response.text,
                )
            elif response.status_code == 404:
                raise GitHubAPIError(
                    f"Repository {owner}/{repo} not found or not accessible",
                    status_code=404,
                    response_body=response.text,
                )
            elif response.status_code >= 400:
                raise GitHubAPIError(
                    f"GitHub API error: {response.status_code}",
                    status_code=response.status_code,
                    response_body=response.text,
                )

            commits_data = response.json()

            return [
                {
                    "message": c["commit"]["message"].split("\n")[0],  # First line only
                    "committed_at": datetime.fromisoformat(
                        c["commit"]["committer"]["date"].replace("Z", "+00:00")
                    ),
                }
                for c in commits_data
            ]

    except httpx.TimeoutException:
        raise GitHubAPIError("GitHub API request timed out")
    except httpx.RequestError as e:
        raise GitHubAPIError(f"Network error connecting to GitHub: {str(e)}")


async def validate_github_token(pat: str) -> tuple[bool, str]:
    """Validate a GitHub personal access token.

    Args:
        pat: Personal Access Token to validate

    Returns:
        Tuple of (is_valid, message)
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GITHUB_API_BASE}/user",
                headers={
                    "Authorization": f"Bearer {pat}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
                timeout=10.0,
            )

            if response.status_code == 200:
                user_data = response.json()
                username = user_data.get("login", "unknown")
                return True, f"Valid token for user: {username}"
            elif response.status_code == 401:
                return False, "Invalid or expired token"
            else:
                return False, f"Unexpected response: {response.status_code}"

    except httpx.TimeoutException:
        return False, "Connection timed out"
    except httpx.RequestError as e:
        return False, f"Connection error: {str(e)}"


async def fetch_user_repos(pat: str) -> list[dict]:
    """Fetch list of repositories accessible to the authenticated user.

    Args:
        pat: Personal Access Token for GitHub

    Returns:
        List of repo dicts with owner and name

    Raises:
        GitHubAPIError: If the API request fails
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GITHUB_API_BASE}/user/repos",
                params={"per_page": 100, "sort": "pushed", "direction": "desc"},
                headers={
                    "Authorization": f"Bearer {pat}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
                timeout=30.0,
            )

            if response.status_code != 200:
                raise GitHubAPIError(
                    f"Failed to fetch repos: {response.status_code}",
                    status_code=response.status_code,
                    response_body=response.text,
                )

            repos_data = response.json()

            return [
                {
                    "owner": r["owner"]["login"],
                    "name": r["name"],
                    "full_name": r["full_name"],
                    "private": r["private"],
                    "pushed_at": r.get("pushed_at"),
                }
                for r in repos_data
            ]

    except httpx.TimeoutException:
        raise GitHubAPIError("GitHub API request timed out")
    except httpx.RequestError as e:
        raise GitHubAPIError(f"Network error connecting to GitHub: {str(e)}")
