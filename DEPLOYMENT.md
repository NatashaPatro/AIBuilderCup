# Deployment Guide

Step-by-step commands to go from this repo to a live, judge-accessible
prototype. Run these yourself (outside the assistant) once the required
accounts/tools below are set up.

## 0. Prerequisites (one-time)

- Install [`gcloud` CLI](https://cloud.google.com/sdk/docs/install) and run `gcloud init`
- Install [`firebase` CLI](https://firebase.google.com/docs/cli): `npm install -g firebase-tools`
- Install Node.js 20+ and Python 3.12
- Create a GCP project (or use an existing one) and **enable billing**
  (claim the $300 free trial or your hackathon's credit coupon)
- In the GCP Console, enable these APIs:
  - Cloud Run API
  - Vertex AI API
  - Cloud Firestore API
  - Cloud Build API
  - Secret Manager API (optional, can use plain env vars instead)
- In the [Firebase Console](https://console.firebase.google.com), add Firebase
  to the same GCP project. Enable:
  - **Firestore** (Native mode, pick a region e.g. `us-central1`)
  - **Authentication** → Email/Password provider
  - **Hosting**
- Create one demo analyst user under Authentication → Users, e.g.
  `analyst@demo.com` with a password you'll share with judges.

## 1. Local setup

```powershell
gcloud auth login
gcloud auth application-default login
gcloud config set project investigate-511912
firebase login
```

Copy env templates and fill in real values:

```powershell
Copy-Item backend\.env.example backend\.env
Copy-Item frontend\.env.example frontend\.env
```

- `backend/.env`: set `GOOGLE_CLOUD_PROJECT`, keep `GOOGLE_GENAI_USE_VERTEXAI=true`
- `frontend/.env`: paste the Firebase web app config from
  Firebase Console → Project Settings → Your apps → Web app, and set
  `VITE_API_BASE_URL` to your Cloud Run URL once deployed (step 3).

## 2. Seed Firestore with demo data

```powershell
pip install -r backend\requirements.txt
python scripts\generate_data.py      # already run once; re-run to regenerate
python scripts\seed_firestore.py     # loads customers + historical transactions
```

## 3. Deploy backend to Cloud Run

```powershell
cd backend
gcloud run deploy investigate-api `
  --source . `
  --region us-central1 `
  --allow-unauthenticated `
  --set-env-vars GOOGLE_CLOUD_PROJECT=investigate-511912,GOOGLE_GENAI_USE_VERTEXAI=true,GOOGLE_CLOUD_LOCATION=us-central1 `
  --min-instances 0
cd ..
```

Copy the resulting **Service URL** into `frontend/.env` as `VITE_API_BASE_URL`,
and into `backend`'s `ALLOWED_ORIGINS` env var once you know your Firebase
Hosting URL (step 4), then redeploy with:

```powershell
gcloud run services update investigate-api --region us-central1 `
  --set-env-vars ALLOWED_ORIGINS=https://investigate-511912.web.app
```

## 4. Deploy frontend to Firebase Hosting

```powershell
cd frontend
npm install
npm run build
cd ..
firebase deploy --only hosting,firestore:rules,firestore:indexes
```

Your live prototype will be at `https://investigate-511912.web.app`.

## 5. Right before judging / submission

```powershell
gcloud run services update investigate-api --region us-central1 --min-instances 1
```

This keeps one instance warm so the API never cold-starts/fails during
evaluation. Remember this has a small ongoing cost — only do it right before
and during the evaluation window, then scale back with `--min-instances 0`.

## 6. Sanity check before submitting

- [ ] Open the Hosting URL in an incognito window, sign in with the demo
      analyst account, confirm live transactions are streaming
- [ ] Click an alert → Run AI Investigation → confirm reasoning trace + chat work
- [ ] Confirm `/health` on the Cloud Run URL returns `{"status": "ok"}`
- [ ] Confirm the GitHub repo is public and has the latest code pushed








