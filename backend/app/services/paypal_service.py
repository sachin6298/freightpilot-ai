"""PayPal Sandbox REST API integration service with secure server-side amount calculation."""

import base64
import logging
import os
from decimal import Decimal
from typing import Any, Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

SANDBOX_API_BASE = "https://api-m.sandbox.paypal.com"


class PayPalServiceError(Exception):
    """Custom exception for PayPal integration errors."""

    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def get_paypal_api_base() -> str:
    """Get PayPal API base URL based on environment configuration."""
    return os.getenv("PAYPAL_API_BASE", SANDBOX_API_BASE)


def get_access_token() -> str:
    """Obtain OAuth2 access token from PayPal REST API using Client ID and Secret."""
    client_id = settings.PAYPAL_CLIENT_ID
    client_secret = settings.PAYPAL_CLIENT_SECRET

    if not client_id or not client_secret or client_id.startswith("replace_") or client_secret.startswith("replace_"):
        raise PayPalServiceError(
            code="PAYPAL_CONFIG_MISSING",
            message=(
                "PayPal Sandbox credentials are not configured. "
                "Please configure PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET in backend/.env "
                "per docs/PAYPAL_INTEGRATION.md and docs/ENV_SETUP.md."
            ),
            status_code=503,
        )

    auth_str = f"{client_id}:{client_secret}"
    b64_auth = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")

    url = f"{get_paypal_api_base()}/v1/oauth2/token"
    headers = {
        "Authorization": f"Basic {b64_auth}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {"grant_type": "client_credentials"}

    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.post(url, headers=headers, data=data)
            if response.status_code != 200:
                logger.error(f"PayPal token acquisition failed: {response.status_code} - {response.text}")
                raise PayPalServiceError(
                    code="PAYPAL_AUTH_FAILED",
                    message="Failed to authenticate with PayPal Sandbox API.",
                    status_code=502,
                )
            token_data = response.json()
            access_token = token_data.get("access_token")
            if not access_token:
                raise PayPalServiceError(
                    code="PAYPAL_AUTH_FAILED",
                    message="PayPal token response did not contain an access token.",
                    status_code=502,
                )
            return access_token
    except httpx.RequestError as e:
        logger.error(f"PayPal connection error during auth: {e}")
        raise PayPalServiceError(
            code="PAYPAL_CONNECTION_ERROR",
            message="Could not connect to PayPal Sandbox API.",
            status_code=502,
        )


def create_paypal_order(
    amount: Decimal,
    currency: str,
    reference_id: str,
    description: str,
) -> dict[str, Any]:
    """Create a PayPal order using server-owned authoritative amount and reference."""
    access_token = get_access_token()
    url = f"{get_paypal_api_base()}/v2/checkout/orders"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }

    payload = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "reference_id": reference_id,
                "description": description,
                "amount": {
                    "currency_code": currency,
                    "value": f"{amount:.2f}",
                },
            }
        ],
    }

    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.post(url, headers=headers, json=payload)
            if response.status_code not in (200, 201):
                logger.error(f"PayPal create order failed: {response.status_code} - {response.text}")
                raise PayPalServiceError(
                    code="PAYPAL_ORDER_CREATION_FAILED",
                    message=f"PayPal order creation failed: {response.text}",
                    status_code=502,
                )
            return response.json()
    except httpx.RequestError as e:
        logger.error(f"PayPal connection error during create order: {e}")
        raise PayPalServiceError(
            code="PAYPAL_CONNECTION_ERROR",
            message="Could not connect to PayPal Sandbox API for order creation.",
            status_code=502,
        )


def capture_paypal_order(provider_order_id: str) -> dict[str, Any]:
    """Capture an approved PayPal order by its provider order ID."""
    access_token = get_access_token()
    url = f"{get_paypal_api_base()}/v2/checkout/orders/{provider_order_id}/capture"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }

    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.post(url, headers=headers)
            if response.status_code not in (200, 201):
                logger.error(f"PayPal capture failed: {response.status_code} - {response.text}")
                raise PayPalServiceError(
                    code="PAYPAL_CAPTURE_FAILED",
                    message=f"PayPal order capture failed: {response.text}",
                    status_code=502,
                )
            return response.json()
    except httpx.RequestError as e:
        logger.error(f"PayPal connection error during capture: {e}")
        raise PayPalServiceError(
            code="PAYPAL_CONNECTION_ERROR",
            message="Could not connect to PayPal Sandbox API for order capture.",
            status_code=502,
        )


def get_paypal_order_details(provider_order_id: str) -> dict[str, Any]:
    """Retrieve order details from PayPal for verification and reconciliation."""
    access_token = get_access_token()
    url = f"{get_paypal_api_base()}/v2/checkout/orders/{provider_order_id}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.get(url, headers=headers)
            if response.status_code != 200:
                logger.error(f"PayPal get order failed: {response.status_code} - {response.text}")
                raise PayPalServiceError(
                    code="PAYPAL_ORDER_FETCH_FAILED",
                    message="Failed to retrieve order details from PayPal.",
                    status_code=502,
                )
            return response.json()
    except httpx.RequestError as e:
        logger.error(f"PayPal connection error during get order: {e}")
        raise PayPalServiceError(
            code="PAYPAL_CONNECTION_ERROR",
            message="Could not connect to PayPal Sandbox API.",
            status_code=502,
        )
