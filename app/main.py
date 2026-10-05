from fastapi import FastAPI

from app.config import settings
from app.database import Base, engine
from app.models import User  # noqa: F401 — registers the model with Base
from app.routers import auth, health

app = FastAPI(
    title=settings.app_name,
    description="Unified Single Sign-On & Digital Campus Wallet",
    version=settings.app_version,
)

# Create tables on startup. Fine for development; we'll move to migrations later.
Base.metadata.create_all(bind=engine)

# Register routers
app.include_router(health.router)
app.include_router(auth.router)


@app.get("/", tags=["Root"])
def read_root():
    return {
        "message": f"Welcome to {settings.app_name}",
        "status": "ok",
        "version": settings.app_version,
    }