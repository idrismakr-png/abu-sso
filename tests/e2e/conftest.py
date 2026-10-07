"""E2E test fixtures: spawn a live server + browser for system tests."""
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import httpx
import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
E2E_PORT = 8001
BASE_URL = f"http://127.0.0.1:{E2E_PORT}"


@pytest.fixture(scope="session")
def live_server():
    """Start uvicorn on a test port with a temp SQLite DB."""
    tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp_db.close()

    env = os.environ.copy()
    env["DATABASE_URL"] = f"sqlite:///{tmp_db.name}"
    env["JWT_SECRET"] = "e2e-test-secret-key-which-is-long-enough-32-bytes"
    env["PYTHONPATH"] = str(ROOT)

    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app",
         "--host", "127.0.0.1", "--port", str(E2E_PORT), "--log-level", "warning"],
        cwd=str(ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    # Wait for the server to accept requests (max 30s)
    for _ in range(60):
        try:
            r = httpx.get(f"{BASE_URL}/health", timeout=1.0)
            if r.status_code == 200:
                break
        except Exception:
            time.sleep(0.5)
    else:
        proc.terminate()
        pytest.fail("Live server did not start within 30 seconds")

    yield BASE_URL

    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
    try:
        os.unlink(tmp_db.name)
    except OSError:
        pass


@pytest.fixture(scope="session")
def base_url(live_server):
    """Overrides pytest-playwright's base_url so `page.goto(base_url)` hits our test server."""
    return live_server


@pytest.fixture
def registered_user(live_server):
    """Create a fresh user via API for each test."""
    import uuid
    email = f"e2e_{uuid.uuid4().hex[:8]}@abu.edu.ng"
    httpx.post(
        f"{live_server}/auth/register",
        json={
            "email": email,
            "password": "secret123",
            "full_name": "E2E Tester",
            "role": "student",
            "matric_no": "E2E/2026/001",
        },
        timeout=5.0,
    )
    return {"email": email, "password": "secret123"}