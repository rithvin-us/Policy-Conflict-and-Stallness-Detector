"""GitHub API proxy routes for the automated onboarding flow."""
from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, Query

router = APIRouter()

_API = "https://api.github.com"


def _get_headers(authorization: str | None = Header(None)) -> dict:
    if not authorization:
        raise HTTPException(401, "GitHub Personal Access Token is required")
    return {
        "Authorization": authorization,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


@router.get("/user")
def get_user(headers: dict = Depends(_get_headers)):
    """Fetch the authenticated user's profile."""
    try:
        r = httpx.get(f"{_API}/user", headers=headers, timeout=10)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPError as e:
        raise HTTPException(400, f"Failed to fetch user: {e}")


@router.get("/orgs")
def list_orgs(headers: dict = Depends(_get_headers)):
    """List organizations for the authenticated user."""
    try:
        r = httpx.get(f"{_API}/user/orgs", headers=headers, timeout=10)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPError as e:
        raise HTTPException(400, f"Failed to fetch orgs: {e}")


@router.get("/repos")
def list_repos(
    org: str | None = Query(None, description="Organization name. If missing, fetches user's repos."),
    page: int = Query(1),
    per_page: int = Query(50),
    headers: dict = Depends(_get_headers),
):
    """List repositories for a specific org or the authenticated user."""
    try:
        if org:
            url = f"{_API}/orgs/{org}/repos"
        else:
            # For user repos, we fetch repos that the user owns or has explicit access to
            url = f"{_API}/user/repos"
        
        # Sort by updated to show most recently active repos first
        params = {"page": page, "per_page": per_page, "sort": "updated"}
        
        r = httpx.get(url, headers=headers, params=params, timeout=15)
        r.raise_for_status()
        return {"items": r.json()}
    except httpx.HTTPError as e:
        raise HTTPException(400, f"Failed to fetch repos: {e}")
