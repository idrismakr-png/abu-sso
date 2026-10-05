from fastapi import FastAPI

from app.config import settings
from app.routers import health

app = FastAPI(
    title=settings.app_name,
    description="Unified Single Sign-On & Digital Campus Wallet",
    version=settings.app_version,
)

# Register routers
app.include_router(health.router)


@app.get("/", tags=["Root"])
def read_root():
    return {
        "message": f"Welcome to {settings.app_name}",
        "status": "ok",
        "version": settings.app_version,
    }