"""SQLAlchemy models for users, freight operations, payments and auditability."""

from datetime import datetime, timezone
import uuid

from sqlalchemy import (
    Boolean, Column, Date, DateTime, Enum, ForeignKey, Index, Integer, JSON, LargeBinary,
    Numeric, String, Text, UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db.session import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(254), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum('BUYER', 'SELLER', 'ADMIN', name='userrole'), nullable=False, default="BUYER")
    is_active = Column(Boolean, nullable=False, default=True)
    email_verified = Column(Boolean, nullable=False, default=False)
    phone_verified = Column(Boolean, nullable=False, default=False)
    phone_number = Column(String(30), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    shipments = relationship("Shipment", back_populates="owner")
    buyer_profile = relationship("BuyerProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    seller_profile = relationship("SellerProfile", back_populates="user", uselist=False, cascade="all, delete-orphan", foreign_keys="[SellerProfile.user_id]")
    email_verifications = relationship("EmailVerification", back_populates="user", cascade="all, delete-orphan")
    phone_verifications = relationship("PhoneVerification", back_populates="user", cascade="all, delete-orphan")


class OAuthIdentity(Base):
    """Verified external identity linked to one FreightPilot account."""

    __tablename__ = "oauth_identities"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = Column(String(20), nullable=False)
    subject = Column(String(255), nullable=False)
    email = Column(String(254), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    __table_args__ = (
        UniqueConstraint("provider", "subject", name="uq_oauth_identity_provider_subject"),
    )



class BuyerProfile(Base):
    __tablename__ = "buyer_profiles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    company_name = Column(String(200), nullable=True)
    contact_person = Column(String(150), nullable=True)
    phone_number = Column(String(30), nullable=True)
    billing_address = Column(Text, nullable=True)
    default_currency = Column(String(10), nullable=True, default="USD")
    preferred_regions = Column(JSON, nullable=True, default=list)
    notification_preferences = Column(JSON, nullable=True, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    user = relationship("User", back_populates="buyer_profile")


class SellerProfile(Base):
    __tablename__ = "seller_profiles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    business_name = Column(String(200), nullable=False)
    registration_number = Column(String(100), nullable=True)
    tax_id = Column(String(100), nullable=True)
    business_address = Column(Text, nullable=False)
    country = Column(String(2), nullable=False)
    contact_person = Column(String(150), nullable=False)
    contact_email = Column(String(254), nullable=False)
    contact_phone = Column(String(30), nullable=False)
    business_type = Column(String(50), nullable=True)
    years_in_operation = Column(Integer, nullable=True)
    insurance_coverage = Column(JSON, nullable=True)
    service_regions = Column(JSON, nullable=True, default=list)
    transport_modes = Column(JSON, nullable=True, default=list)
    fleet_capacity = Column(Numeric(12, 2), nullable=True)
    verification_status = Column(String(30), nullable=False, default="UNVERIFIED", index=True)
    trust_score = Column(Integer, nullable=False, default=50)
    verification_notes = Column(Text, nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    verified_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    user = relationship("User", back_populates="seller_profile", foreign_keys=[user_id])
    verifier = relationship("User", foreign_keys=[verified_by])
    verification_documents = relationship("SellerVerificationDocument", back_populates="seller_profile", cascade="all, delete-orphan")


class SellerVerificationDocument(Base):
    __tablename__ = "seller_verification_documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    seller_profile_id = Column(String(36), ForeignKey("seller_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    document_type = Column(String(50), nullable=False)
    document_name = Column(String(200), nullable=False)
    file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    verification_status = Column(String(30), nullable=False, default="PENDING")
    verified_at = Column(DateTime(timezone=True), nullable=True)
    verified_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    seller_profile = relationship("SellerProfile", back_populates="verification_documents")
    verifier = relationship("User", foreign_keys=[verified_by])


class EmailVerification(Base):
    __tablename__ = "email_verifications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    email = Column(String(254), nullable=False)
    token_hash = Column(String(64), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    user = relationship("User", back_populates="email_verifications")


class PhoneVerification(Base):
    __tablename__ = "phone_verifications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    phone_number = Column(String(30), nullable=False)
    otp_hash = Column(String(255), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    attempts = Column(Integer, nullable=False, default=0)
    last_attempt_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    user = relationship("User", back_populates="phone_verifications")


class Shipment(Base):
    __tablename__ = "shipments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    cargo_type = Column(String(100), nullable=False)
    quantity_tonnes = Column(Numeric(12, 2), nullable=False)
    origin = Column(String(150), nullable=False)
    destination = Column(String(150), nullable=False)
    ready_date = Column(Date, nullable=False)
    required_arrival_date = Column(Date, nullable=True)
    currency = Column(String(10), nullable=False, default="USD")
    mode = Column(String(20), nullable=False, default="DEMO")
    status = Column(String(30), nullable=False, default="DRAFT", index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    owner = relationship("User", back_populates="shipments")
    quotes = relationship("Quote", back_populates="shipment", cascade="all, delete-orphan")
    tracking_events = relationship(
        "TrackingEvent", back_populates="shipment", cascade="all, delete-orphan",
        order_by="TrackingEvent.occurred_at",
    )


class Quote(Base):
    __tablename__ = "quotes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    shipment_id = Column(String(36), ForeignKey("shipments.id", ondelete="CASCADE"), nullable=False, index=True)
    seller_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    provider_label = Column(String(150), nullable=False)
    reference = Column(String(100), nullable=False)
    base_amount = Column(Numeric(12, 2), nullable=False)
    surcharge_amount = Column(Numeric(12, 2), nullable=False, default=0.0)
    total_amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(10), nullable=False, default="USD")
    transit_days = Column(Integer, nullable=True)
    validity_until = Column(DateTime(timezone=True), nullable=True)
    vessel_class = Column(String(100), nullable=True)
    cargo_capacity_tonnes = Column(Numeric(12, 2), nullable=True)
    terms = Column(JSON, nullable=True)
    source_kind = Column(String(50), nullable=False, default="SYNTHETIC_DEMO")
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    shipment = relationship("Shipment", back_populates="quotes")
    assessment = relationship("RiskAssessment", back_populates="quote", uselist=False, cascade="all, delete-orphan")
    price_revisions = relationship("QuotePriceRevision", back_populates="quote", cascade="all, delete-orphan", order_by="QuotePriceRevision.revision_number.desc()")
    counter_offers = relationship("CounterOffer", back_populates="quote", cascade="all, delete-orphan", order_by="CounterOffer.created_at.desc()")


class QuotePriceRevision(Base):
    __tablename__ = "quote_price_revisions"
    __table_args__ = (Index("ix_price_revisions_quote_rev", "quote_id", "revision_number"),)

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    quote_id = Column(String(36), ForeignKey("quotes.id", ondelete="CASCADE"), nullable=False, index=True)
    seller_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    revision_number = Column(Integer, nullable=False, default=1)
    original_amount = Column(Numeric(12, 2), nullable=False)
    previous_amount = Column(Numeric(12, 2), nullable=False)
    revised_amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(10), nullable=False, default="USD")
    fee_breakdown = Column(JSON, nullable=False, default=dict)
    revision_reason = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    quote = relationship("Quote", back_populates="price_revisions")
    changed_by = relationship("User", foreign_keys=[seller_id])


class CounterOffer(Base):
    __tablename__ = "counter_offers"
    __table_args__ = (Index("ix_counter_offers_quote_status", "quote_id", "status"),)

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    quote_id = Column(String(36), ForeignKey("quotes.id", ondelete="CASCADE"), nullable=False, index=True)
    buyer_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    seller_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    original_amount = Column(Numeric(12, 2), nullable=False)
    counter_amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(10), nullable=False, default="USD")
    status = Column(String(30), nullable=False, default="OPEN", index=True)
    notes = Column(Text, nullable=True)
    seller_response = Column(Text, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    quote = relationship("Quote", back_populates="counter_offers")
    buyer = relationship("User", foreign_keys=[buyer_id])
    seller = relationship("User", foreign_keys=[seller_id])


class Settlement(Base):
    __tablename__ = "settlements"
    __table_args__ = (Index("ix_settlements_payment_status", "payment_id", "status"),)

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    payment_id = Column(String(36), ForeignKey("payments.id", ondelete="RESTRICT"), nullable=False, unique=True, index=True)
    seller_id = Column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    buyer_payment_amount = Column(Numeric(12, 2), nullable=False)
    platform_fee = Column(Numeric(12, 2), nullable=False, default=0.0)
    applicable_taxes = Column(Numeric(12, 2), nullable=False, default=0.0)
    seller_payable_amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(10), nullable=False, default="USD")
    status = Column(String(30), nullable=False, default="PENDING", index=True)
    payout_reference = Column(String(100), nullable=True)
    reconciliation_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    payment = relationship("Payment")
    seller = relationship("User")


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    quote_id = Column(String(36), ForeignKey("quotes.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    score = Column(Integer, nullable=False, default=0)
    label = Column(String(50), nullable=False, default="LOWER_CONCERN")
    flags = Column(JSON, nullable=False, default=list)
    method_version = Column(String(50), nullable=False, default="v1.0-rules")
    assessed_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    quote = relationship("Quote", back_populates="assessment")


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_payments_idempotency_key"),
        Index("ix_payments_shipment_created", "shipment_id", "created_at"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    shipment_id = Column(String(36), ForeignKey("shipments.id", ondelete="RESTRICT"), nullable=False, index=True)
    quote_id = Column(String(36), ForeignKey("quotes.id", ondelete="RESTRICT"), nullable=False, index=True)
    amount_snapshot = Column(Numeric(12, 2), nullable=False)
    currency_snapshot = Column(String(10), nullable=False)
    provider = Column(String(50), nullable=False, default="paypal_sandbox")
    provider_order_id = Column(String(100), nullable=False, unique=True, index=True)
    provider_capture_id = Column(String(100), nullable=True, unique=True, index=True)
    provider_refund_id = Column(String(100), nullable=True, unique=True, index=True)
    status = Column(String(50), nullable=False, default="CREATED", index=True)
    idempotency_key = Column(String(100), nullable=True)
    last_verified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)


class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    provider_event_id = Column(String(150), nullable=False, unique=True, index=True)
    event_type = Column(String(100), nullable=False)
    verification_status = Column(String(50), nullable=False, default="REJECTED")
    processing_status = Column(String(50), nullable=False, default="RECEIVED")
    payload_hash = Column(String(64), nullable=True)
    received_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    processed_at = Column(DateTime(timezone=True), nullable=True)


class StoredDocument(Base):
    """Private file metadata; document bytes live outside the public web root."""
    __tablename__ = "stored_documents"
    __table_args__ = (Index("ix_documents_owner_created", "owner_id", "created_at"),)

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    shipment_id = Column(String(36), ForeignKey("shipments.id", ondelete="CASCADE"), nullable=True, index=True)
    storage_key = Column(String(100), nullable=False, unique=True)
    original_filename = Column(String(255), nullable=False)
    document_type = Column(String(60), nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)
    sha256 = Column(String(64), nullable=False)
    content = Column(LargeBinary, nullable=True)
    scan_status = Column(String(30), nullable=False, default="NOT_SCANNED")
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)


class TrackingEvent(Base):
    __tablename__ = "tracking_events"
    __table_args__ = (Index("ix_tracking_shipment_time", "shipment_id", "occurred_at"),)

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    shipment_id = Column(String(36), ForeignKey("shipments.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(30), nullable=False)
    location = Column(String(200), nullable=True)
    description = Column(Text, nullable=False)
    source_kind = Column(String(40), nullable=False, default="USER_INPUT")
    occurred_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    shipment = relationship("Shipment", back_populates="tracking_events")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (Index("ix_audit_entity_time", "entity_type", "entity_id", "created_at"),)

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(36), nullable=False, index=True)
    action = Column(String(80), nullable=False)
    details = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (Index("ix_notifications_user_created", "user_id", "created_at"),)

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    shipment_id = Column(String(36), ForeignKey("shipments.id", ondelete="SET NULL"), nullable=True, index=True)
    kind = Column(String(40), nullable=False)
    title = Column(String(150), nullable=False)
    message = Column(Text, nullable=False)
    read_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)


class AIConversation(Base):
    __tablename__ = "ai_conversations"
    __table_args__ = (Index("ix_ai_conversations_user_created", "user_id", "created_at"),)

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    shipment_id = Column(String(36), ForeignKey("shipments.id", ondelete="SET NULL"), nullable=True, index=True)
    task = Column(String(50), nullable=False, default="QUOTE_COMPARISON")
    input_snapshot = Column(JSON, nullable=False, default=dict)
    response_snapshot = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
