# Test Results & Quality Evidence
## ABU-SSO: Unified Single Sign-On & Digital Campus Wallet

**Course:** COEN838 — Advanced Software Engineering  
**Student:** Idris Muhammad Abubakar  
**Matric No:** P25EGCP9003  
**Date:** October 2026  

---

## 1. Executive Summary

| Metric | Value |
|--------|-------|
| Total tests | **69** |
| Tests passing | **69 (100%)** |
| Line coverage | **96%** (473 statements, 19 missed) |
| SAST findings (Bandit) | **0** |
| CI status | ✅ Green |
| Test framework | pytest 9.1.1 + httpx + FastAPI TestClient |

---

## 2. Testing Strategy (Module II)

ABU-SSO uses a **three-layer testing pyramid**, complemented by static analysis and continuous integration.

| Layer | Test Count | Scope | Tooling |
|-------|:----------:|-------|---------|
| **Unit** | 7 | Pure functions (`hash_password`, `verify_password`) | pytest |
| **Service** | 29 | Business logic (`user_service`, `wallet_service`, `admin_service`) | pytest + SQLAlchemy |
| **Integration** | 33 | HTTP endpoints via FastAPI TestClient | pytest + httpx |

**Test isolation:** every test runs against a temporary SQLite database created by `tests/conftest.py`. The production `DATABASE_URL` is overridden during the test session, and tables are wiped between tests — so tests are independent and never touch real data.

**Red–Green–Refactor influence:** although the full TDD cycle was not followed for every line, tests were written for each business rule *before* the UI was built, and existing tests caught two bugs during development.

---

## 3. Coverage Report
Name Stmts Miss Cover Missing

app_init_.py 0 0 100%
app\config.py 11 0 100%
app\database.py 19 6 68% 14, 16, 39-43
app\main.py 19 0 100%
app\models_init_.py 3 0 100%
app\models\user.py 18 1 94% 26
app\models\wallet.py 27 2 93% 30, 46
app\routers_init_.py 0 0 100%
app\routers\admin.py 33 2 94% 51-52
app\routers\auth.py 24 0 100%
app\routers\health.py 5 0 100%
app\routers\id_card.py 11 0 100%
app\routers\pages.py 13 2 85% 15, 20, 25
app\routers\wallet.py 32 2 94% 55-56
app\schemas_init_.py 0 0 100%
app\schemas\admin.py 29 0 100%
app\schemas\id_card.py 8 0 100%
app\schemas\user.py 24 0 100%
app\schemas\wallet.py 22 0 100%
app\services_init_.py 0 0 100%
app\services\admin_service.py 38 0 100%
app\services\qr_service.py 16 0 100%
app\services\user_service.py 26 0 100%
app\services\wallet_service.py 37 0 100%
app\utils_init_.py 0 0 100%
app\utils\jwt.py 31 1 97% 63
app\utils\rbac.py 9 0 100%
app\utils\security.py 14 2 86% 22-23

TOTAL 473 19 96%

**Target:** ≥ 70% line coverage (rubric requirement).  
**Achieved:** **96%** — exceeds target by 26 percentage points.

**Why some lines are uncovered:** the remaining uncovered lines are defensive exception paths (e.g., SQLite file cleanup on session teardown) that are difficult to exercise without environment manipulation. This is acceptable residual coverage.

---

## 4. Test Inventory

### 4.1 Unit Tests — `tests/test_security.py` (7 tests)

| Test | What it verifies |
|------|------------------|
| `test_hash_password_returns_string` | Returns a non-empty string |
| `test_hash_password_is_not_plaintext` | Password is never stored plaintext |
| `test_hash_password_same_input_different_output` | Salt produces different hashes each time |
| `test_verify_password_correct` | Correct password verifies successfully |
| `test_verify_password_wrong` | Wrong password is rejected |
| `test_verify_password_empty_password` | Empty input is rejected |
| `test_hash_password_empty_raises` | Empty input raises `ValueError` |

### 4.2 Service Tests

**`tests/test_user_service.py` (13 tests)** — CRUD operations, email normalisation, duplicate detection, password hashing, lookups by email/id/matric, authentication success/failure/inactive-user rejection.

**`tests/test_wallet_service.py` (12 tests)** — Wallet auto-creation, idempotency, top-up, pay, insufficient funds, zero/negative amounts, transaction list ordering.

**`tests/test_admin.py` (20 tests)** — RBAC enforcement, user listing, role changes, activate/deactivate, deactivated user login rejection, admin top-up, stats aggregation, error handling.

### 4.3 Integration Tests — `tests/test_api_integration.py` (21 tests)

Full HTTP flows: register, duplicate rejection, invalid input, login, missing/bad token, `/auth/me`, ID card generation, wallet top-up/pay, transaction listing, health check, root endpoint.

---

## 5. Static Analysis (SAST)

**Tool:** Bandit 1.9.4  
**Command:** `bandit -r app/`  
**Result:**


Test results:
No issues identified.

Code scanned:
Total lines of code: 525
Total lines skipped (#nosec): 0

Total issues (by severity):
High: 0
Medium: 0
Low: 0


**Interpretation:** no common Python vulnerabilities (hardcoded credentials, unsafe `eval`, weak cryptography, shell injection, etc.) were detected.

---

## 6. Continuous Integration

**Workflow:** `.github/workflows/ci.yml`  
**Trigger:** every push to `main` and every pull request  
**Runner:** Ubuntu latest, Python 3.12  
**Steps:**
1. Checkout code
2. Set up Python 3.12
3. Install dependencies from `requirements.txt`
4. Run `pytest -v` — all tests must pass

**Status:** ✅ Green (34-second runtime)

The CI badge in the README shows the current status. A failing test blocks merge.

---

## 7. How to Reproduce These Results

```bash
# Activate environment
conda activate abu-sso

# Run all tests
pytest -v

# Run with coverage
pytest --cov=app --cov-report=term-missing

# Run with HTML coverage report
pytest --cov=app --cov-report=html
# Open htmlcov/index.html in a browser

# Run SAST
pip install bandit
bandit -r app/


**Interpretation:** no common Python vulnerabilities (hardcoded credentials, unsafe `eval`, weak cryptography, shell injection, etc.) were detected.

---

## 6. Continuous Integration

**Workflow:** `.github/workflows/ci.yml`  
**Trigger:** every push to `main` and every pull request  
**Runner:** Ubuntu latest, Python 3.12  
**Steps:**
1. Checkout code
2. Set up Python 3.12
3. Install dependencies from `requirements.txt`
4. Run `pytest -v` — all tests must pass

**Status:** ✅ Green (34-second runtime)

The CI badge in the README shows the current status. A failing test blocks merge.

---

## 7. How to Reproduce These Results

```bash
# Activate environment
conda activate abu-sso

# Run all tests
pytest -v

# Run with coverage
pytest --cov=app --cov-report=term-missing

# Run with HTML coverage report
pytest --cov=app --cov-report=html
# Open htmlcov/index.html in a browser

# Run SAST
pip install bandit
bandit -r app/
Expected outcome: 69 tests pass, coverage ≥ 90%, Bandit reports 0 findings.

8. Traceability
Every Functional Requirement (FR) is traced to at least one test. See docs/RTM.md for the full Requirements Traceability Matrix.

Coverage summary:

Category	FRs covered	%
Authentication & registration	FR-01, FR-02, FR-03, FR-04, FR-05, FR-06	100%
ID card	FR-07	100%
Wallet	FR-08, FR-09, FR-10, FR-11, FR-12	100%
Roles & RBAC	FR-13	100%
Platform (health, UI)	FR-14 (automated), FR-15 (manual)	50% automated, 100% verified

9. Quality Metrics — Dashboard
Metric	Value	Target	Status
Test pass rate	100%	100%	✅
Line coverage	96%	≥ 70%	✅
SAST findings	0	0	✅
CI pass rate	100%	100%	✅
Tests per requirement	≥ 1	≥ 1	✅


