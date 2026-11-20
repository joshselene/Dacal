---
name: chyron-repo-map
description: Orientation for the Dacal / Chernyx AI Studio monorepo - which folders are live (apps/api, apps/web), which are legacy (src/ Express, root package.json, Redis/MinIO in compose), where the lifecycle, validator, provider, runs and four-wall engine live, and the keep/adapt/remove decisions for the Google rebuild. Use when starting a task, when unsure where code belongs, or before deleting anything.
---

# Repo map and migration decisions

## Live code paths

```text
apps/api/app/
  main.py                      FastAPI app, CORS (CORS_ORIGINS), /health and /api/health
  db.py                        DATABASE_URL (SQLite local, Cloud SQL Postgres in cloud)
  routers/studio_srs.py        /api/v1: modules, validate, scenarios, concepts, generate, jobs,
                               versions/{n}/edit|config|approve, runs, runs/{id}/command, WS console
  routers/experiences*.py      Earlier experience API (still mounted)
  routers/auth.py              JWT login, register, logout, me
  services/validator.py        R1–R7, reference spec, compile_pathway_config, simulate_learner_completion
  services/ai_provider.py      AIProvider, MockAIProvider, get_ai_provider, generate_with_repair_loop
  services/gemini_provider.py  GeminiAIProvider (AI_PROVIDER=gemini)
  services/scene_schema.json   Schema handed to Gemini
  models/                      organisation, tutor, student, classroom, module, project, experience,
                               experience_version, job, run, notebook_event, audit_event, notification
  modules/classes/             Clean-architecture class workspace (domain, application, infra, http)
  demo_seeds/                  Valid and faulty kirana-shop specs for the demo
apps/web/src/
  main.jsx                     Whole tutor app (login, home, authoring questions, concepts, generate,
                               configure, launch); calls API through VITE_API_BASE_URL
  classWorkspaceApi.js         Class and experience API client (CRLF line endings: keep them)
  components/FourWallPreview.jsx  Three.js room renderer and learner controls
  pages/ClassWorkspace.jsx     Classes and modules screen
  style.css, *.css             Glass tokens, to be replaced by Material 3
```

## Lifecycle as implemented

`draft` → (concepts) `preview_approved` → `/generate` runs the repair loop → `ready_to_configure` → `/config` → `configured` → `/approve` → `approved` → `/runs` (needs a valid, approved version) → run `running`, `paused` or `completed`.

## Decisions for the Google rebuild

| Area | Today | Decision |
| --- | --- | --- |
| AI provider | Mock, plus a `ClaudeAIProvider` stub that is really the mock | **Replace** with `GeminiAIProvider`; delete the Claude stub once the Gemini path is demoed |
| Validator | R1–R7 for shop scenarios | **Keep**; extend only with tests |
| Database | SQLAlchemy, `create_all` at startup, Alembic present | **Keep**; point `DATABASE_URL` to Cloud SQL |
| Queue | Redis and Celery in compose, unused by the API | **Remove from the cloud plan**. Generation runs synchronously within the 300 s Cloud Run timeout; Cloud Tasks or Pub/Sub is a stretch goal |
| Object store | MinIO in compose, unused by the API | **Replace** with Cloud Storage when previews are stored |
| Auth | Custom JWT with argon2 | **Keep** for the demo; Firebase Auth or Google Sign-In is a stretch goal |
| Web hosting | Vite dev server; `apps/web/Dockerfile` points at files that don't exist (pnpm lock, vite.config.ts) | **Firebase Hosting** from `vite build`; fix or delete the web Dockerfile |
| UI | Glass tokens in `style.css` | **Replace** with Material 3 (`material-redesign`) |
| Legacy `src/` and root `package.json` | Express and BullMQ prototype | **Remove** in a separate commit after the team agrees |

## Gotchas

- `classWorkspaceApi.js` uses CRLF line endings. Edit it with byte-safe tools or the diff will touch every line.
- `main.jsx` is large. Extract components into `src/screens/` while restyling, rather than adding more to it.
- `db.py` probes a default local Postgres with a 1 s timeout when `DATABASE_URL` is unset. Always set `DATABASE_URL`.
- Tests: run `cd apps/api && DATABASE_URL=sqlite:///./test.db AI_PROVIDER=mock python -m pytest -q`, and delete `test.db` after.
