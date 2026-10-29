# Chernyx AI Studio – Phase 1 Monorepo

This repository contains the Phase 1 implementation of Chernyx AI Studio.

- **Backend:** FastAPI + Python 3.12 (`apps/api`)
- **Frontend:** React + TypeScript + Vite (`apps/web`)
- **Shared:** Generated OpenAPI client (`packages/shared`)
- **Infrastructure:** Docker Compose, CI pipelines, and environment templates (`infra`)
- **Documentation:** Architecture diagrams, ADRs, and runbooks (`docs`)

## Quick Start

Start the application using Docker Compose:

```bash
cp infra/.env.example .env
docker compose up -d
```

The API should be available at `http://localhost:8000/health` and the web application at `http://localhost:5173`.

## Project Structure

```text
cheranyx-ai-studio/
├── apps/
│   ├── api/       # FastAPI backend
│   └── web/       # Frontend application
├── packages/
│   └── shared/    # Shared client code
├── infra/         # Docker and environment configuration
└── .pre-commit-config.yaml
```
