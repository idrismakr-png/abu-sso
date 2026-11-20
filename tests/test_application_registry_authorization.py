
import base64
import hashlib
import uuid

from app.models import OIDCClient, User
from app.services.idp_session_service import create_idp_session


def test_deactivated_application_cannot_authorize(client, db):
    suffix = uuid.uuid4().hex

    registration = client.post(
        "/auth/register",
        json={
            "email": f"{suffix}@abu.edu.ng",
            "password": "secret123",
            "full_name": "Inactive Client Tester",
            "role": "student",
            "matric_no": f"INACTIVE/{suffix[:8]}",
        },
    )

    assert registration.status_code == 201

    user = db.query(User).filter_by(
        email=f"{suffix}@abu.edu.ng"
    ).one()

    client_id = f"inactive-client-{suffix}"
    redirect_uri = "http://localhost:8001/callback"

    application = OIDCClient(
        client_id=client_id,
        name="Deactivated Test Application",
        client_type="public",
        redirect_uris=[redirect_uri],
        allowed_scopes=["openid", "profile", "email"],
        grant_types=["authorization_code"],
        response_types=["code"],
        token_endpoint_auth_method="none",
        require_pkce=True,
        is_active=False,
    )

    db.add(application)
    db.commit()

    session_record, session_token = create_idp_session(
        db=db,
        user=user,
        ip_address="127.0.0.1",
        user_agent="Inactive Client Test",
    )

    verifier = "abcdefghijklmnopqrstuvwxyz0123456789ABCDEFG"
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode("ascii")).digest()
    ).rstrip(b"=").decode("ascii")

    client.cookies.set("abu_idp_session", session_token)

    try:
        response = client.get(
            "/authorize",
            params={
                "client_id": client_id,
                "response_type": "code",
                "redirect_uri": redirect_uri,
                "scope": "openid profile email",
                "state": "inactive-client-state",
                "nonce": "inactive-client-nonce",
                "code_challenge": challenge,
                "code_challenge_method": "S256",
            },
            follow_redirects=False,
        )

        assert response.status_code == 400
        assert "code" not in response.text

    finally:
        from app.models import IdPSession

        db.query(IdPSession).filter_by(
            id=session_record.id
        ).delete(synchronize_session=False)

        db.query(OIDCClient).filter_by(
            client_id=client_id
        ).delete(synchronize_session=False)

        db.query(User).filter_by(
            id=user.id
        ).delete(synchronize_session=False)

        db.commit()
