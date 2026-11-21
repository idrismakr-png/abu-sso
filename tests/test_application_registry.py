
from app.models import OIDCClient
from app.services.user_service import create_user


def _create_user(db, matric, email, role):
    return create_user(
        db,
        email=email,
        password="secret123",
        matric_no=matric,
        full_name="Registry Test User",
        role=role,
    )


def _login(client, matric):
    response = client.post(
        "/auth/login",
        json={
            "matric_no": matric,
            "password": "secret123",
        },
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_only_admin_can_register_applications(client, db):
    response = client.post(
        "/admin/applications",
        json={
            "name": "Student Portal",
            "redirect_uris": ["https://student.example.edu/callback"],
        },
    )
    assert response.status_code == 401

    _create_user(
        db,
        "REGISTRY/STUDENT",
        "registry-student@abu.edu.ng",
        "student",
    )
    student_headers = _login(client, "REGISTRY/STUDENT")

    response = client.post(
        "/admin/applications",
        json={
            "name": "Student Portal",
            "redirect_uris": ["https://student.example.edu/callback"],
        },
        headers=student_headers,
    )
    assert response.status_code == 403


def test_admin_can_register_public_application(client, db):
    _create_user(
        db,
        "REGISTRY/ADMIN1",
        "registry-admin1@abu.edu.ng",
        "admin",
    )
    headers = _login(client, "REGISTRY/ADMIN1")

    response = client.post(
        "/admin/applications",
        json={
            "name": "Student Portal",
            "client_type": "public",
            "redirect_uris": [
                "https://student.example.edu/callback"
            ],
        },
        headers=headers,
    )

    assert response.status_code == 201
    data = response.json()

    assert data["name"] == "Student Portal"
    assert data["client_type"] == "public"
    assert data["is_active"] is True
    assert data["redirect_uris"] == [
        "https://student.example.edu/callback"
    ]
    assert "client_id" in data
    assert "client_secret" not in data

    application = db.query(OIDCClient).filter_by(
        client_id=data["client_id"]
    ).one()

    assert application.require_pkce is True
    assert application.token_endpoint_auth_method == "none"


def test_confidential_secret_is_returned_only_at_registration(
    client,
    db,
):
    _create_user(
        db,
        "REGISTRY/ADMIN2",
        "registry-admin2@abu.edu.ng",
        "admin",
    )
    headers = _login(client, "REGISTRY/ADMIN2")

    response = client.post(
        "/admin/applications",
        json={
            "name": "Library Backend",
            "client_type": "confidential",
            "redirect_uris": [
                "https://library.example.edu/callback"
            ],
        },
        headers=headers,
    )

    assert response.status_code == 201
    data = response.json()

    assert data["client_secret"]
    assert data["client_type"] == "confidential"

    application = db.query(OIDCClient).filter_by(
        client_id=data["client_id"]
    ).one()

    assert application.client_secret_hash != data["client_secret"]
    assert application.check_client_secret(data["client_secret"])
    assert application.token_endpoint_auth_method == "client_secret_basic"

    listing = client.get(
        "/admin/applications",
        headers=headers,
    )

    assert listing.status_code == 200

    listed_application = next(
        item
        for item in listing.json()
        if item["client_id"] == data["client_id"]
    )

    assert "client_secret" not in listed_application
    assert "client_secret_hash" not in listed_application


def test_admin_can_deactivate_application(client, db):
    _create_user(
        db,
        "REGISTRY/ADMIN3",
        "registry-admin3@abu.edu.ng",
        "admin",
    )
    headers = _login(client, "REGISTRY/ADMIN3")

    registration = client.post(
        "/admin/applications",
        json={
            "name": "Results Portal",
            "redirect_uris": [
                "https://results.example.edu/callback"
            ],
        },
        headers=headers,
    )

    assert registration.status_code == 201
    client_id = registration.json()["client_id"]

    response = client.patch(
        f"/admin/applications/{client_id}/active?active=false",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is False

    application = db.query(OIDCClient).filter_by(
        client_id=client_id
    ).one()

    assert application.is_active is False


def test_application_registration_rejects_insecure_redirect_uri(
    client,
    db,
):
    _create_user(
        db,
        "REGISTRY/ADMIN4",
        "registry-admin4@abu.edu.ng",
        "admin",
    )
    headers = _login(client, "REGISTRY/ADMIN4")

    response = client.post(
        "/admin/applications",
        json={
            "name": "Unsafe Portal",
            "redirect_uris": [
                "http://example.edu/callback"
            ],
        },
        headers=headers,
    )

    assert response.status_code == 422
