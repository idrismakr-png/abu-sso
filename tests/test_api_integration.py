def register(client, email="api@abu.edu.ng", password="secret123", matric_no="ABU/2024/1111", **extra):
    payload = {"email": email, "password": password, "matric_no": matric_no, **extra}
    return client.post("/auth/register", json=payload)


def login(client, matric_no="ABU/2024/1111", password="secret123"):
    return client.post("/auth/login", json={"matric_no": matric_no, "password": password})


def auth_headers(client, matric_no="ABU/2024/1111", password="secret123"):
    res = login(client, matric_no, password)
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ---------- REGISTER ----------

def test_register_returns_201_and_user(client):
    res = register(client, full_name="API Tester", matric_no="ABU/2024/1111")
    assert res.status_code == 201
    data = res.json()
    assert data["email"] == "api@abu.edu.ng"
    assert data["full_name"] == "API Tester"
    assert data["matric_no"] == "ABU/2024/1111"
    assert data["is_active"] is True
    assert "password" not in data
    assert "password_hash" not in data


def test_register_duplicate_email_returns_400(client):
    register(client)
    res = register(client, matric_no="ABU/2024/2222")
    assert res.status_code == 400


def test_register_duplicate_matric_returns_400(client):
    register(client, email="first@abu.edu.ng", matric_no="ABU/2024/3333")
    res = register(client, email="second@abu.edu.ng", matric_no="ABU/2024/3333")
    assert res.status_code == 400


def test_register_missing_matric_returns_422(client):
    res = client.post("/auth/register", json={"email": "noMatric@abu.edu.ng", "password": "secret123"})
    assert res.status_code == 422


def test_register_invalid_email_returns_422(client):
    res = client.post(
        "/auth/register",
        json={"email": "not-an-email", "password": "secret123", "matric_no": "ABU/2024/4444"},
    )
    assert res.status_code == 422


def test_register_short_password_returns_422(client):
    res = client.post(
        "/auth/register",
        json={"email": "short@abu.edu.ng", "password": "12", "matric_no": "ABU/2024/5555"},
    )
    assert res.status_code == 422


# ---------- LOGIN ----------

def test_login_returns_token(client):
    register(client)
    res = login(client)
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 20


def test_login_with_lowercase_matric_works(client):
    register(client, matric_no="ABU/2024/6666")
    res = login(client, matric_no="abu/2024/6666")
    assert res.status_code == 200


def test_login_wrong_password_returns_401(client):
    register(client)
    res = login(client, password="wrongpass")
    assert res.status_code == 401


def test_login_unknown_user_returns_401(client):
    res = login(client, matric_no="ABU/2024/GHOST")
    assert res.status_code == 401


# ---------- /auth/me ----------

def test_me_without_token_returns_401(client):
    res = client.get("/auth/me")
    assert res.status_code == 401


def test_me_with_bad_token_returns_401(client):
    res = client.get("/auth/me", headers={"Authorization": "Bearer nonsense"})
    assert res.status_code == 401


def test_me_with_valid_token_returns_user(client):
    register(client, full_name="API Tester")
    headers = auth_headers(client)
    res = client.get("/auth/me", headers=headers)
    assert res.status_code == 200
    assert res.json()["email"] == "api@abu.edu.ng"


# ---------- ID CARD ----------

def test_id_card_requires_auth(client):
    res = client.get("/id-card")
    assert res.status_code == 401


def test_id_card_returns_qr_data_url(client):
    register(client, full_name="API Tester", matric_no="ABU/2024/1111")
    headers = auth_headers(client)
    res = client.get("/id-card", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["qr_data_url"].startswith("data:image/png;base64,")
    assert data["matric_no"] == "ABU/2024/1111"


# ---------- WALLET ----------

def test_wallet_requires_auth(client):
    res = client.get("/wallet")
    assert res.status_code == 401


def test_wallet_auto_created_with_zero_balance(client):
    register(client)
    headers = auth_headers(client)
    res = client.get("/wallet", headers=headers)
    assert res.status_code == 200
    assert res.json()["balance"] == "0.00"


def test_wallet_topup_credits_balance(client):
    register(client)
    headers = auth_headers(client)
    res = client.post("/wallet/topup", json={"amount": 1000, "description": "Test"}, headers=headers)
    assert res.status_code == 201
    assert res.json()["type"] == "credit"

    balance = client.get("/wallet", headers=headers).json()["balance"]
    assert balance == "1000.00"


def test_wallet_pay_debits_balance(client):
    register(client)
    headers = auth_headers(client)
    client.post("/wallet/topup", json={"amount": 500}, headers=headers)
    res = client.post("/wallet/pay", json={"amount": 200, "description": "Fine"}, headers=headers)
    assert res.status_code == 201
    assert res.json()["type"] == "debit"

    balance = client.get("/wallet", headers=headers).json()["balance"]
    assert balance == "300.00"


def test_wallet_pay_insufficient_funds_returns_400(client):
    register(client)
    headers = auth_headers(client)
    res = client.post("/wallet/pay", json={"amount": 5000}, headers=headers)
    assert res.status_code == 400


def test_wallet_negative_topup_returns_422(client):
    register(client)
    headers = auth_headers(client)
    res = client.post("/wallet/topup", json={"amount": -100}, headers=headers)
    assert res.status_code == 422


def test_wallet_transactions_returns_list(client):
    register(client)
    headers = auth_headers(client)
    client.post("/wallet/topup", json={"amount": 500, "description": "Initial"}, headers=headers)
    client.post("/wallet/pay", json={"amount": 100, "description": "Fine"}, headers=headers)
    res = client.get("/wallet/transactions", headers=headers)
    assert res.status_code == 200
    assert len(res.json()) == 2


# ---------- HEALTH / ROOT ----------

def test_health_endpoint(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"


def test_root_endpoint(client):
    res = client.get("/")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"