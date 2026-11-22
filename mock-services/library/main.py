
"""University Library — OIDC client for the central ABU-SSO identity provider."""

import os
import secrets
import time
from pathlib import Path

from authlib.integrations.starlette_client import OAuth
from authlib.integrations.base_client.errors import OAuthError
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

# One-time server-side tickets prevent replay of a browser session cookie.
PENDING_LANDINGS: dict[str, tuple[str, float]] = {}
LANDING_TICKET_TTL_SECONDS = 30

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

# Keep the IdP endpoints local and deterministic. Avoid a network
# discovery request during module import or on every login attempt.
oauth.register(
    name="abu_sso",
    client_id=CLIENT_ID,
    server_metadata={
        "issuer": IDP_URL,
        "authorization_endpoint": f"{IDP_URL}/authorize",
        "token_endpoint": f"{IDP_URL}/token",
        "userinfo_endpoint": f"{IDP_URL}/userinfo",
        "jwks_uri": f"{IDP_URL}/jwks.json",
        "revocation_endpoint": f"{IDP_URL}/revoke",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code"],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": ["RS256"],
        "token_endpoint_auth_methods_supported": ["none"],
        "code_challenge_methods_supported": ["S256"],
    },
    client_kwargs={
        "scope": "openid profile email",
        "code_challenge_method": "S256",
        "token_endpoint_auth_method": "none",
    },
)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request, landing: str = ""):
    # A service-local session is not sufficient. The OIDC callback must
    # issue a fresh, unconsumed server-side landing ticket.
    now = time.monotonic()
    expired = [
        ticket for ticket, (_, created_at) in PENDING_LANDINGS.items()
        if now - created_at > LANDING_TICKET_TTL_SECONDS
    ]
    for ticket in expired:
        PENDING_LANDINGS.pop(ticket, None)

    pending = PENDING_LANDINGS.pop(landing, None) if landing else None
    user = request.session.get("user")
    if (
        pending is None
        or now - pending[1] > LANDING_TICKET_TTL_SECONDS
        or not user
        or user.get("id") != pending[0]
    ):
        request.session.clear()
        return RedirectResponse(url="/login", status_code=303)

    return templates.TemplateResponse(
        request,
        "service.html",
        {
            "service_name": SERVICE_NAME,
            "service_color": SERVICE_COLOR,
            "service_description": SERVICE_DESCRIPTION,
            "user": user,
            "token": None,
        },
    )

@app.get("/login")
async def login(request: Request):
    nonce = secrets.token_urlsafe(32)
    return await oauth.abu_sso.authorize_redirect(
        request,
        REDIRECT_URI,
        nonce=nonce,
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
        landing_ticket = secrets.token_urlsafe(32)
        PENDING_LANDINGS[landing_ticket] = (
            profile["sub"],
            time.monotonic(),
        )

        return RedirectResponse(
            url=f"/?landing={landing_ticket}",
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
