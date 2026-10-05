import base64
import io
import json

import qrcode

from app.models.user import User


def build_id_card_payload(user: User) -> str:
    """The small JSON payload that gets encoded into the QR code."""
    return json.dumps(
        {
            "id": user.id,
            "matric_no": user.matric_no,
            "role": user.role,
        },
        separators=(",", ":"),
    )


def generate_qr_data_url(data: str) -> str:
    """Generate a QR code for `data` and return it as a PNG data URL."""
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"