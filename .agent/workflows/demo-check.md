---
description: Run the jury demo path and readiness checklist from the buildathon-demo skill; report pass or fail and change nothing.
---

1. Run the API tests and `npm --prefix apps/web run build`.
2. On the deployed URL, walk the six-step demo path in the `buildathon-demo` skill.
3. POST `apps/api/app/demo_seeds/kirana_shop.faulty.json` to `/api/v1/validate` and confirm R3, R4, R5 and R6 fail; confirm generation repairs within 3 attempts.
4. Restart the API locally with `DEMO_MODE=cache` and no network, and replay the path.
5. Run `npm --prefix apps/web run test:ui` (Playwright plus axe) against local services.
6. Print a pass or fail table mapped to the SPARK letters. Do not fix anything without asking.
