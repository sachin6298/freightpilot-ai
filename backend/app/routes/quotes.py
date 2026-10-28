"""Quote endpoints for FreightPilot AI."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import Quote, RiskAssessment, Shipment
from app.db.session import get_db
from app.schemas import QuoteResponse, RiskAssessmentResponse
from app.services.risk_service import assess_quote_risk

router = APIRouter(prefix="/api/quotes", tags=["Quotes"])


@router.get("/{quote_id}", response_model=QuoteResponse)
def get_quote(quote_id: str, db: Session = Depends(get_db)) -> QuoteResponse:
    """Get a single quote by ID with its latest risk assessment."""
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "QUOTE_NOT_FOUND", "message": f"Quote '{quote_id}' not found."},
        )

    shipment = db.query(Shipment).filter(Shipment.id == quote.shipment_id).first()
    peer_quotes = db.query(Quote).filter(Quote.shipment_id == quote.shipment_id).all() if shipment else []

    resp = QuoteResponse.model_validate(quote)

    if shipment:
        assessment_data = assess_quote_risk(quote, shipment, peer_quotes)
        resp.assessment = RiskAssessmentResponse(
            score=assessment_data["score"],
            label=assessment_data["label"],
            flags=assessment_data["flags"],
            method_version=assessment_data["method_version"],
            benchmark_variance_pct=assessment_data["benchmark_variance_pct"],
        )
        resp.benchmark_variance_pct = assessment_data["benchmark_variance_pct"]
    elif quote.assessment:
        resp.assessment = RiskAssessmentResponse(
            score=quote.assessment.score,
            label=quote.assessment.label,
            flags=quote.assessment.flags,
            method_version=quote.assessment.method_version,
            assessed_at=quote.assessment.assessed_at,
        )

    return resp


@router.post("/{quote_id}/assess", response_model=QuoteResponse)
def recalculate_quote_assessment(quote_id: str, db: Session = Depends(get_db)) -> QuoteResponse:
    """Recalculate deterministic assessment against current quote and shipment state per API_SPEC.md."""
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "QUOTE_NOT_FOUND", "message": f"Quote '{quote_id}' not found."},
        )

    shipment = db.query(Shipment).filter(Shipment.id == quote.shipment_id).first()
    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SHIPMENT_NOT_FOUND", "message": f"Parent shipment '{quote.shipment_id}' not found."},
        )

    peer_quotes = db.query(Quote).filter(Quote.shipment_id == quote.shipment_id).all()
    assessment_data = assess_quote_risk(quote, shipment, peer_quotes)

    # Persist or update RiskAssessment record
    db_assessment = db.query(RiskAssessment).filter(RiskAssessment.quote_id == quote.id).first()
    if not db_assessment:
        db_assessment = RiskAssessment(
            quote_id=quote.id,
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
