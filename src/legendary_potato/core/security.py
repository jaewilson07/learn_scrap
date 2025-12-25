from authlib.integrations.starlette_client import OAuth
from .config import app_config

__all__ = ["oauth"]

oauth = OAuth()

oauth.register(
    name="google",
    client_id=app_config.google_client_id,
    client_secret=app_config.google_client_secret,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)