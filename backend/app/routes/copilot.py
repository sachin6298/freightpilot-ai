"""Copilot router for quote analysis and comparison."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.access import get_accessible_shipment
from app.core.security import get_optional_current_user
from app.db.models import AIConversation, Quote, Shipment, User
from app.db.session import get_db
from app.schemas import CopilotRequest, CopilotResponse
from app.services.copilot_service import generate_copilot_analysis

router = APIRouter(prefix="/api/copilot", tags=["Copilot"])


@router.post("/compare", response_model=CopilotResponse)
def compare_quotes(
    payload: CopilotRequest,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_current_user),
) -> Any:
    """Compare quotes for a shipment using AI copilot or deterministic fallback."""
    # 1. Verify shipment exists
    shipment = get_accessible_shipment(db, payload.shipment_id, user)

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
    conversation = AIConversation(
        user_id=user.id if user else None, shipment_id=shipment.id, task="QUOTE_COMPARISON",
        input_snapshot={"shipment_id": shipment.id, "quote_ids": payload.quote_ids},
        response_snapshot=analysis,
    )
    db.add(conversation)
    db.commit()
    return analysis


@router.get("/history")
def copilot_history(
    shipment_id: str | None = None, limit: int = 20,
    db: Session = Depends(get_db), user: User | None = Depends(get_optional_current_user),
):
    limit = max(1, min(limit, 100))
    query = db.query(AIConversation)
    if user:
        query = query.filter(AIConversation.user_id == user.id)
    else:
        query = query.filter(AIConversation.user_id.is_(None))
    if shipment_id:
        get_accessible_shipment(db, shipment_id, user)
        query = query.filter(AIConversation.shipment_id == shipment_id)
    rows = query.order_by(AIConversation.created_at.desc()).limit(limit).all()
    return [{"id": row.id, "shipment_id": row.shipment_id, "task": row.task,
             "input": row.input_snapshot, "response": row.response_snapshot,
             "created_at": row.created_at.isoformat()} for row in rows]
