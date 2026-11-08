# FreightPilot AI provider credentials

Use separate credentials for development, staging and production. Keep every secret in the Render Environment dashboard. Do not commit secrets, paste them into `VITE_*` variables, or put them in GitHub source files.


## 1. Google sign-in (optional OAuth provider)

1. Open [Google Cloud Console](https://console.cloud.google.com/apis/credentials).
2. Configure the OAuth consent screen for your app.
3. Create an OAuth Client ID of type **Web application**.
4. Add your local origin (for example `http://localhost:5173`) and your production Vercel domain under **Authorized JavaScript origins**.
5. Use the same Client ID in both places:
   - Render API: `GOOGLE_CLIENT_ID`
   - Vercel frontend: `VITE_GOOGLE_CLIENT_ID`
6. For local development, put the same value in `backend/.env` and `frontend/.env.local`.

The browser sends the Google ID token to the API. The API verifies the signature using Google's published signing keys, checks issuer, audience, expiry and nonce, and only then creates/links a buyer account. Never put a Google client secret in the frontend; this implementation uses the ID-token credential and does not require a browser-visible secret.

## 2. Apple Sign in with Apple (optional OAuth provider)

Apple web sign-in requires an Apple Developer account, a Services ID, a registered HTTPS domain/Return URL, and a server-side client secret.

1. Enrol in the [Apple Developer Program](https://developer.apple.com/programs/).
2. In **Certificates, Identifiers & Profiles**, create or configure a primary App ID and enable **Sign in with Apple**.
3. Create a **Services ID** and associate it with the primary App ID.
4. In the Services ID configuration, add your production website domain and the exact HTTPS Return URL. Apple does not accept `localhost`, an IP address, or a URL with a fragment as the registered web Return URL. Use a deployed HTTPS domain or a suitable HTTPS development tunnel when testing.
5. Use the Services ID value as:
   - Render API: `APPLE_CLIENT_ID`
   - Vercel frontend: `VITE_APPLE_CLIENT_ID`
6. Create a Sign in with Apple **Key** in the Apple Developer portal and record its Key ID and the Team ID.
7. Add the following server-only values to Render:
   - `APPLE_TEAM_ID`
   - `APPLE_KEY_ID`
   - `APPLE_PRIVATE_KEY` (the `.p8` private-key contents; encode newlines as `\\n` if entering it as one environment-variable line)
   - `APPLE_REDIRECT_URI` (exactly the same URL registered with Apple)
8. Add these browser-safe values to Vercel:
   - `VITE_APPLE_CLIENT_ID`
   - `VITE_APPLE_REDIRECT_URI` (must exactly match the backend value and Apple Return URL)

The browser sends Apple's one-time authorization code to the API. The API creates a short-lived ES256 client secret, exchanges the code at Apple's token endpoint, then validates the returned ID token's signature, issuer, audience, expiry and nonce using Apple's published signing keys. The Apple private key is never exposed to the browser. See Apple's [web sign-in configuration](https://developer.apple.com/documentation/signinwithapple/configuring-your-webpage-for-sign-in-with-apple) and [identity verification guidance](https://developer.apple.com/documentation/signinwithapple/verifying-a-user).


## 3. Phone sign-in using SMS OTP

Phone sign-in is a one-time-code login method (not OAuth). It only works for an existing FreightPilot account that has a unique phone number registered in E.164 format, for example `+919876543210`.

- Local development: `SMS_PROVIDER=console`; the generated code is logged in the backend terminal.
- Production: configure Twilio using the `SMS_PROVIDER`, Account SID, scoped API key SID/Secret and approved sender number fields described below.
- Codes expire after 10 minutes, are hashed at rest, and are limited to five verification attempts. The request endpoint does not disclose whether a number belongs to an account.

## 4. PayPal Checkout (required for payments)

1. Open the [PayPal Developer Dashboard](https://developer.paypal.com/dashboard/applications).
2. Go to **Apps & Credentials** and create a REST app in **Sandbox** first.
3. Copy its **Client ID** and **Secret**.
4. Add these to the Render API service:
   - `PAYPAL_ENV=sandbox`
   - `PAYPAL_CLIENT_ID`
   - `PAYPAL_CLIENT_SECRET`
5. After the Render API is deployed, create a webhook for `https://<render-api-host>/api/webhooks/paypal`. Subscribe to `PAYMENT.CAPTURE.COMPLETED`, `PAYMENT.CAPTURE.DENIED`, and `PAYMENT.CAPTURE.REFUNDED`.
6. Copy the generated **Webhook ID** into Render as `PAYPAL_WEBHOOK_ID` and redeploy. PayPal uses this ID when verifying webhook messages.
7. Add the same **Client ID only** to Vercel as `VITE_PAYPAL_CLIENT_ID`. Never expose the Secret in the browser.

Do not switch `PAYPAL_ENV=live` until the full Sandbox checkout, duplicate webhook, refund, and reconciliation tests pass and the live merchant account is approved.

## 5. Transactional email (required for production verification)

1. Create a [Resend account](https://resend.com/).
2. Add a domain you control and complete the SPF/DKIM DNS verification shown in the Resend dashboard.
3. In **API Keys**, create a key with **Sending access**, restricted to the verified sending domain.
4. Add to Render:
   - `EMAIL_PROVIDER=resend`
   - `RESEND_API_KEY`
   - `EMAIL_FROM=FreightPilot <no-reply@your-verified-domain>`

Do not use `example.com`, an unverified sender domain, or a full-access API key when sending-only access is sufficient.

## 6. SMS verification for account verification (required for production phone OTP)

1. Create a [Twilio account](https://www.twilio.com/).
2. In **Console → Account Info**, copy the **Account SID**.
3. In **Console → API Keys & Tokens**, create a **Standard API Key** and copy its SID and Secret immediately.
4. Obtain an SMS-capable Twilio sender number (or approved sender for your destination countries).
5. Add to Render:
   - `SMS_PROVIDER=twilio`
   - `TWILIO_ACCOUNT_SID`
   - `TWILIO_API_KEY_SID`
   - `TWILIO_API_KEY_SECRET`
   - `TWILIO_FROM_NUMBER` (E.164 format, e.g. `+15005550006`)

The application uses the scoped API Key SID/Secret for HTTP Basic authentication and the Account SID in the Messages API path. The account master Auth Token is not required in production. Confirm sender eligibility and country-specific messaging registration with Twilio before launch.

## 7. Private document storage (required for production uploads)

Cloudflare R2 is the configured S3-compatible option:

1. Open the [Cloudflare Dashboard](https://dash.cloudflare.com/) and go to **Storage & databases → R2 → Overview**.
2. Create a private bucket for FreightPilot documents.
3. Under **Manage R2 API Tokens**, create an API token with **Object Read & Write** permission scoped only to that bucket.
4. Copy the Access Key ID and Secret Access Key immediately.
5. Add to Render:
   - `STORAGE_BACKEND=s3`
   - `S3_BUCKET=<bucket-name>`
   - `S3_REGION=auto`
   - `S3_ENDPOINT_URL=https://<account-id>.r2.cloudflarestorage.com`
   - `AWS_ACCESS_KEY_ID=<R2 Access Key ID>`
   - `AWS_SECRET_ACCESS_KEY=<R2 Secret Access Key>`

Keep the bucket private. Do not enable public object access. The API checks owner/admin permissions before downloads. Files remain quarantined until ClamAV confirms they are clean.

AWS S3 can be used instead: create a least-privilege IAM identity for one bucket, set `S3_REGION` to the AWS region and leave `S3_ENDPOINT_URL` empty.

## 8. AI copilot (optional)

1. Open [Google AI Studio API keys](https://aistudio.google.com/app/apikey).
2. Create a Gemini API key for a dedicated project and apply available project/API restrictions and billing limits.
3. Add to Render:
   - `AI_PROVIDER=gemini`
   - `AI_API_KEY`
   - `AI_MODEL=gemini-2.5-flash`

The key belongs only on the backend. Never use a `VITE_` variable for it. If no key is configured in local development, the application can use its deterministic fallback; production AI features should be tested with the chosen model and account limits.

## 9. Values generated or supplied by hosting

These are not third-party API keys that you need to create manually:

| Variable | Where it comes from |
|---|---|
| `JWT_SECRET_KEY` | Generated automatically by the included Render Blueprint (256-bit random value) |
| `DATABASE_URL` | Render PostgreSQL private connection string, automatically injected by the Blueprint |
| `REDIS_URL` | Render Key Value private connection string, automatically injected by the Blueprint |
| `API_PUBLIC_URL` | Set to the deployed Render API HTTPS URL |
| `FRONTEND_ORIGIN` | Set to the deployed Vercel HTTPS origin, without a trailing slash |
| `CLAMAV_HOST` | Private hostname of a reachable ClamAV daemon; this is not an API key |
| `CLAMAV_PORT` | ClamAV daemon port, normally `3310` |

The package includes a local ClamAV Docker Compose file for development. Production document downloads stay blocked while the production scanner is unreachable; configure a private scanner before using KYC or shipment document uploads.

## 10. Vercel browser-safe variables

Set only these in **Vercel → Project → Settings → Environment Variables**:

```dotenv
VITE_API_BASE_URL=https://<your-render-api-host>
VITE_GOOGLE_CLIENT_ID=<Google Web Client ID>
VITE_APPLE_CLIENT_ID=<Apple Services ID>
VITE_APPLE_REDIRECT_URI=https://<your-vercel-domain>/
VITE_PAYPAL_CLIENT_ID=<same PayPal Client ID configured on Render>
```

No `GOOGLE_CLIENT_SECRET`, `APPLE_PRIVATE_KEY`, `AI_API_KEY`, PayPal Secret, Resend key, Twilio key, database URL, Redis URL, JWT secret or R2 credentials belong in Vercel browser variables.

## 11. Integrations that still require separate engineering/provider access

This repository does not include a live carrier integration. Freight rate feeds, booking, cancellation and tracking require selecting a carrier/provider, commercial access, sandbox credentials and a provider-specific adapter. There is no generic carrier key to generate.

Google/Apple sign-in are implemented but require provider-console registration and credentials. Actual seller payout/disbursement, escrow, disputes and a buyer refund-request/approval workflow are not included in this release. Do not treat an internal settlement ledger as a completed payout.
