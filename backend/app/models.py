"""Pydantic request/response models for the API."""
from __future__ import annotations

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str


class InvestigateRequest(BaseModel):
    alert_id: str


class StatsResponse(BaseModel):
    transactions_today: int
    alerts_today: int
    high_risk_open: int
    avg_investigation_seconds: float

