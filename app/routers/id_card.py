from fastapi import APIRouter, Depends

from app.models.user import User
from app.schemas.id_card import IdCardResponse
from app.services.qr_service import build_id_card_payload, generate_qr_data_url
from app.utils.jwt import get_current_user

router = APIRouter(
    prefix="/id-card",
    tags=["ID Card"],
)


@router.get("", response_model=IdCardResponse)
def get_my_id_card(current_user: User = Depends(get_current_user)):
    """Return the authenticated user's digital ID card with a QR code."""
    payload = build_id_card_payload(current_user)
    qr_data_url = generate_qr_data_url(payload)
    return IdCardResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        matric_no=current_user.matric_no,
        qr_data_url=qr_data_url,
    )