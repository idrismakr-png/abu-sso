
from app.models.oidc import OIDCClient
from app.services.oidc_server import (
    ABUAuthorizationServer,
    create_authorization_server,
)


def test_create_authorization_server(db):
    server = create_authorization_server(db)

    assert isinstance(server, ABUAuthorizationServer)
    assert server.db is db


def test_query_client_returns_active_registered_client(db):
    registered_client = OIDCClient(
        client_id="abu-oidc-server-test",
        name="ABU OIDC Server Test",
        redirect_uris=["http://localhost:8001/callback"],
        allowed_scopes=["openid", "profile", "email"],
        grant_types=["authorization_code"],
        response_types=["code"],
        token_endpoint_auth_method="none",
        is_active=True,
    )

    db.add(registered_client)
    db.commit()

    try:
        server = create_authorization_server(db)

        result = server.query_client("abu-oidc-server-test")

        assert result is not None
        assert result.client_id == "abu-oidc-server-test"
        assert result.is_active is True
    finally:
        db.delete(registered_client)
        db.commit()


def test_query_client_rejects_inactive_client(db):
    registered_client = OIDCClient(
        client_id="abu-oidc-inactive-test",
        name="Inactive ABU Application",
        redirect_uris=["http://localhost:8002/callback"],
        is_active=False,
    )

    db.add(registered_client)
    db.commit()

    try:
        server = create_authorization_server(db)

        result = server.query_client("abu-oidc-inactive-test")

        assert result is None
    finally:
        db.delete(registered_client)
        db.commit()
