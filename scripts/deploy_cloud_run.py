"""One-off deployment helper: creates/updates the Cloud Run service via the
Cloud Run Admin API v2 (no gcloud CLI needed), using the pushed image, and
makes it publicly invokable.
"""
import json
import time
import google.auth
import google.auth.transport.requests
import requests

PROJECT = "investigate-511912"
REGION = "us-central1"
SERVICE = "investigate-api"
IMAGE = f"us-central1-docker.pkg.dev/{PROJECT}/investigate-repo/investigate-api:latest"
RUNTIME_SA = f"firebase-adminsdk-fbsvc@{PROJECT}.iam.gserviceaccount.com"

credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
credentials.refresh(google.auth.transport.requests.Request())
headers = {"Authorization": f"Bearer {credentials.token}", "Content-Type": "application/json"}

base = f"https://run.googleapis.com/v2/projects/{PROJECT}/locations/{REGION}"

service_body = {
    "template": {
        "serviceAccount": RUNTIME_SA,
        "containers": [
            {
                "image": IMAGE,
                "ports": [{"containerPort": 8080}],
                "env": [
                    {"name": "GOOGLE_CLOUD_PROJECT", "value": PROJECT},
                    {"name": "GOOGLE_CLOUD_LOCATION", "value": REGION},
                    {"name": "GOOGLE_GENAI_USE_VERTEXAI", "value": "true"},
                    {"name": "SIMULATOR_INTERVAL_SECONDS", "value": "8"},
                    {
                        "name": "ALLOWED_ORIGINS",
                        "value": "https://investigate-511912.web.app,http://localhost:5173",
                    },
                ],
                "resources": {"limits": {"cpu": "1", "memory": "512Mi"}},
            }
        ],
        "scaling": {"minInstanceCount": 0, "maxInstanceCount": 3},
    }
}

# Check if service already exists
get_resp = requests.get(f"{base}/services/{SERVICE}", headers=headers)
if get_resp.status_code == 200:
    print("Service exists, updating (PATCH)...")
    resp = requests.patch(f"{base}/services/{SERVICE}", headers=headers, json=service_body)
else:
    print("Creating new service...")
    resp = requests.post(f"{base}/services?serviceId={SERVICE}", headers=headers, json=service_body)

print("Status:", resp.status_code)
print(resp.text[:1500])

op = resp.json()
op_name = op.get("name")
if op_name and "operations" in op_name:
    print("Waiting for operation to complete...")
    for _ in range(60):
        time.sleep(5)
        op_resp = requests.get(f"https://run.googleapis.com/v2/{op_name}", headers=headers).json()
        if op_resp.get("done"):
            if "error" in op_resp:
                print("ERROR:", json.dumps(op_resp["error"], indent=2))
            else:
                print("Operation complete.")
            break
        print(".", end="", flush=True)

# Make it publicly invokable
iam_url = f"{base}/services/{SERVICE}:setIamPolicy"
policy = {"policy": {"bindings": [{"role": "roles/run.invoker", "members": ["allUsers"]}]}}
iam_resp = requests.post(iam_url, headers=headers, json=policy)
print("IAM policy status:", iam_resp.status_code)
print(iam_resp.text[:500])

# Fetch final service URL
final = requests.get(f"{base}/services/{SERVICE}", headers=headers).json()
print("SERVICE_URL:", final.get("uri"))

