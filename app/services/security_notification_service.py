from sqlalchemy.orm import Session

from app.models import AuthenticationEvent, SecurityNotification


def create_authentication_notification(
    db: Session,
    event: AuthenticationEvent,
) -> SecurityNotification | None:
    """Create one user-facing notification for a successful sign-in event.

    Central password logins and successful OIDC service authorizations are
    both sign-in events. The unique authentication_event_id makes creation
    idempotent. The caller owns the transaction and commits the changes.
    """

    is_central_login = (
        event.event_type == "login"
        and event.application_name == "ABU-SSO Portal"
    )
    is_service_authorization = (
        event.event_type == "authorization"
        and bool(event.client_id)
    )

    if (
        event.outcome != "success"
        or not event.user_id
        or not event.application_name
        or not (is_central_login or is_service_authorization)
    ):
        return None

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
            f"Your ABU account was used to sign in to "
            f"{event.application_name}."
        ),
    )
    db.add(notification)
    db.flush()
    return notification
