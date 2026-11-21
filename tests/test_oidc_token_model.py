from datetime import datetime, timezone

from app.models import OIDCAccessToken


def test_oidc_access_token_has_required_fields():
    token = OIDCAccessToken(
        token_hash="a" * 64,
        client_id="abu-student-portal",
        user_id="test-user-id",
        scopes=["openid", "profile"],
        expires_at=datetime.now(timezone.utc),
    )

    assert token.token_hash == "a" * 64
    assert token.client_id == "abu-student-portal"
    assert token.user_id == "test-user-id"
    assert token.scopes == ["openid", "profile"]
    assert token.expires_at is not None


def test_oidc_access_token_supports_revocation():
    token = OIDCAccessToken(
        token_hash="b" * 64,
        client_id="abu-student-portal",
        user_id="test-user-id",
        expires_at=datetime.now(timezone.utc),
    )

    assert token.revoked_at is None

    revoked_time = datetime.now(timezone.utc)
    token.revoked_at = revoked_time

    assert token.revoked_at == revoked_time


def test_oidc_access_token_hash_is_unique_and_required():
    column = OIDCAccessToken.__table__.columns["token_hash"]

    assert column.unique is True
    assert column.nullable is False
    assert column.type.length == 64


def test_oidc_access_token_has_user_and_client_relationship_keys():
    table = OIDCAccessToken.__table__

    assert table.columns["user_id"].foreign_keys
    assert table.columns["client_id"].foreign_keys
    assert table.columns["expires_at"].nullable is False