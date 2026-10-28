"""Idempotent seed data for demo shipments and synthetic freight quotes."""

from datetime import date, datetime, timezone
from decimal import Decimal
from sqlalchemy.orm import Session

from app.db.models import Shipment, Quote

DEMO_SHIPMENT_ID = "demo-shipment-001"


def seed_demo_data(db: Session) -> Shipment:
    """Seed initial demo shipment and 3 synthetic freight quotes if not present."""
    existing_shipment = db.query(Shipment).filter(Shipment.id == DEMO_SHIPMENT_ID).first()
    if existing_shipment:
        return existing_shipment

    # Create demo shipment
    demo_shipment = Shipment(
        id=DEMO_SHIPMENT_ID,
        cargo_type="Agricultural Grain Bulk",
        quantity_tonnes=Decimal("25000.00"),
        origin="Port of Santos, Brazil",
        destination="Port of Rotterdam, Netherlands",
        ready_date=date(2026, 11, 10),
        required_arrival_date=date(2026, 12, 5),
        currency="USD",
        mode="DEMO",
    )
    db.add(demo_shipment)
    db.flush()

    # Quote 1: Baseline balanced offer (low concern)
    quote1 = Quote(
        id="quote-demo-001",
        shipment_id=DEMO_SHIPMENT_ID,
        provider_label="Atlantic Bulk Carriers (Demo)",
        reference="ABC-2026-881",
        base_amount=Decimal("28500.00"),
        surcharge_amount=Decimal("4500.00"),
        total_amount=Decimal("33000.00"),
        currency="USD",
        transit_days=18,
        validity_until=datetime(2026, 11, 20, 23, 59, 59, tzinfo=timezone.utc),
        vessel_class="Supramax Bulk Carrier",
        cargo_capacity_tonnes=Decimal("32000.00"),
        terms={
            "fuel_surcharge": 3000.00,
            "port_dues": 1500.00,
            "payment_terms": "net_30",
            "advance_pct": 0,
            "itemized": True,
        },
        source_kind="SYNTHETIC_DEMO",
    )

    # Quote 2: Fast transit, high price, unitemized surcharges, 100% advance term
    quote2 = Quote(
        id="quote-demo-002",
        shipment_id=DEMO_SHIPMENT_ID,
        provider_label="Global Express Maritime (Demo)",
        reference="GEM-2026-104",
        base_amount=Decimal("42000.00"),
        surcharge_amount=Decimal("0.00"),
        total_amount=Decimal("42000.00"),
        currency="USD",
        transit_days=14,
        validity_until=datetime(2026, 11, 25, 23, 59, 59, tzinfo=timezone.utc),
        vessel_class="Panamax Bulk Carrier",
        cargo_capacity_tonnes=Decimal("55000.00"),
        terms={
            "payment_terms": "100% advance required",
            "advance_pct": 100,
            "itemized": False,
        },
        source_kind="SYNTHETIC_DEMO",
    )

    # Quote 3: Low price outlier, expired validity, capacity mismatch (20k tonnes < 25k tonnes)
    quote3 = Quote(
        id="quote-demo-003",
        shipment_id=DEMO_SHIPMENT_ID,
        provider_label="Pacific Star Freight (Demo)",
        reference="PSF-2026-442",
        base_amount=Decimal("14000.00"),
        surcharge_amount=Decimal("2000.00"),
        total_amount=Decimal("16000.00"),
        currency="USD",
        transit_days=28,
        validity_until=datetime(2026, 10, 15, 23, 59, 59, tzinfo=timezone.utc),
        vessel_class="Handysize Vessel",
        cargo_capacity_tonnes=Decimal("20000.00"),
        terms={
            "fuel_surcharge": 2000.00,
            "demurrage_rate_daily": 6500.00,
            "itemized": True,
        },
        source_kind="SYNTHETIC_DEMO",
    )

    db.add_all([quote1, quote2, quote3])
    db.commit()
    db.refresh(demo_shipment)
    return demo_shipment


def reset_demo_data(db: Session) -> Shipment:
    """Clear and re-seed demo shipment and quotes."""
    shipment = db.query(Shipment).filter(Shipment.id == DEMO_SHIPMENT_ID).first()
    if shipment:
        db.delete(shipment)
        db.commit()
    return seed_demo_data(db)
