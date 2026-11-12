# FreightPilot AI

**AI-assisted freight procurement, explainable quote-risk review and PayPal Sandbox checkout.**

The application is a React + TypeScript + Vite frontend backed by a FastAPI modular monolith and SQLAlchemy persistence. It is currently configured as a local Sandbox/demo application. Synthetic quotes and unavailable live integrations are explicitly identified in the UI.

## Current application capabilities

- Overview with database-backed shipment, quote, risk and captured-payment metrics.
- Shipment register, shipment creation, lifecycle status, manual tracking timeline and cancellation.
- Freight quote comparison with fee breakdown, provenance, quote validity and risk assessments.
- Dedicated risk review page using the backend's versioned rule-based assessment engine.
- AI Copilot comparison using stored shipment and quote IDs; the result is structured procurement decision support.
- Payment history read from the shipment payment endpoints.
- PayPal JavaScript SDK Sandbox checkout calling backend order-creation and capture-verification routes.
- Analytics grouped by shipment status, carrier and currency. Monetary values are never combined across currencies.
- Email/password buyer and seller registration and login.
- Google sign-in using server-verified Google ID tokens; Apple Sign in with Apple using server-side authorization-code exchange and ID-token verification.
- SMS one-time-code sign-in for existing accounts with a unique registered phone number, plus an account-settings flow to add and verify a phone number.
- Bearer-token session handling; the local demo can still run as Guest while `AUTH_REQUIRED=false`.
- Settings and service configuration visibility without exposing secrets.

## Repository layout

```text
FreightPilot_AI/
├── backend/
│   ├── app/
│   │   ├── core/             # Auth, ownership, audit helpers
│   │   ├── db/               # SQLAlchemy models, seed and migration helper
│   │   ├── routes/           # Auth, shipments, tracking, quotes, risk, copilot, payments, analytics
│   │   └── services/         # PayPal, carrier adapter registry, risk and AI services
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/       # Shipment form and PayPal checkout
│   │   ├── App.tsx           # Multi-page FreightPilot workspace
│   │   ├── api.ts            # Typed backend API client
│   │   ├── types.ts          # API/domain types
│   │   └── index.css         # Responsive product design system
│   ├── package.json
│   ├── package-lock.json
│   └── .env.example
├── docs/
├── AGENT_RULES.md
└── README.md
```

## Requirements

- Python 3.12.x
- Node.js 24.12.0 or newer within Node 24, and npm 11 or newer
- PayPal Developer Sandbox app credentials for checkout
- Optional Google OAuth client ID, Apple Developer Services ID/key, and Twilio SMS credentials for external sign-in providers
- Optional AI provider credentials for externally hosted AI analysis

## Run locally on Windows PowerShell

### 1. Backend

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Create `backend/.env` by copying `backend/.env.example` if it does not exist. Keep `DEMO_MODE=true`, `PAYPAL_ENV=sandbox`, and `AUTH_REQUIRED=false` for a local demo. Set a unique `JWT_SECRET_KEY`. The Google client ID belongs in this file. Apple also needs its Team ID, Key ID, `.p8` private key and exact HTTPS Return URL. PayPal, email, SMS and AI credentials remain server-side.

Initialize or upgrade the local database:

```powershell
python -m app.db.migrate
```

Run automated backend tests:

```powershell
pytest -q
```

Start FastAPI:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- Health: <http://127.0.0.1:8000/health>
- Interactive API docs: <http://127.0.0.1:8000/docs>

### 2. Frontend (a second terminal)

```powershell
cd frontend
npm ci
```

Create `frontend/.env.local` by copying `frontend/.env.example` if it does not exist:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_PAYPAL_CLIENT_ID=
VITE_GOOGLE_CLIENT_ID=
VITE_APPLE_CLIENT_ID=
VITE_APPLE_REDIRECT_URI=
```

Only public client identifiers belong in Vite variables. Never put a Google client secret, Apple `.p8` private key, PayPal Secret, Twilio key or any backend secret in the frontend. Apple requires a registered HTTPS Return URL; localhost is not accepted for Apple web sign-in.

Build and run:

```powershell
npm run typecheck
npm run build
npm run dev
```

Open <http://localhost:5173>.

## PayPal Sandbox checkout

1. Create a Sandbox REST app in the PayPal Developer Dashboard.
2. Put the Sandbox Client ID in `frontend/.env.local` and the Sandbox Client ID and Secret in `backend/.env`.
3. Restart both Vite and FastAPI after changing environment files.
4. Open Freight quotes, select an unexpired quote and choose **Continue to payment**.
5. Complete the approval using a PayPal Sandbox personal test account.
6. The frontend sends the approved order ID to FastAPI. FastAPI retrieves/verifies the order and confirms the capture before the payment record is marked captured.
7. The payment appears in the Payments transaction ledger.

Webhook verification requires a publicly reachable HTTPS callback (or a secure development tunnel) and the matching PayPal Sandbox webhook ID. `http://localhost` is not reachable by PayPal from its servers.

## Data and integration boundaries

- Local storage uses SQLite at `backend/freightpilot.db` by default. Do not delete this file if its records must be retained.
- Analytics and payment history are database-backed. Payment history is retrieved from the shipment-level payment API because the current backend does not expose a global payment-list endpoint.
- The current carrier registry contains no provider-specific live adapter unless one has been configured. The UI does not fabricate live carrier offers; existing seeded offers are marked `SYNTHETIC_DEMO`.
- Shipment tracking events entered in the UI are manual updates. No live carrier tracking feed is claimed.
- Risk scores come from the backend's explainable rule-based engine. They are not represented as a trained ML model.
- Copilot compares saved quote records. It is advisory and cannot execute a payment or change a shipment.
- For deployment, use PostgreSQL with migrations, HTTPS, a strong JWT secret, `AUTH_REQUIRED=true`, `DEMO_MODE=false`, production provider credentials, and a publicly reachable webhook URL. Do not expose the local demo configuration publicly.

## API areas used by the frontend

`/health`, `/api/auth/*`, `/api/shipments`, `/api/shipments/{id}/quotes`, `/api/shipments/{id}/estimate`, `/api/shipments/{id}/tracking`, `/api/quotes/{id}/assess`, `/api/copilot/compare`, `/api/payments/*`, `/api/shipments/{id}/payments`, `/api/analytics/*`, `/api/carriers`, `/api/notifications` and `/api/demo/reset`.


## Hardened deployment package

The current release includes production-mode safeguards, security-focused backend changes, private S3-compatible document storage, Render Blueprint configuration, Vercel SPA configuration and GitHub CI. Read **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)** before deploying, and **[docs/SECURITY.md](docs/SECURITY.md)** for implemented controls and remaining security work. The deployment is not fully operational until you add provider credentials, configure ClamAV, create the initial administrator, and complete the frontend verification experience.


Provider credential setup and exact environment-variable mapping: [docs/PROVIDER_CREDENTIALS.md](docs/PROVIDER_CREDENTIALS.md).
