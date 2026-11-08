# FreightPilot AI deployment (Vercel + Render)

This repository is prepared for a split deployment: Vercel serves the Vite frontend; Render runs FastAPI, PostgreSQL and Redis-compatible rate-limit storage. Do not deploy the backend as a Vercel function.

## 1. Before deploying

1. Create a GitHub repository and push this project. Keep all `.env` files out of Git.
2. Create accounts with Render, Vercel, PayPal Developer, Google Cloud (OAuth Web Client), Apple Developer (Services ID and Sign in with Apple key), Resend, Twilio and an S3-compatible object-storage provider (Cloudflare R2 or AWS S3).
3. Verify a sending domain with Resend before sending real verification emails. Buy/configure a Twilio-capable sender and check destination-country A2P/registration requirements.
4. Create a private S3 bucket. For Cloudflare R2, create an S3 API token and use the account endpoint `https://<account-id>.r2.cloudflarestorage.com`, region `auto`. For AWS S3, use a least-privilege IAM user/policy and set the AWS region; leave `S3_ENDPOINT_URL` empty.
5. Configure a ClamAV TCP daemon reachable from the Render web service on port 3310. The application intentionally quarantines files and blocks downloads when scanning is unavailable. Never disable this safeguard to make documents downloadable.

## 2. Deploy backend and data stores to Render

1. In Render, choose **New → Blueprint**, connect the GitHub repository and use its root `render.yaml`.
2. The blueprint creates the FastAPI web service, PostgreSQL and Redis-compatible Key Value service in Singapore. The web service uses a pre-deploy Alembic migration command.
3. Enter the requested secrets in Render, including `GOOGLE_CLIENT_ID`, `APPLE_CLIENT_ID`, `APPLE_TEAM_ID`, `APPLE_KEY_ID`, `APPLE_PRIVATE_KEY` and `APPLE_REDIRECT_URI` when enabling those providers. The blueprint generates `JWT_SECRET_KEY`; keep it private and do not rotate it without planning token invalidation.
4. Set `FRONTEND_ORIGIN` to the exact Vercel HTTPS origin after Vercel creates it, e.g. `https://your-app.vercel.app` (no trailing slash). Set `API_PUBLIC_URL` to the Render API URL, e.g. `https://freightpilot-api.onrender.com`.
5. Set `CLAMAV_HOST` to the private hostname of your ClamAV service. Keep `CLAMAV_PORT=3310`.
6. Confirm `GET /health` returns 200 and `GET /health/ready` returns 200. The API intentionally hides interactive docs in production.
7. Before the first real users, create the first administrator using the Render shell from `backend/`: `python -m app.cli create-admin --email admin@yourdomain.com`. Use a unique long password. Public registration cannot create an admin.

**Render plan note:** the blueprint selects the smallest non-free API and PostgreSQL plans and a small Key Value plan so pre-deploy migrations and persistent PostgreSQL are available. Render pricing changes; check current billing before approving resources. The plans are a minimum deployment baseline, not a high-availability production architecture.

## 3. Deploy frontend to Vercel

1. In Vercel, import the GitHub repository.
2. Set **Root Directory** to `frontend`. Framework: Vite. Build command: `npm run build`. Output directory: `dist`. The included `frontend/vercel.json` has SPA rewrites and baseline response headers.
3. Add these Vercel environment variables for Production (and Preview only if the preview API is isolated):
   - `VITE_API_BASE_URL=https://<your-render-api>.onrender.com`
   - `VITE_PAYPAL_CLIENT_ID=<the same PayPal sandbox/live Client ID selected for the backend>`
   - `VITE_GOOGLE_CLIENT_ID=<the same Google Web Client ID configured on Render>`
   - `VITE_APPLE_CLIENT_ID=<Apple Services ID>`
   - `VITE_APPLE_REDIRECT_URI=<the exact HTTPS Return URL registered with Apple>`
4. Deploy and copy the exact HTTPS Vercel origin into Render's `FRONTEND_ORIGIN`. Redeploy the backend after changing it.

## 4. PayPal setup

1. Start with `PAYPAL_ENV=sandbox`. In PayPal Developer Dashboard → Apps & Credentials, create/select a REST app and copy its sandbox Client ID and Secret into Render (`PAYPAL_CLIENT_ID`, `PAYPAL_CLIENT_SECRET`).
2. After the Render API is deployed, add a webhook to that app with listener URL `https://<your-render-api>.onrender.com/api/webhooks/paypal`. Subscribe at least to `PAYMENT.CAPTURE.COMPLETED`, `PAYMENT.CAPTURE.DENIED`, and `PAYMENT.CAPTURE.REFUNDED`; add other events only when implemented. Copy its Webhook ID into Render as `PAYPAL_WEBHOOK_ID` and redeploy.
3. Configure `VITE_PAYPAL_CLIENT_ID` in Vercel to match the backend Client ID. Never put the PayPal Secret in a `VITE_` variable.
4. Complete end-to-end sandbox payment, webhook retry/duplicate, and refund tests. Only then consider `PAYPAL_ENV=live`, using credentials and webhook created under the live environment and an eligible PayPal Business account.

## 5. First production checklist

- `APP_ENV=production`, `DEMO_MODE=false`, `AUTO_CREATE_DB=false`, `AUTH_REQUIRED=true`, `RATE_LIMIT_ENABLED=true`.
- PostgreSQL and Redis are connected; Alembic revision is `0004_oauth_identities`.
- Resend domain is verified; send test email and verify delivery.
- Google and Apple sign-in complete with the configured origins/Services ID/Return URL; Twilio can send a test OTP to the required destination countries; use a scoped API Key SID/Secret (not the master Auth Token), and enforce spend and rate limits in Twilio.
- Object-storage bucket is private; no public read policy; bucket access key has only required object read/write/delete scope.
- ClamAV is healthy; test clean, malformed and EICAR test files; only clean files can be downloaded.
- First admin created through CLI; seller approval tested; buyer/seller/admin isolation tested.
- PayPal webhook signature is verified and events reach the endpoint; sandbox capture and refund reconciliation tested.
- Add monitoring, alerting, backup/restore tests, legal/privacy notices, terms, retention/deletion policy and incident-response contacts before real transactions.

## 6. Important limitations

- Live freight carrier booking/rates/tracking require carrier-specific contracts, sandbox access, schemas and API credentials. No carrier provider can be enabled just by entering a generic key. The adapter registry fails closed rather than returning fabricated live results.
- A complete seller payout/escrow/dispute product is not implemented. The current settlement data is an internal ledger; it is not proof of payout. Provider-side refunds are admin-only until a formal buyer refund request and approval workflow is built.
- Google sign-in, Apple web sign-in (authorization-code exchange) and SMS OTP login are implemented. They remain unavailable until provider credentials, registered origins/Return URLs and SMS delivery settings are configured.
- Email verification is still completed through the configured email delivery flow. The frontend now collects an optional buyer phone number, requires the seller contact phone, and provides account settings to add/verify a phone number. SMS sign-in requires an existing account with a unique E.164 phone number (for example `+919876543210`).
- The current AI risk engine is an explainable rules engine, not a trained fraud model. Freight rate values are not a live market feed or statistically validated market prediction.
- Render filesystem storage is not used for production business documents; production requires S3-compatible storage. Documents remain quarantined until ClamAV is reachable.
- This is a hardened deployable MVP baseline, not a security certification or high-availability enterprise platform. Arrange an independent penetration test and provider/legal review before processing real payments or regulated cargo.
