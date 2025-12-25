import uuid

from fastapi import HTTPException, Request

from ..core.db import Db
from ..core.rate_limit import RateLimiter
from ..core.tokens import verify_access_token


def get_db(request: Request) -> Db:
    db = getattr(request.app.state, "db", None)
    if db is None:
        raise HTTPException(status_code=500, detail="Database is not configured")
    return db


def get_rate_limiter(request: Request) -> RateLimiter:
    rl = getattr(request.app.state, "rate_limiter", None)
    if rl is None:
        rl = RateLimiter()
        request.app.state.rate_limiter = rl
    return rl


def get_session_user_id(request: Request) -> uuid.UUID:
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return uuid.UUID(str(user_id))


def get_bearer_user_id(request: Request) -> uuid.UUID:
    auth = request.headers.get("authorization") or request.headers.get("Authorization")
    if not auth:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    parts = auth.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid Authorization header")

    try:
        return verify_access_token(parts[1])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_user(request: Request) -> dict:
    """
    Backwards-compatible helper for existing routes.
    """
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user
