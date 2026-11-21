
from app.models import AuthenticationEvent
from app.services.user_service import create_user


def _create_student(db, matric, email):
    return create_user(
        db,
        email=email,
        password="secret123",
        matric_no=matric,
        full_name="Activity Test Student",
        role="student",
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


def test_student_can_view_own_authentication_activity(client, db):
    student = _create_student(
        db,
        "ACTIVITY/STUDENT/001",
        "activity-student@abu.edu.ng",
    )

    db.add_all([
        AuthenticationEvent(
            user_id=student.id,
            application_name="ABU-SSO Portal",
            event_type="login",
            outcome="success",
            authentication_method="password",
        ),
        AuthenticationEvent(
            user_id=student.id,
            application_name="Learning Management System",
            event_type="authorization",
            outcome="success",
            authentication_method="existing_sso_session",
        ),
    ])
    db.commit()

    headers = _login(client, "ACTIVITY/STUDENT/001")

    response = client.get(
        "/auth/activity",
        headers=headers,
    )

    assert response.status_code == 200

    activities = response.json()

    assert len(activities) == 3
    assert activities[0]["application_name"] == "ABU-SSO Portal"
    assert activities[0]["event_type"] == "login"
    assert activities[0]["outcome"] == "success"
    assert activities[0]["authentication_method"] == "password"

    assert all("ip_address" not in item for item in activities)
    assert all("user_agent" not in item for item in activities)


def test_student_cannot_view_another_students_activity(client, db):
    first_student = _create_student(
        db,
        "ACTIVITY/STUDENT/002",
        "activity-student2@abu.edu.ng",
    )
    second_student = _create_student(
        db,
        "ACTIVITY/STUDENT/003",
        "activity-student3@abu.edu.ng",
    )

    db.add(
        AuthenticationEvent(
            user_id=second_student.id,
            application_name="Results Portal",
            event_type="authorization",
            outcome="success",
            authentication_method="existing_sso_session",
        )
    )
    db.commit()

    headers = _login(client, "ACTIVITY/STUDENT/002")

    response = client.get(
        "/auth/activity",
        headers=headers,
    )

    assert response.status_code == 200

    activities = response.json()

    # The first student sees their own login event.
    assert activities
    assert all(
        item["application_name"] == "ABU-SSO Portal"
        for item in activities
    )

    # The second student's Results Portal event must remain private.
    assert not any(
        item["application_name"] == "Results Portal"
        for item in activities
    )


def test_authentication_activity_requires_login(client):
    response = client.get("/auth/activity")

    assert response.status_code == 401


def test_authentication_activity_limit_is_validated(client, db):
    _create_student(
        db,
        "ACTIVITY/STUDENT/004",
        "activity-student4@abu.edu.ng",
    )

    headers = _login(client, "ACTIVITY/STUDENT/004")

    response = client.get(
        "/auth/activity?limit=101",
        headers=headers,
    )

    assert response.status_code == 422
