
from urllib.parse import parse_qs, urlsplit


def test_authorize_redirects_unauthenticated_user_to_login(client):
    authorization_parameters = {
        "client_id": "test-unregistered-client",
        "response_type": "code",
        "redirect_uri": "http://localhost:8001/callback",
        "scope": "openid profile",
        "state": "test-state-123",
        "nonce": "test-nonce-123",
        "code_challenge": "test-challenge",
        "code_challenge_method": "S256",
    }

    response = client.get(
        "/authorize",
        params=authorization_parameters,
        follow_redirects=False,
    )

    assert response.status_code == 303

    location = response.headers["location"]

    assert location.startswith("/login?")

    query_parameters = parse_qs(urlsplit(location).query)

    assert "next" in query_parameters

    original_request = urlsplit(query_parameters["next"][0])

    assert original_request.path == "/authorize"

    preserved_parameters = parse_qs(original_request.query)

    for key, value in authorization_parameters.items():
        assert preserved_parameters[key] == [value]
