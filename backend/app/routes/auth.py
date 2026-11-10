"""Buyer and Seller authentication, registration and verification endpoints."""

from datetime import datetime, timedelta, timezone
import secrets
import hashlib
import logging

import jwt
import httpx
from jwt import PyJWKClient

from pydantic import BaseModel, ConfigDict, Field
from app.config import settings
from fastapi.responses import HTMLResponse
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from app.services.verification_delivery import send_verification_email, send_phone_otp, verify_firebase_phone_token, DeliveryNotConfigured
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token, create_refresh_token, decode_refresh_token, get_current_user, hash_password,
    normalize_email, verify_password,
    require_buyer, require_seller, require_admin,
    require_verified_email, require_verified_phone, require_full_verification,
    hash_otp, verify_otp,
)
from app.db.models import User, BuyerProfile, SellerProfile, EmailVerification, PhoneVerification, OAuthIdentity, PasswordResetToken
from app.db.session import get_db

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# Valid roles
BUYER = "BUYER"
SELLER = "SELLER"
ADMIN = "ADMIN"
logger = logging.getLogger(__name__)


# ================== Request Models ==================

class BuyerRegistrationRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=254)
    password: str = Field(..., min_length=10, max_length=128)
    company_name: str | None = Field(None, max_length=200)
    contact_person: str | None = Field(None, max_length=150)
    phone_number: str | None = Field(None, min_length=9, max_length=16, pattern=r"^\+[1-9]\d{7,14}$")


class SellerRegistrationRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=254)
    password: str = Field(..., min_length=10, max_length=128)
    business_name: str = Field(..., min_length=1, max_length=200)
    business_address: str = Field(..., min_length=1)
    country: str = Field(..., min_length=2, max_length=2)
    contact_person: str = Field(..., min_length=1, max_length=150)
    contact_phone: str = Field(..., min_length=9, max_length=16, pattern=r"^\+[1-9]\d{7,14}$")
    registration_number: str | None = Field(None, max_length=100)


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=254)
    password: str = Field(..., min_length=1, max_length=128)


class OAuthSignInRequest(BaseModel):
    id_token: str = Field(..., min_length=50, max_length=10000)
    nonce: str = Field(..., min_length=16, max_length=256)


class AppleSignInRequest(BaseModel):
    authorization_code: str = Field(..., min_length=20, max_length=4096)
    nonce: str = Field(..., min_length=16, max_length=256)


class PhoneLoginRequest(BaseModel):
    phone_number: str = Field(..., min_length=9, max_length=16, pattern=r"^\+[1-9]\d{7,14}$")


class PhoneLoginVerifyRequest(PhoneLoginRequest):
    otp: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")


class EmailVerificationRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=254)


class VerifyEmailRequest(BaseModel):
    token: str = Field(..., min_length=20, max_length=100)


class SetPhoneRequest(BaseModel):
    phone_number: str = Field(..., min_length=9, max_length=16, pattern=r"^\+[1-9]\d{7,14}$")


class PhoneVerificationRequest(BaseModel):
    phone_number: str = Field(..., min_length=9, max_length=16, pattern=r"^\+[1-9]\d{7,14}$")


class VerifyPhoneRequest(BaseModel):
    phone_number: str = Field(..., min_length=9, max_length=16, pattern=r"^\+[1-9]\d{7,14}$")
    otp: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")


class ForgotPasswordRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=254)


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=20, max_length=100)
    password: str = Field(..., min_length=10, max_length=128)


class DeleteAccountRequest(BaseModel):
    password: str = Field(..., min_length=1, max_length=128)
    reason: str | None = Field(None, max_length=500)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    role: str
    is_active: bool
    email_verified: bool
    phone_verified: bool | None = None
    phone_number: str | None = None


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
    refresh_token: str | None = None
    token_type: str = "bearer"
    expires_in: int
    refresh_expires_in: int | None = None
    user: UserResponse
    requires_email_verification: bool = False
    requires_phone_verification: bool = False


class VerificationStatusResponse(BaseModel):
    email_verified: bool
    phone_verified: bool
    email_verification_sent: bool = False


# ================== Helper Functions ==================

def _utc_aware(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def _generate_otp() -> str:
    """Generate a 6-digit OTP."""
    return ''.join([str(secrets.randbelow(10)) for _ in range(6)])


def _token_response(user: User, db: Session, requires_email_verification: bool = False, requires_phone_verification: bool = False) -> dict:
    access_token, expires_in = create_access_token(user)
    refresh_token, refresh_expires_in = create_refresh_token(user)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": expires_in,
        "refresh_expires_in": refresh_expires_in,
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
        phone_number=(profile_data.get("phone_number") or profile_data.get("contact_phone")) if profile_data else None,
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

def _ensure_phone_available(db: Session, phone_number: str | None) -> None:
    if not phone_number:
        return
    existing = db.query(User.id).filter(User.phone_number == phone_number.strip()).first()
    if existing:
        raise HTTPException(status_code=409, detail={
            "code": "PHONE_NUMBER_IN_USE",
            "message": "This phone number is already linked to another account.",
        })


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register_user(payload: BuyerRegistrationRequest, db: Session = Depends(get_db)):
    """Register a new buyer account."""
    if settings.is_production and not payload.phone_number:
        raise HTTPException(status_code=422, detail={"code": "PHONE_REQUIRED", "message": "Provide a phone number in E.164 format, including the country code."})
    _ensure_phone_available(db, payload.phone_number)
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
    if settings.is_production and not payload.phone_number:
        raise HTTPException(status_code=422, detail={"code": "PHONE_REQUIRED", "message": "Provide a phone number in E.164 format, including the country code."})
    _ensure_phone_available(db, payload.phone_number)
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
    _ensure_phone_available(db, payload.contact_phone)
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



# ================== Social and phone authentication ==================

def _apple_client_secret() -> str:
    """Create a short-lived ES256 client secret for Apple's token endpoint."""
    required = [
        settings.APPLE_CLIENT_ID,
        settings.APPLE_TEAM_ID,
        settings.APPLE_KEY_ID,
        settings.APPLE_PRIVATE_KEY,
        settings.APPLE_REDIRECT_URI,
    ]
    if not all(required):
        raise HTTPException(status_code=503, detail={
            "code": "APPLE_NOT_CONFIGURED",
            "message": "Apple sign-in requires its Services ID, Team ID, Key ID, private key and registered Return URL.",
        })
    now = datetime.now(timezone.utc)
    key = settings.APPLE_PRIVATE_KEY.replace("\\n", "\n")
    payload = {
        "iss": settings.APPLE_TEAM_ID,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=5)).timestamp()),
        "aud": "https://appleid.apple.com",
        "sub": settings.APPLE_CLIENT_ID,
    }
    try:
        return jwt.encode(payload, key, algorithm="ES256", headers={"kid": settings.APPLE_KEY_ID})
    except Exception as exc:
        logger.error("Apple client secret could not be created (%s)", type(exc).__name__)
        raise HTTPException(status_code=503, detail={
            "code": "APPLE_KEY_INVALID",
            "message": "Apple sign-in private key configuration is invalid.",
        })


def _exchange_apple_authorization_code(authorization_code: str) -> str:
    """Exchange Apple's one-time web authorization code for a server-returned ID token."""
    client_secret = _apple_client_secret()
    try:
        response = httpx.post(
            "https://appleid.apple.com/auth/token",
            data={
                "client_id": settings.APPLE_CLIENT_ID,
                "client_secret": client_secret,
                "code": authorization_code,
                "grant_type": "authorization_code",
                "redirect_uri": settings.APPLE_REDIRECT_URI,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=12.0,
        )
        response.raise_for_status()
        result = response.json()
        id_token = result.get("id_token")
        if not isinstance(id_token, str) or not id_token:
            raise ValueError("Apple token endpoint did not return an ID token")
        return id_token
    except (httpx.HTTPError, ValueError, KeyError) as exc:
        logger.info("Apple authorization code exchange failed (%s)", type(exc).__name__)
        raise HTTPException(status_code=401, detail={
            "code": "APPLE_CODE_EXCHANGE_FAILED",
            "message": "Apple could not complete sign-in. Please try again.",
        })


_PROVIDER_JWKS = {
    "google": "https://www.googleapis.com/oauth2/v3/certs",
    "apple": "https://appleid.apple.com/auth/keys",
}


def _verify_provider_identity(provider: str, id_token: str, nonce: str) -> dict:
    """Verify provider signature, issuer, audience, expiry and one-time nonce."""
    provider = provider.lower()
    client_id = settings.GOOGLE_CLIENT_ID if provider == "google" else settings.APPLE_CLIENT_ID
    if provider not in _PROVIDER_JWKS or not client_id:
        raise HTTPException(status_code=503, detail={
            "code": "OAUTH_NOT_CONFIGURED",
            "message": f"{provider.title()} sign-in is not configured on the API.",
        })
    try:
        signing_key = PyJWKClient(_PROVIDER_JWKS[provider], cache_keys=True).get_signing_key_from_jwt(id_token).key
        issuer = ["accounts.google.com", "https://accounts.google.com"] if provider == "google" else "https://appleid.apple.com"
        claims = jwt.decode(
            id_token,
            signing_key,
            algorithms=["RS256"] if provider == "google" else ["ES256", "RS256"],
            audience=client_id,
            issuer=issuer,
            options={"require": ["exp", "iat", "sub", "iss", "aud", "nonce"]},
        )
    except Exception as exc:
        # Provider/network/key errors are intentionally collapsed into a safe auth response.
        logger.info("%s identity token verification rejected (%s)", provider, type(exc).__name__)
        raise HTTPException(status_code=401, detail={
            "code": "INVALID_PROVIDER_TOKEN",
            "message": f"{provider.title()} sign-in could not be verified. Please try again.",
        })
    token_nonce = str(claims.get("nonce", ""))
    accepted_nonces = (nonce, hashlib.sha256(nonce.encode("utf-8")).hexdigest())
    if not any(secrets.compare_digest(token_nonce, candidate) for candidate in accepted_nonces):
        raise HTTPException(status_code=401, detail={
            "code": "INVALID_PROVIDER_NONCE",
            "message": "The sign-in session expired. Please try again.",
        })
    verified = claims.get("email_verified")
    if isinstance(verified, str):
        verified = verified.lower() == "true"
    if not verified:
        raise HTTPException(status_code=403, detail={
            "code": "PROVIDER_EMAIL_NOT_VERIFIED",
            "message": "Verify your email address with the identity provider before continuing.",
        })
    if not claims.get("email"):
        raise HTTPException(status_code=422, detail={
            "code": "PROVIDER_EMAIL_MISSING",
            "message": "The identity provider did not supply an email address.",
        })
    return claims


def _complete_oauth_sign_in(provider: str, payload: OAuthSignInRequest, db: Session) -> dict:
    claims = _verify_provider_identity(provider, payload.id_token, payload.nonce)
    subject = str(claims.get("sub", "")).strip()
    if not subject:
        raise HTTPException(status_code=401, detail={"code": "INVALID_PROVIDER_SUBJECT", "message": "Provider identity is incomplete."})

    identity = db.query(OAuthIdentity).filter(
        OAuthIdentity.provider == provider,
        OAuthIdentity.subject == subject,
    ).first()
    if identity:
        user = db.query(User).filter(User.id == identity.user_id, User.is_active.is_(True)).first()
        if not user:
            raise HTTPException(status_code=403, detail={"code": "ACCOUNT_UNAVAILABLE", "message": "This account is unavailable."})
        return _token_response(user, db, not user.email_verified, not user.phone_verified)

    try:
        email = normalize_email(str(claims["email"]))
    except (KeyError, ValueError):
        raise HTTPException(status_code=422, detail={"code": "INVALID_PROVIDER_EMAIL", "message": "The identity provider returned an invalid email."})

    user = db.query(User).filter(func.lower(User.email) == email).first()
    if user and not user.is_active:
        raise HTTPException(status_code=403, detail={"code": "ACCOUNT_UNAVAILABLE", "message": "This account is unavailable."})
    if user:
        # Linking is allowed only because the provider's verified email was checked above.
        user.email_verified = True
    else:
        user = User(
            email=email,
            password_hash=hash_password(secrets.token_urlsafe(48)),
            role=BUYER,
            is_active=True,
            email_verified=True,
            phone_verified=False,
        )
        db.add(user)
        db.flush()
        db.add(BuyerProfile(user_id=user.id, default_currency="USD"))

    db.add(OAuthIdentity(provider=provider, subject=subject, user_id=user.id, email=email))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # A concurrent first login can create the mapping; re-read it safely.
        identity = db.query(OAuthIdentity).filter(
            OAuthIdentity.provider == provider,
            OAuthIdentity.subject == subject,
        ).first()
        if not identity:
            raise HTTPException(status_code=409, detail={"code": "OAUTH_LINK_CONFLICT", "message": "This identity could not be linked. Please retry."})
        user = db.query(User).filter(User.id == identity.user_id, User.is_active.is_(True)).first()
        if not user:
            raise HTTPException(status_code=403, detail={"code": "ACCOUNT_UNAVAILABLE", "message": "This account is unavailable."})
    db.refresh(user)
    return _token_response(user, db, not user.email_verified, not user.phone_verified)


@router.post("/oauth/google", response_model=TokenResponse)
def google_sign_in(payload: OAuthSignInRequest, db: Session = Depends(get_db)):
    return _complete_oauth_sign_in("google", payload, db)


@router.post("/oauth/apple", response_model=TokenResponse)
def apple_sign_in(payload: AppleSignInRequest, db: Session = Depends(get_db)):
    id_token = _exchange_apple_authorization_code(payload.authorization_code)
    oauth_payload = OAuthSignInRequest(id_token=id_token, nonce=payload.nonce)
    return _complete_oauth_sign_in("apple", oauth_payload, db)


@router.post("/phone/request")
def request_phone_login(payload: PhoneLoginRequest, db: Session = Depends(get_db)):
    """Send a short-lived SMS login code without revealing whether a number has an account."""
    phone = payload.phone_number.strip()
    matches = db.query(User).filter(User.phone_number == phone, User.is_active.is_(True)).all()
    if not matches:
        return {"code": "OTP_REQUESTED", "message": "If an active account is linked to this number, a code has been sent."}
    if len(matches) != 1:
        logger.warning("SMS sign-in unavailable because a phone number is linked to multiple accounts.")
        return {"code": "OTP_REQUESTED", "message": "If an active account is linked to this number, a code has been sent."}
    user = matches[0]
    existing = db.query(PhoneVerification).filter(
        PhoneVerification.user_id == user.id,
        PhoneVerification.verified_at.is_(None),
    ).order_by(PhoneVerification.created_at.desc()).first()
    if existing and datetime.now(timezone.utc) - _utc_aware(existing.created_at) < timedelta(minutes=2):
        return {"code": "OTP_REQUESTED", "message": "If an active account is linked to this number, a code has been sent."}
    if existing:
        db.delete(existing)
        db.flush()
    otp = _generate_otp()
    verification = PhoneVerification(
        user_id=user.id,
        phone_number=phone,
        otp_hash=hash_otp(otp),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
    )
    db.add(verification)
    try:
        send_phone_otp(phone, otp)
    except DeliveryNotConfigured as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail={"code": "SMS_DELIVERY_NOT_CONFIGURED", "message": str(exc)})
    except Exception:
        db.rollback()
        raise HTTPException(status_code=502, detail={"code": "SMS_DELIVERY_FAILED", "message": "The SMS could not be delivered. Please retry later."})
    db.commit()
    return {"code": "OTP_REQUESTED", "message": "If an active account is linked to this number, a code has been sent."}


@router.post("/phone/verify", response_model=TokenResponse)
def verify_phone_login(payload: PhoneLoginVerifyRequest, db: Session = Depends(get_db)):
    """Verify an SMS login code and issue the normal FreightPilot access token."""
    phone = payload.phone_number.strip()
    matches = db.query(User).filter(User.phone_number == phone, User.is_active.is_(True)).all()
    if len(matches) != 1:
        raise HTTPException(status_code=401, detail={"code": "INVALID_PHONE_CODE", "message": "The phone number or verification code is invalid."})
    user = matches[0]
    verification = db.query(PhoneVerification).filter(
        PhoneVerification.user_id == user.id,
        PhoneVerification.phone_number == phone,
        PhoneVerification.verified_at.is_(None),
    ).order_by(PhoneVerification.created_at.desc()).first()
    if not verification or datetime.now(timezone.utc) > _utc_aware(verification.expires_at):
        if verification:
            db.delete(verification)
            db.commit()
        raise HTTPException(status_code=401, detail={"code": "OTP_EXPIRED", "message": "The verification code is invalid or expired. Request a new code."})
    if verification.attempts >= 5:
        db.delete(verification)
        db.commit()
        raise HTTPException(status_code=429, detail={"code": "OTP_ATTEMPTS_EXCEEDED", "message": "Too many attempts. Request a new code."})
    if not verify_otp(payload.otp, verification.otp_hash):
        verification.attempts += 1
        verification.last_attempt_at = datetime.now(timezone.utc)
        db.commit()
        raise HTTPException(status_code=401, detail={"code": "INVALID_PHONE_CODE", "message": "The phone number or verification code is invalid."})
    verification.verified_at = datetime.now(timezone.utc)
    user.phone_verified = True
    db.commit()
    db.refresh(user)
    return _token_response(user, db, not user.email_verified, False)


# ================== Email Verification Endpoints ==================

@router.post("/send-email-verification")
def send_email_verification(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Send a one-time email verification link; token material is never returned by the API."""
    if user.email_verified:
        raise HTTPException(status_code=400, detail={"code": "EMAIL_ALREADY_VERIFIED", "message": "Email is already verified."})
    existing = db.query(EmailVerification).filter(
        EmailVerification.user_id == user.id, EmailVerification.verified_at.is_(None),
    ).order_by(EmailVerification.created_at.desc()).first()
    if existing and datetime.now(timezone.utc) - _utc_aware(existing.created_at) < timedelta(minutes=5):
        raise HTTPException(status_code=429, detail={"code": "VERIFICATION_COOLDOWN", "message": "Please wait before requesting another verification email."})
    if existing:
        db.delete(existing)
        db.flush()
    token = secrets.token_urlsafe(32)
    verification = EmailVerification(
        user_id=user.id, email=user.email,
        token_hash=hashlib.sha256(token.encode("utf-8")).hexdigest(),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db.add(verification)
    try:
        send_verification_email(user.email, token)
    except DeliveryNotConfigured as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail={"code": "EMAIL_DELIVERY_NOT_CONFIGURED", "message": str(exc)})
    except Exception:
        db.rollback()
        raise HTTPException(status_code=502, detail={"code": "EMAIL_DELIVERY_FAILED", "message": "Verification email could not be delivered. Please retry later."})
    db.commit()
    return {"code": "VERIFICATION_SENT", "message": "Verification email sent. Check your inbox."}




def _consume_email_verification(token: str, db: Session) -> None:
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    verification = db.query(EmailVerification).filter(
        EmailVerification.token_hash == token_hash,
        EmailVerification.verified_at.is_(None),
    ).first()
    if not verification:
        raise HTTPException(status_code=400, detail={"code": "INVALID_TOKEN", "message": "Invalid or expired verification token."})
    if datetime.now(timezone.utc) > _utc_aware(verification.expires_at):
        db.delete(verification)
        db.commit()
        raise HTTPException(status_code=400, detail={"code": "TOKEN_EXPIRED", "message": "Verification token has expired."})
    user = db.query(User).filter(User.id == verification.user_id).first()
    if user is None or user.email.lower() != verification.email.lower():
        db.delete(verification)
        db.commit()
        raise HTTPException(status_code=400, detail={"code": "ACCOUNT_CHANGED", "message": "The account email changed. Request a new verification link."})
    user.email_verified = True
    verification.verified_at = datetime.now(timezone.utc)
    db.delete(verification)
    db.commit()

@router.post("/verify-email")
def verify_email(payload: VerifyEmailRequest, db: Session = Depends(get_db)):
    """Verify an email address using a single-use hashed token."""
    _consume_email_verification(payload.token, db)
    return {"code": "EMAIL_VERIFIED", "message": "Email address verified successfully."}


@router.get("/verify-email/confirm", response_class=HTMLResponse)
def confirm_email_from_link(token: str, db: Session = Depends(get_db)):
    """Consume a one-time email link sent by the configured delivery provider."""
    try:
        _consume_email_verification(token, db)
    except HTTPException as exc:
        message = "This verification link is invalid or has expired. Sign in and request a new link."
        status_code = exc.status_code
        return HTMLResponse(
            f"<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>FreightPilot verification</title></head><body style='font-family:system-ui;max-width:36rem;margin:12vh auto;padding:1rem;color:#182334'><h1>Email verification was not completed</h1><p>{message}</p></body></html>",
            status_code=status_code, headers={"Cache-Control": "no-store", "Referrer-Policy": "no-referrer"},
        )
    return HTMLResponse(
        "<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>FreightPilot verification</title></head><body style='font-family:system-ui;max-width:36rem;margin:12vh auto;padding:1rem;color:#182334'><h1>Email verified</h1><p>Your FreightPilot AI email address has been verified. You can return to the application and sign in.</p></body></html>",
        headers={"Cache-Control": "no-store", "Referrer-Policy": "no-referrer"},
    )


# ================== Phone Verification Endpoints ==================

@router.patch("/me/phone")
def update_my_phone(payload: SetPhoneRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Bind an E.164 phone number to the current account before SMS verification."""
    if user.phone_verified and user.phone_number != payload.phone_number:
        raise HTTPException(status_code=409, detail={"code": "PHONE_CHANGE_REQUIRES_SUPPORT", "message": "A verified phone number cannot be changed through self-service."})
    user.phone_number = payload.phone_number
    user.phone_verified = False
    db.query(PhoneVerification).filter(PhoneVerification.user_id == user.id, PhoneVerification.verified_at.is_(None)).delete(synchronize_session=False)
    db.commit()
    return {"code": "PHONE_UPDATED", "message": "Phone number updated. Request verification to confirm ownership."}


@router.put("/me/phone", response_model=UserResponse)
def set_account_phone(payload: SetPhoneRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Set or replace an unverified account phone number before sending its OTP."""
    requested = payload.phone_number.strip()
    if user.phone_verified and user.phone_number == requested:
        return user
    if user.phone_verified and user.phone_number != requested:
        raise HTTPException(status_code=403, detail={
            "code": "VERIFIED_PHONE_CHANGE_REQUIRES_SUPPORT",
            "message": "A verified phone number cannot be changed from this screen. Contact support to update it securely.",
        })
    duplicate = db.query(User).filter(
        User.phone_number == requested,
        User.id != user.id,
        User.is_active.is_(True),
    ).first()
    if duplicate:
        raise HTTPException(status_code=409, detail={
            "code": "PHONE_NUMBER_IN_USE",
            "message": "This phone number is already linked to another account.",
        })
    user.phone_number = requested
    user.phone_verified = False
    for pending in db.query(PhoneVerification).filter(
        PhoneVerification.user_id == user.id,
        PhoneVerification.verified_at.is_(None),
    ).all():
        db.delete(pending)
    if user.buyer_profile:
        user.buyer_profile.phone_number = requested
    if user.seller_profile:
        user.seller_profile.contact_phone = requested
    db.commit()
    db.refresh(user)
    return user


@router.post("/send-phone-verification")
def send_phone_verification(payload: PhoneVerificationRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Send OTP only to the phone number already bound to the authenticated account."""
    if user.phone_verified:
        raise HTTPException(status_code=400, detail={"code": "PHONE_ALREADY_VERIFIED", "message": "Phone number is already verified."})
    requested = payload.phone_number.strip()
    if not user.phone_number or requested != user.phone_number:
        raise HTTPException(status_code=422, detail={"code": "PHONE_NUMBER_MISMATCH", "message": "The phone number must match the number on your account. Update your profile before requesting verification."})
    existing = db.query(PhoneVerification).filter(
        PhoneVerification.user_id == user.id, PhoneVerification.verified_at.is_(None),
    ).order_by(PhoneVerification.created_at.desc()).first()
    if existing and datetime.now(timezone.utc) - _utc_aware(existing.created_at) < timedelta(minutes=2):
        raise HTTPException(status_code=429, detail={"code": "VERIFICATION_COOLDOWN", "message": "Please wait before requesting another OTP."})
    if existing:
        db.delete(existing)
        db.flush()
    otp = _generate_otp()
    verification = PhoneVerification(
        user_id=user.id, phone_number=user.phone_number, otp_hash=hash_otp(otp),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
    )
    db.add(verification)
    try:
        send_phone_otp(user.phone_number, otp)
    except DeliveryNotConfigured as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail={"code": "SMS_DELIVERY_NOT_CONFIGURED", "message": str(exc)})
    except Exception:
        db.rollback()
        raise HTTPException(status_code=502, detail={"code": "SMS_DELIVERY_FAILED", "message": "Verification SMS could not be delivered. Please retry later."})
    db.commit()
    return {"code": "OTP_SENT", "message": "OTP sent to your registered phone number."}


@router.post("/verify-phone")
def verify_phone(payload: VerifyPhoneRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Verify phone number using the OTP."""
    verification = db.query(PhoneVerification).filter(
        PhoneVerification.user_id == user.id,
        PhoneVerification.verified_at.is_(None),
    ).order_by(PhoneVerification.created_at.desc()).first()

    if not verification or verification.phone_number != user.phone_number or payload.phone_number.strip() != user.phone_number:
        raise HTTPException(status_code=400, detail={
            "code": "INVALID_REQUEST",
            "message": "No pending verification found.",
        })

    if datetime.now(timezone.utc) > _utc_aware(verification.expires_at):
        db.delete(verification)
        db.commit()
        raise HTTPException(status_code=400, detail={"code": "OTP_EXPIRED", "message": "OTP has expired."})

    if verification.attempts >= 5:
        db.delete(verification)
        db.commit()
        raise HTTPException(status_code=400, detail={"code": "MAX_ATTEMPTS_EXCEEDED", "message": "Max attempts exceeded."})

    if not verify_otp(payload.otp, verification.otp_hash):
        verification.attempts += 1
        verification.last_attempt_at = datetime.now(timezone.utc)
        db.commit()
        raise HTTPException(status_code=400, detail={"code": "INVALID_OTP", "message": "Invalid OTP."})

    user.phone_verified = True
    user.phone_number = verification.phone_number
    verification.verified_at = datetime.now(timezone.utc)

    db.commit()

    return {"code": "PHONE_VERIFIED", "message": "Phone number verified successfully."}


# ================== Firebase Phone Authentication ==================

class FirebasePhoneVerifyRequest(BaseModel):
    """Request to verify a Firebase phone authentication ID token."""
    id_token: str = Field(..., min_length=50, max_length=10000)
    phone_number: str = Field(..., min_length=9, max_length=16, pattern=r"^\+[1-9]\d{7,14}$")


@router.post("/firebase/verify-phone", response_model=TokenResponse)
async def verify_firebase_phone(payload: FirebasePhoneVerifyRequest, db: Session = Depends(get_db)):
    """Verify a Firebase Phone Authentication ID token and link to user account.

    The frontend uses Firebase Client SDK to send OTP and get ID token.
    Backend verifies the token and links the phone number to the authenticated user.
    """
    # Verify Firebase ID token
    try:
        claims = await verify_firebase_phone_token(payload.id_token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail={"code": "INVALID_FIREBASE_TOKEN", "message": str(exc)})

    # Ensure the phone number matches
    if claims['phone_number'] != payload.phone_number.strip():
        raise HTTPException(status_code=400, detail={"code": "PHONE_NUMBER_MISMATCH", "message": "Phone number does not match token."})

    # Find or create user
    user = db.query(User).filter(User.phone_number == claims['phone_number'], User.is_active.is_(True)).first()

    if user:
        # Update existing user
        if not user.phone_verified:
            user.phone_verified = True
            db.commit()
            db.refresh(user)
    else:
        # Create new user with phone verification
        # We need an email - if not in claims, we can't create a full account yet
        if not claims.get('email'):
            raise HTTPException(status_code=422, detail={
                "code": "EMAIL_REQUIRED",
                "message": "Email is required to create account. Please sign up with email first."
            })

        try:
            email = normalize_email(claims['email'])
        except ValueError:
            raise HTTPException(status_code=422, detail={"code": "INVALID_EMAIL", "message": "Invalid email from Firebase token."})

        # Check if email already exists
        existing_user = db.query(User).filter(func.lower(User.email) == email).first()
        if existing_user:
            if not existing_user.is_active:
                raise HTTPException(status_code=403, detail={"code": "ACCOUNT_UNAVAILABLE", "message": "This account is unavailable."})
            # Link phone to existing account
            existing_user.phone_number = claims['phone_number']
            existing_user.phone_verified = True
            db.commit()
            db.refresh(existing_user)
            user = existing_user
        else:
            # Create new user
            user = User(
                email=email,
                password_hash=hash_password(secrets.token_urlsafe(48)),  # Random password, login via phone
                role=BUYER,
                is_active=True,
                email_verified=claims.get('email_verified', False),
                phone_verified=True,
                phone_number=claims['phone_number'],
            )
            db.add(user)
            db.flush()
            db.add(BuyerProfile(user_id=user.id, default_currency="USD"))
            db.commit()
            db.refresh(user)

    return _token_response(user, db, not user.email_verified, False)


@router.post("/firebase/link-phone", response_model=UserResponse)
async def link_firebase_phone(payload: FirebasePhoneVerifyRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Link a verified Firebase phone number to the current authenticated user."""
    # Verify Firebase ID token
    try:
        claims = await verify_firebase_phone_token(payload.id_token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail={"code": "INVALID_FIREBASE_TOKEN", "message": str(exc)})

    # Ensure the phone number matches
    if claims['phone_number'] != payload.phone_number.strip():
        raise HTTPException(status_code=400, detail={"code": "PHONE_NUMBER_MISMATCH", "message": "Phone number does not match token."})

    # Check if phone is already linked to another account
    existing = db.query(User).filter(
        User.phone_number == claims['phone_number'],
        User.id != user.id,
        User.is_active.is_(True),
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail={"code": "PHONE_NUMBER_IN_USE", "message": "This phone number is already linked to another account."})

    # Update user's phone
    user.phone_number = claims['phone_number']
    user.phone_verified = True

    # Also update profile phone numbers
    if user.buyer_profile:
        user.buyer_profile.phone_number = claims['phone_number']
    if user.seller_profile:
        user.seller_profile.contact_phone = claims['phone_number']

    db.commit()
    db.refresh(user)

    return user


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


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., min_length=50, max_length=5000)


@router.post("/refresh", response_model=TokenResponse)
def refresh_access_token(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Refresh an access token using a valid refresh token."""
    # Decode and validate refresh token
    refresh_payload = decode_refresh_token(payload.refresh_token)
    user_id = refresh_payload["sub"]

    user = db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()
    if not user:
        raise HTTPException(status_code=401, detail={
            "code": "USER_INACTIVE", "message": "The account is unavailable.",
        })

    # Issue new access token
    return _token_response(user, db, not user.email_verified, not user.phone_verified)


@router.post("/logout")
def logout():
    """Logout endpoint. Client discards the tokens."""
    return {"code": "LOGGED_OUT", "message": "Logged out successfully."}


# ================== Password Reset Endpoints ==================

# Rate limiting: track forgot password requests per IP/email
_forgot_password_requests: dict[str, list[datetime]] = {}
_FORGOT_PASSWORD_WINDOW = timedelta(hours=1)
_FORGOT_PASSWORD_MAX_REQUESTS = 3


def _check_forgot_password_rate_limit(identifier: str) -> None:
    """Check rate limit for forgot password requests."""
    now = datetime.now(timezone.utc)
    window_start = now - _FORGOT_PASSWORD_WINDOW
    if identifier not in _forgot_password_requests:
        _forgot_password_requests[identifier] = []
    # Remove old entries
    _forgot_password_requests[identifier] = [
        t for t in _forgot_password_requests[identifier] if t > window_start
    ]
    if len(_forgot_password_requests[identifier]) >= _FORGOT_PASSWORD_MAX_REQUESTS:
        raise HTTPException(status_code=429, detail={
            "code": "RATE_LIMIT_EXCEEDED",
            "message": "Too many password reset requests. Please try again later.",
        })


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Request a password reset email. Does not reveal if email exists."""
    email = normalize_email(payload.email)
    identifier = f"forgot:{email}"
    _check_forgot_password_rate_limit(identifier)

    user = db.query(User).filter(User.email == email, User.is_active.is_(True), User.is_deleted.is_(False)).first()

    # Always return success to prevent email enumeration
    if not user:
        return {"code": "RESET_EMAIL_SENT", "message": "If an account exists for this email, a password reset link has been sent."}

    # Invalidate any existing unused reset tokens for this user
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used_at.is_(None),
    ).update({PasswordResetToken.used_at: datetime.now(timezone.utc)})

    # Create new reset token
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()

    reset_token = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    db.add(reset_token)

    # Send reset email
    try:
        # Use the existing send_verification_email but with reset URL
        from app.services.verification_delivery import send_verification_email
        # We need a reset password email - let's create a simple inline one
        reset_url = f"{settings.FRONTEND_URL or 'http://localhost:5173'}/reset-password?token={token}"

        import httpx
        if settings.RESEND_API_KEY:
            async def send_reset_email():
                async with httpx.AsyncClient() as client:
                    await client.post(
                        "https://api.resend.com/emails",
                        headers={
                            "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "from": settings.RESEND_FROM_EMAIL or "FreightPilot <noreply@freightpilot.ai>",
                            "to": [email],
                            "subject": "Reset your FreightPilot AI password",
                            "html": f"""
                                <div style="font-family:system-ui;max-width:600px;margin:0 auto;padding:20px;color:#182334">
                                    <h1 style="color:#1a3c5e">Reset your password</h1>
                                    <p>You requested a password reset for your FreightPilot AI account.</p>
                                    <p><a href="{reset_url}" style="background:#1a3c5e;color:white;padding:12px 24px;text-decoration:none;border-radius:6px;display:inline-block">Reset Password</a></p>
                                    <p style="color:#666;font-size:14px">This link expires in 1 hour. If you didn't request this, please ignore this email.</p>
                                    <hr style="border:none;border-top:1px solid #e0e0e0;margin:20px 0">
                                    <p style="color:#999;font-size:12px">FreightPilot AI - Freight Management Platform</p>
                                </div>
                            """,
                        },
                        timeout=10.0,
                    )
            import asyncio
            asyncio.run(send_reset_email())
        else:
            logger.warning("Resend not configured; password reset email not sent")
    except Exception as exc:
        logger.error("Failed to send password reset email: %s", exc)
        # Don't fail the request - we already created the token

    _forgot_password_requests[identifier].append(datetime.now(timezone.utc))
    db.commit()

    return {"code": "RESET_EMAIL_SENT", "message": "If an account exists for this email, a password reset link has been sent."}


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset password using a valid token."""
    token_hash = hashlib.sha256(payload.token.encode("utf-8")).hexdigest()

    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token_hash == token_hash,
        PasswordResetToken.used_at.is_(None),
    ).first()

    if not reset_token:
        raise HTTPException(status_code=400, detail={
            "code": "INVALID_TOKEN", "message": "Invalid or expired reset token."
        })

    if datetime.now(timezone.utc) > reset_token.expires_at:
        db.delete(reset_token)
        db.commit()
        raise HTTPException(status_code=400, detail={
            "code": "TOKEN_EXPIRED", "message": "Reset token has expired. Please request a new one."
        })

    user = db.query(User).filter(User.id == reset_token.user_id, User.is_active.is_(True)).first()
    if not user:
        raise HTTPException(status_code=400, detail={
            "code": "USER_NOT_FOUND", "message": "User no longer exists."
        })

    # Hash new password
    new_password_hash = hash_password(payload.password)
    user.password_hash = new_password_hash

    # Mark token as used
    reset_token.used_at = datetime.now(timezone.utc)

    # Invalidate all other unused tokens for this user
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used_at.is_(None),
    ).update({PasswordResetToken.used_at: datetime.now(timezone.utc)})

    db.commit()

    return {"code": "PASSWORD_RESET", "message": "Password has been reset successfully. You can now sign in with your new password."}


# ================== Account Deletion Endpoint ==================

@router.delete("/me")
def delete_account(payload: DeleteAccountRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Soft delete the current user's account. Requires password confirmation."""
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail={
            "code": "INVALID_PASSWORD", "message": "Incorrect password. Account deletion requires password confirmation."
        })

    # Soft delete: mark user as deleted
    user.is_deleted = True
    user.deleted_at = datetime.now(timezone.utc)
    user.deletion_reason = payload.reason
    user.is_active = False
    user.email_verified = False
    user.phone_verified = False
    # Keep email for audit but mark as deleted
    user.email = f"deleted_{user.id}_{user.email}"

    # Clear refresh tokens would happen on next login attempt (user is inactive)

    db.commit()

    return {"code": "ACCOUNT_DELETED", "message": "Your account has been deleted. You can contact support within 30 days to restore it."}