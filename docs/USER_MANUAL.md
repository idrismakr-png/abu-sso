# ABU-SSO User Manual & Installation Guide
## Unified Single Sign-On & Digital Campus Wallet

**Version:** 1.0  
**Target users:** Students, Staff, and System Administrators of Ahmadu Bello University  
**Course:** COEN838 — Advanced Software Engineering  

---

## Part A — User Manual (For Students & Staff)

### A.1 What is ABU-SSO?

ABU-SSO is a single sign-on system that lets you use **one email and password** to access multiple campus services (Student Portal, LMS, Library, Hostel, Wi-Fi) and manage a personal **digital wallet** — all from one dashboard.

### A.2 Before You Start

- Use a modern browser: **Chrome, Edge, Firefox, or Safari**.
- Make sure you have a working email address.
- If you're using a shared computer, remember to **log out** when finished.

### A.3 Creating Your Account

1. Open your browser and go to:  
   `http://127.0.0.1:8000/login` (or the deployed URL).
2. You'll see the **Sign in** page.
3. If you are a new user, use the API's registration endpoint (`/docs` → **POST /auth/register**) or the ABU ICT portal — registration via the web UI is planned for a future release.
4. Provide:
   - **Email** — e.g. `idris@abu.edu.ng`
   - **Password** — at least 6 characters (8+ recommended)
   - **Full name** — e.g. `Idris Muhammad Abubakar`
   - **Role** — `student`, `staff`, or `admin`
   - **Matric number** — e.g. `ABU/2024/0001` (optional for staff)
5. Confirm. Your account is now created.

### A.4 Logging In

1. Go to `http://127.0.0.1:8000/login`.
2. Enter your **email** and **password**.
3. Click **Sign in**.
4. On success, you are redirected to your **Dashboard**.
5. On failure, a red error message appears — check your email and password.

### A.5 Your Dashboard

The dashboard shows everything you need at a glance:

| Section | What it shows |
|---------|---------------|
| **Welcome bar** | Your name, role, and matric number |
| **Campus Wallet** | Current balance, most recent transactions |
| **Digital ID Card** | Your name, matric, role, email, and a QR code |
| **Campus Services** | Quick-launch cards for Portal, LMS, Library, Hostel |
| **Log out** | Ends your session everywhere |

### A.6 Using Your Campus Wallet

**To top up your wallet:**
1. From the API docs (`/docs`) → **POST /wallet/topup** with `{ "amount": 5000, "description": "Initial top-up" }`.
2. Your balance increases immediately.
3. The transaction appears at the top of the list.

**To pay for a service (e.g., library fine):**
1. Use **POST /wallet/pay** with `{ "amount": 250, "description": "Library fine" }`.
2. The amount is deducted from your wallet.
3. If your balance is insufficient, the request is rejected with an error.

**To view transactions:**
- The dashboard shows the 50 most recent transactions automatically.
- API clients can call **GET /wallet/transactions**.

### A.7 Using Your Digital ID Card

- On the dashboard, your **QR code** appears under "Digital ID Card".
- Present it at library counters and hostel gates for scanning.
- Each QR code encodes **only** `id`, `matric_no`, and `role` — no personal data such as passwords.
- Regenerating your ID card: refresh the dashboard.

### A.8 Logging Out

- Click the red **Log out** button on the dashboard.
- Your token is deleted from the browser.
- You are redirected to the login page.
- If you try to open `/dashboard` without logging in, you will be sent back to `/login`.

### A.9 Troubleshooting

| Problem | Likely cause | Solution |
|---------|--------------|----------|
| "Invalid email or password" | Wrong credentials | Re-type carefully; email is case-insensitive |
| "Not authenticated" | Token expired (15 min) | Log in again |
| Dashboard shows "—" or blank | Token missing | Log out and log back in |
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

```bash
git clone https://github.com/idrismakr-png/abu-sso.git
cd abu-sso