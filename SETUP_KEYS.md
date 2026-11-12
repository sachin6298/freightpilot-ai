# Where to paste API keys

Two files hold every value you need. Both are already created for local development.

- `backend/.env` for server secrets. Never prefix these with `VITE_`.
- `frontend/.env.local` for public identifiers only. Anything with `VITE_` ends up in the browser.

Leave a value empty and that feature falls back to a local or demo mode. The app runs without any keys.

## Backend: `backend/.env` (secret, server-only)

| Feature | Variable(s) to paste | Where to get it | Needed locally? |
|---|---|---|---|
| Local login/session | `JWT_SECRET_KEY` | Already generated. Replace with your own long random value before deploying. | Already set |
| Google sign-in | `GOOGLE_CLIENT_ID` | Google Cloud Console > OAuth client ID (same value as the frontend's `VITE_GOOGLE_CLIENT_ID`) | No |
| Apple sign-in | `APPLE_CLIENT_ID`, `APPLE_TEAM_ID`, `APPLE_KEY_ID`, `APPLE_PRIVATE_KEY`, `APPLE_REDIRECT_URI` | Apple Developer account. The `.p8` key goes in on one line with `\n` for newlines. Apple requires an HTTPS return URL, so localhost will not work. | No |
| PayPal checkout (Sandbox) | `PAYPAL_CLIENT_ID`, `PAYPAL_CLIENT_SECRET` | developer.paypal.com > Sandbox > App credentials | Yes, for checkout |
| AI copilot (Gemini) | `AI_API_KEY` | Google AI Studio | No, rules-based fallback is used |
| Verification email | `RESEND_API_KEY`, `EMAIL_FROM`, and set `EMAIL_PROVIDER=resend` | resend.com | No, emails print to the console |
| Phone (SMS) sign-in | `FIREBASE_PROJECT_ID`, `FIREBASE_SERVICE_ACCOUNT_JSON` (the whole service-account JSON on one line), and set `SMS_PROVIDER=firebase` | Firebase console > Project settings > Service accounts | No, codes print to the console |
| Document storage (production) | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `S3_BUCKET`, `S3_ENDPOINT_URL` | Your S3-compatible provider | No, local folder is used |

## Frontend: `frontend/.env.local` (public, browser-visible)

| Variable | Value | Where to get it |
|---|---|---|
| `VITE_API_BASE_URL` | `http://localhost:8000` (already set) | Use your backend's HTTPS URL in production |
| `VITE_PAYPAL_CLIENT_ID` | PayPal Sandbox client ID (public) | Same app as `PAYPAL_CLIENT_ID` above |
| `VITE_GOOGLE_CLIENT_ID` | Google OAuth client ID | Google Cloud Console |
| `VITE_APPLE_CLIENT_ID`, `VITE_APPLE_REDIRECT_URI` | Apple Services ID and HTTPS return URL | Apple Developer account |
| `VITE_FIREBASE_API_KEY`, `VITE_FIREBASE_AUTH_DOMAIN`, `VITE_FIREBASE_PROJECT_ID`, `VITE_FIREBASE_STORAGE_BUCKET`, `VITE_FIREBASE_MESSAGING_SENDER_ID`, `VITE_FIREBASE_APP_ID` | Firebase web app config (public) | Firebase console > Project settings > Your apps |

## Never put these in any file that is committed

- `PAYPAL_CLIENT_SECRET`, `AI_API_KEY`, `RESEND_API_KEY`, `FIREBASE_SERVICE_ACCOUNT_JSON`, `APPLE_PRIVATE_KEY`, `AWS_SECRET_ACCESS_KEY`, `JWT_SECRET_KEY`
- Any `VITE_` variable that contains a secret

## Production (Render)

`render.yaml` already lists these variables. Enter the secret values in the Render dashboard, not in files. Set the backend's `FRONTEND_ORIGIN` to your exact static-site HTTPS URL with no trailing slash, or the browser will block every API call.

## After changing keys

Restart the backend (`uvicorn`) and restart Vite (`npm run dev`). Both read their env files only at startup.
