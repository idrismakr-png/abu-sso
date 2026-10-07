"""Mock Student Portal service — demonstrates SSO.

This is an INDEPENDENT FastAPI app running on port 4001.
It does NOT contain any user database. Instead, when a request arrives,
it extracts the JWT from the URL/header and asks the ABU-SSO identity
provider to verify it via /auth/me.

If the IdP says the token is valid → serve the Portal page.
If not → return 401.
"""
import os

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

IDP_URL = os.getenv("IDP_URL", "http://127.0.0.1:8000")
SERVICE_NAME = "Student Portal"
SERVICE_COLOR = "#0b3d91"
SERVICE_DESCRIPTION = "Course registration, results, and transcript requests."

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

app = FastAPI(title=f"{SERVICE_NAME} (Mock)")


async def verify_token_with_idp(token: str) -> dict:
    """Ask the IdP to verify the JWT. Returns the user profile or raises 401."""
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(
                f"{IDP_URL}/auth/me",
                headers={"Authorization": f"Bearer {token}"},
                timeout=5.0,
            )
        except httpx.RequestError:
            raise HTTPException(503, "Identity provider unreachable")
    if res.status_code != 200:
        raise HTTPException(401, "Invalid or expired token")
    return res.json()


def extract_token(request: Request) -> str:
    """Token may arrive via Authorization header OR ?token= query param."""
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:]
    token = request.query_params.get("token")
    if token:
        return token
    raise HTTPException(401, "No token provided")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    token = extract_token(request)
    user = await verify_token_with_idp(token)
    return templates.TemplateResponse(
        request,
        "service.html",
        {
            "service_name": SERVICE_NAME,
            "service_color": SERVICE_COLOR,
            "service_description": SERVICE_DESCRIPTION,
            "user": user,
            "token": token,
        },
    )


@app.get("/health")
def health():
    return {"service": "portal", "status": "ok"}