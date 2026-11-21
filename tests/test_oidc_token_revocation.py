
import hashlib
import uuid
from datetime import timedelta

import pytest

from app.models import OIDCClient, OIDCAccessToken, User
from app.services.oidc_token_service import (
    revoke_access_token,
    utcnow,
)


@pytest.fixture
def revocation_records(db):
    suffix = uuid.uuid4().hex

    user = User(
        id=str(uuid.uuid4()),
        email=f"{suffix}@abu.edu.ng",
        password_hash="test-password-hash",
        full_name="Revocation Test User",
    )

    client = OIDCClient(
        client_id=f"revocation-client-{suffix}",
        name="Revocation Test Application",
        is_active=True,
    )

    other_client = OIDCClient(
        client_id=f"other-client-{suffix}",
        name="Other Test Application",
        is_active=True,
    )

    raw_token = f"revocation-token-{suffix}"

    token_record = OIDCAccessToken(
        token_hash=hashlib.sha256(
            raw_token.encode("utf-8")
        ).hexdigest(),
        client_id=client.client_id,
        user_id=user.id,
        scopes=["openid", "profile"],
        expires_at=utcnow() + timedelta(minutes=15),
    )

    db.add_all([
        user,
        client,
        other_client,
        token_record,
    ])
    db.commit()

    yield {
        "user": user,
        "client": client,
        "other_client": other_client,
        "token": token_record,
        "raw_token": raw_token,
    }

    db.query(OIDCAccessToken).filter_by(
        id=token_record.id
    ).delete(synchronize_session=False)

    db.query(OIDCClient).filter(
        OIDCClient.client_id.in_([
            client.client_id,
            other_client.client_id,
        ])
    ).delete(synchronize_session=False)

    db.query(User).filter_by(
        id=user.id
    ).delete(synchronize_session=False)

    db.commit()


def test_revokes_valid_access_token(db, revocation_records):
    records = revocation_records

    result = revoke_access_token(
        db=db,
        raw_token=records["raw_token"],
        client_id=records["client"].client_id,
    )

    db.refresh(records["token"])

    assert result is True
    assert records["token"].revoked_at is not None


def test_token_cannot_be_revoked_by_another_client(
    db,
    revocation_records,
):
    records = revocation_records

    result = revoke_access_token(
        db=db,
        raw_token=records["raw_token"],
        client_id=records["other_client"].client_id,
    )

    db.refresh(records["token"])

    assert result is False
    assert records["token"].revoked_at is None


def test_unknown_token_returns_false(db, revocation_records):
    records = revocation_records

    result = revoke_access_token(
        db=db,
        raw_token="unknown-access-token",
        client_id=records["client"].client_id,
    )

    assert result is False


def test_already_revoked_token_returns_false(
    db,
    revocation_records,
):
    records = revocation_records
    records["token"].revoked_at = utcnow()
    db.commit()

    result = revoke_access_token(
        db=db,
        raw_token=records["raw_token"],
        client_id=records["client"].client_id,
    )

    assert result is False


@pytest.mark.parametrize(
    "raw_token, client_id",
    [
        ("", "valid-client"),
        (None, "valid-client"),
        ("valid-token", ""),
        ("valid-token", None),
    ],
)
def test_invalid_revocation_inputs_return_false(
    db,
    raw_token,
    client_id,
):
    result = revoke_access_token(
        db=db,
        raw_token=raw_token,
        client_id=client_id,
    )

    assert result is False
