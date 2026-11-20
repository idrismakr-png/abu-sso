
import hashlib
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.models import OIDCClient, OIDCAccessToken, User
from app.services.oidc_token_service import (
    generate_access_token,
    persist_access_token,
)


def test_generates_secure_opaque_access_token():
    token = generate_access_token(
        grant_type="authorization_code",
        client=None,
        user=None,
        scope="openid profile",
    )

    assert token["token_type"] == "Bearer"
    assert isinstance(token["access_token"], str)
    assert len(token["access_token"]) >= 40
    assert token["scope"] == "openid profile"
    assert token["expires_in"] > 0


def test_generates_different_tokens_for_each_request():
    first = generate_access_token("authorization_code", None)
    second = generate_access_token("authorization_code", None)

    assert first["access_token"] != second["access_token"]


def test_rejects_unsupported_grant_type():
    with pytest.raises(ValueError, match="Unsupported OIDC token grant type"):
        generate_access_token("client_credentials", None)


def test_rejects_refresh_token_generation():
    with pytest.raises(ValueError, match="Refresh tokens are not yet supported"):
        generate_access_token(
            "authorization_code",
            None,
            include_refresh_token=True,
        )


def test_rejects_invalid_token_lifetime():
    with pytest.raises(ValueError, match="positive integer"):
        generate_access_token(
            "authorization_code",
            None,
            expires_in=0,
        )


def test_persists_only_token_hash(db):
    suffix = uuid.uuid4().hex

    user = User(
        id=str(uuid.uuid4()),
        email=f"{suffix}@abu.edu.ng",
        password_hash="test-password-hash",
    )
    client = OIDCClient(
        client_id=f"test-client-{suffix}",
        name="OIDC Persistence Test",
    )

    db.add_all([user, client])
    db.commit()

    raw_token = "test-secret-access-token-" + suffix
    token = {
        "access_token": raw_token,
        "expires_in": 900,
        "scope": "openid profile",
    }

    record = persist_access_token(
        db=db,
        token=token,
        client_id=client.client_id,
        user_id=user.id,
    )

    expected_hash = hashlib.sha256(
        raw_token.encode("utf-8")
    ).hexdigest()

    assert record.token_hash == expected_hash
    assert record.token_hash != raw_token
    assert record.client_id == client.client_id
    assert record.user_id == user.id
    assert record.scopes == ["openid", "profile"]

    saved_record = db.query(OIDCAccessToken).filter_by(
        token_hash=expected_hash
    ).one()

    assert saved_record.token_hash == expected_hash
    assert raw_token not in repr(saved_record)

    db.delete(saved_record)
    db.delete(client)
    db.delete(user)
    db.commit()


def test_persisted_token_has_correct_expiry(db):
    suffix = uuid.uuid4().hex

    user = User(
        id=str(uuid.uuid4()),
        email=f"{suffix}@abu.edu.ng",
        password_hash="test-password-hash",
    )
    client = OIDCClient(
        client_id=f"expiry-client-{suffix}",
        name="OIDC Expiry Test",
    )

    db.add_all([user, client])
    db.commit()

    lifetime = 600
    token = {
        "access_token": "expiry-test-token-" + suffix,
        "expires_in": lifetime,
        "scope": "openid",
    }

    before_save = datetime.now(timezone.utc)

    record = persist_access_token(
        db=db,
        token=token,
        client_id=client.client_id,
        user_id=user.id,
    )

    after_save = datetime.now(timezone.utc)

    expiry = record.expires_at

    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)

    assert before_save + timedelta(seconds=lifetime) <= expiry
    assert expiry <= after_save + timedelta(seconds=lifetime)

    db.delete(record)
    db.delete(client)
    db.delete(user)
    db.commit()


def test_rejects_missing_raw_access_token(db):
    with pytest.raises(ValueError, match="valid access token"):
        persist_access_token(
            db=db,
            token={"expires_in": 900},
            client_id="test-client",
            user_id="test-user",
        )


def test_rejects_missing_client_or_user(db):
    token = {
        "access_token": "test-access-token",
        "expires_in": 900,
    }

    with pytest.raises(ValueError, match="Client ID and user ID"):
        persist_access_token(
            db=db,
            token=token,
            client_id=None,
            user_id="test-user",
        )
