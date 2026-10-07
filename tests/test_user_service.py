import pytest

from app.services.user_service import (
    authenticate_user,
    create_user,
    get_user_by_email,
    get_user_by_id,
    get_user_by_matric,
)


def test_create_user_returns_user(db):
    user = create_user(
        db,
        email="student1@abu.edu.ng",
        password="secret123",
        full_name="Student One",
        role="student",
        matric_no="ABU/2024/0001",
    )
    assert user.id is not None
    assert user.email == "student1@abu.edu.ng"
    assert user.role == "student"
    assert user.is_active is True


def test_create_user_normalizes_email_to_lowercase(db):
    user = create_user(db, email="UPPER@ABU.EDU.NG", password="secret123")
    assert user.email == "upper@abu.edu.ng"


def test_create_user_duplicate_email_raises(db):
    create_user(db, email="dup@abu.edu.ng", password="secret123")
    with pytest.raises(ValueError, match="already registered"):
        create_user(db, email="dup@abu.edu.ng", password="another123")


def test_create_user_hashes_password(db):
    user = create_user(db, email="hash@abu.edu.ng", password="secret123")
    assert user.password_hash != "secret123"
    assert "secret123" not in user.password_hash


def test_get_user_by_email_finds_user(db):
    create_user(db, email="find@abu.edu.ng", password="secret123")
    user = get_user_by_email(db, "find@abu.edu.ng")
    assert user is not None
    assert user.email == "find@abu.edu.ng"


def test_get_user_by_email_case_insensitive(db):
    create_user(db, email="case@abu.edu.ng", password="secret123")
    user = get_user_by_email(db, "CASE@abu.edu.ng")
    assert user is not None


def test_get_user_by_email_returns_none_for_missing(db):
    assert get_user_by_email(db, "nobody@abu.edu.ng") is None


def test_get_user_by_id_works(db):
    created = create_user(db, email="byid@abu.edu.ng", password="secret123")
    user = get_user_by_id(db, created.id)
    assert user is not None
    assert user.id == created.id


def test_get_user_by_matric_works(db):
    create_user(
        db,
        email="matric@abu.edu.ng",
        password="secret123",
        matric_no="ABU/2024/9999",
    )
    user = get_user_by_matric(db, "ABU/2024/9999")
    assert user is not None
    assert user.matric_no == "ABU/2024/9999"


def test_authenticate_user_correct_password(db):
    create_user(db, email="auth@abu.edu.ng", password="secret123")
    user = authenticate_user(db, "auth@abu.edu.ng", "secret123")
    assert user is not None


def test_authenticate_user_wrong_password(db):
    create_user(db, email="auth2@abu.edu.ng", password="secret123")
    assert authenticate_user(db, "auth2@abu.edu.ng", "wrong") is None


def test_authenticate_user_missing_user(db):
    assert authenticate_user(db, "ghost@abu.edu.ng", "secret123") is None


def test_authenticate_user_inactive_user(db):
    user = create_user(db, email="inactive@abu.edu.ng", password="secret123")
    user.is_active = False
    db.commit()
    assert authenticate_user(db, "inactive@abu.edu.ng", "secret123") is None
    