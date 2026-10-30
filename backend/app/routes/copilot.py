"""Copilot router for quote analysis and comparison."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import Quote, Shipment
from app.db.session import get_db
from app.schemas import CopilotRequest, CopilotResponse
from app.services.copilot_service import generate_copilot_analysis

router = APIRouter(prefix="/api/copilot", tags=["Copilot"])


@router.post("/compare", response_model=CopilotResponse)
def compare_quotes(
    payload: CopilotRequest,
    db: Session = Depends(get_db),
) -> Any:
    """Compare quotes for a shipment using AI copilot or deterministic fallback."""
    # 1. Verify shipment exists
    shipment = db.query(Shipment).filter(Shipment.id == payload.shipment_id).first()
    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SHIPMENT_NOT_FOUND", "message": f"Shipment '{payload.shipment_id}' not found."},
        )

    # 2. Validate requested quote_ids
    if not payload.quote_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "EMPTY_QUOTE_IDS", "message": "At least one quote ID must be provided for comparison."},
        )

    # 3. Retrieve quotes for the shipment
    quotes = (
        db.query(Quote)
        .filter(Quote.shipment_id == payload.shipment_id, Quote.id.in_(payload.quote_ids))
        .all()
    )

    if not quotes or len(quotes) != len(set(payload.quote_ids)):
        found_ids = {q.id for q in quotes}
        missing_ids = set(payload.quote_ids) - found_ids
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "QUOTE_NOT_FOUND",
                "message": f"Quote(s) {sorted(list(missing_ids))} not found for shipment '{payload.shipment_id}'.",
            },
        )

    # 4. Get all peer quotes for shipment for rate estimation & risk benchmark
    all_shipment_quotes = db.query(Quote).filter(Quote.shipment_id == payload.shipment_id).all()

    # 5. Generate copilot analysis
    analysis = generate_copilot_analysis(shipment, quotes, all_shipment_quotes)
    return analysis
