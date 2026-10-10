# Alok Agarwal — Motion Portfolio

A professional, responsive portfolio for a hybrid profile: SEO & digital marketing + data analytics + data science / AI-ML projects.

## Features

- Dark, high-contrast design with lime/cyan accents
- CSS animated data visualization, orbital rings, marquee, pulse, floating UI, and ambient pointer-reactive lighting
- Type-and-delete headline, animated color sweep, scroll progress, reveal-on-scroll, and interactive project-card highlights
- Native keyboard-accessible FAQ accordion with animated answers
- Reduced-motion accessibility support
- Project URLs matched to repository names in the connected GitHub account
- Curated project gallery with accessible Show all projects interaction
- Service-oriented collaboration section for SEO analytics, Python prototypes, and opportunities
- FastAPI + Jinja2 backend, SQLite contact form and admin inbox
- CSRF token checks, session/CSRF rotation on admin login, basic in-memory rate limiting, browser security headers, and environment-based configuration
- SEO description, Open Graph/Twitter metadata, Person structured data, `robots.txt`, a sitemap endpoint, privacy notice, and keyboard skip link
- Dockerfile and tests

## Run in VS Code (Windows PowerShell)

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
Copy-Item .env.example .env
python -m uvicorn app.main:app --reload
```

Visit http://127.0.0.1:8000. API docs: http://127.0.0.1:8000/docs

## macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
python -m uvicorn app.main:app --reload
```

## Important customization

1. Edit `.env` to confirm `CONTACT_EMAIL` and `CONTACT_PHONE` are the contact details you want visitors to see. These are prefilled with the details supplied for this portfolio.
2. Set `SITE_URL` to the canonical origin. For production this must be the real public `https://` URL.
3. Check project and live-demo links in `app/main.py` before launch. Project descriptions are intentionally conservative and avoid unverified performance claims.
4. Set a strong unique `ADMIN_PASSWORD` and `SESSION_SECRET`.
5. Update LinkedIn/GitHub links if your preferred public URLs change.
6. Review and customize the included privacy notice to match the actual hosting and data-retention setup before accepting real leads.
7. Configure real checkout links before advertising paid services or products.

## Monetization

The contact form can capture consulting and freelance leads in SQLite. A hidden honeypot field adds basic bot filtering. To monetize, add a real booking link, paid digital product checkout, or clearly disclosed affiliate links. This starter does not process card details, send email notifications, or deliver newsletter campaigns. Use a payment provider for checkout and configure email delivery separately.

## Security and production notes

- The included rate limiter is process-local, not distributed.
- Admin login is a minimal single-admin starter, not production-grade identity management; login attempts are rate-limited per process. Consider an established identity provider or VPN-protected admin path for a high-value inbox.
- Production startup refuses a short/default admin password, a short/default session secret, a placeholder contact email, or disabled HTTPS-only cookies.
- Use HTTPS, a long random session secret, a strong admin password, backups, monitoring, and persistent storage.
- Set `SITE_URL` to the canonical public HTTPS origin in production; production mode disables the interactive API docs and refuses to start with a non-HTTPS or placeholder site URL.
- SQLite is appropriate for local development or a single instance with a mounted persistent disk. Free web hosts commonly use disposable filesystems, so set `DATABASE_URL` to a managed PostgreSQL database for persistent contact and subscriber records. PostgreSQL URLs using `postgres://` or `postgresql://` are normalized to the bundled psycopg 3 driver.
- Do not commit `.env`, secrets, or customer data.

### Deployment entry point

The included `Procfile` starts the ASGI application on the hosting platform's `$PORT`. Configure `APP_ENV=production`, `HTTPS_ONLY=true`, a canonical HTTPS `SITE_URL`, a real `CONTACT_EMAIL`, unique strong `ADMIN_PASSWORD` and `SESSION_SECRET` values, and a persistent PostgreSQL `DATABASE_URL` in the provider's secret manager. This project is prepared for deployment but is not connected to a hosting account or deployed yet.

### Docker

The image runs as a non-root user, excludes local secrets through `.dockerignore`, and stores SQLite data under `/data`. Mount a persistent volume at `/data` and provide production environment variables (`APP_ENV=production`, `SITE_URL`, `CONTACT_EMAIL`, `ADMIN_PASSWORD`, `SESSION_SECRET`, and `HTTPS_ONLY=true`) through your hosting platform's secret/configuration manager. Terminate HTTPS at a trusted reverse proxy or hosting platform.

## Test

```bash
pip install -r requirements-dev.txt
python -m pytest -q
```

## Final launch checklist

- [ ] Set a real `CONTACT_EMAIL` and verify all external profile/project links.
- [ ] Replace default `ADMIN_PASSWORD` and `SESSION_SECRET` with unique secrets.
- [ ] Set `APP_ENV=production` and `HTTPS_ONLY=true` behind HTTPS.
- [ ] Configure a managed PostgreSQL `DATABASE_URL` (or mount persistent storage for SQLite) and backups.
- [ ] Review the included privacy notice and test contact-form storage; configure email delivery separately if required.
- [ ] Test the live site on mobile and keyboard-only navigation.
- [ ] Verify project descriptions and any claims against the repositories before publishing.

## Profile accuracy and project links

The current role summary focuses on SEO/search strategy, marketing analytics, and junior data analysis. Work history, education, and certifications are omitted until verified details are supplied. Previously displayed campaign metrics and credential claims were removed because their source evidence was not available for independent verification.

All eight linked GitHub repositories returned successfully when checked. The two previously listed Streamlit demos redirected to sign-in and are therefore not presented as public live demos; the portfolio notes that status and keeps the source-repository links available. Recheck hosted links before launch, since service availability can change.


### Profile photo

The homepage portrait is stored at `app/static/images/alok-agarwal.jpg`. Replace that file to update the photo while keeping the same path, or update the image URL in `app/templates/index.html`.


## Launch readiness

- The unverified resume draft is retained locally at `app/documents/alok-agarwal-resume-draft.pdf`, excluded from Git and Docker, and not publicly served. Add a revised, verified resume before restoring a download link.
- Production launch checks: see [`DEPLOYMENT_CHECKLIST.md`](DEPLOYMENT_CHECKLIST.md).
- Run tests with `python -m pytest -q` after installing `requirements-dev.txt`.


## Portfolio upgrade features

- **Project discovery filters** for SEO/AI, analytics, machine learning, and engineering. Filters work locally in the browser and support keyboard-accessible buttons.
- **Recruiter and client quick answers** with curated, profile-grounded responses. This is a lightweight offline guide—not a generative AI model—and it does not send questions to an external service or require an API key.
- **Job and client conversion paths** through the existing resume download, project case studies, service descriptions, and contact form.
- **No product or booking link is published.** The contact form is the current contact path; add a real destination before advertising a booking or paid product.
- **Reduced-motion support** and responsive layouts remain in place.

## Recommended launch checks

1. Recheck all repository and live-demo links before sharing the site publicly.
2. Add verified employment dates, education, and credentials if you want those sections published; do not add unverified claims.
3. Use a persistent database or managed PostgreSQL if deploying to a host with an ephemeral filesystem.
4. Configure a unique production `SESSION_SECRET`, strong `ADMIN_PASSWORD`, real `SITE_URL`, and `HTTPS_ONLY=true`.
5. Test contact submissions and admin access on the deployed site.
