from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()

__all__ = ["app_config"]


class AppConfig(BaseModel):
    google_client_id: str
    google_client_secret: str
    starlette_session_key: str


app_config = AppConfig(
    google_client_id=os.getenv("GOOGLE_CLIENT_ID"),
    google_client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    starlette_session_key=os.getenv("STARLET_SECRET_KEY"),
)
