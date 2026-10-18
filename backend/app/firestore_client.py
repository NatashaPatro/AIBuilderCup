"""Firestore client singleton + small helper CRUD functions.

Collections used:
  customers      -> customer profiles (seeded once)
  transactions   -> replayed transaction stream (written by the simulator)
  alerts         -> transactions flagged by the scoring engine
  investigations -> Gemini agent output per alert
  chats          -> follow-up Q&A messages per investigation
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from google.cloud import firestore

from app.config import settings

_db: firestore.Client | None = None


def get_db() -> firestore.Client:
    global _db
    if _db is None:
        _db = firestore.Client(project=settings.google_cloud_project or None)
    return _db


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------- customers ----------
def get_customer(customer_id: str) -> dict[str, Any] | None:
    doc = get_db().collection("customers").document(customer_id).get()
    return doc.to_dict() if doc.exists else None


def get_customer_transactions(customer_id: str, limit: int = 20) -> list[dict[str, Any]]:
    query = (
        get_db()
        .collection("transactions")
        .where("customer_id", "==", customer_id)
        .order_by("timestamp", direction=firestore.Query.DESCENDING)
        .limit(limit)
    )
    return [d.to_dict() for d in query.stream()]


# ---------- transactions ----------
def write_transaction(transaction: dict[str, Any]) -> str:
    ref = get_db().collection("transactions").document(transaction["id"])
    ref.set(transaction)
    return ref.id


# ---------- alerts ----------
def write_alert(alert: dict[str, Any]) -> str:
    ref = get_db().collection("alerts").document(alert["id"])
    ref.set(alert)
    return ref.id


def get_alert(alert_id: str) -> dict[str, Any] | None:
    doc = get_db().collection("alerts").document(alert_id).get()
    return doc.to_dict() if doc.exists else None


def update_alert_status(alert_id: str, status: str) -> None:
    get_db().collection("alerts").document(alert_id).update({"status": status})


# ---------- investigations ----------
def write_investigation(alert_id: str, investigation: dict[str, Any]) -> str:
    ref = get_db().collection("investigations").document(alert_id)
    ref.set(investigation)
    return ref.id


def get_investigation(alert_id: str) -> dict[str, Any] | None:
    doc = get_db().collection("investigations").document(alert_id).get()
    return doc.to_dict() if doc.exists else None


# ---------- chats ----------
def add_chat_message(investigation_id: str, role: str, content: str) -> None:
    get_db().collection("investigations").document(investigation_id).collection(
        "chats"
    ).add({"role": role, "content": content, "timestamp": now_iso()})


def get_chat_history(investigation_id: str) -> list[dict[str, Any]]:
    query = (
        get_db()
        .collection("investigations")
        .document(investigation_id)
        .collection("chats")
        .order_by("timestamp")
    )
    return [d.to_dict() for d in query.stream()]

