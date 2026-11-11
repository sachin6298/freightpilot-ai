"""Seller verification routes for business profile onboarding, admin verification, and trust score checking."""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import User, SellerProfile, SellerVerificationDocument
from app.core.security import get_current_user, require_seller, require_admin
from app.services.seller_verification_service import (
    SellerVerificationService,
    TrustScoreCalculator,
    VerificationStatus
)

router = APIRouter(prefix="/api/seller-verification", tags=["Seller Verification"])


class SubmitVerificationRequest(BaseModel):
    business_name: str = Field(..., min_length=2, max_length=200)
    business_address: str = Field(..., min_length=5)
    country: str = Field(..., min_length=2, max_length=2)
    contact_person: str = Field(..., min_length=2, max_length=150)
    contact_email: str
    contact_phone: str = Field(..., min_length=5, max_length=30)
    registration_number: Optional[str] = None
    tax_id: Optional[str] = None
    business_type: Optional[str] = None
    years_in_operation: Optional[int] = None
    service_regions: Optional[List[str]] = None
    transport_modes: Optional[List[str]] = None


class VerificationDecisionRequest(BaseModel):
    decision: str = Field(..., pattern="^(APPROVE|REJECT|SUSPEND)$")
    reason: Optional[str] = None


@router.get("/status")
def get_verification_status(
    user: User = Depends(require_seller),
    db: Session = Depends(get_db)
):
    """Get the current seller's verification status and trust score details."""
    profile = db.query(SellerProfile).filter(SellerProfile.user_id == user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Seller profile not found.")

    score_details = TrustScoreCalculator.calculate_score(profile)

    return {
        "status": profile.verification_status,
        "trust_score": profile.trust_score,
        "trust_score_details": score_details,
        "verified_at": profile.verified_at,
        "verification_notes": profile.verification_notes,
    }


@router.post("/submit")
def submit_verification(
    data: SubmitVerificationRequest,
    user: User = Depends(require_seller),
    db: Session = Depends(get_db)
):
    """Submit or update business profile details and request verification."""
    profile = db.query(SellerProfile).filter(SellerProfile.user_id == user.id).first()
    if not profile:
        profile = SellerProfile(user_id=user.id, **data.model_dump())
        db.add(profile)
    else:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(profile, key, value)

    service = SellerVerificationService(db)
    service.submit_for_verification(profile)

    return {
        "message": "Verification submitted successfully. An administrator will review your application.",
        "status": profile.verification_status
    }


@router.get("/admin/pending")
def list_pending_verifications(
    user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin endpoint to list all seller profiles awaiting review."""
    pending = db.query(SellerProfile).filter(
        SellerProfile.verification_status.in_([VerificationStatus.PENDING_REVIEW, VerificationStatus.UNVERIFIED])
    ).all()

    return [
        {
            "id": p.id,
            "user_id": p.user_id,
            "business_name": p.business_name,
            "country": p.country,
            "contact_email": p.contact_email,
            "verification_status": p.verification_status,
            "trust_score": p.trust_score,
            "created_at": p.created_at,
        }
        for p in pending
    ]


@router.post("/admin/{seller_profile_id}/decision")
def process_verification_decision(
    seller_profile_id: str,
    decision_data: VerificationDecisionRequest,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin endpoint to approve, reject, or suspend a seller profile."""
    profile = db.query(SellerProfile).filter(SellerProfile.id == seller_profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Seller profile not found.")

    service = SellerVerificationService(db)
    if decision_data.decision == "APPROVE":
        service.approve_verification(profile, user, decision_data.reason)
    elif decision_data.decision == "REJECT":
        service.reject_verification(profile, user, decision_data.reason or "Requirements not met.")
    elif decision_data.decision == "SUSPEND":
        service.suspend_seller(profile, user, decision_data.reason or "Policy violation.")

    return {
        "message": f"Seller verification status updated to {profile.verification_status}",
        "verification_status": profile.verification_status,
        "trust_score": profile.trust_score
    }
