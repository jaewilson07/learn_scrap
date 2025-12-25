from fastapi import APIRouter, Depends
from ...api.dependencies import get_current_user

__all__ = ["router"]

router = APIRouter()


@router.get("/profile")
async def profile(user: dict = Depends(get_current_user)):
    return {"message": "this is a protected profile page", "user": user}
