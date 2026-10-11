"""Shared pytest fixtures for ABU-SSO tests (unit + service + integration + E2E)."""
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
TEST_DB_PATH = _tmp_db.name
_tmp_db.close()

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Transaction, User, Wallet  # noqa: E402,F401

engine = create_engine(
    f"sqlite:///{TEST_DB_PATH}",
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    try:
        os.unlink(TEST_DB_PATH)
    except OSError:
        pass


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(autouse=True)
def clean_tables():
    yield
    session = TestingSessionLocal()
    try:
        session.query(Transaction).delete()
        session.query(Wallet).delete()
        session.query(User).delete()
        session.commit()
    finally:
        session.close()


# ---------- E2E fixtures ----------

E2E_PORT = 8001
E2E_BASE_URL = f"http://127.0.0.1:{E2E_PORT}"


@pytest.fixture(scope="session")
def live_server():
    """Spawn a real uvicorn subprocess on a separate port with its own temp DB."""
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

    for _ in range(60):
        try:
            r = httpx.get(f"{E2E_BASE_URL}/health", timeout=1.0)
            if r.status_code == 200:
                break
        except Exception:
            time.sleep(0.5)
    else:
        proc.terminate()
        pytest.fail("Live server did not start within 30 seconds")

    yield E2E_BASE_URL

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
    """Override pytest-playwright's base_url so tests hit our live server."""
    return live_server


@pytest.fixture
def registered_user(live_server):
    """Create a fresh user in the live server and return matric + password."""
    import uuid
    matric = f"E2E/{uuid.uuid4().hex[:8].upper()}"
    httpx.post(
        f"{live_server}/auth/register",
        json={
            "email": f"{matric.replace('/', '_').lower()}@abu.edu.ng",
            "password": "secret123",
            "full_name": "E2E Tester",
            "role": "student",
            "matric_no": matric,
        },
        timeout=5.0,
    )
    return {"matric_no": matric, "password": "secret123"}