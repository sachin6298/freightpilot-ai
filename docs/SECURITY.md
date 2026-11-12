# Security and dependency verification

- Run `npm audit --audit-level=high` in `frontend/` after `npm ci`.
- Run `pip-audit -r backend/requirements.txt` in an environment with pip-audit installed and package index access.
- Do not blindly apply major dependency upgrades; review compatibility and rerun the frontend production build and backend tests.
- `VITE_*` variables are public at build time. Never put PayPal secrets, OAuth client secrets, Apple private keys, Firebase service-account JSON, or database credentials in them.
- Rotate any credential that has been committed or shared.
- Production must use HTTPS, explicit CORS origins, PostgreSQL, a strong generated JWT secret, `AUTH_REQUIRED=true`, `DEMO_MODE=false`, rate limiting with Redis, and provider credentials stored in Render's secret environment settings.
