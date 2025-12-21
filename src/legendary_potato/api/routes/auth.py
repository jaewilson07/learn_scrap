from fastapi import APIRouter, Request
from starlette.responses import RedirectResponse, JSONResponse

from ...api.dependencies import get_db
from ...core.config import app_config
from ...core.security import oauth
from ...core.tokens import create_access_token

router = APIRouter()


def _is_allowed_return_to(return_to: str) -> bool:
    """
    Allowlist rules:
    - Entries in EXTENSION_RETURN_TO_ALLOWLIST can be either:
      - a full URL (exact match), e.g. chrome-extension://<id>/auth.html
      - an origin prefix ending with '/', e.g. chrome-extension://<id>/
    """
    if not return_to.startswith("chrome-extension://"):
        return False

    allowlist = app_config.extension_return_to_allowlist
    if not allowlist:
        # In production we require explicit allowlisting.
        return app_config.env != "production"

    for entry in allowlist:
        if entry.endswith("/"):
            if return_to.startswith(entry):
                return True
        else:
            if return_to == entry:
                return True
    return False


@router.get("/login")
async def login(request: Request, return_to: str | None = None):
    """
    Starts Google OAuth.

    If `return_to` is provided (e.g. a chrome extension URL), we will redirect
    there after login with an access token in the URL fragment.
    """
    if return_to:
        if not _is_allowed_return_to(return_to):
            msg = "Invalid return_to"
            if app_config.env == "production" and not app_config.extension_return_to_allowlist:
                msg = "return_to not allowed; configure EXTENSION_RETURN_TO_ALLOWLIST"
            return JSONResponse(status_code=400, content={"error": msg})
        request.session["return_to"] = return_to

    redirect_uri = request.url_for("auth_google_callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/auth/google/callback")
async def auth_google_callback(request: Request):
    try:
        db = get_db(request)
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get("userinfo")
        user_id = None
        if user_info:
            request.session["user"] = dict(user_info)

            provider = "google"
            provider_subject = user_info.get("sub")
            if provider_subject:
                user_id = await db.get_or_create_user_id_for_identity(
                    provider=provider,
                    provider_subject=str(provider_subject),
                    email=user_info.get("email"),
                    name=user_info.get("name"),
                    avatar_url=user_info.get("picture"),
                )
                request.session["user_id"] = str(user_id)

        return_to = request.session.pop("return_to", None)
        if return_to and user_id is not None:
            access_token = create_access_token(user_id=user_id)
            # Use fragment so the token doesn't hit server logs.
            redirect = f"{return_to}#access_token={access_token}&token_type=bearer"
            return RedirectResponse(url=redirect)

        return RedirectResponse(url="/")
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"error": "Authentication failed", "detail": str(e)},
        )

@router.get("/logout")
async def logout(request: Request):
    request.session.pop("user", None)
    request.session.pop("user_id", None)
    return RedirectResponse(url="/")