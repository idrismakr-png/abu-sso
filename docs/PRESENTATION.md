# Presentation Guide
## ABU-SSO: Unified Single Sign-On & Digital Campus Wallet

**Course:** COEN838 — Advanced Software Engineering  
**Student:** Idris Muhammad Abubakar  
**Matric No:** P25EGCP9003  
**Presentation duration:** ~12–15 minutes + Q&A

---

## Part 1 — Slide Deck Outline (20 slides)

### Slide 1 — Title
- **ABU-SSO**: Unified Single Sign-On & Digital Campus Wallet
- Idris Muhammad Abubakar | P25EGCP9003
- COEN838 — Advanced Software Engineering
- GitHub: `github.com/idrismakr-png/abu-sso`

### Slide 2 — The Problem
- Students juggle **5 credentials** (Portal, LMS, Wi-Fi, Library, Hostel)
- Passwords forgotten, reused, or shared
- IT support flooded with reset requests
- **Nigeria-specific:** fragmented identity = security & productivity loss

### Slide 3 — The Goal
- One login → all campus services
- Digital ID card with QR
- Wallet for cashless campus payments
- Open API for any ABU service

### Slide 4 — Scope
**In scope:** auth, JWT, wallet, ID card, dashboard, OpenAPI, tests, CI  
**Out of scope:** real ERP integration, mobile apps, biometrics, real payments

### Slide 5 — Requirements Engineering (Module I)
- 15 Functional Requirements (FR-01 – FR-15)
- 12 Non-Functional Requirements (NFR-01 – NFR-12)
- Elicitation: interviews + ethnography + document analysis
- UML: Use Case, Sequence, Class
- **RTM** links every FR → design → code → test

### Slide 6 — Architecture (Module III)
- **Modular monolith**, layered
- Feature routers: `auth`, `wallet`, `id_card`, `health`, `pages`
- HTTP → Router → Service → Model → DB
- Justification: single developer, clear growth path to microservices

### Slide 7 — Data Model
- 3 tables: `users`, `wallets`, `transactions`
- UUID primary keys (works on SQLite + PostgreSQL)
- `Numeric(10,2)` for money (no float errors)
- Cascade delete (wallet → transactions)

### Slide 8 — Security (Module IV)
- **STRIDE** threat model applied
- bcrypt password hashing (cost ≥ 12)
- JWT with 15-min expiry, HS256, ≥32-byte secret
- Least privilege, defence in depth, fail securely
- **Bandit SAST: 0 findings** across 525 lines

### Slide 9 — Authentication Flow
- Register → bcrypt hash → DB
- Login → verify → JWT issued
- Protected request → Bearer token → `get_current_user` dependency
- Stateless → horizontally scalable

### Slide 10 — Testing (Module II)
- **53 automated tests** (7 unit + 25 service + 21 integration)
- **96% line coverage**
- pytest + httpx + FastAPI TestClient
- Fixtures give each test a clean temp DB

### Slide 11 — Continuous Integration
- GitHub Actions on every push to `main`
- Runs full suite in ~34 seconds
- Fails fast — broken code cannot merge

### Slide 12 — Live Demo Preview
Screenshot flow:
1. Login page
2. Dashboard
3. QR ID card
4. Wallet balance + transactions
5. Swagger UI

### Slide 13 — Implementation Stats
| Metric | Value |
|--------|-------|
| Lines of Python | ~900 |
| Endpoints | 12 |
| Test coverage | 96% |
| SAST findings | 0 |
| CI status | ✅ green |
| Increments | 10 |

### Slide 14 — Risk Register (Module V)
- R1 JWT secret leak (RE 2.5) → `.env` + gitignore + rotate
- R2 Weak passwords (RE 2.4) → Pydantic min-length
- R4 Deadline overrun (RE 2.0) → Agile increments
- R6 Dependency CVE (RE 2.0) → `pip-audit` planned

### Slide 15 — Maintenance Plan (Module V)
- Corrective 20% | Adaptive 20% | Perfective 50% | Preventive 10%
- Semantic versioning + Conventional Commits
- Quality gates: 53 tests + 70% coverage + Bandit clean
- Decommission plan documented

### Slide 16 — Documentation Delivered
- SRS (Section 1–7 + appendices)
- RTM (bidirectional traceability)
- Design Document
- Security Document
- Technical Report
- User Manual
- Risk & Maintenance Plan

### Slide 17 — Lessons Learned
- Iteration beats planning
- Tests caught 2 real bugs
- Docs forced clarity
- Security is a process

### Slide 18 — Future Work
- OIDC/RS256 asymmetric keys
- Admin dashboard + audit log
- Rate limiting (slowapi)
- Native mobile app
- Real payment gateway

### Slide 19 — Conclusion
- Delivered a working, tested, documented SSO system
- 15/15 FRs implemented
- 96% coverage, 0 SAST findings
- Production-ready architecture

### Slide 20 — Thank You & Questions
- Repo: `github.com/idrismakr-png/abu-sso`
- Docs: `docs/`
- Live demo URL: (localhost / Render)

---

## Part 2 — Live Demo Script (~4 minutes)

**Setup before the session:**
1. Ensure `conda activate abu-sso` is active.
2. Run `uvicorn app.main:app --reload` — confirm "Application startup complete".
3. Open two browser tabs: `http://127.0.0.1:8000/login` and `http://127.0.0.1:8000/docs`.
4. Optionally have a **backup screen recording** in case of network issues.

### Demo Flow

| Step | Action | Talking Point |
|------|--------|---------------|
| 1 | Show login page | "This is the single entry point for all ABU services." |
| 2 | Enter `idris@abu.edu.ng` / `secret123` | "Credentials verified via bcrypt." |
| 3 | Show dashboard loads | "One login gave us access to everything." |
| 4 | Point at balance ₦4750 | "Wallet balance is live from the DB." |
| 5 | Point at transaction list | "Every credit/debit is timestamped — non-repudiable." |
| 6 | Point at QR code | "This card works at library and hostel gates." |
| 7 | Click **Log out** | "Session cleared from the browser." |
| 8 | Paste dashboard URL again | "Redirected to login — auth guard works." |
| 9 | Open Swagger `/docs` | "Auto-generated OpenAPI — any service can integrate." |
| 10 | Run `POST /auth/login` in Swagger | "Same token, machine-consumable." |
| 11 | Show GitHub Actions page | "Every push runs 53 tests automatically." |
| 12 | Show coverage report | "96% line coverage." |

**Demo tips:**
- Have a printed cheat sheet of demo credentials.
- Speak slowly; don't rush.
- If a step fails: "Let me show you the recorded version" → play backup recording.

---

## Part 3 — Defence Q&A (15 likely questions)

### Q1. Why FastAPI over Flask or Django?
**A.** FastAPI gives async-native performance, automatic OpenAPI/Swagger documentation, and type-driven validation via Pydantic. Django is heavyweight for a small SSO API; Flask lacks native async and auto-docs. FastAPI also aligns with modern industry practice.

### Q2. Why a modular monolith rather than microservices?
**A.** The project is built by one developer within a course timeframe. Microservices add deployment, orchestration, and distributed-transaction overhead. However, the routers are already drawn as service boundaries — any one can be extracted into a microservice later without rewriting business logic.

### Q3. Why JWT instead of server-side sessions?
**A.** JWT is stateless — the API can be horizontally scaled without a shared session store, and third-party services can verify tokens locally. Sessions require sticky load balancing or Redis. JWT is also the industry standard for SSO.

### Q4. Why bcrypt? Couldn't you use SHA-256?
**A.** SHA-256 is designed to be *fast* — billions of guesses per second on a GPU. bcrypt is deliberately *slow* (~100 ms per hash) and salt-aware, defeating rainbow tables and brute-force. It is the OWASP-recommended algorithm for password storage.

### Q5. How do you handle token expiry?
**A.** JWTs have a 15-minute `exp`. When expired, `/auth/me` returns 401 and the dashboard redirects to `/login`. A future release will add refresh tokens so users aren't forced to re-login frequently.

### Q6. What did Bandit find?
**A.** Zero findings across 525 lines. Bandit is a static analysis tool that detects hardcoded secrets, weak cryptography, use of `eval`, and shell injection. The clean result is evidence of secure coding.

### Q7. How did you achieve 96% coverage?
**A.** Three test layers: 7 unit tests for hashing, 25 service tests for business logic, and 21 integration tests through the FastAPI TestClient. Fixtures give each test a fresh temporary SQLite DB, so state never leaks between tests.

### Q8. What is your STRIDE threat model?
**A.** Spoofing (stolen creds) → bcrypt + generic errors; Tampering (SQLi, JWT modification) → ORM + HMAC signature; Repudiation → timestamped transactions; Info Disclosure → no password in responses; DoS → rate limiting planned; Elevation → `get_current_user` scoping.

### Q9. How is your architecture scalable?
**A.** Stateless JWT allows horizontal scale-out behind a load balancer. The DB is the only stateful piece and can switch from SQLite to PostgreSQL by changing `DATABASE_URL`. SQLAlchemy abstracts the DB engine.

### Q10. What would you do differently if you started again?
**A.** Introduce pytest from the first commit (TDD); add rate limiting early; define the admin role before building the UI so RBAC is baked in; set up CI from day one rather than after tests existed.

### Q11. How do you prevent SQL injection?
**A.** Every query goes through SQLAlchemy's parameterisation — no f-strings or string concatenation in queries. This is enforced by the ORM pattern.

### Q12. How do you prevent Cross-Site Scripting (XSS)?
**A.** All API responses are JSON (no HTML). The Jinja2 templates auto-escape variables by default. Since we don't render user content with `|safe`, XSS is mitigated.

### Q13. What is the risk register about?
**A.** Seven risks are documented with probability, impact, exposure (RE = P × I), and mitigation. The top two: R1 (JWT secret leak) and R2 (weak user passwords). Both are actively managed.

### Q14. What is your maintenance plan?
**A.** 20% corrective, 20% adaptive, 50% perfective, 10% preventive. Quality gates before every release: 53 tests pass, coverage ≥70%, Bandit clean. Semantic versioning + Conventional Commits.

### Q15. What's next after the prototype?
**A.** (1) OIDC/RS256 for real ABU ICT integration, (2) admin dashboard with audit log, (3) rate limiting via slowapi, (4) mobile app, (5) real payment gateway.

---

## Part 4 — Presentation Day Checklist

**Night before:**
- [ ] Charge laptop; bring charger
- [ ] Backup: USB with source code + zip of repo
- [ ] Backup: screen recording of the demo (MP4)
- [ ] Print: cheat sheet of demo credentials
- [ ] Print: 1-page summary of rubric coverage

**Morning of:**
- [ ] `conda activate abu-sso`
- [ ] `uvicorn app.main:app --reload`
- [ ] Verify `/login`, `/dashboard`, `/docs` all load
- [ ] Clear browser cache
- [ ] Close all extra apps (Slack, WhatsApp) — no notification popups

**During presentation:**
- [ ] Speak slowly; pause between slides
- [ ] If demo fails → switch to recording without apology
- [ ] Reference concrete artifacts: SRS, RTM, test count, coverage, Bandit output

---

*End of Presentation Guide.*