# Environment Variables and Local Setup

## Backend `.env` (never commit this file)
Use a backend-only `.env` file based on these placeholders:
```dotenv
APP_ENV=development
DEMO_MODE=true
DATABASE_URL=sqlite:///./freightpilot.db
FRONTEND_ORIGIN=http://localhost:5173

PAYPAL_ENV=sandbox
PAYPAL_CLIENT_ID=replace_with_sandbox_client_id
PAYPAL_CLIENT_SECRET=replace_with_sandbox_client_secret
PAYPAL_WEBHOOK_ID=replace_when_webhook_is_configured

AI_PROVIDER=replace_with_selected_provider
AI_API_KEY=replace_with_your_ai_provider_key
AI_MODEL=replace_with_supported_model
```

Do not place real keys in this documentation, source code, screenshots, public issue threads, or Vite variables. Vite exposes variables prefixed with `VITE_` to browser code. Only a PayPal client identifier intended for browser use may be exposed, never the secret.

## Frontend `.env.local`
```dotenv
VITE_API_BASE_URL=http://localhost:8000
VITE_PAYPAL_CLIENT_ID=replace_with_sandbox_client_id
```

Only expose values that are safe for the browser. Do not put `PAYPAL_CLIENT_SECRET` or `AI_API_KEY` in the frontend file.

## Installation outline
### Backend
```bash
cd backend
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Verification
- Open API health route and FastAPI `/docs`.
- Confirm CORS is restricted to the intended local frontend origin.
- Confirm the app starts with `DEMO_MODE=true` even if AI/PayPal keys are absent; payment controls should clearly say configuration is missing rather than silently pretend to pay.
- Test AI fallback without an API key.
- Use only PayPal Sandbox credentials for this hackathon prototype.

Exact setup commands depend on the generated project files. Keep `.env.example` updated as real variables are added, but leave values as placeholders.
