"""Email and phone verification utilities."""

import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import EmailVerification, PhoneVerification, User


class EmailVerificationService:
    """Service for handling email verification."""

    def __init__(self, db: Session):
        self.db = db

    def _generate_verification_token(self) -> Tuple[str, str]:
        """Generate a verification token and its hash."""
        token = secrets.token_urlsafe(32)
        token_hash = self._hash_token(token)
        return token, token_hash

    def _hash_token(self, token: str) -> str:
        """Hash a token for storage."""
        return hashlib.sha256(token.encode()).hexdigest()

    def _verify_token_match(self, token: str, token_hash: str) -> bool:
        """Verify that a token matches its hash."""
        return self._hash_token(token) == token_hash

    def create_email_verification(
        self,
        user: User,
        email: str,
        expires_minutes: int = 24 * 60
    ) -> EmailVerification:
        """Create an email verification record."""
        # Delete any existing verifications
        self.db.query(EmailVerification).filter(
            EmailVerification.user_id == user.id,
            EmailVerification.verified_at.is_(None),
        ).delete(synchronize_session=False)

        token, token_hash = self._generate_verification_token()

        verification = EmailVerification(
            user_id=user.id,
            email=email,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=expires_minutes),
        )
        self.db.add(verification)
        self.db.commit()
        self.db.refresh(verification)

        return verification

    def verify_email_token(self, token: str) -> Optional[EmailVerification]:
        """Verify an email token and return the verification record."""
        verification = self.db.query(EmailVerification).filter(
            EmailVerification.token_hash == self._hash_token(token),
            EmailVerification.verified_at.is_(None),
        ).first()

        if not verification:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token.",
            )

        if datetime.now(timezone.utc) > verification.expires_at:
            self.db.delete(verification)
            self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification token has expired.",
            )

        return verification

    def complete_email_verification(self, verification: EmailVerification) -> User:
        """Complete email verification for a user."""
        user = verification.user
        user.email_verified = True

        verification.verified_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(user)

        return user

    def check_email_verification_required(self, user: User) -> bool:
        """Check if email verification is required for a user."""
        if user.email_verified:
            return False

        # Check if there's a pending verification
        verification = self.db.query(EmailVerification).filter(
            EmailVerification.user_id == user.id,
            EmailVerification.verified_at.is_(None),
        ).first()

        return verification is None

    def can_request_email_verification(self, user: User) -> Tuple[bool, Optional[str]]:
        """Check if a user can request an email verification."""
        from typing import Tuple

        if user.email_verified:
            return True, None

        # Check cooldown (5 minutes)
        verification = self.db.query(EmailVerification).filter(
            EmailVerification.user_id == user.id,
            EmailVerification.verified_at.is_(None),
        ).order_by(EmailVerification.created_at.desc()).first()

        if verification and datetime.now(timezone.utc) - verification.created_at < timedelta(minutes=5):
            return False, "Please wait before requesting another verification email."

        return True, None
class PhoneVerificationService:
    """Service for handling phone verification with OTP."""

    def __init__(self, db: Session):
        self.db = db

    def _generate_otp(self) -> str:
        """Generate a 6-digit OTP."""
        return ''.join([str(secrets.randbelow(10)) for _ in range(6)])

    def _hash_otp(self, otp: str) -> str:
        """Hash an OTP for storage."""
        return hashlib.sha256(otp.encode()).hexdigest()

    def _verify_otp(self, otp: str, otp_hash: str) -> bool:
        """Verify an OTP against its hash."""
        return self._hash_otp(otp) == otp_hash

    def create_phone_verification(
        self,
        user: User,
        phone_number: str,
        expires_minutes: int = 10
    ) -> Tuple[PhoneVerification, str]:
        """Create a phone verification record."""
        # Delete any existing verifications
        self.db.query(PhoneVerification).filter(
            PhoneVerification.user_id == user.id,
            PhoneVerification.verified_at.is_(None),
        ).delete(synchronize_session=False)

        otp = self._generate_otp()
        otp_hash = self._hash_otp(otp)

        verification = PhoneVerification(
            user_id=user.id,
            phone_number=phone_number,
            otp_hash=otp_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=expires_minutes),
        )
        self.db.add(verification)
        self.db.commit()
        self.db.refresh(verification)

        return verification, otp

    def verify_phone_otp(
        self,
        user: User,
        phone_number: str,
        otp: str
    ) -> Optional[PhoneVerification]:
        """Verify a phone OTP and return the verification record."""
        verification = self.db.query(PhoneVerification).filter(
            PhoneVerification.user_id == user.id,
            PhoneVerification.verified_at.is_(None),
        ).first()

        if not verification:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No pending phone verification found.",
            )

        if verification.phone_number != phone_number:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number does not match verification record.",
            )

        if datetime.now(timezone.utc) > verification.expires_at:
            self.db.delete(verification)
            self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone verification has expired.",
            )

        if verification.attempts >= 5:
            self.db.delete(verification)
            self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum verification attempts exceeded.",
            )

        if not self._verify_otp(otp, verification.otp_hash):
            verification.attempts += 1
            verification.last_attempt_at = datetime.now(timezone.utc)
            self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid OTP.",
            )

        return verification

    def complete_phone_verification(
        self,
        verification: PhoneVerification,
        phone_number: str
    ) -> User:
        """Complete phone verification for a user."""
        user = verification.user
        user.phone_verified = True
        user.phone_number = phone_number

        verification.verified_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(user)

        return user

    def check_phone_verification_required(self, user: User) -> bool:
        """Check if phone verification is required for a user."""
        if user.phone_verified:
            return False

        # Check if there's a pending verification
        verification = self.db.query(PhoneVerification).filter(
            PhoneVerification.user_id == user.id,
            PhoneVerification.verified_at.is_(None),
        ).first()

        return verification is None

    def can_request_phone_verification(self, user: User) -> Tuple[bool, Optional[str]]:
        """Check if a user can request a phone verification."""
        from typing import Tuple

        if user.phone_verified:
            return True, None

        # Check cooldown (2 minutes)
        verification = self.db.query(PhoneVerification).filter(
            PhoneVerification.user_id == user.id,
            PhoneVerification.verified_at.is_(None),
        ).order_by(PhoneVerification.created_at.desc()).first()

        if verification and datetime.now(timezone.utc) - verification.created_at < timedelta(minutes=2):
            return False, "Please wait before requesting another verification."

        return True, None
class UserVerificationService:
    """Service for managing user verification requirements."""

    def __init__(self, db: Session):
        self.db = db

    def check_verification_requirements(
        self,
        user: User,
        require_email_verification: bool = True,
        require_phone_verification: bool = True,
    ) -> Dict[str, Any]:
        """Check if a user meets verification requirements."""
        from typing import Dict

        result = {
            "can_access": True,
            "missing_requirements": [],
            "verification_status": {
                "email_verified": user.email_verified,
                "phone_verified": user.phone_verified,
            },
        }

        if require_email_verification and not user.email_verified:
            result["missing_requirements"].append("email")
            result["can_access"] = False

        if require_phone_verification and not user.phone_verified:
            result["missing_requirements"].append("phone")
            result["can_access"] = False

        return result

    def enforce_verification_requirements(
        self,
        user: User,
        require_email_verification: bool = True,
        require_phone_verification: bool = True,
    ) -> User:
        """Enforce verification requirements on a user."""
        result = self.check_verification_requirements(user, require_email_verification, require_phone_verification)

        if not result["can_access"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "VERIFICATION_REQUIRED",
                    "message": "Please verify your email and phone before accessing this resource.",
                    "missing_requirements": result["missing_requirements"],
                },
            )

        return user