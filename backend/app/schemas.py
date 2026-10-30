"""Pydantic schemas for request validation and response serialization."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

SUPPORTED_CURRENCIES = {"USD", "EUR", "GBP"}


class ShipmentCreate(BaseModel):
    """Schema for creating a shipment."""

    cargo_type: str = Field(..., min_length=2, max_length=100, description="Cargo description or category")
    quantity_tonnes: Decimal = Field(..., gt=0, description="Quantity in metric tonnes (must be positive)")
    origin: str = Field(..., min_length=2, max_length=150, description="Origin port or region")
    destination: str = Field(..., min_length=2, max_length=150, description="Destination port or region")
    ready_date: date = Field(..., description="Cargo ready date")
    required_arrival_date: Optional[date] = Field(None, description="Target arrival date")
    currency: str = Field(default="USD", description="Currency for comparison")

    @model_validator(mode="after")
    def validate_shipment(self) -> "ShipmentCreate":
        # Origin and destination must differ
        if self.origin.strip().lower() == self.destination.strip().lower():
            raise ValueError("Origin and destination must be different ports or locations.")

        # Arrival date must be on or after ready date
        if self.required_arrival_date and self.required_arrival_date < self.ready_date:
            raise ValueError("Required arrival date cannot be earlier than ready date.")

        # Currency validation
        cur = self.currency.strip().upper()
        if cur not in SUPPORTED_CURRENCIES:
            raise ValueError(f"Currency '{self.currency}' is not supported. Must be one of {sorted(SUPPORTED_CURRENCIES)}.")
        self.currency = cur

        return self


class ShipmentResponse(BaseModel):
    """Schema for shipment details response."""

    id: str
    cargo_type: str
    quantity_tonnes: Decimal
    origin: str
    destination: str
    ready_date: date
    required_arrival_date: Optional[date]
    currency: str
    mode: str
    created_at: datetime
    updated_at: datetime
    quotes_count: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class QuoteCreate(BaseModel):
    """Schema for creating a freight quote."""

    shipment_id: Optional[str] = Field(None, description="Associated shipment ID")
    provider_label: str = Field(..., min_length=2, max_length=150, description="Carrier or broker name")
    reference: str = Field(..., min_length=2, max_length=100, description="Internal or carrier quote reference")
    base_amount: Decimal = Field(..., ge=0, description="Base freight rate")
    surcharge_amount: Decimal = Field(default=Decimal("0.00"), ge=0, description="Surcharges and fees")
    total_amount: Optional[Decimal] = Field(None, ge=0, description="Total amount (must equal base + surcharges)")
    currency: str = Field(default="USD", description="Quote currency")
    transit_days: Optional[int] = Field(None, ge=1, description="Estimated transit days")
    validity_until: Optional[datetime] = Field(None, description="Expiry timestamp")
    vessel_class: Optional[str] = Field(None, max_length=100, description="Vessel type or class")
    cargo_capacity_tonnes: Optional[Decimal] = Field(None, gt=0, description="Declared vessel cargo capacity")
    terms: Optional[dict[str, Any]] = Field(None, description="Structured quote terms")
    source_kind: str = Field(default="SYNTHETIC_DEMO", description="Data source identifier")

    @model_validator(mode="after")
    def validate_amounts_and_currency(self) -> "QuoteCreate":
        cur = self.currency.strip().upper()
        if cur not in SUPPORTED_CURRENCIES:
            raise ValueError(f"Currency '{self.currency}' is not supported.")
        self.currency = cur

        expected_total = self.base_amount + self.surcharge_amount
        if self.total_amount is not None:
            if self.total_amount != expected_total:
                raise ValueError(
                    f"Total amount ({self.total_amount}) must equal base ({self.base_amount}) + surcharges ({self.surcharge_amount}) = {expected_total}."
                )
        else:
            self.total_amount = expected_total

        return self


class RiskFlagResponse(BaseModel):
    """Explainable risk indicator flag."""

    code: str
    severity: str
    title: str
    evidence: str
    recommended_check: str


class RiskAssessmentResponse(BaseModel):
    """Structured assessment output."""

    score: int = Field(..., ge=0, le=100)
    label: str
    flags: list[RiskFlagResponse]
    method_version: str = "v1.0-rules"
    benchmark_variance_pct: Optional[float] = None
    assessed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class RateEstimateResponse(BaseModel):
    """Statistical rate estimate baseline."""

    currency: str
    median_rate: Optional[float]
    min_rate: Optional[float]
    max_rate: Optional[float]
    sample_size: int
    coverage_status: str
    method: str
    disclaimer: str


class QuoteResponse(BaseModel):
    """Schema for quote response enriched with risk assessment and benchmark comparison."""

    id: str
    shipment_id: str
    provider_label: str
    reference: str
    base_amount: Decimal
    surcharge_amount: Decimal
    total_amount: Decimal
    currency: str
    transit_days: Optional[int]
    validity_until: Optional[datetime]
    vessel_class: Optional[str]
    cargo_capacity_tonnes: Optional[Decimal]
    terms: Optional[dict[str, Any]]
    source_kind: str
    created_at: datetime
    assessment: Optional[RiskAssessmentResponse] = None
    benchmark_variance_pct: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class ErrorDetail(BaseModel):
    """Standardized error structure per API_SPEC.md."""

    code: str
    message: str


class ErrorResponse(BaseModel):
    """Standardized error wrapper."""

    error: ErrorDetail


class CopilotRequest(BaseModel):
    """Schema for copilot comparison request."""

    shipment_id: str
    quote_ids: list[str]


class ComparisonDetail(BaseModel):
    """Schema for quote comparison detail."""

    quote_id: str
    advantages: list[str]
    concerns: list[str]


class CopilotResponse(BaseModel):
    """Schema for copilot comparison output."""

    summary: str
    comparison: list[ComparisonDetail]
    missing_information: list[str]
    next_questions: list[str]
    disclaimer: str = "Human review required; outputs are estimates."
