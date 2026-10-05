from pydantic import BaseModel


class IdCardResponse(BaseModel):
    """Digital ID card payload returned to the authenticated user."""

    id: str
    email: str
    full_name: str | None
    role: str
    matric_no: str | None
    qr_data_url: str  # data:image/png;base64,....