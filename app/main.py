from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import Base, engine
from app.models import User, Transaction, Wallet  # noqa: F401 — registers models
from app.routers import auth, health, id_card, pages, wallet

app = FastAPI(
    title=settings.app_name,
    description="Unified Single Sign-On & Digital Campus Wallet",
    version=settings.app_version,
)

# Create tables on startup. Fine for development; we'll move to migrations later.
Base.metadata.create_all(bind=engine)

# Static files (CSS, JS)
STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Register routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(id_card.router)
app.include_router(wallet.router)
app.include_router(pages.router)


@app.get("/", tags=["Root"])
def read_root():
    return {
        "message": f"Welcome to {settings.app_name}",
        "status": "ok",
        "version": settings.app_version,
    }