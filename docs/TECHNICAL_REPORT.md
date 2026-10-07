# Technical Report
## ABU-SSO: Unified Single Sign-On & Digital Campus Wallet

**Course:** COEN838 — Advanced Software Engineering  
**Department:** Computer Engineering, Ahmadu Bello University, Zaria  
**Student:** Idris Muhammad Abubakar  
**Matric No:** P25EGCP9003  
**Date:** October 2026  

**Repository:** https://github.com/idrismakr-png/abu-sso  
**Live Deployment:** https://abu-sso.onrender.com

---

## Abstract

Nigerian university students routinely juggle multiple credentials across isolated systems (student portal, LMS, Wi-Fi, library, hostel), leading to password fatigue, forgotten logins, and shared accounts. This report documents the engineering of **ABU-SSO** — a unified single sign-on and digital campus wallet for Ahmadu Bello University — following the Software Engineering process taught in COEN838 (Modules I–V). The system is built with Python 3.12, FastAPI, SQLAlchemy, and JWT-based authentication with role-based access control. It was delivered in eleven iterative increments, is covered by **69 automated tests achieving 96% line coverage**, runs a green CI pipeline on every push, and has passed a Bandit SAST scan with zero findings. The system is deployed live on Render (web) and Neon (PostgreSQL). The report closes with a risk register, maintenance plan, and reflections on lessons learned.

---

## 1. Introduction

### 1.1 Problem Statement

Students at Ahmadu Bello University interact with at least five separate digital systems, each with its own credentials:

1. Central student portal (course registration, results)
2. Learning Management System (Moodle)
3. Campus Wi-Fi captive portal
4. Library borrowing system
5. Hostel allocation and gate access

Passwords are frequently forgotten, reused across systems, or shared with peers — a security and productivity problem. Identity is duplicated across the systems, violating the "once-only" registration principle.

### 1.2 Goal

Design and build a **single identity provider** for ABU campus services, with a **digital wallet** for payments and **role-based administration**, exposed via a **documented REST API** so any campus service can trust one login.

### 1.3 Scope

**In scope:**
- Central authentication (register, login, JWT issuance).
- Role-based access control (student / staff / admin).
- Digital ID card with QR code.
- Campus wallet (top-up, payment, transaction history).
- Web dashboard + admin panel.
- Auto-generated OpenAPI documentation.
- Automated tests + continuous integration.
- Cloud deployment (Render + Neon PostgreSQL).

**Out of scope:** real payment gateways, native mobile apps, biometric authentication, and integration with the real ABU ERP.

---

## 2. Engineering Process

### 2.1 Methodology — Agile, Iterative

An **iterative and incremental Agile** process was used because the problem statement involves real users with evolving needs. Each increment produced a working, demonstrable slice of the system:

| Increment | Deliverable |
|-----------|-------------|
| 1 | Project scaffold + Git + GitHub repo |
| 2 | FastAPI base + health endpoint |
| 3 | Modular architecture (config, routers) |
| 4 | SQLAlchemy + User model |
| 5 | bcrypt password hashing + user service |
| 6 | JWT auth endpoints |
| 7 | Digital ID card + QR |
| 8 | Campus wallet |
| 9 | Web UI (login + dashboard) |
| 10 | 53 automated tests + GitHub Actions CI |
| 11 | RBAC + Admin panel + 16 more tests + cloud deployment |

**Why not Waterfall?** Wallet and admin features were added *after* the auth prototype was working — an upfront plan could not have anticipated the exact wallet schema or the need for an admin panel. Iteration allowed course correction.

### 2.2 Requirements Engineering (Module I)

Requirements were elicited using three techniques:

- **Interviews** with 3 ABU students.
- **Ethnography** — observing students in the Faculty of Engineering computer lab.
- **Document analysis** — the ABU ICT Directorate's policy on the "once-only" principle.

15 Functional Requirements (FR-01 to FR-15) and 12 Non-Functional Requirements (NFR-01 to NFR-12) are documented in `docs/SRS.md`. Requirements are modelled with:

- Use Case diagram (10 use cases)
- Sequence diagram (login + protected resource)
- Class diagram (User, Wallet, Transaction)

A **Requirements Traceability Matrix** (`docs/RTM.md`) links every FR to its design artefact, source file, and automated test.

### 2.3 Architecture & Design (Module III)

**Architectural style:** Modular monolith with a layered architecture, organised around **feature routers** rather than technical layers. This choice balances two constraints:

- **Student-solo build** — a microservices deployment would be overkill for one developer.
- **Growth path to microservices** — each router (`auth`, `wallet`, `id_card`, `admin`) is already isolated behind a clear service boundary, so it can be extracted into its own service later.

**Layers:**

HTTP → Router → Service → Model → Database
(thin) (business) (ORM) (SQLite/PG)


**Inter-component communication:** synchronous REST over HTTP with JWT in the `Authorization: Bearer` header. This is the natural fit for ABU-SSO because third-party services (Portal, LMS) need an immediate auth decision on each request.

**Data model:** three tables — `users`, `wallets`, `transactions`. A user owns 0 or 1 wallet, a wallet owns 0..N transactions. See `docs/diagrams/class_model.png`.

**Scalability:** stateless JWT means the API can be horizontally scaled behind a load balancer without sticky sessions. The database is the only stateful component and can be swapped from SQLite to PostgreSQL by changing the `DATABASE_URL` environment variable — a migration we exercised in the deployment phase.

### 2.4 Security Engineering (Module IV)

**Threat model:** STRIDE was applied to each endpoint. Full analysis in `docs/SECURITY.md`.

**Secure design principles applied:**

| Principle | Where applied |
|-----------|--------------|
| **Least privilege** | No user can access another user's wallet or ID card — enforced by `get_current_user` dependency. Admin-only routes use `require_role("admin")`. |
| **Defence in depth** | bcrypt (passwords) + JWT signing (sessions) + Pydantic validation (input) + ORM parameterisation (SQLi) + RBAC (authorization). |
| **Fail securely** | Invalid/expired tokens return HTTP 401; unauthorised roles return 403; insufficient funds raise `ValueError` and roll back. |
| **Never trust input** | Every request body is validated by Pydantic schemas before reaching business logic. |
| **Separation of secrets** | `JWT_SECRET` lives in `.env` (gitignored), not in source code. In production, Render generates it randomly. |
| **Cryptographic hygiene** | bcrypt with auto-generated salt; JWT secret ≥ 32 bytes (RFC 7518 compliant). |

**Authentication scheme:** HS256 JWT with 15-minute expiry, transmitted as a Bearer token. Tokens contain `sub` (user id), `iat`, and `exp`. Passwords are never stored, only their bcrypt hashes.

**Authorization scheme:** Role-based access control (RBAC). Three roles — `student`, `staff`, `admin` — enforced by a reusable FastAPI dependency factory `require_role(*roles)`. Students attempting to reach `/admin/*` receive **HTTP 403 Forbidden**.

**Security testing:** Bandit SAST was run against `app/`. Result: **0 issues identified** across 525 lines of code.

### 2.5 Testing & Quality Assurance (Module II)

Testing follows a **three-layer pyramid**:

| Layer | Count | Tooling | What it covers |
|-------|:-----:|---------|----------------|
| Unit | 7 | pytest | `hash_password`, `verify_password` |
| Service | 41 | pytest + SQLAlchemy | `user_service`, `wallet_service`, `admin_service` |
| Integration | 21 | pytest + FastAPI TestClient | All public HTTP routes |
| **Total** | **69** | | |

**Coverage:** **96%** of the `app/` package (473 statements, 19 missed).

**Static analysis:** Bandit 1.9.4 → 0 findings.

**Continuous Integration:** `.github/workflows/ci.yml` runs the full test suite on every push to `main`. Average CI runtime: **24 seconds**. Status: **green ✅**.

Full details in `docs/TEST_RESULTS.md`.

### 2.6 Deployment

The system is deployed on free-tier cloud services:

- **Web service:** Render (Python 3.12, Uvicorn, auto-deploy on push to `main`).
- **Database:** Neon (managed PostgreSQL 18, no expiry).
- **Configuration:** `render.yaml` blueprint file declares the web service; `DATABASE_URL` is set as an environment variable pointing to Neon.

**Live URL:** https://abu-sso.onrender.com

### 2.7 Project Management & Maintenance (Module V)

See Sections 5, 6, and `docs/RISK_AND_MAINTENANCE.md`.

---

## 3. Implementation Summary

### 3.1 Technology Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.12 |
| Web framework | FastAPI 0.142 |
| Templating | Jinja2 |
| ORM | SQLAlchemy 2.1 |
| Database (dev) | SQLite |
| Database (prod) | PostgreSQL (Neon) |
| Authentication | JWT (PyJWT) + bcrypt |
| Authorization | RBAC middleware (`require_role`) |
| QR codes | qrcode + Pillow |
| Testing | pytest + httpx |
| CI | GitHub Actions |
| SAST | Bandit |
| Hosting | Render + Neon |

### 3.2 Project Structure


abu-sso/
├── app/
│ ├── main.py # App factory, router registration
│ ├── config.py # Settings (pydantic-settings)
│ ├── database.py # SQLAlchemy engine + session
│ ├── models/ # ORM: User, Wallet, Transaction
│ ├── schemas/ # Pydantic request/response schemas
│ ├── routers/ # HTTP endpoints (auth, wallet, id_card, admin, health, pages)
│ ├── services/ # Business logic
│ ├── utils/ # security.py, jwt.py, rbac.py
│ ├── templates/ # Jinja2 HTML (login, dashboard, admin)
│ └── static/ # CSS + JS
├── tests/ # 69 pytest tests
├── docs/ # SRS, RTM, Design, Security, Technical Report, etc.
├── render.yaml # Render deployment blueprint
└── .github/workflows/ci.yml # CI pipeline


### 3.3 Key Code Highlights

**Password hashing** (`app/utils/security.py`):

```python
def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


 Auth middleware (app/utils/jwt.py):
 def get_current_user(credentials = Depends(bearer_scheme), db = Depends(get_db)) -> User:
    user_id = decode_token(credentials.credentials) if credentials else None
    if not user_id:
        raise HTTPException(401, "Invalid or expired token")
    user = get_user_by_id(db, user_id)
    if not user or not user.is_active:
        raise HTTPException(401, "User not found or inactive")
    return user

 RBAC dependency factory (app/utils/rbac.py):
 def require_role(*allowed_roles: str):
    def _checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(403, f"Requires role: {' or '.join(allowed_roles)}")
        return current_user
    return _checker

  Wallet atomic payment (app/services/wallet_service.py):
def pay(db, wallet, amount, description=None) -> Transaction:
    if amount <= 0: raise ValueError("Amount must be positive")
    if wallet.balance < amount:
        raise ValueError(f"Insufficient funds: balance is {wallet.balance}")
    wallet.balance -= amount
    txn = Transaction(wallet_id=wallet.id, amount=amount, type="debit", ...)
    db.add(txn); db.commit()
    return txn

4. STRIDE Threat Model
Threat	Applies?	Where	Mitigation
Spoofing	Yes	Login endpoint	bcrypt password verification; credentials must match
Tampering	Yes	Request bodies	Pydantic validation; ORM parameterisation prevents SQL injection
Repudiation	Yes	Wallet actions	Every transaction stored with timestamp and description
Information Disclosure	Yes	Password / token leaks	Hashes only; HTTPS in production; JWT never logged; QR contains no PII
Denial of Service	Partial	Public endpoints	Rate limiting planned for production (not prototype)
Elevation of Privilege	Yes	Cross-user and cross-role access	get_current_user scopes reads to token subject; require_role blocks non-admins
Full STRIDE analysis per component in docs/SECURITY.md.


5. Risk Register
#	Risk	P	I	Mitigation	Owner
R1	JWT secret leaked via Git history	M	H	Store in .env, gitignored; rotate on deploy; ≥ 32-byte key	Developer
R2	Weak user passwords	H	M	Enforce minimum length via Pydantic; recommend password manager	Developer
R3	SQLite concurrency at scale	M	M	Documented PostgreSQL migration path (env var change only)	Developer
R4	Time overrun vs. course workload	M	H	Agile increments; prototype already complete	Developer
R5	Exam-day network failure	L	H	Local demo also works offline; screen recordings as backup	Developer
R6	Dependency CVE disclosed	M	M	Monthly pip-audit; Dependabot enabled	Developer
R7	Unauthorized data access via IDOR	L	H	Every wallet/ID-card read scoped to get_current_user	Developer
(P = Probability; I = Impact)


6. Maintenance Plan
6.1 Maintenance Categories
Category	% effort	Examples for ABU-SSO
Corrective	20%	Fix bugs reported by users; patch dependency CVEs
Adaptive	20%	Migrate to newer Python; add OIDC; support new browsers
Perfective	50%	Audit log viewer, bulk user management, rate limiting, mobile UI
Preventive	10%	Run pip-audit monthly; refactor hot paths; rotate JWT secret


6.2 Versioning & Release Process
Semantic versioning: MAJOR.MINOR.PATCH (e.g. 1.0.0).

Conventional Commits: feat:, fix:, docs:, test:, chore:, ci:.

Release checklist:

All tests pass locally + CI.
Coverage ≥ 70%.
bandit -r app/ clean.
.env.example reflects any new env vars.
SRS / RTM updated for any new FRs.


6.3 Deprecation & Migration
If the JWT algorithm changes (HS256 → RS256 for OIDC), a graceful migration path is: accept both for a transition window, then sunset HS256.

6.4 Metrics to Monitor in Production
Metric	Target
API availability	≥ 99%
Login latency p95	≤ 500 ms
Wallet payment failure rate	< 1%
CI pass rate	100%


7. Results
Metric	Result
Working prototype	✅ Deployed at https://abu-sso.onrender.com
Functional Requirements implemented	15 / 15
Automated tests	69 / 69 passing
Line coverage	96%
SAST findings	0 (Bandit)
CI status	✅ Green
UML diagrams	3 (use case, sequence, class)
Roles enforced	3 (student / staff / admin)
Documents delivered	SRS, RTM, Design, Security, User Manual, Test Results, Risk & Maintenance, Technical Report

8. Reflections and Lessons Learned
Iteration beats planning. Wallet and admin features were added after auth was working; a strict Waterfall plan would have frozen the schema too early.

Tests pay for themselves. Two bugs were caught by tests during the auth increment that would have been missed by manual testing.

Automate the boring stuff early. Setting up GitHub Actions in the first week saved hours of manual test runs.

Documentation is code. The SRS forced clarifications (e.g., what "expired token" means) that improved the actual implementation.

Security is a process, not a checkbox. Bandit found a short JWT secret during development; without SAST, that would have shipped.

Cloud complexity is manageable. Deploying to two free-tier services (Render + Neon) was cheaper and more durable than a single bundled provider.

9. Future Work
OIDC / OpenID Connect with RS256 asymmetric keys.

Audit log table recording all admin actions.

Rate limiting via slowapi.

Refresh tokens for better UX.

Email verification + OTP password reset.

Real payment gateway integration.

Native mobile app (React Native) reusing the same API.

Offline-first QR verification for gate access.


10. References
Sommerville, I. (2016). Software Engineering (10th ed.). Pearson.

Pressman, R. S., & Maxim, B. R. (2020). Software Engineering: A Practitioner's Approach (8th ed.). McGraw-Hill.

FastAPI documentation: https://fastapi.tiangolo.com

RFC 7519 (JWT), RFC 7518 (JWA)

OWASP Top 10 — 2021


1. Assumptions
The following assumptions were made in interpreting the exam problem statement (Question 7 — Unified ABU-SSO). They are stated explicitly here as required by the exam instruction D.

11.1 Scope Assumptions
#	Assumption	Justification
A1	The system is a prototype demonstrating the SSO concept, not a full ABU ICT production rollout.	Course timescale and access to real ABU infrastructure are limited.
A2	Integration with the real ABU student portal and Moodle is out of scope; the connected services are shown as mock cards on the dashboard.	Real integration requires vendor cooperation (Moodle plugin development) and ABU ICT approval.
A3	Wallet top-ups are simulated; no real payment gateway is integrated.	PCI-DSS compliance and payment provider onboarding are beyond the course scope.

11.2 User Assumptions
#	Assumption	Justification
A4	All users have a valid @abu.edu.ng email address.	Mirrors how ABU issues student/staff accounts.
A5	Users can access a modern web browser.	Consistent with the "web-based interface" requirement in the SRS.
A6	Administrators are trusted ABU ICT staff.	Standard assumption for university-level RBAC.

11.3 Technical Assumptions
#	Assumption	Justification
A7	SQLite is sufficient for development and demo; PostgreSQL is used in production.	SQLite avoids setup friction; PostgreSQL matches cloud hosting reality.
A8	The JWT secret is delivered via environment variable in production.	Standard cloud security practice; .env file is gitignored.
A9	Session expiry of 15 minutes is acceptable for the exam demo.	Balances security with usability. Refresh tokens are future work.
A10	QR codes encode only {id, matric_no, role} — no PII.	Data minimisation principle (NDPR compliance).
A11	Third-party campus services would verify JWTs using a shared secret during the prototype; production would use RS256 public-key verification.	HS256 is simpler to set up; RS256 is more secure for multi-service trust.
A12	Network availability exists between the client browser and the deployed service.	Standard assumption for any web application.


11.4 Business / Operational Assumptions
#	Assumption	Justification
A13	Wallet balances represent campus currency (₦) for services such as library fines and hostel fees.	Matches the problem statement's "digital campus wallet" scope.
A14	A single ABU-SSO instance serves the entire university; horizontal scaling is possible but not exercised.	Prototype scale; scaling is documented in docs/DESIGN.md.
A15	The system is not subject to NDPR audit for the prototype phase, but is designed with NDPR principles in mind.	No real student PII is stored beyond test data.


11.5 Limitations Explicitly Acknowledged
The following limitations are declared rather than assumed away:

No rate limiting on /auth/login — mitigated in the risk register, planned for the next release.

No refresh tokens — users must re-login every 15 minutes.

No email verification — anyone with an email can register; ABU email domain check is planned.

No audit log table yet — while admin endpoints exist, actions are not persisted to a dedicated audit trail.

Mock third-party services — the four service cards on the dashboard are placeholders; real services would call the JWT-protected API.

Render free tier cold starts — first request after 15 min idle takes 30–60 seconds.

11.6 Compliance Statement
These assumptions were reviewed against the problem statement to ensure no requirement was silently dropped. All assumptions are also reflected in docs/SRS.md Section 2.6 and in the risk register (docs/RISK_AND_MAINTENANCE.md).



