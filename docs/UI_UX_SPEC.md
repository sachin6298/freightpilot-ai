# UI/UX Specification

## Product tone
Reliable, modern B2B logistics software. Avoid crypto-style visuals, exaggerated AI claims, faux real-time market data, and payment success animations before backend confirmation.

## Navigation
- Overview
- Shipments
- Quote comparison
- Payment activity
- Settings / demo status

## Main screens
### 1. Overview
- Header: `FreightPilot AI` and `Sandbox Demo` pill.
- KPI cards: active shipment, quotes compared, high-priority flags, recent successful sandbox payments.
- Main panel: current shipment and next recommended action.
- Timeline panel: quote selected → PayPal approved → capture verified.

### 2. Shipment details
- Cargo details and route.
- Freight estimate card with method/data date.
- Quote table/cards with sortable total, transit time, feasibility, and risk.
- Click quote to open detail.

### 3. Quote details
- Cost breakdown and terms.
- Risk flags with severity and reason.
- “Ask Freight Copilot” prompt buttons and generated summary.
- Explicit `Select this quote` action.

### 4. Checkout review
- Selected quote and shipment references.
- Exact amount and currency, copied from backend response.
- What's included / what's excluded.
- `Sandbox payment — no real money` disclosure.
- PayPal button. Prevent repeated clicks while a request is in flight.

### 5. Payment result
- Status badge uses the backend-confirmed state.
- Provider/internal reference IDs.
- `Back to shipment` and `Refresh status` actions.
- Failure state shows safe recovery instructions, not raw stack traces.

## Visual behavior
- Consistent spacing, typography, focus states, and responsive layout.
- Color is not the only status signal: include labels/icons and readable text.
- Show loading and empty states; do not leave blank panels during API failure.
- For risk: show reason list and data quality, not a single mysterious number.
- For payment: success only after backend confirmation; approved-but-not-captured is a distinct state.

## Accessibility baseline
- Keyboard-navigable forms and dialogs.
- Label all form inputs.
- Maintain visible focus state and sufficient color contrast.
- Announce asynchronous checkout/AI result updates to screen readers when practical.
