# ABU-SSO — Unified Single Sign-On & Digital Campus Wallet

[![CI](https://github.com/idrismakr-png/abu-sso/actions/workflows/ci.yml/badge.svg)](https://github.com/idrismakr-png/abu-sso/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.142-009688)
![Tests](https://img.shields.io/badge/tests-69%20passing-brightgreen)
![Coverage](https://img.shields.io/badge/coverage-96%25-brightgreen)
![SAST](https://img.shields.io/badge/bandit-0%20findings-brightgreen)
![Live](https://img.shields.io/badge/live-abu--sso.onrender.com-success)

A unified authentication and campus services platform for **Ahmadu Bello University, Zaria**. One login grants access to multiple campus services (Portal, LMS, Library, Hostel, Wi-Fi) plus a digital wallet with QR ID card.

**Course:** COEN838 — Advanced Software Engineering  
**Student:** Idris Muhammad Abubakar (P25EGCP9003)

---

## 🌐 Live Demo

**Public URL:** [https://abu-sso.onrender.com](https://abu-sso.onrender.com)  
**API Docs:** [https://abu-sso.onrender.com/docs](https://abu-sso.onrender.com/docs)  
**Login Page:** [https://abu-sso.onrender.com/login](https://abu-sso.onrender.com/login)

> **Note:** The free tier spins down after 15 minutes of inactivity. The first request may take 30–60 seconds to wake the service.

**Demo credentials:**
- Admin: `idris@abu.edu.ng` / `secret123`
- Student: `student@abu.edu.ng` / `student123`

---

## ✨ Features

- 🔐 **Single Sign-On** — JWT-based authentication for all ABU services
- 🔑 **Secure Password Storage** — bcrypt hashing (cost ≥ 12)
- 🛡️ **Role-Based Access Control** — `student` / `staff` / `admin` roles enforced by middleware
- 📇 **Digital ID Card** — QR code encoding matric number + role
- 💰 **Campus Wallet** — top-up, pay, transaction history
- 🌐 **Web Dashboard** — Jinja2 + vanilla JS
- 👑 **Admin Panel** — user management, role changes, wallet top-ups, system stats
- 📖 **Auto-Generated API Docs** — OpenAPI 3.0 at `/docs`
- ✅ **69 Automated Tests** — 96% line coverage
- 🤖 **Continuous Integration** — GitHub Actions on every push
- 🛡️ **SAST Clean** — 0 findings across 525 lines (Bandit)
- ☁️ **Deployed** — Render (web) + Neon (PostgreSQL)

---

## 🚀 Quick Start (Local)

```bash
# Clone
git clone https://github.com/idrismakr-png/abu-sso.git
cd abu-sso

# Create environment
conda create -n abu-sso python=3.12 -y
conda activate abu-sso

# Install
pip install -r requirements.txt

# Run
uvicorn app.main:app --reload

🧪 Run Tests
pytest -v
pytest --cov=app --cov-report=term-missing

📚 Documentation
All engineering artefacts live in docs/:


Document Description
SRS	Software Requirements Specification (Module I)
RTM	Requirements Traceability Matrix
Design	Architecture, data model, patterns (Module III)
Security	STRIDE threat model, SAST evidence (Module IV)
Technical Report	Engineering narrative (Modules I–V)
Test Results	Full test inventory, coverage report, SAST output
User Manual	End-user + installation guide
Risk & Maintenance	Risk register + maintenance plan (Module V)
Presentation Guide	Slides + demo script + defence Q&A


🏗️ Architecture
HTTP  →  Router  →  Service  →  Model  →  Database
        (thin)    (business)   (ORM)     (SQLite/PG)

        Backend: FastAPI (Python 3.12)

Database: SQLite (dev) → PostgreSQL (prod, Neon)

Auth: JWT (HS256) + bcrypt

Authorization: Role-based middleware (require_role)

Testing: pytest + httpx

CI: GitHub Actions

SAST: Bandit

Hosting: Render (free tier) + Neon (free tier)

See docs/DESIGN.md for full details.

📊 Project Stats
Metric	Value
Endpoints	17
Functional Requirements	15/15 implemented
Automated Tests	69 passing
Line Coverage	96%
SAST Findings	0
CI Runtime	~24s
Deployment	Live on Render + Neon

🔒 Roles & Access
Role	Permissions
student	Own profile, own wallet, own ID card, dashboard
staff	Same as student
admin	All of the above + admin panel: list users, change roles, activate/deactivate, top up any wallet, view system stats
Students attempting to access /admin/* receive HTTP 403 Forbidden.

📄 License
MIT — see project documentation for details.

👤 Author
Idris Muhammad Abubakar
P25EGCP9003 — Department of Computer Engineering
Ahmadu Bello University, Zaria
📧 idrismakr@gmail.com