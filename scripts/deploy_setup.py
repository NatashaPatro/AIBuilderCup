"""One-off deployment helper: creates the Artifact Registry repo (if needed)
and prints a docker-login-ready access token so we can push the locally
built image without requiring the gcloud CLI.
"""
import json
import google.auth
import google.auth.transport.requests
import requests

PROJECT = "investigate-511912"
REGION = "us-central1"
REPO = "investigate-repo"

credentials, _ = google.auth.default(
    scopes=["https://www.googleapis.com/auth/cloud-platform"]
)
credentials.refresh(google.auth.transport.requests.Request())
token = credentials.token

# Create Artifact Registry Docker repo if it doesn't already exist.
url = f"https://artifactregistry.googleapis.com/v1/projects/{PROJECT}/locations/{REGION}/repositories?repositoryId={REPO}"
body = {"format": "DOCKER", "description": "InvestiGate backend images"}
resp = requests.post(url, headers={"Authorization": f"Bearer {token}"}, json=body)
print("Create repo status:", resp.status_code)
print(resp.text[:500])

# Print the token so the shell can pipe it into `docker login`.
with open("access_token.txt", "w", encoding="utf-8") as f:
    f.write(token)
print("TOKEN_WRITTEN")

