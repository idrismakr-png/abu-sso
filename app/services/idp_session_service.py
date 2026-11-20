
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.models import IdPSession, User
from app.models.oidc import utcnow


def _hash_session_token(token: str) -> str:
    """Hash a raw browser-session token before database storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _as_utc(value: datetime) -> datetime:
    """Normalise database timestamps to timezone-aware UTC."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def create_idp_session(
    db: Session,
    user: User,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> tuple[IdPSession, str]:
    """Create a central IdP session and return its record and raw token."""

    if not user.is_active:
        raise ValueError("Inactive users cannot create IdP sessions")

    raw_token = secrets.token_urlsafe(32)
    now = utcnow()

    session_record = IdPSession(
        user_id=user.id,
        session_token_hash=_hash_session_token(raw_token),
        ip_address=ip_address,
        user_agent=user_agent,
        created_at=now,
        last_seen_at=now,
        expires_at=now + timedelta(
            hours=settings.oidc_idp_session_expire_hours
        ),
    )

    try:
        db.add(session_record)
        db.commit()
        db.refresh(session_record)
    except Exception:
        db.rollback()
        raise

    return session_record, raw_token


def get_active_idp_session(
    db: Session,
    raw_token: str | None,
) -> tuple[IdPSession, User] | None:
    """Validate a browser-session token and return its session and user."""

    if not raw_token:
        return None

    token_hash = _hash_session_token(raw_token)

    session_record = (
        db.query(IdPSession)
        .filter_by(
            session_token_hash=token_hash,
            revoked_at=None,
        )
        .first()
    )

    if session_record is None:
        return None

    now = utcnow()

    if _as_utc(session_record.expires_at) <= now:
        return None

    user = db.query(User).filter_by(
        id=session_record.user_id,
        is_active=True,
    ).first()

    if user is None:
        return None

    session_record.last_seen_at = now
    db.commit()

    return session_record, user


def revoke_idp_session(
    db: Session,
    raw_token: str | None,
) -> bool:
    """Revoke a browser session without storing or exposing its raw token."""

    if not raw_token:
        return False

    token_hash = _hash_session_token(raw_token)

    session_record = (
        db.query(IdPSession)
        .filter_by(
            session_token_hash=token_hash,
            revoked_at=None,
        )
        .first()
    )

    if session_record is None:
        return False

    session_record.revoked_at = utcnow()

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return True
