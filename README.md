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

## Glass UI Preview

With API dependencies installed, run these in separate terminals from the repository root:

```bash
DATABASE_URL=sqlite:///./chernyx.db AI_PROVIDER=mock python3 -m uvicorn app.main:app --app-dir apps/api --host 127.0.0.1 --port 8000
```

```bash
npm --prefix apps/web ci
npm --prefix apps/web run dev -- --host 127.0.0.1 --port 5173
```

Open `http://127.0.0.1:5173`. Light/dark theme preferences persist in the browser.
This preview uses the existing mock AI provider, not live AI generation.

With both services running, the UI smoke test creates its own school and account:

```bash
cd apps/web
npx playwright install chromium
npm run test:ui
```

The test covers authoring through launch, theme persistence, 320/390/768/1440px layouts,
scene pixels and controls, and automated light/dark home-screen accessibility checks.
Set `UI_URL` to test a different web URL. Use a disposable development database for tests.

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
