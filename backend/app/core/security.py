"""Password hashing, JWT issuance and request-user dependencies."""

from datetime import datetime, timedelta, timezone
import re

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


def create_access_token(user: User) -> tuple[str, int]:
    expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user.id,
        "role": user.role,
        "iat": now,
        "exp": now + timedelta(seconds=expires_in),
        "iss": "freightpilot-ai",
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, expires_in


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
            options={"require": ["exp", "iat", "sub", "iss"]},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail={
            "code": "INVALID_TOKEN", "message": "The access token is invalid or expired.",
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
    """Ensure a user can access a shipment; unowned demo rows remain demo-readable."""
    if user is None:
        return
    if shipment.user_id == user.id:
        return
    if settings.DEMO_MODE and shipment.user_id is None:
        return
    raise HTTPException(status_code=404, detail={
        "code": "SHIPMENT_NOT_FOUND", "message": "Shipment not found.",
    })
