# System Architecture

## Design principles
- PayPal and AI must be integral to the workflow.
- The backend owns quote amount, order creation, capture, payment state, and webhook verification.
- AI is an advisory layer; the user makes the final selection and approves payment.
- Forecast and risk outputs expose their method and evidence.
- Sandbox/demo data is visibly identified.

## Logical architecture
```text
Browser
  ├── Dashboard / shipment / quote comparison
  ├── AI explanation panel (calls backend; no secret AI key in browser)
  └── PayPal JS SDK (Sandbox client ID only)
          │ HTTPS / JSON
          ▼
FastAPI backend
  ├── Shipment & quote API
  ├── Forecast baseline service
  ├── Explainable risk engine
  ├── AI copilot adapter
  ├── PayPal service
  │     ├── OAuth access token (server-side)
  │     ├── create order from stored quote
  │     ├── capture approved order
  │     ├── verify provider response
  │     └── verify/process webhooks
  └── persistence layer
          ▼
SQLite (local MVP) / PostgreSQL (hosted)
  ├── shipments
  ├── quotes
  ├── risk assessments
  ├── payments
  └── webhook_events
```

## Main application flow
1. Frontend requests shipment and quotes.
2. Backend returns normalized quote details, estimate metadata, and risk flags.
3. AI endpoint receives a bounded structured payload containing only fields needed for explanation.
4. The buyer selects a saved `quote_id` and confirms the checkout amount shown by the server.
5. Frontend invokes PayPal SDK. The browser requests creation through the backend; backend reads the stored quote and creates the PayPal order with the stored amount and currency.
6. Buyer approves in PayPal Sandbox.
7. Frontend invokes backend capture using the internal payment ID/order ID; backend captures the PayPal order and validates provider status, amount, currency, and reference.
8. Backend writes a payment event and final state transactionally where possible.
9. A verified PayPal webhook can reconcile subsequent provider events. Duplicate events are idempotent.
10. Frontend reads the backend payment record to display status.

## Trust boundaries
- **Untrusted:** request body, browser callbacks, redirect query parameters, user-supplied documents, LLM output.
- **Trusted only after validation:** saved quote values, server-authenticated PayPal API response, verified PayPal webhook.
- **Never trust:** client-provided amount/currency, front-end `success=true`, an unverified webhook, or an AI recommendation as a payment authorization.

## Technology choices
- React + TypeScript + Vite keeps the frontend approach close to the previous AI Risk Manager project.
- FastAPI keeps AI/risk logic and PayPal REST calls in Python.
- SQLite makes local setup fast. Use PostgreSQL for hosted multi-user persistence if the team can configure it reliably.
- Begin with a deterministic scoring engine and a transparent rate-estimation baseline. Add complex ML only if the team has useful data and can test it.

## Failure behavior
- AI unavailable: show risk flags and quote data without the generated prose; never block safety checks.
- PayPal unavailable: payment stays pending/failed; do not show paid.
- Capture response uncertain: query/reconcile provider state before allowing a retry.
- Webhook invalid: reject it; do not update payment status.
- Stored quote changed after order creation: reject stale quote/order mismatch and require renewed user confirmation.
