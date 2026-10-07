import os
import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# --- Setup a temporary test database BEFORE importing the app ---
_tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
TEST_DB_PATH = _tmp_db.name
_tmp_db.close()

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"

# Now import the app and models (they will read DATABASE_URL above)
from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Transaction, User, Wallet  # noqa: E402,F401

# Fresh engine bound to the temp DB
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
    """Create all tables once per test session, drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    try:
        os.unlink(TEST_DB_PATH)
    except OSError:
        pass


@pytest.fixture
def client():
    """FastAPI TestClient for integration tests."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db():
    """Direct DB session for service-level tests."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(autouse=True)
def clean_tables():
    """Wipe tables before each test to keep tests independent."""
    yield
    session = TestingSessionLocal()
    try:
        session.query(Transaction).delete()
        session.query(Wallet).delete()
        session.query(User).delete()
        session.commit()
    finally:
        session.close()
        