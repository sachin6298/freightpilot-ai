"""Shipment lifecycle state machine and transition validation."""

from fastapi import HTTPException

ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "DRAFT": {"QUOTED", "CANCELLED"},
    "QUOTED": {"BOOKED", "PAYMENT_PENDING", "CANCELLED"},
    "BOOKED": {"PAYMENT_PENDING", "PAID", "IN_TRANSIT", "CANCELLED"},
    "PAYMENT_PENDING": {"PAID", "PAYMENT_FAILED", "CANCELLED"},
    "PAYMENT_FAILED": {"PAYMENT_PENDING", "CANCELLED"},
    "PAID": {"IN_TRANSIT", "CANCELLED"},
    "IN_TRANSIT": {"DELIVERED", "EXCEPTION"},
    "EXCEPTION": {"IN_TRANSIT", "DELIVERED"},
    "DELIVERED": set(),
    "CANCELLED": set(),
}


def transition_shipment(shipment, new_status: str) -> None:
    current = shipment.status or "DRAFT"
    target = new_status.upper().strip()
    if target == current:
        return
    if target not in ALLOWED_TRANSITIONS.get(current, set()):
        raise HTTPException(status_code=409, detail={
            "code": "INVALID_SHIPMENT_TRANSITION",
            "message": f"Shipment cannot move from {current} to {target}.",
        })
    shipment.status = target
