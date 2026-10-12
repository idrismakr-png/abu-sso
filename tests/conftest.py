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
from sqlalchemy.pool import StaticPool

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ["ALLOW_PUBLIC_REGISTRATION"] = "true"
os.environ["JWT_SECRET"] = "test-secret-key-with-at-least-32-bytes-length-ok"

import app.database as db_module  # noqa: E402
from app.database import Base, get_db  # noqa: E402
from app.models import Transaction, User, Wallet  # noqa: E402,F401
from app.main import app  # noqa: E402

test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

Base.metadata.create_all(bind=test_engine)

db_module.engine = test_engine
db_module.SessionLocal = TestSession


def _override_get_db():
    s = TestSession()
    try:
        yield s
    finally:
        s.close()


app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture(autouse=True)
def clean_tables():
    yield
    s = TestSession()
    try:
        s.query(Transaction).delete()
        s.query(Wallet).delete()
        s.query(User).delete()
        s.commit()
    except Exception:
        s.rollback()
    finally:
        s.close()


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db():
    s = TestSession()
    try:
        yield s
    finally:
        s.close()


E2E_PORT = 8001
E2E_BASE_URL = f"http://127.0.0.1:{E2E_PORT}"


@pytest.fixture(scope="session")
def e2e_live_server():
    tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp_db.close()

    env = os.environ.copy()
    env["DATABASE_URL"] = f"sqlite:///{Path(tmp_db.name).as_posix()}"
    env["JWT_SECRET"] = "e2e-test-secret-key-which-is-long-enough-32-bytes"
    env["ALLOW_PUBLIC_REGISTRATION"] = "true"
    env["PYTHONPATH"] = str(ROOT)

    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app",
         "--host", "127.0.0.1", "--port", str(E2E_PORT), "--log-level", "warning"],
        cwd=str(ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    # trust_env=False ignores HTTP_PROXY/HTTPS_PROXY env vars, which on
    # Windows can hijack 127.0.0.1 traffic and cause silent timeouts.
    ready = False
    with httpx.Client(trust_env=False, timeout=1.0) as client:
        for _ in range(60):
            try:
                r = client.get(f"{E2E_BASE_URL}/health")
                if r.status_code == 200:
                    ready = True
                    break
            except Exception:
                time.sleep(0.5)

    if not ready:
        proc.terminate()
        pytest.fail("E2E live server did not start within 30 seconds")

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
def e2e_base_url(e2e_live_server):
    return e2e_live_server


@pytest.fixture
def registered_user(e2e_live_server):
    import uuid
    matric = f"E2E/{uuid.uuid4().hex[:8].upper()}"
    with httpx.Client(trust_env=False, timeout=5.0) as client:
        client.post(
            f"{e2e_live_server}/auth/register",
            json={
                "email": f"{matric.replace('/', '_').lower()}@abu.edu.ng",
                "password": "secret123",
                "full_name": "E2E Tester",
                "role": "student",
                "matric_no": matric,
            },
        )
    return {"matric_no": matric, "password": "secret123"}
