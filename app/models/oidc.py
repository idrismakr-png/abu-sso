import uuid
import bcrypt

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

from authlib.oauth2.rfc6749 import ClientMixin
from authlib.oidc.core.models import (
    AuthorizationCodeMixin as OIDCAuthorizationCodeMixin,
)

from app.database import Base


def utcnow() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc)


class OIDCClient(Base, ClientMixin):
    """Registry of applications authorised to use ABU-SSO."""

    __tablename__ = "oidc_clients"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    client_id = Column(String(128), unique=True, nullable=False, index=True)
    name = Column(String(150), nullable=False)

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

    def get_client_id(self):
        return self.client_id

    def get_default_redirect_uri(self):
        if len(self.redirect_uris or []) == 1:
            return self.redirect_uris[0]
        return None

    def get_allowed_scope(self, scope):
        allowed = set(self.allowed_scopes or [])
        requested = set(scope.split()) if scope else allowed
        return " ".join(sorted(requested.intersection(allowed)))

    def check_redirect_uri(self, redirect_uri):
        return redirect_uri in (self.redirect_uris or [])

    def check_client_secret(self, client_secret):
        if not self.client_secret_hash or not client_secret:
            return False

        try:
            return bcrypt.checkpw(
                client_secret.encode("utf-8"),
                self.client_secret_hash.encode("utf-8"),
            )
        except (ValueError, TypeError):
            return False

    def check_endpoint_auth_method(self, method, endpoint):
        if endpoint == "token":
            return method == self.token_endpoint_auth_method
        return True

    def check_response_type(self, response_type):
        return response_type in (self.response_types or [])

    def check_grant_type(self, grant_type):
        return grant_type in (self.grant_types or [])

    def __repr__(self) -> str:
        return f"<OIDCClient name={self.name} client_id={self.client_id}>"


class OIDCAuthorizationCode(Base, OIDCAuthorizationCodeMixin):
    """Short-lived, single-use OIDC authorization codes."""

    __tablename__ = "oidc_authorization_codes"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

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

    def get_redirect_uri(self):
        return self.redirect_uri

    def get_scope(self):
        return " ".join(self.scopes or [])

    def get_nonce(self):
        return self.nonce

    def get_auth_time(self):
        return None

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

    application_name = Column(String(150), nullable=True)

    event_type = Column(
        String(50),
        nullable=False,
        default="authorization",
    )

    outcome = Column(String(20), nullable=False)

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