from app.utils.security import hash_password, verify_password


def test_hash_password_returns_string():
    result = hash_password("secret123")
    assert isinstance(result, str)
    assert len(result) > 20


def test_hash_password_is_not_plaintext():
    result = hash_password("secret123")
    assert result != "secret123"
    assert "secret123" not in result


def test_hash_password_same_input_different_output():
    """bcrypt salts each hash, so two hashes of the same password differ."""
    h1 = hash_password("secret123")
    h2 = hash_password("secret123")
    assert h1 != h2


def test_verify_password_correct():
    h = hash_password("secret123")
    assert verify_password("secret123", h) is True


def test_verify_password_wrong():
    h = hash_password("secret123")
    assert verify_password("wrongpass", h) is False


def test_verify_password_empty_password():
    h = hash_password("secret123")
    assert verify_password("", h) is False


def test_hash_password_empty_raises():
    import pytest
    with pytest.raises(ValueError):
        hash_password("")
        