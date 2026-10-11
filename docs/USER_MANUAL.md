# ABU-SSO User Manual & Installation Guide
## Unified Single Sign-On & Digital Campus Wallet

**Version:** 1.1  
**Target users:** Students, Staff, and System Administrators of Ahmadu Bello University  
**Course:** COEN838 — Advanced Software Engineering  

---

## Part A — User Manual (For Students & Staff)

### A.1 What is ABU-SSO?

ABU-SSO is a single sign-on system that lets you use **one matric / staff number and password** to access multiple campus services (Student Portal, LMS, Library, Hostel, Wi-Fi, Result Checker) and manage a personal **digital wallet** — all from one dashboard.

### A.2 Before You Start

- Use a modern browser: **Chrome, Edge, Firefox, or Safari**.
- You need your **matric number** (students) or **staff number** (staff).
- Your account is created by **ABU ICT** after admission or employment — you do **not** self-register.
- If you're using a shared computer, remember to **log out** when finished.

### A.3 Getting Your Account

Unlike consumer websites, **ABU-SSO does not have public self-registration**.

| Your situation | What to do |
|----------------|-----------|
| **New student / staff member** | Wait for ABU ICT to create your account. They will provide your initial password. |
| **Administrator onboarding a user** | Log in as admin → Admin Panel → "Create User Account" (see Part C). |
| **You forgot your password** | Contact ABU ICT. |

**Why no self-registration?** Because accounts must be tied to real university records. Only the very first user of a fresh deployment becomes an admin automatically; after that, all new accounts come from an administrator.

### A.4 Logging In

1. Open your browser and go to the login page:  
   `https://abu-sso.onrender.com/login` (production)  
   or `http://127.0.0.1:8000/login` (local development)
2. Enter your **Matric / Staff Number** — e.g., `P25EGCP9003` or `ADMIN/001`
3. Enter your **Password**
4. Click **Sign in**
5. On success, you are redirected to your **Dashboard**.
6. On failure, a red error message appears — check your number and password.

> **Tip:** Your matric / staff number is **not case-sensitive**. `p25egcp9003` and `P25EGCP9003` both work.

### A.5 Your Dashboard

The dashboard shows everything at a glance:

| Section | What it shows |
|---------|---------------|
| **Welcome bar** | Your name, role, and matric number |
| **Campus Wallet** | Current balance and recent transactions |
| **Digital ID Card** | Your name, matric, role, email, and QR code |
| **Campus Services** | Six clickable cards — Portal, LMS, Result Checker, Library, Hostel, Wi-Fi |
| **Log out** | Ends your session |
| **Admin Panel** (admins only) | Blue button to open the admin page |

### A.6 Using Your Campus Wallet

**To check your balance:**
- The dashboard shows your current balance at the top of the "Campus Wallet" card.

**To top up your wallet:**
- Students can request a top-up from library or hostel counters.
- Admins can top up any wallet via the Admin Panel (see Part C).

**To pay for a service (e.g., library fine):**
- Payments are initiated through the relevant campus service (Library, Hostel, etc.).

**To view transactions:**
- The dashboard lists the 50 most recent transactions automatically.

### A.7 Using Your Digital ID Card

- On the dashboard, your **QR code** appears under "Digital ID Card".
- Present it at library counters and hostel gates for scanning.
- Each QR code encodes **only** `id`, `matric_no`, and `role` — no personal data such as passwords.
- Regenerating your ID card: just refresh the dashboard.

### A.8 Using the Six Campus Services (Single Sign-On)

The **Campus Services** card on your dashboard shows six buttons. Clicking any of them opens a **separate campus application** in a new tab — **already signed in** with your ABU-SSO account.

| Service | What you can do |
|---------|-----------------|
| **Student Portal** | Course registration, enrollment |
| **LMS (Moodle)** | Lectures, assignments, quizzes |
| **Result Checker** | Semester results, GPA |
| **Library** | Borrowed books, fines |
| **Hostel** | Room booking, gate access |
| **Campus Wi-Fi** | Network access, device registration |

You do **not** need to log in again — each service independently verifies your ABU-SSO token.

> **First-click delay:** On the free-tier deployment, the first click after 15 minutes of inactivity may take 30–60 seconds while the service wakes up. Subsequent clicks are instant.

### A.9 Logging Out

- Click the red **Log out** button on the dashboard.
- Your token is deleted from the browser.
- You are redirected to the login page.
- If you try to open `/dashboard` without logging in, you will be sent back to `/login`.

### A.10 Troubleshooting

| Problem | Likely cause | Solution |
|---------|--------------|----------|
| "Invalid matric/staff number or password" | Wrong credentials | Re-type carefully; matric is not case-sensitive |
| "Not authenticated" | Token expired (15 min) | Log in again |
| Dashboard shows "—" or blank | Token missing | Log out and log back in |
| Service card opens but page times out | Free-tier service sleeping | Wait 30–60 s and refresh |
| "Invalid or expired token" on a service | Token expired between clicks | Return to dashboard, log out, log back in, click immediately |
| Page looks unstyled | Cache issue | Press **Ctrl + F5** |

---

## Part B — Installation Guide (For Developers)

### B.1 Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.12.x | Backend runtime |
| Git | 2.40+ | Version control |
| VS Code | Latest | Code editor |
| Anaconda or Miniconda | Latest | Environment management |

### B.2 Clone the Repository

git clone https://github.com/idrismakr-png/abu-sso.git
cd abu-sso
B.3 Create and Activate the Environment

conda create -n abu-sso python=3.12 -y
conda activate abu-sso
B.4 Install Dependencies

python -m pip install --upgrade pip
pip install -r requirements.txt
B.5 Configure Environment Variables (Optional)
Copy .env.example to .env and adjust:


copy .env.example .env     # Windows
cp .env.example .env       # macOS/Linux
Edit .env and set a strong JWT_SECRET (at least 32 characters).

B.6 Run the Application

uvicorn app.main:app --reload
Then open:

Dashboard: http://127.0.0.1:8000/login

API docs: http://127.0.0.1:8000/docs

B.7 Run the Six Mock SSO Services (optional)
In six separate terminals:


cd mock-services/portal  && uvicorn main:app --reload --port 4001
cd mock-services/lms     && uvicorn main:app --reload --port 4002
cd mock-services/library && uvicorn main:app --reload --port 4003
cd mock-services/hostel  && uvicorn main:app --reload --port 4004
cd mock-services/wifi    && uvicorn main:app --reload --port 4005
cd mock-services/results && uvicorn main:app --reload --port 4006
The dashboard auto-detects localhost vs. production and wires the cards accordingly.

B.8 Run the Tests
pytest -q                      # 79 fast tests
pytest tests/e2e -m e2e        # 5 E2E tests
Expected: 84 passed.

B.9 Optional — Coverage Report

pip install pytest-cov
pytest --cov=app --cov-report=html
Open htmlcov/index.html in your browser.

B.10 Optional — Static Security Scan

pip install bandit
bandit -r app/
Expected: 0 findings.

B.11 Optional — Deploy to Render
The repo includes render.yaml, which declares all seven web services (IdP + 6 mock services). To deploy:

Push your repo to GitHub.

Go to https://render.com → New → Blueprint → connect your repo.

Render detects render.yaml and creates all seven services.

Set the DATABASE_URL environment variable on the abu-sso service to your PostgreSQL connection string (e.g., from Neon).

Wait ~5 minutes for all services to build.

Your IdP is live at https://abu-sso.onrender.com.

Part C — Administrator Guide
C.1 Getting Admin Access
The first-ever user on a fresh deployment becomes admin automatically. This is called the "bootstrap" user.

To create the bootstrap admin (fresh deployment only):

Visit https://abu-sso.onrender.com/docs

Find POST /auth/register → click "Try it out"

Submit a JSON body:

json
{
  "email": "admin@abu.edu.ng",
  "password": "admin123",
  "full_name": "System Administrator",
  "role": "student",
  "matric_no": "ADMIN/001"
}
The response shows "role": "admin" — the bootstrap worked.

After this, POST /auth/register returns HTTP 403 — no more public registrations.

C.2 Logging In as Admin
Go to /login

Enter matric/staff number: ADMIN/001

Enter password: admin123

You'll see the dashboard with a blue Admin Panel button.

Click Admin Panel to reach /admin.

C.3 The Admin Panel
The Admin Panel has four sections:

1. System Statistics

Total users, active users, wallets, total balance, total transactions.

2. Create User Account

Full Name, Email, Matric / Staff Number, Role (student / staff / admin), Initial Password.

The new user can log in immediately with their matric number and password.

All fields are required.

3. Top Up Any Wallet

Enter a user's matric number and an amount.

Instantly credits their wallet with a "credit" transaction.

4. All Users

Table of every account with columns: Matric, Name, Email, Role, Active, Actions.

Change role: select from the dropdown — saves immediately.

Activate / Deactivate: toggle a user's account. Deactivated users cannot log in.

C.4 Admin Operations — Step by Step
Create a new student:

Scroll to "Create User Account"

Fill in: Jane Doe, jane@abu.edu.ng, P25EGCP1234, student, welcome123

Click Create Account

Green confirmation appears; Jane can now log in with P25EGCP1234 / welcome123

Promote a user to staff:

In the "All Users" table, find the user

Change the Role dropdown from student to staff

Confirm the notification

Deactivate a user:

In the "All Users" table, find the user

Click the red Deactivate button

Their is_active becomes false; login attempts are rejected

Top up a wallet:

Scroll to "Top Up Any Wallet"

Enter the user's matric number and amount (e.g., 1000)

Click Top Up

C.5 Rotating the JWT Secret
Change JWT_SECRET in .env (local) or in Render's Environment tab (production).

Restart the application (Render does this automatically).

All existing tokens become invalid — every user must log in again.

C.6 Backups
SQLite (dev): copy abu_sso.db to a safe location.

PostgreSQL (production): use Neon's built-in PITR (point-in-time recovery).

C.7 Monitoring
Ping /health every 60 seconds (UptimeRobot or similar).

If it fails, check the Render logs.

Part D — Support
For issues related to the ABU-SSO prototype, contact the project author:

Idris Muhammad Abubakar — P25EGCP9003 — Department of Computer Engineering, ABU Zaria.