
from datetime import timedelta
from types import SimpleNamespace
import uuid

import pytest
from authlib.oauth2.rfc6749 import InvalidGrantError

from app.models import OIDCClient, OIDCAuthorizationCode, User
from app.models.oidc import utcnow
from app.services.oidc_server import ABUAuthorizationCodeGrant


def test_authorization_code_can_only_be_consumed_once(db):
    suffix = uuid.uuid4().hex

    user = User(
        id=str(uuid.uuid4()),
        email=f"{suffix}@abu.edu.ng",
        password_hash="test-password-hash",
    )

    client = OIDCClient(
        client_id=f"single-use-{suffix}",
        name="Single Use Test Application",
        redirect_uris=["http://localhost:8001/callback"],
    )

    code = OIDCAuthorizationCode(
        code_hash=suffix,
        client_id=client.client_id,
        user_id=user.id,
        redirect_uri="http://localhost:8001/callback",
        scopes=["openid"],
        nonce="test-nonce",
        code_challenge="test-challenge",
        code_challenge_method="S256",
        expires_at=utcnow() + timedelta(minutes=5),
    )

    db.add_all([user, client, code])
    db.commit()

    try:
        grant = object.__new__(ABUAuthorizationCodeGrant)
        grant.request = SimpleNamespace(database_session=db)

        # First consumption must succeed.
        grant.delete_authorization_code(code)

        db.commit()
        db.expire_all()

        saved_code = db.query(OIDCAuthorizationCode).filter_by(
            id=code.id
        ).one()

        assert saved_code.consumed_at is not None

        # A second consumption must be rejected.
        with pytest.raises(InvalidGrantError):
            grant.delete_authorization_code(saved_code)

    finally:
        db.rollback()
        db.query(OIDCAuthorizationCode).filter_by(
            id=code.id
        ).delete()
        db.query(OIDCClient).filter_by(
            client_id=client.client_id
        ).delete()
        db.query(User).filter_by(id=user.id).delete()
        db.commit()
