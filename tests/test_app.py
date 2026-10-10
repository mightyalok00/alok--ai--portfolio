import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

TEST_DB = Path("test_portfolio.db")
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB}"
os.environ["SESSION_SECRET"] = "test-secret-that-is-long-enough"
os.environ["ADMIN_PASSWORD"] = "test-admin-password"

from fastapi.testclient import TestClient  # noqa: E402
from app.database import engine, normalize_database_url  # noqa: E402
from app.main import app  # noqa: E402
from app.security import _requests  # noqa: E402


@pytest.fixture(autouse=True)
def isolate_rate_limiter():
    _requests.clear()
    yield
    _requests.clear()


def csrf_from(response):
    match = re.search(r'name="csrf_token" value="([^"]+)"', response.text)
    assert match, "CSRF token should be present in the form"
    return match.group(1)


def test_homepage_renders_projects_and_animation():
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert "SEO AI Intelligence" in response.text
        assert "Bank Customer Churn" in response.text
        assert "main.js" in response.text
        assert "Explore selected work" in response.text
        assert 'class="menu-toggle" type="button"' in response.text
        assert 'aria-controls="primary-navigation"' in response.text
        assert 'class="hero-ambience" aria-hidden="true"' in response.text
        assert 'href="#faq"' in response.text
        assert response.text.count('class="faq-item"') == 6
        assert "What roles are you looking for?" in response.text
        assert "Are the campaign metrics independently verified?" in response.text
        stylesheet = client.get("/static/css/styles.css")
        assert stylesheet.status_code == 200
        assert "@keyframes ambient-drift" in stylesheet.text
        assert "@keyframes faq-answer-in" in stylesheet.text
        assert "@media(prefers-reduced-motion:reduce)" in stylesheet.text


def test_health_endpoint():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


def test_postgres_database_urls_select_psycopg_driver():
    assert normalize_database_url("postgres://user:pass@db.example/app") == (
        "postgresql+psycopg://user:pass@db.example/app"
    )
    assert normalize_database_url("postgresql://user:pass@db.example/app?sslmode=require") == (
        "postgresql+psycopg://user:pass@db.example/app?sslmode=require"
    )
    assert normalize_database_url("postgresql+psycopg://user:pass@db.example/app") == (
        "postgresql+psycopg://user:pass@db.example/app"
    )


def test_admin_page_requires_login():
    with TestClient(app) as client:
        response = client.get("/admin")
        assert response.status_code == 200
        assert "Password" in response.text
        assert "Portfolio inbox" in response.text


def test_search_engine_endpoints():
    with TestClient(app) as client:
        robots = client.get("/robots.txt")
        sitemap = client.get("/sitemap.xml")
        assert robots.status_code == 200
        assert "Disallow: /admin" in robots.text
        assert "Sitemap:" in robots.text
        assert sitemap.status_code == 200
        assert sitemap.headers["content-type"].startswith("application/xml")
        assert "<urlset" in sitemap.text


def test_security_headers_are_set():
    with TestClient(app) as client:
        response = client.get("/")
        assert response.headers["x-content-type-options"] == "nosniff"
        assert response.headers["x-frame-options"] == "DENY"
        assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"
        assert "frame-ancestors 'none'" in response.headers["content-security-policy"]


def test_contact_form_rejects_invalid_csrf():
    with TestClient(app) as client:
        response = client.post("/contact", data={
            "name": "Test Visitor", "email": "visitor@example.com", "topic": "General",
            "message": "Hello", "csrf_token": "not-a-real-token",
        })
        assert response.status_code == 403


def test_contact_form_accepts_valid_submission():
    with TestClient(app) as client:
        page = client.get("/")
        token = csrf_from(page)
        response = client.post("/contact", data={
            "name": "Test Visitor", "email": "visitor@example.com", "topic": "Job opportunity",
            "message": "I would like to discuss a role.", "website": "", "csrf_token": token,
        })
        assert response.status_code == 200
        assert "Thank you" in response.text


def test_admin_login_and_logout():
    with TestClient(app) as client:
        login_page = client.get("/admin")
        response = client.post("/admin/login", data={
            "password": "test-admin-password", "csrf_token": csrf_from(login_page),
        })
        assert response.status_code == 200
        assert "Contact messages" in response.text
        logout_token = csrf_from(response)
        logout = client.post("/admin/logout", data={"csrf_token": logout_token})
        assert logout.status_code == 200
        assert "Sign in" in logout.text


def test_admin_login_rejects_wrong_password():
    with TestClient(app) as client:
        login_page = client.get("/admin")
        response = client.post("/admin/login", data={
            "password": "wrong-password", "csrf_token": csrf_from(login_page),
        })
        assert response.status_code == 401


def teardown_module():
    engine.dispose()
    if TEST_DB.exists():
        TEST_DB.unlink()


def test_privacy_page_and_skip_link():
    with TestClient(app) as client:
        response = client.get("/privacy")
        home = client.get("/")
        assert response.status_code == 200
        assert "Privacy notice" in response.text
        assert "Last updated" in response.text
        assert 'href="#main-content"' in home.text
        assert 'id="main-content"' in home.text


def test_sitemap_does_not_trust_unconfigured_host_header():
    with TestClient(app) as client:
        response = client.get("/sitemap.xml")
        assert response.status_code == 200
        assert "127.0.0.1:8000" in response.text
        malicious = client.get("/sitemap.xml", headers={"host": "attacker.example"})
        assert malicious.status_code == 400


def test_static_assets_resolve_from_absolute_application_path():
    with TestClient(app) as client:
        response = client.get("/static/css/styles.css")
        assert response.status_code == 200
        assert "text/css" in response.headers["content-type"]


def test_contact_rate_limit_returns_429_after_limit():
    with TestClient(app) as client:
        page = client.get("/")
        token = csrf_from(page)
        payload = {
            "name": "Test Visitor", "email": "not-an-email", "topic": "General",
            "message": "This request should fail validation.", "website": "", "csrf_token": token,
        }
        for _ in range(8):
            assert client.post("/contact", data=payload).status_code == 422
        assert client.post("/contact", data=payload).status_code == 429


def test_production_disables_interactive_api_docs():
    env = os.environ.copy()
    with tempfile.TemporaryDirectory() as tmpdir:
        env.update({
            "APP_ENV": "production",
            "SITE_URL": "https://portfolio.example.org",
            "CONTACT_EMAIL": "hello@portfolio.example.org",
            "ADMIN_PASSWORD": "a-strong-test-admin-password-123",
            "SESSION_SECRET": "a-long-random-test-session-secret-value-123456",
            "HTTPS_ONLY": "true",
            "DATABASE_URL": f"sqlite:///{Path(tmpdir) / 'production.db'}",
        })
        result = subprocess.run(
            [sys.executable, "-c", (
                "from fastapi.testclient import TestClient; from app.main import app; "
                "with_test = TestClient(app, base_url='https://portfolio.example.org'); "
                "with_test.__enter__(); "
                "print(app.docs_url, app.redoc_url, app.openapi_url, with_test.get('/').status_code, "
                "with_test.get('/docs').status_code); with_test.__exit__(None, None, None)"
            )],
            cwd=Path(__file__).resolve().parents[1],
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert result.stdout.strip() == "None None None 200 404"


def test_unverified_resume_is_not_published_and_case_studies_render():
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert "case-studies" in response.text
        assert "Download resume" not in response.text
        resume = client.get("/static/documents/alok-agarwal-resume.pdf")
        assert resume.status_code == 404
        private_draft = Path(__file__).resolve().parents[1] / "app" / "documents" / "alok-agarwal-resume-draft.pdf"
        assert private_draft.is_file()


def test_portfolio_upgrade_has_project_filters_and_quick_answers():
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert 'data-filter="seo"' in response.text
        assert 'data-filter="analytics"' in response.text
        assert 'id="quick-answers"' in response.text
        assert 'data-answer="projects"' in response.text
        assert "Quick answers." in response.text
        assert "Clear next steps." in response.text
        javascript = client.get("/static/js/main.js")
        assert javascript.status_code == 200
        assert "quickAnswers" in javascript.text
        assert "filter-hidden" in javascript.text


def test_portfolio_omits_unverified_claims_and_marks_private_demos():
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert "SEO & Search Strategy" in response.text
        assert "Marketing / SEO Analyst" in response.text
        assert "Junior Data Analyst" in response.text
        assert 'href="#target-roles"' in response.text
        assert "236%" not in response.text
        assert "346K" not in response.text
        assert "Google Skillshop" not in response.text
        assert "WsCube Tech" not in response.text
        assert response.text.count("Public demo unavailable at last check.") == 2


def test_contact_area_is_grouped_and_form_remains_accessible():
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert 'id="contact"' in response.text
        assert 'class="contact-info reveal"' in response.text
        assert 'class="contact-fields-row"' in response.text
        assert 'for="contact-name"' in response.text
        assert 'for="contact-email"' in response.text
        assert 'for="contact-topic"' in response.text
        assert 'for="contact-message"' in response.text
        assert 'action="/contact" method="post"' in response.text
