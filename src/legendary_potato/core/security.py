import os

from fastapi import FastAPI, Request
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth

__all__ = ["oauth"]

oauth = OAuth()

oauth.register(
    name="google",
    client_id=google_client_id,  # Paste from Google Cloud
    client_secret=google_client_secret,  # Paste from Google Cloud
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)
