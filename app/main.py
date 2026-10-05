from fastapi import FastAPI

app = FastAPI(
    title="ABU-SSO",
    description="Unified Single Sign-On & Digital Campus Wallet",
    version="0.1.0",
)


@app.get("/")
def read_root():
    return {"message": "Welcome to ABU-SSO", "status": "ok"}


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "abu-sso"}