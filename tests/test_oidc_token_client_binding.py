
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


def test_authorization_code_cannot_be_redeemed_by_another_client(
    client,
    db,
):
    suffix = uuid.uuid4().hex
    email = f"{suffix}@abu.edu.ng"
    redirect_uri = "http://localhost:8001/callback"

    registration = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "secret123",
            "full_name": "OIDC Client Binding Tester",
            "role": "student",
            "matric_no": f"OIDC/BIND/{suffix[:8]}",
        },
    )

    assert registration.status_code == 201

    user = db.query(User).filter_by(email=email).one()

    first_client_id = f"student-portal-{suffix}"
    second_client_id = f"lms-portal-{suffix}"

    first_client = OIDCClient(
        client_id=first_client_id,
        name="Student Portal",
        client_type="public",
        redirect_uris=[redirect_uri],
        allowed_scopes=["openid", "profile", "email"],
        grant_types=["authorization_code"],
        response_types=["code"],
        token_endpoint_auth_method="none",
        require_pkce=True,
        is_active=True,
    )

    second_client = OIDCClient(
        client_id=second_client_id,
        name="Learning Management System",
        client_type="public",
        redirect_uris=[redirect_uri],
        allowed_scopes=["openid", "profile", "email"],
        grant_types=["authorization_code"],
        response_types=["code"],
        token_endpoint_auth_method="none",
        require_pkce=True,
        is_active=True,
    )

    db.add_all([first_client, second_client])
    db.commit()

    session_record, session_token = create_idp_session(
        db=db,
        user=user,
        ip_address="127.0.0.1",
        user_agent="OIDC Client Binding Test",
    )

    verifier = "abcdefghijklmnopqrstuvwxyz0123456789ABCDEFG"

    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode("ascii")).digest()
    ).rstrip(b"=").decode("ascii")

    try:
        client.cookies.set("abu_idp_session", session_token)

        authorization_response = client.get(
            "/authorize",
            params={
                "client_id": first_client_id,
                "response_type": "code",
                "redirect_uri": redirect_uri,
                "scope": "openid profile email",
                "state": "client-binding-state",
                "nonce": "client-binding-nonce",
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
                "client_id": second_client_id,
                "code": authorization_code,
                "redirect_uri": redirect_uri,
                "code_verifier": verifier,
            },
        )

        assert token_response.status_code == 400
        assert token_response.json()["error"] == "invalid_grant"

    finally:
        db.query(OIDCAuthorizationCode).filter(
            OIDCAuthorizationCode.client_id.in_(
                [first_client_id, second_client_id]
            )
        ).delete(synchronize_session=False)

        db.query(OIDCClient).filter(
            OIDCClient.client_id.in_(
                [first_client_id, second_client_id]
            )
        ).delete(synchronize_session=False)

        db.query(type(session_record)).filter_by(
            id=session_record.id
        ).delete(synchronize_session=False)

        db.commit()
