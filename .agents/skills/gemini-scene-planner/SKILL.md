---
name: gemini-scene-planner
description: GeminiAIProvider in apps/api/app/services/gemini_provider.py - google-genai structured JSON output with scene_schema.json for concepts, scene planning, critique-driven repair and RFC 6902 patch edits, plus token logging, demo replay cache, fallbacks, and context caching. Use for any Gemini call, prompt, model setting, or AI_PROVIDER change.
---

# Gemini planner

`AI_PROVIDER=gemini` makes `get_ai_provider()` return `GeminiAIProvider`. Every router that calls the provider (scenario concepts, generate, version edit) then uses Gemini with no other changes.

## What each method does

| Method | Gemini call | Fallback |
| --- | --- | --- |
| `generate_concepts` | 3 concepts (guided, explore, calm) as a JSON array; optional Nano Banana image each | Mock concepts, so the tutor is never blocked |
| `plan_scene` | Spec using `response_json_schema=SCENE_SCHEMA`, temperature 0.5; on a repair call, errors plus the previous spec at temperature 0.2 | **None.** On error it returns a non-dict, the validator reports R1 and the loop records it honestly |
| `apply_plain_language_edit` | `{ops:[{op, path, value_json}]}` patch limited to /layout, /task, /support and /events, applied by `apply_patch` | The deterministic regex editor in `MockAIProvider` |

After any edit the router re-validates. Keep it that way.

## Configuration

- `GEMINI_API_KEY` (AI Studio), or Vertex AI through `GOOGLE_GENAI_USE_VERTEXAI=true`, `GOOGLE_CLOUD_PROJECT` and `GOOGLE_CLOUD_LOCATION`. On Cloud Run, Vertex AI with the service account avoids handling a key at all. Use it if the quota is there.
- `GEMINI_PLANNER_MODEL`: a Flash-class model. **Confirm the ID in AI Studio on Day 1**; the default in code is only a placeholder.
- `DEMO_MODE=cache` with `DEMO_CACHE_DIR`: live calls write `{kind}-{hash}.json`, and cache mode replays them without network access. Warm the cache the night before by running each demo prompt live. On Cloud Run the filesystem is temporary, so warm it on the laptop that will run the fallback demo.

## Prompting rules

- `PLANNER_SYSTEM` restates R2–R7 in plain words with typical values. Whenever the validator changes, update the prompt too. A high first-pass rate is the story ("most scenes pass first time; repairs are rare and bounded").
- Send only the tutor's description, the tutor's answers, the chosen concept and the spec. Never send student records (SEC-04).
- Keep outputs small: 4–10 layout objects and 1–4 required items.

## Observability (for the jury)

Each call appends to `provider.usage` and logs `{"event":"gemini_call", kind, model, latency_ms, input_tokens, output_tokens, cached_tokens}`. On Cloud Run, build a log-based metric and a Monitoring chart (tokens per scene, attempts per scene), and keep it open during Q&A.

## Context caching

The system prompt and schema repeat on every call. Gemini caches long repeated prefixes implicitly on recent models; check `cached_tokens` in the logs. If you need explicit caching, create a cache at startup with `client.caches.create(...)` holding the system instruction, then pass `cached_content=` instead of `system_instruction`. Check the minimum token size for the chosen model first.

## Tests

`apps/api/tests/test_gemini_provider.py` uses a fake client, so it needs no key and no network. It covers the factory, repair on attempt 2, stopping after 3, network errors staying visible, cache replay, concept fallback, patch edits and patch path safety. Add a test for any new behaviour.

## Next steps (in order)

1. Run one real call with a key: `AI_PROVIDER=gemini` and create a scenario through the UI.
2. Show attempt-by-attempt `rules_summary` in the generate screen.
3. Stream progress (Server-Sent Events from `/scenarios/{id}/generate`, or polling `/jobs/{id}`).
4. `EDIT_PROVIDER=gemma` switch (`gemma-private-edits`).
