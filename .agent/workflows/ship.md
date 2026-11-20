---
description: Test, build and deploy buildathon/google to Cloud Run and Firebase Hosting, then smoke test.
---

1. Confirm the working tree is clean on `buildathon/google`.
2. Run the API tests and the web build. Stop on any failure.
3. Run `PROJECT_ID=... GEMINI_PLANNER_MODEL=... bash infra/gcp/deploy.sh`.
4. Smoke test: `/api/health`, sign in, generate a seed scenario, launch a run.
5. Tag the commit `demo-YYYYMMDD-HHMM`.
