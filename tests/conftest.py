"""Shared pytest fixtures for ABU-SSO — with full diagnostics."""
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

# ============ Import app modules ============
import app.database as db_module
from app.database import Base, get_db
from app.models import Transaction, User, Wallet
from app.main import app

# ============ One test engine, shared by EVERYTHING ============
test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Create tables on the shared engine.
Base.metadata.create_all(bind=test_engine)

# Patch the app's module-level engine + session factory.
# Anything that calls `SessionLocal()` from app.database now uses the test engine.
db_module.engine = test_engine
db_module.SessionLocal = TestSession


def _override_get_db():
    s = TestSession()
    try:
        yield s
    finally:
        s.close()


# Also override the FastAPI dependency (belt and braces).
app.dependency_overrides[get_db] = _override_get_db


# --- Diagnostic helper (called by fixtures) ---
def _tables_in_engine(engine):
    import sqlite3
    with engine.connect() as conn:
        cursor = conn.connection.cursor()
        rows = cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        return [r[0] for r in rows]


print(f"\n[conftest] test_engine id={id(test_engine)} url={test_engine.url}")
print(f"[conftest] db_module.engine is test_engine? {db_module.engine is test_engine}")
print(f"[conftest] db_module.SessionLocal is TestSession? {db_module.SessionLocal is TestSession}")
print(f"[conftest] Tables right after create_all: {_tables_in_engine(test_engine)}\n")


# ============ Fixtures ============

@pytest.fixture(autouse=True)
def diag_and_cleanup():
    """Before each test: print tables. After: clean rows."""
    tables_before = _tables_in_engine(test_engine)
    if "users" not in tables_before:
        print(f"\n[!] tables missing before test: {tables_before}")
        Base.metadata.create_all(bind=test_engine)
        print(f"[!] recreated. now: {_tables_in_engine(test_engine)}")
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


# ============ E2E fixtures ============

E2E_PORT = 8001
E2E_BASE_URL = f"http://127.0.0.1:{E2E_PORT}"


@pytest.fixture(scope="session")
def live_server():
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
    return live_server


@pytest.fixture
def registered_user(live_server):
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