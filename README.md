# Chernyx AI Studio – Phase 1 Monorepo

This repository contains the **Phase 1** implementation of **Chernyx AI Studio**.

- **Backend** – FastAPI + Python 3.12 (apps/api)
- **Frontend** – React 18 + TypeScript + Vite (apps/web)
- **Shared** – generated OpenAPI client (packages/shared)
- **Infra** – Docker‑Compose, CI pipelines, environment templates (infra)
- **Docs** – Architecture diagrams, ADRs, run‑books (docs)

The code is deliberately minimal for the first milestone: a health‑check endpoint, Docker setup, CI skeleton and pre‑commit hooks. Subsequent milestones will flesh out authentication, domain logic, AI integration, etc.

---
## Quick start (Docker)
```bash
# copy example env file and adjust if needed
cp infra/.env.example .env

# start all services
docker compose up -d
```
You should see the API health endpoint at `http://localhost:8000/health` and the web app at `http://localhost:5173`.

---
## Project layout
```
cheranyx-ai-studio/
├─ apps/
│   ├─ api/            # FastAPI backend
│   └─ web/            # React TypeScript frontend
├─ packages/
│   └─ shared/         # generated TS client (OpenAPI)
├─ infra/               # Docker, CI, env template
├─ docs/                # Architecture, ADRs
└─ .pre-commit-config.yaml
```