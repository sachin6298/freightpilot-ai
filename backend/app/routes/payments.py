"""PayPal checkout, capture, refund, payment history and verified webhooks."""

import hashlib
import logging
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.core.access import get_accessible_shipment
from app.core.audit import create_notification, write_audit
from app.core.security import get_optional_current_user, get_current_user, require_buyer
from app.db.models import Payment, Quote, Shipment, User, WebhookEvent, SellerProfile
from app.db.session import get_db
from app.services.paypal_service import (
    PayPalServiceError, capture_paypal_order, create_paypal_order,
    get_paypal_order_details, refund_paypal_capture, verify_paypal_webhook,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Payments"])


class CreateOrderRequest(BaseModel):
    quote_id: str = Field(min_length=1, max_length=36)
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=100)


class CaptureOrderRequest(BaseModel):
    provider_order_id: str | None = Field(default=None, max_length=100)


class PaymentResponse(BaseModel):
    payment_id: str
    shipment_id: str
    quote_id: str
    provider: str
    provider_order_id: str
    provider_capture_id: str | None = None
    provider_refund_id: str | None = None
    status: str
    amount: str
    currency: str
    last_verified_at: str | None = None
    created_at: str
    updated_at: str


def _format_payment_response(payment: Payment) -> dict[str, Any]:
    return {
        "payment_id": payment.id,
        "shipment_id": payment.shipment_id,
        "quote_id": payment.quote_id,
        "provider": payment.provider,
        "provider_order_id": payment.provider_order_id,
        "provider_capture_id": payment.provider_capture_id,
        "provider_refund_id": payment.provider_refund_id,
        "status": payment.status,
        "amount": f"{Decimal(str(payment.amount_snapshot)):.2f}",
        "currency": payment.currency_snapshot,
        "last_verified_at": payment.last_verified_at.isoformat() if payment.last_verified_at else None,
        "created_at": payment.created_at.isoformat(),
        "updated_at": payment.updated_at.isoformat(),
    }


def _payment_for_user(db: Session, payment_id: str, user: User | None) -> Payment:
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if payment is None:
        raise HTTPException(status_code=404, detail={"code": "PAYMENT_NOT_FOUND", "message": "Payment not found."})
    if user is None or user.role != "ADMIN":
        get_accessible_shipment(db, payment.shipment_id, user)
    return payment


def _amount_and_currency(order: dict[str, Any]) -> tuple[Decimal | None, str | None, dict | None]:
    units = order.get("purchase_units") or []
    if not units:
        return None, None, None
    unit = units[0]
    amount = unit.get("amount") or {}
    try:
        value = Decimal(str(amount.get("value"))).quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError):
        value = None
    return value, amount.get("currency_code"), unit


def _verify_order_snapshot(order: dict[str, Any], payment: Payment) -> bool:
    amount, currency, unit = _amount_and_currency(order)
    if amount is None or currency != payment.currency_snapshot or amount != Decimal(str(payment.amount_snapshot)):
        return False
    if unit:
        reference = unit.get("reference_id") or unit.get("custom_id")
        if reference and reference != payment.quote_id:
            return False
    return True


def _extract_capture(result: dict[str, Any]) -> tuple[str | None, str | None, Decimal | None, str | None]:
    _, _, unit = _amount_and_currency(result)
    if not unit:
        return None, None, None, None
    captures = (unit.get("payments") or {}).get("captures") or []
    if not captures:
        return None, None, None, None
    capture = captures[0]
    amount = capture.get("amount") or {}
    try:
        capture_amount = Decimal(str(amount.get("value"))).quantize(Decimal("0.01")) if amount.get("value") else None
    except InvalidOperation:
        capture_amount = None
    return capture.get("id"), capture.get("status"), capture_amount, amount.get("currency_code")


def _ensure_settlement(db: Session, payment: Payment, actor_id: str | None = None) -> bool:
    """Create a seller settlement only for the seller explicitly attached to the paid quote."""
    from app.db.models import Settlement
    quote = db.query(Quote).filter(Quote.id == payment.quote_id).first()
    if quote is None or not quote.seller_id:
        write_audit(db, entity_type="PAYMENT", entity_id=payment.id, action="SETTLEMENT_HELD_NO_SELLER",
                    user_id=actor_id, details={"reason": "quote has no explicitly assigned seller"})
        return False
    seller = db.query(User).filter(User.id == quote.seller_id, User.role == "SELLER", User.is_active.is_(True)).first()
    profile = db.query(SellerProfile).filter(SellerProfile.user_id == quote.seller_id).first()
    if seller is None or profile is None or profile.verification_status != "VERIFIED":
        write_audit(db, entity_type="PAYMENT", entity_id=payment.id, action="SETTLEMENT_HELD_SELLER_NOT_VERIFIED",
                    user_id=actor_id, details={"seller_id": quote.seller_id})
        return False
    existing = db.query(Settlement).filter(Settlement.payment_id == payment.id).first()
    if existing:
        return True
    payment_amt = Decimal(str(payment.amount_snapshot)).quantize(Decimal("0.01"))
    platform_fee = (payment_amt * Decimal("0.05")).quantize(Decimal("0.01"))
    applicable_tax = (platform_fee * Decimal("0.10")).quantize(Decimal("0.01"))
    seller_payable = payment_amt - platform_fee - applicable_tax
    db.add(Settlement(
        payment_id=payment.id, seller_id=seller.id,
        buyer_payment_amount=payment_amt, platform_fee=platform_fee,
        applicable_taxes=applicable_tax, seller_payable_amount=seller_payable,
        currency=payment.currency_snapshot, status="PENDING_DISBURSEMENT",
    ))
    write_audit(db, entity_type="PAYMENT", entity_id=payment.id, action="SETTLEMENT_CREATED",
                user_id=actor_id, details={"seller_id": seller.id, "amount": str(seller_payable)})
    return True


def _mark_paid(db: Session, payment: Payment) -> None:
    shipment = db.query(Shipment).filter(Shipment.id == payment.shipment_id).first()
    if shipment and shipment.status in {"PAYMENT_PENDING", "QUOTED", "BOOKED"}:
        shipment.status = "PAID"
    if shipment:
        create_notification(
            db, user_id=shipment.user_id, shipment_id=shipment.id, kind="PAYMENT",
            title="Payment confirmed", message=f"PayPal payment for shipment {shipment.id} was captured.",
        )


@router.post("/payments/create-order", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    payload: CreateOrderRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_buyer),
):
    quote = db.query(Quote).filter(Quote.id == payload.quote_id).first()
    if quote is None:
        raise HTTPException(status_code=404, detail={"code": "QUOTE_NOT_FOUND", "message": "Selected quote was not found."})
    if settings.is_production and (not payload.idempotency_key or len(payload.idempotency_key) < 16):
        raise HTTPException(status_code=422, detail={"code": "IDEMPOTENCY_KEY_REQUIRED", "message": "A unique idempotency key of at least 16 characters is required for payment creation."})
    if False and settings.is_production and (not user.email_verified or not user.phone_verified):
        raise HTTPException(status_code=403, detail={"code": "BUYER_VERIFICATION_REQUIRED", "message": "Verify your email and phone before making payments."})
    shipment = get_accessible_shipment(db, quote.shipment_id, user)
    if settings.is_production:
        if not quote.seller_id:
            raise HTTPException(status_code=409, detail={"code": "QUOTE_SELLER_MISSING", "message": "This quote has no verified seller beneficiary and cannot be paid."})
        seller_profile = db.query(SellerProfile).filter(SellerProfile.user_id == quote.seller_id).first()
        seller_user = db.query(User).filter(User.id == quote.seller_id, User.is_active.is_(True)).first()
        if not seller_user or seller_user.role != "SELLER" or not seller_profile or seller_profile.verification_status != "VERIFIED":
            raise HTTPException(status_code=409, detail={"code": "SELLER_NOT_VERIFIED", "message": "Seller verification must be approved before payment."})

    if quote.validity_until:
        valid_until = quote.validity_until
        if valid_until.tzinfo is None:
            valid_until = valid_until.replace(tzinfo=timezone.utc)
        if valid_until < datetime.now(timezone.utc):
            raise HTTPException(status_code=409, detail={
                "code": "QUOTE_EXPIRED", "message": "This quote has expired. Refresh the comparison and select a current quote.",
            })
    if not settings.DEMO_MODE and quote.source_kind in {"SYNTHETIC_DEMO", "DEMO"}:
        raise HTTPException(status_code=409, detail={
            "code": "SYNTHETIC_QUOTE_NOT_PAYABLE",
            "message": "Synthetic demo quotes cannot be used for live payment. Obtain a verified provider quote.",
        })
    if quote.total_amount is None or Decimal(str(quote.total_amount)) <= 0:
        raise HTTPException(status_code=422, detail={"code": "INVALID_QUOTE_AMOUNT", "message": "Selected quote has no payable amount."})

    if payload.idempotency_key:
        existing = db.query(Payment).filter(Payment.idempotency_key == payload.idempotency_key).first()
        if existing:
            if existing.quote_id != quote.id or existing.shipment_id != shipment.id:
                raise HTTPException(status_code=409, detail={
                    "code": "IDEMPOTENCY_KEY_REUSED", "message": "This idempotency key was already used for another quote.",
                })
            return _format_payment_response(existing)
    else:
        # Reuse an unfinished attempt when an older client omits an idempotency key.
        pending = (db.query(Payment).filter(
            Payment.quote_id == quote.id,
            Payment.status.in_(["CREATED", "APPROVED", "REVIEW_REQUIRED"]),
        ).order_by(Payment.created_at.desc()).first())
        if pending:
            return _format_payment_response(pending)
        already_paid = db.query(Payment.id).filter(
            Payment.quote_id == quote.id, Payment.status == "CAPTURED",
        ).first()
        if already_paid:
            raise HTTPException(status_code=409, detail={
                "code": "QUOTE_ALREADY_PAID", "message": "This quote already has a captured payment.",
            })

    payment_id = str(uuid.uuid4())
    request_id = payload.idempotency_key or payment_id
    try:
        provider_order = create_paypal_order(
            amount=Decimal(str(quote.total_amount)), currency=quote.currency,
            reference_id=quote.id,
            description=f"FreightPilot AI - {quote.reference}: {shipment.origin} to {shipment.destination}",
            request_id=request_id,
        )
    except PayPalServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail={"code": exc.code, "message": exc.message})

    provider_order_id = provider_order.get("id")
    if not provider_order_id:
        raise HTTPException(status_code=502, detail={"code": "PAYPAL_INVALID_RESPONSE", "message": "PayPal did not return an order ID."})

    payment = Payment(
        id=payment_id, shipment_id=shipment.id, quote_id=quote.id,
        amount_snapshot=quote.total_amount, currency_snapshot=quote.currency,
        provider=f"paypal_{settings.PAYPAL_ENV.lower()}",
        provider_order_id=provider_order_id, status="CREATED", idempotency_key=payload.idempotency_key,
    )
    db.add(payment)
    if shipment.status in {"DRAFT", "QUOTED", "BOOKED", "PAYMENT_FAILED"}:
        shipment.status = "PAYMENT_PENDING"
    write_audit(db, entity_type="PAYMENT", entity_id=payment.id, action="PAYMENT_ORDER_CREATED",
                user_id=user.id if user else None,
                details={"quote_id": quote.id, "provider_order_id": provider_order_id,
                         "amount": str(payment.amount_snapshot), "currency": payment.currency_snapshot})
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        if payload.idempotency_key:
            existing = db.query(Payment).filter(Payment.idempotency_key == payload.idempotency_key).first()
            if existing and existing.quote_id == quote.id:
                return _format_payment_response(existing)
        raise HTTPException(status_code=409, detail={"code": "PAYMENT_CONFLICT", "message": "Payment order already exists; refresh payment status."})
    db.refresh(payment)
    return _format_payment_response(payment)


@router.post("/payments/{payment_id}/capture", response_model=PaymentResponse)
def capture_order(
    payment_id: str, payload: CaptureOrderRequest,
    db: Session = Depends(get_db), user: User = Depends(require_buyer),
):
    payment = _payment_for_user(db, payment_id, user)
    if payment.status == "CAPTURED":
        return _format_payment_response(payment)
    if payment.status == "REFUNDED":
        raise HTTPException(status_code=409, detail={"code": "PAYMENT_ALREADY_REFUNDED", "message": "This payment has already been refunded."})
    if payload.provider_order_id and payload.provider_order_id != payment.provider_order_id:
        raise HTTPException(status_code=400, detail={"code": "ORDER_ID_MISMATCH", "message": "PayPal order ID does not match the stored payment."})

    try:
        order = get_paypal_order_details(payment.provider_order_id)
        if not _verify_order_snapshot(order, payment):
            payment.status = "REVIEW_REQUIRED"
            db.commit()
            raise HTTPException(status_code=409, detail={"code": "AMOUNT_CURRENCY_MISMATCH", "message": "PayPal order does not match the saved quote amount and currency."})

        order_status = order.get("status")
        if order_status == "COMPLETED":
            capture_id, capture_status, capture_amount, capture_currency = _extract_capture(order)
            if capture_status != "COMPLETED" or not capture_id:
                payment.status = "REVIEW_REQUIRED"
                db.commit()
                raise HTTPException(status_code=502, detail={"code": "CAPTURE_NOT_VERIFIED", "message": "PayPal order is completed but capture details could not be verified."})
            if capture_amount is None or capture_amount != Decimal(str(payment.amount_snapshot)) or capture_currency != payment.currency_snapshot:
                payment.status = "REVIEW_REQUIRED"
                db.commit()
                raise HTTPException(status_code=409, detail={"code": "CAPTURE_AMOUNT_MISMATCH", "message": "Captured amount differs from the stored quote."})
            payment.provider_capture_id = capture_id
        elif order_status == "APPROVED":
            payment.status = "APPROVED"
            db.commit()
            captured = capture_paypal_order(payment.provider_order_id, request_id=payment.id)
            capture_id, capture_status, capture_amount, capture_currency = _extract_capture(captured)
            if capture_status != "COMPLETED" or not capture_id:
                payment.status = "REVIEW_REQUIRED"
                db.commit()
                raise HTTPException(status_code=502, detail={"code": "CAPTURE_NOT_COMPLETED", "message": "PayPal did not confirm a completed capture."})
            if capture_amount is None or capture_amount != Decimal(str(payment.amount_snapshot)) or capture_currency != payment.currency_snapshot:
                payment.status = "REVIEW_REQUIRED"
                db.commit()
                raise HTTPException(status_code=409, detail={"code": "CAPTURE_AMOUNT_MISMATCH", "message": "Captured amount differs from the stored quote."})
            payment.provider_capture_id = capture_id
        else:
            raise HTTPException(status_code=409, detail={
                "code": "ORDER_NOT_APPROVED", "message": f"PayPal order is {order_status or 'unknown'}; buyer approval is required before capture.",
            })
    except PayPalServiceError as exc:
        # Network errors may happen after the provider completed capture. Do not mark FAILED.
        payment.status = "REVIEW_REQUIRED"
        db.commit()
        raise HTTPException(status_code=exc.status_code, detail={"code": exc.code, "message": exc.message})

    payment.status = "CAPTURED"
    payment.last_verified_at = datetime.now(timezone.utc)
    _mark_paid(db, payment)

    # Never infer a settlement beneficiary from database order. The quote must
    # identify an explicitly assigned, verified seller.
    settlement_created = _ensure_settlement(db, payment, actor_id=user.id if user else None)
    if not settlement_created and settings.is_production:
        payment.status = "REVIEW_REQUIRED"

    write_audit(db, entity_type="PAYMENT", entity_id=payment.id, action="PAYMENT_CAPTURED",
                user_id=user.id if user else None,
                details={"provider_capture_id": payment.provider_capture_id})
    db.commit()
    db.refresh(payment)
    return _format_payment_response(payment)


@router.get("/settlements")
def list_settlements(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Sellers can view only their ledger; administrators can view the full ledger."""
    from app.db.models import Settlement
    if user.role == "SELLER":
        query = db.query(Settlement).filter(Settlement.seller_id == user.id)
    elif user.role == "ADMIN":
        query = db.query(Settlement)
    else:
        raise HTTPException(status_code=403, detail={"code": "SETTLEMENT_ACCESS_DENIED", "message": "Only sellers and administrators can access settlements."})

    settlements = query.order_by(Settlement.created_at.desc()).limit(100).all()
    return [
        {
            "id": s.id,
            "payment_id": s.payment_id,
            "seller_id": s.seller_id,
            "buyer_payment": float(s.buyer_payment_amount),
            "platform_fee": float(s.platform_fee),
            "applicable_taxes": float(s.applicable_taxes),
            "seller_payable": float(s.seller_payable_amount),
            "currency": s.currency,
            "status": s.status,
            "payout_reference": s.payout_reference,
            "created_at": s.created_at.isoformat(),
        }
        for s in settlements
    ]


@router.post("/payments/{payment_id}/refund", response_model=PaymentResponse)
def refund_payment(
    payment_id: str, db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role != "ADMIN":
        raise HTTPException(status_code=403, detail={"code": "REFUND_APPROVAL_REQUIRED", "message": "Refund execution is restricted to administrators until a formal refund-request and approval workflow is enabled."})
    payment = _payment_for_user(db, payment_id, user)
    if payment.status == "REFUNDED":
        return _format_payment_response(payment)
    if payment.status != "CAPTURED" or not payment.provider_capture_id:
        raise HTTPException(status_code=409, detail={"code": "PAYMENT_NOT_REFUNDABLE", "message": "Only captured payments can be refunded."})
    from app.db.models import Settlement
    settlement = db.query(Settlement).filter(Settlement.payment_id == payment.id).first()
    if settlement and settlement.status == "PAID_OUT":
        raise HTTPException(status_code=409, detail={"code": "SETTLEMENT_ALREADY_PAID_OUT", "message": "This payment has already been paid out to the seller. Reconcile the payout before initiating a refund."})
    try:
        refund = refund_paypal_capture(payment.provider_capture_id, request_id=f"refund-{payment.id}")
    except PayPalServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail={"code": exc.code, "message": exc.message})
    if refund.get("status") != "COMPLETED" or not refund.get("id"):
        payment.status = "REVIEW_REQUIRED"
        db.commit()
        raise HTTPException(status_code=502, detail={"code": "REFUND_NOT_CONFIRMED", "message": "PayPal did not confirm the refund."})
    payment.provider_refund_id = refund["id"]
    if settlement and settlement.status != "PAID_OUT":
        settlement.status = "REVERSED"
        settlement.reconciliation_notes = "Reversed following confirmed full PayPal refund."
    elif settlement and settlement.status == "PAID_OUT":
        settlement.reconciliation_notes = "Refund confirmed after payout; manual recovery/reconciliation required."
    payment.status = "REFUNDED"
    payment.last_verified_at = datetime.now(timezone.utc)
    write_audit(db, entity_type="PAYMENT", entity_id=payment.id, action="PAYMENT_REFUNDED",
                user_id=user.id if user else None, details={"provider_refund_id": payment.provider_refund_id})
    db.commit()
    db.refresh(payment)
    return _format_payment_response(payment)


@router.get("/payments/{payment_id}", response_model=PaymentResponse)
def get_payment(
    payment_id: str, db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return _format_payment_response(_payment_for_user(db, payment_id, user))


@router.get("/shipments/{shipment_id}/payments", response_model=list[PaymentResponse])
def list_shipment_payments(
    shipment_id: str, limit: int = 100, offset: int = 0,
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    if user.role != "ADMIN":
        get_accessible_shipment(db, shipment_id, user)
    payments = (
        db.query(Payment).filter(Payment.shipment_id == shipment_id)
        .order_by(Payment.created_at.desc()).offset(max(0, offset)).limit(max(1, min(limit, 500))).all()
    )
    return [_format_payment_response(payment) for payment in payments]


@router.post("/webhooks/paypal", status_code=status.HTTP_200_OK)
async def paypal_webhook(request: Request, db: Session = Depends(get_db)):
    raw_body = await request.body()
    if len(raw_body) > 1_000_000:
        raise HTTPException(status_code=413, detail={"code": "WEBHOOK_TOO_LARGE", "message": "Webhook payload is too large."})
    try:
        event = await request.json()
    except ValueError:
        raise HTTPException(status_code=400, detail={"code": "INVALID_WEBHOOK_JSON", "message": "Webhook body must be valid JSON."})
    event_id = event.get("id")
    event_type = event.get("event_type")
    if not event_id or not event_type:
        raise HTTPException(status_code=400, detail={"code": "INVALID_WEBHOOK", "message": "Webhook event ID and type are required."})

    headers = {key.lower(): value for key, value in request.headers.items()}
    try:
        verified = verify_paypal_webhook(headers, event)
    except PayPalServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail={"code": exc.code, "message": exc.message})
    if not verified:
        raise HTTPException(status_code=400, detail={"code": "WEBHOOK_SIGNATURE_INVALID", "message": "PayPal webhook signature could not be verified."})

    existing = db.query(WebhookEvent).filter(WebhookEvent.provider_event_id == event_id).first()
    if existing:
        return {"status": "duplicate", "event_id": event_id}

    webhook_record = WebhookEvent(
        provider_event_id=event_id, event_type=event_type,
        verification_status="VERIFIED", processing_status="RECEIVED",
        payload_hash=hashlib.sha256(raw_body).hexdigest(),
    )
    db.add(webhook_record)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        return {"status": "duplicate", "event_id": event_id}

    resource = event.get("resource") or {}
    related_ids = (resource.get("supplementary_data") or {}).get("related_ids") or {}
    order_id = related_ids.get("order_id")
    capture_lookup_id = resource.get("id") if str(event_type).startswith("PAYMENT.CAPTURE.") else None
    payment = db.query(Payment).filter(Payment.provider_order_id == order_id).first() if order_id else None
    if payment is None and capture_lookup_id:
        payment = db.query(Payment).filter(Payment.provider_capture_id == capture_lookup_id).first()

    if payment and payment.status == "REFUNDED":
        webhook_record.processing_status = "IGNORED_OUT_OF_ORDER"
    elif payment and event_type == "PAYMENT.CAPTURE.COMPLETED":
        amount = resource.get("amount") or {}
        try:
            webhook_amount = Decimal(str(amount.get("value"))).quantize(Decimal("0.01"))
        except (InvalidOperation, TypeError):
            webhook_amount = None
        capture_id = resource.get("id")
        if (webhook_amount == Decimal(str(payment.amount_snapshot))
                and amount.get("currency_code") == payment.currency_snapshot and capture_id):
            payment.status = "CAPTURED"
            payment.provider_capture_id = capture_id
            payment.last_verified_at = datetime.now(timezone.utc)
            _mark_paid(db, payment)
            if not _ensure_settlement(db, payment) and settings.is_production:
                payment.status = "REVIEW_REQUIRED"
        else:
            payment.status = "REVIEW_REQUIRED"
    elif payment and event_type == "PAYMENT.CAPTURE.DENIED":
        payment.status = "FAILED"
    elif payment and event_type == "PAYMENT.CAPTURE.REFUNDED":
        related_capture_id = related_ids.get("capture_id")
        if related_capture_id == payment.provider_capture_id and resource.get("id"):
            payment.status = "REFUNDED"
            payment.provider_refund_id = resource.get("id")
            from app.db.models import Settlement
            settlement = db.query(Settlement).filter(Settlement.payment_id == payment.id).first()
            if settlement and settlement.status != "PAID_OUT":
                settlement.status = "REVERSED"
                settlement.reconciliation_notes = "Reversed following provider refund webhook."
            elif settlement and settlement.status == "PAID_OUT":
                settlement.reconciliation_notes = "Provider refund received after payout; manual recovery/reconciliation required."

    webhook_record.processing_status = "PROCESSED"
    webhook_record.processed_at = datetime.now(timezone.utc)
    db.commit()
    return {"status": "processed", "event_id": event_id}

