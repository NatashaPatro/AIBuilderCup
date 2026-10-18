"""FastAPI app: fraud analyst copilot backend.

Endpoints:
  GET  /health                         liveness check
  GET  /stats                          dashboard header stats
  POST /investigate/{alert_id}         run (or fetch cached) Gemini investigation
  POST /chat/{alert_id}                grounded follow-up question
  GET  /chat/{alert_id}                chat history

The transaction simulator runs as a background asyncio task for the lifetime
of the process so the Firestore-backed dashboard always shows live data.
"""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.agent import chat_followup, investigate_alert
from app.config import settings
from app.firestore_client import (
    add_chat_message,
    get_alert,
    get_chat_history,
    get_db,
    get_investigation,
    update_alert_status,
    write_investigation,
)
from app.models import ChatRequest, StatsResponse
from app.simulator import run_simulator_forever

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(run_simulator_forever())
    logger.info("Background simulator task started")
    yield
    task.cancel()


app = FastAPI(title="InvestiGate API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/stats", response_model=StatsResponse)
def stats():
    db = get_db()
    today = datetime.now(timezone.utc).date().isoformat()

    txns = list(db.collection("transactions").stream())
    alerts = list(db.collection("alerts").stream())

    txns_today = [t for t in txns if t.to_dict().get("timestamp", "").startswith(today)]
    alerts_today = [a for a in alerts if a.to_dict().get("created_at", "").startswith(today)]
    high_risk_open = [
        a for a in alerts
        if a.to_dict().get("status") == "open" and a.to_dict().get("severity") in ("high", "critical")
    ]

    return StatsResponse(
        transactions_today=len(txns_today),
        alerts_today=len(alerts_today),
        high_risk_open=len(high_risk_open),
        avg_investigation_seconds=2.0,
    )


@app.post("/investigate/{alert_id}")
async def investigate(alert_id: str):
    alert = get_alert(alert_id)
    if not alert:
        raise HTTPException(404, "Alert not found")

    cached = get_investigation(alert_id)
    if cached:
        return cached

    result = await investigate_alert(alert)
    write_investigation(alert_id, result)
    update_alert_status(alert_id, "investigating")
    return result


@app.post("/chat/{alert_id}")
async def chat(alert_id: str, body: ChatRequest):
    alert = get_alert(alert_id)
    investigation = get_investigation(alert_id)
    if not alert or not investigation:
        raise HTTPException(404, "Run an investigation before chatting")

    answer = await chat_followup(alert_id, alert, investigation, body.message)
    return {"answer": answer}


@app.get("/chat/{alert_id}")
def chat_history(alert_id: str):
    return get_chat_history(alert_id)


