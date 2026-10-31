"""Database-backed analytics endpoints. Monetary totals are grouped by currency."""

from fastapi import APIRouter, Depends
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.config import settings
from app.core.security import get_optional_current_user
from app.db.models import Payment, Quote, RiskAssessment, Shipment, User
from app.db.session import get_db

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


def _visible_shipments(db: Session, user: User | None):
    query = db.query(Shipment)
    if user:
        if settings.DEMO_MODE:
            query = query.filter(or_(Shipment.user_id == user.id, Shipment.user_id.is_(None)))
        else:
            query = query.filter(Shipment.user_id == user.id)
    return query


@router.get("/overview")
def overview(db: Session = Depends(get_db), user: User | None = Depends(get_optional_current_user)):
    shipments = _visible_shipments(db, user).with_entities(Shipment.id, Shipment.status).all()
    shipment_ids = [row.id for row in shipments]
    status_counts: dict[str, int] = {}
    for row in shipments:
        status_counts[row.status or "DRAFT"] = status_counts.get(row.status or "DRAFT", 0) + 1

    if shipment_ids:
        quote_count = db.query(func.count(Quote.id)).filter(Quote.shipment_id.in_(shipment_ids)).scalar() or 0
        risk_count = (
            db.query(func.count(RiskAssessment.id))
            .join(Quote, Quote.id == RiskAssessment.quote_id)
            .filter(Quote.shipment_id.in_(shipment_ids), RiskAssessment.score >= 50).scalar() or 0
        )
        currency_spend = (
            db.query(Payment.currency_snapshot, func.sum(Payment.amount_snapshot))
            .filter(Payment.shipment_id.in_(shipment_ids), Payment.status == "CAPTURED")
            .group_by(Payment.currency_snapshot).all()
        )
        payment_count = db.query(func.count(Payment.id)).filter(Payment.shipment_id.in_(shipment_ids)).scalar() or 0
        captured_count = db.query(func.count(Payment.id)).filter(
            Payment.shipment_id.in_(shipment_ids), Payment.status == "CAPTURED").scalar() or 0
    else:
        quote_count = risk_count = payment_count = captured_count = 0
        currency_spend = []

    active_statuses = {"QUOTED", "BOOKED", "PAYMENT_PENDING", "PAYMENT_FAILED", "PAID", "IN_TRANSIT", "EXCEPTION"}
    return {
        "shipment_count": len(shipments),
        "active_shipments": sum(1 for row in shipments if row.status in active_statuses),
        "delivered_shipments": status_counts.get("DELIVERED", 0),
        "shipment_status_counts": status_counts,
        "quote_count": quote_count,
        "high_attention_quotes": risk_count,
        "payment_attempts": payment_count,
        "captured_payments": captured_count,
        "captured_spend_by_currency": [
            {"currency": currency, "amount": f"{amount:.2f}"} for currency, amount in currency_spend
        ],
        "data_scope": "SANDBOX_DEMO" if settings.DEMO_MODE else "ACCOUNT_DATA",
    }


@router.get("/carriers")
def carrier_performance(db: Session = Depends(get_db), user: User | None = Depends(get_optional_current_user)):
    shipments = _visible_shipments(db, user).with_entities(Shipment.id).all()
    shipment_ids = [row.id for row in shipments]
    if not shipment_ids:
        return {"items": [], "note": "No shipment quote history is available."}
    rows = (
        db.query(
            Quote.provider_label, Quote.currency,
            func.count(Quote.id).label("quote_count"),
            func.avg(Quote.total_amount).label("average_quote"),
            func.min(Quote.total_amount).label("lowest_quote"),
            func.avg(Quote.transit_days).label("average_transit_days"),
        )
        .filter(Quote.shipment_id.in_(shipment_ids))
        .group_by(Quote.provider_label, Quote.currency)
        .order_by(Quote.provider_label.asc())
        .all()
    )
    return {"items": [{
        "carrier": row.provider_label, "currency": row.currency, "quote_count": row.quote_count,
        "average_quote": f"{row.average_quote:.2f}" if row.average_quote is not None else None,
        "lowest_quote": f"{row.lowest_quote:.2f}" if row.lowest_quote is not None else None,
        "average_transit_days": round(float(row.average_transit_days), 1) if row.average_transit_days is not None else None,
        "data_source": "QUOTE_RECORDS; verify synthetic source_kind before commercial use",
    } for row in rows]}
