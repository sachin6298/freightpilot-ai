# FreightPilot AI

**A PayPal-powered AI copilot for freight procurement, quote comparison, and payment-risk review.**

Freight buyers often need to compare inconsistent shipping offers, understand changing freight prices, and decide whether a quote looks operationally and commercially plausible. FreightPilot AI centralizes these steps and connects the decision to a verified PayPal Sandbox checkout.

## The core experience
1. Create a shipment request (cargo, origin, destination, desired dates, and quantity).
2. Compare sample carrier/broker quotes using estimated cost, transit time, and feasibility fields.
3. See a rate trend/range and an explainable risk assessment for each quote.
4. Ask the AI freight copilot to explain trade-offs and flag missing or inconsistent quote fields.
5. Select a quote and review a fixed, user-approved demo amount.
6. Create and approve a PayPal Sandbox order; the backend captures it and records verified status.
7. See the shipment and payment timeline in the dashboard.

## Why this is a PayPal AI Hackathon project
PayPal is part of the actual workflow—not just a logo or mock button. The system links a chosen quote to a server-created PayPal order, uses server-side capture, and records payment status from verified backend responses/webhooks. AI helps interpret quotes, explain anomalies, and summarize the decision before payment is approved.

## Suggested stack
- Frontend: React, TypeScript, Vite, Tailwind CSS (or existing CSS design system).
- Backend: Python, FastAPI, Pydantic, Uvicorn.
- Storage: SQLite for first local prototype; PostgreSQL for hosted demo if time permits.
- AI: LLM provider behind a backend adapter for quote explanation; deterministic, explainable scoring for high-risk indicators. A simple baseline time-series/rolling-median model can drive the demo rate range.
- Payments: PayPal JavaScript SDK + Orders REST API in Sandbox; backend is the source of truth for order creation and capture.
- Tests: pytest for backend; frontend tests or Playwright smoke flows if time allows.

Do not integrate multiple databases, model families, payout products, or a marketplace onboarding flow into the MVP. Ship a reliable vertical slice first.

## Repository layout (target)
```text
freightpilot-ai/
├── frontend/
│   ├── src/
│   ├── public/
│   └── package.json
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── schemas.py
│   │   ├── routes/
│   │   ├── services/
│   │   │   ├── paypal_service.py
│   │   │   ├── quote_service.py
│   │   │   ├── risk_service.py
│   │   │   └── ai_copilot.py
│   │   └── db/
│   ├── tests/
│   └── requirements.txt
├── docs/                 # these Markdown files
├── .env.example
├── .gitignore
├── LICENSE
└── README.md
```

## Local development: intended sequence
1. Install Python 3.11+ and Node.js LTS.
2. Create and activate a Python virtual environment in `backend/`.
3. Install backend requirements and configure `backend/.env` using `ENV_SETUP.md`.
4. Start FastAPI: `uvicorn app.main:app --reload --port 8000` from `backend/`.
5. Install frontend dependencies and start Vite: `npm install` then `npm run dev` from `frontend/`.
6. Open the frontend URL printed by Vite. Test quote/risk flows first; then configure PayPal Sandbox credentials and run checkout.
7. Use `/docs` on the API server to inspect FastAPI endpoints.

The exact commands may need adjustment after the repository is generated. Do not claim that code has been built or deployed until it has actually been verified.

## PayPal setup
- Create a PayPal Developer account and a Sandbox REST app.
- Copy the sandbox Client ID to the frontend as a public client identifier, and keep the Client Secret on the backend only.
- Use the Sandbox base URL for REST calls.
- Never store card details or expose the secret in browser code.
- For this hackathon, all payment demonstrations must use Sandbox accounts and clearly labeled simulated freight quotes.

See [PAYPAL_INTEGRATION.md](PAYPAL_INTEGRATION.md), [SECURITY.md](SECURITY.md), and [ENV_SETUP.md](ENV_SETUP.md).

## Scope boundaries
The MVP does not move real freight, verify a real carrier's legal identity, provide escrow, guarantee a freight forecast, or promise production suitability for cross-border freight settlement. It is a working decision-support prototype with sandbox payments. Any real-money launch needs separate PayPal account/country/transaction eligibility, contractual, regulatory, and operational review.

## Hackathon delivery checklist
- [ ] Functional app that runs from clean setup instructions.
- [ ] PayPal Sandbox order create/approve/capture flow.
- [ ] AI feature is demonstrably useful and visible.
- [ ] Public code repository and visible open-source license.
- [ ] README contains setup, architecture, configuration, and test instructions.
- [ ] Public YouTube demonstration video under 3 minutes.
- [ ] Devpost description includes what was built, tools used, and a working demo/repository.

The official submission deadline is listed by Devpost; re-check the [official rules](https://paypalaihackathon.devpost.com/rules) before submitting.
