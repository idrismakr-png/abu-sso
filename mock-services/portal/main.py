
"""Student Portal — OIDC client for the central ABU-SSO identity provider."""

import logging
import os
import secrets
from pathlib import Path

from authlib.integrations.starlette_client import OAuth
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

IDP_URL = os.getenv("IDP_URL", "http://localhost:8000").rstrip("/")
CLIENT_ID = os.getenv("OIDC_CLIENT_ID", "")
REDIRECT_URI = os.getenv(
    "OIDC_REDIRECT_URI",
    "http://127.0.0.1:4001/auth/callback",
)
SESSION_SECRET = os.getenv("SESSION_SECRET", "")

logger = logging.getLogger(__name__)

SERVICE_NAME = "Student Portal"
SERVICE_COLOR = "#0b3d91"
SERVICE_DESCRIPTION = (
    "Course registration, results, and transcript requests."
)

if not CLIENT_ID:
    raise RuntimeError("OIDC_CLIENT_ID must be configured.")

if not SESSION_SECRET:
    if os.getenv("RENDER"):
        raise RuntimeError(
            "SESSION_SECRET must be configured in the Render environment."
        )
    SESSION_SECRET = "local-development-only-change-this-secret"

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

app = FastAPI(title=f"{SERVICE_NAME} (OIDC Client)")

app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    session_cookie="abu_portal_session",
    max_age=3600,
    same_site="lax",
    https_only=IDP_URL.startswith("https://"),
)

oauth = OAuth()

oauth.register(
    name="abu_sso",
    client_id=CLIENT_ID,
    server_metadata_url=(
        f"{IDP_URL}/.well-known/openid-configuration"
    ),
    client_kwargs={
        "scope": "openid profile email",
        "code_challenge_method": "S256",
        "token_endpoint_auth_method": "none",
    },
)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    user = request.session.get("user")

    if not user:
        return RedirectResponse(
            url="/login",
            status_code=303,
        )

    return templates.TemplateResponse(
        request,
        "service.html",
        {
            "service_name": SERVICE_NAME,
            "service_color": SERVICE_COLOR,
            "service_description": SERVICE_DESCRIPTION,
            "user": user,
        },
    )


@app.get("/login")
async def login(request: Request):
    redirect_uri = REDIRECT_URI

    nonce = secrets.token_urlsafe(32)
    return await oauth.abu_sso.authorize_redirect(
        request,
        redirect_uri,
        nonce=nonce,
    )


@app.get("/auth/callback")
async def auth_callback(request: Request):
    try:
        token = await oauth.abu_sso.authorize_access_token(request)

        response = await oauth.abu_sso.get(
            "userinfo",
            token=token,
        )
        response.raise_for_status()
        profile = response.json()

        if not profile.get("sub"):
            raise HTTPException(
                status_code=401,
                detail="Identity provider returned no subject claim.",
            )

        request.session.clear()
        request.session["user"] = {
            "id": profile["sub"],
            "full_name": profile.get("name") or "ABU User",
            "email": profile.get("email") or "",
            "role": "Not supplied by OIDC userinfo",
            "matric_no": "Not supplied by OIDC userinfo",
        }

        return RedirectResponse(
            url="/",
            status_code=303,
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(
            "OIDC callback failed for %s (%s): %s",
            SERVICE_NAME,
            type(exc).__name__,
            str(exc),
        )
        request.session.clear()
        raise HTTPException(
            status_code=401,
            detail="OIDC authentication failed. Please try again.",
        )


@app.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(
        url="/",
        status_code=303,
    )


@app.get("/health")
def health():
    return {
        "service": "portal",
        "status": "ok",
    }
