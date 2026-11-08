"""Shipment tracking timeline endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.access import get_accessible_shipment
from app.core.audit import create_notification, write_audit
from app.core.security import get_optional_current_user, get_current_user
from app.config import settings
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
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    shipment = get_accessible_shipment(db, shipment_id, user)
    if user.role != "ADMIN" and not (settings.DEMO_MODE and user.role == "BUYER" and shipment.user_id == user.id):
        raise HTTPException(status_code=403, detail={"code": "TRACKING_UPDATE_FORBIDDEN", "message": "Only authorized operations personnel can update shipment status."})
    target = payload.status.upper().strip()
    if target not in _ALLOWED_STATUSES:
        raise HTTPException(status_code=422, detail={"code": "INVALID_TRACKING_STATUS", "message": "Unsupported shipment status."})
    transition_shipment(shipment, target)
    occurred_at = payload.occurred_at or datetime.now(timezone.utc)
    event = TrackingEvent(
        shipment_id=shipment.id, status=target, location=payload.location,
        description=payload.description.strip(),
        source_kind="ADMIN_MANUAL" if user.role == "ADMIN" else "DEMO_MANUAL",
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


@router.post("/{shipment_id}/tracking/provider-lookup", response_model=TrackingEventResponse)
def provider_tracking_lookup(
    shipment_id: str,
    carrier_code: str,
    tracking_number: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Fetch verified tracking information from a configured carrier adapter."""
    shipment = get_accessible_shipment(db, shipment_id, user)
    from app.services.carrier_service import carrier_registry

    adapter = carrier_registry.get(carrier_code)
    if not adapter or not hasattr(adapter, "fetch_tracking"):
        raise HTTPException(status_code=501, detail={"code": "CARRIER_TRACKING_NOT_CONFIGURED", "message": "No verified live tracking adapter is configured for this carrier."})
    result = adapter.fetch_tracking(tracking_number)
    status_label = str(result.get("status", "")).upper()
    if status_label not in _ALLOWED_STATUSES:
        raise HTTPException(status_code=502, detail={"code": "CARRIER_TRACKING_INVALID", "message": "Carrier returned an unsupported tracking status."})
    description = str(result.get("description", "Carrier update"))[:2000]
    source_kind = "LIVE_PROVIDER"

    event = TrackingEvent(
        shipment_id=shipment.id,
        status=status_label,
        location=str(result.get("location", ""))[:200] or None,
        description=description,
        source_kind=source_kind,
        occurred_at=datetime.now(timezone.utc),
    )
    db.add(event)
    write_audit(db, entity_type="SHIPMENT", entity_id=shipment.id, action="PROVIDER_TRACKING_LOOKUP",
                user_id=user.id if user else None, details={"carrier": carrier_code, "source_kind": source_kind})
    db.commit()
    db.refresh(event)
    return event
