# Provider credential configuration

Never commit secrets or paste them into source code. Keep server secrets in `backend/.env` locally and in the backend service's Render Environment settings in production. Only public identifiers may be exposed through `VITE_*` variables.

## Google Sign-In

- Frontend: `VITE_GOOGLE_CLIENT_ID` (OAuth 2.0 Web application client ID)
- Backend: `GOOGLE_CLIENT_ID` (same client ID; backend validates token audience)
- Authorized JavaScript origins: `http://localhost:5173` for local development and the exact production HTTPS origin.
- The backend validates Google signature, issuer, audience, expiry, nonce and verified email. A client ID alone does not complete setup unless backend has the matching value and the API is reachable.

## Apple Sign-In

- Frontend: `VITE_APPLE_CLIENT_ID`, `VITE_APPLE_REDIRECT_URI`
- Backend: `APPLE_CLIENT_ID`, `APPLE_TEAM_ID`, `APPLE_KEY_ID`, `APPLE_PRIVATE_KEY`, `APPLE_REDIRECT_URI`
- The Apple private key is server-only. Configure a registered HTTPS domain/return URL; Apple web sign-in is not supported on plain localhost origins.

## PayPal

- Frontend: `VITE_PAYPAL_CLIENT_ID` (public ID for the selected environment)
- Backend: `PAYPAL_CLIENT_ID`, `PAYPAL_CLIENT_SECRET`, `PAYPAL_ENV`, and `PAYPAL_WEBHOOK_ID`
- Keep `PAYPAL_ENV=sandbox` until a Sandbox order creation, approval, server-side capture and webhook verification have passed. For Live, use the Live client ID/secret and matching Live webhook ID on both frontend and backend. Never mix Sandbox and Live credentials.
- Do not run real-money tests without explicit business approval and a confirmed production checklist.

## Firebase Phone Authentication

- Frontend Firebase web app configuration belongs in `VITE_FIREBASE_*` values only if the frontend Firebase SDK flow is enabled.
- Backend Admin SDK: `FIREBASE_PROJECT_ID` and `FIREBASE_SERVICE_ACCOUNT_JSON` (server-only JSON).
- Enable Phone provider in Firebase Authentication and add the local and production authorized domains. Configure billing/quotas and test SMS delivery before production.
