# Requirements Traceability Matrix (RTM)
## ABU-SSO: Central Identity Provider, OIDC Federation and Digital Campus Services

**Purpose:** Trace functional and non-functional requirements to the design, implementation and available verification evidence. This RTM covers both the original ABU-SSO campus platform and the OIDC federation extension.

**Legend:** UC = use case; SQ = sequence; CL = class/data model. Test references identify existing automated tests where their names have been verified. Where a requirement has no individually identified test reference in this matrix, it must not be interpreted as independently verified merely because the full suite passes.

---

## 1. Existing Campus Platform — Functional Requirements

| Req ID | Requirement | Design artefact | Implementation | Verification reference |
|---|---|---|---|---|
| FR-01 | Bootstrap-only registration: first account becomes administrator | UC-01, SQ-Login | `app/routers/auth.py`, `app/services/user_service.py`, `app/schemas/user.py` | `test_api_integration.py::test_register_returns_201_and_user` |
| FR-02 | Reject duplicate email or matric number | UC-01 | `app/services/user_service.py` | `test_api_integration.py::test_register_duplicate_email_returns_400`; `test_user_service.py::test_create_user_duplicate_email_raises` |
| FR-03 | Hash passwords with bcrypt | CL-User | `app/utils/security.py` | `test_security.py` password-hashing tests; `test_user_service.py::test_create_user_hashes_password` |
| FR-04 | Authenticate with matric/staff number and password | UC-02, SQ-Login | `app/routers/auth.py`, `app/services/user_service.py` | `test_api_integration.py` login tests; `test_user_service.py` authentication tests |
| FR-05 | Issue signed legacy API access JWT | SQ-Login | `app/utils/jwt.py`, `app/config.py` | `test_api_integration.py::test_login_returns_token` |
| FR-06 | Retrieve the current user's profile | UC-03 | `app/routers/auth.py`, `app/utils/jwt.py` | `test_api_integration.py` profile authorization tests |
| FR-07 | Generate QR digital ID card | UC-04, CL-User | `app/routers/id_card.py`, `app/services/qr_service.py` | `test_api_integration.py` ID-card tests |
| FR-08 | Automatically create a wallet | UC-05, CL-Wallet | `app/services/wallet_service.py` | `test_wallet_service.py` wallet creation tests |
| FR-09 | Top up wallet with a positive amount | UC-05, SQ-Wallet | `app/routers/wallet.py`, `app/services/wallet_service.py` | `test_wallet_service.py` top-up tests; `test_api_integration.py` top-up tests |
| FR-10 | Pay from wallet subject to sufficient balance | UC-06, SQ-Wallet | `app/routers/wallet.py`, `app/services/wallet_service.py` | `test_wallet_service.py` payment tests; `test_api_integration.py` payment tests |
| FR-11 | Record wallet transactions with timestamps | CL-Transaction | `app/models/wallet.py` | Wallet service transaction tests |
| FR-12 | View transaction history | UC-07, SQ-Wallet | `app/routers/wallet.py`, `app/services/wallet_service.py` | `test_wallet_service.py` transaction-list tests; `test_api_integration.py` transaction endpoint test |
| FR-13 | Distinguish student, staff and administrator roles in the existing application | CL-User, UC-09 | `app/models/user.py`, `app/schemas/user.py`, RBAC utilities | `test_user_service.py::test_create_user_returns_user` |
| FR-14 | Provide application health check | — | `app/routers/health.py` | `test_api_integration.py::test_health_endpoint` |
| FR-15 | Provide web login and dashboard | UC-01, UC-02, UC-03, UC-07 | `app/routers/pages.py`, `app/templates/login.html`, `app/templates/dashboard.html`, `app/static/` | Manual/browser verification and applicable UI tests |

---

## 2. OIDC Federation — Functional Requirements

| Req ID | Requirement | Design / protocol artefact | Implementation | Verification evidence |
|---|---|---|---|---|
| OIDC-FR-01 | Publish OIDC provider metadata and endpoint locations | OIDC Discovery | `app/routers/oidc.py::openid_configuration` | OIDC discovery endpoint tests in the OIDC test suite |
| OIDC-FR-02 | Provide Authorization Code Flow for registered clients | OAuth 2.0 Authorization Code Grant | `app/routers/oidc.py`, `app/services/oidc_server.py` | Authorization and token endpoint tests |
| OIDC-FR-03 | Require PKCE using S256 | RFC 7636 PKCE | `app/services/oidc_server.py::ABUCodeChallenge` and `ABUAuthorizationCodeGrant` | OIDC authorization/token tests, including PKCE validation |
| OIDC-FR-04 | Issue RS256-signed ID tokens and publish matching public key material | OIDC ID Token, JWKS | `app/services/oidc_server.py::ABUOpenIDCode`, `app/utils/oidc_keys.py`, `/jwks.json` | OIDC token and signing-key tests |
| OIDC-FR-05 | Exchange a valid authorization code for tokens and reject expired, invalid or reused codes | OAuth token endpoint | `app/services/oidc_server.py`, `app/services/oidc_token_service.py` | `tests/test_oidc_token_endpoint.py`, including `test_authorization_code_can_be_exchanged_for_tokens`, `test_authorization_code_cannot_be_reused`, `test_expired_authorization_code_is_rejected` |
| OIDC-FR-06 | Return permitted user claims for a valid bearer access token | OIDC UserInfo | `app/routers/oidc.py::userinfo`, `app/services/oidc_token_service.py` | OIDC userinfo/access-token tests |
| OIDC-FR-07 | Revoke an access token for its authenticated client | RFC 7009 token revocation | `app/routers/oidc.py::revoke`, `app/services/oidc_token_service.py` | OIDC revocation tests |
| OIDC-FR-08 | Maintain a central browser session so a user can access another registered client without another password prompt | IdP session and browser redirect flow | `app/services/idp_session_service.py`, `app/routers/oidc.py::authorize`, `app/routers/auth.py` | OIDC session and service-authentication tests |
| OIDC-FR-09 | Register clients under administrator control and validate exact redirect URIs | Application Registry | `app/routers/admin.py`, `app/services/application_registry_service.py`, `app/schemas/application_registry.py` | Application-registry tests |
| OIDC-FR-10 | Allow administrators to activate or deactivate registered clients | Application Registry | `app/routers/admin.py` application status endpoint | Application-registry tests |
| OIDC-FR-11 | Keep each campus application as an independent OIDC client with its own callback and local session | OIDC client integration | `mock-services/portal/`, `lms/`, `library/`, `hostel/`, `wifi/`, `results/` | Service authentication matrix tests |
| OIDC-FR-12 | Reject legacy token query-string authentication in the migrated services | Client-side authentication boundary | Six `mock-services/*/main.py` client implementations | Service authentication matrix tests |
| OIDC-FR-13 | Record successful and failed authentication events with application and authentication-method context | Authentication audit model | `app/models/` authentication-event model, `app/routers/auth.py`, `app/routers/oidc.py` | Authentication-event and OIDC authorization tests |
| OIDC-FR-14 | Distinguish a fresh password login from use of an existing SSO session in the audit record | IdP login marker | `app/services/idp_login_marker_service.py`, `app/routers/oidc.py` | IdP session/login-marker tests |
| OIDC-FR-15 | Notify the user about authentication activity across registered applications | Security notification model and dashboard | `app/services/security_notification_service.py`, `app/routers/auth.py`, `app/templates/dashboard.html` | Security-notification and dashboard tests |
| OIDC-FR-16 | Restrict a user's activity and notifications to that user's own records | User-scoped authorization | `app/routers/auth.py` activity and notification endpoints | Authentication activity/notification authorization tests |
| OIDC-FR-17 | Let administrators inspect authentication events across applications and filter records | Admin audit interface/API | `app/routers/admin.py::list_authentication_activity` | Admin authentication-activity tests |

**Claim boundary for identity claims:** The current OIDC UserInfo implementation supplies `sub` and optional `name`/`email` according to granted scopes. Matric number and ABU role are not currently returned as OIDC claims. Client applications must not infer those attributes from the current OIDC response.

**Wi-Fi boundary:** The Wi-Fi item in this implementation is a browser-based OIDC client/portal. It does not by itself implement RADIUS, 802.1X or direct Wi-Fi network authentication. Those require a separate network-access integration.

---

## 3. Non-Functional Requirements Traceability

| Req ID | Requirement | Design / configuration | Verification / status |
|---|---|---|---|
| NFR-01 | Passwords must be stored as hashes, not plaintext | Bcrypt utility | Automated password-hashing tests |
| NFR-02 | OIDC authorization requests must use PKCE S256 | OIDC grant extension | Automated OIDC authorization/token tests |
| NFR-03 | OIDC ID tokens must be signed with an asymmetric algorithm and verifiable through published public keys | RS256, RSA key helper, JWKS | Automated token/key tests; production key configuration still requires operational verification |
| NFR-04 | Redirect URIs must be explicitly registered and validated | Application Registry | Registry validation tests |
| NFR-05 | Secrets and bearer credentials must not be exposed in audit records | Hash-only access-token persistence and audit-event fields | Security/code review and relevant tests |
| NFR-06 | Users must not read another user's activity or notifications | User-scoped database queries | Authorization tests |
| NFR-07 | Administrator-only operations must be protected by role-based access control | `require_role("admin")` | Admin authorization tests |
| NFR-08 | Each service must have an independent local session secret | Per-service `SESSION_SECRET` configuration | Configuration and service startup checks |
| NFR-09 | Production OIDC endpoints and callbacks must use HTTPS | Render environment and registered production callback URIs | Deployment verification required; local HTTP test override is not for production |
| NFR-10 | Support Windows local development and Linux CI | Python 3.12, dependency pins, GitHub Actions Ubuntu runner | Local Windows test run and GitHub Actions |
| NFR-11 | Preserve existing wallet, QR ID and legacy central API behavior while adding OIDC | Existing routers/models retained alongside OIDC components | Full regression test suite |
| NFR-12 | Database schema changes must be safely repeatable and versioned | SQLAlchemy models currently create missing tables; formal migration tooling is still recommended | Migration strategy review required before production schema evolution |
| NFR-13 | Production availability and recovery must be monitored | Render services and Neon database | Operational monitoring and recovery testing required; target uptime is not established by unit tests |

---

## 4. Verification Summary

### Local test evidence

The latest full local test run recorded during CI remediation completed with:

| Result | Count |
|---|---:|
| Passed | 208 |
| Deselected | 5 |
| Warnings | 15 |
| Failed | 0 |

This is evidence of the local test-suite result at that point in development. It is not proof that the latest GitHub Actions workflow has passed, that the six production clients are registered, or that production browser SSO has been verified.

### CI workflow

The GitHub Actions workflow contains a pytest job and a dependent Playwright E2E job. Both test steps require the local Authlib HTTP transport override when their tests use HTTP localhost URLs. The override is a test-only setting; production must use HTTPS.

### Deployment readiness gates

Before treating the OIDC upgrade as deployed, verify all of the following:

1. The feature branch is reviewed and merged to `main`.
2. The latest GitHub Actions unit/integration/service and E2E jobs pass.
3. The central IdP is deployed with its persistent RSA private/public signing-key pair and production issuer.
4. Each of the six services is registered in the central Application Registry using its exact production callback URI.
5. The issued client ID is configured in the corresponding service, with a unique session secret.
6. Browser tests confirm first login, SSO reuse across services, logout behavior, user notifications and audit records.
7. Database persistence and recovery are checked against the production database.

Until these gates are complete, the OIDC upgrade should be described as implemented on the feature branch and pending production rollout—not as a verified production SSO deployment.

---

## 5. Backward Traceability — Examples

| Test / verification area | Requirement(s) verified |
|---|---|
| `test_authorization_code_can_be_exchanged_for_tokens` | OIDC-FR-02, OIDC-FR-05 |
| `test_authorization_code_cannot_be_reused` | OIDC-FR-05 |
| `test_expired_authorization_code_is_rejected` | OIDC-FR-05 |
| Existing wallet payment and insufficient-balance tests | FR-10 |
| Existing duplicate-registration tests | FR-02 |
| Existing password-hashing tests | FR-03, NFR-01 |

---

## 6. Change Impact Analysis

For a change to the OIDC authorization-code or PKCE behavior, review at least:

1. `app/routers/oidc.py` — authorization and token endpoint wiring.
2. `app/services/oidc_server.py` — grant validation, PKCE, code persistence and ID-token generation.
3. `app/services/oidc_token_service.py` — access-token persistence and validation.
4. The OIDC client integrations under `mock-services/`.
5. The OIDC authorization and token endpoint test modules.
6. The OIDC protocol, deployment and security documentation.

For a change to security notifications or authentication auditing, review the event/session/notification models, their service modules, the user and administrator endpoints, dashboard rendering, and the corresponding authorization tests.

---

*End of Requirements Traceability Matrix.*
