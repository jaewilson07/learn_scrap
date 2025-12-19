from pydantic import BaseModel
import os


__all__ = ["app_config"]


class AppConfig(BaseModel):
    google_client_id: str
    google_client_secret: str
    starlette_session_key: str
    uvicorn_port: int = 8001
    public_domain: str | None = None
    env: str = "local"


app_config = AppConfig(
    google_client_id=os.environ["GOOGLE_CLIENT_ID"],
    google_client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
    starlette_session_key=os.environ["STARLET_SECRET_KEY"],
    uvicorn_port=int(os.environ.get("UVICORN_PORT", 8001)),
    public_domain=os.environ.get("PUBLIC_DOMAIN"),
    env=os.environ.get("ENV", "local"),
)