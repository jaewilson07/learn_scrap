from ..core.oauth import oauth

from fastapi import APIRouter, Request
from starlette.responses import RedirectResponse


router = APIRouter()


@router.get("/login")
async def login(request: Request):
    # Generate the redirect URI dynamically
    redirect_uri = request.url_for("auth_google_callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/auth/google/callback")
async def auth_google_callback(request: Request):
    pass


@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/")
