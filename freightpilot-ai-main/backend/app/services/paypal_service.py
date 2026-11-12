"""PayPal REST integration. Secrets and all capture operations stay server-side."""

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import logging
import threading
import time
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_TOKEN_LOCK = threading.Lock()
_TOKEN_VALUE: str | None = None
_TOKEN_EXPIRES_AT = 0.0


class PayPalServiceError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 502):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def get_paypal_api_base() -> str:
    environment = settings.PAYPAL_ENV.lower().strip()
    if settings.DEMO_MODE and environment != "sandbox":
        raise PayPalServiceError("PAYPAL_ENVIRONMENT_INVALID", "Demo payments must use PayPal Sandbox.", 503)
    if environment == "sandbox":
        return "https://api-m.sandbox.paypal.com"
    if environment == "live" and not settings.DEMO_MODE:
        return "https://api-m.paypal.com"
    raise PayPalServiceError("PAYPAL_ENVIRONMENT_INVALID", "PAYPAL_ENV must be sandbox or live.", 503)


def _credentials() -> tuple[str, str]:
    client_id, secret = settings.PAYPAL_CLIENT_ID.strip(), settings.PAYPAL_CLIENT_SECRET.strip()
    if not client_id or not secret or client_id.startswith("replace_") or secret.startswith("replace_"):
        raise PayPalServiceError(
            "PAYPAL_CONFIG_MISSING",
            "Configure PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET in backend/.env.",
            503,
        )
    return client_id, secret


def get_access_token(force_refresh: bool = False) -> str:
    """Obtain and briefly cache the PayPal OAuth token to avoid an auth call per API request."""
    global _TOKEN_VALUE, _TOKEN_EXPIRES_AT
    now = time.monotonic()
    with _TOKEN_LOCK:
        if not force_refresh and _TOKEN_VALUE and now < _TOKEN_EXPIRES_AT - 30:
            return _TOKEN_VALUE
        client_id, secret = _credentials()
        try:
            response = httpx.post(
                f"{get_paypal_api_base()}/v1/oauth2/token",
                auth=(client_id, secret),
                data={"grant_type": "client_credentials"},
                headers={"Accept": "application/json", "Accept-Language": "en_US"},
                timeout=settings.PAYPAL_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            data = response.json()
            token = data.get("access_token")
            if not token:
                raise PayPalServiceError("PAYPAL_AUTH_FAILED", "PayPal did not return an access token.")
            _TOKEN_VALUE = token
            _TOKEN_EXPIRES_AT = now + int(data.get("expires_in", 300))
            return token
        except PayPalServiceError:
            raise
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("PayPal OAuth request failed: %s", type(exc).__name__)
            raise PayPalServiceError("PAYPAL_AUTH_FAILED", "Could not authenticate with PayPal.") from exc


def _request(method: str, path: str, *, json_body: dict | None = None,
             request_id: str | None = None) -> dict[str, Any]:
    token = get_access_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }
    if request_id:
        headers["PayPal-Request-Id"] = request_id[:108]
    try:
        response = httpx.request(
            method,
            f"{get_paypal_api_base()}{path}",
            headers=headers,
            json=json_body,
            timeout=settings.PAYPAL_TIMEOUT_SECONDS,
        )
        if response.status_code == 401:
            # One bounded token refresh for an expired cached token.
            token = get_access_token(force_refresh=True)
            headers["Authorization"] = f"Bearer {token}"
            response = httpx.request(
                method, f"{get_paypal_api_base()}{path}", headers=headers,
                json=json_body, timeout=settings.PAYPAL_TIMEOUT_SECONDS,
            )
        if response.status_code not in (200, 201):
            logger.warning("PayPal API returned HTTP %s for %s", response.status_code, path)
            raise PayPalServiceError(
                "PAYPAL_PROVIDER_ERROR", "PayPal could not complete the requested operation.", 502,
            )
        return response.json() if response.content else {}
    except PayPalServiceError:
        raise
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning("PayPal request failed for %s: %s", path, type(exc).__name__)
        raise PayPalServiceError("PAYPAL_CONNECTION_ERROR", "Could not connect to PayPal.", 502) from exc


def create_paypal_order(amount: Decimal, currency: str, reference_id: str,
                        description: str, request_id: str | None = None) -> dict[str, Any]:
    """Create an order using a server-calculated amount. Never pass client amount here."""
    try:
        value = Decimal(str(amount)).quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError) as exc:
        raise PayPalServiceError("INVALID_PAYMENT_AMOUNT", "Payment amount is invalid.", 422) from exc
    if value <= 0:
        raise PayPalServiceError("INVALID_PAYMENT_AMOUNT", "Payment amount must be greater than zero.", 422)
    currency = currency.upper().strip()
    if len(currency) != 3 or not currency.isalpha():
        raise PayPalServiceError("INVALID_PAYMENT_CURRENCY", "Payment currency must be a valid 3-letter code.", 422)
    body = {
        "intent": "CAPTURE",
        "purchase_units": [{
            "reference_id": reference_id,
            "custom_id": reference_id,
            "description": description[:127],
            "amount": {"currency_code": currency, "value": f"{value:.2f}"},
        }],
        "payment_source": {"paypal": {"experience_context": {
            "shipping_preference": "NO_SHIPPING",
            "user_action": "PAY_NOW",
        }}},
    }
    return _request("POST", "/v2/checkout/orders", json_body=body, request_id=request_id)


def get_paypal_order_details(provider_order_id: str) -> dict[str, Any]:
    if not provider_order_id or len(provider_order_id) > 100:
        raise PayPalServiceError("INVALID_ORDER_ID", "PayPal order ID is invalid.", 422)
    return _request("GET", f"/v2/checkout/orders/{provider_order_id}")


def capture_paypal_order(provider_order_id: str, request_id: str | None = None) -> dict[str, Any]:
    if not provider_order_id or len(provider_order_id) > 100:
        raise PayPalServiceError("INVALID_ORDER_ID", "PayPal order ID is invalid.", 422)
    return _request(
        "POST", f"/v2/checkout/orders/{provider_order_id}/capture",
        json_body={}, request_id=request_id,
    )


def refund_paypal_capture(capture_id: str, request_id: str | None = None) -> dict[str, Any]:
    if not capture_id or len(capture_id) > 100:
        raise PayPalServiceError("INVALID_CAPTURE_ID", "PayPal capture ID is invalid.", 422)
    return _request(
        "POST", f"/v2/payments/captures/{capture_id}/refund",
        json_body={}, request_id=request_id,
    )


def verify_paypal_webhook(headers: dict[str, str], event: dict[str, Any]) -> bool:
    """Verify the PayPal webhook signature with PayPal's verification endpoint."""
    webhook_id = settings.PAYPAL_WEBHOOK_ID.strip()
    if not webhook_id:
        raise PayPalServiceError("PAYPAL_WEBHOOK_NOT_CONFIGURED", "PAYPAL_WEBHOOK_ID is not configured.", 503)
    required = {
        "transmission_id": headers.get("paypal-transmission-id"),
        "transmission_time": headers.get("paypal-transmission-time"),
        "cert_url": headers.get("paypal-cert-url"),
        "auth_algo": headers.get("paypal-auth-algo"),
        "transmission_sig": headers.get("paypal-transmission-sig"),
    }
    if not all(required.values()):
        return False
    body = {
        **required,
        "webhook_id": webhook_id,
        "webhook_event": event,
    }
    result = _request("POST", "/v1/notifications/verify-webhook-signature", json_body=body)
    return result.get("verification_status") == "SUCCESS"
