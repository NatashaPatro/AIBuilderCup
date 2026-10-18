"""Generates synthetic customers + transactions for the demo, including
crafted fraud patterns so the simulator reliably produces alerts.

Pure Python, no external APIs - fast and deterministic (seeded) so the
dataset is reproducible. Writes data/customers.json and data/transactions.json.

Run:  python scripts/generate_data.py
"""
from __future__ import annotations

import json
import random
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

random.seed(42)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

FIRST_NAMES = [
    "Aarav", "Maya", "Liam", "Sofia", "Noah", "Zara", "Ethan", "Priya",
    "Mateo", "Ivy", "Kenji", "Elena", "Omar", "Nina", "Lucas", "Ava",
    "Rohan", "Grace", "Diego", "Hannah",
]
LAST_NAMES = [
    "Shah", "Rossi", "Nguyen", "Garcia", "Müller", "Kim", "Dubois", "Khan",
    "Silva", "Novak",
]
MERCHANTS = [
    "Amazon", "Walmart", "Target", "Starbucks", "Uber", "Netflix", "Shell",
    "Best Buy", "Delta Airlines", "Marriott", "Apple Store", "Steam",
    "DoorDash", "Costco", "Home Depot",
]
RARE_MERCHANTS = [
    "QuickCash Wire Transfer", "CryptoSwap Exchange", "Global Gift Cards Ltd",
    "Offshore Holdings LLC", "Rapid Remit International",
]
COUNTRIES = ["US", "GB", "CA", "DE", "FR", "IN", "AU", "SG"]
HIGH_RISK_COUNTRIES = ["KP", "IR", "RU", "SY"]


def _gen_customers(n: int = 20) -> list[dict]:
    customers = []
    for _ in range(n):
        home_country = random.choice(COUNTRIES)
        customers.append(
            {
                "id": str(uuid.uuid4()),
                "name": f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
                "home_country": home_country,
                "account_tier": random.choice(["standard", "premium", "private_banking"]),
                "avg_monthly_spend": round(random.uniform(800, 6000), 2),
                "account_age_years": round(random.uniform(0.5, 12), 1),
            }
        )
    return customers


def _normal_transaction(customer: dict, ts: datetime) -> dict:
    amount = round(max(5, random.gauss(customer["avg_monthly_spend"] / 20, 30)), 2)
    return {
        "id": str(uuid.uuid4()),
        "customer_id": customer["id"],
        "amount": amount,
        "merchant": random.choice(MERCHANTS),
        "country": customer["home_country"],
        "timestamp": ts.isoformat(),
    }


def _fraud_transaction(customer: dict, ts: datetime, pattern: str) -> dict:
    base = _normal_transaction(customer, ts)
    if pattern == "amount_spike":
        base["amount"] = round(customer["avg_monthly_spend"] * random.uniform(3, 8), 2)
        base["merchant"] = random.choice(RARE_MERCHANTS)
    elif pattern == "geo_mismatch":
        base["country"] = random.choice(HIGH_RISK_COUNTRIES)
        base["amount"] = round(random.uniform(2000, 9000), 2)
    elif pattern == "odd_hours":
        ts = ts.replace(hour=random.randint(0, 4), minute=random.randint(0, 59))
        base["timestamp"] = ts.isoformat()
        base["amount"] = round(random.uniform(1500, 4000), 2)
        base["merchant"] = random.choice(RARE_MERCHANTS)
    elif pattern == "new_merchant_large":
        base["merchant"] = random.choice(RARE_MERCHANTS)
        base["amount"] = round(customer["avg_monthly_spend"] * random.uniform(2, 4), 2)
    return base


def _gen_transactions(customers: list[dict], n_normal: int = 420, n_fraud: int = 30) -> list[dict]:
    txns: list[dict] = []
    now = datetime.now(timezone.utc)

    for _ in range(n_normal):
        customer = random.choice(customers)
        ts = now - timedelta(minutes=random.randint(1, 60 * 24 * 14))
        txns.append(_normal_transaction(customer, ts))

    patterns = ["amount_spike", "geo_mismatch", "odd_hours", "new_merchant_large"]
    for _ in range(n_fraud):
        customer = random.choice(customers)
        ts = now - timedelta(minutes=random.randint(1, 60 * 24 * 14))
        pattern = random.choice(patterns)
        txns.append(_fraud_transaction(customer, ts, pattern))

    # Velocity burst: pick 2 customers and give them 6 rapid-fire transactions
    for _ in range(2):
        customer = random.choice(customers)
        burst_start = now - timedelta(minutes=random.randint(1, 60 * 24 * 10))
        for i in range(6):
            ts = burst_start + timedelta(minutes=i * 2)
            txns.append(_normal_transaction(customer, ts))

    txns.sort(key=lambda t: t["timestamp"])
    return txns


def main() -> None:
    customers = _gen_customers()
    transactions = _gen_transactions(customers)

    (DATA_DIR / "customers.json").write_text(
        json.dumps(customers, indent=2), encoding="utf-8"
    )
    (DATA_DIR / "transactions.json").write_text(
        json.dumps(transactions, indent=2), encoding="utf-8"
    )
    print(f"Generated {len(customers)} customers and {len(transactions)} transactions in {DATA_DIR}")


if __name__ == "__main__":
    main()

