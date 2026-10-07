"""Mock LMS (Moodle) service — demonstrates SSO. Independent app on port 4002."""
import os
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

IDP_URL = os.getenv("IDP_URL", "http://127.0.0.1:8000")
SERVICE_NAME = "LMS (Moodle)"
SERVICE_COLOR = "#6a1b9a"
SERVICE_DESCRIPTION = "Lectures, assignments, quizzes, and course materials."

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

app = FastAPI(title=f"{SERVICE_NAME} (Mock)")


async def verify_token_with_idp(token: str) -> dict:
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
    return {"service": "lms", "status": "ok"}