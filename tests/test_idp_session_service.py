
import uuid
from datetime import timedelta

from app.models import IdPSession, User
from app.models.oidc import utcnow
from app.services.idp_session_service import (
    create_idp_session,
    get_active_idp_session,
    revoke_idp_session,
)


def test_idp_session_lifecycle(db):
    suffix = uuid.uuid4().hex

    user = User(
        id=str(uuid.uuid4()),
        email=f"{suffix}@abu.edu.ng",
        password_hash="test-password-hash",
        full_name="OIDC Session Test",
        role="student",
    )

    db.add(user)
    db.commit()

    created_session = None
    expired_session = None

    try:
        # Create a central browser session.
        created_session, raw_token = create_idp_session(
            db=db,
            user=user,
            ip_address="127.0.0.1",
            user_agent="OIDC Session Test",
        )

        assert raw_token
        assert created_session.user_id == user.id
        assert created_session.session_token_hash != raw_token
        assert created_session.ip_address == "127.0.0.1"

        # A valid token must identify the correct user.
        result = get_active_idp_session(db, raw_token)

        assert result is not None

        saved_session, authenticated_user = result

        assert saved_session.id == created_session.id
        assert authenticated_user.id == user.id

        # Missing or invalid tokens must not authenticate anyone.
        assert get_active_idp_session(db, None) is None
        assert get_active_idp_session(db, "invalid-token") is None

        # Revocation must invalidate the session.
        assert revoke_idp_session(db, raw_token) is True
        assert get_active_idp_session(db, raw_token) is None
        assert revoke_idp_session(db, raw_token) is False

        # An expired session must also be rejected.
        expired_session, expired_token = create_idp_session(
            db=db,
            user=user,
        )

        expired_session.expires_at = utcnow() - timedelta(minutes=1)
        db.commit()

        assert get_active_idp_session(db, expired_token) is None

    finally:
        db.query(IdPSession).filter(
            IdPSession.user_id == user.id
        ).delete(synchronize_session=False)

        db.delete(user)
        db.commit()
