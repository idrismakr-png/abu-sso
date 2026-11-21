import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    JSON,
    String,
)

from app.database import Base


def utcnow() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc)


class OIDCAccessToken(Base):
    """Store hashed OIDC access tokens issued by ABU-SSO."""

    __tablename__ = "oidc_access_tokens"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    # Only the SHA-256 hash is stored, never the raw bearer token.
    token_hash = Column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
    )

    client_id = Column(
        String(128),
        ForeignKey("oidc_clients.client_id"),
        nullable=False,
        index=True,
    )

    user_id = Column(
        String(36),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    scopes = Column(
        JSON,
        nullable=False,
        default=list,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
    )

    expires_at = Column(
        DateTime(timezone=True),
        nullable=False,
    )

    revoked_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    __table_args__ = (
        Index(
            "ix_oidc_access_tokens_user_expiry",
            "user_id",
            "expires_at",
        ),
        Index(
            "ix_oidc_access_tokens_client_expiry",
            "client_id",
            "expires_at",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<OIDCAccessToken client_id={self.client_id} "
            f"user_id={self.user_id}>"
        )