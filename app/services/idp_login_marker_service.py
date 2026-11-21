
from datetime import datetime, timezone

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.models.idp_login_marker import IdPLoginMarker


def consume_fresh_login_marker(db: Session, session_id: str) -> bool:
    """
    Consume a fresh-login marker once.

    Returns True only for the first successful consumption.
    Returns False when no unconsumed marker exists.
    """
    if not session_id:
        return False

    try:
        result = db.execute(
            update(IdPLoginMarker)
            .where(
                IdPLoginMarker.session_id == session_id,
                IdPLoginMarker.consumed_at.is_(None),
            )
            .values(consumed_at=datetime.now(timezone.utc))
        )

        consumed = result.rowcount == 1
        db.commit()

        return consumed

    except Exception:
        db.rollback()
        raise
