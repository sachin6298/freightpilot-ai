"""Quote detail and deterministic risk assessment endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.access import get_accessible_shipment
from app.core.audit import write_audit
from app.core.security import get_optional_current_user
from app.db.models import Quote, RiskAssessment, Shipment, User
from app.db.session import get_db
from app.schemas import QuoteResponse, RiskAssessmentResponse
from app.services.rate_estimate_service import calculate_shipment_estimate
from app.services.risk_service import assess_quote_risk

router = APIRouter(prefix="/api/quotes", tags=["Quotes"])


@router.get("/{quote_id}", response_model=QuoteResponse)
def get_quote(
    quote_id: str, db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_current_user),
) -> QuoteResponse:
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail={"code": "QUOTE_NOT_FOUND", "message": f"Quote '{quote_id}' not found."})
    shipment = get_accessible_shipment(db, quote.shipment_id, user)
    peers = db.query(Quote).filter(Quote.shipment_id == quote.shipment_id).all()
    benchmark = calculate_shipment_estimate(shipment, peers)
    data = assess_quote_risk(quote, shipment, peers, benchmark=benchmark)
    assessment = db.query(RiskAssessment).filter(RiskAssessment.quote_id == quote.id).first()
    if assessment is None:
        assessment = RiskAssessment(quote_id=quote.id)
        db.add(assessment)
    assessment.score = data["score"]
    assessment.label = data["label"]
    assessment.flags = data["flags"]
    assessment.method_version = data["method_version"]
    db.commit()
    result = QuoteResponse.model_validate(quote)
    result.assessment = RiskAssessmentResponse(
        score=data["score"], label=data["label"], flags=data["flags"],
        method_version=data["method_version"], benchmark_variance_pct=data["benchmark_variance_pct"],
    )
    result.benchmark_variance_pct = data["benchmark_variance_pct"]
    return result


@router.post("/{quote_id}/assess", response_model=QuoteResponse)
def assess_quote(
    quote_id: str, db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_current_user),
) -> QuoteResponse:
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail={"code": "QUOTE_NOT_FOUND", "message": f"Quote '{quote_id}' not found."})
    shipment = get_accessible_shipment(db, quote.shipment_id, user)
    peers = db.query(Quote).filter(Quote.shipment_id == quote.shipment_id).all()
    benchmark = calculate_shipment_estimate(shipment, peers)
    data = assess_quote_risk(quote, shipment, peers, benchmark=benchmark)
    assessment = db.query(RiskAssessment).filter(RiskAssessment.quote_id == quote.id).first()
    if assessment is None:
        assessment = RiskAssessment(quote_id=quote.id)
        db.add(assessment)
    assessment.score, assessment.label = data["score"], data["label"]
    assessment.flags, assessment.method_version = data["flags"], data["method_version"]
    write_audit(db, entity_type="QUOTE", entity_id=quote.id, action="RISK_ASSESSED",
                user_id=user.id if user else None, details={"score": data["score"], "label": data["label"]})
    db.commit()
    result = QuoteResponse.model_validate(quote)
    result.assessment = RiskAssessmentResponse(
        score=data["score"], label=data["label"], flags=data["flags"],
        method_version=data["method_version"], benchmark_variance_pct=data["benchmark_variance_pct"],
    )
    result.benchmark_variance_pct = data["benchmark_variance_pct"]
    return result
