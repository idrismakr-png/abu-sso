
from app.models import IdPSession, User
from app.models.idp_login_marker import IdPLoginMarker


def test_successful_login_creates_secure_idp_session(client, db):
    registration = client.post(
        "/auth/register",
        json={
            "email": "oidc-session@abu.edu.ng",
            "password": "secret123",
            "full_name": "OIDC Session Tester",
            "role": "student",
            "matric_no": "OIDC/SESSION/001",
        },
    )

    assert registration.status_code == 201

    response = client.post(
        "/auth/login",
        json={
            "matric_no": "OIDC/SESSION/001",
            "password": "secret123",
        },
    )

    assert response.status_code == 200
    assert "access_token" in response.json()

    cookie = response.cookies.get("abu_idp_session")

    assert cookie
    assert len(cookie) > 20

    set_cookie = response.headers.get("set-cookie", "").lower()

    assert "httponly" in set_cookie
    assert "samesite=lax" in set_cookie

    user = db.query(User).filter_by(
        matric_no="OIDC/SESSION/001"
    ).one()

    session_record = db.query(IdPSession).filter_by(
        user_id=user.id
    ).one()

    assert session_record.session_token_hash != cookie
    assert session_record.revoked_at is None
    assert session_record.expires_at is not None

    # Confirm that the new password login created one marker.
    marker = db.query(IdPLoginMarker).filter_by(
        session_id=session_record.id
    ).one()

    assert marker.session_id == session_record.id
    assert marker.consumed_at is None
