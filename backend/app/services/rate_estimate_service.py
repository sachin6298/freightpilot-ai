"""Freight rate estimation and benchmark service.

Uses transparent statistical aggregation (median, min, max) over available
quotes. Does NOT claim to be a trained machine-learning model or live market feed.
"""

from decimal import Decimal
import statistics
from typing import Optional

from app.db.models import Quote, Shipment


class RateEstimate:
    """Rate estimation result."""

    def __init__(
        self,
        currency: str,
        median_rate: Optional[Decimal],
        min_rate: Optional[Decimal],
        max_rate: Optional[Decimal],
        sample_size: int,
        coverage_status: str,
        method: str,
        disclaimer: str,
    ):
        self.currency = currency
        self.median_rate = median_rate
        self.min_rate = min_rate
        self.max_rate = max_rate
        self.sample_size = sample_size
        self.coverage_status = coverage_status
        self.method = method
        self.disclaimer = disclaimer

    def to_dict(self) -> dict:
        return {
            "currency": self.currency,
            "median_rate": float(self.median_rate) if self.median_rate is not None else None,
            "min_rate": float(self.min_rate) if self.min_rate is not None else None,
            "max_rate": float(self.max_rate) if self.max_rate is not None else None,
            "sample_size": self.sample_size,
            "coverage_status": self.coverage_status,
            "method": self.method,
            "disclaimer": self.disclaimer,
        }


def calculate_shipment_estimate(shipment: Shipment, peer_quotes: list[Quote]) -> RateEstimate:
    """Calculate rate estimate baseline from comparable quotes for the shipment."""
    matching_amounts = [
        Decimal(str(q.total_amount))
        for q in peer_quotes
        if q.currency == shipment.currency
    ]

    method = "Statistical median and spread across available quotes in dataset"
    disclaimer = (
        "Demo estimate derived from sample observations in this prototype. "
        "Not a live market feed, trained ML forecast, or binding commercial quote."
    )

    if len(matching_amounts) >= 2:
        median_val = statistics.median(matching_amounts).quantize(Decimal("0.01"))
        min_val = min(matching_amounts)
        max_val = max(matching_amounts)
        return RateEstimate(
            currency=shipment.currency,
            median_rate=median_val,
            min_rate=min_val,
            max_rate=max_val,
            sample_size=len(matching_amounts),
            coverage_status="REPRESENTATIVE_DEMO",
            method=method,
            disclaimer=disclaimer,
        )

    # Insufficient data scenario
    return RateEstimate(
        currency=shipment.currency,
        median_rate=None,
        min_rate=None,
        max_rate=None,
        sample_size=len(matching_amounts),
        coverage_status="INSUFFICIENT_DATA",
        method=method,
        disclaimer="Insufficient comparable observations to establish rate range.",
    )


def calculate_variance_vs_median(quote_amount: Decimal, median_rate: Optional[Decimal]) -> Optional[float]:
    """Calculate percentage variance between a quote and the median benchmark."""
    if median_rate is None or median_rate == 0:
        return None
    variance = ((quote_amount - median_rate) / median_rate) * Decimal("100")
    return float(variance.quantize(Decimal("0.1")))
