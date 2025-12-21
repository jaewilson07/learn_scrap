import time
import uuid

import jwt
from jwt import InvalidTokenError

from .config import app_config

__all__ = ["create_access_token", "verify_access_token"]


def create_access_token(*, user_id: uuid.UUID) -> str:
    if not app_config.api_jwt_secret:
        raise RuntimeError("API_JWT_SECRET is not configured")

    now = int(time.time())
    payload = {
        "iss": app_config.api_jwt_issuer,
        "sub": str(user_id),
        "iat": now,
        "exp": now + int(app_config.api_jwt_ttl_seconds),
        "typ": "access",
    }
    return jwt.encode(payload, app_config.api_jwt_secret, algorithm="HS256")


def verify_access_token(token: str) -> uuid.UUID:
    if not app_config.api_jwt_secret:
        raise RuntimeError("API_JWT_SECRET is not configured")

    payload = jwt.decode(
        token,
        app_config.api_jwt_secret,
        algorithms=["HS256"],
        issuer=app_config.api_jwt_issuer,
        options={"require": ["exp", "iat", "iss", "sub"]},
    )
    if payload.get("typ") != "access":
        raise InvalidTokenError("Invalid token type")
    return uuid.UUID(str(payload["sub"]))

