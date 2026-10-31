# Product Requirements Document (PRD)

## Product objective
Deliver a complete, working proof of concept that turns freight quote evaluation into a safer and more explainable quote-to-payment workflow using AI and PayPal Sandbox.

## Primary user journey
1. User opens the dashboard.
2. User selects or creates a shipment request.
3. The app displays comparable quotes and a forecast context panel.
4. User opens a quote to inspect its total, terms, route, timing, and risk flags.
5. AI copilot explains a comparison grounded only in the quote data supplied to it.
6. User explicitly selects a quote and sees a confirmation screen with the exact amount/currency.
7. Frontend starts PayPal checkout using the Sandbox client ID.
8. Backend creates the order using server-owned quote data; the browser cannot dictate a trusted amount.
9. After approval, backend captures the order and validates the returned status/amount/currency before marking the payment complete.
10. User sees the verified status and an entry in payment history.

## Functional requirements
- FR-01: Create/read a shipment request.
- FR-02: Display at least three seeded quotes for a demo shipment.
- FR-03: Normalize quote totals and show the components used in the comparison.
- FR-04: Show the method, data timestamp, currency, and limitations of rate estimates.
- FR-05: Calculate explainable risk indicators and show the exact reasons behind the score.
- FR-06: Generate an AI summary of quote differences and risk indicators.
- FR-07: Require an explicit user selection and confirmation before a PayPal order is created.
- FR-08: Create PayPal orders only on the backend, using an authoritative saved quote amount.
- FR-09: Capture orders only through a backend route and validate the result.
- FR-10: Persist internal quote/payment references and the provider order/capture IDs.
- FR-11: Process PayPal webhooks only after signature verification; handle duplicate delivery safely.
- FR-12: Distinguish `CREATED`, `APPROVED`, `CAPTURED/COMPLETED`, `FAILED`, `CANCELLED`, and `REFUNDED` when implemented. Do not equate a browser return URL with successful payment.
- FR-13: Clearly label sandbox/demo data.
- FR-14: Provide a guided demo path and resettable seed data.

## Non-functional requirements
- NFR-01: Secrets never appear in the frontend bundle, git history, logs, or screenshots.
- NFR-02: Invalid amount, currency, quote ID, or payment state is rejected server-side.
- NFR-03: Payment operations are idempotent or safely guarded against repeated clicks/retries.
- NFR-04: API errors are readable and do not leak credentials or stack traces to users.
- NFR-05: The main workflow works on desktop and mobile browser sizes.
- NFR-06: Every scoring result explains its inputs; unknown data is not silently treated as safe.
- NFR-07: The demo can be launched using the documented steps from a clean clone.

## MVP prioritization
### P0 — required for submission
- Dashboard, shipment view, quote comparison, risk explanation, AI summary.
- PayPal Sandbox payment workflow from quote selection through backend capture.
- Payment history and clear success/failure states.
- Basic tests, `.env.example`, public repository, `LICENSE`, run instructions, short demo video.

### P1 — high value if P0 works
- Quote document upload and extraction of fee fields.
- Timeline of quote changes and payment events.
- Confidence/uncertainty display for the estimated rate range.
- Admin-seeded demo quotes and one-click reset.

### P2 — do not start before P0
- Live carrier integrations, live money, real vendor onboarding, payout splitting, escrow, subscriptions, blockchain, complex agents, mobile app, or multi-provider ML benchmarking.

## Success measures
- A first-time evaluator can complete the main demo without manual database edits.
- One Sandbox payment can be approved and captured, and its state is visible after a page refresh.
- At least one risk flag changes the displayed recommendation and is explainable.
- The AI summary references real fields present in the selected quotes and does not invent missing values.
- Tests confirm that a client cannot modify the payment amount by editing frontend payloads.
