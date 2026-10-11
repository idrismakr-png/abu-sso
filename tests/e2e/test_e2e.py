"""End-to-end (system) tests — drive a real Chromium browser against a live server."""
import re

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e


def login(page: Page, base_url: str, matric_no: str, password: str):
    page.goto(f"{base_url}/login")
    page.fill("#matric_no", matric_no)
    page.fill("#password", password)
    page.click("#login-btn")
    page.wait_for_url(re.compile(r"/dashboard"), timeout=10_000)


def test_login_page_renders(page: Page, base_url: str):
    page.goto(f"{base_url}/login")
    expect(page).to_have_title(re.compile("Login"))
    expect(page.locator("#matric_no")).to_be_visible()
    expect(page.locator("#password")).to_be_visible()
    expect(page.locator("#login-btn")).to_be_visible()


def test_login_success_redirects_to_dashboard(page: Page, base_url: str, registered_user):
    login(page, base_url, registered_user["matric_no"], registered_user["password"])
    expect(page).to_have_url(re.compile(r"/dashboard"))
    expect(page.locator("#welcome")).to_contain_text("Welcome")


def test_dashboard_shows_user_data_and_qr(page: Page, base_url: str, registered_user):
    login(page, base_url, registered_user["matric_no"], registered_user["password"])
    expect(page.locator("#balance")).to_contain_text("₦0.00")
    expect(page.locator("#id-matric")).to_have_text(registered_user["matric_no"])
    page.wait_for_function(
        "document.querySelector('#qr-img')?.src?.startsWith('data:image/png;base64,')",
        timeout=10_000,
    )
    qr_src = page.locator("#qr-img").get_attribute("src")
    assert qr_src and qr_src.startswith("data:image/png;base64,")


def test_logout_redirects_to_login(page: Page, base_url: str, registered_user):
    login(page, base_url, registered_user["matric_no"], registered_user["password"])
    page.click("#logout-btn")
    page.wait_for_url(re.compile(r"/login"), timeout=5_000)
    expect(page.locator("#matric_no")).to_be_visible()


def test_student_cannot_access_admin_page(page: Page, base_url: str, registered_user):
    login(page, base_url, registered_user["matric_no"], registered_user["password"])
    admin_btn = page.locator("#admin-link")
    expect(admin_btn).to_be_hidden()
    page.goto(f"{base_url}/admin")
    page.wait_for_url(re.compile(r"/dashboard"), timeout=5_000)