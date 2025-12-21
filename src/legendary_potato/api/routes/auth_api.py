from fastapi import APIRouter, Depends, Request

from ..dependencies import get_session_user_id
from ...core.tokens import create_access_token

__all__ = ["router"]


router = APIRouter()


@router.get("/auth/status")
async def auth_status(request: Request):
    return {"logged_in": bool(request.session.get("user_id"))}


@router.post("/auth/token")
async def auth_token(user_id=Depends(get_session_user_id)):
    token = create_access_token(user_id=user_id)
    return {"access_token": token, "token_type": "bearer"}

