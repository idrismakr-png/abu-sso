
import hashlib
import uuid
from datetime import timedelta

import pytest

from app.models import OIDCClient, OIDCAccessToken, User
from app.services.oidc_token_service import utcnow


@pytest.fixture
def revocation_endpoint_records(db):
    suffix = uuid.uuid4().hex

    user = User(
        id=str(uuid.uuid4()),
        email=f"{suffix}@abu.edu.ng",
        password_hash="test-password-hash",
        full_name="Revocation Endpoint Tester",
    )

    client = OIDCClient(
        client_id=f"revoke-endpoint-{suffix}",
        name="Revocation Endpoint Test Application",
        client_type="public",
        token_endpoint_auth_method="none",
        is_active=True,
    )

    raw_token = f"endpoint-revocation-token-{suffix}"

    token_record = OIDCAccessToken(
        token_hash=hashlib.sha256(
            raw_token.encode("utf-8")
        ).hexdigest(),
        client_id=client.client_id,
        user_id=user.id,
        scopes=["openid", "profile"],
        expires_at=utcnow() + timedelta(minutes=15),
    )

    db.add_all([user, client, token_record])
    db.commit()

    yield {
        "user": user,
        "client": client,
        "token": token_record,
        "raw_token": raw_token,
    }

    db.query(OIDCAccessToken).filter_by(
        id=token_record.id
    ).delete(synchronize_session=False)

    db.query(OIDCClient).filter_by(
        client_id=client.client_id
    ).delete(synchronize_session=False)

    db.query(User).filter_by(
        id=user.id
    ).delete(synchronize_session=False)

    db.commit()


def test_revoke_endpoint_revokes_valid_client_token(
    client,
    db,
    revocation_endpoint_records,
):
    records = revocation_endpoint_records

    response = client.post(
        "/revoke",
        data={
            "token": records["raw_token"],
            "client_id": records["client"].client_id,
        },
    )

    db.refresh(records["token"])

    assert response.status_code == 200
    assert records["token"].revoked_at is not None


def test_revoke_endpoint_returns_success_for_unknown_token(
    client,
    revocation_endpoint_records,
):
    records = revocation_endpoint_records

    response = client.post(
        "/revoke",
        data={
            "token": "unknown-token",
            "client_id": records["client"].client_id,
        },
    )

    assert response.status_code == 200


def test_revoke_endpoint_requires_client_identification(client):
    response = client.post(
        "/revoke",
        data={"token": "some-token"},
    )

    assert response.status_code == 401


def test_revoke_endpoint_rejects_unknown_client(client):
    response = client.post(
        "/revoke",
        data={
            "token": "some-token",
            "client_id": "unregistered-client",
        },
    )

    assert response.status_code == 401


def test_revoke_endpoint_does_not_revoke_another_clients_token(
    client,
    db,
    revocation_endpoint_records,
):
    records = revocation_endpoint_records

    other_client = OIDCClient(
        client_id=f"another-client-{uuid.uuid4().hex}",
        name="Another Application",
        client_type="public",
        token_endpoint_auth_method="none",
        is_active=True,
    )

    db.add(other_client)
    db.commit()

    response = client.post(
        "/revoke",
        data={
            "token": records["raw_token"],
            "client_id": other_client.client_id,
        },
    )

    db.refresh(records["token"])

    assert response.status_code == 200
    assert records["token"].revoked_at is None

    db.delete(other_client)
    db.commit()


def test_revoked_token_is_rejected_by_userinfo(
    client,
    revocation_endpoint_records,
):
    records = revocation_endpoint_records

    revoke_response = client.post(
        "/revoke",
        data={
            "token": records["raw_token"],
            "client_id": records["client"].client_id,
        },
    )

    assert revoke_response.status_code == 200

    userinfo_response = client.get(
        "/userinfo",
        headers={
            "Authorization": f"Bearer {records['raw_token']}"
        },
    )

    assert userinfo_response.status_code == 401
