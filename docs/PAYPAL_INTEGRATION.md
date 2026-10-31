# PayPal Integration Plan

## Goal
Demonstrate a real PayPal Developer Platform integration using the free Sandbox: create an order for a selected freight quote, let the buyer approve it, capture it on the server, and show a backend-confirmed payment record.

Official resources:
- PayPal current REST API resources: https://developer.paypal.com/api/rest/current-resources/
- Orders API: https://developer.paypal.com/docs/api/orders/v2/
- JavaScript SDK / Checkout: https://developer.paypal.com/sdk/js/
- Webhooks overview: https://developer.paypal.com/api/rest/webhooks

## Sandbox setup
1. Sign in to PayPal Developer.
2. Create or select a Sandbox REST app.
3. Copy its Sandbox Client ID and Secret.
4. Store the Client ID in the frontend configuration only if needed to render the SDK.
5. Store the Secret only in backend environment variables.
6. Use Sandbox buyer and seller accounts from Developer Dashboard; do not use real money.
7. Configure webhook URL/event subscriptions when deployed, then save and verify the webhook ID.

## Proposed checkout sequence
1. User selects a stored `quote_id` and confirms the displayed quote.
2. Frontend calls `POST /api/payments/create-order` with the internal quote ID—not an amount.
3. Backend checks authentication/demo session, validates quote state and currency, loads the quote from storage, and creates a PayPal Orders API order using server-owned amount and a stable internal reference.
4. PayPal SDK displays the approval experience.
5. After the buyer approves, frontend calls `POST /api/payments/{payment_id}/capture`.
6. Backend verifies the internal payment is associated with the returned PayPal order ID, calls the capture endpoint, and checks provider status, amount, currency, and purchase-unit reference.
7. Backend persists the provider order/capture IDs and final status.
8. Frontend fetches the backend payment resource and displays the recorded status.
9. If webhook delivery is configured, verify signature using PayPal's documented mechanism, check event ID for deduplication, and reconcile relevant events. A webhook is not trusted until verified.

## API routes in our app
- `POST /api/payments/create-order`
- `POST /api/payments/{payment_id}/capture`
- `GET /api/payments/{payment_id}`
- `GET /api/shipments/{shipment_id}/payments`
- `POST /api/webhooks/paypal`

Use provider-specific route names only if they exactly reflect the implementation. Do not expose raw secrets or accept a client-submitted amount as authoritative.

## State model
- `CREATED`: internal row/order has been created, not paid.
- `APPROVED`: buyer approval reported but not necessarily captured.
- `CAPTURED`: provider-confirmed capture succeeded and amount/currency match.
- `FAILED`: confirmed failed state.
- `CANCELLED`: buyer cancelled or order abandoned; verify provider state where needed.
- `REVIEW_REQUIRED`: local and provider states do not agree or a verification check fails.
- `REFUNDED`: only when refund is actually implemented and provider confirms it.

Never display `CAPTURED` solely because the browser returned to a success URL. A client callback is not a substitute for backend capture verification.

## Idempotency and amount integrity
- Bind one internal payment attempt to one selected quote and one provider order ID.
- Read the amount/currency from stored quote data on the server.
- Save the amount/currency snapshot with the payment row.
- Reject unknown quote IDs, expired quote versions, currency mismatch, or attempts to capture an unrelated order.
- Disable duplicate checkout clicks and make capture retries safe. If a capture timeout occurs, query provider state before creating a second order.
- Treat repeated webhook delivery as normal; persist event IDs and process each event only once.

## Important scope restriction
Do not describe this prototype as escrow, trustless payment protection, automatic settlement, split payout, or a production freight marketplace. Those features are not included in this MVP. For any live transaction, validate business-country eligibility, supported currencies, seller account requirements, PayPal terms, and whether the intended freight transaction is permitted. PayPal's India help page says India accounts cannot receive domestic payments but can receive international payments; a sandbox demo does not establish live merchant eligibility for this exact use case: https://www.paypal.com/in/cshelp/article/can-i-use-paypal-to-receive-payments-from-indian-customers-help1049
