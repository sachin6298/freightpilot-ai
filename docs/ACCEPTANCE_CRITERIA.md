# Acceptance Criteria / Definition of Done

## Product
- [ ] User can open a seeded shipment and view at least three normalized quotes.
- [ ] The app shows quote totals, currency, transit estimate, terms, validity, and source type.
- [ ] At least two risk scenarios are implemented and each displays specific evidence.
- [ ] Rate estimate includes method, coverage, and uncertainty; insufficient data is handled explicitly.
- [ ] AI summary is created from loaded quote data and supports a safe fallback.
- [ ] User sees a confirmation page/modal before launching checkout.

## PayPal
- [ ] PayPal button uses the Sandbox environment.
- [ ] Backend creates order from a saved quote, not a browser amount.
- [ ] Buyer approval and capture are distinct states.
- [ ] Backend verifies provider response before setting a completed status.
- [ ] Amount/currency/provider IDs are tied to an internal payment record.
- [ ] Repeated requests and uncertain responses are safely handled.
- [ ] Webhook signature verification and idempotent event processing are implemented if webhooks are enabled.

## Engineering
- [ ] Environment values are documented in `.env.example` and no secrets are committed.
- [ ] CORS, request validation, errors, and logging are configured.
- [ ] Automated tests cover key validation and payment integrity paths.
- [ ] Clean local setup works from instructions.
- [ ] Deployed app passes smoke tests or the local run path is fully documented.

## Submission
- [ ] Public repository with open-source `LICENSE`.
- [ ] README accurately lists technologies and instructions.
- [ ] Demo works and is not a static mockup.
- [ ] Demo video shows app functioning and is under 3 minutes.
- [ ] Demo uses Sandbox and labels synthetic data.
- [ ] Devpost entry submitted before deadline.
