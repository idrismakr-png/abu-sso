
import base64
import hashlib
import uuid
from urllib.parse import parse_qs, urlsplit

from app.models import (
    AuthenticationEvent,
    OIDCClient,
    OIDCAuthorizationCode,
    User,
)
from app.services.idp_session_service import create_idp_session


def test_authenticated_user_receives_authorization_code(client, db):
    suffix = uuid.uuid4().hex

    registration = client.post(
        "/auth/register",
        json={
            "email": f"{suffix}@abu.edu.ng",
            "password": "secret123",
            "full_name": "OIDC Authorization Tester",
            "role": "student",
            "matric_no": f"OIDC/AUTH/{suffix[:8]}",
        },
    )

    assert registration.status_code == 201

    user = db.query(User).filter_by(
        email=f"{suffix}@abu.edu.ng"
    ).one()

    client_id = f"test-client-{suffix}"
    redirect_uri = "http://localhost:8001/callback"

    oidc_client = OIDCClient(
        client_id=client_id,
        name="Authorization Test Application",
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

    session_record, session_token = create_idp_session(
        db=db,
        user=user,
        ip_address="127.0.0.1",
        user_agent="OIDC Authorization Test",
    )

    verifier = "abcdefghijklmnopqrstuvwxyz0123456789ABCDEFG"

    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode("ascii")).digest()
    ).rstrip(b"=").decode("ascii")

    client.cookies.set(
        "abu_idp_session",
        session_token,
    )

    try:
        response = client.get(
            "/authorize",
            params={
                "client_id": client_id,
                "response_type": "code",
                "redirect_uri": redirect_uri,
                "scope": "openid profile email",
                "state": "authorization-state-123",
                "nonce": "authorization-nonce-123",
                "code_challenge": challenge,
                "code_challenge_method": "S256",
            },
            follow_redirects=False,
        )

        assert response.status_code == 302

        location = response.headers["location"]
        callback = urlsplit(location)
        callback_parameters = parse_qs(callback.query)

        assert callback.scheme == "http"
        assert callback.netloc == "localhost:8001"
        assert callback.path == "/callback"
        assert callback_parameters["state"] == [
            "authorization-state-123"
        ]

        assert "code" in callback_parameters

        # The authorization code must be stored as a hash.
        saved_code = db.query(OIDCAuthorizationCode).filter_by(
            client_id=client_id
        ).one()

        raw_code = callback_parameters["code"][0]

        assert saved_code.code_hash != raw_code
        assert saved_code.user_id == user.id
        assert saved_code.nonce == "authorization-nonce-123"
        assert saved_code.code_challenge == challenge

        # Successful authorization must generate an audit event.
        event = db.query(AuthenticationEvent).filter_by(
            client_id=client_id,
            outcome="success",
        ).one()

        assert event.user_id == user.id
        assert event.authentication_method == "existing_sso_session"

    finally:
        db.query(AuthenticationEvent).filter_by(
            client_id=client_id
        ).delete(synchronize_session=False)

        db.query(OIDCAuthorizationCode).filter_by(
            client_id=client_id
        ).delete(synchronize_session=False)

        db.query(OIDCClient).filter_by(
            client_id=client_id
        ).delete(synchronize_session=False)

        db.query(type(session_record)).filter_by(
            id=session_record.id
        ).delete(synchronize_session=False)

        db.commit()
