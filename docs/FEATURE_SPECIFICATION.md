# Feature Specification

## 1. Dashboard
Show active demo shipment, current quotes, average/range context, risk summary, and recent payment events. At top, display a clear `SANDBOX DEMO` indicator.

## 2. Shipment request
Fields for cargo type, quantity/weight, origin port/region, destination port/region, earliest ready date, required arrival date, vessel/capacity requirement, and preferred currency. Keep the demo input short; advanced details can be prefilled.

Validation: quantity must be positive; dates must be valid; origin and destination must differ; currency must be from the supported demo list. Never infer port feasibility without the required fields.

## 3. Quote comparison
Each quote should show:
- Carrier/broker demo name and quote reference.
- Route and vessel class/type if available.
- Freight base amount, surcharges, total, currency, and what is included.
- Estimated transit time and validity/expiry date.
- Payment terms/advance request when supplied.
- Feasibility flags (e.g., capacity constraint or missing port draft).
- AI/rule-based risk label with reasons.

Sort by total comparable cost, ETA, or risk. Do not compare unlike currencies without a clearly labeled conversion source and timestamp; for MVP use one currency per comparison.

## 4. Freight-rate estimate
Show a range, not false precision. Include method and coverage such as “Demo estimate based on available sample observations; not a market quote.” Include sample size/last updated when known. If there is not enough data, show `insufficient data` rather than a made-up forecast.

## 5. Explainable risk assessment
Potential flags:
- Required field missing.
- Quote price is an outlier relative to comparable quotes.
- Quote expired or validity is unclear.
- Transit/arrival date is inconsistent.
- Cargo weight exceeds stated vessel capacity.
- Required port/vessel constraint appears incompatible.
- Fees or payment terms are not itemized.
- Unusually high advance fraction, if advance details are supplied.

Each flag must show: trigger, severity, input evidence, and suggested verification step. An overall score is a prioritization signal, not a claim of fraud.

## 6. AI Freight Copilot
Prompts users can click:
- “Compare these offers.”
- “Explain the highest-risk quote.”
- “What information is missing before I accept?”
- “Summarize cost vs transit-time trade-offs.”

AI must be grounded in selected quote data and rule-engine outputs. Ask it to return a structured summary with `summary`, `pros`, `concerns`, `missing_information`, and `next_questions`. The UI must retain the structured source fields alongside the generated summary.

## 7. Payment review and checkout
Before calling PayPal, show quote reference, amount, currency, seller/recipient label, and clear sandbox notice. The user must confirm. Backend fetches the amount from the saved quote; frontend cannot choose an arbitrary amount.

## 8. Payment result/history
States: `PENDING`, `APPROVED`, `CAPTURED`, `FAILED`, `CANCELLED`, `REFUNDED`, `REVIEW_REQUIRED`. Show provider order/capture reference, internal quote/shipment reference, amount/currency, and timestamps. The source of truth is the backend record reconciled to PayPal—not the checkout redirect.

## 9. Demo controls
Seed deterministic sample data and provide a reset action restricted to demo mode. Never seed or print real credentials. A reset must not change a true provider transaction record into a fake state; only reset internal demo shipments/quotes and clearly handle existing payment rows.
