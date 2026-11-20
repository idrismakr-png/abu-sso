
from app.models import AuthenticationEvent, User


def test_password_login_success_and_failures_are_audited(client, db):
    test_user_agent = "abu-sso-auth-audit-test"

    registration = client.post(
        "/auth/register",
        json={
            "email": "auth-audit@abu.edu.ng",
            "password": "secret123",
            "full_name": "Authentication Audit Tester",
            "role": "student",
            "matric_no": "AUDIT/TEST/001",
        },
    )

    assert registration.status_code == 201

    user = db.query(User).filter_by(
        matric_no="AUDIT/TEST/001"
    ).one()

    # 1. A successful password login must create a success event.
    successful_login = client.post(
        "/auth/login",
        json={
            "matric_no": "AUDIT/TEST/001",
            "password": "secret123",
        },
        headers={"user-agent": test_user_agent},
    )

    assert successful_login.status_code == 200

    success_event = db.query(AuthenticationEvent).filter_by(
        user_id=user.id,
        event_type="login",
        outcome="success",
        application_name="ABU-SSO Portal",
        authentication_method="password",
        user_agent=test_user_agent,
    ).one()

    assert success_event.failure_reason is None

    # 2. A failed login for a known account must create a failure event.
    failed_known_user = client.post(
        "/auth/login",
        json={
            "matric_no": "AUDIT/TEST/001",
            "password": "incorrect-password",
        },
        headers={"user-agent": test_user_agent},
    )

    assert failed_known_user.status_code == 401

    known_user_failure = db.query(AuthenticationEvent).filter_by(
        user_id=user.id,
        event_type="login",
        outcome="failure",
        application_name="ABU-SSO Portal",
        authentication_method="password",
        failure_reason="invalid_credentials",
        user_agent=test_user_agent,
    ).one()

    # 3. A failed login for an unknown account must also be recorded,
    # without revealing whether the account exists.
    failed_unknown_user = client.post(
        "/auth/login",
        json={
            "matric_no": "AUDIT/UNKNOWN/999",
            "password": "incorrect-password",
        },
        headers={"user-agent": test_user_agent},
    )

    assert failed_unknown_user.status_code == 401
    assert failed_unknown_user.json() == failed_known_user.json()

    unknown_user_failure = db.query(AuthenticationEvent).filter_by(
        user_id=None,
        event_type="login",
        outcome="failure",
        application_name="ABU-SSO Portal",
        authentication_method="password",
        failure_reason="invalid_credentials",
        user_agent=test_user_agent,
    ).one()

    assert success_event.id
    assert known_user_failure.id
    assert unknown_user_failure.id
