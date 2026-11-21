
from app.models import AuthenticationEvent, SecurityNotification
from app.services.security_notification_service import (
    create_authentication_notification,
)
from app.services.user_service import create_user


def _create_student(db):
    return create_user(
        db,
        email="notification-test@abu.edu.ng",
        password="secret123",
        matric_no="NOTIFICATION/001",
        full_name="Notification Test Student",
        role="student",
    )


def test_successful_authorization_creates_notification(db):
    student = _create_student(db)

    event = AuthenticationEvent(
        user_id=student.id,
        client_id="notification-test-client",
        application_name="Learning Management System",
        event_type="authorization",
        outcome="success",
        authentication_method="existing_sso_session",
    )

    db.add(event)
    db.flush()

    notification = create_authentication_notification(db, event)

    assert notification is not None
    assert notification.user_id == student.id
    assert notification.authentication_event_id == event.id
    assert notification.title == (
        "New sign-in to Learning Management System"
    )
    assert "Learning Management System" in notification.message
    assert notification.read_at is None

    db.commit()

    saved = db.query(SecurityNotification).filter_by(
        authentication_event_id=event.id
    ).one()

    assert saved.id == notification.id

    db.delete(saved)
    db.delete(event)
    db.delete(student)
    db.commit()


def test_notification_is_not_duplicated_for_same_event(db):
    student = _create_student(db)

    event = AuthenticationEvent(
        user_id=student.id,
        client_id="notification-test-client",
        application_name="Results Portal",
        event_type="authorization",
        outcome="success",
        authentication_method="fresh_password_login",
    )

    db.add(event)
    db.flush()

    first = create_authentication_notification(db, event)
    second = create_authentication_notification(db, event)

    assert first.id == second.id

    count = db.query(SecurityNotification).filter_by(
        authentication_event_id=event.id
    ).count()

    assert count == 1

    db.delete(first)
    db.delete(event)
    db.delete(student)
    db.commit()


def test_failed_authentication_does_not_create_notification(db):
    student = _create_student(db)

    event = AuthenticationEvent(
        user_id=student.id,
        client_id="notification-test-client",
        application_name="Library",
        event_type="authorization",
        outcome="failure",
        authentication_method="password",
        failure_reason="invalid_credentials",
    )

    db.add(event)
    db.flush()

    notification = create_authentication_notification(db, event)

    assert notification is None

    count = db.query(SecurityNotification).filter_by(
        authentication_event_id=event.id
    ).count()

    assert count == 0

    db.delete(event)
    db.delete(student)
    db.commit()
