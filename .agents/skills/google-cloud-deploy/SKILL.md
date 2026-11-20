---
name: google-cloud-deploy
description: Deploy Chyron on Google Cloud - FastAPI from apps/api on Cloud Run (asia-south1) with Cloud SQL for PostgreSQL, Secret Manager for DATABASE_URL, JWT and Gemini key, Vite build on Firebase Hosting with /api/** rewrite, Cloud Storage replacing MinIO, Cloud Logging and Monitoring. Scripts in infra/gcp/. Use for Docker, deploys, database, secrets, CORS, scaling or cost questions.
---

# Google Cloud deployment

## Files

| File | Does |
| --- | --- |
| `infra/gcp/setup.sh` | Enables APIs; creates the service account and roles, the Cloud SQL Postgres 16 instance `chyron-pg` (db-f1-micro), the database and user, the bucket, and the secrets `chyron-database-url`, `chyron-jwt-secret` and `gemini-api-key` |
| `infra/gcp/deploy.sh` | Cloud Run from source (`apps/api`) with the Cloud SQL socket and secrets; `vite build` with `VITE_API_BASE_URL=/api/v1`; `firebase deploy --only hosting` |
| `apps/api/Dockerfile` | python:3.12-slim, `pip install .`, uvicorn on `$PORT` |
| `firebase.json` | Hosting from `apps/web/dist`; `/api/**` → Cloud Run `chyron-api`; SPA fallback |

## Architecture

```text
Browser (React + Three.js, Material 3)
  └─ Firebase Hosting ──/api/**──► Cloud Run chyron-api (FastAPI, JWT auth)
                                      ├─► Gemini API / Vertex AI (plan, repair, edit, previews)
                                      ├─► Cloud SQL for PostgreSQL (SQLAlchemy models, unchanged)
                                      ├─► Cloud Storage (previews, exports)
                                      ├─► Secret Manager (DATABASE_URL, JWT_SECRET_KEY, GEMINI_API_KEY)
                                      └─► Cloud Logging → log-based metrics → Monitoring dashboard
Console WebSocket: browser → Cloud Run URL directly (Hosting rewrites don't proxy WebSockets)
```

## Order of operations (Day 1 evening at the latest)

1. `gcloud auth login && gcloud auth application-default login`, and `npm i -g firebase-tools && firebase login`.
2. `PROJECT_ID=... DB_PASSWORD=... bash infra/gcp/setup.sh`
3. `firebase projects:addfirebase $PROJECT_ID` (once).
4. `PROJECT_ID=... GEMINI_PLANNER_MODEL=<id> bash infra/gcp/deploy.sh`
5. `curl https://$PROJECT_ID.web.app/api/health` → `{"status":"ok","ai_provider":"gemini",...}`
6. Register a tutor, create a scenario, generate it and launch a run, all over a phone hotspot.

## Notes

- **Schema creation:** `main.py` runs `Base.metadata.create_all` at startup, so a fresh Cloud SQL database is ready on first boot. Alembic exists for real migrations later.
- **CORS:** `CORS_ORIGINS` is set to the Hosting domains in `deploy.sh`. Local development keeps localhost.
- **Cold starts:** `--min-instances 1` during the event; set it to 0 afterwards to save cost.
- **Timeouts:** generation is synchronous. With at most 1 plan call and 3 repair calls, it fits the 300 s request timeout. Moving it to Cloud Tasks or Pub/Sub plus a worker is the scale story; say "designed for" unless you have built it.
- **Cost guard:** set a billing budget alert in the console before the event, and an AI Studio or Vertex quota cap.
- **docker-compose.yml** stays for local Postgres only. Redis and MinIO are not used by the API.

## True scale statements for the jury

The API is stateless on Cloud Run and autoscales. Generation cost per scene is bounded by design (at most 4 model calls). Data stays in India (asia-south1). Postgres is managed by Cloud SQL. Static assets are served from the Firebase CDN.
