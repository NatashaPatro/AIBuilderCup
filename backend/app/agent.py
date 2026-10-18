"""Gemini-powered fraud investigation agent.

Given an alert, pulls the customer profile + recent transaction history from
Firestore, builds a grounded prompt with a small embedded compliance
rulebook, and asks Gemini (JSON mode) to produce a structured investigation:
risk score, evidence, a step-by-step reasoning trace, and a recommended
action. Also supports grounded follow-up chat on a completed investigation.

Falls back to a cached, pre-computed investigation if the Gemini call fails,
so the live demo never breaks due to API hiccups/quota.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from google import genai
from google.genai import types

from app.config import settings
from app.firestore_client import (
    add_chat_message,
    get_chat_history,
    get_customer,
    get_customer_transactions,
)

logger = logging.getLogger("agent")

# A few canned compliance rules used as grounding context instead of a full
# retrieval system (keeps the prototype lean while still "RAG-flavored").
COMPLIANCE_RULEBOOK = """
1. Transactions over $10,000 to a new merchant require enhanced due diligence.
2. Transactions involving sanctioned or high-risk jurisdictions (KP, IR, RU, SY)
   must be escalated to compliance regardless of amount.
3. More than 4 transactions within a short window from one customer should be
   treated as a potential account-takeover / velocity-fraud pattern.
4. Transactions between 00:00-05:00 local time combined with any other risk
   factor should raise the recommended action by one severity level.
5. First-time merchant + amount > 3x customer's historical average should
   recommend a temporary hold pending customer verification.
"""

INVESTIGATION_SCHEMA = {
    "type": "object",
    "properties": {
        "risk_score": {"type": "integer"},
        "severity": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
        "evidence": {"type": "array", "items": {"type": "string"}},
        "reasoning_trace": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "step": {"type": "string"},
                    "detail": {"type": "string"},
                },
                "required": ["step", "detail"],
            },
        },
        "recommended_action": {"type": "string"},
        "summary": {"type": "string"},
    },
    "required": [
        "risk_score",
        "severity",
        "evidence",
        "reasoning_trace",
        "recommended_action",
        "summary",
    ],
}

FALLBACK_INVESTIGATION = {
    "risk_score": 78,
    "severity": "high",
    "evidence": [
        "Transaction amount is 4.2x the customer's historical average.",
        "First transaction with this merchant.",
        "Occurred at 02:14 local time, an unusual hour for this customer.",
    ],
    "reasoning_trace": [
        {"step": "Pulled customer history", "detail": "Reviewed last 10 transactions for this account."},
        {"step": "Compared transaction amount", "detail": "Current amount significantly exceeds the customer's typical spend."},
        {"step": "Checked merchant familiarity", "detail": "This merchant has never been used by the customer before."},
        {"step": "Checked compliance rulebook", "detail": "Matched rule 5: first-time merchant + amount > 3x average."},
    ],
    "recommended_action": "Place a temporary hold and contact the customer to verify the transaction before releasing funds.",
    "summary": "This transaction shows multiple independent risk signals consistent with card-not-present fraud. Recommend verification before clearing.",
    "fallback": True,
}


def _get_client() -> genai.Client:
    if settings.use_vertexai:
        return genai.Client(
            vertexai=True,
            project=settings.google_cloud_project,
            location=settings.google_cloud_location,
        )
    return genai.Client(api_key=settings.gemini_api_key)


def _build_investigation_prompt(alert: dict[str, Any], customer: dict[str, Any] | None, history: list[dict[str, Any]]) -> str:
    return f"""You are a senior fraud investigation analyst AI at a bank. Analyze the
flagged transaction below and produce a structured investigation.

COMPLIANCE RULEBOOK:
{COMPLIANCE_RULEBOOK}

CUSTOMER PROFILE:
{json.dumps(customer or {}, indent=2, default=str)}

RECENT TRANSACTION HISTORY (most recent first):
{json.dumps(history, indent=2, default=str)}

FLAGGED ALERT:
{json.dumps(alert, indent=2, default=str)}

Instructions:
- Think step by step like a human investigator would, referencing specific
  numbers from the data (amounts, dates, countries, merchants).
- Cite which compliance rule(s) apply, if any.
- reasoning_trace should have 3-6 steps describing your investigation process
  in order (e.g. "Pulled customer history", "Compared transaction amount", ...).
- recommended_action should be a single clear, actionable instruction for the
  human analyst (e.g. approve, hold and verify, block and escalate).
- Return ONLY valid JSON matching the required schema.
"""


async def investigate_alert(alert: dict[str, Any]) -> dict[str, Any]:
    customer = get_customer(alert["customer_id"])
    history = get_customer_transactions(alert["customer_id"], limit=10)
    prompt = _build_investigation_prompt(alert, customer, history)

    try:
        client = _get_client()
        response = client.models.generate_content(
            model=settings.gemini_pro_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=INVESTIGATION_SCHEMA,
                temperature=0.2,
            ),
        )
        result = json.loads(response.text)
        result["fallback"] = False
        return result
    except Exception:  # noqa: BLE001
        logger.exception("Gemini investigation failed, using fallback")
        return dict(FALLBACK_INVESTIGATION)


async def chat_followup(investigation_id: str, alert: dict[str, Any], investigation: dict[str, Any], message: str) -> str:
    history = get_chat_history(investigation_id)
    history_text = "\n".join(f"{m['role']}: {m['content']}" for m in history)

    prompt = f"""You are a fraud analyst copilot. Answer the analyst's follow-up
question using ONLY the investigation context below. Be concise (2-4 sentences).

ALERT:
{json.dumps(alert, indent=2, default=str)}

INVESTIGATION:
{json.dumps(investigation, indent=2, default=str)}

PRIOR CONVERSATION:
{history_text}

ANALYST QUESTION: {message}
"""

    add_chat_message(investigation_id, "user", message)

    try:
        client = _get_client()
        response = client.models.generate_content(
            model=settings.gemini_flash_model,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.3),
        )
        answer = response.text.strip()
    except Exception:  # noqa: BLE001
        logger.exception("Gemini chat follow-up failed, using fallback")
        answer = (
            "I'm temporarily unable to reach the reasoning engine, but based on the "
            "investigation on file, the key risk driver is the flagged evidence above. "
            "Please retry in a moment."
        )

    add_chat_message(investigation_id, "assistant", answer)
    return answer

