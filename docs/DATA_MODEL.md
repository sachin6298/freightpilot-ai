# Data Model

Use SQLAlchemy/Pydantic models or an equivalent typed persistence approach. Keep provider response payloads minimal; avoid storing unnecessary buyer data.

## `shipments`
| Field | Type | Notes |
|---|---|---|
| id | UUID/string | Primary key |
| cargo_type | string | Required demo category |
| quantity_tonnes | decimal | Positive quantity |
| origin | string | Port/region label; validate real data only if integrations exist |
| destination | string | Port/region label |
| ready_date | date | Required if used for feasibility |
| required_arrival_date | date/null | Optional target |
| currency | string | Fixed supported currency for quote comparison |
| mode | enum | `DEMO` for seeded prototype |
| created_at / updated_at | timestamp | UTC |

## `quotes`
| Field | Type | Notes |
|---|---|---|
| id | UUID/string | Primary key |
| shipment_id | FK | Parent shipment |
| provider_label | string | Seeded carrier/broker display name, not a verified identity claim |
| reference | string | Internal quote reference |
| base_amount | decimal | Non-negative |
| surcharge_amount | decimal | Non-negative; itemization may be a JSON child/table |
| total_amount | decimal | Computed or verified from fee components on server |
| currency | string | Must match shipment comparison currency for MVP |
| transit_days | integer/null | Explain if estimated |
| validity_until | timestamp/null | Quote expiry |
| vessel_class | string/null | Optional demo field |
| cargo_capacity_tonnes | decimal/null | Optional feasibility signal |
| terms | JSON/text | Structured terms; treat uploaded/user text as untrusted |
| source_kind | enum | `SYNTHETIC_DEMO`, `USER_INPUT`, or licensed external source |
| created_at | timestamp | UTC |

## `risk_assessments`
| Field | Type | Notes |
|---|---|---|
| id | UUID/string | Primary key |
| quote_id | FK | Assessed quote |
| score | integer | 0–100 prioritization index, not fraud probability |
| label | enum | `LOWER_CONCERN`, `REVIEW`, `HIGH_ATTENTION`, `INSUFFICIENT_DATA` |
| flags | JSON | Structured code, severity, evidence, suggested check |
| method_version | string | Reproducibility |
| assessed_at | timestamp | UTC |

## `payments`
| Field | Type | Notes |
|---|---|---|
| id | UUID/string | Internal primary key |
| shipment_id | FK | Associated shipment |
| quote_id | FK | Selected quote |
| amount_snapshot | decimal | Exact amount used at order creation |
| currency_snapshot | string | Exact currency used at order creation |
| provider | string | `paypal_sandbox` for demo |
| provider_order_id | string | Unique where possible |
| provider_capture_id | string/null | Provider capture reference |
| status | enum | Controlled state machine |
| idempotency_key | string | Prevent duplicate create requests |
| last_verified_at | timestamp/null | Last backend/provider reconciliation |
| created_at / updated_at | timestamp | UTC |

## `webhook_events`
| Field | Type | Notes |
|---|---|---|
| id | UUID/string | Internal key |
| provider_event_id | string | Unique/deduplication key |
| event_type | string | PayPal event name |
| verification_status | enum | `VERIFIED`/`REJECTED` |
| processing_status | enum | `RECEIVED`/`PROCESSED`/`FAILED` |
| received_at | timestamp | UTC |

## Relationships
- One shipment has many quotes.
- One quote may have multiple assessment versions over time.
- A payment belongs to exactly one shipment and selected quote.
- One payment may reference one provider order and, after capture, a provider capture ID.
- Many webhook deliveries may exist, but a provider event ID is processed once.

## Integrity rules
- Use decimals, not binary floating-point, for monetary storage and arithmetic.
- Persist amount/currency snapshots because the original quote could later change.
- Validate total against components in server logic.
- Never store client secrets, access tokens, payment card data, or full unneeded webhook payloads.
- Treat synthetic test rows as demo rows and keep their provenance visible.
