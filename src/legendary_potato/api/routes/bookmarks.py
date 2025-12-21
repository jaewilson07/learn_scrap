from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from ..dependencies import get_bearer_user_id, get_db
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
):
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

