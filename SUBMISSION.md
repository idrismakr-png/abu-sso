# COEN838 Project Submission

**Student:** Idris Muhammad Abubakar  
**Matric No:** P25EGCP9003  
**Course:** COEN838 — Advanced Software Engineering  
**Question:** Question 7 — Unified ABU-SSO  
**Date:** October 2026  

---

## 🚀 Live Application

| What | URL |
|------|-----|
| **Dashboard / Login** | https://abu-sso.onrender.com/login |
| **Admin Panel** | https://abu-sso.onrender.com/admin |
| **API Documentation** | https://abu-sso.onrender.com/docs |
| **Health Check** | https://abu-sso.onrender.com/health |

**Demo credentials:** Use only credentials issued for the current demonstration environment. Do not publish passwords in source control or submission documents.

> **Note:** Free-tier cloud services sleep after 15 minutes of inactivity. First request after idle takes 30–60 seconds. Subsequent requests are fast.

---

## 🌐 Six Distributed SSO Services

| Service | URL |
|---------|-----|
| Student Portal | https://abu-sso-portal.onrender.com |
| LMS (Moodle) | https://abu-sso-lms.onrender.com |
| Library | https://abu-sso-library.onrender.com |
| Hostel | https://abu-sso-hostel.onrender.com |
| Wi-Fi | https://abu-sso-wifi.onrender.com |
| Result Checker | https://abu-sso-results.onrender.com |

Each service is an independent OIDC client. It redirects to the central ABU-SSO identity provider, completes Authorization Code Flow with PKCE, validates the OIDC response and establishes its own local service session. The central IdP browser session enables SSO across services.

---

## 📚 Documentation Index

| # | Document | Markdown | PDF |
|---|----------|:--------:|:---:|
| 1 | Software Requirements Specification | [SRS.md](docs/SRS.md) | [SRS.pdf](docs/SRS.pdf) |
| 2 | Requirements Traceability Matrix | [RTM.md](docs/RTM.md) | [RTM.pdf](docs/RTM.pdf) |
| 3 | Design Document | [DESIGN.md](docs/DESIGN.md) | [DESIGN.pdf](docs/DESIGN.pdf) |
| 4 | Security Document | [SECURITY.md](docs/SECURITY.md) | [SECURITY.pdf](docs/SECURITY.pdf) |
| 5 | Technical Report | [TECHNICAL_REPORT.md](docs/TECHNICAL_REPORT.md) | [TECHNICAL_REPORT.pdf](docs/TECHNICAL_REPORT.pdf) |
| 6 | Test Results & Quality Evidence | [TEST_RESULTS.md](docs/TEST_RESULTS.md) | [TEST_RESULTS.pdf](docs/TEST_RESULTS.pdf) |
| 7 | User Manual & Installation Guide | [USER_MANUAL.md](docs/USER_MANUAL.md) | [USER_MANUAL.pdf](docs/USER_MANUAL.pdf) |
| 8 | Risk Register & Maintenance Plan | [RISK_AND_MAINTENANCE.md](docs/RISK_AND_MAINTENANCE.md) | [RISK_AND_MAINTENANCE.pdf](docs/RISK_AND_MAINTENANCE.pdf) |
| 9 | AI Use Declaration | [AI_USE_DECLARATION.md](docs/AI_USE_DECLARATION.md) | [AI_USE_DECLARATION.pdf](docs/AI_USE_DECLARATION.pdf) |
| 10 | Presentation Guide | [PRESENTATION.md](docs/PRESENTATION.md) | [PRESENTATION.pdf](docs/PRESENTATION.pdf) |
| 11 | UML Diagrams | [diagrams/](docs/diagrams/) | [UML_Diagrams.pdf](docs/diagrams/UML_Diagrams.pdf) |

---

## 🧪 Running the Project

### Quick Start

```bash
git clone https://github.com/idrismakr-png/abu-sso.git
cd abu-sso
conda create -n abu-sso python=3.12 -y
conda activate abu-sso
pip install -r requirements.txt
uvicorn app.main:app --reload

<!-- Documentation reviewed against the deployed implementation on November 22, 2026. -->
