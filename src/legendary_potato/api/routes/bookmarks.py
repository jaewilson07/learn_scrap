from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..dependencies import get_bearer_user_id, get_db, get_rate_limiter
from ...core.config import app_config
from ...core.db import Db

__all__ = ["router"]


router = APIRouter()


class BookmarkCreate(BaseModel):
    url: str = Field(min_length=1)
    title: str | None = None
    html: str | None = None


@router.post("/bookmarks")
async def create_bookmark(
    payload: BookmarkCreate,
    user_id=Depends(get_bearer_user_id),
    db: Db = Depends(get_db),
    rl=Depends(get_rate_limiter),
):
    if not rl.allow(key=f"bookmark:create:{user_id}", limit=60, window_seconds=60):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    if payload.html is not None:
        if len(payload.html.encode("utf-8")) > int(app_config.max_html_bytes):
            raise HTTPException(
                status_code=413,
                detail=f"HTML too large (max {app_config.max_html_bytes} bytes)",
            )

    bookmark_id = await db.create_bookmark(
        user_id=user_id, url=payload.url, title=payload.title, html=payload.html
    )
    return {"id": str(bookmark_id)}


@router.get("/bookmarks")
async def list_bookmarks(
    limit: int = 50,
    user_id=Depends(get_bearer_user_id),
    db: Db = Depends(get_db),
):
    limit = max(1, min(int(limit), 200))
    rows = await db.list_bookmarks(user_id=user_id, limit=limit)
    for r in rows:
        r["id"] = str(r["id"])
        r["created_at"] = r["created_at"].isoformat()
    return {"bookmarks": rows}

