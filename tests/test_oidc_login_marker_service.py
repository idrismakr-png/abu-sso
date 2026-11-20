
from datetime import datetime, timedelta, timezone
import uuid

from app.models import IdPSession, User
from app.models.idp_login_marker import IdPLoginMarker
from app.services.idp_login_marker_service import consume_fresh_login_marker


def test_login_marker_can_only_be_consumed_once(db):
    user = User(
        id=str(uuid.uuid4()),
        email="marker-test@abu.edu.ng",
        password_hash="test-hash",
        full_name="Marker Test User",
        role="student",
        matric_no="MARKER/TEST/001",
        is_active=True,
    )
    db.add(user)
    db.flush()

    session = IdPSession(
        id=str(uuid.uuid4()),
        user_id=user.id,
        session_token_hash="test-session-token-hash",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=12),
    )
    db.add(session)
    db.flush()

    marker = IdPLoginMarker(session_id=session.id)
    db.add(marker)
    db.commit()

    try:
        first_result = consume_fresh_login_marker(db, session.id)
        second_result = consume_fresh_login_marker(db, session.id)

        db.refresh(marker)

        assert first_result is True
        assert second_result is False
        assert marker.consumed_at is not None
    finally:
        db.delete(marker)
        db.delete(session)
        db.delete(user)
        db.commit()
