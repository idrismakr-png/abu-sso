"""End-to-end (system) tests — drive a real Chromium browser against a live server."""
import re

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e


def login(page: Page, base_url: str, email: str, password: str):
    """Helper: log in through the UI."""
    page.goto(f"{base_url}/login")
    page.fill("#email", email)
    page.fill("#password", password)
    page.click("#login-btn")
    page.wait_for_url(re.compile(r"/dashboard"), timeout=10_000)


# ---------- 1. Login page renders ----------

def test_login_page_renders(page: Page, base_url: str):
    page.goto(f"{base_url}/login")
    expect(page).to_have_title(re.compile("Login"))
    expect(page.locator("#email")).to_be_visible()
    expect(page.locator("#password")).to_be_visible()
    expect(page.locator("#login-btn")).to_be_visible()


# ---------- 2. Successful login redirects to dashboard ----------

def test_login_success_redirects_to_dashboard(page: Page, base_url: str, registered_user):
    login(page, base_url, registered_user["email"], registered_user["password"])
    expect(page).to_have_url(re.compile(r"/dashboard"))
    expect(page.locator("#welcome")).to_contain_text("Welcome")


# ---------- 3. Dashboard displays user data + QR ----------

def test_dashboard_shows_user_data_and_qr(page: Page, base_url: str, registered_user):
    login(page, base_url, registered_user["email"], registered_user["password"])

    # Wallet section
    expect(page.locator("#balance")).to_contain_text("₦0.00")

    # Profile info renders from /auth/me
    expect(page.locator("#id-email")).to_have_text(registered_user["email"])

    # QR image src is set asynchronously — wait for it
    qr = page.locator("#qr-img")
    page.wait_for_function(
        "document.querySelector('#qr-img')?.src?.startsWith('data:image/png;base64,')",
        timeout=10_000,
    )
    qr_src = qr.get_attribute("src")
    assert qr_src and qr_src.startswith("data:image/png;base64,")


# ---------- 4. Logout redirects to login page ----------

def test_logout_redirects_to_login(page: Page, base_url: str, registered_user):
    login(page, base_url, registered_user["email"], registered_user["password"])
    page.click("#logout-btn")
    page.wait_for_url(re.compile(r"/login"), timeout=5_000)
    expect(page.locator("#email")).to_be_visible()


# ---------- 5. RBAC: student is redirected away from /admin ----------

def test_student_cannot_access_admin_page(page: Page, base_url: str, registered_user):
    login(page, base_url, registered_user["email"], registered_user["password"])

    # Admin Panel button is hidden for a student
    admin_btn = page.locator("#admin-link")
    expect(admin_btn).to_be_hidden()

    # Direct navigation to /admin redirects to /dashboard (client-side guard)
    page.goto(f"{base_url}/admin")
    page.wait_for_url(re.compile(r"/dashboard"), timeout=5_000)