import pytest

from app.config import settings
from app.services.verification_delivery import DeliveryNotConfigured, send_phone_otp


def test_firebase_sms_backend_does_not_claim_it_sent_an_otp(monkeypatch):
    monkeypatch.setattr(settings, "SMS_PROVIDER", "firebase")
    monkeypatch.setattr(settings, "FIREBASE_PROJECT_ID", "freightpilot-test")
    with pytest.raises(DeliveryNotConfigured, match="frontend SDK"):
        send_phone_otp("+15551234567", "123456")
