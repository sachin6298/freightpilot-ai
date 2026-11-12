# FreightPilot AI deployment and local runbook

## Supported runtimes

- Python 3.12.x (`backend/requirements.txt`)
- Node.js 24.13.0 (`.node-version`, `.nvmrc`) and npm 11+

## Local development (Windows PowerShell)

Backend terminal, from repository root:

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
Copy-Item .env.example .env  # only if backend/.env does not already exist
python -m pip install -r requirements-dev.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend terminal, from repository root:

```powershell
cd frontend
Copy-Item .env.example .env.local  # only if frontend/.env.local does not already exist
npm ci
npm run typecheck
npm run build
npm run dev
```

Set `VITE_API_BASE_URL=http://127.0.0.1:8000` in `frontend/.env.local` for local work. Restart Vite after changing any `VITE_*` variable. The frontend must not point to the Render hostname when the local backend is intended.

## Render Blueprint

The Blueprint service name is `freightpilot-backend`; the frontend static site obtains its API URL from that service's Render URL. If an existing Render service has a different name or custom URL, reconcile the Blueprint with the existing service before applying it—do not deploy a duplicate backend accidentally.

The backend readiness probe is `/health/ready`, which checks the database and (in production) Redis. The liveness probe `/health` intentionally does not check dependencies.

Production requires PostgreSQL and `STORAGE_BACKEND=postgresql`; document bytes are stored in the database. Do not set S3 as the production storage backend unless the application storage implementation and production validation are deliberately changed together.

Set `FRONTEND_ORIGIN` to the exact HTTPS frontend origin. Add additional exact HTTPS origins to `CORS_ALLOWED_ORIGINS` as comma-separated values. Never use `*` with credentialed CORS.

## Troubleshooting API connection errors

1. Check the API base displayed in the app Settings page.
2. For local frontend, it must be `http://127.0.0.1:8000` or `http://localhost:8000`.
3. Open `/health` and `/health/ready` on that exact host.
4. Confirm the backend terminal is running and not reporting startup errors.
5. If browser console reports CORS, set `FRONTEND_ORIGIN` to the exact origin shown in the browser address bar and restart FastAPI.
6. In production, verify the actual Render service URL and use that exact URL in the frontend environment. Changing Vite variables requires a new frontend build/deploy.
