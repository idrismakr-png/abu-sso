"""End-to-end (system) tests — self-contained with own fixtures."""
import os
import re
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

import httpx
import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e

ROOT = Path(__file__).resolve().parent.parent.parent
E2E_PORT = 8001
E2E_BASE_URL = f"http://127.0.0.1:{E2E_PORT}"


@pytest.fixture(scope="session")
def live_server():
    """Spawn a real uvicorn subprocess on port 8001 with its own temp DB."""
    tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp_db.close()

    log_path = ROOT / "e2e_server.log"
    log_file = open(log_path, "w", encoding="utf-8")

    env = os.environ.copy()
    env["DATABASE_URL"] = f"sqlite:///{tmp_db.name}"
    env["JWT_SECRET"] = "e2e-test-secret-key-which-is-long-enough-32-bytes"
    env["PYTHONPATH"] = str(ROOT)
    env["PYTHONUNBUFFERED"] = "1"

    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app",
         "--host", "127.0.0.1", "--port", str(E2E_PORT), "--log-level", "info"],
        cwd=str(ROOT),
        env=env,
        stdout=log_file,
        stderr=subprocess.STDOUT,
    )

    # Wait for the server, up to 30s
    ready = False
    for _ in range(60):
        if proc.poll() is not None:
            break  # process died
        try:
            r = httpx.get(f"{E2E_BASE_URL}/health", timeout=1.0)
            if r.status_code == 200:
                ready = True
                break
        except Exception:
            time.sleep(0.5)

    if not ready:
        log_file.close()
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                log_content = f.read()
        except OSError:
            log_content = "(could not read log)"
        proc.terminate()
        pytest.fail(
            f"Live server did not start within 30 seconds.\n"
            f"Exit code: {proc.poll()}\n"
            f"--- server log ---\n{log_content}\n--- end log ---"
        )

    yield E2E_BASE_URL

    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
    log_file.close()
    try:
        os.unlink(tmp_db.name)
    except OSError:
        pass
    try:
        os.unlink(log_path)
    except OSError:
        pass


@pytest.fixture(scope="session")
def base_url(live_server):
    return live_server


@pytest.fixture
def registered_user(live_server):
    """Create a fresh user in the live server and return matric + password."""
    matric = f"E2E/{uuid.uuid4().hex[:8].upper()}"
    res = httpx.post(
        f"{live_server}/auth/register",
        json={
            "email": f"{matric.replace('/', '_').lower()}@abu.edu.ng",
            "password": "secret123",
            "full_name": "E2E Tester",
            "role": "student",
            "matric_no": matric,
        },
        timeout=5.0,
    )
    assert res.status_code == 201, f"Register failed: {res.status_code} {res.text}"
    return {"matric_no": matric, "password": "secret123"}


def login(page: Page, base_url: str, matric_no: str, password: str):
    page.goto(f"{base_url}/login")
    page.fill("#matric_no", matric_no)
    page.fill("#password", password)
    page.click("#login-btn")
    page.wait_for_url(re.compile(r"/dashboard"), timeout=10_000)


# ---------- 1. Login page renders ----------

def test_login_page_renders(page: Page, base_url: str):
    page.goto(f"{base_url}/login")
    expect(page).to_have_title(re.compile("Login"))
    expect(page.locator("#matric_no")).to_be_visible()
    expect(page.locator("#password")).to_be_visible()
    expect(page.locator("#login-btn")).to_be_visible()


# ---------- 2. Successful login redirects to dashboard ----------

def test_login_success_redirects_to_dashboard(page: Page, base_url: str, registered_user):
    login(page, base_url, registered_user["matric_no"], registered_user["password"])
    expect(page).to_have_url(re.compile(r"/dashboard"))
    expect(page.locator("#welcome")).to_contain_text("Welcome")


# ---------- 3. Dashboard displays user data + QR ----------

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


# ---------- 4. Logout redirects to login page ----------

def test_logout_redirects_to_login(page: Page, base_url: str, registered_user):
    login(page, base_url, registered_user["matric_no"], registered_user["password"])
    page.click("#logout-btn")
    page.wait_for_url(re.compile(r"/login"), timeout=5_000)
    expect(page.locator("#matric_no")).to_be_visible()


# ---------- 5. RBAC: student is redirected away from /admin ----------

def test_student_cannot_access_admin_page(page: Page, base_url: str, registered_user):
    login(page, base_url, registered_user["matric_no"], registered_user["password"])
    admin_btn = page.locator("#admin-link")
    expect(admin_btn).to_be_hidden()
    page.goto(f"{base_url}/admin")
    page.wait_for_url(re.compile(r"/dashboard"), timeout=5_000)