# Build Roadmap — 27 October to Submission

**Timebox:** The official Devpost deadline is November 12, 2026 at 12:00 p.m. Pacific Time. Confirm this in the official rules and plan to submit at least a day early. Because the team is working from India, avoid treating the displayed local date/time as interchangeable with Pacific Time.

## Build strategy
Build one reliable vertical slice. Use deterministic seeded quote data first, then add AI explanation and PayPal Sandbox. Do not spend the first week polishing UI or training a complex model before payment and core data flow work.

## Day-by-day plan

### Day 1 — Oct 27: Lock scope and repository
- Confirm product name, README, directory layout, MVP, and responsibilities.
- Create repo, `.gitignore`, `.env.example`, `LICENSE`, and basic README.
- Create a seeded shipment with three quotes.
- **Exit gate:** app starts locally and team agrees on one demo story.

### Days 2–3 — Oct 28–29: UI shell and data model
- Implement dashboard, shipment details, quote cards/table, quote detail drawer/page.
- Implement backend health route, shipment/quote schemas, seed data, storage.
- Add loading, empty, and error states.
- **Exit gate:** quote comparison works without AI or PayPal.

### Days 4–5 — Oct 30–31: Risk scoring and forecast baseline
- Implement deterministic quote risk flags with visible reasons.
- Add rate range from historical/seeded sample data using a clearly documented baseline (rolling median or comparable historical median).
- Show data coverage and uncertainty.
- **Exit gate:** same input yields reproducible, explainable results.

### Days 6–7 — Nov 1–2: AI copilot
- Add backend AI adapter and a strict prompt/schema.
- Provide quote comparison summary, missing-field explanation, and questions to ask the carrier.
- Ground generation only in provided structured facts; return an explicit fallback if AI is unavailable.
- **Exit gate:** an evaluator can see an AI-generated explanation tied to quote fields.

### Days 8–9 — Nov 3–4: PayPal Sandbox
- Create developer app and configure client ID/secret.
- Implement backend order creation from a saved quote.
- Implement frontend PayPal approval, backend capture, payment record, and result screen.
- Check returned amount/currency and final provider status.
- **Exit gate:** approved Sandbox payment appears as captured/complete after refresh; cancelled flow does not look paid.

### Day 10 — Nov 5: Webhooks and duplicate handling
- Implement webhook endpoint and provider signature verification.
- Process only relevant configured events; persist event ID and ignore duplicates.
- Add reconciliation path: query PayPal order/capture details if state is uncertain.
- **Exit gate:** webhook verification and duplicate-event tests pass; if the Sandbox cannot deliver webhooks during demo, the main checkout flow remains complete.

### Days 11–12 — Nov 6–7: QA and design polish
- Test payment errors, invalid quote IDs, stale quote values, repeated clicks, and missing environment variables.
- Make responsive layout and consistent UI states.
- Add test data reset and visible “Sandbox / demo data” marker.
- **Exit gate:** a clean clone can run the documented local setup.

### Day 13 — Nov 8: Deployment
- Deploy frontend/backend and configure HTTPS, environment variables, allowed origins, and PayPal Sandbox webhook URL.
- Run smoke tests on deployed URLs. Keep local mode documented as fallback.
- **Exit gate:** deployed or repeatably runnable demo.

### Day 14 — Nov 9: Submission materials
- Finalize architecture diagram in README, screenshots, tool list, use cases, limitations, and license.
- Draft Devpost text and judge test steps.
- Record a first demo video under 3 minutes.
- **Exit gate:** another teammate can narrate and reproduce the demo.

### Day 15 — Nov 10: Feature freeze
- Fix only high-impact bugs; avoid new features.
- Verify repository is public, license visible, secrets absent, and install instructions complete.
- Make a clean environment run.

### Day 16 — Nov 11: Final run and early submission
- Record final short video with actual working checkout flow.
- Submit before the deadline rather than waiting for final hours.
- Keep a final-known-good commit/tag.

## If behind schedule
1. Keep: quote comparison, explainable risk flag, one AI summary, PayPal Sandbox create/capture, payment record, README, license, demo video.
2. Remove: file upload, advanced charting, extra ML models, multiple AI agents, real carrier APIs, payout/escrow.
3. Do not replace PayPal with a fake button or replace AI with static text while claiming the features are functional.
