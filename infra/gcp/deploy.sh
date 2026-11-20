#!/usr/bin/env bash
# Deploy API to Cloud Run and web app to Firebase Hosting.
#   PROJECT_ID=my-project GEMINI_PLANNER_MODEL=<id from AI Studio> bash infra/gcp/deploy.sh
set -euo pipefail
: "${PROJECT_ID:?set PROJECT_ID}"
: "${GEMINI_PLANNER_MODEL:?set GEMINI_PLANNER_MODEL (confirm the current id in AI Studio)}"
REGION=asia-south1
CONN="${PROJECT_ID}:${REGION}:chyron-pg"

gcloud run deploy chyron-api \
  --project "$PROJECT_ID" --region "$REGION" \
  --source apps/api \
  --service-account "chyron-api@${PROJECT_ID}.iam.gserviceaccount.com" \
  --add-cloudsql-instances "$CONN" \
  --set-secrets "DATABASE_URL=chyron-database-url:latest,JWT_SECRET_KEY=chyron-jwt-secret:latest,GEMINI_API_KEY=gemini-api-key:latest" \
  --set-env-vars "^|^AI_PROVIDER=gemini|GEMINI_PLANNER_MODEL=${GEMINI_PLANNER_MODEL}|GEMINI_IMAGE_MODEL=${GEMINI_IMAGE_MODEL:-}|GEMINI_PREVIEW_IMAGES=${GEMINI_PREVIEW_IMAGES:-off}|DEMO_MODE=${DEMO_MODE:-live}|DEMO_CACHE_DIR=/tmp/demo_cache|BUCKET=${PROJECT_ID}-chyron|CORS_ORIGINS=https://${PROJECT_ID}.web.app,https://${PROJECT_ID}.firebaseapp.com" \
  --min-instances 1 --cpu 1 --memory 1Gi --timeout 300 \
  --allow-unauthenticated   # the API enforces its own JWT auth

# Web: same-origin API through the Hosting rewrite
VITE_API_BASE_URL=/api/v1 npm --prefix apps/web ci
VITE_API_BASE_URL=/api/v1 npm --prefix apps/web run build
firebase deploy --only hosting --project "$PROJECT_ID"

echo "Check: curl https://${PROJECT_ID}.web.app/api/health"
