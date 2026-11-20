
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    JSON,
    String,
    Text,
)

from app.database import Base


def utcnow() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc)


class OIDCClient(Base):
    """Registry of applications authorised to use ABU-SSO."""

    __tablename__ = "oidc_clients"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    client_id = Column(String(128), unique=True, nullable=False, index=True)
    name = Column(String(150), nullable=False)

    # Confidential clients receive a secret, stored only as a hash.
    # Public clients use PKCE instead of a client secret.
    client_secret_hash = Column(String(255), nullable=True)
    client_type = Column(String(20), nullable=False, default="public")

    redirect_uris = Column(JSON, nullable=False, default=list)
    allowed_scopes = Column(
        JSON,
        nullable=False,
        default=lambda: ["openid", "profile", "email"],
    )
    grant_types = Column(
        JSON,
        nullable=False,
        default=lambda: ["authorization_code"],
    )
    response_types = Column(
        JSON,
        nullable=False,
        default=lambda: ["code"],
    )

    token_endpoint_auth_method = Column(
        String(50),
        nullable=False,
        default="none",
    )

    require_pkce = Column(Boolean, nullable=False, default=True)
    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
    )

    def __repr__(self) -> str:
        return f"<OIDCClient name={self.name} client_id={self.client_id}>"


class OIDCAuthorizationCode(Base):
    """Short-lived, single-use OIDC authorization codes."""

    __tablename__ = "oidc_authorization_codes"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    # Store a hash of the authorization code, never the raw code.
    code_hash = Column(String(128), unique=True, nullable=False, index=True)

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

    redirect_uri = Column(Text, nullable=False)
    scopes = Column(JSON, nullable=False, default=list)
    nonce = Column(String(255), nullable=True)

    # PKCE protection.
    code_challenge = Column(String(128), nullable=False)
    code_challenge_method = Column(
        String(10),
        nullable=False,
        default="S256",
    )

    expires_at = Column(DateTime(timezone=True), nullable=False)
    consumed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
    )

    def __repr__(self) -> str:
        return f"<OIDCAuthorizationCode client_id={self.client_id}>"


class IdPSession(Base):
    """Central browser session maintained by the ABU identity provider."""

    __tablename__ = "idp_sessions"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    user_id = Column(
        String(36),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    # Only the hash of the opaque browser session token is stored.
    session_token_hash = Column(
        String(128),
        unique=True,
        nullable=False,
        index=True,
    )

    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
    )
    last_seen_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
    )
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<IdPSession user_id={self.user_id}>"


class AuthenticationEvent(Base):
    """Audit record of authentication activity across ABU applications."""

    __tablename__ = "authentication_events"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    client_id = Column(
        String(128),
        ForeignKey("oidc_clients.client_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Preserve the application name even if its registry entry changes.
    application_name = Column(String(150), nullable=True)

    event_type = Column(
        String(50),
        nullable=False,
        default="authorization",
    )

    outcome = Column(String(20), nullable=False)

    # Examples: password, existing_sso_session.
    authentication_method = Column(String(50), nullable=True)

    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    failure_reason = Column(String(255), nullable=True)

    occurred_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        index=True,
    )

    __table_args__ = (
        Index(
            "ix_auth_events_user_time",
            "user_id",
            "occurred_at",
        ),
        Index(
            "ix_auth_events_client_time",
            "client_id",
            "occurred_at",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<AuthenticationEvent "
            f"application={self.application_name} outcome={self.outcome}>"
        )
