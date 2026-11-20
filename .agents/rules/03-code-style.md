# Code style and workflow (always on)

- API: Python 3.12, FastAPI, pydantic, SQLAlchemy. Keep routers thin and put logic in `services/`. Use ruff with line length 120.
- Web: React 18 JSX with Vite. Put new screens in `apps/web/src/screens/` instead of growing `main.jsx`. Keep CRLF endings in `classWorkspaceApi.js`.
- Don't extend the legacy `src/` Express code.
- Before calling a task done: `cd apps/api && DATABASE_URL=sqlite:///./test.db AI_PROVIDER=mock python -m pytest -q` passes, `npm --prefix apps/web run build` passes, and one seed scenario runs end to end.
- Every Gemini call logs one structured `gemini_call` JSON line.
- Small commits; `buildathon/google` must always run the demo path.
