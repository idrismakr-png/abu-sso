
"""Authorization matrix — verifies protected endpoints and service authentication."""

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
    ("POST", "/admin/wallet/topup", {
        "user_id": "some-id",
        "amount": 100,
    }),
    ("GET", "/admin/stats", None),
]


def _login(client, matric, password="secret123"):
    res = client.post(
        "/auth/login",
        json={"matric_no": matric, "password": password},
    )
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


@pytest.mark.parametrize("method,path,body", AUTHENTICATED_ENDPOINTS)
def test_authenticated_endpoint_requires_token(client, method, path, body):
    kwargs = {"json": body} if body else {}
    res = getattr(client, method.lower())(path, **kwargs)
    assert res.status_code == 401, (
        f"{method} {path} returned {res.status_code}"
    )


@pytest.mark.parametrize("method,path,body", ADMIN_ENDPOINTS)
def test_admin_endpoint_requires_token(client, method, path, body):
    kwargs = {"json": body} if body else {}
    res = getattr(client, method.lower())(path, **kwargs)
    assert res.status_code == 401, (
        f"{method} {path} returned {res.status_code}"
    )


@pytest.mark.parametrize("method,path,body", ADMIN_ENDPOINTS)
def test_admin_endpoint_forbids_students(client, db, method, path, body):
    create_user(
        db,
        email="s@abu.edu.ng",
        password="secret123",
        matric_no="STU/001",
        role="student",
    )
    headers = _login(client, "STU/001")
    kwargs = {"json": body} if body else {}
    res = getattr(client, method.lower())(
        path,
        headers=headers,
        **kwargs,
    )
    assert res.status_code == 403, (
        f"{method} {path} returned {res.status_code}"
    )


@pytest.mark.parametrize("method,path,body", ADMIN_ENDPOINTS)
def test_admin_endpoint_forbids_staff(client, db, method, path, body):
    create_user(
        db,
        email="st@abu.edu.ng",
        password="secret123",
        matric_no="STAFF/001",
        role="staff",
    )
    headers = _login(client, "STAFF/001")
    kwargs = {"json": body} if body else {}
    res = getattr(client, method.lower())(
        path,
        headers=headers,
        **kwargs,
    )
    assert res.status_code == 403, (
        f"{method} {path} returned {res.status_code}"
    )


def test_admin_can_access_admin_stats(client, db):
    create_user(
        db,
        email="a@abu.edu.ng",
        password="secret123",
        matric_no="ADM/001",
        role="admin",
    )
    headers = _login(client, "ADM/001")
    res = client.get("/admin/stats", headers=headers)
    assert res.status_code == 200


MOCK_SERVICES = [
    "portal",
    "lms",
    "library",
    "hostel",
    "wifi",
    "results",
]

OIDC_SERVICES = ["portal", "lms"]


def _load_mock_app(service):
    path = (
        Path(__file__).resolve().parent.parent
        / "mock-services"
        / service
        / "main.py"
    )
    spec = importlib.util.spec_from_file_location(
        f"mock_{service}",
        str(path),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.app


@pytest.mark.parametrize("service", OIDC_SERVICES)
def test_oidc_service_redirects_unauthenticated_visitors_to_login(service):
    app = _load_mock_app(service)
    with TestClient(app, follow_redirects=False) as client:
        res = client.get("/")
        assert res.status_code == 303
        assert res.headers["location"] == "/login"


@pytest.mark.parametrize("service", OIDC_SERVICES)
def test_oidc_service_does_not_accept_legacy_token_query(service):
    app = _load_mock_app(service)
    with TestClient(app, follow_redirects=False) as client:
        res = client.get("/?token=fake-token")
        assert res.status_code == 303
        assert res.headers["location"] == "/login"


LEGACY_TOKEN_SERVICES = [
    service for service in MOCK_SERVICES
    if service not in OIDC_SERVICES
]


@pytest.mark.parametrize("service", LEGACY_TOKEN_SERVICES)
def test_legacy_mock_service_requires_token(service):
    app = _load_mock_app(service)
    with TestClient(app) as client:
        res = client.get("/")
        assert res.status_code == 401, (
            f"{service} did not require token"
        )


@pytest.mark.parametrize("service", LEGACY_TOKEN_SERVICES)
def test_legacy_mock_service_rejects_invalid_token(service):
    app = _load_mock_app(service)
    with TestClient(app) as client:
        res = client.get("/?token=fake-token")
        assert res.status_code in (401, 503), (
            f"{service} accepted invalid token"
        )
