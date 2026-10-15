"""Authorization matrix — verifies every protected endpoint enforces auth."""
import importlib.util
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.services.user_service import create_user


AUTHENTICATED_ENDPOINTS = [
    ("GET", "/auth/me", None),
    ("GET", "/id-card", None),
    ("GET", "/wallet", None),
    ("GET", "/wallet/transactions", None),
    ("POST", "/wallet/topup", {"amount": 100}),
    ("POST", "/wallet/pay", {"amount": 100}),
]

ADMIN_ENDPOINTS = [
    ("GET", "/admin/users", None),
    ("POST", "/admin/users", {
        "email": "new@abu.edu.ng",
        "password": "secret123",
        "matric_no": "NEW/001",
    }),
    ("PATCH", "/admin/users/some-id/role", {"role": "staff"}),
    ("PATCH", "/admin/users/some-id/active?active=false", None),
    ("POST", "/admin/wallet/topup", {"user_id": "some-id", "amount": 100}),
    ("GET", "/admin/stats", None),
]


def _login(client, matric, password="secret123"):
    res = client.post("/auth/login", json={"matric_no": matric, "password": password})
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


# ============ 1. Authenticated endpoints: no token -> 401 ============

@pytest.mark.parametrize("method,path,body", AUTHENTICATED_ENDPOINTS)
def test_authenticated_endpoint_requires_token(client, method, path, body):
    kwargs = {"json": body} if body else {}
    res = getattr(client, method.lower())(path, **kwargs)
    assert res.status_code == 401, f"{method} {path} returned {res.status_code}"


# ============ 2. Admin endpoints: no token -> 401 ============

@pytest.mark.parametrize("method,path,body", ADMIN_ENDPOINTS)
def test_admin_endpoint_requires_token(client, method, path, body):
    kwargs = {"json": body} if body else {}
    res = getattr(client, method.lower())(path, **kwargs)
    assert res.status_code == 401, f"{method} {path} returned {res.status_code}"


# ============ 3. Admin endpoints: student token -> 403 ============

@pytest.mark.parametrize("method,path,body", ADMIN_ENDPOINTS)
def test_admin_endpoint_forbids_students(client, db, method, path, body):
    create_user(db, email="s@abu.edu.ng", password="secret123", matric_no="STU/001", role="student")
    headers = _login(client, "STU/001")
    kwargs = {"json": body} if body else {}
    res = getattr(client, method.lower())(path, headers=headers, **kwargs)
    assert res.status_code == 403, f"{method} {path} returned {res.status_code}"


# ============ 4. Admin endpoints: staff token -> 403 ============

@pytest.mark.parametrize("method,path,body", ADMIN_ENDPOINTS)
def test_admin_endpoint_forbids_staff(client, db, method, path, body):
    create_user(db, email="st@abu.edu.ng", password="secret123", matric_no="STAFF/001", role="staff")
    headers = _login(client, "STAFF/001")
    kwargs = {"json": body} if body else {}
    res = getattr(client, method.lower())(path, headers=headers, **kwargs)
    assert res.status_code == 403, f"{method} {path} returned {res.status_code}"


# ============ 5. Positive: admin CAN access admin endpoints ============

def test_admin_can_access_admin_stats(client, db):
    create_user(db, email="a@abu.edu.ng", password="secret123", matric_no="ADM/001", role="admin")
    headers = _login(client, "ADM/001")
    res = client.get("/admin/stats", headers=headers)
    assert res.status_code == 200


# ============ 6. Mock services reject missing/invalid tokens ============

MOCK_SERVICES = ["portal", "lms", "library", "hostel", "wifi", "results"]


def _load_mock_app(service):
    path = Path(__file__).resolve().parent.parent / "mock-services" / service / "main.py"
    spec = importlib.util.spec_from_file_location(f"mock_{service}", str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.app


@pytest.mark.parametrize("service", MOCK_SERVICES)
def test_mock_service_requires_token(service):
    app = _load_mock_app(service)
    with TestClient(app) as c:
        res = c.get("/")
        assert res.status_code == 401, f"{service} did not require token"


@pytest.mark.parametrize("service", MOCK_SERVICES)
def test_mock_service_rejects_invalid_token(service):
    app = _load_mock_app(service)
    with TestClient(app) as c:
        res = c.get("/?token=fake-token")
        assert res.status_code in (401, 503), f"{service} accepted invalid token"
