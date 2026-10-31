# Master Implementation Prompt for a Coding Agent

Build **FreightPilot AI**, a functional web application for the PayPal AI Hackathon. Read every Markdown file in `docs/` (or the root folder if docs are stored there) before editing code. Treat `PROJECT_CHARTER.md`, `PRODUCT_REQUIREMENTS.md`, `SYSTEM_ARCHITECTURE.md`, `PAYPAL_INTEGRATION.md`, and `SECURITY.md` as source-of-truth requirements.

## Core requirements
1. Create a professional responsive freight procurement dashboard with a seeded shipment and at least three quote offers.
2. Use React + TypeScript + Vite for the frontend and Python FastAPI for the backend. Keep AI provider and PayPal secrets in backend environment variables only.
3. Implement structured shipment/quote data, a reproducible rate-estimate baseline, and deterministic quote risk flags with evidence/recommended checks.
4. Implement an AI copilot endpoint that explains the provided fields and risk flags using structured output. Provide a graceful fallback and never let AI control payment amount or payment actions.
5. Integrate the PayPal JavaScript SDK and Orders REST API in Sandbox. The server must create orders from stored quote data, not an amount from the browser; backend must capture and validate amount/currency/provider status before a payment is marked complete.
6. Persist payment state, provider IDs, quote/shipment references, timestamps, and idempotency keys. Implement webhook signature verification and event deduplication if webhook configuration is available.
7. Show `SANDBOX DEMO` and clearly identify synthetic data. Never claim escrow, live market data, real carrier verification, or production suitability unless actually implemented and validated.
8. Add tests for quote validation, risk flags, amount integrity, payment states, invalid webhooks, and repeated requests.
9. Add environment examples, `.gitignore`, public `LICENSE`, and clean README setup instructions. No real secrets in code or docs.
10. Build the application; run frontend build and backend tests; fix errors rather than reporting success based on code generation alone.

## Work order
A. Inspect repository and identify what already exists. Preserve valid code and avoid destroying unrelated user work.
B. Implement the thinnest vertical slice: seeded quotes → comparison → risk reasons → PayPal Sandbox create/approve/capture → persisted payment status.
C. Add AI explanation and fallback.
D. Add tests, accessibility/error states, and documentation.
E. Return exact commands run, successful results, known gaps, environment variables required, and the files changed.

## Do not
- Add large extra features before core flow works.
- use fake hard-coded “payment successful” responses;
- trust frontend amount/currency or browser redirect state;
- expose secrets through Vite `VITE_*` values;
- call a heuristic risk score a trained fraud model or a forecast a real-time market quote;
- invent unsupported PayPal API capabilities.
