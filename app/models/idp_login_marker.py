
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, String

from app.database import Base


def utcnow():
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc)


class IdPLoginMarker(Base):
    """Tracks whether a new IdP login has been used for app authorization."""

    __tablename__ = "idp_login_markers"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    session_id = Column(
        String(36),
        ForeignKey("idp_sessions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
    )

    consumed_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )
