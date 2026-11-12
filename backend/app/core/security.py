"""Password hashing, JWT issuance and request-user dependencies."""

from datetime import datetime, timedelta, timezone
import re
import uuid

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.db.models import User
from app.db.session import get_db

_password_hasher = PasswordHasher(time_cost=2, memory_cost=19456, parallelism=1)
_bearer_scheme = HTTPBearer(auto_error=False)
_EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

# Token expiration settings
REFRESH_TOKEN_EXPIRE_DAYS = 30


def normalize_email(email: str) -> str:
    normalized = email.strip().lower()
    if len(normalized) > 254 or not _EMAIL_PATTERN.fullmatch(normalized):
        raise ValueError("Enter a valid email address.")
    return normalized


def hash_password(password: str) -> str:
    if len(password) < 10 or len(password) > 128:
        raise ValueError("Password must contain between 10 and 128 characters.")
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _password_hasher.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError, ValueError):
        return False


def hash_otp(otp: str) -> str:
    """Hash short-lived OTP material without applying the password minimum length rule."""
    return _password_hasher.hash(otp)


def verify_otp(otp: str, otp_hash: str) -> bool:
    try:
        return _password_hasher.verify(otp_hash, otp)
    except (VerifyMismatchError, VerificationError, ValueError):
        return False


def create_access_token(user: User) -> tuple[str, int]:
    expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user.id,
        "role": user.role,
        "iat": now,
        "exp": now + timedelta(seconds=expires_in),
        "iss": "freightpilot-ai",
        "jti": str(uuid.uuid4()),
        "typ": "access",
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, expires_in


def create_refresh_token(user: User) -> tuple[str, int]:
    """Create a long-lived refresh token for session persistence."""
    expires_in = REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user.id,
        "role": user.role,
        "iat": now,
        "exp": now + timedelta(seconds=expires_in),
        "iss": "freightpilot-ai",
        "jti": str(uuid.uuid4()),
        "typ": "refresh",
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, expires_in


def decode_refresh_token(token: str) -> dict:
    """Decode and validate a refresh token, returning the payload."""
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM], issuer="freightpilot-ai",
            options={"require": ["exp", "iat", "sub", "iss", "jti", "typ"]},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail={
            "code": "INVALID_REFRESH_TOKEN", "message": "The refresh token is invalid or expired.",
        }, headers={"WWW-Authenticate": "Bearer"})
    if payload.get("typ") != "refresh":
        raise HTTPException(status_code=401, detail={
            "code": "INVALID_TOKEN_TYPE", "message": "The supplied token cannot be used for session refresh.",
        }, headers={"WWW-Authenticate": "Bearer"})
    return payload


def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    token = credentials.credentials if credentials else None
    if not token:
        if settings.AUTH_REQUIRED:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={
                "code": "AUTHENTICATION_REQUIRED", "message": "A valid bearer token is required.",
            }, headers={"WWW-Authenticate": "Bearer"})
        return None
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM], issuer="freightpilot-ai",
            options={"require": ["exp", "iat", "sub", "iss", "jti", "typ"]},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail={
            "code": "INVALID_TOKEN", "message": "The access token is invalid or expired.",
        }, headers={"WWW-Authenticate": "Bearer"})
    if payload.get("typ") != "access":
        raise HTTPException(status_code=401, detail={
            "code": "INVALID_TOKEN_TYPE", "message": "The supplied token cannot be used for API access.",
        }, headers={"WWW-Authenticate": "Bearer"})
    user = db.query(User).filter(User.id == payload["sub"], User.is_active.is_(True)).first()
    if not user:
        raise HTTPException(status_code=401, detail={
            "code": "USER_INACTIVE", "message": "The account is unavailable.",
        })
    return user


def get_current_user(user: User | None = Depends(get_optional_current_user)) -> User:
    if user is None:
        raise HTTPException(status_code=401, detail={
            "code": "AUTHENTICATION_REQUIRED", "message": "Please sign in to continue.",
        }, headers={"WWW-Authenticate": "Bearer"})
    return user


def require_shipment_access(shipment, user: User | None) -> None:
    """Enforce tenant ownership; unowned rows are visible only in explicit local demo mode."""
    if user is not None and user.role == "ADMIN":
        return
    if user is None:
        if settings.AUTH_REQUIRED:
            raise HTTPException(status_code=401, detail={"code": "AUTHENTICATION_REQUIRED", "message": "Please sign in to continue."})
        if settings.DEMO_MODE and shipment.user_id is None:
            return
        raise HTTPException(status_code=404, detail={"code": "SHIPMENT_NOT_FOUND", "message": "Shipment not found."})
    if shipment.user_id == user.id:
        return
    if settings.DEMO_MODE and shipment.user_id is None:
        return
    raise HTTPException(status_code=404, detail={"code": "SHIPMENT_NOT_FOUND", "message": "Shipment not found."})


# Role-based authorization
def require_buyer(user: User = Depends(get_current_user)) -> User:
    """Require the current user to be a buyer."""
    if user.role != "BUYER":
        raise HTTPException(status_code=403, detail={
            "code": "NOT_A_BUYER",
            "message": "This action requires a buyer account.",
        })
    return user


def require_seller(user: User = Depends(get_current_user)) -> User:
    """Require the current user to be a seller."""
    if user.role != "SELLER":
        raise HTTPException(status_code=403, detail={
            "code": "NOT_A_SELLER",
            "message": "This action requires a seller account.",
        })
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    """Require the current user to be an admin."""
    if user.role != "ADMIN":
        raise HTTPException(status_code=403, detail={
            "code": "NOT_AN_ADMIN",
            "message": "This action requires an admin account.",
        })
    return user


def require_verified_email(user: User = Depends(get_current_user)) -> User:
    """Require the current user to have verified their email."""
    if not user.email_verified:
        raise HTTPException(status_code=403, detail={
            "code": "EMAIL_NOT_VERIFIED",
            "message": "Please verify your email address before accessing this resource.",
        })
    return user


def require_verified_phone(user: User = Depends(get_current_user)) -> User:
    """Require the current user to have verified their phone."""
    if not user.phone_verified:
        raise HTTPException(status_code=403, detail={
            "code": "PHONE_NOT_VERIFIED",
            "message": "Please verify your phone number before accessing this resource.",
        })
    return user


def require_full_verification(user: User = Depends(get_current_user)) -> User:
    """Require the current user to have verified both email and phone."""
    if not user.email_verified:
        raise HTTPException(status_code=403, detail={
            "code": "EMAIL_NOT_VERIFIED",
            "message": "Please verify your email address.",
        })
    if not user.phone_verified:
        raise HTTPException(status_code=403, detail={
            "code": "PHONE_NOT_VERIFIED",
            "message": "Please verify your phone number.",
        })
    return user


def require_verified_seller(user: User = Depends(require_seller), db: Session = Depends(get_db)) -> User:
    """Require an active seller profile approved by an administrator."""
    from app.db.models import SellerProfile
    profile = db.query(SellerProfile).filter(SellerProfile.user_id == user.id).first()
    if profile is None or profile.verification_status != "VERIFIED":
        raise HTTPException(status_code=403, detail={
            "code": "SELLER_NOT_VERIFIED",
            "message": "Seller verification must be approved before marketplace quoting or payouts.",
        })
    if settings.is_production and (not user.email_verified or not user.phone_verified):
        raise HTTPException(status_code=403, detail={
            "code": "SELLER_IDENTITY_NOT_VERIFIED",
            "message": "Verify the account email and phone before using marketplace seller operations.",
        })
    return user
