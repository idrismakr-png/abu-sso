from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router = APIRouter(tags=["Pages"])


@router.get("/login", response_class=HTMLResponse, include_in_schema=False)
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html")


@router.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
def dashboard_page(request: Request):
    return templates.TemplateResponse(request, "dashboard.html")