
import secrets

import bcrypt
from sqlalchemy.orm import Session

from app.models import OIDCClient


DEFAULT_SCOPES = ["openid", "profile", "email"]


def create_application(
    db: Session,
    *,
    name: str,
    client_type: str,
    redirect_uris: list[str],
):
    """
    Register an application with the central ABU identity provider.

    Returns the registered client and its one-time secret, if confidential.
    Raw client secrets are never stored in the database.
    """

    if client_type not in ("public", "confidential"):
        raise ValueError("Client type must be public or confidential.")

    if not redirect_uris:
        raise ValueError("At least one redirect URI is required.")

    client_id = secrets.token_urlsafe(24)
    raw_client_secret = None
    client_secret_hash = None

    if client_type == "confidential":
        raw_client_secret = secrets.token_urlsafe(48)
        client_secret_hash = bcrypt.hashpw(
            raw_client_secret.encode("utf-8"),
            bcrypt.gensalt(),
        ).decode("utf-8")

    client = OIDCClient(
        client_id=client_id,
        name=name,
        client_secret_hash=client_secret_hash,
        client_type=client_type,
        redirect_uris=redirect_uris,
        allowed_scopes=DEFAULT_SCOPES.copy(),
        grant_types=["authorization_code"],
        response_types=["code"],
        token_endpoint_auth_method=(
            "client_secret_basic"
            if client_type == "confidential"
            else "none"
        ),
        require_pkce=True,
        is_active=True,
    )

    try:
        db.add(client)
        db.commit()
        db.refresh(client)
    except Exception:
        db.rollback()
        raise

    return client, raw_client_secret
