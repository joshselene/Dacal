---
name: chyron-validator
description: The R1-R7 constraint layer in apps/api/app/services/validator.py (structure, geometry, BFS reachability with R3w warning, solvability and budget, comfort caps per pathway, monotone support, referential integrity) and the bounded k=3 repair loop in ai_provider.generate_with_repair_loop. Use when touching validation, comfort caps, repair behaviour, the validate endpoint, or validator tests.
---

# Validator and repair loop

This is the safety core and the clearest proof of technical depth for the jury. It already exists and works. **Extend it; don't rewrite it.**

## Rules as implemented

| Rule | Check | Code examples |
| --- | --- | --- |
| R1 | Structure, types and enums for room, layout, task, support, events | `missing_required_fields`, `invalid_object_cell` |
| R7 | Unique ids; event targets exist (or `shopkeeper`) | `duplicate_object_id`, `unknown_event_target` |
| R2 | Entrance on the S wall and its edge; objects inside the room; no overlaps; entrance not blocked | `object_overlap`, `entrance_blocked` |
| R3 | Breadth-first search from the entrance; shelves holding required items, and the counter, must be reachable | `unreachable_critical_object`, `missing_counter` |
| R3w | Unreachable decor | Warning only |
| R4 | Every required sku is stocked; the cheapest basket is within budget | `missing_required_items`, `budget_insufficient` |
| R5 | Volume and density per pathway within caps (A 40/2, B 60/3, C 80/5) | `volume_exceeds_cap` |
| R6 | prompt A≥B≥C, density A≤B≤C, volume A≤B≤C | `non_monotone_volume` |

The report shape is `{valid, errors[{rule, code, message, target}], warnings, rules_summary{R1..R7, R3w}, elapsed_ms}`. The UI should render `rules_summary` as seven chips that turn from grey to green or red. That screen sells the architecture.

## Repair loop

`generate_with_repair_loop(prompt, answers, concept, max_retries=3, provider=...)`:

1. `provider.plan_scene(...)`, then `validate_scene_spec`.
2. If the spec is invalid, the next `plan_scene` call gets `critique=report["errors"]`. `GeminiAIProvider` then sends a REPAIR prompt with the previous spec.
3. After 3 failures it returns `success: False` and `error_plain`. The scenario goes back to `preview_approved` for the tutor to adjust.

Improvements worth doing for the demo (each needs a test):

- Return every attempt's `rules_summary` in the job record (`JobRecord.validation_report` already exists). The UI can then animate *attempt 1: R3 ✗ R4 ✗ → attempt 2: all ✓*.
- Log one JSON line per attempt (`event: validation`, attempt, rules failed, elapsed_ms) next to the `gemini_call` lines.

## Demo spec

`apps/api/app/demo_seeds/kirana_shop.faulty.json` fails R3, R4, R5 and R6 at once. POST it to `/api/v1/validate` to show the chips, then show Gemini repairing it. A "Run safety check" developer button is enough.

## Rules for changes

- Caps and thresholds are illustrative. Never describe them as clinically validated.
- New rule → new test in `tests/` → update the planner system prompt in `gemini_provider.py` and `scene_schema.json`.
- Never add a bypass parameter.
