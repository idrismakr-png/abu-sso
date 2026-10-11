"""Tests for admin-only endpoints and RBAC enforcement."""

from app.services import admin_service
from app.services.user_service import create_user


def _create_admin(db, matric="ADMIN/001", email="admin@abu.edu.ng"):
    return create_user(db, email=email, password="secret123", matric_no=matric, role="admin")


def _create_student(db, matric="STU/001", email="student@abu.edu.ng"):
    return create_user(db, email=email, password="secret123", matric_no=matric, role="student")


def _login(client, matric, password="secret123"):
    res = client.post("/auth/login", json={"matric_no": matric, "password": password})
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


# ---------- RBAC ENFORCEMENT ----------

def test_admin_endpoints_require_auth(client):
    """Without a token, every admin endpoint returns 401."""
    for method, path in [
        ("get", "/admin/users"),
        ("get", "/admin/stats"),
    ]:
        res = getattr(client, method)(path)
        assert res.status_code == 401, f"{path} did not require auth"


def test_admin_endpoints_forbid_students(client, db):
    """Students must receive 403 on admin endpoints."""
    _create_student(db)
    headers = _login(client, "STU/001")
    for method, path in [
        ("get", "/admin/users"),
        ("get", "/admin/stats"),
    ]:
        res = getattr(client, method)(path, headers=headers)
        assert res.status_code == 403, f"{path} did not forbid student"


# ---------- LIST USERS ----------

def test_admin_can_list_users(client, db):
    _create_admin(db)
    _create_student(db)
    headers = _login(client, "ADMIN/001")
    res = client.get("/admin/users", headers=headers)
    assert res.status_code == 200
    matrics = [u["matric_no"] for u in res.json()]
    assert "ADMIN/001" in matrics
    assert "STU/001" in matrics


# ---------- CREATE USER ----------

def test_admin_can_create_new_user(client, db):
    _create_admin(db)
    headers = _login(client, "ADMIN/001")
    res = client.post(
        "/admin/users",
        json={
            "email": "created@abu.edu.ng",
            "password": "newpass123",
            "full_name": "Created Student",
            "role": "student",
            "matric_no": "ABU/2026/XYZ",
        },
        headers=headers,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["email"] == "created@abu.edu.ng"
    assert data["matric_no"] == "ABU/2026/XYZ"
    assert data["role"] == "student"
    assert "password" not in data
    assert "password_hash" not in data


def test_admin_create_user_rejects_duplicate_email(client, db):
    _create_admin(db)
    _create_student(db, email="dup@abu.edu.ng", matric="DUP/001")
    headers = _login(client, "ADMIN/001")
    res = client.post(
        "/admin/users",
        json={
            "email": "dup@abu.edu.ng",
            "password": "pass1234",
            "role": "student",
            "matric_no": "OTHER/999",
        },
        headers=headers,
    )
    assert res.status_code == 400


def test_admin_create_user_rejects_duplicate_matric(client, db):
    _create_admin(db)
    _create_student(db, email="first@abu.edu.ng", matric="SAME/123")
    headers = _login(client, "ADMIN/001")
    res = client.post(
        "/admin/users",
        json={
            "email": "second@abu.edu.ng",
            "password": "pass1234",
            "role": "student",
            "matric_no": "SAME/123",
        },
        headers=headers,
    )
    assert res.status_code == 400


def test_student_cannot_create_users(client, db):
    """A student must not be able to call POST /admin/users."""
    _create_student(db)
    headers = _login(client, "STU/001")
    res = client.post(
        "/admin/users",
        json={
            "email": "sneaky@abu.edu.ng",
            "password": "pass1234",
            "role": "admin",
            "matric_no": "SNEAK/001",
        },
        headers=headers,
    )
    assert res.status_code == 403


# ---------- ROLE CHANGE ----------

def test_admin_can_change_role(client, db):
    _create_admin(db)
    student = _create_student(db)
    headers = _login(client, "ADMIN/001")
    res = client.patch(
        f"/admin/users/{student.id}/role",
        json={"role": "staff"},
        headers=headers,
    )
    assert res.status_code == 200
    assert res.json()["role"] == "staff"


def test_admin_role_change_rejects_invalid_role(client, db):
    _create_admin(db)
    student = _create_student(db)
    headers = _login(client, "ADMIN/001")
    res = client.patch(
        f"/admin/users/{student.id}/role",
        json={"role": "superhero"},
        headers=headers,
    )
    assert res.status_code == 422


def test_admin_role_change_unknown_user_returns_404(client, db):
    _create_admin(db)
    headers = _login(client, "ADMIN/001")
    res = client.patch(
        "/admin/users/does-not-exist/role",
        json={"role": "staff"},
        headers=headers,
    )
    assert res.status_code == 404


# ---------- ACTIVATE / DEACTIVATE ----------

def test_admin_can_deactivate_and_reactivate(client, db):
    _create_admin(db)
    student = _create_student(db)
    headers = _login(client, "ADMIN/001")

    res = client.patch(f"/admin/users/{student.id}/active?active=false", headers=headers)
    assert res.status_code == 200
    assert res.json()["is_active"] is False

    res = client.patch(f"/admin/users/{student.id}/active?active=true", headers=headers)
    assert res.status_code == 200
    assert res.json()["is_active"] is True


def test_deactivated_user_cannot_log_in(client, db):
    _create_admin(db)
    student = _create_student(db)
    headers = _login(client, "ADMIN/001")
    client.patch(f"/admin/users/{student.id}/active?active=false", headers=headers)

    res = client.post(
        "/auth/login",
        json={"matric_no": "STU/001", "password": "secret123"},
    )
    assert res.status_code == 401


# ---------- ADMIN TOP-UP ----------

def test_admin_can_top_up_another_wallet(client, db):
    _create_admin(db)
    student = _create_student(db)
    headers = _login(client, "ADMIN/001")
    res = client.post(
        "/admin/wallet/topup",
        json={"user_id": student.id, "amount": 1000, "description": "Scholarship"},
        headers=headers,
    )
    assert res.status_code == 201
    assert res.json()["type"] == "credit"
    assert res.json()["amount"] == "1000.00"


def test_admin_topup_unknown_user_returns_404(client, db):
    _create_admin(db)
    headers = _login(client, "ADMIN/001")
    res = client.post(
        "/admin/wallet/topup",
        json={"user_id": "ghost", "amount": 100},
        headers=headers,
    )
    assert res.status_code == 404


def test_admin_topup_rejects_negative_amount(client, db):
    _create_admin(db)
    student = _create_student(db)
    headers = _login(client, "ADMIN/001")
    res = client.post(
        "/admin/wallet/topup",
        json={"user_id": student.id, "amount": -50},
        headers=headers,
    )
    assert res.status_code == 422


# ---------- STATS ----------

def test_admin_stats_reflect_system_state(client, db):
    _create_admin(db)
    student = _create_student(db)
    headers = _login(client, "ADMIN/001")
    client.post(
        "/admin/wallet/topup",
        json={"user_id": student.id, "amount": 500},
        headers=headers,
    )

    res = client.get("/admin/stats", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total_users"] == 2
    assert data["active_users"] == 2
    assert data["total_transactions"] == 1
    assert data["total_balance"] == "500.00"


# ---------- SERVICE-LEVEL TESTS ----------

def test_set_user_role_unknown_user_raises(db):
    import pytest
    with pytest.raises(ValueError):
        admin_service.set_user_role(db, "missing", "admin")


def test_set_user_active_unknown_user_raises(db):
    import pytest
    with pytest.raises(ValueError):
        admin_service.set_user_active(db, "missing", False)


def test_admin_top_up_unknown_user_raises(db):
    import pytest
    from decimal import Decimal
    with pytest.raises(ValueError):
        admin_service.admin_top_up(db, "missing", Decimal("10"))


def test_list_all_users_returns_all(db):
    _create_admin(db, matric="ADMIN/AAA", email="a1@abu.edu.ng")
    _create_admin(db, matric="ADMIN/BBB", email="a2@abu.edu.ng")
    users = admin_service.list_all_users(db)
    assert len(users) == 2