
import hashlib
import uuid
from datetime import timedelta

import pytest

from app.models import OIDCClient, OIDCAccessToken, User
from app.services.oidc_token_service import utcnow


@pytest.fixture
def userinfo_access_token(db):
    suffix = uuid.uuid4().hex

    user = User(
        id=str(uuid.uuid4()),
        email=f"{suffix}@abu.edu.ng",
        password_hash="test-password-hash",
        full_name="ABU UserInfo Endpoint Tester",
    )

    oidc_client = OIDCClient(
        client_id=f"userinfo-endpoint-{suffix}",
        name="UserInfo Endpoint Test Application",
        is_active=True,
    )

    raw_token = f"endpoint-access-token-{suffix}"

    token_record = OIDCAccessToken(
        token_hash=hashlib.sha256(
            raw_token.encode("utf-8")
        ).hexdigest(),
        client_id=oidc_client.client_id,
        user_id=user.id,
        scopes=["openid", "profile", "email"],
        expires_at=utcnow() + timedelta(minutes=15),
    )

    db.add_all([user, oidc_client, token_record])
    db.commit()

    yield {
        "user": user,
        "client": oidc_client,
        "token": token_record,
        "raw_token": raw_token,
    }

    db.query(OIDCAccessToken).filter_by(
        id=token_record.id
    ).delete(synchronize_session=False)

    db.query(OIDCClient).filter_by(
        client_id=oidc_client.client_id
    ).delete(synchronize_session=False)

    db.query(User).filter_by(
        id=user.id
    ).delete(synchronize_session=False)

    db.commit()


def test_userinfo_returns_claims_for_valid_bearer_token(
    client,
    userinfo_access_token,
):
    response = client.get(
        "/userinfo",
        headers={
            "Authorization": (
                f"Bearer {userinfo_access_token['raw_token']}"
            )
        },
    )

    assert response.status_code == 200

    assert response.json() == {
        "sub": userinfo_access_token["user"].id,
        "name": "ABU UserInfo Endpoint Tester",
        "email": userinfo_access_token["user"].email,
    }


def test_userinfo_rejects_missing_authorization_header(client):
    response = client.get("/userinfo")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_userinfo_rejects_malformed_authorization_header(client):
    response = client.get(
        "/userinfo",
        headers={
            "Authorization": "Basic invalid-credentials"
        },
    )

    assert response.status_code == 401


def test_userinfo_rejects_invalid_bearer_token(client):
    response = client.get(
        "/userinfo",
        headers={
            "Authorization": "Bearer invalid-access-token"
        },
    )

    assert response.status_code == 401


def test_userinfo_rejects_expired_access_token(
    client,
    db,
    userinfo_access_token,
):
    userinfo_access_token["token"].expires_at = (
        utcnow() - timedelta(minutes=1)
    )
    db.commit()

    response = client.get(
        "/userinfo",
        headers={
            "Authorization": (
                f"Bearer {userinfo_access_token['raw_token']}"
            )
        },
    )

    assert response.status_code == 401


def test_userinfo_rejects_revoked_access_token(
    client,
    db,
    userinfo_access_token,
):
    userinfo_access_token["token"].revoked_at = utcnow()
    db.commit()

    response = client.get(
        "/userinfo",
        headers={
            "Authorization": (
                f"Bearer {userinfo_access_token['raw_token']}"
            )
        },
    )

    assert response.status_code == 401


def test_discovery_document_advertises_userinfo_endpoint(client):
    response = client.get("/.well-known/openid-configuration")

    assert response.status_code == 200
    assert response.json()["userinfo_endpoint"].endswith("/userinfo")
