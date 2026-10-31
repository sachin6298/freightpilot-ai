"""Shipment tracking timeline endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.access import get_accessible_shipment
from app.core.audit import create_notification, write_audit
from app.core.security import get_optional_current_user
from app.db.models import TrackingEvent, User
from app.db.session import get_db
from app.services.shipment_service import transition_shipment

router = APIRouter(prefix="/api/shipments", tags=["Tracking"])
_ALLOWED_STATUSES = {
    "DRAFT", "QUOTED", "BOOKED", "PAYMENT_PENDING", "PAYMENT_FAILED", "PAID",
    "IN_TRANSIT", "DELIVERED", "EXCEPTION", "CANCELLED",
}


class TrackingEventCreate(BaseModel):
    status: str = Field(min_length=3, max_length=30)
    location: str | None = Field(default=None, max_length=200)
    description: str = Field(min_length=3, max_length=2000)
    occurred_at: datetime | None = None
    source_kind: str = Field(default="USER_INPUT", max_length=40)


class TrackingEventResponse(BaseModel):
    id: str
    shipment_id: str
    status: str
    location: str | None
    description: str
    source_kind: str
    occurred_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


@router.get("/{shipment_id}/tracking", response_model=list[TrackingEventResponse])
def list_tracking_events(
    shipment_id: str, limit: int = 100, offset: int = 0,
    db: Session = Depends(get_db), user: User | None = Depends(get_optional_current_user),
):
    get_accessible_shipment(db, shipment_id, user)
    return (
        db.query(TrackingEvent).filter(TrackingEvent.shipment_id == shipment_id)
        .order_by(TrackingEvent.occurred_at.asc(), TrackingEvent.created_at.asc())
        .offset(max(0, offset)).limit(max(1, min(limit, 500))).all()
    )


@router.post("/{shipment_id}/tracking", response_model=TrackingEventResponse, status_code=status.HTTP_201_CREATED)
def add_tracking_event(
    shipment_id: str, payload: TrackingEventCreate,
    db: Session = Depends(get_db), user: User | None = Depends(get_optional_current_user),
):
    shipment = get_accessible_shipment(db, shipment_id, user)
    target = payload.status.upper().strip()
    if target not in _ALLOWED_STATUSES:
        raise HTTPException(status_code=422, detail={"code": "INVALID_TRACKING_STATUS", "message": "Unsupported shipment status."})
    transition_shipment(shipment, target)
    occurred_at = payload.occurred_at or datetime.now(timezone.utc)
    event = TrackingEvent(
        shipment_id=shipment.id, status=target, location=payload.location,
        description=payload.description.strip(), source_kind=payload.source_kind,
        occurred_at=occurred_at,
    )
    db.add(event)
    write_audit(db, entity_type="SHIPMENT", entity_id=shipment.id, action="TRACKING_EVENT_ADDED",
                user_id=user.id if user else None,
                details={"status": target, "source_kind": payload.source_kind})
    if target in {"EXCEPTION", "DELIVERED", "CANCELLED"}:
        create_notification(
            db, user_id=shipment.user_id, shipment_id=shipment.id,
            kind="SHIPMENT", title=f"Shipment {target.lower().replace('_', ' ')}",
            message=payload.description.strip(),
        )
    db.commit()
    db.refresh(event)
    return event
