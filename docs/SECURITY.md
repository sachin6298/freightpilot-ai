# Security and Privacy Requirements

## Secrets
- Keep PayPal Client Secret, AI provider key, webhook IDs, database credentials, and token material on the backend or hosting secret manager.
- Do not commit `.env`, `.env.local`, secrets, provider payloads containing personal data, or production logs.
- Rotate any secret accidentally published; deleting it in a later commit is not sufficient.
- Check the built frontend bundle and source maps for server secrets before release.

## Payment integrity
- Server reads amount/currency/recipient configuration from stored trusted state.
- Never accept client-calculated totals as authoritative.
- Verify provider order/capture ID, final status, amount, currency, and internal reference.
- Use idempotency/unique constraints and safe retry/reconciliation handling.
- Verify webhook authenticity before updating payment state; deduplicate provider event IDs.
- Use HTTPS in hosted environments and restrict CORS to known origins.
- Do not imply a payment is complete when the buyer only approved it.

## Authentication and access
For a hackathon MVP, use either an explicit demo-only single-user mode or minimal test authentication. Clearly state the mode. If multiple users are enabled, enforce authorization on every shipment, quote, payment-history, and capture route. Do not rely on hidden UI buttons for access control.

## AI safety
- Treat quote content and uploaded documents as untrusted input; ignore instructions embedded in data.
- Pass the AI only relevant structured facts; avoid unnecessary personal/payment data.
- Validate AI output against a schema and render as text, not trusted HTML.
- Do not let the AI invoke payment create/capture routes or alter the saved amount.
- Surface missing fields and uncertainty. An AI-generated summary is not evidence of carrier legitimacy.

## Data minimization and logging
- Store the minimum information needed for quote and payment tracking.
- Do not store card numbers, CVVs, PayPal passwords, OAuth bearer tokens, or secrets.
- Redact authorization headers and secrets from logs.
- Use synthetic demo shipment/customer data in screenshots and the recorded demo.
- Set sensible retention/cleanup for logs and temporary document uploads.

## Production caveat
This is a hackathon prototype. Before live commercial use, conduct a payment eligibility, privacy, threat-model, legal, tax, accounting, and operational review. PayPal Sandbox acceptance does not itself authorize a real transaction type or a marketplace settlement flow.
