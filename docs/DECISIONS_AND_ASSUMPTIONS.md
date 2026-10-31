# Decisions and Assumptions Log

## Confirmed direction
- Product: FreightPilot AI.
- Domain: freight quote evaluation and buyer-approved quote-to-payment workflow.
- Competition: PayPal AI Hackathon “Build What's Next with PayPal and AI.”
- Payments: PayPal Sandbox for the submission demo.
- Main frontend: React + TypeScript + Vite, matching the approach used in the prior AI Risk Manager work.
- Backend: FastAPI to keep AI/risk and payment REST calls server-side.
- AI: quote explanation grounded in structured data plus transparent rule-based flags.
- Rate estimate: documented baseline over demo/historical inputs; never falsely call seeded data real-time market data.

## Assumptions to validate
1. Team wants to reuse knowledge from its previous React/FastAPI/ML app rather than switching to Next.js.
2. First demo uses three synthetic/sample quotes and a fixed supported currency.
3. PayPal Sandbox accounts and developer credentials can be created successfully.
4. The selected AI API is available to the team and permitted for hackathon use.
5. Database begins as SQLite locally; a persistent hosted database is selected before deployment.

## Not assumed
- There is no official fixed problem statement for this hackathon; this project charter is proposed by the team.
- No real carrier identity, vessel capacity, port draft, freight price, or quote is verified unless an actual data source is implemented.
- No production transaction eligibility is inferred from Sandbox success.
- No escrow, payout split, seller onboarding, or marketplace settlement capability is included.
- No model accuracy is claimed until measured on appropriate held-out data.

## Decisions that require a conscious change
- Changing the payment recipient/business model.
- Supporting more than one currency in the same quote comparison.
- Switching PayPal from Sandbox to live credentials.
- Introducing real user accounts, uploads, or live vendor data.
- Allowing AI or agents to take a payment action without direct user approval.

Log any change with date, reason, impact, and tests required.
