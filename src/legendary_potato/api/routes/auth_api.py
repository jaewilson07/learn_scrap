from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from ..dependencies import get_bearer_user_id, get_db, get_rate_limiter, get_session_user_id
from ...core.db import Db

from ...core.tokens import create_access_token

__all__ = ["router"]


router = APIRouter()


@router.get("/auth/status")
async def auth_status(request: Request):
    return {"logged_in": bool(request.session.get("user_id"))}


@router.post("/auth/token")
async def auth_token(
    user_id=Depends(get_session_user_id),
    db: Db = Depends(get_db),
):
    token = create_access_token(user_id=user_id)
    refresh_token = await db.issue_refresh_token(user_id=user_id)
    return {"access_token": token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.get("/me")
async def me(
    user_id=Depends(get_bearer_user_id),
    db: Db = Depends(get_db),
):
    identities = await db.get_identities(user_id=user_id)
    for r in identities:
        r["created_at"] = r["created_at"].isoformat()
    return {"user_id": str(user_id), "identities": identities}


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/auth/refresh")
async def refresh(
    payload: RefreshRequest,
    db: Db = Depends(get_db),
    rl=Depends(get_rate_limiter),
):
    if not rl.allow(key=f"auth:refresh:{payload.refresh_token[:12]}", limit=30, window_seconds=60):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    try:
        user_id, new_refresh = await db.rotate_refresh_token(refresh_token=payload.refresh_token)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    access = create_access_token(user_id=user_id)
    return {"access_token": access, "refresh_token": new_refresh, "token_type": "bearer"}


@router.post("/auth/revoke")
async def revoke(
    user_id=Depends(get_bearer_user_id),
    db: Db = Depends(get_db),
):
    count = await db.revoke_refresh_tokens_for_user(user_id=user_id)
    return {"revoked": count}

