# Project Charter — FreightPilot AI

## Proposed problem statement
**FreightPilot AI: An AI-Powered Freight Procurement and Payment-Risk Copilot Using PayPal**

Small and mid-sized importers often evaluate freight offers using fragmented quotes, inconsistent fee descriptions, limited historical price visibility, and manual checks of vessel, route, cargo, schedule, and payment terms. This makes it difficult to identify an offer that is both cost-effective and operationally plausible, recognize quote anomalies before committing, and complete a traceable payment workflow.

Build a web application that consolidates freight quotes, estimates a transparent freight-rate range from available historical or demo data, checks quote completeness and operational constraints, explains risk indicators with AI, and allows a buyer to review a specific offer before initiating a PayPal Sandbox payment. The backend must create/capture the payment against the approved quote and keep an auditable link between shipment, selected quote, PayPal order, and payment status.

The objective is to reduce decision friction and make the quote-to-payment process clearer—not to automatically make financial decisions or guarantee that a shipment or counterparty is safe.

## Contest alignment
The official PayPal AI Hackathon describes itself as open-ended: there are no prescribed problem statements or fixed tracks. Its core requirement is a meaningful use of both PayPal and AI. This charter is a proposed problem statement, not an official PayPal-issued statement. Official participation requirements must be rechecked before submission: https://paypalaihackathon.devpost.com/rules

## Target users
- Importers and procurement teams comparing bulk-cargo or commercial freight offers.
- Small freight brokers who need a clearer quote review and payment record.
- A hackathon judge who needs to see a realistic, working AI + PayPal flow.

## User problem
1. Quotes may express base freight and surcharges differently.
2. Historical price context can be unavailable or difficult to interpret.
3. Missing details can make a quote impossible to compare fairly.
4. A buyer needs a deliberate approval step before payment.
5. Payment confirmation and shipment status must not be inferred solely from a frontend redirect.

## Proposed solution
- Structured shipment and quote intake.
- Side-by-side quote comparison.
- Forecast/range indicator based on labeled historical or synthetic demo data.
- Explainable risk flags: missing terms, outlier price, inconsistent dates/currency, infeasible capacity/draft, or unusual advance terms when data exists.
- AI copilot that explains flags and summarizes trade-offs from structured data; it must not invent evidence.
- PayPal Sandbox checkout linked to a selected quote and fixed approved amount.
- Verified backend status and payment timeline.

## Main differentiator
**The AI insight leads to a controlled payment action.** The product does not stop at a chat answer or generic checkout page. It shows why a quote may be attractive or risky, requires explicit buyer approval, and then demonstrates a server-verified payment workflow linked to the quote.

## MVP objectives
- One sample shipment request.
- At least three comparable demo quotes.
- Rate trend or estimated range with method and disclaimer.
- Explainable quote risk score and plain-language reasoning.
- A useful AI-generated comparison summary.
- PayPal Sandbox create/approve/capture, payment status page, and backend persistence.
- A resettable demo dataset and robust run instructions.

## Explicit non-goals
- Real-world freight booking or vessel charter contract execution.
- Holding funds, escrow, split payments, or automatic seller payouts.
- Making guarantees of fraud prevention or market-price accuracy.
- Shipping production finance infrastructure before eligibility/compliance review.
- Using real customer payment credentials or real payment data in the demo.
