
from app.config import settings


def test_openid_configuration_returns_expected_metadata(client):
    response = client.get("/.well-known/openid-configuration")

    assert response.status_code == 200

    metadata = response.json()

    issuer = settings.oidc_issuer.rstrip("/")

    assert metadata["issuer"] == issuer
    assert metadata["authorization_endpoint"] == f"{issuer}/authorize"
    assert metadata["token_endpoint"] == f"{issuer}/token"
    assert metadata["jwks_uri"] == f"{issuer}/jwks.json"

    assert metadata["response_types_supported"] == ["code"]
    assert metadata["grant_types_supported"] == ["authorization_code"]
    assert metadata["subject_types_supported"] == ["public"]
    assert metadata["id_token_signing_alg_values_supported"] == [
        settings.oidc_signing_algorithm
    ]

    assert metadata["scopes_supported"] == [
        "openid",
        "profile",
        "email",
    ]

    assert metadata["code_challenge_methods_supported"] == ["S256"]


def test_openid_configuration_removes_trailing_issuer_slash(
    client,
    monkeypatch,
):
    monkeypatch.setattr(
        settings,
        "oidc_issuer",
        "https://sso.abu.edu.ng/",
    )

    response = client.get("/.well-known/openid-configuration")

    assert response.status_code == 200
    assert response.json()["issuer"] == "https://sso.abu.edu.ng"
    assert (
        response.json()["authorization_endpoint"]
        == "https://sso.abu.edu.ng/authorize"
    )
