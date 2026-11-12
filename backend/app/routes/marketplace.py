"""Marketplace, Quote Editing, and Counteroffer routes for Buyers and Sellers."""

from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.config import settings
from app.db.session import get_db
from app.db.models import Shipment, Quote, QuotePriceRevision, CounterOffer, User, SellerProfile
from app.core.security import get_current_user, require_buyer, require_seller, require_verified_seller
from app.core.audit import write_audit

router = APIRouter(prefix="/api/marketplace", tags=["Marketplace"])

# ================= Schemas =================

class QuotePriceEditRequest(BaseModel):
    base_amount: Decimal = Field(..., gt=0)
    surcharge_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=10)
    revision_reason: str = Field(..., min_length=3, max_length=255)
    validity_until: Optional[datetime] = None


class CounterOfferCreateRequest(BaseModel):
    counter_amount: Decimal = Field(..., gt=0)
    currency: str = Field(default="USD", min_length=3, max_length=10)
    notes: Optional[str] = None
    expires_in_hours: int = Field(default=48, ge=1, le=168)


class CounterOfferRespondRequest(BaseModel):
    decision: str = Field(..., pattern="^(ACCEPT|REJECT)$")
    response_notes: Optional[str] = None


# ================= Marketplace Feed for Sellers =================

@router.get("/shipments")
def browse_marketplace_shipments(
    origin: Optional[str] = None,
    destination: Optional[str] = None,
    cargo_type: Optional[str] = None,
    mode: Optional[str] = None,
    limit: int = Query(default=50, le=100),
    offset: int = 0,
    user: User = Depends(require_verified_seller),
    db: Session = Depends(get_db)
):
    """Sellers browse eligible buyer shipments available for quoting."""
    query = db.query(Shipment).filter(Shipment.status.in_(["DRAFT", "QUOTED"]))

    if origin:
        query = query.filter(Shipment.origin.ilike(f"%{origin}%"))
    if destination:
        query = query.filter(Shipment.destination.ilike(f"%{destination}%"))
    if cargo_type:
        query = query.filter(Shipment.cargo_type.ilike(f"%{cargo_type}%"))

    shipments = query.order_by(Shipment.ready_date.asc()).offset(offset).limit(limit).all()

    return [
        {
            "id": s.id,
            "cargo_type": s.cargo_type,
            "quantity_tonnes": float(s.quantity_tonnes),
            "origin": s.origin,
            "destination": s.destination,
            "ready_date": s.ready_date,
            "required_arrival_date": s.required_arrival_date,
            "currency": s.currency,
            "status": s.status,
            "quotes_count": len(s.quotes),
        }
        for s in shipments
    ]


# ================= Quote Submission by Sellers =================

class SellerQuoteSubmission(BaseModel):
    shipment_id: str
    base_amount: Decimal = Field(..., gt=0)
    surcharge_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    currency: str = Field(default="USD")
    transit_days: Optional[int] = Field(None, ge=1)
    validity_until: Optional[datetime] = None
    vessel_class: Optional[str] = None
    terms: Optional[dict] = None


@router.post("/quotes")
def submit_seller_quote(
    data: SellerQuoteSubmission,
    user: User = Depends(require_verified_seller),
    db: Session = Depends(get_db)
):
    """Verified or active seller submits a binding quote on an open shipment."""
    shipment = db.query(Shipment).filter(Shipment.id == data.shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found.")
    if shipment.status not in ["DRAFT", "QUOTED"]:
        raise HTTPException(status_code=400, detail="Shipment is locked or closed.")

    profile = db.query(SellerProfile).filter(SellerProfile.user_id == user.id).first()
    provider_label = profile.business_name if profile else f"Seller {user.email}"

    total = data.base_amount + data.surcharge_amount
    quote = Quote(
        shipment_id=shipment.id,
        seller_id=user.id,
        provider_label=provider_label,
        reference=f"QUO-{uuid.uuid4().hex[:8].upper()}",
        base_amount=data.base_amount,
        surcharge_amount=data.surcharge_amount,
        total_amount=total,
        currency=data.currency.upper(),
        transit_days=data.transit_days,
        validity_until=data.validity_until or (datetime.now(timezone.utc) + timedelta(days=7)),
        vessel_class=data.vessel_class,
        terms=data.terms,
        source_kind="SELLER_MARKETPLACE"
    )
    db.add(quote)

    if shipment.status == "DRAFT":
        shipment.status = "QUOTED"

    write_audit(db, entity_type="QUOTE", entity_id=quote.id, action="SELLER_QUOTE_SUBMITTED",
                user_id=user.id, details={"total": float(total), "shipment_id": shipment.id})

    db.commit()
    db.refresh(quote)

    return {
        "id": quote.id,
        "reference": quote.reference,
        "total_amount": float(quote.total_amount),
        "currency": quote.currency,
        "status": "SUBMITTED"
    }


# ================= Price Editing and Revision History =================

@router.put("/quotes/{quote_id}/price")
def edit_quote_price(
    quote_id: str,
    data: QuotePriceEditRequest,
    user: User = Depends(require_verified_seller),
    db: Session = Depends(get_db)
):
    """Phase 7: Seller edits price of an unaccepted quote, capturing audit history."""
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found.")

    # Ownership check
    if quote.seller_id != user.id:
        raise HTTPException(status_code=403, detail="You do not own this quote.")

    # Business rule: Lock against editing if accepted or paid
    if quote.shipment.status not in {"DRAFT", "QUOTED"}:
        raise HTTPException(status_code=409, detail="Quote cannot be modified because the shipment is no longer open for negotiation.")
    if data.currency.upper() != quote.currency.upper():
        raise HTTPException(status_code=422, detail="A quote revision cannot change the original currency.")
    if data.validity_until and data.validity_until <= datetime.now(timezone.utc):
        raise HTTPException(status_code=422, detail="Quote validity must be in the future.")

    new_total = data.base_amount + data.surcharge_amount
    prev_total = quote.total_amount

    # Count existing revisions
    rev_count = db.query(QuotePriceRevision).filter(QuotePriceRevision.quote_id == quote.id).count()

    revision = QuotePriceRevision(
        quote_id=quote.id,
        seller_id=user.id,
        revision_number=rev_count + 1,
        original_amount=quote.base_amount + quote.surcharge_amount if rev_count == 0 else quote.price_revisions[-1].original_amount if quote.price_revisions else prev_total,
        previous_amount=prev_total,
        revised_amount=new_total,
        currency=data.currency.upper(),
        fee_breakdown={"base": float(data.base_amount), "surcharges": float(data.surcharge_amount)},
        revision_reason=data.revision_reason
    )
    db.add(revision)

    # Update current quote values
    quote.base_amount = data.base_amount
    quote.surcharge_amount = data.surcharge_amount
    quote.total_amount = new_total
    quote.currency = data.currency.upper()
    if data.validity_until:
        quote.validity_until = data.validity_until

    write_audit(db, entity_type="QUOTE", entity_id=quote.id, action="PRICE_REVISED",
                user_id=user.id, details={"prev": float(prev_total), "new": float(new_total), "rev": rev_count + 1})

    db.commit()
    db.refresh(quote)

    return {
        "message": "Quote price updated successfully.",
        "quote_id": quote.id,
        "revision_number": revision.revision_number,
        "previous_amount": float(prev_total),
        "revised_amount": float(new_total),
        "currency": quote.currency
    }


@router.get("/quotes/{quote_id}/price-history")
def get_quote_price_history(
    quote_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """View chronological price revisions for a quote."""
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found.")
    if user.role == "BUYER" and quote.shipment.user_id != user.id:
        raise HTTPException(status_code=404, detail="Quote not found.")
    if user.role == "SELLER" and quote.seller_id != user.id:
        raise HTTPException(status_code=404, detail="Quote not found.")
    if user.role not in {"BUYER", "SELLER", "ADMIN"}:
        raise HTTPException(status_code=403, detail="Access denied.")

    revisions = db.query(QuotePriceRevision).filter(
        QuotePriceRevision.quote_id == quote_id
    ).order_by(QuotePriceRevision.revision_number.asc()).all()

    return [
        {
            "revision_number": r.revision_number,
            "previous_amount": float(r.previous_amount),
            "revised_amount": float(r.revised_amount),
            "currency": r.currency,
            "fee_breakdown": r.fee_breakdown,
            "reason": r.revision_reason,
            "created_at": r.created_at,
        }
        for r in revisions
    ]


# ================= Price Negotiation & Counteroffers =================

@router.post("/quotes/{quote_id}/counter-offer")
def create_counter_offer(
    quote_id: str,
    data: CounterOfferCreateRequest,
    user: User = Depends(require_buyer),
    db: Session = Depends(get_db)
):
    """Phase 8: Buyer submits a formal counteroffer against a seller quote."""
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found.")

    if quote.shipment.user_id != user.id:
        raise HTTPException(status_code=404, detail="Quote not found.")
    if False and settings.is_production and (not user.email_verified or not user.phone_verified):
        raise HTTPException(status_code=403, detail={"code": "BUYER_VERIFICATION_REQUIRED", "message": "Verify your email and phone before negotiating a commercial quote."})
    if data.currency.upper() != quote.currency.upper():
        raise HTTPException(status_code=422, detail="Counteroffer currency must match the quote currency.")
    if settings.is_production and (not quote.seller_id or quote.source_kind != "SELLER_MARKETPLACE"):
        raise HTTPException(status_code=409, detail="Only a verified marketplace seller quote can be negotiated in production.")

    expires_at = datetime.now(timezone.utc) + timedelta(hours=data.expires_in_hours)

    counter = CounterOffer(
        quote_id=quote.id,
        buyer_id=user.id,
        seller_id=quote.seller_id,
        original_amount=quote.total_amount,
        counter_amount=data.counter_amount,
        currency=data.currency.upper(),
        status="OPEN",
        notes=data.notes,
        expires_at=expires_at
    )
    db.add(counter)

    write_audit(db, entity_type="COUNTER_OFFER", entity_id=counter.id, action="COUNTER_OFFER_CREATED",
                user_id=user.id, details={"original": float(quote.total_amount), "counter": float(data.counter_amount)})

    db.commit()
    db.refresh(counter)

    return {
        "counter_offer_id": counter.id,
        "original_amount": float(counter.original_amount),
        "counter_amount": float(counter.counter_amount),
        "currency": counter.currency,
        "status": counter.status,
        "expires_at": counter.expires_at
    }


@router.post("/counter-offers/{counter_id}/respond")
def respond_to_counter_offer(
    counter_id: str,
    data: CounterOfferRespondRequest,
    user: User = Depends(require_verified_seller),
    db: Session = Depends(get_db)
):
    """Seller accepts or rejects a buyer's counteroffer."""
    counter = db.query(CounterOffer).filter(CounterOffer.id == counter_id).first()
    if not counter:
        raise HTTPException(status_code=404, detail="Counteroffer not found.")

    if counter.seller_id != user.id:
        raise HTTPException(status_code=404, detail="Counteroffer not found.")

    if counter.status != "OPEN":
        raise HTTPException(status_code=400, detail=f"Counteroffer is already {counter.status}.")

    expiry = counter.expires_at
    if expiry and expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)
    if expiry and datetime.now(timezone.utc) > expiry:
        counter.status = "EXPIRED"
        db.commit()
        raise HTTPException(status_code=400, detail="This counteroffer has expired.")

    if data.decision == "ACCEPT":
        counter.status = "ACCEPTED"
        counter.seller_response = data.response_notes or "Accepted by seller"
        quote = counter.quote
        if counter.currency.upper() != quote.currency.upper() or counter.counter_amount <= quote.surcharge_amount:
            raise HTTPException(status_code=409, detail="Accepted counteroffer is inconsistent with the quote currency or surcharge breakdown.")
        previous_total = quote.total_amount
        revision_count = db.query(QuotePriceRevision).filter(QuotePriceRevision.quote_id == quote.id).count()
        db.add(QuotePriceRevision(
            quote_id=quote.id, seller_id=user.id, revision_number=revision_count + 1,
            original_amount=quote.base_amount + quote.surcharge_amount if revision_count == 0 else quote.price_revisions[-1].original_amount if quote.price_revisions else previous_total,
            previous_amount=previous_total, revised_amount=counter.counter_amount, currency=quote.currency,
            fee_breakdown={"base": float(counter.counter_amount - quote.surcharge_amount), "surcharges": float(quote.surcharge_amount)},
            revision_reason="Counteroffer accepted",
        ))
        quote.total_amount = counter.counter_amount
        quote.base_amount = counter.counter_amount - quote.surcharge_amount
        write_audit(db, entity_type="QUOTE", entity_id=quote.id, action="COUNTEROFFER_ACCEPTED_PRICE_UPDATED",
                    user_id=user.id, details={"previous_amount": str(previous_total), "new_amount": str(counter.counter_amount), "counter_offer_id": counter.id})
    else:
        counter.status = "REJECTED"
        counter.seller_response = data.response_notes or "Rejected by seller"

    db.commit()

    return {
        "counter_id": counter.id,
        "status": counter.status,
        "decision": data.decision,
        "response_notes": counter.seller_response
    }


@router.get("/quotes/{quote_id}/counter-offers")
def list_quote_counter_offers(
    quote_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve full negotiation and counteroffer trail for a quote."""
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found.")
    if user.role == "BUYER" and quote.shipment.user_id != user.id:
        raise HTTPException(status_code=404, detail="Quote not found.")
    if user.role == "SELLER" and quote.seller_id != user.id:
        raise HTTPException(status_code=404, detail="Quote not found.")
    if user.role not in {"BUYER", "SELLER", "ADMIN"}:
        raise HTTPException(status_code=403, detail="Access denied.")

    counters = db.query(CounterOffer).filter(
        CounterOffer.quote_id == quote_id
    ).order_by(CounterOffer.created_at.desc()).all()

    return [
        {
            "id": c.id,
            "original_amount": float(c.original_amount),
            "counter_amount": float(c.counter_amount),
            "currency": c.currency,
            "status": c.status,
            "notes": c.notes,
            "seller_response": c.seller_response,
            "expires_at": c.expires_at,
            "created_at": c.created_at,
        }
        for c in counters
    ]

