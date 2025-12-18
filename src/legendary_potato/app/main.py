from ..core.config import app_config, AppConfig

from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from ..api.routes import public, auth


__all__ = ["app"]

# Create the application instance
app = FastAPI()

# required to "remember" the user after they log in
app.add_middleware(SessionMiddleware, secret_key=app_config.starlette_session_key)

app.include_router(public.router, tags=["public"])
app.include_router(auth.router, tags=["auth"])
