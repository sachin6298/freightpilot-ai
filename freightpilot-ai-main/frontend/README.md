# Freight operations frontend

React + TypeScript + Vite frontend for the existing FastAPI logistics platform.

## Local development

```powershell
npm ci
npm run dev
```

The development server normally starts at `http://localhost:5173`. If that port is occupied, use the URL printed by Vite.

## Production build

```powershell
npm run build
```

## Environment

Copy `.env.example` to `.env.local` and set the values required by your deployment:

- `VITE_API_BASE_URL`: FastAPI base URL (defaults to `http://localhost:8000`).
- `VITE_PAYPAL_CLIENT_ID`: PayPal Sandbox client ID for the browser SDK.
- `VITE_GOOGLE_CLIENT_ID`: Google OAuth Web client ID.
- `VITE_APPLE_CLIENT_ID` and `VITE_APPLE_REDIRECT_URI`: Apple Sign In configuration.
- `VITE_SUPPORT_EMAIL`: support mailbox used by the public Contact section.

Never put private OAuth secrets, PayPal secrets, Gemini API keys, Twilio credentials, or database credentials in frontend environment variables. Configure those on the backend.

## Main screens

- Public landing page with maritime hero, capabilities, workflow, vessel visual and contact section.
- Login and buyer/seller registration backed by the existing authentication API.
- Tallie-inspired workspace shell with Overview, Shipments, Freight quotes, Payments, AI Copilot, Risk, Analytics, Carriers, Documents and Settings.
- Persistent light/dark theme preference.

Dashboard metrics and records are populated from the backend API. No sample Tallie transactions or fabricated logistics KPIs are included.
