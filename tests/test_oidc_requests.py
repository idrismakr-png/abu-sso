import pytest

from starlette.requests import Request

from app.utils.oidc_requests import create_oauth2_request


def make_request(method, query_string=b"", body=b"", headers=None):
    async def receive():
        return {
            "type": "http.request",
            "body": body,
            "more_body": False,
        }

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": "/authorize" if method == "GET" else "/token",
        "raw_path": b"/authorize" if method == "GET" else b"/token",
        "query_string": query_string,
        "headers": headers or [(b"host", b"localhost")],
        "server": ("localhost", 80),
        "client": ("127.0.0.1", 12345),
    }

    return Request(scope, receive)


@pytest.mark.asyncio
async def test_get_authorization_request_preserves_query_parameters():
    request = make_request(
        "GET",
        query_string=b"client_id=abu-portal&scope=openid&scope=email",
    )

    oauth_request = await create_oauth2_request(request)

    assert oauth_request.method == "GET"
    assert oauth_request.payload.client_id == "abu-portal"
    assert oauth_request.payload.datalist["scope"] == ["openid", "email"]
    assert oauth_request.args.get("client_id") == "abu-portal"


@pytest.mark.asyncio
async def test_post_token_request_reads_form_data():
    request = make_request(
        "POST",
        body=b"grant_type=authorization_code&client_id=abu-portal&code=test-code",
        headers=[
            (b"host", b"localhost"),
            (b"content-type", b"application/x-www-form-urlencoded"),
        ],
    )

    oauth_request = await create_oauth2_request(request)

    assert oauth_request.method == "POST"
    assert oauth_request.payload.grant_type == "authorization_code"
    assert oauth_request.form.get("client_id") == "abu-portal"
    assert oauth_request.form.get("code") == "test-code"


@pytest.mark.asyncio
async def test_post_request_preserves_duplicate_form_parameters():
    request = make_request(
        "POST",
        body=b"scope=openid&scope=email",
        headers=[
            (b"host", b"localhost"),
            (b"content-type", b"application/x-www-form-urlencoded"),
        ],
    )

    oauth_request = await create_oauth2_request(request)

    assert oauth_request.payload.datalist["scope"] == ["openid", "email"]