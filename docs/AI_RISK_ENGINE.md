# AI and Risk Engine

## Purpose
Provide an explainable decision-support layer that helps a buyer inspect quote anomalies and trade-offs before making a payment decision. It is not a regulated risk decision, fraud guarantee, or substitute for shipping/legal due diligence.

## Use two separate components
1. **Deterministic assessment:** calculates flags from known structured fields.
2. **AI explanation:** converts those flags and quote facts into a readable summary and follow-up questions.

Keep the separation visible in code and in the UI.

## Risk indicators for MVP
Each flag should contain `code`, `severity`, `title`, `evidence`, and `recommended_check`.

Examples:
- `MISSING_FEE_BREAKDOWN`: quote total exists but included fees are not itemized.
- `QUOTE_PRICE_OUTLIER`: total differs materially from comparable quotes in the same currency/units. Configure a threshold and state it in docs; do not imply statistical certainty.
- `QUOTE_EXPIRED`: validity date is before the current date.
- `CAPACITY_MISMATCH`: cargo quantity exceeds a declared vessel/capacity field.
- `SCHEDULE_CONFLICT`: estimated transit/dates conflict with the requested arrival window.
- `ADVANCE_TERM_REVIEW`: advance request exceeds a configurable demo threshold and terms need human review.
- `CURRENCY_MISMATCH`: quotes in the same comparison use different currencies or missing conversion evidence.
- `INSUFFICIENT_DATA`: not enough observations exist to estimate a rate range.

Score mechanics should be transparent. Example: assign a small weighted score to each flag, clamp to 0–100, and map to “Lower concern / Review / High attention.” Document weights and emphasize that a high score means review priority, not proven fraud. Unknown facts must not receive a positive/safe score.

## Freight rate estimate
For the hackathon baseline, use a reproducible method such as a median from comparable seeded observations by cargo class, route group, vessel class, and time bucket. A simple rolling median or exponential moving average is acceptable if described honestly. Provide a range (for example, selected quantiles when there is enough sample data). If the demo dataset is synthetic, display that fact. Do not claim live market data unless a licensed live source is genuinely connected.

## AI copilot contract
Input only necessary fields:
- shipment summary;
- list of quote IDs and normalized totals/currencies;
- structured risks with evidence;
- estimate method/coverage;
- explicit instruction to say when information is missing.

Suggested output schema:
```json
{
  "summary": "string",
  "comparison": [
    {"quote_id": "string", "advantages": ["string"], "concerns": ["string"]}
  ],
  "missing_information": ["string"],
  "next_questions": ["string"],
  "disclaimer": "Human review required; outputs are estimates."
}
```

Validate the model output against a schema. If malformed, show a graceful fallback using the deterministic flags.

## Guardrails
- AI does not create a PayPal order, choose a payment amount, trigger capture, or approve a payment.
- AI must not say it verified a carrier, vessel, port, market quote, or sanctions status without a connected and validated source.
- Treat uploaded quote text as untrusted input; ignore prompt instructions embedded in the document.
- Do not send PayPal secrets, full payment credentials, or unnecessary personally identifying information to the AI provider.
- Keep user approval separate from an AI recommendation.

## Evaluation
Create fixed test cases: clear low-concern quote, missing fee details, expired quote, obvious price outlier, capacity mismatch, insufficient observations, and malformed AI output. Check that each reason is repeatable and the AI summary matches rather than contradicts the flags.

## Honest claims
Say “AI-assisted quote review” or “risk indicators.” Do not claim a trained fraud model, real-time market forecast, predictive accuracy, or verified fraud detection unless the team has data and evaluation to support it.
