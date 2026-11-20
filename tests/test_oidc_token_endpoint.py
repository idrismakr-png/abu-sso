
from datetime import timedelta
import base64
import hashlib
import uuid
from urllib.parse import parse_qs, urlsplit

from app.models import (
    OIDCClient,
    OIDCAuthorizationCode,
    User,
)
from app.models.oidc import utcnow
from app.services.idp_session_service import create_idp_session


def create_authorization_code(client, db):
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

    return {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "authorization_code": authorization_code,
        "verifier": verifier,
        "session_record": session_record,
    }


def cleanup_authorization_test(db, client_id, session_record):
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


def exchange_authorization_code(client, test_data, verifier=None):
    return client.post(
        "/token",
        data={
            "grant_type": "authorization_code",
            "client_id": test_data["client_id"],
            "code": test_data["authorization_code"],
            "redirect_uri": test_data["redirect_uri"],
            "code_verifier": (
                verifier
                if verifier is not None
                else test_data["verifier"]
            ),
        },
    )


def test_authorization_code_can_be_exchanged_for_tokens(client, db):
    test_data = create_authorization_code(client, db)

    try:
        token_response = exchange_authorization_code(
            client,
            test_data,
        )

        assert token_response.status_code == 200

        tokens = token_response.json()

        assert tokens["token_type"].lower() == "bearer"
        assert tokens["access_token"]
        assert tokens["id_token"]
        assert tokens["expires_in"] > 0
        assert "openid" in tokens["scope"]

        saved_code = db.query(OIDCAuthorizationCode).filter_by(
            client_id=test_data["client_id"]
        ).one()

        assert saved_code.consumed_at is not None

    finally:
        cleanup_authorization_test(
            db,
            test_data["client_id"],
            test_data["session_record"],
        )


def test_authorization_code_rejects_incorrect_pkce_verifier(client, db):
    test_data = create_authorization_code(client, db)

    try:
        token_response = exchange_authorization_code(
            client,
            test_data,
            verifier="wrong-verifier-abcdefghijklmnopqrstuvwxyz-1234567890",
        )

        assert token_response.status_code == 400
        assert token_response.json()["error"] == "invalid_grant"

    finally:
        cleanup_authorization_test(
            db,
            test_data["client_id"],
            test_data["session_record"],
        )


def test_authorization_code_cannot_be_reused(client, db):
    test_data = create_authorization_code(client, db)

    try:
        first_response = exchange_authorization_code(
            client,
            test_data,
        )

        assert first_response.status_code == 200

        second_response = exchange_authorization_code(
            client,
            test_data,
        )

        assert second_response.status_code == 400
        assert second_response.json()["error"] == "invalid_grant"

    finally:
        cleanup_authorization_test(
            db,
            test_data["client_id"],
            test_data["session_record"],
        )


def test_expired_authorization_code_is_rejected(client, db):
    test_data = create_authorization_code(client, db)

    try:
        saved_code = db.query(OIDCAuthorizationCode).filter_by(
            client_id=test_data["client_id"]
        ).one()

        saved_code.expires_at = utcnow() - timedelta(minutes=1)
        db.commit()

        token_response = exchange_authorization_code(
            client,
            test_data,
        )

        assert token_response.status_code == 400
        assert token_response.json()["error"] == "invalid_grant"

    finally:
        cleanup_authorization_test(
            db,
            test_data["client_id"],
            test_data["session_record"],
        )
