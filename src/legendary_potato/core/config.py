from pydantic import BaseModel, Field
import os
from dotenv import load_dotenv
from ..utils.services.db_utils import get_database_url

load_dotenv()

__all__ = ["app_config"]


class AppConfig(BaseModel):
    google_client_id: str
    google_client_secret: str
    starlette_session_key: str
    database_url: str | None = None
    api_jwt_secret: str | None = None
    api_jwt_issuer: str = "legendary_potato"
    api_jwt_ttl_seconds: int = 60 * 60 * 24 * 7  # 7 days
    refresh_token_ttl_seconds: int = 60 * 60 * 24 * 30  # 30 days
    max_html_bytes: int = 1_500_000  # ~1.5MB
    cors_allow_origin_regex: str | None = r"chrome-extension://.*"
    extension_return_to_allowlist: list[str] = Field(default_factory=list)
    uvicorn_port: int = 8001
    public_domain: str | None = None
    env: str = "local"


app_config = AppConfig(
    google_client_id=os.environ["GOOGLE_CLIENT_ID"],
    google_client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
    starlette_session_key=os.environ["STARLET_SECRET_KEY"],
    database_url=get_database_url(),
    api_jwt_secret=os.environ.get("API_JWT_SECRET"),
    api_jwt_issuer=os.environ.get("API_JWT_ISSUER", "legendary_potato"),
    api_jwt_ttl_seconds=int(os.environ.get("API_JWT_TTL_SECONDS", 60 * 60 * 24 * 7)),
    refresh_token_ttl_seconds=int(
        os.environ.get("REFRESH_TOKEN_TTL_SECONDS", 60 * 60 * 24 * 30)
    ),
    max_html_bytes=int(os.environ.get("MAX_HTML_BYTES", 1_500_000)),
    cors_allow_origin_regex=os.environ.get("CORS_ALLOW_ORIGIN_REGEX", r"chrome-extension://.*"),
    extension_return_to_allowlist=[
        s.strip()
        for s in os.environ.get("EXTENSION_RETURN_TO_ALLOWLIST", "").split(",")
        if s.strip()
    ],
    uvicorn_port=int(os.environ.get("UVICORN_PORT", 8001)),
    public_domain=os.environ.get("PUBLIC_DOMAIN"),
    env=os.environ.get("ENV", "local"),
)