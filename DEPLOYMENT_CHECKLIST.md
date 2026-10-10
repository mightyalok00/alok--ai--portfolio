# Production launch checklist

## Before deployment
- Set `APP_ENV=production`, a strong unique `ADMIN_PASSWORD`, a random `SESSION_SECRET`, `SITE_URL` to the final HTTPS origin, `HTTPS_ONLY=true`, and `CONTACT_EMAIL`.
- Configure a managed PostgreSQL `DATABASE_URL` for hosts with ephemeral filesystems, or mount persistent storage for SQLite. Schedule backups and test restores.
- Restrict admin routes; use a long unique password and verify logout/session invalidation.
- Run `pip-audit` or an equivalent dependency scanner and review all findings.
- Run tests, build the Docker image, and verify the health check in a staging environment.
- Test the contact form with valid/invalid input, CSRF failures, spam honeypot, rate limits, and database write/read.
- Recheck repository links and any enabled public demos from a clean browser session; verify the resume only after its download link is restored.

## After deployment
- Confirm HTTPS, trusted host configuration, canonical URL, sitemap and robots.txt.
- Test at mobile and desktop breakpoints and with keyboard-only navigation.
- Check reduced-motion behavior, contrast, focus visibility, and image alt text.
- Run Lighthouse/PageSpeed and address major accessibility, SEO, and performance issues.
- Verify backup restoration and confirm secrets are not exposed in source control or logs.

## Profile accuracy
- The resume draft is excluded from public static files and Docker images until it is revised with verified details. Restore a download link only after reviewing the final document.
- Treat public LinkedIn campaign metrics as self-reported unless you have permission and source evidence to publish independently verified analytics.
