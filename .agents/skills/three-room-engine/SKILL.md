---
name: three-room-engine
description: Render a validated Chyron scene spec as a Three.js practice room in the browser - laptop mode and four-wall projected room via scissor viewports, support levels A/B/C, step progression, comfort-safe audio, and the counts-and-times notebook. Use for any 3D, learner view, tutor console, or projection work.
---

# Three.js room engine

The engine is a pure function of the spec: `buildRoom(spec) → scene graph`. It never calls a model and never trusts a spec that hasn't passed validation (the API only serves validated versions).

## What exists (`apps/web/src/components/FourWallPreview.jsx`)

- `buildScene(spec)` builds walls, floor, shelves with item labels, counter, shoppers (density) and the shopkeeper from the **grid spec** (room w/h cells).
- Modes: `overview` (OrbitControls), `laptop` (first person, facing `position.dir`), `room` (four walls N, E, S, W via `setViewport` per wall), `grid2x2`, and single wall. `?wall=N` turns one browser window into one projector's wall, so four machines can each show one wall.
- On-screen arrow controls, "Hand" (pick up), pause and reset, using lucide icons.
- Runs: `POST /api/v1/runs {scenario_id, pathway, mode}`. Commands go through `POST /runs/{id}/command` (pause, resume, simplify, prompt, what_if, move, select, step_complete, end) and the WebSocket `/api/v1/runs/{id}/console`.

## Improvements for the buildathon (in order)

1. **Pathway visible in the room:** A shows a highlight and arrow to the next required item plus a spoken prompt; C shows none. Read `compile_pathway_config(spec, pathway)` from the run.
2. **Speech:** use `speechSynthesis` for prompts now; Gemini TTS through the API is a stretch goal. Never play sudden loud audio. Fade in, and clamp to the pathway volume.
3. **Large controls:** at least 72 px targets, single-switch scanning mode (Space cycles, Enter acts).
4. **Tutor console view:** live pathway switch and "what if" buttons wired to `/command`.
5. Keep 60 fps on integrated graphics: share materials (already cached), avoid shadows, and cap shoppers at the density value.

## WebSocket on Firebase Hosting

Hosting rewrites don't proxy WebSockets. Point the console socket straight at the Cloud Run URL (`VITE_WS_BASE_URL=wss://chyron-api-....run.app/api/v1`), or fall back to polling `/runs/{id}` every second.

## Notebook (non-diagnostic)

`NotebookEvent` stores `kind, step_id, pathway, t_ms, event_data`. Show counts and times only. No labels such as "struggled", and no scores on the learner screen.
