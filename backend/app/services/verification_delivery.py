"""Transactional email/SMS delivery adapters. Never return verification secrets from API routes."""
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
    provider = settings.SMS_PROVIDER.lower()
    body = f"Your FreightPilot AI verification code is {otp}. It expires in 10 minutes."
    if provider == "console" and not settings.is_production:
        logger.info("DEV SMS VERIFICATION recipient=%s otp=%s", phone_number, otp)
        return
    if provider == "twilio" and settings.TWILIO_ACCOUNT_SID and settings.TWILIO_FROM_NUMBER:
        if settings.TWILIO_API_KEY_SID and settings.TWILIO_API_KEY_SECRET:
            auth = (settings.TWILIO_API_KEY_SID, settings.TWILIO_API_KEY_SECRET)
        elif not settings.is_production and settings.TWILIO_AUTH_TOKEN:
            # Local-only compatibility; production must use a scoped API key.
            auth = (settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        else:
            raise DeliveryNotConfigured("Twilio API key credentials are required. Create a scoped key in the Twilio Console.")
        response = httpx.post(
            f"https://api.twilio.com/2010-04-01/Accounts/{settings.TWILIO_ACCOUNT_SID}/Messages.json",
            auth=auth,
            data={"From": settings.TWILIO_FROM_NUMBER, "To": phone_number, "Body": body},
            timeout=12.0,
        )
        response.raise_for_status()
        return
    raise DeliveryNotConfigured("SMS delivery is not configured. Set SMS_PROVIDER=twilio and Twilio credentials.")
