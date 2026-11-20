# Google-first stack (always on)

- AI: Gemini API through `google-genai` (Python) and `@google/genai` (JS), via `AIProvider` in `apps/api/app/services/`. Gemma for private edits, Nano Banana for images. No other AI vendors on this branch. The `mock` provider stays for tests and offline work.
- Cloud: Cloud Run, Cloud SQL for PostgreSQL, Firebase Hosting, Cloud Storage, Secret Manager, Cloud Logging and Monitoring. Region asia-south1.
- UI: Material 3 tokens and Material Web, Material Symbols, Google Fonts.
- Model IDs come only from environment variables (`GEMINI_PLANNER_MODEL`, `GEMINI_LIVE_MODEL`, `GEMINI_IMAGE_MODEL`, `GEMMA_MODEL`).
- Prefer Google-maintained SDKs. If you add any other dependency, say why in the commit message.
