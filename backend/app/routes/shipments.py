"""Shipment endpoints with ownership checks, lifecycle persistence and quote analysis."""

from datetime import date, datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, or_
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.orm import Session

from app.config import settings
from app.core.access import get_accessible_shipment
from app.core.audit import write_audit
from app.core.security import get_optional_current_user
from app.db.models import Quote, RiskAssessment, Shipment, TrackingEvent, User
from app.db.session import get_db
from app.schemas import (
    QuoteCreate, QuoteResponse, RateEstimateResponse, RiskAssessmentResponse,
    ShipmentCreate, ShipmentResponse,
)
from app.services.rate_estimate_service import calculate_shipment_estimate
from app.services.risk_service import assess_quote_risk

router = APIRouter(prefix="/api/shipments", tags=["Shipments"])


class ShipmentUpdate(BaseModel):
    cargo_type: str | None = Field(default=None, min_length=2, max_length=100)
    quantity_tonnes: Decimal | None = Field(default=None, gt=0)
    origin: str | None = Field(default=None, min_length=2, max_length=150)
    destination: str | None = Field(default=None, min_length=2, max_length=150)
    ready_date: date | None = None

    @model_validator(mode="after")
    def validate_route(self):
        if self.origin and self.destination and self.origin.strip().lower() == self.destination.strip().lower():
            raise ValueError("Origin and destination must be different ports or locations.")
        return self


def _shipment_scope(query, user: User | None):
    if user is None:
        return query
    if settings.DEMO_MODE:
        return query.filter(or_(Shipment.user_id == user.id, Shipment.user_id.is_(None)))
    return query.filter(Shipment.user_id == user.id)


@router.get("", response_model=list[ShipmentResponse])
def list_shipments(
    limit: int = 100, offset: int = 0,
    db: Session = Depends(get_db), user: User | None = Depends(get_optional_current_user),
) -> list[ShipmentResponse]:
    limit = max(1, min(limit, 500))
    offset = max(0, offset)
    shipments = (_shipment_scope(db.query(Shipment), user)
                 .order_by(Shipment.created_at.desc()).offset(offset).limit(limit).all())
    if not shipments:
        return []
    shipment_ids = [shipment.id for shipment in shipments]
    counts = (
        db.query(Quote.shipment_id, func.count(Quote.id))
        .filter(Quote.shipment_id.in_(shipment_ids))
        .group_by(Quote.shipment_id)
        .all()
    )
    count_map = {shipment_id: count for shipment_id, count in counts}
    results = []
    for shipment in shipments:
        result = ShipmentResponse.model_validate(shipment)
        result.quotes_count = count_map.get(shipment.id, 0)
        results.append(result)
    return results


@router.post("", response_model=ShipmentResponse, status_code=status.HTTP_201_CREATED)
def create_shipment(
    payload: ShipmentCreate,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_current_user),
) -> ShipmentResponse:
    shipment = Shipment(
        user_id=user.id if user else None,
        cargo_type=payload.cargo_type.strip(), quantity_tonnes=payload.quantity_tonnes,
        origin=payload.origin.strip(), destination=payload.destination.strip(),
        ready_date=payload.ready_date, required_arrival_date=payload.required_arrival_date,
        currency=payload.currency, mode="DEMO" if settings.DEMO_MODE else "LIVE", status="DRAFT",
    )
    db.add(shipment)
    db.flush()
    write_audit(db, entity_type="SHIPMENT", entity_id=shipment.id, action="SHIPMENT_CREATED",
                user_id=user.id if user else None,
                details={"origin": shipment.origin, "destination": shipment.destination})
    db.commit()
    db.refresh(shipment)
    result = ShipmentResponse.model_validate(shipment)
    result.quotes_count = 0
    return result


@router.get("/{shipment_id}", response_model=ShipmentResponse)
def get_shipment(
    shipment_id: str, db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_current_user),
) -> ShipmentResponse:
    shipment = get_accessible_shipment(db, shipment_id, user)
    result = ShipmentResponse.model_validate(shipment)
    result.quotes_count = db.query(Quote).filter(Quote.shipment_id == shipment_id).count()
    return result


@router.patch("/{shipment_id}", response_model=ShipmentResponse)
def update_shipment(
    shipment_id: str, payload: ShipmentUpdate, db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_current_user),
) -> ShipmentResponse:
    shipment = get_accessible_shipment(db, shipment_id, user)
    if shipment.status not in {"DRAFT", "QUOTED"}:
        raise HTTPException(status_code=409, detail={
            "code": "SHIPMENT_LOCKED", "message": "Shipment details cannot be edited after booking or payment begins.",
        })
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        if value is None:
            raise HTTPException(status_code=422, detail={
                "code": "INVALID_SHIPMENT_UPDATE", "message": f"Field '{field}' cannot be null.",
            })
        if isinstance(value, str):
            value = value.strip()
        setattr(shipment, field, value)
    if shipment.origin.strip().lower() == shipment.destination.strip().lower():
        raise HTTPException(status_code=422, detail={
            "code": "INVALID_ROUTE", "message": "Origin and destination must be different.",
        })
    write_audit(db, entity_type="SHIPMENT", entity_id=shipment.id, action="SHIPMENT_UPDATED",
                user_id=user.id if user else None, details={"fields": sorted(updates)})
    db.commit()
    db.refresh(shipment)
    result = ShipmentResponse.model_validate(shipment)
    result.quotes_count = db.query(Quote).filter(Quote.shipment_id == shipment.id).count()
    return result


@router.post("/{shipment_id}/cancel", response_model=ShipmentResponse)
def cancel_shipment(
    shipment_id: str, db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_current_user),
) -> ShipmentResponse:
    shipment = get_accessible_shipment(db, shipment_id, user)
    from app.services.shipment_service import transition_shipment
    transition_shipment(shipment, "CANCELLED")
    event = TrackingEvent(
        shipment_id=shipment.id, status="CANCELLED", description="Shipment cancelled by user.",
        source_kind="USER_INPUT", occurred_at=datetime.now(timezone.utc),
    )
    db.add(event)
    write_audit(db, entity_type="SHIPMENT", entity_id=shipment.id, action="SHIPMENT_CANCELLED",
                user_id=user.id if user else None)
    db.commit()
    db.refresh(shipment)
    result = ShipmentResponse.model_validate(shipment)
    result.quotes_count = db.query(Quote).filter(Quote.shipment_id == shipment.id).count()
    return result


@router.get("/{shipment_id}/estimate", response_model=RateEstimateResponse)
def get_shipment_rate_estimate(
    shipment_id: str, db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_current_user),
) -> RateEstimateResponse:
    shipment = get_accessible_shipment(db, shipment_id, user)
    quotes = db.query(Quote).filter(Quote.shipment_id == shipment_id).all()
    return RateEstimateResponse(**calculate_shipment_estimate(shipment, quotes).to_dict())


@router.get("/{shipment_id}/quotes", response_model=list[QuoteResponse])
def get_shipment_quotes(
    shipment_id: str, db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_current_user),
) -> list[QuoteResponse]:
    get_accessible_shipment(db, shipment_id, user)
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    quotes = db.query(Quote).filter(Quote.shipment_id == shipment_id).order_by(Quote.total_amount.asc()).all()
    enriched = []
    benchmark = calculate_shipment_estimate(shipment, quotes)
    existing_assessments = db.query(RiskAssessment).filter(
        RiskAssessment.quote_id.in_([quote.id for quote in quotes])
    ).all() if quotes else []
    assessment_by_quote = {assessment.quote_id: assessment for assessment in existing_assessments}
    for quote in quotes:
        data = assess_quote_risk(quote, shipment, quotes, benchmark=benchmark)
        assessment = assessment_by_quote.get(quote.id)
        if assessment is None:
            assessment = RiskAssessment(quote_id=quote.id)
            db.add(assessment)
        assessment.score = data["score"]
        assessment.label = data["label"]
        assessment.flags = data["flags"]
        assessment.method_version = data["method_version"]
        result = QuoteResponse.model_validate(quote)
        result.assessment = RiskAssessmentResponse(
            score=data["score"], label=data["label"], flags=data["flags"],
            method_version=data["method_version"], benchmark_variance_pct=data["benchmark_variance_pct"],
        )
        result.benchmark_variance_pct = data["benchmark_variance_pct"]
        enriched.append(result)
    db.commit()
    return enriched


@router.post("/{shipment_id}/quotes", response_model=QuoteResponse, status_code=status.HTTP_201_CREATED)
def create_shipment_quote(
    shipment_id: str, payload: QuoteCreate, db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_current_user),
) -> QuoteResponse:
    shipment = get_accessible_shipment(db, shipment_id, user)
    if payload.currency != shipment.currency:
        raise HTTPException(status_code=400, detail={
            "code": "CURRENCY_MISMATCH",
            "message": f"Quote currency '{payload.currency}' must match shipment currency '{shipment.currency}'.",
        })
    quote = Quote(
        shipment_id=shipment_id, provider_label=payload.provider_label.strip(), reference=payload.reference.strip(),
        base_amount=payload.base_amount, surcharge_amount=payload.surcharge_amount,
        total_amount=payload.total_amount, currency=payload.currency, transit_days=payload.transit_days,
        validity_until=payload.validity_until, vessel_class=payload.vessel_class,
        cargo_capacity_tonnes=payload.cargo_capacity_tonnes, terms=payload.terms,
        source_kind=payload.source_kind,
    )
    db.add(quote)
    if shipment.status == "DRAFT":
        shipment.status = "QUOTED"
    db.flush()
    quotes = db.query(Quote).filter(Quote.shipment_id == shipment_id).all()
    benchmark = calculate_shipment_estimate(shipment, quotes)
    data = assess_quote_risk(quote, shipment, quotes, benchmark=benchmark)
    db.add(RiskAssessment(
        quote_id=quote.id, score=data["score"], label=data["label"],
        flags=data["flags"], method_version=data["method_version"],
    ))
    write_audit(db, entity_type="QUOTE", entity_id=quote.id, action="QUOTE_CREATED",
                user_id=user.id if user else None,
                details={"shipment_id": shipment_id, "source_kind": quote.source_kind})
    db.commit()
    db.refresh(quote)
    result = QuoteResponse.model_validate(quote)
    result.assessment = RiskAssessmentResponse(
        score=data["score"], label=data["label"], flags=data["flags"],
        method_version=data["method_version"], benchmark_variance_pct=data["benchmark_variance_pct"],
    )
    result.benchmark_variance_pct = data["benchmark_variance_pct"]
    return result
