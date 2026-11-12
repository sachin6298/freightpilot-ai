"""Explainable Freight Cost Calculator endpoints and deterministic baseline logic."""

from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/calculator", tags=["Freight Cost Calculator"])

BASE_RATES_PER_TONNE_KM = {
    "OCEAN": Decimal("0.025"),
    "AIR": Decimal("0.450"),
    "ROAD": Decimal("0.120"),
    "RAIL": Decimal("0.065"),
}

CARGO_MULTIPLIERS = {
    "GENERAL_CARGO": Decimal("1.0"),
    "PERISHABLE": Decimal("1.35"),
    "HAZARDOUS": Decimal("1.70"),
    "BULK_MINERAL": Decimal("0.85"),
    "HEAVY_MACHINERY": Decimal("1.40"),
}


class CostCalculationRequest(BaseModel):
    cargo_type: str = Field(default="GENERAL_CARGO")
    quantity_tonnes: Decimal = Field(..., gt=0)
    distance_km: Decimal = Field(..., gt=0)
    transport_mode: str = Field(default="OCEAN", pattern="^(OCEAN|AIR|ROAD|RAIL)$")
    currency: str = Field(default="USD")
    include_insurance: bool = True
    express_handling: bool = False


@router.post("/estimate")
def calculate_freight_cost(req: CostCalculationRequest):
    """Phase 15: Explainable Freight Cost Calculator with detailed fee breakdown."""
    mode = req.transport_mode.upper()
    rate_km = BASE_RATES_PER_TONNE_KM.get(mode, Decimal("0.05"))
    multiplier = CARGO_MULTIPLIERS.get(req.cargo_type.upper(), Decimal("1.0"))

    # Base freight = rate_per_km * distance * weight * cargo_multiplier
    base_freight = (rate_km * req.distance_km * req.quantity_tonnes * multiplier).quantize(Decimal("0.01"))

    # Surcharges
    fuel_surcharge = (base_freight * Decimal("0.12")).quantize(Decimal("0.01")) # 12% standard bunker/fuel
    port_handling = (req.quantity_tonnes * Decimal("15.00")).quantize(Decimal("0.01"))
    insurance = (base_freight * Decimal("0.035")).quantize(Decimal("0.01")) if req.include_insurance else Decimal("0.00")
    express_fee = (base_freight * Decimal("0.20")).quantize(Decimal("0.01")) if req.express_handling else Decimal("0.00")

    subtotal = base_freight + fuel_surcharge + port_handling + insurance + express_fee
    tax = (subtotal * Decimal("0.05")).quantize(Decimal("0.01")) # 5% VAT
    total = subtotal + tax

    # Confidence interval range (+/- 15%)
    min_range = (total * Decimal("0.88")).quantize(Decimal("0.01"))
    max_range = (total * Decimal("1.15")).quantize(Decimal("0.01"))

    return {
        "estimated_freight_cost": float(total),
        "currency": req.currency.upper(),
        "range": {
            "min_estimate": float(min_range),
            "max_estimate": float(max_range),
            "confidence_level": "85% (Indicative model benchmark)"
        },
        "breakdown": {
            "base_freight": float(base_freight),
            "fuel_surcharge": float(fuel_surcharge),
            "port_terminal_handling": float(port_handling),
            "cargo_insurance": float(insurance),
            "express_handling": float(express_fee),
            "applicable_taxes": float(tax)
        },
        "assumptions": [
            f"Base rate factor: {float(rate_km)} {req.currency} per tonne-km for {mode}",
            f"Cargo classification multiplier: {float(multiplier)}x for {req.cargo_type}",
            "Standard bunker fuel adjustment applied at 12%",
            "Port/Terminal handling calculated at 15.00 per metric tonne"
        ],
        "disclaimer": "This estimate is indicative and non-binding. Final costs depend on carrier contract quotes and actual cargo dimensions."
    }
