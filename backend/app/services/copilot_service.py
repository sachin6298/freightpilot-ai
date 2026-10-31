
"""Copilot service for AI-assisted quote analysis and deterministic fallback."""

import json
import logging
from decimal import Decimal
from typing import Any, Optional

import httpx

from app.config import settings
from app.db.models import Quote, Shipment
from app.schemas import CopilotResponse
from app.services.rate_estimate_service import calculate_shipment_estimate
from app.services.risk_service import assess_quote_risk

logger = logging.getLogger(__name__)

DISCLAIMER = "Human review required; outputs are estimates."


def generate_fallback_copilot_response(
    shipment: Shipment,
    quotes: list[Quote],
    peer_quotes: list[Quote],
    benchmark=None,
) -> dict[str, Any]:
    """Generate a deterministic quote comparison grounded in available data."""

    if not quotes:
        return {
            "summary": "No quotes provided for comparison.",
            "comparison": [],
            "missing_information": ["No quote data available."],
            "next_questions": [
                "Please request quotes from carriers for this shipment."
            ],
            "disclaimer": DISCLAIMER,
        }

    benchmark = benchmark or calculate_shipment_estimate(
        shipment, peer_quotes
    )

    assessments = {
        q.id: assess_quote_risk(
            q, shipment, peer_quotes, benchmark=benchmark
        )
        for q in quotes
    }

    lowest_quote = min(
        quotes, key=lambda q: Decimal(str(q.total_amount))
    )
    highest_quote = max(
        quotes, key=lambda q: Decimal(str(q.total_amount))
    )

    fastest_transit_days = min(
        (
            q.transit_days
            for q in quotes
            if q.transit_days is not None
        ),
        default=None,
    )

    low_amt = Decimal(str(lowest_quote.total_amount))
    high_amt = Decimal(str(highest_quote.total_amount))
    currency = shipment.currency

    if len(quotes) == 1:
        q = quotes[0]
        summary = (
            f"Evaluated 1 quote from {q.provider_label} for "
            f"{shipment.cargo_type} ({shipment.quantity_tonnes} MT) "
            f"from {shipment.origin} to {shipment.destination}. "
            f"Total price is {q.total_amount} {q.currency} with "
            f"an estimated transit of "
            f"{q.transit_days or 'unspecified'} days."
        )
    else:
        summary = (
            f"Compared {len(quotes)} freight quotes for shipping "
            f"{shipment.quantity_tonnes} MT of {shipment.cargo_type} "
            f"from {shipment.origin} to {shipment.destination}. "
            f"Quote totals range from {low_amt} {currency} "
            f"({lowest_quote.provider_label}) to "
            f"{high_amt} {currency} ({highest_quote.provider_label}). "
            "Key trade-offs center around price competitiveness, "
            "transit time, fee transparency, and advance terms."
        )

    comparison_details = []
    all_missing_info = set()
    all_next_questions = set()

    for q in quotes:
        risk_info = assessments[q.id]
        flags = risk_info.get("flags", [])

        advantages = []
        concerns = []

        if q.id == lowest_quote.id and len(quotes) > 1:
            advantages.append(
                f"Lowest total cost ({q.total_amount} {q.currency})."
            )

        if q.transit_days is not None:
            if q.transit_days == fastest_transit_days:
                advantages.append(
                    f"Fastest estimated transit time ({q.transit_days} days)."
                )
            else:
                advantages.append(
                    f"Declared transit duration of {q.transit_days} days."
                )

        if (
            q.surcharge_amount > 0
            and q.terms
            and q.terms.get("itemized")
        ):
            advantages.append(
                "Provides itemized fee structure for ocean freight "
                "and surcharges."
            )

        if not flags:
            advantages.append(
                "No automated risk flags detected; quote matches "
                "standard benchmark parameters."
            )

        for flag in flags:
            concerns.append(
                f"[{flag['severity']}] {flag['title']}: "
                f"{flag['evidence']}"
            )

            if flag.get("recommended_check"):
                all_next_questions.add(
                    f"{q.provider_label}: {flag['recommended_check']}"
                )

        if q.transit_days is None:
            all_missing_info.add(
                f"Transit duration unspecified for "
                f"{q.provider_label} ({q.reference})."
            )
            all_next_questions.add(
                f"Ask {q.provider_label} for estimated transit "
                "days and vessel schedule."
            )

        if q.validity_until is None:
            all_missing_info.add(
                f"Quote validity expiration date missing "
                f"for {q.provider_label}."
            )
            all_next_questions.add(
                f"Ask {q.provider_label} until when this quoted "
                "rate remains valid."
            )

        if q.vessel_class is None:
            all_missing_info.add(
                f"Vessel class/specification not declared "
                f"for {q.provider_label}."
            )

        if (
            q.surcharge_amount == 0
            and q.terms
            and not q.terms.get("itemized")
        ):
            all_missing_info.add(
                f"Itemized surcharge breakdown (BAF, THCs) "
                f"omitted for {q.provider_label}."
            )

        if q.terms and q.terms.get("advance_pct"):
            all_next_questions.add(
                f"Confirm payment milestone schedule and security "
                f"with {q.provider_label} for the requested "
                f"{q.terms['advance_pct']}% advance deposit."
            )

        comparison_details.append(
            {
                "quote_id": q.id,
                "advantages": advantages or [
                    "Valid freight quote structure."
                ],
                "concerns": concerns or [
                    "No critical risk concerns identified."
                ],
            }
        )

    if not all_next_questions:
        all_next_questions.update(
            [
                "Confirm whether demurrage and detention free days "
                "are included.",
                "Verify whether fuel adjustment factor (BAF) "
                "is subject to floating adjustments.",
            ]
        )

    if not all_missing_info:
        all_missing_info.add(
            "None identified; all core quote fields are populated."
        )

    return {
        "summary": summary,
        "comparison": comparison_details,
        "missing_information": sorted(all_missing_info),
        "next_questions": sorted(all_next_questions),
        "disclaimer": DISCLAIMER,
    }


def _build_ai_prompt(
    shipment: Shipment,
    quotes: list[Quote],
    assessments: dict,
) -> dict[str, Any]:
    """Build structured shipment and quote context for the AI provider."""

    quotes_data = []

    for q in quotes:
        quotes_data.append(
            {
                "quote_id": q.id,
                "carrier_label": q.provider_label,
                "reference": q.reference,
                "base_amount": float(q.base_amount),
                "surcharge_amount": float(q.surcharge_amount),
                "total_amount": float(q.total_amount),
                "currency": q.currency,
                "transit_days": q.transit_days,
                "validity_until": (
                    q.validity_until.isoformat()
                    if q.validity_until
                    else None
                ),
                "vessel_class": q.vessel_class,
                "cargo_capacity_tonnes": (
                    float(q.cargo_capacity_tonnes)
                    if q.cargo_capacity_tonnes
                    else None
                ),
                "terms": q.terms,
                "risk_assessment": assessments[q.id],
            }
        )

    return {
        "shipment": {
            "id": shipment.id,
            "cargo_type": shipment.cargo_type,
            "quantity_tonnes": float(shipment.quantity_tonnes),
            "origin": shipment.origin,
            "destination": shipment.destination,
            "ready_date": shipment.ready_date.isoformat(),
            "required_arrival_date": (
                shipment.required_arrival_date.isoformat()
                if shipment.required_arrival_date
                else None
            ),
            "currency": shipment.currency,
        },
        "quotes": quotes_data,
    }


def _build_system_instruction() -> str:
    """Return strict grounding instructions for the AI model."""

    return (
        "You are FreightPilot AI, an expert freight procurement assistant.\n"
        "Analyze the provided shipment and quotes data objectively.\n"
        "STRICT GROUNDING RULES:\n"
        "1. Ground all explanations exclusively in the provided "
        "shipment and quote facts.\n"
        "2. Do NOT invent carrier facts, prices, sanctions status, "
        "or market data.\n"
        "3. Do NOT authorize, create, or mention payment execution "
        "capabilities.\n"
        "4. Highlight differences in cost, transit time, risk flags, "
        "missing data, and trade-offs.\n"
        "5. Output strictly valid JSON matching this schema:\n"
        "{\n"
        '  "summary": "Brief overall narrative of trade-offs",\n'
        '  "comparison": [\n'
        '    {"quote_id": "string", '
        '"advantages": ["string"], "concerns": ["string"]}\n'
        "  ],\n"
        '  "missing_information": ["string"],\n'
        '  "next_questions": ["string"],\n'
        '  "disclaimer": "Human review required; outputs are estimates."\n'
        "}"
    )


def _call_gemini(
    model: str,
    prompt_context: dict[str, Any],
    system_instruction: str,
) -> dict[str, Any]:
    """Call Gemini securely using an HTTP header for API authentication."""

    if not settings.AI_API_KEY:
        raise ValueError("Gemini API key is not configured.")

    url = (
        "https://generativelanguage.googleapis.com/v1beta/"
        f"models/{model}:generateContent"
    )

    headers = {
        "x-goog-api-key": settings.AI_API_KEY,
        "Content-Type": "application/json",
    }

    payload = {
        "system_instruction": {
            "parts": [{"text": system_instruction}]
        },
        "contents": [
            {
                "parts": [
                    {"text": json.dumps(prompt_context)}
                ]
            }
        ],
        "generationConfig": {
            "response_mime_type": "application/json",
            "temperature": 0.2,
        },
    }

    with httpx.Client(timeout=20.0) as client:
        response = client.post(
            url,
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

    candidates = data.get("candidates", [])

    if not candidates:
        raise ValueError("Gemini returned no response candidates.")

    parts = candidates[0].get("content", {}).get("parts", [])
    response_text = next(
        (
            part["text"]
            for part in parts
            if isinstance(part, dict) and "text" in part
        ),
        None,
    )

    if not response_text:
        raise ValueError("Gemini returned an empty response.")

    parsed = json.loads(response_text)

    return CopilotResponse.model_validate(parsed).model_dump()


def _call_openai(
    model: str,
    prompt_context: dict[str, Any],
    system_instruction: str,
) -> dict[str, Any]:
    """Call OpenAI using server-side authentication."""

    if not settings.AI_API_KEY:
        raise ValueError("OpenAI API key is not configured.")

    url = "https://api.openai.com/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {settings.AI_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": system_instruction,
            },
            {
                "role": "user",
                "content": json.dumps(prompt_context),
            },
        ],
        "response_format": {
            "type": "json_object"
        },
        "temperature": 0.2,
    }

    with httpx.Client(timeout=20.0) as client:
        response = client.post(
            url,
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

    choices = data.get("choices", [])

    if not choices:
        raise ValueError("OpenAI returned no response choices.")

    response_text = (
        choices[0]
        .get("message", {})
        .get("content")
    )

    if not response_text:
        raise ValueError("OpenAI returned an empty response.")

    parsed = json.loads(response_text)

    return CopilotResponse.model_validate(parsed).model_dump()


def call_ai_provider(
    shipment: Shipment,
    quotes: list[Quote],
    peer_quotes: list[Quote],
    benchmark=None,
) -> Optional[dict[str, Any]]:
    """Call the configured AI provider with grounded shipment data."""

    provider = settings.AI_PROVIDER.lower().strip()

    if provider not in {"gemini", "openai"}:
        logger.warning(
            "Unsupported AI provider configured: %s",
            provider,
        )
        return None

    if not settings.AI_API_KEY:
        logger.warning("AI API key is not configured.")
        return None

    if provider == "gemini":
        model = (
            settings.AI_MODEL.strip()
            if settings.AI_MODEL
            else "gemini-2.5-flash"
        )
    else:
        model = (
            settings.AI_MODEL.strip()
            if settings.AI_MODEL
            else "gpt-4o-mini"
        )

    try:
        benchmark = benchmark or calculate_shipment_estimate(
            shipment, peer_quotes
        )

        assessments = {
            q.id: assess_quote_risk(
                q, shipment, peer_quotes, benchmark=benchmark
            )
            for q in quotes
        }

        prompt_context = _build_ai_prompt(
            shipment, quotes, assessments
        )

        system_instruction = _build_system_instruction()

        if provider == "gemini":
            return _call_gemini(
                model,
                prompt_context,
                system_instruction,
            )

        return _call_openai(
            model,
            prompt_context,
            system_instruction,
        )

    except Exception as exc:
        # Do not log exception messages or request URLs:
        # they may contain sensitive authentication information.
        logger.warning(
            "AI provider call failed (%s). "
            "Using deterministic fallback.",
            type(exc).__name__,
        )
        return None


def generate_copilot_analysis(
    shipment: Shipment,
    quotes: list[Quote],
    peer_quotes: list[Quote],
) -> dict[str, Any]:
    """Generate AI analysis with a deterministic fallback."""

    benchmark = calculate_shipment_estimate(
        shipment, peer_quotes
    )

    ai_result = call_ai_provider(
        shipment,
        quotes,
        peer_quotes,
        benchmark=benchmark,
    )

    if ai_result:
        ai_result.setdefault("disclaimer", DISCLAIMER)
        return ai_result

    return generate_fallback_copilot_response(
        shipment,
        quotes,
        peer_quotes,
        benchmark=benchmark,
    )
