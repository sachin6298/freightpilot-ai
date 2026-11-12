"""Carrier connector discovery and normalized quote refresh endpoint."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.access import get_accessible_shipment
from app.core.audit import write_audit
from app.core.security import get_optional_current_user
from app.db.models import Quote, RiskAssessment, User
from app.db.session import get_db
from app.schemas import QuoteCreate
from app.services.carrier_service import carrier_registry
from app.services.rate_estimate_service import calculate_shipment_estimate
from app.services.risk_service import assess_quote_risk

router = APIRouter(prefix="/api", tags=["Carrier Integrations"])


@router.get("/carriers")
def list_carriers():
    configured = carrier_registry.list()
    return {
        "items": configured,
        "live_integrations_available": bool(configured),
        "note": None if configured else (
            "No live carrier API adapter is configured. Existing quote records are manual or "
            "SYNTHETIC_DEMO data; do not present them as live carrier responses."
        ),
    }


@router.post("/shipments/{shipment_id}/refresh-quotes")
def refresh_carrier_quotes(
    shipment_id: str, carrier_code: str,
    db: Session = Depends(get_db), user: User | None = Depends(get_optional_current_user),
):
    shipment = get_accessible_shipment(db, shipment_id, user)
    adapter = carrier_registry.get(carrier_code)
    if adapter is None:
        raise HTTPException(status_code=501, detail={
            "code": "CARRIER_NOT_CONFIGURED",
            "message": "No live adapter is configured for this carrier. Add a provider adapter and credentials first.",
        })

    offers = adapter.fetch_quotes(shipment)
    created: list[Quote] = []
    for offer in offers:
        payload_data = {**offer, "source_kind": "CARRIER_API"}
        try:
            payload = QuoteCreate.model_validate(payload_data)
        except Exception as exc:
            raise HTTPException(status_code=502, detail={
                "code": "CARRIER_RESPONSE_INVALID", "message": "Carrier adapter returned an invalid normalized quote.",
            }) from exc
        if payload.currency != shipment.currency:
            raise HTTPException(status_code=502, detail={
                "code": "CARRIER_CURRENCY_MISMATCH", "message": "Carrier quote currency differs from shipment comparison currency.",
            })
        quote = Quote(
            shipment_id=shipment.id, provider_label=payload.provider_label,
            reference=payload.reference, base_amount=payload.base_amount,
            surcharge_amount=payload.surcharge_amount, total_amount=payload.total_amount,
            currency=payload.currency, transit_days=payload.transit_days,
            validity_until=payload.validity_until, vessel_class=payload.vessel_class,
            cargo_capacity_tonnes=payload.cargo_capacity_tonnes, terms=payload.terms,
            source_kind="CARRIER_API",
        )
        db.add(quote)
        created.append(quote)

    db.flush()
    all_quotes = db.query(Quote).filter(Quote.shipment_id == shipment.id).all()
    benchmark = calculate_shipment_estimate(shipment, all_quotes)
    for quote in created:
        risk = assess_quote_risk(quote, shipment, all_quotes, benchmark=benchmark)
        db.add(RiskAssessment(
            quote_id=quote.id, score=risk["score"], label=risk["label"],
            flags=risk["flags"], method_version=risk["method_version"],
        ))
    if created and shipment.status == "DRAFT":
        shipment.status = "QUOTED"
    write_audit(db, entity_type="SHIPMENT", entity_id=shipment.id, action="CARRIER_QUOTES_REFRESHED",
                user_id=user.id if user else None,
                details={"carrier_code": carrier_code, "created_count": len(created)})
    db.commit()
    return {"created_count": len(created), "quote_ids": [quote.id for quote in created]}
