"""Deterministic explainable risk assessment engine for freight quotes.

Rules strictly follow AI_RISK_ENGINE.md. All flags expose:
- code: unique identifier
- severity: 'HIGH' | 'MEDIUM' | 'LOW'
- title: concise human-readable title
- evidence: exact factual basis from quote/shipment attributes
- recommended_check: actionable verification step
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Optional

from app.db.models import Quote, Shipment
from app.services.rate_estimate_service import (
    calculate_shipment_estimate,
    calculate_variance_vs_median,
)


class RiskFlag:
    """Represents a single explainable risk finding."""

    def __init__(
        self,
        code: str,
        severity: str,
        title: str,
        evidence: str,
        recommended_check: str,
        weight: int,
    ):
        self.code = code
        self.severity = severity
        self.title = title
        self.evidence = evidence
        self.recommended_check = recommended_check
        self.weight = weight

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "severity": self.severity,
            "title": self.title,
            "evidence": self.evidence,
            "recommended_check": self.recommended_check,
        }


def assess_quote_risk(
    quote: Quote,
    shipment: Shipment,
    peer_quotes: list[Quote],
    benchmark=None,
) -> dict[str, Any]:
    """Calculate deterministic risk flags, 0-100 score, and label for a quote."""
    flags: list[RiskFlag] = []
    now = datetime.now(timezone.utc)

    # 1. Rate estimate benchmark for outlier detection
    estimate = benchmark or calculate_shipment_estimate(shipment, peer_quotes)
    median_rate = estimate.median_rate

    # Rule 1: Currency Mismatch
    if quote.currency != shipment.currency:
        flags.append(
            RiskFlag(
                code="CURRENCY_MISMATCH",
                severity="HIGH",
                title="Currency Discrepancy",
                evidence=f"Quote currency ({quote.currency}) does not match shipment currency ({shipment.currency}).",
                recommended_check="Request quote normalized in shipment currency or agree on a fixed FX benchmark.",
                weight=30,
            )
        )

    # Rule 2: Quote Price Outlier (if comparable median exists)
    if median_rate is not None and quote.currency == shipment.currency:
        quote_total = Decimal(str(quote.total_amount))
        variance = calculate_variance_vs_median(quote_total, median_rate)
        if variance is not None:
            if quote_total < Decimal("0.70") * median_rate:
                flags.append(
                    RiskFlag(
                        code="QUOTE_PRICE_OUTLIER",
                        severity="HIGH",
                        title="Significant Low-Price Outlier",
                        evidence=(
                            f"Quote total ({quote.total_amount} {quote.currency}) is {abs(variance)}% "
                            f"below the benchmark median ({median_rate} {quote.currency})."
                        ),
                        recommended_check="Verify whether essential port dues, destination handling, or bunker charges are omitted.",
                        weight=35,
                    )
                )
            elif quote_total > Decimal("1.35") * median_rate:
                flags.append(
                    RiskFlag(
                        code="QUOTE_PRICE_OUTLIER",
                        severity="HIGH",
                        title="High-Price Premium Outlier",
                        evidence=(
                            f"Quote total ({quote.total_amount} {quote.currency}) is +{variance}% "
                            f"above the benchmark median ({median_rate} {quote.currency})."
                        ),
                        recommended_check="Request justification for premium over comparable market benchmark.",
                        weight=25,
                    )
                )

    # Rule 3: Missing Fee Breakdown / Unitemized Surcharges
    terms = quote.terms or {}
    is_itemized = terms.get("itemized", True)
    if quote.surcharge_amount == 0 and not is_itemized:
        flags.append(
            RiskFlag(
                code="MISSING_FEE_BREAKDOWN",
                severity="MEDIUM",
                title="Unitemized Surcharges & Fees",
                evidence=(
                    f"Quote total ({quote.total_amount} {quote.currency}) lumps all charges with 0.00 "
                    "itemized surcharges; port terminal dues and bunker adjustment (BAF) are unspecified."
                ),
                recommended_check="Request an itemized breakdown of ocean freight vs fuel adjustment and terminal fees.",
                weight=20,
            )
        )

    # Rule 4: Quote Validity Expired
    if quote.validity_until is not None:
        validity = quote.validity_until
        # Handle naive datetime from SQLite
        if validity.tzinfo is None:
            validity = validity.replace(tzinfo=timezone.utc)
        if validity < now:
            flags.append(
                RiskFlag(
                    code="QUOTE_EXPIRED",
                    severity="HIGH",
                    title="Quote Validity Expired",
                    evidence=f"Validity expired on {validity.strftime('%Y-%m-%d')}.",
                    recommended_check="Obtain written validity extension from carrier before proceeding with booking or payment.",
                    weight=40,
                )
            )

    # Rule 5: Vessel Cargo Capacity Mismatch
    if quote.cargo_capacity_tonnes is not None and shipment.quantity_tonnes is not None:
        capacity = Decimal(str(quote.cargo_capacity_tonnes))
        quantity = Decimal(str(shipment.quantity_tonnes))
        if capacity < quantity:
            flags.append(
                RiskFlag(
                    code="CAPACITY_MISMATCH",
                    severity="HIGH",
                    title="Vessel Capacity Incompatible",
                    evidence=(
                        f"Nominated vessel capacity ({capacity:,.0f} MT) is less than required "
                        f"cargo volume ({quantity:,.0f} MT) by {(quantity - capacity):,.0f} MT."
                    ),
                    recommended_check="Verify vessel suitability or confirm whether split-shipment voyages are planned.",
                    weight=35,
                )
            )

    # Rule 6: Schedule Conflict with Arrival Window
    if shipment.required_arrival_date and quote.transit_days and shipment.ready_date:
        projected_arrival = shipment.ready_date + timedelta(days=quote.transit_days)
        if projected_arrival > shipment.required_arrival_date:
            days_late = (projected_arrival - shipment.required_arrival_date).days
            flags.append(
                RiskFlag(
                    code="SCHEDULE_CONFLICT",
                    severity="HIGH",
                    title="Schedule Conflict / Late ETA",
                    evidence=(
                        f"Estimated arrival ({projected_arrival.strftime('%Y-%m-%d')}) exceeds the "
                        f"required arrival deadline ({shipment.required_arrival_date.strftime('%Y-%m-%d')}) by {days_late} days."
                    ),
                    recommended_check="Verify actual vessel sailing dates and confirm whether accelerated transit is possible.",
                    weight=30,
                )
            )

    # Rule 7: Advance Payment Terms Review
    advance_pct = terms.get("advance_pct")
    try:
        high_advance = advance_pct is not None and Decimal(str(advance_pct)) >= Decimal("50")
    except (InvalidOperation, TypeError, ValueError):
        high_advance = False
    payment_terms_str = str(terms.get("payment_terms", "")).lower()
    if high_advance or "100% advance" in payment_terms_str:
        flags.append(
            RiskFlag(
                code="ADVANCE_TERM_REVIEW",
                severity="MEDIUM",
                title="Substantial Advance Payment Requested",
                evidence=f"Payment terms require {advance_pct if high_advance else 100}% upfront advance before cargo release.",
                recommended_check="Review commercial terms and check if carrier provides letter of credit or escrow.",
                weight=25,
            )
        )

    # Rule 8: Insufficient Observations in Dataset
    if len(peer_quotes) < 2:
        flags.append(
            RiskFlag(
                code="INSUFFICIENT_DATA",
                severity="LOW",
                title="Limited Benchmark Observations",
                evidence="Fewer than 2 comparable quotes exist in the current dataset to establish statistical baseline.",
                recommended_check="Obtain additional carrier offers to evaluate rate competitiveness.",
                weight=10,
            )
        )

    # Compute Total Score (0 - 100)
    raw_score = sum(f.weight for f in flags)
    score = min(100, raw_score)

    # Map to Classification Label
    if score >= 50:
        label = "HIGH_ATTENTION"
    elif score >= 25:
        label = "REVIEW"
    elif len(peer_quotes) < 2 and len(flags) == 1 and flags[0].code == "INSUFFICIENT_DATA":
        label = "INSUFFICIENT_DATA"
    else:
        label = "LOWER_CONCERN"

    # Compute variance vs median if possible
    variance_pct = None
    if median_rate is not None and quote.currency == shipment.currency:
        variance_pct = calculate_variance_vs_median(Decimal(str(quote.total_amount)), median_rate)

    return {
        "score": score,
        "label": label,
        "flags": [f.to_dict() for f in flags],
        "method_version": "v1.0-rules",
        "benchmark_variance_pct": variance_pct,
    }
