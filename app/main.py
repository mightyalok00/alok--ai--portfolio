import secrets
import re
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlparse
from xml.sax.saxutils import escape as xml_escape

from email_validator import EmailNotValidError, validate_email
from fastapi import Depends, FastAPI, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.database import SessionLocal, init_db
from app.models import ContactMessage, Subscriber
from app.security import allow_request, csrf_token, valid_csrf
from app.settings import settings


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.app_env.lower() == "production":
        if settings.admin_password == "change-this-before-deploying" or len(settings.admin_password) < 16:
            raise RuntimeError("Set a unique ADMIN_PASSWORD of at least 16 characters before production startup.")
        if settings.session_secret == "development-only-change-this-secret" or len(settings.session_secret) < 32:
            raise RuntimeError("Set a random SESSION_SECRET of at least 32 characters before production startup.")
        if not settings.https_only:
            raise RuntimeError("Set HTTPS_ONLY=true when running in production behind HTTPS.")
        if not settings.contact_email or settings.contact_email.endswith("@example.com"):
            raise RuntimeError("Set a real CONTACT_EMAIL before production startup.")
        site_url = urlparse(settings.site_url)
        if (
            site_url.scheme != "https"
            or not site_url.netloc
            or not site_url.hostname
            or not re.fullmatch(r"[A-Za-z0-9.-]+", site_url.hostname)
            or site_url.hostname in {"localhost", "127.0.0.1", "example.com", "your-domain.com"}
            or site_url.hostname.endswith(".example")
            or site_url.username
            or site_url.password
            or site_url.path not in {"", "/"}
            or site_url.query
            or site_url.fragment
        ):
            raise RuntimeError("Set SITE_URL to your real public HTTPS origin before production startup.")
    init_db()
    yield


is_production = settings.app_env.lower() == "production"
app = FastAPI(
    title=settings.site_name,
    description=settings.tagline,
    lifespan=lifespan,
    docs_url=None if is_production else "/docs",
    redoc_url=None if is_production else "/redoc",
    openapi_url=None if is_production else "/openapi.json",
)
configured_hostname = urlparse(settings.site_url).hostname
if is_production:
    trusted_hosts = [configured_hostname] if configured_hostname else []
else:
    trusted_hosts = ["localhost", "127.0.0.1", "testserver"]
    if configured_hostname and configured_hostname not in trusted_hosts:
        trusted_hosts.append(configured_hostname)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=trusted_hosts)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret,
    https_only=settings.https_only,
    same_site="lax",
    max_age=60 * 60 * 8,
)
STATIC_DIR = Path(__file__).resolve().parent / "static"
TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATE_DIR)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Set baseline browser protections for every response."""
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self'; "
        "base-uri 'self'; form-action 'self'; frame-ancestors 'none'; object-src 'none'",
    )
    return response


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def page_context(request: Request) -> dict:
    return {"request": request, "settings": settings, "csrf_token": csrf_token(request)}


def public_base_url(request: Request) -> str:
    """Return a configured canonical origin, avoiding Host-header-derived URLs in production."""
    configured = settings.site_url.strip().rstrip("/")
    if configured:
        return configured
    return str(request.base_url).rstrip("/")


def clean_text(value: str, limit: int) -> str:
    value = " ".join(value.strip().split())
    if not value or len(value) > limit:
        raise ValueError(f"Field must contain 1–{limit} characters.")
    return value


PROJECTS = [
    {
        "number": "01", "type": "SEO · AI · ANALYTICS",
        "name": "SEO AI Intelligence",
        "summary": "An SEO intelligence platform exploring search analytics, machine-learning signals, and actionable recommendations.",
        "stack": ["Python", "FastAPI", "SEO", "AI/ML"],
        "repo": "https://github.com/mightyalok00/seo-ai-intelligence",
        "demo": "",
        "demo_note": "Public demo unavailable at last check.",
        "visual": "seo", "featured": True,
    },
    {
        "number": "02", "type": "RECOMMENDATION SYSTEM",
        "name": "Movie Recommendation System",
        "summary": "A Scikit-learn recommendation project using movie metadata and rating data, with emphasis on reproducibility and evaluation.",
        "stack": ["Python", "Scikit-learn", "Recommenders"],
        "repo": "https://github.com/mightyalok00/movie-recommendation-system-scikit-learn",
        "demo": "",
        "demo_note": "Public demo unavailable at last check.",
        "visual": "churn", "featured": True,
    },
    {
        "number": "03", "type": "BUSINESS INTELLIGENCE",
        "name": "Mega Market Sales Dashboard",
        "summary": "A sales analytics project designed to turn transactional data into useful business views and decision support.",
        "stack": ["Python", "Pandas", "Dashboards"],
        "repo": "https://github.com/mightyalok00/mega-market-sales-dashboard",
        "visual": "fare", "featured": True,
    },
    {
        "number": "04", "type": "CLASSIFICATION · MODEL EVALUATION",
        "name": "Bank Customer Churn",
        "summary": "A supervised-learning workflow focused on churn prediction, preprocessing, model comparison, and communicating evaluation results.",
        "stack": ["Pandas", "Scikit-learn", "Classification"],
        "repo": "https://github.com/mightyalok00/bank-customer-churn-prediction",
        "visual": "sql", "featured": True,
    },
    {
        "number": "05", "type": "REGRESSION · ML",
        "name": "Uber Fare Prediction",
        "summary": "A fare-prediction project exploring regression workflows, feature preparation, model comparison, and an applied ML use case.",
        "stack": ["Python", "Regression", "Scikit-learn"],
        "repo": "https://github.com/mightyalok00/Uber-Fare-Prediction-Model",
        "visual": "eda", "featured": False,
    },
    {
        "number": "06", "type": "PYTHON · DEVELOPER TOOLING",
        "name": "Repo Doctor AI",
        "summary": "A repository-health tool exploring automated code checks and practical feedback for developer workflows.",
        "stack": ["Python", "AST", "Automation"],
        "repo": "https://github.com/mightyalok00/Repo-Doctor-AI",
        "visual": "code", "featured": False,
    },
    {
        "number": "07", "type": "SQL · OPERATIONS ANALYTICS",
        "name": "Apollo Patient Flow",
        "summary": "Healthcare operations analysis using SQL to explore patient flow, aggregate operational metrics, and structure reporting data.",
        "stack": ["MySQL", "CTEs", "Window Functions"],
        "repo": "https://github.com/mightyalok00/apollo-patient-flow-SQL-analysis",
        "visual": "sql", "featured": False,
    },
    {
        "number": "08", "type": "EDA · VISUAL ANALYTICS",
        "name": "Diamonds Visual Analysis",
        "summary": "Exploratory data analysis and visualization focused on understanding relationships in the diamonds dataset.",
        "stack": ["Pandas", "Seaborn", "EDA"],
        "repo": "https://github.com/mightyalok00/seaborn-diamonds-visual-analysis",
        "visual": "eda", "featured": False,
    },
]


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    context = page_context(request)
    context["projects"] = PROJECTS
    context["featured_projects"] = [project for project in PROJECTS if project["featured"]]
    context["project_count"] = len(PROJECTS)
    context["services"] = [
        ("01", "SEO & search performance", "Technical SEO, local search, content optimization, and search-performance reporting."),
        ("02", "Marketing analytics", "Translate campaign and website data into dashboards, clear KPIs, and next-step recommendations."),
        ("03", "Data science prototypes", "Explore a business question with Python, SQL, exploratory analysis, and carefully evaluated ML models."),
        ("04", "Automation & AI experiments", "Prototype useful workflows and AI-enabled tools with a focus on measurable outcomes."),
    ]
    return templates.TemplateResponse(request=request, name="index.html", context=context)


@app.post("/contact")
def submit_contact(
    request: Request,
    name: str = Form(..., max_length=100),
    email: str = Form(..., max_length=254),
    topic: str = Form("General", max_length=120),
    message: str = Form(..., max_length=4000),
    website: str = Form("", max_length=200),
    submitted_csrf: str = Form(..., alias="csrf_token"),
    db: Session = Depends(get_db),
):
    if website.strip():
        return RedirectResponse("/thanks", status_code=status.HTTP_303_SEE_OTHER)
    if not allow_request(request):
        raise HTTPException(status_code=429, detail="Please refresh the page and try again.")
    if not valid_csrf(request, submitted_csrf):
        raise HTTPException(status_code=403, detail="Invalid session token. Refresh the page and try again.")
    try:
        name = clean_text(name, 100)
        topic = clean_text(topic or "General", 120)
        message = message.strip()
        if not message or len(message) > 4000:
            raise ValueError("Message must contain 1–4000 characters.")
        email = validate_email(email, check_deliverability=False).normalized
    except (ValueError, EmailNotValidError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    db.add(ContactMessage(name=name, email=email, topic=topic, message=message))
    db.commit()
    request.session["csrf_token"] = secrets.token_urlsafe(32)
    return RedirectResponse("/thanks", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/subscribe")
def subscribe(
    request: Request,
    email: str = Form(..., max_length=254),
    submitted_csrf: str = Form(..., alias="csrf_token"),
    db: Session = Depends(get_db),
):
    if not allow_request(request, limit=5):
        raise HTTPException(status_code=429, detail="Please refresh the page and try again.")
    if not valid_csrf(request, submitted_csrf):
        raise HTTPException(status_code=403, detail="Invalid session token. Refresh the page and try again.")
    try:
        email = validate_email(email, check_deliverability=False).normalized
    except EmailNotValidError as exc:
        raise HTTPException(status_code=422, detail="Enter a valid email address.") from exc
    db.add(Subscriber(email=email))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
    request.session["csrf_token"] = secrets.token_urlsafe(32)
    return RedirectResponse("/thanks?subscribed=1", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/thanks", response_class=HTMLResponse)
def thanks(request: Request):
    context = page_context(request)
    context["subscribed"] = request.query_params.get("subscribed") == "1"
    return templates.TemplateResponse(request=request, name="thanks.html", context=context)


@app.get("/privacy", response_class=HTMLResponse)
def privacy(request: Request):
    return templates.TemplateResponse(request=request, name="privacy.html", context=page_context(request))


@app.get("/robots.txt", response_class=PlainTextResponse)
def robots(request: Request):
    base = public_base_url(request)
    return f"User-agent: *\nAllow: /\nDisallow: /admin\nSitemap: {base}/sitemap.xml\n"


@app.get("/sitemap.xml")
def sitemap(request: Request):
    base = public_base_url(request)
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f'<url><loc>{xml_escape(base)}/</loc></url>'
        '</urlset>'
    )
    return Response(content=xml, media_type="application/xml")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/admin", response_class=HTMLResponse)
def admin(request: Request, db: Session = Depends(get_db)):
    context = page_context(request)
    if not request.session.get("admin_authenticated"):
        context["authenticated"] = False
        return templates.TemplateResponse(request=request, name="admin.html", context=context)
    context["authenticated"] = True
    context["messages"] = db.scalars(select(ContactMessage).order_by(ContactMessage.id.desc()).limit(100)).all()
    context["subscribers"] = db.scalars(select(Subscriber).order_by(Subscriber.id.desc()).limit(500)).all()
    return templates.TemplateResponse(request=request, name="admin.html", context=context)


@app.post("/admin/login")
def admin_login(
    request: Request,
    password: str = Form(...),
    submitted_csrf: str = Form(..., alias="csrf_token"),
):
    if not allow_request(request, limit=5):
        raise HTTPException(status_code=429, detail="Please wait and try again.")
    if not valid_csrf(request, submitted_csrf):
        raise HTTPException(status_code=403, detail="Invalid session token. Refresh the page and try again.")
    if not secrets.compare_digest(password, settings.admin_password):
        raise HTTPException(status_code=401, detail="Incorrect password.")
    # Rotate the CSRF token on privilege change to reduce session-fixation risk.
    request.session.pop("admin_authenticated", None)
    request.session["csrf_token"] = secrets.token_urlsafe(32)
    request.session["admin_authenticated"] = True
    return RedirectResponse("/admin", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/admin/logout")
def admin_logout(request: Request, submitted_csrf: str = Form(..., alias="csrf_token")):
    if not valid_csrf(request, submitted_csrf):
        raise HTTPException(status_code=400, detail="Invalid session token.")
    request.session.pop("admin_authenticated", None)
    request.session["csrf_token"] = secrets.token_urlsafe(32)
    return RedirectResponse("/admin", status_code=status.HTTP_303_SEE_OTHER)
