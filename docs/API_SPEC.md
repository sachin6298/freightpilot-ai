# Backend API Contract (Proposed)

Base path: `/api`. JSON requests and responses use UTF-8. All routes below are proposed contracts; align the code and this document during implementation.

## `GET /health`
Response:
```json
{"status":"ok","app":"freightpilot-ai","mode":"sandbox"}
```
Do not include secrets or internal stack details.

## `GET /api/shipments`
Returns saved shipments available to the current demo/user.

## `POST /api/shipments`
Request:
```json
{
  "cargo_type":"bulk commodity",
  "quantity_tonnes":2500,
  "origin":"Port Alpha",
  "destination":"Port Beta",
  "ready_date":"2026-11-10",
  "required_arrival_date":"2026-12-05",
  "currency":"USD"
}
```
Validate positive quantity, date syntax/order, non-empty route, and allowed demo currency.

## `GET /api/shipments/{shipment_id}/quotes`
Returns quotes normalized for comparison. Include quote ID, seller/carrier label, base amount, surcharges, total amount, currency, transit estimate, terms, quote validity, capacity fields, risk flags, and source/method metadata.

## `GET /api/quotes/{quote_id}`
Returns one quote and associated risk assessment.

## `POST /api/quotes/{quote_id}/assess`
Recalculates deterministic assessment against current quote/shipment state. AI output is separate and should not overwrite deterministic results.

## `POST /api/copilot/compare`
Request contains shipment ID and quote IDs. Server loads trusted quote values; clients should not be able to supply fabricated risk flags as evidence. Response should follow the structured output schema in `AI_RISK_ENGINE.md`.

## `POST /api/payments/create-order`
Request:
```json
{"quote_id":"quote_demo_001","idempotency_key":"client-generated-uuid"}
```
The browser does **not** submit trusted `amount` or `currency` values. Backend verifies the quote exists, is still valid, and is payable in this demo; then it creates the provider order and a local payment record.

Success response (illustrative only):
```json
{
  "payment_id":"pay_local_123",
  "provider":"paypal_sandbox",
  "provider_order_id":"SANDBOX_ORDER_ID",
  "status":"CREATED",
  "amount":"12500.00",
  "currency":"USD"
}
```

## `POST /api/payments/{payment_id}/capture`
Request contains the provider order ID only if required to cross-check it; backend must compare it with the ID already stored. Do not let the client choose a new amount or payment recipient. Response is the final locally recorded status after backend capture verification.

## `GET /api/payments/{payment_id}`
Returns internal payment state, saved amount/currency snapshot, provider IDs, timestamps, and safe status messages.

## `GET /api/shipments/{shipment_id}/payments`
Lists associated payments, sorted newest first.

## `POST /api/webhooks/paypal`
Accept provider webhook payload only after verifying it using PayPal's documented signature-verification approach. Deduplicate by webhook event ID and reconcile relevant states. Return 2xx only after durable receipt/processing strategy is satisfied.

## Error convention
Use a stable structure:
```json
{"error":{"code":"QUOTE_EXPIRED","message":"This quote is no longer valid. Refresh the comparison and select a current quote."}}
```
Use appropriate 4xx codes for client errors and 5xx for server errors. Never include access tokens, client secrets, stack traces, raw provider credentials, or sensitive payloads in an error.

## Required checks for payment endpoints
- Quote exists and is eligible for this demo.
- Saved amount/currency are authoritative.
- Provider app/environment is Sandbox for demo.
- Internal payment attempt and provider order ID match.
- Provider status/amount/currency are validated before marking captured.
- Repeated requests do not create duplicate charges/orders unexpectedly.
