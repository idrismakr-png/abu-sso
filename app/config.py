
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables / .env file."""

    app_name: str = "ABU-SSO"
    app_version: str = "0.1.0"
    debug: bool = True

    # Legacy JWT settings
    # Retained to avoid breaking the existing authentication system.
    jwt_secret: str = "change-me-in-production-with-a-much-longer-key-please-min-32-bytes"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15

    # OpenID Connect (OIDC) identity provider settings
    oidc_issuer: str = "http://localhost:8000"
    oidc_signing_algorithm: str = "RS256"
    oidc_key_id: str = "abu-sso-rsa-2026"

    # RSA signing key locations
    oidc_private_key_path: str = "keys/abu_sso_private.pem"
    oidc_public_key_path: str = "keys/abu_sso_public.pem"

    # OIDC token and authorization lifetimes
    oidc_access_token_expire_minutes: int = 15
    oidc_id_token_expire_minutes: int = 15
    oidc_authorization_code_expire_minutes: int = 5

    # Database
    database_url: str = "sqlite:///./abu_sso.db"

    # Registration policy
    # In production: only the very first user can self-register (bootstrap admin).
    # In tests: set to true so test suites can create users freely.
    allow_public_registration: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
