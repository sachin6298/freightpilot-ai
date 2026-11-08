# Environment Variables and Local Setup

The archive includes safe placeholder files at `backend/.env` and `frontend/.env.local`. Edit these files locally. Never commit populated environment files.

## Backend `.env` (server-only)

```dotenv
APP_ENV=development
DEMO_MODE=true
DATABASE_URL=sqlite:///./freightpilot.db
FRONTEND_ORIGIN=http://localhost:5173
API_PUBLIC_URL=http://localhost:8000

GOOGLE_CLIENT_ID=
APPLE_CLIENT_ID=
APPLE_TEAM_ID=
APPLE_KEY_ID=
# Apple .p8 private-key contents; use escaped \\n line breaks when stored on one line.
APPLE_PRIVATE_KEY=
APPLE_REDIRECT_URI=

PAYPAL_ENV=sandbox
PAYPAL_CLIENT_ID=
PAYPAL_CLIENT_SECRET=
PAYPAL_WEBHOOK_ID=

SMS_PROVIDER=console
EMAIL_PROVIDER=console
AI_PROVIDER=gemini
AI_API_KEY=
AI_MODEL=gemini-2.5-flash
```

Google and Apple client IDs must match the corresponding browser values. Apple also requires its Team ID, Key ID, `.p8` private key and exact registered HTTPS Return URL. The Apple private key, PayPal Secret, Twilio credentials, AI API key, database credentials and JWT signing key are server-only.

## Frontend `.env.local` (browser-safe values only)

```dotenv
VITE_API_BASE_URL=http://localhost:8000
VITE_PAYPAL_CLIENT_ID=
VITE_GOOGLE_CLIENT_ID=
VITE_APPLE_CLIENT_ID=
VITE_APPLE_REDIRECT_URI=
```

Only public client identifiers belong in Vite variables. Do not put a provider secret, Apple `.p8` private key, Twilio key, database URL or JWT secret in the frontend. Apple web sign-in requires a registered HTTPS Return URL; localhost is not accepted.

## Installation outline

### Backend

```powershell
cd backend
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend

```powershell
cd frontend
npm ci
npm run dev
```

### Tests and migrations

```powershell
pip install -r requirements-dev.txt
pytest -q
alembic upgrade head
```

For full provider setup, see `docs/PROVIDER_CREDENTIALS.md` and `docs/DEPLOYMENT_ENV_CHECKLIST.md`.
