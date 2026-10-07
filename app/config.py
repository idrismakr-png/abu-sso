from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables / .env file."""

    app_name: str = "ABU-SSO"
    app_version: str = "0.1.0"
    debug: bool = True

    # JWT settings (used later for authentication)
    jwt_secret: str = "change-me-in-production-with-a-much-longer-key-please-min-32-bytes"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15

    # Database
    database_url: str = "sqlite:///./abu_sso.db"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()