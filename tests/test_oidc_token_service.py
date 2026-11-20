import pytest

from app.services.oidc_token_service import generate_access_token


def test_generates_secure_opaque_access_token():
    token = generate_access_token(
        grant_type="authorization_code",
        client=None,
        user=None,
        scope="openid profile",
    )

    assert token["token_type"] == "Bearer"
    assert isinstance(token["access_token"], str)
    assert len(token["access_token"]) >= 40
    assert token["scope"] == "openid profile"
    assert token["expires_in"] > 0


def test_generates_different_tokens_for_each_request():
    first = generate_access_token("authorization_code", None)
    second = generate_access_token("authorization_code", None)

    assert first["access_token"] != second["access_token"]


def test_rejects_unsupported_grant_type():
    with pytest.raises(ValueError, match="Unsupported OIDC token grant type"):
        generate_access_token("client_credentials", None)


def test_rejects_refresh_token_generation():
    with pytest.raises(ValueError, match="Refresh tokens are not yet supported"):
        generate_access_token(
            "authorization_code",
            None,
            include_refresh_token=True,
        )


def test_rejects_invalid_token_lifetime():
    with pytest.raises(ValueError, match="positive integer"):
        generate_access_token(
            "authorization_code",
            None,
            expires_in=0,
        )