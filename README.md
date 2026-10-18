# InvestiGate

An AI-powered fraud investigation assistant for BFSI. Transactions stream in
live, a rule + statistical scoring engine flags anomalies in real time, and a
**Gemini-powered agent** autonomously investigates each alert — pulling
customer history, reasoning step-by-step against a compliance rulebook, and
producing a risk score, evidence list, and recommended action. Analysts can
then ask grounded follow-up questions in a chat interface.

Built for the BFSI track: *Intelligent Risk, Fraud & Financial Experiences*.

## How this uses the required Google tech

- **Firebase** — Hosting (frontend deployment) + Authentication (analyst login)
- **Firestore** — real-time data store for transactions, alerts, investigations,
  and chat history; the dashboard uses live `onSnapshot` listeners so new
  alerts appear instantly with zero polling
- **Cloud Run** — hosts the FastAPI backend: the transaction simulator,
  scoring engine, and the Gemini investigation/chat endpoints
- **Gemini (Vertex AI)** — powers the autonomous investigation agent
  (structured JSON reasoning trace + recommendation) and the grounded
  follow-up chat

## Architecture

```
Firebase Hosting (React)  ──Auth──▶  Firebase Authentication
        │
        │ onSnapshot (live)
        ▼
    Firestore  ◀───────────────┐
        ▲                      │
        │ writes               │ reads/writes
Cloud Run (FastAPI)  ───────────┘
  ├─ simulator.py   (background loop replaying synthetic transactions)
  ├─ scoring.py     (rule + z-score anomaly scoring → alerts)
  └─ agent.py       (Gemini: investigation + grounded chat)
```

## Repo structure

```
backend/     FastAPI app, scoring engine, Gemini agent, Dockerfile
frontend/    React + Vite + Tailwind dashboard, Firebase client SDK
scripts/     synthetic data generator + Firestore seeding script
data/        committed synthetic customers.json / transactions.json
```

## Local development

Backend:
```powershell
cd backend
pip install -r requirements.txt
Copy-Item .env.example .env   # fill in GOOGLE_CLOUD_PROJECT etc.
uvicorn app.main:app --reload --port 8080
```

Frontend:
```powershell
cd frontend
npm install
Copy-Item .env.example .env   # fill in Firebase config + API URL
npm run dev
```

## Deployment

See [`DEPLOYMENT.md`](./DEPLOYMENT.md) for the exact `gcloud`/`firebase`
commands to seed Firestore and deploy both services.

## Demo flow

1. Sign in as the demo analyst
2. Watch live transactions stream into the feed (Firestore real-time)
3. A flagged transaction appears in the Alert Queue
4. Click it → **Run AI Investigation** → watch the Gemini agent's reasoning
   trace render step by step → risk score + recommended action
5. Ask a follow-up question in the chat box, grounded on the investigation

## Roadmap (beyond the hackathon prototype)

- Pub/Sub for true event-driven transaction ingestion at scale
- BigQuery ML for a trained anomaly-detection model
- Document AI for KYC/claims document intelligence
- Vertex AI Search for full compliance-corpus retrieval (currently a small
  embedded rulebook)

