# Security Documentation
## ABU-SSO: Unified Single Sign-On & Digital Campus Wallet

**Course:** COEN838 — Advanced Software Engineering  
**Student:** Idris Muhammad Abubakar  
**Matric No:** P25EGCP9003  

---

## 1. Security Objectives

ABU-SSO protects three classes of assets:

| Asset | Confidentiality | Integrity | Availability |
|-------|:---------------:|:---------:|:------------:|
| User credentials (passwords) | ✅ | ✅ | ✅ |
| JWT access tokens | ✅ | ✅ | ✅ |
| Wallet balances & transactions | ✅ | ✅ | ✅ |
| Digital ID card QR payloads | ✅ | ✅ | ✅ |

The system is built on the **CIA Triad** (Confidentiality, Integrity, Availability) plus **non-repudiation** of financial transactions.

---

## 2. STRIDE Threat Model

STRIDE is applied to each major component. For each threat, the *attack scenario* and *current mitigation* are documented.

### 2.1 Authentication Component (`/auth/*`)

| Threat | Attack Scenario | Mitigation |
|--------|-----------------|-----------|
| **S**poofing | Attacker submits stolen credentials | bcrypt password verification; generic error message ("Invalid email or password") prevents user enumeration |
| **S**poofing | Attacker replays an old JWT | JWT includes `exp` (15-min expiry) — expired tokens rejected |
| **T**ampering | Attacker modifies JWT payload (e.g. change `sub`) | HS256 signature; any tampering invalidates signature → 401 |
| **R**epudiation | User denies having logged in | Every login can be logged (audit log planned for future release) |
| **I**nformation Disclosure | Passwords leaked via API | Passwords never returned; `password_hash` never serialised |
| **I**nformation Disclosure | Error messages reveal user existence | Registration returns generic "Email already registered" without confirming matching user IDs |
| **D**enial of Service | Attacker floods `/auth/login` | Rate limiting **not yet implemented** (residual risk — see §5) |
| **E**levation of Privilege | Attacker changes `role` after registration | Role is set at registration only; no endpoint allows role change by a normal user |

### 2.2 Wallet Component (`/wallet/*`)

| Threat | Attack Scenario | Mitigation |
|--------|-----------------|-----------|
| **S**poofing | Attacker calls `/wallet/topup` with another user's token | Token binds to `sub` (user id); every operation scoped to that user |
| **T**ampering | Attacker sends negative amount to gain balance | Pydantic `Field(gt=0)` rejects negative amounts with HTTP 422 |
| **T**ampering | Attacker tries to edit transaction history | `Transaction` records are append-only; no update/delete endpoint exists |
| **R**epudiation | User denies a payment | Every transaction stores `amount`, `type`, `description`, `created_at` |
| **I**nformation Disclosure | Attacker enumerates wallet IDs | Wallet is fetched via `user_id` from token — no ID enumeration possible |
| **D**enial of Service | Attacker spams top-up endpoint | Not rate-limited (residual risk) |
| **E**levation of Privilege | Attacker tries `pay` on another wallet | Not possible — wallet is always derived from `current_user` |

### 2.3 ID Card Component (`/id-card`)

| Threat | Attack Scenario | Mitigation |
|--------|-----------------|-----------|
| **S**poofing | Attacker forges a QR code | QR encodes user id and matric; verifier must validate against the IdP |
| **I**nformation Disclosure | QR photographed and decoded | QR contains only `{id, matric_no, role}` — no email, password, or wallet info |
| **T**ampering | Attacker edits QR payload | Regenerated QR must match the IdP's record |

### 2.4 Database Layer

| Threat | Attack Scenario | Mitigation |
|--------|-----------------|-----------|
| **T**ampering | SQL Injection via form fields | SQLAlchemy parameterises every query; no string concatenation |
| **I**nformation Disclosure | Attacker reads the DB file | In production, DB is PostgreSQL behind TLS; SQLite file is local-only |

---

## 3. Secure Design Principles — Applied

| Principle | Where Applied |
|-----------|--------------|
| **Least Privilege** | No user can access another user's wallet/ID card. Only the `admin` role (future) will access other users' data. |
| **Defence in Depth** | bcrypt (passwords) + JWT (sessions) + Pydantic (input validation) + SQLAlchemy (parameterised queries) + HTTPS (transport) |
| **Fail Securely** | Any auth failure returns HTTP 401. Wallet under-funding raises `ValueError` *before* the DB is touched. |
| **Never Trust Input** | Every request body is validated by Pydantic schemas *before* it reaches business logic. |
| **Separation of Secrets** | `JWT_SECRET` is loaded from `.env`, which is gitignored. The `.env.example` file contains a placeholder only. |
| **Complete Mediation** | Every protected route uses `Depends(get_current_user)` — there is no "back door". |
| **Economy of Mechanism** | Authentication logic lives in exactly one place (`app/utils/jwt.py`), reducing the attack surface. |
| **Cryptographic Hygiene** | bcrypt cost ≥ 12 by default; JWT secret ≥ 32 bytes (RFC 7518 §3.2). |
| **Least Common Mechanism** | No shared state between users; every DB read is filtered by `user_id` from the token. |

---

## 4. Authentication & Authorization Scheme

### 4.1 Authentication — JWT (HS256)

- **Token type:** JSON Web Token signed with HMAC-SHA256.
- **Payload claims:**
  - `sub` — user id (UUID)
  - `iat` — issued at (Unix epoch)
  - `exp` — expiry (iat + 900 seconds = 15 minutes)
- **Transport:** `Authorization: Bearer <token>` header.
- **Storage on client:** `localStorage["abu_token"]`.

**Why JWT and not server-side sessions?**
1. **Stateless** — the API can scale horizontally behind a load balancer.
2. **Cross-service** — third-party services (Portal, LMS) can verify tokens without a shared session store.
3. **Standard** — JWT is the industry norm for SSO; ABU's real portal could adopt it via OIDC.

**Why 15 minutes?** Short-lived tokens limit the damage from theft. A future release will add refresh tokens so users aren't forced to re-login frequently.

### 4.2 Password Storage — bcrypt

- **Algorithm:** bcrypt with auto-generated salt (default work factor = 12).
- **Why bcrypt?** It is *deliberately slow* (~100 ms per hash), resisting brute-force attacks. A SHA-256 hash, by contrast, could be computed billions of times per second on a GPU.
- **Verification:** `bcrypt.checkpw()` uses constant-time comparison to mitigate timing attacks.

### 4.3 Authorization (Current + Planned)

**Current state:** the `role` field (`student` / `staff` / `admin`) is stored but only used to display the user type. All authenticated users have identical access to their *own* resources.

**Planned RBAC:** the next release will add `require_role("admin")` middleware so admin-only endpoints (user management, audit log) reject non-admin callers with HTTP 403.

---

## 5. Security Testing Evidence

### 5.1 Static Application Security Testing (SAST) — Bandit

Command:

Command:
bandit -r app/


Result:


