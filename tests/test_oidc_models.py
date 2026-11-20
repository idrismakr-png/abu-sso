import bcrypt

from app.models.oidc import OIDCClient, OIDCAuthorizationCode


def test_oidc_client_exposes_registered_identity():
    client = OIDCClient(
        client_id="abu-student-portal",
        name="ABU Student Portal",
        redirect_uris=["http://localhost:8001/callback"],
        allowed_scopes=["openid", "profile", "email"],
        grant_types=["authorization_code"],
        response_types=["code"],
        token_endpoint_auth_method="none",
    )

    assert client.get_client_id() == "abu-student-portal"
    assert client.get_default_redirect_uri() == "http://localhost:8001/callback"


def test_oidc_client_validates_redirect_uri_exactly():
    client = OIDCClient(
        client_id="abu-student-portal",
        name="ABU Student Portal",
        redirect_uris=["http://localhost:8001/callback"],
    )

    assert client.check_redirect_uri("http://localhost:8001/callback")
    assert not client.check_redirect_uri("http://localhost:8001/other")
    assert not client.check_redirect_uri("http://localhost:8001/callback?next=admin")


def test_oidc_client_limits_requested_scopes():
    client = OIDCClient(
        client_id="abu-student-portal",
        name="ABU Student Portal",
        allowed_scopes=["openid", "profile", "email"],
    )

    assert client.get_allowed_scope("openid email") == "email openid"
    assert client.get_allowed_scope("openid admin") == "openid"


def test_oidc_client_checks_hashed_client_secret():
    secret = "test-client-secret"
    secret_hash = bcrypt.hashpw(
        secret.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")

    client = OIDCClient(
        client_id="abu-confidential-client",
        name="ABU Confidential Client",
        client_secret_hash=secret_hash,
    )

    assert client.check_client_secret(secret)
    assert not client.check_client_secret("incorrect-secret")


def test_oidc_client_checks_supported_grants_and_responses():
    client = OIDCClient(
        client_id="abu-student-portal",
        name="ABU Student Portal",
        grant_types=["authorization_code"],
        response_types=["code"],
    )

    assert client.check_grant_type("authorization_code")
    assert not client.check_grant_type("implicit")
    assert client.check_response_type("code")
    assert not client.check_response_type("token")


def test_oidc_authorization_code_exposes_required_values():
    authorization_code = OIDCAuthorizationCode(
        client_id="abu-student-portal",
        user_id="test-user-id",
        redirect_uri="http://localhost:8001/callback",
        scopes=["openid", "profile"],
        nonce="test-nonce",
        code_challenge="test-code-challenge",
        code_challenge_method="S256",
    )

    assert authorization_code.get_redirect_uri() == "http://localhost:8001/callback"
    assert authorization_code.get_scope() == "openid profile"
    assert authorization_code.get_nonce() == "test-nonce"
    assert authorization_code.get_auth_time() is None