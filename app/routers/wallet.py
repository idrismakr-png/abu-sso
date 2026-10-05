from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.wallet import PayRequest, TopUpRequest, TransactionRead, WalletRead
from app.services.wallet_service import (
    get_or_create_wallet,
    list_transactions,
    pay,
    top_up,
)
from app.utils.jwt import get_current_user

router = APIRouter(
    prefix="/wallet",
    tags=["Wallet"],
)


@router.get("", response_model=WalletRead)
def get_my_wallet(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return the authenticated user's wallet (creates it if missing)."""
    wallet = get_or_create_wallet(db, current_user)
    return wallet


@router.get("/transactions", response_model=list[TransactionRead])
def get_my_transactions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return the most recent transactions for the authenticated user's wallet."""
    wallet = get_or_create_wallet(db, current_user)
    return list_transactions(db, wallet)


@router.post("/topup", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
def topup_wallet(
    payload: TopUpRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Top up the authenticated user's wallet.

    NOTE: In production this would require admin privileges or a payment gateway.
    For now, any authenticated user can top up their own wallet (fine for a demo).
    """
    wallet = get_or_create_wallet(db, current_user)
    try:
        txn = top_up(db, wallet, payload.amount, payload.description)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return txn


@router.post("/pay", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
def pay_from_wallet(
    payload: PayRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Pay from the authenticated user's wallet (e.g., library fine, hostel fee)."""
    wallet = get_or_create_wallet(db, current_user)
    try:
        txn = pay(db, wallet, payload.amount, payload.description)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return txn