"""One-time seeding script: loads data/customers.json into Firestore and
pre-populates a handful of historical transactions per customer so the
scoring engine has a baseline to compare against from minute one.

Requires GOOGLE_CLOUD_PROJECT env var (or gcloud default project) and
Application Default Credentials (`gcloud auth application-default login`)
or GOOGLE_APPLICATION_CREDENTIALS pointing at a service account key.

Run:  python scripts/seed_firestore.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from google.cloud import firestore  # noqa: E402

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def main() -> None:
    db = firestore.Client()

    customers = json.loads((DATA_DIR / "customers.json").read_text(encoding="utf-8"))
    transactions = json.loads((DATA_DIR / "transactions.json").read_text(encoding="utf-8"))

    batch = db.batch()
    for c in customers:
        batch.set(db.collection("customers").document(c["id"]), c)
    batch.commit()
    print(f"Seeded {len(customers)} customers")

    # Seed the first 150 historical transactions (oldest) so each customer has
    # baseline history before the live simulator starts firing new ones.
    historical = transactions[:150]
    batch = db.batch()
    count = 0
    for t in historical:
        batch.set(db.collection("transactions").document(t["id"]), t)
        count += 1
        if count % 400 == 0:
            batch.commit()
            batch = db.batch()
    batch.commit()
    print(f"Seeded {len(historical)} historical transactions")


if __name__ == "__main__":
    main()

