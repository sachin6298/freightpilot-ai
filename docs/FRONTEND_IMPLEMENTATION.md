# FreightPilot AI Frontend Implementation

## Product shell

The frontend is now structured as a multi-section procurement workspace with a persistent left navigation, responsive header, account control, notification inbox and route-specific page content. The visual system uses a light operational canvas with a navy sidebar and blue/teal semantic accents.

## Sections

1. **Overview** — database-backed KPI cards, recent shipments, captured spend by currency, shipment status distribution and carrier quote activity.
2. **Shipments** — searchable shipment register, selection, lifecycle status, manual tracking timeline and manual tracking event entry.
3. **Freight quotes** — active-shipment quote comparison, base/surcharge totals, transit, quote provenance, validity, benchmark variance and risk label. The buyer can continue to payment for a non-expired quote.
4. **Risk manager** — risk status, score, evidence flags and an action to re-run the backend assessment.
5. **AI Copilot** — select persisted quote records and call `/api/copilot/compare`; display the service's structured summary, advantages, concerns, missing information and next questions.
6. **Payments** — selected-quote checkout, PayPal JavaScript SDK buttons, transaction history and payment status. History is aggregated through each visible shipment's payment-history endpoint.
7. **Analytics** — shipment status distribution, captured payments grouped by currency, and carrier statistics from persisted quotes.
8. **Settings** — API health, database configuration, PayPal client-ID presence, carrier registry, environment and demo reset controls.

## Transaction flow

1. User chooses a quote from the Freight quotes page.
2. The PayPal SDK `createOrder` callback invokes FastAPI `POST /api/payments/create-order` using the stored quote ID and an idempotency key.
3. The frontend returns the backend-created PayPal order ID to the PayPal SDK.
4. After buyer approval, the SDK `onApprove` callback sends the payment ID and provider order ID to FastAPI `POST /api/payments/{payment_id}/capture`.
5. FastAPI verifies the PayPal order, compares the amount/currency with the saved quote, captures if required and persists the capture result.
6. The frontend shows success only after the backend returns a confirmed capture record.

The frontend never calculates or submits a payable amount. The PayPal Client Secret is never exposed to Vite/browser code. The JavaScript SDK is loaded using the selected quote currency.

## API contract used

- `GET /health`
- `GET/POST /api/shipments`
- `POST /api/shipments/{id}/cancel`
- `GET /api/shipments/{id}/quotes`
- `GET /api/shipments/{id}/estimate`
- `GET/POST /api/shipments/{id}/tracking`
- `POST /api/quotes/{id}/assess`
- `POST /api/copilot/compare`
- `GET /api/analytics/overview`
- `GET /api/analytics/carriers`
- `GET /api/carriers`
- `POST /api/shipments/{id}/refresh-quotes?carrier_code=...`
- `GET /api/notifications` and `POST /api/notifications/{id}/read`
- `POST /api/payments/create-order`
- `POST /api/payments/{id}/capture`
- `GET /api/shipments/{id}/payments`
- `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me`
- `POST /api/demo/reset`

## Explicit limitations

- The backend does not expose a global payment list endpoint. The Payments page retrieves history per visible shipment with bounded concurrency.
- The carrier adapter registry is empty by default; the UI does not claim that the seed quotes are live offers.
- Tracking updates entered from the UI are manual and marked as user input by the backend; live carrier tracking is not included.
- Copilot's supported endpoint is quote comparison, not a general-purpose free-form chatbot.
- Authentication can be used from the UI, but local demo mode can remain guest-accessible while `AUTH_REQUIRED=false`. Production must set `AUTH_REQUIRED=true` and use a secure deployment configuration.
- PayPal webhook testing requires an externally reachable HTTPS callback URL and matching Sandbox webhook ID.

## Frontend build

```powershell
cd frontend
npm ci
npm run build
npm run dev
```
