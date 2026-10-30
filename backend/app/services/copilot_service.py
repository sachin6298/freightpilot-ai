"""Copilot service for AI-assisted quote analysis and deterministic fallback."""

import json
import logging
from decimal import Decimal
from typing import Any, Optional

import httpx

from app.config import settings
from app.db.models import Quote, Shipment
from app.services.risk_service import assess_quote_risk

logger = logging.getLogger(__name__)


def generate_fallback_copilot_response(
    shipment: Shipment,
    quotes: list[Quote],
    peer_quotes: list[Quote],
) -> dict[str, Any]:
    """Generate a structured, deterministic fallback comparison grounded strictly in quotes data."""
    if not quotes:
        return {
            "summary": "No quotes provided for comparison.",
            "comparison": [],
            "missing_information": ["No quote data available."],
            "next_questions": ["Please request quotes from carriers for this shipment."],
            "disclaimer": "Human review required; outputs are estimates.",
        }

    # Assess risks for each quote
    assessments = {
        q.id: assess_quote_risk(q, shipment, peer_quotes)
        for q in quotes
    }

    # Sort quotes by total amount
    sorted_quotes = sorted(quotes, key=lambda q: Decimal(str(q.total_amount)))
    lowest_quote = sorted_quotes[0]
    highest_quote = sorted_quotes[-1]

    # Calculate price spread
    low_amt = Decimal(str(lowest_quote.total_amount))
    high_amt = Decimal(str(highest_quote.total_amount))
    currency = shipment.currency

    # Build Summary
    if len(quotes) == 1:
        summary = (
            f"Evaluated 1 quote from {quotes[0].provider_label} for {shipment.cargo_type} "
            f"({shipment.quantity_tonnes} MT) from {shipment.origin} to {shipment.destination}. "
            f"Total price is {quotes[0].total_amount} {quotes[0].currency} with an estimated transit "
            f"of {quotes[0].transit_days or 'unspecified'} days."
        )
    else:
        summary = (
            f"Compared {len(quotes)} freight quotes for shipping {shipment.quantity_tonnes} MT of "
            f"{shipment.cargo_type} from {shipment.origin} to {shipment.destination}. "
            f"Quote totals range from {low_amt} {currency} ({lowest_quote.provider_label}) "
            f"to {high_amt} {currency} ({highest_quote.provider_label}). "
            f"Key trade-offs center around price competitiveness, transit time, fee transparency, and advance terms."
        )

    comparison_details = []
    all_missing_info = set()
    all_next_questions = set()

    for q in quotes:
        risk_info = assessments[q.id]
        flags = risk_info.get("flags", [])
        advantages = []
        concerns = []

        # Advantages
        if q.id == lowest_quote.id and len(quotes) > 1:
            advantages.append(f"Lowest total cost ({q.total_amount} {q.currency}).")
        if q.transit_days is not None:
            if all(other.transit_days is None or q.transit_days <= other.transit_days for other in quotes):
                advantages.append(f"Fastest estimated transit time ({q.transit_days} days).")
            else:
                advantages.append(f"Declared transit duration of {q.transit_days} days.")
        if q.surcharge_amount > 0 and q.terms and q.terms.get("itemized"):
            advantages.append("Provides itemized fee structure for ocean freight and surcharges.")

        if not flags:
            advantages.append("No automated risk flags detected; quote matches standard benchmark parameters.")

        # Concerns from risk flags
        for flag in flags:
            concerns.append(f"[{flag['severity']}] {flag['title']}: {flag['evidence']}")
            if flag.get("recommended_check"):
                all_next_questions.add(f"{q.provider_label}: {flag['recommended_check']}")

        # Check missing information
        if q.transit_days is None:
            all_missing_info.add(f"Transit duration unspecified for {q.provider_label} ({q.reference}).")
            all_next_questions.add(f"Ask {q.provider_label} for estimated transit days and vessel schedule.")
        if q.validity_until is None:
            all_missing_info.add(f"Quote validity expiration date missing for {q.provider_label}.")
            all_next_questions.add(f"Ask {q.provider_label} until when this quoted rate remains valid.")
        if q.vessel_class is None:
            all_missing_info.add(f"Vessel class/specification not declared for {q.provider_label}.")
        if q.surcharge_amount == 0 and q.terms and not q.terms.get("itemized"):
            all_missing_info.add(f"Itemized surcharge breakdown (BAF, THCs) omitted for {q.provider_label}.")

        # General questions
        if q.terms and q.terms.get("advance_pct"):
            all_next_questions.add(
                f"Confirm payment milestone schedule and security with {q.provider_label} "
                f"for the requested {q.terms['advance_pct']}% advance deposit."
            )

        comparison_details.append({
            "quote_id": q.id,
            "advantages": advantages if advantages else ["Valid freight quote structure."],
            "concerns": concerns if concerns else ["No critical risk concerns identified."],
        })

    # Default questions if none
    if not all_next_questions:
        all_next_questions.add("Confirm whether demurrage and detention free days are included.")
        all_next_questions.add("Verify whether fuel adjustment factor (BAF) is subject to floating adjustments.")

    # Default missing info if none
    if not all_missing_info:
        all_missing_info.add("None identified; all core quote fields are populated.")

    return {
        "summary": summary,
        "comparison": comparison_details,
        "missing_information": sorted(list(all_missing_info)),
        "next_questions": sorted(list(all_next_questions)),
        "disclaimer": "Human review required; outputs are estimates.",
    }


def call_ai_provider(
    shipment: Shipment,
    quotes: list[Quote],
    peer_quotes: list[Quote],
) -> Optional[dict[str, Any]]:
    """Call server-side AI provider API to generate grounded quote analysis."""
    if not settings.AI_API_KEY:
        return None

    # Prepare structured context for AI
    assessments = {
        q.id: assess_quote_risk(q, shipment, peer_quotes)
        for q in quotes
    }

    quotes_data = []
    for q in quotes:
        quotes_data.append({
            "quote_id": q.id,
            "carrier_label": q.provider_label,
            "reference": q.reference,
            "base_amount": float(q.base_amount),
            "surcharge_amount": float(q.surcharge_amount),
            "total_amount": float(q.total_amount),
            "currency": q.currency,
            "transit_days": q.transit_days,
            "validity_until": q.validity_until.isoformat() if q.validity_until else None,
            "vessel_class": q.vessel_class,
            "cargo_capacity_tonnes": float(q.cargo_capacity_tonnes) if q.cargo_capacity_tonnes else None,
            "terms": q.terms,
            "risk_assessment": assessments[q.id],
        })

    prompt_context = {
        "shipment": {
            "id": shipment.id,
            "cargo_type": shipment.cargo_type,
            "quantity_tonnes": float(shipment.quantity_tonnes),
            "origin": shipment.origin,
            "destination": shipment.destination,
            "ready_date": shipment.ready_date.isoformat(),
            "required_arrival_date": shipment.required_arrival_date.isoformat() if shipment.required_arrival_date else None,
            "currency": shipment.currency,
        },
        "quotes": quotes_data,
    }

    system_instruction = (
        "You are FreightPilot AI, an expert freight procurement assistant.\n"
        "Analyze the provided shipment and quotes data objectively.\n"
        "STRICT GROUNDING RULES:\n"
        "1. Ground all explanations exclusively in the provided shipment and quote facts.\n"
        "2. Do NOT invent carrier facts, prices, sanctions status, or market data.\n"
        "3. Do NOT authorize, create, or mention payment execution capabilities.\n"
        "4. Highlight differences in cost, transit time, risk flags, missing data, and trade-offs.\n"
        "5. Output strictly valid JSON matching the following schema:\n"
        "{\n"
        '  "summary": "Brief overall narrative of trade-offs between cost, speed, and risk",\n'
        '  "comparison": [\n'
        '    {"quote_id": "string", "advantages": ["string"], "concerns": ["string"]}\n'
        '  ],\n'
        '  "missing_information": ["string"],\n'
        '  "next_questions": ["string"],\n'
        '  "disclaimer": "Human review required; outputs are estimates."\n'
        "}"
    )

    provider = settings.AI_PROVIDER.lower().strip()
    model = settings.AI_MODEL or "gemini-1.5-flash"

    try:
        if provider == "gemini":
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={settings.AI_API_KEY}"
            payload = {
                "system_instruction": {"parts": [{"text": system_instruction}]},
                "contents": [{"parts": [{"text": json.dumps(prompt_context)}]}],
                "generationConfig": {"response_mime_type": "application/json"},
            }
            with httpx.Client(timeout=10.0) as client:
                res = client.post(url, json=payload)
                if res.status_code == 200:
                    res_data = res.json()
                    candidates = res_data.get("candidates", [])
                    if candidates:
                        text = candidates[0]["content"]["parts"][0]["text"]
                        parsed = json.loads(text)
                        if "summary" in parsed and "comparison" in parsed:
                            return parsed

        elif provider == "openai":
            url = "https://api.openai.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {settings.AI_API_KEY}"}
            payload = {
                "model": model or "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": json.dumps(prompt_context)},
                ],
                "response_format": {"type": "json_object"},
            }
            with httpx.Client(timeout=10.0) as client:
                res = client.post(url, headers=headers, json=payload)
                if res.status_code == 200:
                    res_data = res.json()
                    text = res_data["choices"][0]["message"]["content"]
                    parsed = json.loads(text)
                    if "summary" in parsed and "comparison" in parsed:
                        return parsed

    except Exception as e:
        logger.warning(f"AI provider call failed: {e}. Falling back to deterministic copilot response.")

    return None


def generate_copilot_analysis(
    shipment: Shipment,
    quotes: list[Quote],
    peer_quotes: list[Quote],
) -> dict[str, Any]:
    """Generate copilot analysis, attempting AI provider first, falling back to deterministic engine."""
    ai_result = call_ai_provider(shipment, quotes, peer_quotes)
    if ai_result:
        # Ensure default disclaimer
        if "disclaimer" not in ai_result:
            ai_result["disclaimer"] = "Human review required; outputs are estimates."
        return ai_result

    return generate_fallback_copilot_response(shipment, quotes, peer_quotes)
