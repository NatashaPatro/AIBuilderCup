"""Background simulator: replays the committed synthetic transaction dataset
into Firestore at a fixed interval so the dashboard always shows live activity.

Runs as an asyncio background task started from main.py's lifespan handler.
Loops forever over data/transactions.json, advancing the timestamp to "now"
each lap so judges see a believable live feed no matter when they open the demo.
"""
from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.config import settings
from app.firestore_client import (
    get_customer,
    get_customer_transactions,
    write_alert,
    write_transaction,
)
from app.scoring import ALERT_THRESHOLD, score_transaction

logger = logging.getLogger("simulator")

# Works both locally (data/ lives at the repo root, two levels above backend/)
# and in the Cloud Run container (Dockerfile COPYs data/ into backend/data).
_CANDIDATE_DATA_DIRS = [
    Path(__file__).resolve().parent.parent / "data",           # backend/data (container)
    Path(__file__).resolve().parent.parent.parent / "data",    # repo-root/data (local dev)
]
DATA_DIR = next((p for p in _CANDIDATE_DATA_DIRS if (p / "transactions.json").exists()), _CANDIDATE_DATA_DIRS[0])


def _load_dataset() -> list[dict]:
    path = DATA_DIR / "transactions.json"
    with path.open(encoding="utf-8") as f:
        return json.load(f)


async def run_simulator_forever() -> None:
    try:
        dataset = _load_dataset()
    except Exception:  # noqa: BLE001 - must never silently kill the background task
        logger.exception("Failed to load dataset from %s; simulator cannot start.", DATA_DIR)
        return

    if not dataset:
        logger.warning("No transactions found in data/transactions.json; simulator idle.")
        return

    logger.info("Simulator starting with %d transactions, interval=%ss", len(dataset), settings.simulator_interval_seconds)
    i = 0
    while True:
        template = dataset[i % len(dataset)]
        i += 1

        txn = dict(template)
        txn["id"] = str(uuid.uuid4())
        txn["timestamp"] = datetime.now(timezone.utc).isoformat()

        try:
            customer = get_customer(txn["customer_id"])
            history = get_customer_transactions(txn["customer_id"], limit=10)
            result = score_transaction(txn, customer, history)
            txn["risk_score"] = result["score"]

            write_transaction(txn)

            if result["score"] >= ALERT_THRESHOLD:
                alert = {
                    "id": str(uuid.uuid4()),
                    "transaction_id": txn["id"],
                    "customer_id": txn["customer_id"],
                    "amount": txn["amount"],
                    "merchant": txn.get("merchant"),
                    "country": txn.get("country"),
                    "score": result["score"],
                    "severity": result["severity"],
                    "reasons": result["reasons"],
                    "status": "open",
                    "created_at": txn["timestamp"],
                }
                write_alert(alert)
                logger.info("ALERT %s score=%s customer=%s", alert["id"], alert["score"], txn["customer_id"])
        except Exception:  # noqa: BLE001 - keep the loop alive no matter what
            logger.exception("Simulator tick failed, continuing")

        await asyncio.sleep(settings.simulator_interval_seconds)

