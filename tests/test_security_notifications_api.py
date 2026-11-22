
import uuid

from app.models import AuthenticationEvent, SecurityNotification
from app.services.user_service import create_user


def _create_student(db, suffix):
    return create_user(
        db,
        email=f"notification-{suffix}@abu.edu.ng",
        password="secret123",
        matric_no=f"NOTIFICATION/{suffix[:8]}",
        full_name="Notification API Tester",
        role="student",
    )


def _create_notification(db, user, application_name):
    event = AuthenticationEvent(
        user_id=user.id,
        client_id=f"client-{uuid.uuid4().hex}",
        application_name=application_name,
        event_type="authorization",
        outcome="success",
        authentication_method="existing_sso_session",
    )
    db.add(event)
    db.flush()

    notification = SecurityNotification(
        user_id=user.id,
        authentication_event_id=event.id,
        title=f"New sign-in to {application_name}",
        message=f"Your ABU account was used to authenticate with {application_name}.",
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification, event


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


def test_student_can_view_only_own_notifications(client, db):
    suffix = uuid.uuid4().hex
    first_student = _create_student(db, suffix)
    second_student = _create_student(db, uuid.uuid4().hex)

    own_notification, own_event = _create_notification(
        db, first_student, "Learning Management System"
    )
    other_notification, other_event = _create_notification(
        db, second_student, "Results Portal"
    )

    try:
        headers = _login(client, f"NOTIFICATION/{suffix[:8]}")

        response = client.get(
            "/auth/notifications",
            headers=headers,
        )

        assert response.status_code == 200
        notifications = response.json()

        # A successful central login also creates its own notification.
        # The service notification must be present, and another user's
        # notification must never be exposed.
        notification_ids = {item["id"] for item in notifications}
        assert own_notification.id in notification_ids
        assert other_notification.id not in notification_ids
        service_notification = next(
            item for item in notifications
            if item["id"] == own_notification.id
        )
        assert service_notification["title"] == (
            "New sign-in to Learning Management System"
        )
        assert service_notification["read_at"] is None
        assert "ip_address" not in service_notification
        assert "user_agent" not in service_notification

    finally:
        db.query(SecurityNotification).filter(
            SecurityNotification.id.in_([
                own_notification.id,
                other_notification.id,
            ])
        ).delete(synchronize_session=False)
        db.query(AuthenticationEvent).filter(
            AuthenticationEvent.id.in_([
                own_event.id,
                other_event.id,
            ])
        ).delete(synchronize_session=False)
        db.delete(first_student)
        db.delete(second_student)
        db.commit()


def test_student_can_mark_own_notification_as_read(client, db):
    suffix = uuid.uuid4().hex
    student = _create_student(db, suffix)
    notification, event = _create_notification(
        db, student, "Library Portal"
    )

    try:
        headers = _login(client, f"NOTIFICATION/{suffix[:8]}")

        response = client.patch(
            f"/auth/notifications/{notification.id}/read",
            headers=headers,
        )

        assert response.status_code == 200
        assert response.json()["id"] == notification.id
        assert response.json()["read_at"] is not None

        db.refresh(notification)
        assert notification.read_at is not None

    finally:
        db.delete(notification)
        db.delete(event)
        db.delete(student)
        db.commit()


def test_student_cannot_mark_another_students_notification_as_read(
    client, db
):
    first_suffix = uuid.uuid4().hex
    first_student = _create_student(db, first_suffix)
    second_student = _create_student(db, uuid.uuid4().hex)

    notification, event = _create_notification(
        db, second_student, "Hostel Portal"
    )

    try:
        headers = _login(
            client, f"NOTIFICATION/{first_suffix[:8]}"
        )

        response = client.patch(
            f"/auth/notifications/{notification.id}/read",
            headers=headers,
        )

        assert response.status_code == 404

        db.refresh(notification)
        assert notification.read_at is None

    finally:
        db.delete(notification)
        db.delete(event)
        db.delete(first_student)
        db.delete(second_student)
        db.commit()


def test_notifications_require_authentication(client):
    response = client.get("/auth/notifications")
    assert response.status_code == 401


def test_notification_limit_is_validated(client):
    response = client.get(
        "/auth/notifications?limit=101",
        headers={"Authorization": "Bearer invalid"},
    )
    assert response.status_code == 401
