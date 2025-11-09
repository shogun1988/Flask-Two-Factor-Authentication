from bs4 import BeautifulSoup
from urllib.parse import urlparse
import uuid
import pyotp
from src.accounts.models import User
from src import db

# Pages we want to crawl (public + auth required ones)
INITIAL_PATHS = [
    "/login",
    "/register",
]

# Add more pages that become available post-login
AUTH_REQUIRED_PATHS = [
    "/setup-2fa",
    "/verify-2fa",
    "/",  # home
]


def extract_links(html: bytes):
    soup = BeautifulSoup(html, "html.parser")
    links = set()
    for a in soup.find_all("a", href=True):
        href = a['href']
        # Skip external absolute links
        if href.startswith("http://") or href.startswith("https://"):
            continue
        # Basic normalization: ignore anchors and mailto
        if href.startswith("#") or href.startswith("mailto:"):
            continue
        # only keep path part for relative links
        links.add(href)
    return links


def test_dead_links(client):
    visited = set()
    to_visit = list(INITIAL_PATHS)
    status_errors = []

    while to_visit:
        path = to_visit.pop()
        if path in visited:
            continue
        visited.add(path)
        resp = client.get(path, follow_redirects=True)
        if resp.status_code >= 400:
            status_errors.append((path, resp.status_code))
            continue
        # Extract links and enqueue new ones
        for link in extract_links(resp.data):
            # Keep only internal app links
            parsed = urlparse(link)
            internal_path = parsed.path
            if internal_path and internal_path not in visited:
                to_visit.append(internal_path)

    assert not status_errors, f"Dead or failing links: {status_errors}"


def test_dead_links_authenticated(client):
    # 1) Register a new user
    uname = f"user_{uuid.uuid4().hex[:8]}"
    pwd = "TestPass123!"
    resp = client.post(
        "/register",
        data={"username": uname, "password": pwd, "confirm": pwd},
        follow_redirects=True,
    )
    assert resp.status_code < 400

    # 2) Compute current OTP for this user's secret and enable 2FA via verify route
    # Query must run inside app context
    with client.application.app_context():
        user = User.query.filter_by(username=uname).first()
        assert user is not None
        otp = pyotp.TOTP(user.secret_token).now()

    # Load verify page (optional), then submit OTP
    client.get("/verify-2fa")
    resp = client.post("/verify-2fa", data={"otp": otp}, follow_redirects=True)
    assert resp.status_code < 400

    # 3) Now authenticated, crawl internal links starting from protected pages
    to_visit = set(["/", "/setup-2fa", "/verify-2fa"])
    visited = set()
    status_errors = []

    while to_visit:
        path = to_visit.pop()
        if path in visited:
            continue
        visited.add(path)

        resp = client.get(path, follow_redirects=True)
        if resp.status_code >= 400:
            status_errors.append((path, resp.status_code))
            continue

        for link in extract_links(resp.data):
            parsed = urlparse(link)
            internal_path = parsed.path
            if internal_path and internal_path not in visited:
                to_visit.add(internal_path)

    assert not status_errors, f"Dead or failing links (auth): {status_errors}"
