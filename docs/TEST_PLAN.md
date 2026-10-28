# Test Plan

## Automated backend tests
### Quote and shipment
- Valid shipment is created and returned.
- Reject zero/negative cargo quantity and invalid dates.
- Total amount equals the validated sum of cost components.
- Quote ID from another shipment or an unknown ID is rejected.
- Expired quote is flagged and cannot be paid without renewed confirmation.
- Mixed-currency comparison is rejected or clearly separated.

### Risk and AI
- Missing fee breakdown triggers the expected flag.
- An outlier quote is flagged relative to a same-currency comparable set.
- Capacity mismatch is flagged only when required fields exist.
- No data yields `INSUFFICIENT_DATA`, not a confident forecast.
- AI summary cannot override deterministic flag data.
- Invalid/malformed AI output falls back safely.
- Uploaded quote instruction injection cannot change the system rules or call payment routes.

### PayPal
- Missing credentials returns a clear configuration error and does not record success.
- Unknown quote ID cannot create an order.
- Browser-supplied amount/currency is ignored or rejected.
- Provider create-order error leaves payment non-complete.
- Approval without capture does not display `CAPTURED`.
- Capture response with mismatched amount/currency/reference is set to review/error, not success.
- Repeated create-order request with the same idempotency key does not create duplicate internal attempts.
- Repeated capture request is safe and reconciles provider state.
- Invalid webhook signature is rejected.
- Duplicate verified webhook event is processed once.

## Frontend smoke tests
- Dashboard loads with seed data.
- Quote comparison and detail panels load.
- Risk flags have evidence and accessible labels.
- AI error shows fallback state.
- Checkout amount matches the backend quote summary.
- Buyer cancellation shows cancelled/pending status, never success.
- Capture success is followed by API status refresh.
- Mobile layout does not hide quote total or PayPal action.

## Manual end-to-end sandbox test
1. Clone repo and follow README from a clean environment.
2. Configure only Sandbox credentials.
3. Open the seeded shipment and compare three quotes.
4. Select a quote with at least one risk flag; read the AI explanation.
5. Click checkout and verify amount/currency match the quote record.
6. Approve payment using the Sandbox buyer.
7. Verify backend capture and internal payment record.
8. Refresh page; status remains provider-confirmed.
9. Try a cancellation and a deliberately invalid quote ID; neither should show paid.
10. Inspect repository to confirm no secrets are committed.

## Release gate
Do not submit unless the main flow can be reproduced and the repo contains complete test/run instructions. A screenshot-only or static prototype does not satisfy the functional demo requirement described in the official rules.
