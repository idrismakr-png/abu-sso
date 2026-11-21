
import base64
import hashlib
import uuid
from urllib.parse import parse_qs, urlsplit

from app.models import (
    AuthenticationEvent,
    IdPSession,
    OIDCClient,
    OIDCAuthorizationCode,
    User,
)
from app.models.idp_login_marker import IdPLoginMarker


def test_fresh_login_is_recorded_only_for_first_authorization(client, db):
    suffix = uuid.uuid4().hex
    matric_no = f"OIDC/FRESH/{suffix[:8]}".upper()

    registration = client.post(
        "/auth/register",
        json={
            "email": f"{suffix}@abu.edu.ng",
            "password": "secret123",
            "full_name": "Fresh Login Tester",
            "role": "student",
            "matric_no": matric_no,
        },
    )
    assert registration.status_code == 201

    login = client.post(
        "/auth/login",
        json={
            "matric_no": matric_no,
            "password": "secret123",
        },
    )
    assert login.status_code == 200

    user = db.query(User).filter_by(matric_no=matric_no).one()
    session_record = db.query(IdPSession).filter_by(
        user_id=user.id
    ).one()

    client_id = f"fresh-login-client-{suffix}"
    redirect_uri = "http://localhost:8001/fresh-callback"

    oidc_client = OIDCClient(
        client_id=client_id,
        name="Fresh Login Test Application",
        client_type="public",
        redirect_uris=[redirect_uri],
        allowed_scopes=["openid", "profile", "email"],
        grant_types=["authorization_code"],
        response_types=["code"],
        token_endpoint_auth_method="none",
        require_pkce=True,
        is_active=True,
    )
    db.add(oidc_client)
    db.commit()

    verifier = "abcdefghijklmnopqrstuvwxyz0123456789ABCDEFG"
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode("ascii")).digest()
    ).rstrip(b"=").decode("ascii")

    marker = db.query(IdPLoginMarker).filter_by(
        session_id=session_record.id
    ).one()
    assert marker.consumed_at is None

    client.cookies.set(
        "abu_idp_session",
        login.cookies.get("abu_idp_session"),
    )

    def authorize(state_value):
        return client.get(
            "/authorize",
            params={
                "client_id": client_id,
                "response_type": "code",
                "redirect_uri": redirect_uri,
                "scope": "openid profile email",
                "state": state_value,
                "nonce": f"nonce-{state_value}",
                "code_challenge": challenge,
                "code_challenge_method": "S256",
            },
            follow_redirects=False,
        )

    try:
        first_response = authorize("fresh-state")
        assert first_response.status_code == 302

        first_parameters = parse_qs(
            urlsplit(first_response.headers["location"]).query
        )
        assert "code" in first_parameters

        db.refresh(marker)
        assert marker.consumed_at is not None

        first_event = db.query(AuthenticationEvent).filter_by(
            client_id=client_id
        ).one()

        assert first_event.outcome == "success"
        assert first_event.authentication_method == "fresh_password_login"

        second_response = authorize("existing-state")
        assert second_response.status_code == 302

        second_parameters = parse_qs(
            urlsplit(second_response.headers["location"]).query
        )
        assert "code" in second_parameters

        events = db.query(AuthenticationEvent).filter_by(
            client_id=client_id
        ).all()

        assert len(events) == 2
        assert sum(
            event.authentication_method == "fresh_password_login"
            for event in events
        ) == 1
        assert sum(
            event.authentication_method == "existing_sso_session"
            for event in events
        ) == 1

    finally:
        db.query(AuthenticationEvent).filter_by(
            client_id=client_id
        ).delete(synchronize_session=False)

        db.query(OIDCAuthorizationCode).filter_by(
            client_id=client_id
        ).delete(synchronize_session=False)

        db.query(IdPLoginMarker).filter_by(
            session_id=session_record.id
        ).delete(synchronize_session=False)

        db.delete(session_record)
        db.delete(oidc_client)
        db.delete(user)
        db.commit()
