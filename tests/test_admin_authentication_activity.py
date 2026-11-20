
from app.models import AuthenticationEvent
from app.services.user_service import create_user


def _create_user(db, matric, email, role):
    return create_user(
        db,
        email=email,
        password="secret123",
        matric_no=matric,
        full_name="Activity Test User",
        role=role,
    )


def _login(client, matric):
    response = client.post(
        "/auth/login",
        json={
            "matric_no": matric,
            "password": "secret123",
        },
    )
    assert response.status_code == 200
    return {
        "Authorization": f"Bearer {response.json()['access_token']}"
    }


def _add_event(db, user_id, application, outcome, method="password"):
    event = AuthenticationEvent(
        user_id=user_id,
        application_name=application,
        event_type="authorization",
        outcome=outcome,
        authentication_method=method,
        ip_address="192.0.2.10",
        user_agent="Admin activity test",
        failure_reason="invalid_credentials" if outcome == "failure" else None,
    )
    db.add(event)
    db.commit()
    return event


def test_admin_can_view_authentication_activity(client, db):
    admin = _create_user(
        db,
        "ADMIN/ACTIVITY/001",
        "admin-activity@abu.edu.ng",
        "admin",
    )
    student = _create_user(
        db,
        "STUDENT/ACTIVITY/001",
        "student-activity@abu.edu.ng",
        "student",
    )

    _add_event(
        db,
        student.id,
        "Learning Management System",
        "success",
        "existing_sso_session",
    )

    headers = _login(client, "ADMIN/ACTIVITY/001")

    response = client.get(
        "/admin/authentication-activity",
        headers=headers,
    )

    assert response.status_code == 200
    activities = response.json()

    assert any(
        item["application_name"] == "Learning Management System"
        and item["user_id"] == student.id
        for item in activities
    )


def test_admin_can_filter_activity_by_application_and_outcome(client, db):
    admin = _create_user(
        db,
        "ADMIN/ACTIVITY/002",
        "admin-activity2@abu.edu.ng",
        "admin",
    )
    student = _create_user(
        db,
        "STUDENT/ACTIVITY/002",
        "student-activity2@abu.edu.ng",
        "student",
    )

    _add_event(
        db,
        student.id,
        "Learning Management System",
        "success",
    )
    _add_event(
        db,
        student.id,
        "Results Portal",
        "failure",
    )

    headers = _login(client, "ADMIN/ACTIVITY/002")

    response = client.get(
        "/admin/authentication-activity",
        params={
            "application": "Results",
            "outcome": "failure",
        },
        headers=headers,
    )

    assert response.status_code == 200
    activities = response.json()

    assert len(activities) == 1
    assert activities[0]["application_name"] == "Results Portal"
    assert activities[0]["outcome"] == "failure"
    assert activities[0]["failure_reason"] == "invalid_credentials"


def test_student_cannot_view_admin_authentication_activity(client, db):
    _create_user(
        db,
        "STUDENT/ACTIVITY/003",
        "student-activity3@abu.edu.ng",
        "student",
    )

    headers = _login(client, "STUDENT/ACTIVITY/003")

    response = client.get(
        "/admin/authentication-activity",
        headers=headers,
    )

    assert response.status_code == 403


def test_authentication_activity_requires_admin_login(client):
    response = client.get("/admin/authentication-activity")

    assert response.status_code == 401


def test_admin_activity_rejects_invalid_outcome_filter(client, db):
    _create_user(
        db,
        "ADMIN/ACTIVITY/004",
        "admin-activity4@abu.edu.ng",
        "admin",
    )

    headers = _login(client, "ADMIN/ACTIVITY/004")

    response = client.get(
        "/admin/authentication-activity?outcome=pending",
        headers=headers,
    )

    assert response.status_code == 422
