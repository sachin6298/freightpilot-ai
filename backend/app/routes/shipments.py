"""Shipment endpoints for FreightPilot AI."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models import Quote, RiskAssessment, Shipment
from app.db.session import get_db
from app.schemas import (
    QuoteCreate,
    QuoteResponse,
    RateEstimateResponse,
    RiskAssessmentResponse,
    ShipmentCreate,
    ShipmentResponse,
)
from app.services.rate_estimate_service import calculate_shipment_estimate
from app.services.risk_service import assess_quote_risk

router = APIRouter(prefix="/api/shipments", tags=["Shipments"])


@router.get("", response_model=list[ShipmentResponse])
def list_shipments(db: Session = Depends(get_db)) -> list[ShipmentResponse]:
    """List all shipments."""
    shipments = db.query(Shipment).order_by(Shipment.created_at.desc()).all()

    # Count associated quotes per shipment
    counts = (
        db.query(Quote.shipment_id, func.count(Quote.id))
        .group_by(Quote.shipment_id)
        .all()
    )
    count_map = {sid: count for sid, count in counts}

    results: list[ShipmentResponse] = []
    for s in shipments:
        resp = ShipmentResponse.model_validate(s)
        resp.quotes_count = count_map.get(s.id, 0)
        results.append(resp)
    return results


@router.post("", response_model=ShipmentResponse, status_code=status.HTTP_201_CREATED)
def create_shipment(payload: ShipmentCreate, db: Session = Depends(get_db)) -> ShipmentResponse:
    """Create a new shipment request."""
    shipment = Shipment(
        cargo_type=payload.cargo_type,
        quantity_tonnes=payload.quantity_tonnes,
        origin=payload.origin,
        destination=payload.destination,
        ready_date=payload.ready_date,
        required_arrival_date=payload.required_arrival_date,
        currency=payload.currency,
        mode="DEMO",
    )
    db.add(shipment)
    db.commit()
    db.refresh(shipment)

    resp = ShipmentResponse.model_validate(shipment)
    resp.quotes_count = 0
    return resp


@router.get("/{shipment_id}", response_model=ShipmentResponse)
def get_shipment(shipment_id: str, db: Session = Depends(get_db)) -> ShipmentResponse:
    """Get single shipment by ID."""
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SHIPMENT_NOT_FOUND", "message": f"Shipment '{shipment_id}' not found."},
        )

    resp = ShipmentResponse.model_validate(shipment)
    resp.quotes_count = db.query(Quote).filter(Quote.shipment_id == shipment_id).count()
    return resp


@router.get("/{shipment_id}/estimate", response_model=RateEstimateResponse)
def get_shipment_rate_estimate(shipment_id: str, db: Session = Depends(get_db)) -> RateEstimateResponse:
    """Get statistical rate estimate baseline and coverage for a shipment."""
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SHIPMENT_NOT_FOUND", "message": f"Shipment '{shipment_id}' not found."},
        )

    quotes = db.query(Quote).filter(Quote.shipment_id == shipment_id).all()
    estimate = calculate_shipment_estimate(shipment, quotes)
    return RateEstimateResponse(**estimate.to_dict())


@router.get("/{shipment_id}/quotes", response_model=list[QuoteResponse])
def get_shipment_quotes(shipment_id: str, db: Session = Depends(get_db)) -> list[QuoteResponse]:
    """Get all quotes for a shipment enriched with explainable risk flags and benchmark variance."""
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SHIPMENT_NOT_FOUND", "message": f"Shipment '{shipment_id}' not found."},
        )

    quotes = db.query(Quote).filter(Quote.shipment_id == shipment_id).order_by(Quote.total_amount.asc()).all()

    enriched_quotes: list[QuoteResponse] = []
    for q in quotes:
        # Compute deterministic risk assessment against peers
        assessment_data = assess_quote_risk(q, shipment, quotes)

        # Upsert risk assessment in database
        db_assessment = db.query(RiskAssessment).filter(RiskAssessment.quote_id == q.id).first()
        if not db_assessment:
            db_assessment = RiskAssessment(
                quote_id=q.id,
                score=assessment_data["score"],
                label=assessment_data["label"],
                flags=assessment_data["flags"],
                method_version=assessment_data["method_version"],
            )
            db.add(db_assessment)
        else:
            db_assessment.score = assessment_data["score"]
            db_assessment.label = assessment_data["label"]
            db_assessment.flags = assessment_data["flags"]
            db_assessment.method_version = assessment_data["method_version"]

        resp = QuoteResponse.model_validate(q)
        resp.assessment = RiskAssessmentResponse(
            score=assessment_data["score"],
            label=assessment_data["label"],
            flags=assessment_data["flags"],
            method_version=assessment_data["method_version"],
            benchmark_variance_pct=assessment_data["benchmark_variance_pct"],
        )
        resp.benchmark_variance_pct = assessment_data["benchmark_variance_pct"]
        enriched_quotes.append(resp)

    db.commit()
    return enriched_quotes


@router.post("/{shipment_id}/quotes", response_model=QuoteResponse, status_code=status.HTTP_201_CREATED)
def create_shipment_quote(
    shipment_id: str, payload: QuoteCreate, db: Session = Depends(get_db)
) -> QuoteResponse:
    """Create a new freight quote for a specific shipment."""
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SHIPMENT_NOT_FOUND", "message": f"Shipment '{shipment_id}' not found."},
        )

    # Validate currency match per data model integrity rules
    if payload.currency != shipment.currency:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "CURRENCY_MISMATCH",
                "message": f"Quote currency '{payload.currency}' must match shipment currency '{shipment.currency}'.",
            },
        )

    quote = Quote(
        shipment_id=shipment_id,
        provider_label=payload.provider_label,
        reference=payload.reference,
        base_amount=payload.base_amount,
        surcharge_amount=payload.surcharge_amount,
        total_amount=payload.total_amount,
        currency=payload.currency,
        transit_days=payload.transit_days,
        validity_until=payload.validity_until,
        vessel_class=payload.vessel_class,
        cargo_capacity_tonnes=payload.cargo_capacity_tonnes,
        terms=payload.terms,
        source_kind=payload.source_kind,
    )
    db.add(quote)
    db.commit()
    db.refresh(quote)

    # Calculate initial assessment
    existing_quotes = db.query(Quote).filter(Quote.shipment_id == shipment_id).all()
    assessment_data = assess_quote_risk(quote, shipment, existing_quotes)

    db_assessment = RiskAssessment(
        quote_id=quote.id,
        score=assessment_data["score"],
        label=assessment_data["label"],
        flags=assessment_data["flags"],
        method_version=assessment_data["method_version"],
    )
    db.add(db_assessment)
    db.commit()

    resp = QuoteResponse.model_validate(quote)
    resp.assessment = RiskAssessmentResponse(
        score=assessment_data["score"],
        label=assessment_data["label"],
        flags=assessment_data["flags"],
        method_version=assessment_data["method_version"],
        benchmark_variance_pct=assessment_data["benchmark_variance_pct"],
    )
    resp.benchmark_variance_pct = assessment_data["benchmark_variance_pct"]
    return resp
