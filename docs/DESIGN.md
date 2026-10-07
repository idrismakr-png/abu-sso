# Design Document
## ABU-SSO: Unified Single Sign-On & Digital Campus Wallet

**Course:** COEN838 — Advanced Software Engineering  
**Student:** Idris Muhammad Abubakar  
**Matric No:** P25EGCP9003  

---

## 1. Architectural Overview

### 1.1 Architectural Style

ABU-SSO is a **modular monolith** structured as a **layered architecture**, organised around **feature routers** rather than technical layers.

**Why modular monolith (and not microservices)?**

| Consideration | Modular Monolith | Microservices |
|---------------|:----------------:|:-------------:|
| Team size | ✅ 1 developer | ❌ Needs 3+ teams |
| Deployment complexity | ✅ Single process | ❌ Container orchestration |
| Learning curve | ✅ Simple | ❌ High |
| Growth path | ✅ Services can be extracted | ✅ Native |
| Consistency | ✅ Single transaction | ❌ Saga needed |

The modular monolith was chosen because the project is built by a single developer within a course timeframe, but the **service boundaries are already drawn** so any router (`auth`, `wallet`, `id_card`) could be extracted into its own microservice without rewriting business logic.

### 1.2 Layer Responsibilities

┌─────────────────────────────────────────┐
│ Presentation │ Jinja2 HTML + CSS + JS
│ (app/templates, app/static) │
├─────────────────────────────────────────┤
│ HTTP / Routers │ FastAPI route handlers
│ (app/routers/.py) │ (thin — no business logic)
├─────────────────────────────────────────┤
│ Services │ Business rules
│ (app/services/.py) │ (no HTTP, no DB session creation)
├─────────────────────────────────────────┤
│ Models & Schemas │ SQLAlchemy ORM + Pydantic
│ (app/models, app/schemas) │
├─────────────────────────────────────────┤
│ Persistence │ SQLite (dev) / PostgreSQL (prod)
│ (app/database.py) │
└─────────────────────────────────────────┘


**Rule enforced:** each layer only talks to the one directly below it. Routers never touch the database directly — they call services.

### 1.3 Inter-Component Communication

- **Client → Server:** HTTP/1.1 with JSON bodies (or HTML for pages).
- **Server → Third-party services:** synchronous REST; the JWT is forwarded in `Authorization: Bearer`.
- **Style chosen:** synchronous request-response, because authentication decisions must be immediate.

Future asynchronous events (e.g. "notify user on wallet top-up") would use a message broker — out of scope for this prototype.

---

## 2. Component Design

### 2.1 Authentication Component

| File | Responsibility |
|------|----------------|
| `app/routers/auth.py` | HTTP endpoints: `/auth/register`, `/auth/login`, `/auth/me` |
| `app/services/user_service.py` | `create_user`, `authenticate_user`, lookup helpers |
| `app/utils/security.py` | `hash_password`, `verify_password` (bcrypt) |
| `app/utils/jwt.py` | `create_access_token`, `decode_token`, `get_current_user` dependency |
| `app/schemas/user.py` | Pydantic schemas: `UserCreate`, `UserRead`, `UserLogin`, `Token` |

**Key design decision:** `get_current_user` is a FastAPI dependency. Any protected route simply declares `current_user: User = Depends(get_current_user)` — the authentication logic lives in exactly one place.

### 2.2 Wallet Component

| File | Responsibility |
|------|----------------|
| `app/routers/wallet.py` | HTTP endpoints: `/wallet`, `/wallet/topup`, `/wallet/pay`, `/wallet/transactions` |
| `app/services/wallet_service.py` | `get_or_create_wallet`, `top_up`, `pay`, `list_transactions` |
| `app/models/wallet.py` | `Wallet` + `Transaction` ORM models |
| `app/schemas/wallet.py` | `WalletRead`, `TransactionRead`, `TopUpRequest`, `PayRequest` |

**Key design decision:** every wallet operation is **atomic** — the balance update and the transaction insert happen in a single `db.commit()`. If the balance is insufficient, `pay()` raises before touching the DB.

### 2.3 Digital ID Card Component

| File | Responsibility |
|------|----------------|
| `app/routers/id_card.py` | Endpoint `/id-card` |
| `app/services/qr_service.py` | `build_id_card_payload`, `generate_qr_data_url` |
| `app/schemas/id_card.py` | `IdCardResponse` |

**Key design decision:** the QR code encodes only `{id, matric_no, role}` — no personal data — reducing the risk of information disclosure if a card is photographed.

### 2.4 Presentation Component

| File | Responsibility |
|------|----------------|
| `app/routers/pages.py` | Serves `/login` and `/dashboard` |
| `app/templates/base.html`, `login.html`, `dashboard.html` | Jinja2 templates |
| `app/static/css/style.css` | Green campus theme |
| `app/static/js/app.js` | Shared JS; page-specific logic inline in templates |

The dashboard calls `/auth/me`, `/wallet`, `/wallet/transactions`, and `/id-card` using the JWT stored in `localStorage`.

---

## 3. Data Design

### 3.1 Entity Relationship Diagram

See `docs/diagrams/class_model.png`.

### 3.2 Table Definitions

**`users`**

| Column | Type | Constraint |
|--------|------|-----------|
| id | VARCHAR(36) | PRIMARY KEY |
| email | VARCHAR(255) | UNIQUE, NOT NULL, INDEXED |
| password_hash | VARCHAR(255) | NOT NULL |
| full_name | VARCHAR(255) | NULL |
| role | VARCHAR(50) | NOT NULL, default 'student' |
| matric_no | VARCHAR(50) | NULL, INDEXED |
| is_active | BOOLEAN | NOT NULL, default TRUE |
| created_at | DATETIME | NOT NULL |

**`wallets`**

| Column | Type | Constraint |
|--------|------|-----------|
| id | VARCHAR(36) | PRIMARY KEY |
| user_id | VARCHAR(36) | FOREIGN KEY → users.id, UNIQUE |
| balance | NUMERIC(10,2) | NOT NULL, default 0 |
| created_at | DATETIME | NOT NULL |

**`transactions`**

| Column | Type | Constraint |
|--------|------|-----------|
| id | VARCHAR(36) | PRIMARY KEY |
| wallet_id | VARCHAR(36) | FOREIGN KEY → wallets.id |
| amount | NUMERIC(10,2) | NOT NULL |
| type | VARCHAR(20) | NOT NULL, `credit` or `debit` |
| description | VARCHAR(255) | NULL |
| created_at | DATETIME | NOT NULL |

### 3.3 Design Decisions

- **UUIDs instead of integers** for primary keys — safe to expose in URLs, work identically in SQLite and PostgreSQL.
- **`Numeric(10,2)` for money** — avoids floating-point rounding errors.
- **Wallet created lazily** — users who never use the wallet don't consume a row.
- **Cascade delete** — deleting a wallet removes its transactions automatically.

---

## 4. Sequence Design — Payment Flow

See `docs/diagrams/sequence_login.png` for the login sequence. Below is the wallet payment flow:

Client (browser)
│
│ POST /wallet/pay {amount: 250}
│ Authorization: Bearer <JWT>
▼
Router (wallet.py: pay_from_wallet)
│
├─ Depends(get_current_user) ──► JWT validated, User loaded
│
├─ Depends(get_db) ─────────────► DB session opened
│
├─ wallet_service.get_or_create_wallet(db, user)
│
└─ wallet_service.pay(db, wallet, 250)
│
├─ if amount <= 0: raise ValueError
├─ if balance < amount: raise ValueError
│
├─ wallet.balance -= 250
├─ db.add(Transaction(type='debit', amount=250))
├─ db.commit()
│
└─ return Transaction
│
▼
Client receives 201 Created + transaction JSON


---

## 5. Resilience & Scalability

### 5.1 Resilience

- **Fail securely:** any auth failure returns HTTP 401 with a generic message — no info leak about whether the user exists.
- **Transaction atomicity:** wallet balance and transaction record are committed together; a crash between the two cannot occur.
- **Stateless auth:** if any server instance dies, the user's token continues to work on another instance.

### 5.2 Scalability

- **Horizontal scaling:** the app is stateless (JWT), so multiple instances can run behind a load balancer.
- **Database growth:** SQLite is single-writer; at production scale, change `DATABASE_URL` to PostgreSQL — no code changes.
- **Read replicas:** future work can add PostgreSQL read replicas for `/auth/me` reads.

### 5.3 Known Limitations

- No rate limiting yet (planned via `slowapi`).
- No refresh tokens — users must log in every 15 minutes.
- No async task queue — everything is synchronous in the request cycle.

---

## 6. Design Patterns Applied

| Pattern | Where | Why |
|---------|-------|-----|
| **Repository / Service Layer** | `app/services/*.py` | Business logic separated from HTTP |
| **Dependency Injection** | FastAPI `Depends()` for DB and current user | Testable; single source of truth |
| **Schema / DTO** | Pydantic `*Create`, `*Read` classes | Never leak ORM internals to API |
| **Singleton** | `settings = Settings()` in `config.py` | One configuration source |
| **Factory** | `create_engine`, `sessionmaker` in `database.py` | Configurable DB backend |
| **Middleware** | `get_current_user` dependency | Cross-cutting auth for all protected routes |
| **Layered Architecture** | Routers / Services / Models | Clear responsibilities |

---

## 7. Technology Choices — Justification

| Choice | Alternative | Why we chose ours |
|--------|-------------|-------------------|
| FastAPI | Flask / Django | Async-native, auto-generated OpenAPI, type-driven |
| SQLAlchemy | Raw SQL / Django ORM | Portable between SQLite and PostgreSQL |
| SQLite (dev) | PostgreSQL from day 1 | Zero setup for a beginner; migrate later |
| JWT (HS256) | Server-side sessions | Stateless; ideal for SSO across services |
| bcrypt | SHA-256 | Designed for password storage; salted; slow by design |
| Jinja2 + vanilla JS | React / Vue | Simpler; sufficient for a two-page UI |
| pytest | unittest | Cleaner syntax, better fixtures |
| GitHub Actions | Jenkins | Free, integrated with GitHub |
| Bandit | Manual review | Automated SAST — evidence for security rubric |

---

*End of Design Document.*
