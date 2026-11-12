# FreightPilot AI — Backend

This backend upgrade extends the uploaded FreightPilot AI codebase. It is a **modular FastAPI monolith** using SQLAlchemy and SQLite by default, with optional PostgreSQL support.

## Implemented modules

- **Persistence:** SQLAlchemy models for users, shipments, quotes, risk assessments, PayPal payments, webhook events, shipment tracking, audit logs, notifications, and AI conversation snapshots.
- **Database startup/migration:** additive schema initializer that creates new tables and adds the compatibility columns required by the previous prototype. It preserves existing rows.
- **Authentication:** email registration/login, Argon2 password hashing, JWT bearer tokens, optional local-demo auth, and user-scoped shipment/payment access when authenticated.
- **Shipment workflow:** paginated listing, creation, editing, cancellation, status transitions, shipment estimates, and quote retrieval.
- **Tracking:** tracking event timeline and controlled status updates.
- **Quotes and risk:** saved quote comparisons and explainable deterministic risk assessments.
- **PayPal:** OAuth token caching, server-side order creation, server-side capture, amount/currency/reference verification, refunds, payment history, idempotency, webhook signature verification, webhook deduplication, and payment audit events.
- **Carrier adapter contract:** provider registry and normalized quote ingestion endpoint. No real carrier connector is configured because no carrier provider/API credentials were included in the supplied project.
- **Copilot:** persists comparison inputs and responses and exposes per-user history.
- **Operations:** database-backed overview/carrier analytics, notifications, and admin-only audit-log retrieval.

## Requirements

- Python 3.10+ (Python 3.12/3.13 are suitable)
- PayPal Developer Sandbox REST app credentials to perform an actual Sandbox checkout
- Optional: PostgreSQL and `psycopg` (already included in requirements) for hosted deployments

## Windows PowerShell setup

Run these commands from the project root:

```powershell
cd .\backend
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `backend/.env` and set at least:

```env
APP_ENV=development
DEMO_MODE=true
AUTO_CREATE_DB=true
DATABASE_URL=sqlite:///./freightpilot.db
FRONTEND_ORIGIN=http://localhost:5173
AUTH_REQUIRED=false
JWT_SECRET_KEY=replace_with_a_long_random_secret_at_least_32_chars
PAYPAL_ENV=sandbox
PAYPAL_CLIENT_ID=your_paypal_sandbox_client_id
PAYPAL_CLIENT_SECRET=your_paypal_sandbox_secret
PAYPAL_WEBHOOK_ID=your_sandbox_webhook_id
```

Start the API from the `backend` directory:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

API docs: `http://127.0.0.1:8000/docs`
Health endpoint: `http://127.0.0.1:8000/health`

If PowerShell blocks activation scripts, use this for the current terminal only, then activate the environment again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## Linux/macOS setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Database behavior

- By default, SQLite stores data in `backend/freightpilot.db` when the API is started from the `backend` directory.
- `AUTO_CREATE_DB=true` runs the additive initializer at startup. It creates missing tables and adds compatibility columns to the old prototype schema; it does not delete existing shipment, quote, or payment rows.
- The initializer can also be run explicitly from `backend`:

  ```powershell
  python -m app.db.migrate
  ```

- SQLite enables foreign-key checks, WAL mode, and a 5-second busy timeout.
- To use PostgreSQL, set `DATABASE_URL` to a SQLAlchemy PostgreSQL URL, for example `postgresql+psycopg://user:password@host:5432/freightpilot`. Use a fresh database for the cleanest deployment. Back up any existing database before upgrading.
- The included initializer is a compatibility bootstrapper, **not a full migration-history system**. For a production team workflow with many schema versions, adopt Alembic revision files before making repeated schema changes.

## PayPal Sandbox setup

1. Create a REST app in the PayPal Developer Dashboard and select Sandbox.
2. Copy its Sandbox Client ID and Secret into `PAYPAL_CLIENT_ID` and `PAYPAL_CLIENT_SECRET` in `backend/.env`.
3. Keep `DEMO_MODE=true` and `PAYPAL_ENV=sandbox` while testing.
4. Configure a publicly reachable HTTPS webhook URL ending in `/api/webhooks/paypal` in the same Sandbox REST app.
5. Subscribe at minimum to `PAYMENT.CAPTURE.COMPLETED`, `PAYMENT.CAPTURE.DENIED`, and `PAYMENT.CAPTURE.REFUNDED` events.
6. Copy that webhook's ID into `PAYPAL_WEBHOOK_ID`.
7. Use a PayPal Sandbox buyer account to approve the order. The backend then retrieves and captures the order; a browser approval alone is not treated as proof of payment.

The webhook handler verifies messages with PayPal's webhook signature verification endpoint before it stores or processes them. PayPal requires webhook listeners to be HTTPS-accessible and recommends returning a 2xx response to successful deliveries; duplicate deliveries are expected and this backend deduplicates by provider event ID. See the official PayPal docs:

- https://developer.paypal.com/api/rest/integration/orders-api
- https://developer.paypal.com/api/rest/webhooks/rest/
- https://developer.paypal.com/api/rest/webhooks

**Important:** This backend package does not add the PayPal JavaScript SDK or a checkout button to the React frontend. The frontend must call `POST /api/payments/create-order`, render the returned PayPal order ID through the PayPal JS SDK, then call `POST /api/payments/{payment_id}/capture` after approval. Until that frontend work is done, a user cannot complete checkout from the website UI.

## Authentication and deployment settings

Local demo defaults keep `AUTH_REQUIRED=false` so the existing demo frontend can continue to call the API without a bearer token. Public registration/login endpoints are available at `/api/auth/register` and `/api/auth/login`.

Before exposing the API to users:

```env
APP_ENV=production
DEMO_MODE=false
AUTH_REQUIRED=true
JWT_SECRET_KEY=<long-random-secret>
PAYPAL_ENV=live
```

Then use real PayPal Live credentials only after successful Sandbox testing. Do not commit `.env` or put `PAYPAL_CLIENT_SECRET` in frontend environment variables. Use HTTPS, restrictive CORS, backups, database migrations, log redaction, rate limiting, and operational monitoring in production. Admin access is granted by setting a trusted account's `users.role` to `ADMIN`; public registration cannot create an admin account.

Live payment creation rejects quotes whose `source_kind` is `SYNTHETIC_DEMO` or `DEMO`. A live carrier integration is still required before those offers can be treated as real commercial freight quotes.

## API route summary

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/auth/register` | Register a user and issue a token |
| POST | `/api/auth/login` | Login and issue a token |
| GET | `/api/auth/me` | Get current authenticated user |
| GET/POST | `/api/shipments` | List/create shipments |
| GET/PATCH | `/api/shipments/{shipment_id}` | Read/update shipment |
| POST | `/api/shipments/{shipment_id}/cancel` | Cancel eligible shipment |
| GET | `/api/shipments/{shipment_id}/estimate` | Get rate estimate |
| GET/POST | `/api/shipments/{shipment_id}/quotes` | List/create quotes |
| GET/POST | `/api/shipments/{shipment_id}/tracking` | Get/add tracking events |
| GET | `/api/quotes/{quote_id}` | Get a quote |
| POST | `/api/quotes/{quote_id}/assess` | Recalculate quote risk |
| POST | `/api/copilot/compare` | Run a quote comparison with Copilot |
| GET | `/api/copilot/history` | Read saved Copilot comparisons |
| POST | `/api/payments/create-order` | Create PayPal order from stored quote |
| POST | `/api/payments/{payment_id}/capture` | Verify and capture approved order |
| POST | `/api/payments/{payment_id}/refund` | Refund a captured payment |
| GET | `/api/payments/{payment_id}` | Get payment status |
| GET | `/api/shipments/{shipment_id}/payments` | List shipment payments |
| POST | `/api/webhooks/paypal` | Verify and process PayPal webhooks |
| GET | `/api/analytics/overview` | Get database-backed overview metrics |
| GET | `/api/analytics/carriers` | Aggregate quote history by carrier/currency |
| GET | `/api/notifications` | List notifications |
| POST | `/api/notifications/{notification_id}/read` | Mark notification as read |
| GET | `/api/admin/audit-logs` | Read audit trail (admin only) |
| GET | `/api/carriers` | List configured carrier adapters |
| POST | `/api/shipments/{shipment_id}/refresh-quotes` | Request quotes from a configured adapter |
| GET | `/health` | Health check |

Most shipment-related endpoints require a bearer token when `AUTH_REQUIRED=true`. The webhook endpoint uses PayPal signature verification rather than user JWT authentication.

## Tests

From the `backend` directory:

```powershell
python -m compileall -q app tests
pytest -q
```

The package was verified locally with **38 passing tests**. The tests mock external PayPal HTTP calls; they do not prove that your PayPal credentials, Sandbox buyer account, public webhook URL, or frontend checkout have been configured correctly. Run a real Sandbox transaction after adding your credentials and frontend SDK integration.

## Complexity notes

- Indexed entity lookups use database indexes; paginated list endpoints bound response memory by the requested page size.
- Quote comparison/risk calculation uses a single bulk quote fetch and a shared benchmark rather than issuing one query per quote (avoids an N+1 query pattern). The in-memory quote benchmark and risk pass are linear in the number of quotes, `O(n)` time and `O(n)` memory for the loaded quote set.
- Carrier aggregation and analytics are performed with SQL `GROUP BY`/aggregate queries rather than loading all quote rows into Python.
- PayPal access tokens are cached in-process with a lock to avoid an OAuth request on every payment API call. Provider network latency dominates payment request complexity.
- Argon2 password hashing deliberately consumes CPU and memory to increase the cost of offline password guessing; it is not optimized for minimum runtime.
