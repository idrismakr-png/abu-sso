
from app.models import IdPSession, User
from app.services.idp_session_service import get_active_idp_session


def test_logout_revokes_session_and_clears_cookie(client, db):
    # Register a test account.
    registration = client.post(
        "/auth/register",
        json={
            "email": "oidc-logout@abu.edu.ng",
            "password": "secret123",
            "full_name": "OIDC Logout Tester",
            "role": "student",
            "matric_no": "OIDC/LOGOUT/001",
        },
    )

    assert registration.status_code == 201

    # Log in and establish a central IdP session.
    login_response = client.post(
        "/auth/login",
        json={
            "matric_no": "OIDC/LOGOUT/001",
            "password": "secret123",
        },
    )

    assert login_response.status_code == 200

    session_token = login_response.cookies.get("abu_idp_session")
    assert session_token

    # Confirm that the session is initially active.
    user = db.query(User).filter_by(
        matric_no="OIDC/LOGOUT/001"
    ).one()

    active_session = get_active_idp_session(db, session_token)

    assert active_session is not None
    assert active_session[1].id == user.id

    # Log out.
    logout_response = client.post("/auth/logout")

    assert logout_response.status_code == 200
    assert "revoked" in logout_response.json()["message"].lower()

    # The browser cookie must be cleared.
    set_cookie = logout_response.headers.get("set-cookie", "").lower()

    assert "abu_idp_session" in set_cookie
    assert "max-age=0" in set_cookie

    # The database session must be revoked.
    session_record = db.query(IdPSession).filter_by(
        user_id=user.id
    ).one()

    assert session_record.revoked_at is not None
    assert get_active_idp_session(db, session_token) is None
