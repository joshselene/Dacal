# Chyron (Chernyx AI Studio × DACAL) — agent guide

Chyron lets a special-education tutor describe a life-skills scenario in plain words and get a safe, validated 3D practice room. Learners use it on a laptop or in a four-wall projected room. This branch, `buildathon/google`, rebuilds the prototype on Google AI and Google Cloud for the Google Startup Buildathon India 2026. The jury scores it on **SPARK** (see `docs/SPARK.md`).

Read this file first. Each part of the build has a skill under `.agents/skills/`.

## Repo map (what really exists)

| Path | What | Status |
| --- | --- | --- |
| `apps/api/` | FastAPI on Python 3.12, SQLAlchemy, JWT auth (argon2) | **Main backend** |
| `apps/api/app/services/validator.py` | Rules R1–R7 plus the R3w warning, the reference shop spec, the pathway compiler, the learner simulator | Core. Do not weaken it |
| `apps/api/app/services/ai_provider.py` | `AIProvider` interface, Mock provider, `generate_with_repair_loop` (k=3) | Keep the interface |
| `apps/api/app/services/gemini_provider.py` | **Gemini** provider: concepts, plan, repair, JSON Patch edits, demo cache | New on this branch |
| `apps/api/app/services/scene_schema.json` | JSON Schema of the scene spec, used for Gemini structured output | New |
| `apps/api/app/routers/studio_srs.py` | Scenarios lifecycle, jobs, versions/edit/config/approve, runs, console WebSocket | Main API |
| `apps/api/app/demo_seeds/` | `kirana_shop.valid.json`, plus `kirana_shop.faulty.json` (fails R3, R4, R5, R6) | Demo |
| `apps/api/tests/` | `test_srs_acceptance.py` (AT-01..07) and `test_gemini_provider.py` (offline fake) | 13 tests pass |
| `apps/web/` | React 18 + Vite (JSX), Three.js, axios, lucide; `main.jsx` is about 3,400 lines | Main front end |
| `apps/web/src/components/FourWallPreview.jsx` | Three.js room in five modes: overview, laptop, room (four walls), 2×2, single wall (`?wall=N`) | Keep |
| `apps/web/src/style.css` | Apple-style glass tokens | **Redesign to Material 3** |
| `apps/web/tests/ui.spec.js` | Playwright plus axe accessibility checks at 320, 390, 768 and 1440 px | Keep it passing |
| `src/`, root `package.json` | An older Express/Sequelize prototype | Legacy. Do not extend; delete when convenient |
| `docker-compose.yml` | Postgres, Redis, MinIO | Local only. The API doesn't use Redis or MinIO |
| `infra/gcp/`, `firebase.json` | Cloud Run, Cloud SQL and Firebase Hosting scripts | New |

## The one idea that must never break: Plan → Validate → Build

Gemini **proposes** a spec. `validate_scene_spec` (R1–R7) **decides**. Only a valid, approved version reaches `/runs`. Errors go back to Gemini as critique, with at most 3 attempts. After that the tutor gets a plain-language failure message. No flag, endpoint or demo shortcut may skip validation.

The engine and validator currently model **shop** scenarios: grid room, south entrance, shelves with priced items, a required counter, a budget. Demo scenarios must be shops (kirana store, bakery, pharmacy counter, vegetable stall). A bus stop or a road crossing would need new assets and rules first.

## Google stack on this branch

| Job | Google product | Where |
| --- | --- | --- |
| Concepts, plan, repair, edits | Gemini API (`google-genai`, structured JSON) | `gemini_provider.py` |
| Voice description | Gemini Live → `voice_transcript` field | `gemini-live-intake` skill |
| Concept images | Nano Banana | `GEMINI_PREVIEW_IMAGES` |
| Private edits | Gemma | `gemma-private-edits` skill |
| API | Cloud Run, asia-south1 | `apps/api/Dockerfile`, `infra/gcp/deploy.sh` |
| Database | Cloud SQL for PostgreSQL (same SQLAlchemy models) | `infra/gcp/setup.sh` |
| Files | Cloud Storage (replaces MinIO) | bucket `${PROJECT_ID}-chyron` |
| Web | Firebase Hosting, `/api/**` rewritten to Cloud Run | `firebase.json` |
| Secrets | Secret Manager | database URL, JWT secret, Gemini key |
| Observability | Cloud Logging and Monitoring | `gemini_call` JSON log lines |
| Coding agent | Antigravity (Gemini CLI as backup) | this file and `.agents/` |

## Support pathway semantics (from validator.py, don't invert)

- **A** = most prompting and calmest room. **C** = fewest prompts and busiest room.
- `prompt` A ≥ B ≥ C. `density` A ≤ B ≤ C. `volume` A ≤ B ≤ C.
- Caps: A 40/2, B 60/3, C 80/5 (volume/density). These are illustrative and not clinically set.

## Commands

```bash
# API (from repo root)
pip install -e apps/api pytest httpx
cd apps/api && DATABASE_URL=sqlite:///./dev.db AI_PROVIDER=mock python -m pytest -q
DATABASE_URL=sqlite:///./chernyx.db AI_PROVIDER=gemini python -m uvicorn app.main:app --app-dir apps/api --port 8000
# Web
npm --prefix apps/web ci && npm --prefix apps/web run dev -- --port 5173
cd apps/web && npm run test:ui          # needs API + web running
# Cloud
PROJECT_ID=... DB_PASSWORD=... bash infra/gcp/setup.sh
PROJECT_ID=... GEMINI_PLANNER_MODEL=... bash infra/gcp/deploy.sh
```

## Non-negotiables

- No diagnosis, labels or outcome claims. The notebook stores counts and times only (`NotebookEvent`).
- AI prompts carry no learner data (SEC-04). AI output is untrusted input (SEC-05).
- Model IDs only from environment variables. Secrets only in `.env` (gitignored) or Secret Manager.
- `DEMO_MODE=cache` must replay the demo with no network.
- Record anything that existed before the event in `docs/PRIOR_WORK.md`.

## Skills

| Skill | Use when |
| --- | --- |
| `chyron-repo-map` | Orienting in the code; deciding keep, adapt or remove |
| `chyron-scene-spec` | Spec fields, `scene_schema.json`, seeds |
| `chyron-validator` | R1–R7, the repair loop, comfort caps, tests |
| `gemini-scene-planner` | `gemini_provider.py`: prompts, caching, logging, edits |
| `gemini-live-intake` | Voice input for the scenario description |
| `nano-banana-previews` | Concept preview images |
| `gemma-private-edits` | On-premise or private edit mode |
| `three-room-engine` | `FourWallPreview.jsx`, runs, the tutor console |
| `material-redesign` | Any UI or CSS work (glass → Material 3) |
| `google-cloud-deploy` | Docker, Cloud Run, Cloud SQL, Hosting, secrets |
| `buildathon-demo` | Demo path, SPARK mapping, cut list, submission |
