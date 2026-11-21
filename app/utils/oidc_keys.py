
import base64
import os
from functools import lru_cache
from pathlib import Path

from cryptography.hazmat.primitives.serialization import (
    load_pem_private_key,
    load_pem_public_key,
)

from app.config import settings


def _base64url_uint(value: int) -> str:
    """Encode an RSA integer as an unpadded Base64URL string."""
    byte_length = (value.bit_length() + 7) // 8
    encoded = value.to_bytes(byte_length, byteorder="big")

    return base64.urlsafe_b64encode(encoded).rstrip(b"=").decode("ascii")


def _load_key_bytes(environment_variable: str, configured_path: str) -> bytes:
    """
    Load PEM key material from a Base64 environment variable when available.
    Otherwise, load it from the configured local file path.
    """
    encoded_key = os.getenv(environment_variable)

    if encoded_key:
        try:
            return base64.b64decode(
                encoded_key.strip(),
                validate=True,
            )
        except (ValueError, base64.binascii.Error) as exc:
            raise RuntimeError(
                f"{environment_variable} must contain valid Base64-encoded PEM data."
            ) from exc

    key_path = Path(configured_path)

    if not key_path.is_absolute():
        key_path = Path(__file__).resolve().parents[2] / key_path

    if not key_path.is_file():
        raise RuntimeError(
            f"OIDC signing key was not found. Configure "
            f"{environment_variable} or provide the file: {key_path}"
        )

    return key_path.read_bytes()


@lru_cache(maxsize=1)
def get_private_key():
    """Load and cache the RSA private key used for token signing."""
    private_key_bytes = _load_key_bytes(
        "OIDC_PRIVATE_KEY_B64",
        settings.oidc_private_key_path,
    )

    private_key = load_pem_private_key(
        private_key_bytes,
        password=None,
    )

    if private_key.key_size < 2048:
        raise RuntimeError(
            "OIDC RSA signing key must be at least 2048 bits"
        )

    return private_key


@lru_cache(maxsize=1)
def get_public_jwk() -> dict:
    """Return the public RSA key in JSON Web Key format."""
    public_key_bytes = _load_key_bytes(
        "OIDC_PUBLIC_KEY_B64",
        settings.oidc_public_key_path,
    )

    public_key = load_pem_public_key(public_key_bytes)

    private_public_numbers = (
        get_private_key().public_key().public_numbers()
    )
    public_numbers = public_key.public_numbers()

    if private_public_numbers != public_numbers:
        raise RuntimeError(
            "OIDC public key does not match the configured private key"
        )

    return {
        "kty": "RSA",
        "use": "sig",
        "alg": settings.oidc_signing_algorithm,
        "kid": settings.oidc_key_id,
        "n": _base64url_uint(public_numbers.n),
        "e": _base64url_uint(public_numbers.e),
    }


def get_jwks() -> dict:
    """Return the public JSON Web Key Set."""
    return {
        "keys": [get_public_jwk()],
    }
