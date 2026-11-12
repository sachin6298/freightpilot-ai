"""Seller business verification and trust scoring services."""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import math

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import SellerProfile, SellerVerificationDocument, User


class VerificationStatus:
    UNVERIFIED = "UNVERIFIED"
    PENDING_REVIEW = "PENDING_REVIEW"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    SUSPENDED = "SUSPENDED"


class TrustScoreCalculator:
    """Calculate explainable trust scores for sellers based on verified data."""

    @staticmethod
    def calculate_score(
        seller_profile: SellerProfile,
        completed_shipments: int = 0,
        average_rating: float = 0.0,
        cancellation_rate: float = 0.0,
        dispute_rate: float = 0.0,
        response_time_hours: float = 24.0,
    ) -> Dict[str, Any]:
        """Calculate explainable trust score components."""
        # 1. Business Verification (40% max)
        verification_score = 0
        if seller_profile.verification_status == VerificationStatus.VERIFIED:
            verification_score = 40
        elif seller_profile.verification_status == VerificationStatus.PENDING_REVIEW:
            verification_score = 15

        # 2. Operational History (25% max)
        history_score = min(25, completed_shipments * 2)

        # 3. Customer Ratings (20% max)
        rating_score = 0
        if average_rating > 0:
            rating_score = min(20, (average_rating / 5.0) * 20)

        # 4. Reliability - Cancellations & Disputes (15% max)
        reliability_score = 15
        # Deduct for cancellations (up to 8 points)
        reliability_score -= min(8, cancellation_rate * 40)
        # Deduct for disputes (up to 7 points)
        reliability_score -= min(7, dispute_rate * 70)
        reliability_score = max(0, reliability_score)

        # Calculate total score (0-100)
        total_score = int(round(verification_score + history_score + rating_score + reliability_score))

        return {
            "total_score": total_score,
            "components": {
                "business_verification": {
                    "score": verification_score,
                    "max_score": 40,
                    "status": seller_profile.verification_status,
                },
                "operational_history": {
                    "score": history_score,
                    "max_score": 25,
                    "completed_shipments": completed_shipments,
                },
                "customer_ratings": {
                    "score": int(round(rating_score)),
                    "max_score": 20,
                    "average_rating": average_rating,
                },
                "reliability": {
                    "score": int(round(reliability_score)),
                    "max_score": 15,
                    "cancellation_rate": cancellation_rate,
                    "dispute_rate": dispute_rate,
                },
            },
            "last_calculated": datetime.now(timezone.utc).isoformat(),
        }


class SellerVerificationService:
    """Service for managing seller verification workflow and trust scoring."""

    def __init__(self, db: Session):
        self.db = db

    def submit_for_verification(self, seller_profile: SellerProfile) -> SellerProfile:
        """Submit a seller profile for admin verification."""
        if seller_profile.verification_status == VerificationStatus.VERIFIED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Seller profile is already verified.",
            )

        # Check required fields
        if not seller_profile.business_name or not seller_profile.business_address:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Business name and address are required for verification.",
            )

        seller_profile.verification_status = VerificationStatus.PENDING_REVIEW
        self.db.commit()
        self.db.refresh(seller_profile)
        return seller_profile

    def approve_verification(
        self,
        seller_profile: SellerProfile,
        admin_user: User,
        notes: Optional[str] = None,
    ) -> SellerProfile:
        """Admin approve a seller profile."""
        if admin_user.role != "ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can approve seller verifications.",
            )

        seller_profile.verification_status = VerificationStatus.VERIFIED
        seller_profile.verified_at = datetime.now(timezone.utc)
        seller_profile.verified_by = admin_user.id
        if notes:
            seller_profile.verification_notes = notes

        # Recalculate trust score
        score_data = TrustScoreCalculator.calculate_score(seller_profile)
        seller_profile.trust_score = score_data["total_score"]

        self.db.commit()
        self.db.refresh(seller_profile)
        return seller_profile

    def reject_verification(
        self,
        seller_profile: SellerProfile,
        admin_user: User,
        reason: str,
    ) -> SellerProfile:
        """Admin reject a seller profile verification."""
        if admin_user.role != "ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can reject seller verifications.",
            )

        seller_profile.verification_status = VerificationStatus.REJECTED
        seller_profile.verification_notes = f"Rejected: {reason}"

        # Recalculate trust score
        score_data = TrustScoreCalculator.calculate_score(seller_profile)
        seller_profile.trust_score = score_data["total_score"]

        self.db.commit()
        self.db.refresh(seller_profile)
        return seller_profile

    def suspend_seller(
        self,
        seller_profile: SellerProfile,
        admin_user: User,
        reason: str,
    ) -> SellerProfile:
        """Admin suspend a seller."""
        if admin_user.role != "ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can suspend sellers.",
            )

        seller_profile.verification_status = VerificationStatus.SUSPENDED
        seller_profile.verification_notes = f"Suspended: {reason}"
        seller_profile.trust_score = 0

        self.db.commit()
        self.db.refresh(seller_profile)
        return seller_profile

    def upload_verification_document(
        self,
        seller_profile: SellerProfile,
        document_type: str,
        document_name: str,
        file_path: str,
        file_size: int,
        mime_type: str,
    ) -> SellerVerificationDocument:
        """Record an uploaded verification document."""
        doc = SellerVerificationDocument(
            seller_profile_id=seller_profile.id,
            document_type=document_type,
            document_name=document_name,
            file_path=file_path,
            file_size=file_size,
            mime_type=mime_type,
            verification_status="PENDING",
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        return doc