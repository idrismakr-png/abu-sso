## 3. Specific Requirements

### 3.1 Functional Requirements (FRs)

Each FR is assigned a unique ID for traceability to design and test artefacts.

| ID | Requirement | Priority | Actor |
|----|-------------|----------|-------|
| **FR-01** | The system shall allow a new user to register with email, password, full name, role, and optional matric number. | Must | Student, Staff |
| **FR-02** | The system shall reject registration attempts with an email that already exists. | Must | System |
| **FR-03** | The system shall hash all passwords using bcrypt before storage; the plaintext password shall never be persisted. | Must | System |
| **FR-04** | The system shall allow a registered user to log in with email and password. | Must | Student, Staff |
| **FR-05** | On successful login, the system shall return a signed JWT access token with a 15-minute expiry. | Must | System |
| **FR-06** | The system shall allow the authenticated user to retrieve their own profile (`/auth/me`) using the JWT. | Must | Student, Staff |
| **FR-07** | The system shall generate a digital ID card containing the user's name, matric number, role, and a QR code encoding `{id, matric_no, role}`. | Must | Student, Staff |
| **FR-08** | The system shall automatically create a wallet (starting balance ₦0.00) for a user on first access. | Must | System |
| **FR-09** | The system shall allow an authenticated user to top up their wallet with a positive amount. | Must | Student, Staff |
| **FR-10** | The system shall allow an authenticated user to pay from their wallet, provided the balance is sufficient. | Must | Student, Staff |
| **FR-11** | The system shall record every top-up and payment as a `credit` or `debit` transaction with a timestamp. | Must | System |
| **FR-12** | The system shall allow an authenticated user to view their transaction history (most recent first). | Must | Student, Staff |
| **FR-13** | The system shall distinguish between user roles: `student`, `staff`, and `admin`. | Should | System |
| **FR-14** | The system shall expose a health-check endpoint (`/health`) for monitoring. | Must | System, DevOps |
| **FR-15** | The system shall render a web-based login page and a dashboard for authenticated users. | Must | Student, Staff |

### 3.2 Non-Functional Requirements (NFRs)

NFRs are expressed as **quality attribute scenarios** in the format:  
`Stimulus → System Artifact → Response → Quantitative Metric`

| ID | Category | Scenario | Metric |
|----|----------|----------|--------|
| **NFR-01** | Performance | When a user submits login credentials, the system shall return a response within 500 ms at the 95th percentile under normal load. | p95 latency ≤ 500 ms |
| **NFR-02** | Security (Confidentiality) | All user passwords shall be hashed with bcrypt using a work factor of ≥ 12. | bcrypt cost ≥ 12 |
| **NFR-03** | Security (Authentication) | Every protected endpoint shall reject requests without a valid, unexpired JWT. | HTTP 401 on missing/expired token |
| **NFR-04** | Security (Integrity) | JWT tokens shall be signed with HS256 using a secret of ≥ 32 bytes. | RFC 7518 compliance |
| **NFR-05** | Reliability | The `/health` endpoint shall return HTTP 200 whenever the application is running. | Uptime monitoring |
| **NFR-06** | Usability | A new user shall be able to register and log in within 2 minutes of first visiting the login page. | Task-completion time ≤ 2 min |
| **NFR-07** | Maintainability | The codebase shall be divided into routers, services, models, and schemas to allow modification of one feature without affecting others. | Cyclomatic complexity ≤ 10 per function |
| **NFR-08** | Testability | The system shall have automated tests covering at least 70 % of the source code. | ≥ 70 % line coverage (pytest-cov) |
| **NFR-09** | Portability | The system shall run on Windows (development) and Linux (production) without code changes. | Docker/cloud deployable |
| **NFR-10** | Interoperability | All endpoints shall be documented via OpenAPI 3.0 and consumable by any HTTP client. | Auto-generated Swagger at `/docs` |
| **NFR-11** | Scalability | The system shall be deployable behind a load balancer without modifying authentication (stateless JWT). | Horizontal scale-out feasible |
| **NFR-12** | Availability | The system shall target 99 % uptime during the exam demonstration period. | Uptime ≥ 99 % (local demo) |

### 3.3 Interface Requirements

#### 3.3.1 User Interfaces

- **Login page (`/login`)** — email + password form; error messages in red; success redirects to `/dashboard`.
- **Dashboard (`/dashboard`)** — displays welcome message, wallet balance, transaction list, QR ID card, and links to connected services.
- **Swagger UI (`/docs`)** — auto-generated interactive API documentation.

#### 3.3.2 Software Interfaces

| External System | Interface | Protocol | Purpose |
|----------------|-----------|----------|---------|
| Student Portal (mock) | REST | HTTPS/JSON | SSO login via JWT |
| LMS / Moodle (mock) | REST | HTTPS/JSON | SSO login via JWT |
| Library System (mock) | REST | HTTPS/JSON | SSO login via JWT |
| Database | SQLAlchemy | SQLite / PostgreSQL | Persistent storage |

#### 3.3.3 Hardware Interfaces

No specialized hardware is required for the prototype. In a real deployment, the QR code on the digital ID card would be scanned by handheld scanners at library and hostel gateways.

#### 3.3.4 Communication Interfaces

- All client-server communication uses HTTPS in production (TLS 1.2+).
- JWTs are transmitted in the `Authorization: Bearer <token>` HTTP header.
- JSON is the only data format for request and response bodies (except HTML pages).

## 4. From User Needs to Technical Specifications

### 4.1 Requirements Elicitation

To move from user needs to precise specifications, the following elicitation techniques were applied:

| Technique | Application to ABU-SSO |
|-----------|----------------------|
| **Interviews** | Informal interviews with 3 current ABU students about their daily frustration with multiple credentials (portal, LMS, Wi-Fi, hostel). |
| **Ethnography / Contextual Inquiry** | Observation of students in the Faculty of Engineering computer lab struggling to log in to the LMS after resetting their portal password. |
| **Document Analysis** | Review of the ABU ICT Directorate's policy on student credentials and the "once-only" registration principle. |
| **Prototyping (evolving)** | The working prototype itself serves as a live specification; iterative feedback was used to refine the wallet workflow and QR ID card. |

**Justification:** Ethnography was prioritised because interviews alone revealed *what* students wanted ("one login"), but observing them revealed *why* existing systems fail (password fatigue + forgotten credentials). This is the tacit knowledge Sommerville (2016) warns is lost by interviews alone.

### 4.2 Use Case Model

**System boundary:** ABU-SSO.

**Actors:**
- **Student** (primary)
- **Staff** (primary)
- **Administrator** (secondary)
- **Third-Party Service** (machine actor)

**Primary use cases:**

| UC-ID | Use Case | Primary Actor | Description |
|-------|----------|--------------|-------------|
| UC-01 | Register Account | Student / Staff | Create a new account with email and password. |
| UC-02 | Log In | Student / Staff | Authenticate and receive a JWT. |
| UC-03 | View Profile | Student / Staff | Retrieve own profile via `/auth/me`. |
| UC-04 | View Digital ID Card | Student / Staff | Generate QR-coded ID card. |
| UC-05 | Top Up Wallet | Student / Staff | Add funds to campus wallet. |
| UC-06 | Pay from Wallet | Student / Staff | Debit wallet for library/hostel/services. |
| UC-07 | View Transaction History | Student / Staff | List all past credits and debits. |
| UC-08 | Access Third-Party Service | Student / Staff + Machine | Use JWT to log in to Portal, LMS, Library. |
| UC-09 | Administer Users | Administrator | View, activate, or deactivate users (future work). |
| UC-10 | Health Check | Monitoring System | Confirm the API is alive. |

**Diagram (PlantUML code — paste at http://plantuml.com/plantuml to render):**

```plantuml
@startuml ABU-SSO Use Case Diagram
left to right direction
skinparam packageStyle rectangle

actor Student
actor Staff
actor Admin
actor "Third-Party Service" as TPS

rectangle "ABU-SSO" {
  (UC-01 Register Account) as UC01
  (UC-02 Log In) as UC02
  (UC-03 View Profile) as UC03
  (UC-04 View ID Card) as UC04
  (UC-05 Top Up Wallet) as UC05
  (UC-06 Pay from Wallet) as UC06
  (UC-07 View Transactions) as UC07
  (UC-08 SSO to Third-Party) as UC08
  (UC-09 Administer Users) as UC09
  (UC-10 Health Check) as UC10
}

Student --> UC01
Student --> UC02
Student --> UC03
Student --> UC04
Student --> UC05
Student --> UC06
Student --> UC07
Student --> UC08

Staff --> UC01
Staff --> UC02
Staff --> UC03
Staff --> UC04
Staff --> UC05
Staff --> UC06
Staff --> UC07
Staff --> UC08

Admin --> UC09
TPS --> UC08
@enduml


## 4.3 Sequence Model — Login and Access a Protected Resource
#Scenario: A student logs in, then accesses their wallet.

@startuml Login Sequence
actor User
participant Browser
participant "Auth Router\n(/auth/login)" as AuthRouter
participant "User Service" as UserService
participant "JWT Utility" as JWTUtil
database "SQLite /\nPostgreSQL" as DB

User -> Browser: Enter email + password
Browser -> AuthRouter: POST /auth/login
AuthRouter -> UserService: authenticate_user(email, password)
UserService -> DB: SELECT * FROM users WHERE email=?
DB --> UserService: user row (password_hash)
UserService -> UserService: verify_password(bcrypt)
UserService --> AuthRouter: user (or None)
AuthRouter -> JWTUtil: create_access_token(user.id)
JWTUtil --> AuthRouter: signed JWT (15 min exp)
AuthRouter --> Browser: 200 OK {access_token}
Browser -> Browser: localStorage.setItem("abu_token", ...)

note over User, DB
  The user is now authenticated.
  All subsequent requests carry the JWT in the Authorization header.
end note

Browser -> AuthRouter: GET /wallet  (Authorization: Bearer <JWT>)
AuthRouter -> JWTUtil: decode_token(<JWT>)
JWTUtil --> AuthRouter: user_id
AuthRouter -> DB: SELECT wallet WHERE user_id=?
DB --> AuthRouter: wallet row
AuthRouter --> Browser: 200 OK {balance, ...}
@enduml

##4.4 Class / Entity Model
#The core entities of ABU-SSO (also the ERD):
#Diagram (PlantUML):

@startuml Class Diagram
class User {
  +id: str (UUID, PK)
  +email: str (unique)
  +password_hash: str
  +full_name: str
  +role: str
  +matric_no: str
  +is_active: bool
  +created_at: datetime
}

class Wallet {
  +id: str (UUID, PK)
  +user_id: str (FK → User.id, unique)
  +balance: Decimal
  +created_at: datetime
}

class Transaction {
  +id: str (UUID, PK)
  +wallet_id: str (FK → Wallet.id)
  +amount: Decimal
  +type: str (credit | debit)
  +description: str
  +created_at: datetime
}

User "1" -- "0..1" Wallet : owns
Wallet "1" -- "*" Transaction : contains
@enduml

##4.5 Functional Decomposition

ABU-SSO
├── Authentication Subsystem
│   ├── Register (FR-01, FR-02, FR-03)
│   ├── Login (FR-04, FR-05)
│   └── Identity resolution (FR-06)
├── Identity Subsystem
│   └── Digital ID Card + QR (FR-07)
├── Wallet Subsystem
│   ├── Auto-create wallet (FR-08)
│   ├── Top up (FR-09, FR-11)
│   ├── Pay (FR-10, FR-11)
│   └── History (FR-12)
├── Presentation Subsystem
│   ├── Login page
│   └── Dashboard (FR-15)
└── Platform Subsystem
    ├── Health check (FR-14)
    ├── OpenAPI docs
    └── CI / automated tests

###4.6 Evaluation Metrics and KPIs

Goal	       KPI	                     Target
Fast login	   p95 /auth/login latency	 ≤ 500 ms
Secure credentials	% of passwords hashed with bcrypt	100 %
Reliable auth	Unauthorised requests rejected	100 %
Test coverage	pytest line coverage	≥ 70 %
CI health	GitHub Actions pass rate	100 %
Demo readiness	Live demo runs without manual intervention	Yes

## 5. Software Life Cycle Considerations

### 5.1 Development Methodology

ABU-SSO was developed using an **iterative and incremental (Agile)** approach, delivered in small vertical slices:

| Increment | Delivered Feature | Commit Hash Range |
|-----------|------------------|-------------------|
| 1 | Project scaffold, Git setup | `2534a76` |
| 2 | FastAPI base + health endpoint | `b51fb5e` |
| 3 | Modular routers + config | `cbec5f3` |
| 4 | SQLAlchemy + User model | `46ffa17` |
| 5 | Password hashing + user service | `3746c31` |
| 6 | Auth endpoints + JWT | `f8b9c69` |
| 7 | Digital ID card + QR | `0af9ce2` |
| 8 | Campus wallet | `09c0e7e` |
| 9 | Web UI (login + dashboard) | `7e5ced1` |
| 10 | 53 automated tests + CI | `991a534`, `52c04f8` |

**Justification:** Agile was chosen over Waterfall because the problem statement involves real students with evolving needs (e.g., wallet integration was added after the initial auth prototype). Frequent demos to peers validated each increment before moving on.

### 5.2 Version Control

- **System:** Git with a public GitHub repository (`github.com/idrismakr-png/abu-sso`).
- **Branching:** Trunk-based development with a single `main` branch; every change is a small, atomic commit.
- **Commit convention:** Conventional Commits (`feat:`, `fix:`, `chore:`, `test:`, `ci:`).
- **Tags:** Not used in this prototype; production would use semantic versioning (`v1.0.0`).

### 5.3 Continuous Integration (CI)

Every push to `main` triggers `.github/workflows/ci.yml`, which:

1. Spins up a fresh Ubuntu runner.
2. Installs Python 3.12 and all dependencies from `requirements.txt`.
3. Runs `pytest -v` — all 53 tests must pass.
4. Reports status back to the commit (green ✅ or red ❌).

**Evidence:** The CI badge shows on the GitHub Actions page. A failing test automatically blocks merging a pull request.

### 5.4 Test Planning

See Section 7 (Testability).

---

## 6. Feasibility and Considerations

### 6.1 Technical Feasibility

| Aspect | Assessment |
|--------|------------|
| Skill availability | Python + FastAPI is documented extensively; the developer completed the project using free tutorials and library documentation. |
| Technology maturity | FastAPI, SQLAlchemy, bcrypt, and PyJWT are industry-standard, actively maintained libraries. |
| Hardware requirements | Development runs on any modern laptop with 4 GB RAM; production on Render's free tier. |
| Integration feasibility | JWT-based SSO is a widely adopted industry pattern (Google, Microsoft, ABU's own portal vendor). |

**Verdict: Technically feasible.**

### 6.2 Economic Feasibility

| Item | Cost |
|------|------|
| Developer time | 0 (academic project) |
| Development environment | 0 (uses open-source tooling) |
| Cloud hosting (Render free tier) | 0 |
| PostgreSQL (Render free tier) | 0 |
| **Total operational cost** | **₦0 for prototype** |

**Benefit:** Eliminates duplicated IT support tickets caused by password resets. The ABU ICT Directorate currently spends significant staff time on password recovery, which this system substantially reduces.

**Verdict: Economically feasible.**

### 6.3 Risk Assessment

| # | Risk | Probability | Impact | Mitigation |
|---|------|:-----------:|:------:|-----------|
| R1 | JWT secret leaked in Git history | Medium | High | Store in `.env` (gitignored); rotate on deploy; use ≥ 32-byte key |
| R2 | Weak passwords chosen by users | High | Medium | Enforce minimum length via Pydantic schema |
| R3 | SQLite concurrency limitations at scale | Medium | Medium | Migrate to PostgreSQL on deployment (URL env-var swap) |
| R4 | Time overrun due to course workload | Medium | High | Agile increments; the working prototype exists now |

### 6.4 Testability Considerations

The architecture is designed to be **testable at three levels**:

1. **Unit** — pure functions (`hash_password`, `verify_password`) tested in isolation.
2. **Service** — business logic (`create_user`, `top_up`, `pay`) tested against a temporary DB.
3. **Integration** — HTTP endpoints tested with FastAPI's `TestClient`.

The `DATABASE_URL` environment variable is overridden in tests, so **tests never touch production data**.

---

## 7. Testability

### 7.1 Testing Strategy

A **pragmatic layered approach** combining aspects of TDD and traditional testing:

- **Unit tests** for pure functions and small utilities (fast, no DB).
- **Service-level tests** for business logic, using a real (temporary) DB.
- **Integration tests** hitting the FastAPI app via HTTP.
- **Continuous Integration** running all tests on every push.

### 7.2 Test Coverage Goals

| Level | Target | Achieved |
|-------|--------|----------|
| Unit tests | 100 % of `security.py` | ✅ 7/7 |
| Service tests | 100 % of `user_service.py` + `wallet_service.py` | ✅ 25/25 |
| Integration tests | All public HTTP routes | ✅ 21/21 |
| Overall | ≥ 70 % line coverage | ✅ (see `pytest --cov`) |

### 7.3 Test Environment

- Temporary SQLite database per test session (`tempfile.NamedTemporaryFile`).
- Fixtures (`client`, `db`, `clean_tables`) provided in `tests/conftest.py`.
- Autouse fixtures reset state between tests, ensuring independence.

### 7.4 Clear Test Cases and Measurable Outcomes

Every test has:
- **Setup** (arrange)
- **Action** (act)
- **Assertion** (assert) with explicit expected values.

Example measurable outcomes:
- `test_register_returns_201_and_user` — asserts HTTP status AND every field of the response body.
- `test_wallet_pay_insufficient_funds_returns_400` — asserts HTTP status AND that the balance is unchanged.

### 7.5 Verification Against Requirements

See the **Requirements Traceability Matrix (RTM)** in `docs/RTM.md` (next document).

---

## Appendix A — Assumptions

1. All users have an `@abu.edu.ng` email address.
2. Wallet top-ups are simulated for the prototype; no real money is involved.
3. QR codes encode a minimal payload (`id`, `matric_no`, `role`), not biometric or highly sensitive data.
4. The system is deployed on a single-node server for the exam; horizontal scaling is documented but not exercised.

## Appendix B — Future Work

- Integration with the real ABU student portal and Moodle.
- OIDC (OpenID Connect) with asymmetric RS256 keys instead of shared HS256 secret.
- Role-based admin dashboard (audit logs, bulk user management).
- Native mobile app (React Native) reusing the same API.
- Offline-first QR verification for gate access.
- Password reset via email OTP.

---

*End of Software Requirements Specification (SRS).*