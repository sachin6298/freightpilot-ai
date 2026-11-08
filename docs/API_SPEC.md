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


## Authentication provider endpoints (implemented)

All routes below are mounted under `/api/auth`.

### `POST /api/auth/oauth/google`
Request:
```json
{"id_token":"<Google GIS credential JWT>","nonce":"<one-time frontend nonce>"}
```
The API validates the provider signature, issuer, audience, expiry and nonce against Google's published signing keys. It creates or links a buyer account only after the provider email is verified.

### `POST /api/auth/oauth/apple`
Request:
```json
{"authorization_code":"<one-time Apple authorization code>","nonce":"<one-time frontend nonce>"}
```
The API exchanges the one-time code with Apple using a short-lived ES256 client secret signed by the server-only Apple `.p8` key, then validates the returned ID token's signature, issuer, audience, expiry and nonce.

### `PUT /api/auth/me/phone`
Requires an access token. Sets or replaces an unverified account phone number in E.164 format. A verified phone number cannot be changed through this route. Response includes the current user and phone verification state.

### `POST /api/auth/phone/request`
Request:
```json
{"phone_number":"+919876543210"}
```
Requests an SMS login code for an existing account. The response does not disclose whether the phone number belongs to an account.

### `POST /api/auth/phone/verify`
Request:
```json
{"phone_number":"+919876543210","otp":"123456"}
```
Verifies the SMS code and returns a normal access-token response. Codes expire after 10 minutes and are limited to five attempts.

### Authenticated phone verification
`POST /api/auth/send-phone-verification` sends a code to the current account's registered phone number; `POST /api/auth/verify-phone` confirms it. Both require an access token.
