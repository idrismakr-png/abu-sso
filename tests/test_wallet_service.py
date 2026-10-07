from decimal import Decimal

import pytest

from app.services.user_service import create_user
from app.services.wallet_service import (
    get_or_create_wallet,
    list_transactions,
    pay,
    top_up,
)


@pytest.fixture
def user(db):
    return create_user(db, email="walletuser@abu.edu.ng", password="secret123")


def test_get_or_create_wallet_creates_wallet_with_zero_balance(db, user):
    wallet = get_or_create_wallet(db, user)
    assert wallet.id is not None
    assert wallet.user_id == user.id
    assert wallet.balance == Decimal("0.00")


def test_get_or_create_wallet_is_idempotent(db, user):
    w1 = get_or_create_wallet(db, user)
    w2 = get_or_create_wallet(db, user)
    assert w1.id == w2.id


def test_top_up_increases_balance(db, user):
    wallet = get_or_create_wallet(db, user)
    txn = top_up(db, wallet, Decimal("1000.00"), "Test top-up")
    assert wallet.balance == Decimal("1000.00")
    assert txn.type == "credit"
    assert txn.amount == Decimal("1000.00")
    assert txn.description == "Test top-up"


def test_top_up_multiple_times_accumulates(db, user):
    wallet = get_or_create_wallet(db, user)
    top_up(db, wallet, Decimal("500.00"))
    top_up(db, wallet, Decimal("300.00"))
    assert wallet.balance == Decimal("800.00")


def test_top_up_zero_raises(db, user):
    wallet = get_or_create_wallet(db, user)
    with pytest.raises(ValueError, match="positive"):
        top_up(db, wallet, Decimal("0"))


def test_top_up_negative_raises(db, user):
    wallet = get_or_create_wallet(db, user)
    with pytest.raises(ValueError, match="positive"):
        top_up(db, wallet, Decimal("-50"))


def test_pay_decreases_balance(db, user):
    wallet = get_or_create_wallet(db, user)
    top_up(db, wallet, Decimal("1000.00"))
    txn = pay(db, wallet, Decimal("250.00"), "Library fine")
    assert wallet.balance == Decimal("750.00")
    assert txn.type == "debit"
    assert txn.amount == Decimal("250.00")


def test_pay_insufficient_funds_raises(db, user):
    wallet = get_or_create_wallet(db, user)
    top_up(db, wallet, Decimal("100.00"))
    with pytest.raises(ValueError, match="Insufficient funds"):
        pay(db, wallet, Decimal("500.00"))


def test_pay_insufficient_funds_does_not_change_balance(db, user):
    wallet = get_or_create_wallet(db, user)
    top_up(db, wallet, Decimal("100.00"))
    try:
        pay(db, wallet, Decimal("500.00"))
    except ValueError:
        pass
    assert wallet.balance == Decimal("100.00")


def test_pay_zero_raises(db, user):
    wallet = get_or_create_wallet(db, user)
    top_up(db, wallet, Decimal("100.00"))
    with pytest.raises(ValueError, match="positive"):
        pay(db, wallet, Decimal("0"))


def test_list_transactions_returns_all(db, user):
    wallet = get_or_create_wallet(db, user)
    top_up(db, wallet, Decimal("1000.00"), "Initial")
    pay(db, wallet, Decimal("250.00"), "Fine")
    pay(db, wallet, Decimal("100.00"), "Snack")
    txns = list_transactions(db, wallet)
    assert len(txns) == 3


def test_list_transactions_newest_first(db, user):
    wallet = get_or_create_wallet(db, user)
    top_up(db, wallet, Decimal("1000.00"), "First")
    top_up(db, wallet, Decimal("500.00"), "Second")
    txns = list_transactions(db, wallet)
    # Most recent first
    assert txns[0].description == "Second"
    assert txns[1].description == "First"