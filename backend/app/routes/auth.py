"""Buyer and Seller authentication, registration and verification endpoints."""

from datetime import datetime, timedelta, timezone
import secrets

from pydantic import BaseModel, ConfigDict, Field, EmailStr
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token, get_current_user, hash_password,
    normalize_email, verify_password,
    require_buyer, require_seller, require_admin,
    require_verified_email, require_verified_phone, require_full_verification,
)
from app.db.models import User, BuyerProfile, SellerProfile, EmailVerification, PhoneVerification
from app.db.session import get_db

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# Valid roles
BUYER = "BUYER"
SELLER = "SELLER"
ADMIN = "ADMIN"


# ================== Request Models ==================

class BuyerRegistrationRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=254)
    password: str = Field(..., min_length=10, max_length=128)
    company_name: str | None = Field(None, max_length=200)
    contact_person: str | None = Field(None, max_length=150)
    phone_number: str | None = Field(None, max_length=30)


class SellerRegistrationRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=254)
    password: str = Field(..., min_length=10, max_length=128)
    business_name: str = Field(..., min_length=1, max_length=200)
    business_address: str = Field(..., min_length=1)
    country: str = Field(..., min_length=2, max_length=2)
    contact_person: str = Field(..., min_length=1, max_length=150)
    contact_phone: str = Field(..., min_length=1, max_length=30)
    registration_number: str | None = Field(None, max_length=100)


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=254)
    password: str = Field(..., min_length=1, max_length=128)


class EmailVerificationRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=254)


class VerifyEmailRequest(BaseModel):
    token: str


class PhoneVerificationRequest(BaseModel):
    phone_number: str = Field(..., min_length=10, max_length=30)


class VerifyPhoneRequest(BaseModel):
    phone_number: str = Field(..., min_length=10, max_length=30)
    otp: str = Field(..., min_length=4, max_length=8)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    role: str
    is_active: bool
    email_verified: bool
    phone_verified: bool | None = None


class BuyerProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    company_name: str | None
    contact_person: str | None
    phone_number: str | None
    default_currency: str


class SellerProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    business_name: str
    business_address: str
    country: str
    verification_status: str
    trust_score: int


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse
    requires_email_verification: bool = False
    requires_phone_verification: bool = False


class VerificationStatusResponse(BaseModel):
    email_verified: bool
    phone_verified: bool
    email_verification_sent: bool = False


# ================== Helper Functions ==================

def _generate_otp() -> str:
    """Generate a 6-digit OTP."""
    return ''.join([str(secrets.randbelow(10)) for _ in range(6)])


def _token_response(user: User, db: Session, requires_email_verification: bool = False, requires_phone_verification: bool = False) -> dict:
    token, expires_in = create_access_token(user)
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": expires_in,
        "user": {
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
            "email_verified": user.email_verified,
            "phone_verified": user.phone_verified,
        },
        "requires_email_verification": requires_email_verification,
        "requires_phone_verification": requires_phone_verification,
    }


def _create_user_with_profile(db: Session, email: str, password_hash: str, role: str,
                                profile_data: dict | None = None) -> User:
    """Create a new user with the appropriate profile type."""
    user = User(
        email=email,
        password_hash=password_hash,
        role=role,
        is_active=True,
        email_verified=False,
        phone_verified=False,
    )
    db.add(user)
    db.flush()

    if role == BUYER and profile_data:
        buyer_profile = BuyerProfile(
            user_id=user.id,
            company_name=profile_data.get("company_name"),
            contact_person=profile_data.get("contact_person"),
            phone_number=profile_data.get("phone_number"),
            default_currency="USD",
        )
        db.add(buyer_profile)
    elif role == SELLER and profile_data:
        seller_profile = SellerProfile(
            user_id=user.id,
            business_name=profile_data["business_name"],
            business_address=profile_data["business_address"],
            country=profile_data["country"],
            contact_person=profile_data["contact_person"],
            contact_email=email,
            contact_phone=profile_data["contact_phone"],
            registration_number=profile_data.get("registration_number"),
            verification_status="UNVERIFIED",
            trust_score=50,
        )
        db.add(seller_profile)

    db.commit()
    db.refresh(user)
    return user


# ================== Registration Endpoints ==================

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register_user(payload: BuyerRegistrationRequest, db: Session = Depends(get_db)):
    """Register a new user account (default buyer/user role)."""
    try:
        email = normalize_email(payload.email)
        password_hash = hash_password(payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail={
            "code": "INVALID_REGISTRATION",
            "message": str(exc),
        })

    profile_data = {
        "company_name": payload.company_name,
        "contact_person": payload.contact_person,
        "phone_number": payload.phone_number,
    }

    try:
        user = _create_user_with_profile(db, email, password_hash, BUYER, profile_data)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail={
            "code": "EMAIL_ALREADY_REGISTERED",
            "message": "An account with this email already exists.",
        })

    return _token_response(user, db, requires_email_verification=True, requires_phone_verification=True)


@router.post("/register/buyer", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register_buyer(payload: BuyerRegistrationRequest, db: Session = Depends(get_db)):
    """Register a new buyer account."""
    try:
        email = normalize_email(payload.email)
        password_hash = hash_password(payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail={
            "code": "INVALID_REGISTRATION",
            "message": str(exc),
        })

    profile_data = {
        "company_name": payload.company_name,
        "contact_person": payload.contact_person,
        "phone_number": payload.phone_number,
    }

    try:
        user = _create_user_with_profile(db, email, password_hash, BUYER, profile_data)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail={
            "code": "EMAIL_ALREADY_REGISTERED",
            "message": "An account with this email already exists.",
        })

    return _token_response(user, db, requires_email_verification=True, requires_phone_verification=True)


@router.post("/register/seller", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register_seller(payload: SellerRegistrationRequest, db: Session = Depends(get_db)):
    """Register a new seller account."""
    try:
        email = normalize_email(payload.email)
        password_hash = hash_password(payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail={
            "code": "INVALID_REGISTRATION",
            "message": str(exc),
        })

    profile_data = {
        "business_name": payload.business_name,
        "business_address": payload.business_address,
        "country": payload.country,
        "contact_person": payload.contact_person,
        "contact_phone": payload.contact_phone,
        "registration_number": payload.registration_number,
    }

    try:
        user = _create_user_with_profile(db, email, password_hash, SELLER, profile_data)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail={
            "code": "EMAIL_ALREADY_REGISTERED",
            "message": "An account with this email already exists.",
        })

    return _token_response(user, db, requires_email_verification=True, requires_phone_verification=True)


# ================== Login Endpoints ==================

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """Login with email and password. Supports both buyers and sellers."""
    try:
        email = normalize_email(payload.email)
    except ValueError:
        email = ""

    user = db.query(User).filter(User.email == email, User.is_active.is_(True)).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail={
            "code": "INVALID_CREDENTIALS",
            "message": "Email or password is incorrect.",
        }, headers={"WWW-Authenticate": "Bearer"})

    requires_email_verification = not user.email_verified
    requires_phone_verification = not user.phone_verified

    return _token_response(user, db, requires_email_verification, requires_phone_verification)


# ================== Email Verification Endpoints ==================

@router.post("/send-email-verification")
def send_email_verification(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Send email verification link to the current user."""
    if user.email_verified:
        raise HTTPException(status_code=400, detail={
            "code": "EMAIL_ALREADY_VERIFIED",
            "message": "Email is already verified.",
        })

    existing = db.query(EmailVerification).filter(
        EmailVerification.user_id == user.id,
        EmailVerification.verified_at.is_(None),
    ).first()

    if existing:
        if datetime.now(timezone.utc) - existing.created_at < timedelta(minutes=5):
            raise HTTPException(status_code=429, detail={
                "code": "VERIFICATION_COOLDOWN",
                "message": "Please wait before requesting another verification email.",
            })
        db.delete(existing)
        db.commit()

    token = secrets.token_urlsafe(32)
    token_hash = hash_password(token)[:86]

    verification = EmailVerification(
        user_id=user.id,
        email=user.email,
        token=token,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db.add(verification)
    db.commit()

    return {
        "code": "VERIFICATION_SENT",
        "message": "Verification email sent. Check your inbox.",
        "verification_token": token,
    }


@router.post("/verify-email")
def verify_email(payload: VerifyEmailRequest, db: Session = Depends(get_db)):
    """Verify email address using the token from the verification email."""
    verification = db.query(EmailVerification).filter(
        EmailVerification.token == payload.token,
        EmailVerification.verified_at.is_(None),
    ).first()

    if not verification:
        raise HTTPException(status_code=400, detail={
            "code": "INVALID_TOKEN",
            "message": "Invalid or expired verification token.",
        })

    if datetime.now(timezone.utc) > verification.expires_at:
        db.delete(verification)
        db.commit()
        raise HTTPException(status_code=400, detail={
            "code": "TOKEN_EXPIRED",
            "message": "Verification token has expired.",
        })

    user = db.query(User).filter(User.id == verification.user_id).first()
    user.email_verified = True
    verification.verified_at = datetime.now(timezone.utc)

    db.delete(verification)
    db.commit()

    return {"code": "EMAIL_VERIFIED", "message": "Email address verified successfully."}


# ================== Phone Verification Endpoints ==================

@router.post("/send-phone-verification")
def send_phone_verification(payload: PhoneVerificationRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Send phone OTP to the current user."""
    if user.phone_verified:
        raise HTTPException(status_code=400, detail={
            "code": "PHONE_ALREADY_VERIFIED",
            "message": "Phone number is already verified.",
        })

    existing = db.query(PhoneVerification).filter(
        PhoneVerification.user_id == user.id,
        PhoneVerification.verified_at.is_(None),
    ).first()

    if existing:
        if datetime.now(timezone.utc) - existing.created_at < timedelta(minutes=2):
            raise HTTPException(status_code=429, detail={
                "code": "VERIFICATION_COOLDOWN",
                "message": "Please wait before requesting another OTP.",
            })
        db.delete(existing)
        db.commit()

    otp = _generate_otp()
    otp_hash = hash_password(otp)

    verification = PhoneVerification(
        user_id=user.id,
        phone_number=payload.phone_number,
        otp_hash=otp_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
    )
    db.add(verification)
    db.commit()

    return {"code": "OTP_SENT", "message": "OTP sent to your phone.", "otp": otp}


@router.post("/verify-phone")
def verify_phone(payload: VerifyPhoneRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Verify phone number using the OTP."""
    verification = db.query(PhoneVerification).filter(
        PhoneVerification.user_id == user.id,
        PhoneVerification.verified_at.is_(None),
    ).order_by(PhoneVerification.created_at.desc()).first()

    if not verification:
        raise HTTPException(status_code=400, detail={
            "code": "INVALID_REQUEST",
            "message": "No pending verification found.",
        })

    if datetime.now(timezone.utc) > verification.expires_at:
        db.delete(verification)
        db.commit()
        raise HTTPException(status_code=400, detail={"code": "OTP_EXPIRED", "message": "OTP has expired."})

    if verification.attempts >= 5:
        db.delete(verification)
        db.commit()
        raise HTTPException(status_code=400, detail={"code": "MAX_ATTEMPTS_EXCEEDED", "message": "Max attempts exceeded."})

    if not verify_password(payload.otp, verification.otp_hash):
        verification.attempts += 1
        verification.last_attempt_at = datetime.now(timezone.utc)
        db.commit()
        raise HTTPException(status_code=400, detail={"code": "INVALID_OTP", "message": "Invalid OTP."})

    user.phone_verified = True
    user.phone_number = payload.phone_number
    verification.verified_at = datetime.now(timezone.utc)

    db.commit()

    return {"code": "PHONE_VERIFIED", "message": "Phone number verified successfully."}


# ================== User Info Endpoints ==================

@router.get("/me", response_model=UserResponse)
def get_current_user_info(user: User = Depends(get_current_user)) -> User:
    """Get current authenticated user's information."""
    return user


@router.get("/me/verification-status", response_model=VerificationStatusResponse)
def get_verification_status(user: User = Depends(get_current_user)):
    """Get current user's email and phone verification status."""
    return {
        "email_verified": user.email_verified,
        "phone_verified": user.phone_verified or False,
    }


@router.get("/me/buyer-profile", response_model=BuyerProfileResponse)
def get_buyer_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get current buyer's profile information."""
    if user.role != BUYER:
        raise HTTPException(status_code=403, detail={"code": "NOT_A_BUYER", "message": "Only for buyers."})

    profile = db.query(BuyerProfile).filter(BuyerProfile.user_id == user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail={"code": "PROFILE_NOT_FOUND", "message": "Profile not found."})

    return profile


@router.get("/me/seller-profile", response_model=SellerProfileResponse)
def get_seller_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get current seller's profile information."""
    if user.role != SELLER:
        raise HTTPException(status_code=403, detail={"code": "NOT_A_SELLER", "message": "Only for sellers."})

    profile = db.query(SellerProfile).filter(SellerProfile.user_id == user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail={"code": "PROFILE_NOT_FOUND", "message": "Profile not found."})

    return profile


@router.post("/logout")
def logout():
    """Logout endpoint. Client discards the token."""
    return {"code": "LOGGED_OUT", "message": "Logged out successfully."}