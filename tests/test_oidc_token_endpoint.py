import base64
import hashlib
import uuid
from urllib.parse import parse_qs, urlsplit

from app.models import (
    OIDCClient,
    OIDCAuthorizationCode,
    User,
)
from app.services.idp_session_service import create_idp_session


def test_authorization_code_can_be_exchanged_for_tokens(client, db):
    suffix = uuid.uuid4().hex
    email = f"{suffix}@abu.edu.ng"
    client_id = f"token-test-{suffix}"
    redirect_uri = "http://localhost:8001/callback"

    registration = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "secret123",
            "full_name": "OIDC Token Tester",
            "role": "student",
            "matric_no": f"OIDC/TOKEN/{suffix[:8]}",
        },
    )

    assert registration.status_code == 201

    user = db.query(User).filter_by(email=email).one()

    oidc_client = OIDCClient(
        client_id=client_id,
        name="Token Endpoint Test Application",
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
        user_agent="OIDC Token Endpoint Test",
    )

    verifier = "abcdefghijklmnopqrstuvwxyz0123456789ABCDEFG"

    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode("ascii")).digest()
    ).rstrip(b"=").decode("ascii")

    client.cookies.set("abu_idp_session", session_token)

    try:
        authorization_response = client.get(
            "/authorize",
            params={
                "client_id": client_id,
                "response_type": "code",
                "redirect_uri": redirect_uri,
                "scope": "openid profile email",
                "state": "token-test-state",
                "nonce": "token-test-nonce",
                "code_challenge": challenge,
                "code_challenge_method": "S256",
            },
            follow_redirects=False,
        )

        assert authorization_response.status_code == 302

        callback_parameters = parse_qs(
            urlsplit(
                authorization_response.headers["location"]
            ).query
        )

        authorization_code = callback_parameters["code"][0]

        token_response = client.post(
            "/token",
            data={
                "grant_type": "authorization_code",
                "client_id": client_id,
                "code": authorization_code,
                "redirect_uri": redirect_uri,
                "code_verifier": verifier,
            },
        )

        assert token_response.status_code == 200

        tokens = token_response.json()

        assert tokens["token_type"].lower() == "bearer"
        assert tokens["access_token"]
        assert tokens["id_token"]
        assert tokens["expires_in"] > 0
        assert "openid" in tokens["scope"]

        saved_code = db.query(OIDCAuthorizationCode).filter_by(
            client_id=client_id
        ).one()

        assert saved_code.consumed_at is not None

    finally:
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