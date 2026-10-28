# Task Board

Use this as a lightweight execution board. Replace owner placeholders with real team members. Keep tasks small and mark them only after verifying completion.

## Sprint 0 — Scope and setup
- [ ] Confirm product pitch and MVP — Owner: Product
- [ ] Create repository and base folders — Owner: Full-stack
- [ ] Add `.gitignore`, `.env.example`, `LICENSE`, README — Owner: Repo lead
- [ ] Prepare seed shipment and 3 quotes — Owner: Backend/Data

## Sprint 1 — Quote workflow
- [ ] Define Pydantic schemas and DB models — Owner: Backend
- [ ] Create health/shipment/quote endpoints — Owner: Backend
- [ ] Implement dashboard and shipment view — Owner: Frontend
- [ ] Implement quote comparison and quote detail UI — Owner: Frontend
- [ ] Add validation/loading/error states — Owner: Frontend

## Sprint 2 — AI and risk
- [ ] Implement explainable risk flags — Owner: AI/Backend
- [ ] Add reproducible rate-estimate baseline — Owner: AI/Data
- [ ] Implement AI provider adapter and structured output — Owner: AI/Backend
- [ ] Add fallback if AI is disabled or fails — Owner: AI/Frontend
- [ ] Write risk-engine tests — Owner: QA

## Sprint 3 — PayPal
- [ ] Create Sandbox REST app — Owner: Payments
- [ ] Add backend access-token / REST client — Owner: Payments
- [ ] Implement create-order from stored quote — Owner: Payments
- [ ] Integrate PayPal JS SDK in checkout UI — Owner: Frontend
- [ ] Implement backend capture and verification — Owner: Payments
- [ ] Persist payment history and result UI — Owner: Full-stack
- [ ] Configure webhook verification and deduplication — Owner: Payments
- [ ] Test cancellation, retry, mismatch, and errors — Owner: QA

## Sprint 4 — Release
- [ ] Complete automated and manual tests — Owner: QA
- [ ] Deploy backend/frontend and verify environment — Owner: DevOps
- [ ] Check secrets and public repository — Owner: Repo lead
- [ ] Finalize README, architecture docs, and screenshots — Owner: Documentation
- [ ] Record under-3-minute demo video — Owner: Demo lead
- [ ] Submit Devpost entry early — Owner: Representative

## Operating rule
A task is not done just because a coding agent generated code. It is done after the team runs it, observes the expected behavior, tests failure paths, and updates the docs if needed.
