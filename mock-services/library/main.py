
"""University Library — OIDC client for the central ABU-SSO identity provider."""

import os
import secrets
import time
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
    "http://127.0.0.1:4003/auth/callback",
)
SESSION_SECRET = os.getenv("SESSION_SECRET", "")

SERVICE_NAME = "University Library"
SERVICE_COLOR = "#c62828"
SERVICE_DESCRIPTION = "Borrowed books, fines, and reservations."

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
    session_cookie="abu_library_session",
    max_age=600,
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

    # Permit only the immediate landing after the OIDC callback.
    # Every later visit must re-check the central identity provider.
    if not user or not request.session.pop("allow_home_once", False):
        request.session.clear()
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
    nonce = secrets.token_urlsafe(32)
    return await oauth.abu_sso.authorize_redirect(
        request,
        REDIRECT_URI,
        nonce=nonce,
        prompt="none",
    )


@app.get("/auth/callback")
async def auth_callback(request: Request):
    try:
        token = await oauth.abu_sso.authorize_access_token(request)

        response = await oauth.abu_sso.get(
            f"{IDP_URL}/userinfo",
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
        request.session["idp_verified_at"] = time.time()
        request.session["allow_home_once"] = True

        return RedirectResponse(
            url="/",
            status_code=303,
        )

    except HTTPException:
        raise
    except Exception:
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
        "service": "library",
        "status": "ok",
    }
