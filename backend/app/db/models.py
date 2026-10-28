"""SQLAlchemy ORM models for shipments and freight quotes."""

from datetime import datetime, timezone
import uuid

from sqlalchemy import (
    Column,
    String,
    Numeric,
    Date,
    DateTime,
    Integer,
    JSON,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from app.db.session import Base


def utc_now() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


class Shipment(Base):
    """Freight shipment request model."""

    __tablename__ = "shipments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cargo_type = Column(String(100), nullable=False)
    quantity_tonnes = Column(Numeric(12, 2), nullable=False)
    origin = Column(String(150), nullable=False)
    destination = Column(String(150), nullable=False)
    ready_date = Column(Date, nullable=False)
    required_arrival_date = Column(Date, nullable=True)
    currency = Column(String(10), nullable=False, default="USD")
    mode = Column(String(20), nullable=False, default="DEMO")
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    # Relationships
    quotes = relationship("Quote", back_populates="shipment", cascade="all, delete-orphan")


class Quote(Base):
    """Freight quote model."""

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

    # Relationships
    shipment = relationship("Shipment", back_populates="quotes")
    assessment = relationship("RiskAssessment", back_populates="quote", uselist=False, cascade="all, delete-orphan")


class RiskAssessment(Base):
    """Deterministic risk assessment model per DATA_MODEL.md."""

    __tablename__ = "risk_assessments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    quote_id = Column(String(36), ForeignKey("quotes.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    score = Column(Integer, nullable=False, default=0)
    label = Column(String(50), nullable=False, default="LOWER_CONCERN")
    flags = Column(JSON, nullable=False, default=list)
    method_version = Column(String(50), nullable=False, default="v1.0-rules")
    assessed_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    # Relationships
    quote = relationship("Quote", back_populates="assessment")
