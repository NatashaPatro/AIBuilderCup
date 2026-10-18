"""Rule-based + statistical anomaly scoring for transactions.

No ML training required: combines simple fraud heuristics with a
z-score check against the customer's historical spending to produce
a 0-100 risk score. Score >= ALERT_THRESHOLD triggers an alert.
"""
from __future__ import annotations

import statistics
from datetime import datetime
from typing import Any

ALERT_THRESHOLD = 55

HIGH_RISK_COUNTRIES = {"KP", "IR", "RU", "SY"}
ODD_HOURS = set(range(0, 5))  # 00:00 - 04:59 local


def _hour_of(timestamp_iso: str) -> int:
    return datetime.fromisoformat(timestamp_iso).hour


def score_transaction(
    transaction: dict[str, Any],
    customer: dict[str, Any] | None,
    recent_transactions: list[dict[str, Any]],
) -> dict[str, Any]:
    """Returns {score, reasons: [...], severity}."""
    reasons: list[str] = []
    score = 0

    amount = transaction["amount"]
    country = transaction.get("country", "US")
    merchant = transaction.get("merchant", "")
    hour = _hour_of(transaction["timestamp"])

    # 1. Amount deviation vs customer's historical average (z-score)
    history_amounts = [t["amount"] for t in recent_transactions if t["id"] != transaction["id"]]
    if len(history_amounts) >= 3:
        mean = statistics.mean(history_amounts)
        stdev = statistics.pstdev(history_amounts) or 1.0
        z = (amount - mean) / stdev
        if z > 3:
            score += 35
            reasons.append(
                f"Amount ${amount:,.2f} is {z:.1f} std-dev above customer's average (${mean:,.2f})"
            )
        elif z > 2:
            score += 18
            reasons.append(
                f"Amount ${amount:,.2f} is notably higher than usual (avg ${mean:,.2f})"
            )
    elif amount > 5000:
        score += 15
        reasons.append(f"Large transaction (${amount:,.2f}) with insufficient history to baseline")

    # 2. Velocity: multiple transactions in a short window
    recent_count = len(recent_transactions)
    if recent_count >= 5:
        score += 20
        reasons.append(f"{recent_count} transactions from this customer in the lookback window (velocity spike)")

    # 3. Geo mismatch / high-risk country
    home_country = (customer or {}).get("home_country", "US")
    if country in HIGH_RISK_COUNTRIES:
        score += 30
        reasons.append(f"Transaction originates from high-risk jurisdiction ({country})")
    elif country != home_country:
        score += 12
        reasons.append(f"Transaction country ({country}) differs from customer's home country ({home_country})")

    # 4. New / unusual merchant
    known_merchants = {t.get("merchant") for t in recent_transactions}
    if merchant and merchant not in known_merchants:
        score += 10
        reasons.append(f"First transaction with merchant '{merchant}' for this customer")

    # 5. Odd hours
    if hour in ODD_HOURS:
        score += 10
        reasons.append(f"Transaction occurred at {hour:02d}:00 local time (unusual hour)")

    score = min(score, 100)
    severity = "critical" if score >= 80 else "high" if score >= 65 else "medium" if score >= ALERT_THRESHOLD else "low"

    return {"score": score, "reasons": reasons, "severity": severity}

