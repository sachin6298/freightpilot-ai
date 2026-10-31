# PayPal AI Hackathon Submission Draft

## Project title
**FreightPilot AI — AI-Assisted Freight Procurement with PayPal Checkout**

## One-line description
An AI freight copilot that explains quote trade-offs and risk signals, then links a buyer-approved freight quote to a verified PayPal Sandbox payment workflow.

## Problem
Freight quotes can be difficult to compare because fees, schedules, capacity information, and payment terms are not always presented consistently. A buyer may spend time comparing offers without a clear explanation of missing information or potential inconsistencies. The selected quote then has to move into a payment workflow with a clear amount, reference, and status.

## Solution
FreightPilot AI brings shipment details, quote comparison, freight-rate context, explainable risk indicators, and a grounded AI summary into one web app. After reviewing the quote and its risks, the user selects an offer and approves a PayPal Sandbox payment. The backend creates and captures the order against stored quote data and records the verified payment state against the shipment/quote references.

## What uses AI
- Provides a structured comparison of freight quote fields.
- Explains deterministic risk indicators and missing information.
- Produces follow-up questions for the buyer.
- Optionally summarizes rate context from a documented baseline, with uncertainty and demo-data labels.

## What uses PayPal
- PayPal Developer Sandbox and JavaScript Checkout SDK for buyer approval.
- Orders API for server-side order creation and capture.
- Backend payment record tied to the selected quote.
- Verified webhook handling when configured in the prototype.

## What makes it useful
The workflow connects insight to action. AI is not a separate chat window: it helps the buyer inspect a real quote before a deliberate payment step. Payment amount is owned by the backend, and the UI distinguishes approval from capture confirmation.

## Technology
React, TypeScript, Vite, FastAPI, Python, Pydantic, database layer, PayPal Developer Sandbox, and the selected AI provider/model. List only technologies that are actually implemented in the final repository.

## Limitations
The prototype uses seeded or demo quote data unless a source is explicitly integrated. Forecasts are estimates, risk flags do not prove fraud, and AI output requires human review. PayPal payments are Sandbox-only. No escrow, automatic disbursement, real freight booking, or production vendor verification is claimed.

## Submission checklist
- [ ] Public repository URL and working license.
- [ ] Complete README with clean setup and test instructions.
- [ ] Functional demo URL or setup path for judges.
- [ ] Public YouTube video shorter than three minutes.
- [ ] Description and tool list accurately describe what is implemented.
- [ ] No secrets, private data, or misleading claims.
- [ ] Recheck final rules: https://paypalaihackathon.devpost.com/rules
