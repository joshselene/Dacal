---
description: Day 1 kickoff - verify tests, switch to Gemini with a real key, deploy to Google Cloud, warm the demo cache.
---

1. Read `AGENTS.md` and `docs/SPARK.md`. Use the `chyron-repo-map` skill.
2. Install and test: `pip install -e apps/api pytest httpx`, then `cd apps/api && DATABASE_URL=sqlite:///./test.db AI_PROVIDER=mock python -m pytest -q`. All tests must pass.
3. Put the Gemini key in `.env`, confirm the model IDs in AI Studio, and run the API with `AI_PROVIDER=gemini`. Create one kirana-shop scenario through the UI and confirm a `gemini_call` log line appears.
4. With the user present, run `infra/gcp/setup.sh`, then `infra/gcp/deploy.sh` (`google-cloud-deploy` skill). Confirm `/api/health` on the Hosting URL.
5. Warm the demo cache: run the three demo prompts live on the demo laptop.
6. Report the live URL, the test results, and the top three tasks from the `buildathon-demo` cut list.
