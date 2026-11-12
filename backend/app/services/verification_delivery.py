"""Transactional email/SMS delivery adapters. Never return verification secrets from API routes."""
import json
import logging
from urllib.parse import quote
import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class DeliveryNotConfigured(RuntimeError):
    pass


def send_verification_email(email: str, token: str) -> None:
    provider = settings.EMAIL_PROVIDER.lower()
    verification_url = f"{settings.API_PUBLIC_URL.rstrip('/')}/api/auth/verify-email/confirm?token={quote(token)}"
    subject = "Verify your FreightPilot AI email address"
    text_body = f"Verify your email address using this link: {verification_url}\nThis link expires in 24 hours."
    if provider == "console" and not settings.is_production:
        logger.info("DEV EMAIL VERIFICATION recipient=%s url=%s", email, verification_url)
        return
    if provider == "resend" and settings.RESEND_API_KEY:
        response = httpx.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {settings.RESEND_API_KEY}"},
            json={"from": settings.EMAIL_FROM, "to": [email], "subject": subject, "text": text_body},
            timeout=12.0,
        )
        response.raise_for_status()
        return
    raise DeliveryNotConfigured("Email delivery is not configured. Set EMAIL_PROVIDER=resend and RESEND_API_KEY.")


def send_phone_otp(phone_number: str, otp: str) -> None:
    """Send OTP via Firebase Phone Authentication.

    Note: With Firebase Phone Auth, the OTP is sent by Firebase Client SDK on the frontend.
    This function is a compatibility shim for the legacy SMS flow.
    In the Firebase flow, the frontend handles OTP sending/receiving via signInWithPhoneNumber.
    """
    provider = settings.SMS_PROVIDER.lower()

    if provider == "console" and not settings.is_production:
        logger.info("DEV SMS VERIFICATION recipient=%s otp=%s", phone_number, otp)
        return

    if provider == "firebase" and settings.FIREBASE_PROJECT_ID:
        # Firebase sends OTPs from the browser SDK. Returning success here would
        # falsely tell the user an SMS was sent when this backend has no SMS sender.
        raise DeliveryNotConfigured(
            "Firebase Phone Auth sends codes through the frontend SDK. Configure VITE_FIREBASE_* "
            "in the frontend and use the Firebase ID-token verification endpoint."
        )

    raise DeliveryNotConfigured("SMS delivery is not configured. Set SMS_PROVIDER=firebase with FIREBASE_PROJECT_ID and FIREBASE_SERVICE_ACCOUNT_JSON.")


async def verify_firebase_phone_token(id_token: str) -> dict:
    """Verify a Firebase ID token and return decoded claims.

    Validates: signature, expiry, issuer, audience, and project.
    Returns: dict with uid, phone_number, and other claims.
    """
    try:
        import firebase_admin
        from firebase_admin import auth, credentials

        # Initialize Firebase Admin SDK if not already initialized
        if not firebase_admin._apps:
            if settings.FIREBASE_SERVICE_ACCOUNT_JSON:
                cred = credentials.Certificate(json.loads(settings.FIREBASE_SERVICE_ACCOUNT_JSON))
            else:
                # Use default credentials (GOOGLE_APPLICATION_CREDENTIALS env var)
                cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred, {
                'projectId': settings.FIREBASE_PROJECT_ID,
            })

        # Verify the ID token
        decoded_token = auth.verify_id_token(id_token)

        # Validate token is for phone auth
        if 'phone_number' not in decoded_token:
            raise ValueError("Token does not contain phone_number claim")

        return {
            'uid': decoded_token['uid'],
            'phone_number': decoded_token['phone_number'],
            'email': decoded_token.get('email'),
            'email_verified': decoded_token.get('email_verified', False),
        }
    except Exception as e:
        logger.error("Firebase token verification failed: %s", type(e).__name__)
        raise ValueError(f"Invalid Firebase token: {str(e)}")