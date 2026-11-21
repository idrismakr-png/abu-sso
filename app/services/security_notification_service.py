
from sqlalchemy.orm import Session

from app.models import AuthenticationEvent, SecurityNotification


def create_authentication_notification(
    db: Session,
    event: AuthenticationEvent,
) -> SecurityNotification | None:
    """
    Create one notification for a successful application authorization.

    The caller controls the database transaction and commits the changes.
    """

    if (
        event.outcome != "success"
        or event.event_type != "authorization"
        or not event.user_id
        or not event.client_id
        or not event.application_name
    ):
        return None

    # Ensure the authentication event has been assigned its database ID.
    db.flush()

    existing = (
        db.query(SecurityNotification)
        .filter_by(authentication_event_id=event.id)
        .first()
    )

    if existing is not None:
        return existing

    notification = SecurityNotification(
        user_id=event.user_id,
        authentication_event_id=event.id,
        title=f"New sign-in to {event.application_name}",
        message=(
            f"Your ABU account was used to authenticate with "
            f"{event.application_name}."
        ),
    )

    db.add(notification)
    db.flush()

    return notification
