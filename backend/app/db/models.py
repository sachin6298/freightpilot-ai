"""SQLAlchemy models for users, freight operations, payments and auditability."""

from datetime import datetime, timezone
import uuid

from sqlalchemy import (
    Boolean, Column, Date, DateTime, ForeignKey, Index, Integer, JSON,
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
    role = Column(String(30), nullable=False, default="USER")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    shipments = relationship("Shipment", back_populates="owner")


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
