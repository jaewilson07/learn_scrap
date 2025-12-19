from ...core.security import oauth
from fastapi import APIRouter, Request
from starlette.responses import RedirectResponse, JSONResponse

router = APIRouter()

@router.get("/login")
async def login(request: Request):
    redirect_uri = request.url_for("auth_google_callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/auth/google/callback")
async def auth_google_callback(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get("userinfo")
        if user_info:
            request.session["user"] = dict(user_info)
        return RedirectResponse(url="/")
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"error": "Authentication failed", "detail": str(e)},
        )

@router.get("/logout")
async def logout(request: Request):
    request.session.pop("user", None)
    return RedirectResponse(url="/")