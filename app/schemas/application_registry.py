
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, Field, field_validator


class ApplicationRegistrationRequest(BaseModel):
    """Validated input for an administrator registering an OIDC client."""

    name: str = Field(min_length=2, max_length=150)
    client_type: Literal["public", "confidential"] = "public"
    redirect_uris: list[str] = Field(min_length=1, max_length=10)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Application name cannot be empty.")

        return value

    @field_validator("redirect_uris")
    @classmethod
    def validate_redirect_uris(cls, values: list[str]) -> list[str]:
        validated = []

        for uri in values:
            if not isinstance(uri, str) or not uri:
                raise ValueError("Redirect URIs must be non-empty strings.")

            if uri != uri.strip():
                raise ValueError("Redirect URIs cannot contain surrounding whitespace.")

            if "*" in uri:
                raise ValueError("Wildcard redirect URIs are not permitted.")

            try:
                parsed = urlsplit(uri)
                hostname = parsed.hostname
                port = parsed.port
            except ValueError:
                raise ValueError("A redirect URI is malformed.")

            if not parsed.scheme or not hostname:
                raise ValueError("Redirect URIs must be absolute URLs.")

            if parsed.username or parsed.password:
                raise ValueError("Redirect URIs cannot contain user credentials.")

            if parsed.fragment:
                raise ValueError("Redirect URIs cannot contain fragments.")

            is_localhost = hostname.lower() in {
                "localhost",
                "127.0.0.1",
                "::1",
            }

            if parsed.scheme != "https":
                if not (parsed.scheme == "http" and is_localhost):
                    raise ValueError(
                        "Redirect URIs must use HTTPS, except on localhost."
                    )

            if port is not None and not (1 <= port <= 65535):
                raise ValueError("Redirect URI contains an invalid port.")

            validated.append(uri)

        if len(validated) != len(set(validated)):
            raise ValueError("Duplicate redirect URIs are not permitted.")

        return validated


class ApplicationRegistryView(BaseModel):
    """Safe application details returned by the registry API."""

    id: str
    client_id: str
    name: str
    client_type: str
    redirect_uris: list[str]
    allowed_scopes: list[str]
    is_active: bool

    model_config = {"from_attributes": True}
