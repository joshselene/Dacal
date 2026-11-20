#!/usr/bin/env bash
# One-time Google Cloud setup for Chyron (run before Day 1, read each step first).
#   PROJECT_ID=my-project DB_PASSWORD='...' bash infra/gcp/setup.sh
set -euo pipefail
: "${PROJECT_ID:?set PROJECT_ID}"
: "${DB_PASSWORD:?set DB_PASSWORD for the Cloud SQL app user}"
REGION=asia-south1
SQL_INSTANCE=chyron-pg
SA="chyron-api@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud config set project "$PROJECT_ID"
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com \
  sqladmin.googleapis.com secretmanager.googleapis.com storage.googleapis.com \
  logging.googleapis.com monitoring.googleapis.com aiplatform.googleapis.com firebasehosting.googleapis.com

# Service account the API runs as
gcloud iam service-accounts create chyron-api --display-name="Chyron API" 2>/dev/null || true
for role in roles/cloudsql.client roles/secretmanager.secretAccessor roles/storage.objectAdmin \
            roles/logging.logWriter roles/aiplatform.user; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" --member="serviceAccount:${SA}" \
    --role="$role" --condition=None --quiet >/dev/null
done

# Cloud SQL for PostgreSQL (replaces the docker-compose postgres). Smallest tier for the demo.
gcloud sql instances create "$SQL_INSTANCE" --database-version=POSTGRES_16 --region="$REGION" \
  --edition=ENTERPRISE --tier=db-f1-micro --storage-size=10GB 2>/dev/null || true
gcloud sql databases create chyron --instance="$SQL_INSTANCE" 2>/dev/null || true
gcloud sql users create chyron --instance="$SQL_INSTANCE" --password="$DB_PASSWORD" 2>/dev/null || true

# Cloud Storage replaces MinIO (concept previews, exports)
gcloud storage buckets create "gs://${PROJECT_ID}-chyron" --location="$REGION" \
  --uniform-bucket-level-access 2>/dev/null || true

# Secrets
CONN="${PROJECT_ID}:${REGION}:${SQL_INSTANCE}"
put_secret() { printf "%s" "$2" | gcloud secrets create "$1" --data-file=- 2>/dev/null \
  || printf "%s" "$2" | gcloud secrets versions add "$1" --data-file=-; }
put_secret chyron-database-url "postgresql+psycopg2://chyron:${DB_PASSWORD}@/chyron?host=/cloudsql/${CONN}"
put_secret chyron-jwt-secret "$(openssl rand -hex 32)"
KEY="${GEMINI_API_KEY:-}"
if [ -z "$KEY" ]; then
  printf "Paste GEMINI_API_KEY from AI Studio: "; read -rs KEY; echo
fi
put_secret gemini-api-key "$KEY"

echo "Setup done. Cloud SQL connection name: ${CONN}"
echo "Next: firebase projects:addfirebase ${PROJECT_ID}  (once), then bash infra/gcp/deploy.sh"
