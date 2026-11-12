"""Ownership-aware lookup helpers shared by API routers."""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.core.security import require_shipment_access
from app.db.models import Shipment


def get_accessible_shipment(db: Session, shipment_id: str, user=None) -> Shipment:
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if shipment is None:
        raise HTTPException(status_code=404, detail={
            "code": "SHIPMENT_NOT_FOUND", "message": f"Shipment '{shipment_id}' not found.",
        })
    require_shipment_access(shipment, user)
    if user is not None and shipment.user_id is None and not settings.DEMO_MODE:
        raise HTTPException(status_code=404, detail={"code": "SHIPMENT_NOT_FOUND", "message": "Shipment not found."})
    return shipment
