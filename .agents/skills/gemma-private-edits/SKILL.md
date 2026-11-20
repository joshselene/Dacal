---
name: gemma-private-edits
description: Run small scene edits with Gemma, Google's open model, so a school can keep tutor instructions on its own hardware; same JSON Patch contract and validator as the Gemini path. Use for the private or offline mode, Gemma model setup, or the provider switch between Gemini and Gemma.
---

# Gemma private edits

Schools may not want any text leaving their building. Gemma lets the **edit** step (small JSON patches such as "make it quieter") run locally, while planning stays on Gemini. For the buildathon, show it as a switch and **describe it more than demo it**. It is second on the cut list.

## Where it plugs in

`GeminiAIProvider.apply_plain_language_edit` already produces and applies patches. Add a `GemmaEditor` with the same `{ops:[{op,path,value_json}]}` contract and choose it when `EDIT_PROVIDER=gemma`. Planning stays on Gemini.

## One interface, two providers

```python
class EditProvider(Protocol):
    def patch(self, spec: dict, instruction: str) -> list[dict]: ...   # RFC 6902 ops

class GeminiEdits(EditProvider): ...            # google-genai, GEMINI_PLANNER_MODEL
class GemmaEdits(EditProvider): ...             # see the options below

provider = GemmaEdits() if os.environ.get("EDIT_PROVIDER") == "gemma" else GeminiEdits()
```

Whichever provider ran, the output goes through the same steps: apply the patch to a copy, validate it, and on failure run the repair loop (on Gemini, or show the errors to the tutor in private mode).

## Ways to run Gemma

| Where | How | When |
| --- | --- | --- |
| Gemini API (hosted) | `client.models.generate_content(model=GEMMA_MODEL, ...)`; check that the current Gemma 4 ID is available in AI Studio | Demo day: no setup |
| Vertex AI Model Garden | Deploy a Gemma 4 endpoint in asia-south1 | Pilot with a managed endpoint |
| School hardware | Ollama or vLLM serving a small Gemma 4 instruct model on a local GPU or laptop, with an OpenAI-compatible endpoint | The real privacy story |

Gemma has weaker support for strict JSON schemas than Gemini. Ask it for a JSON array of patch operations, parse defensively, reject anything that isn't a valid patch, and rely on the validator.

## Prompt sketch

"You edit a JSON scene. Return ONLY a JSON array of RFC 6902 operations using replace, add or remove, on paths under /objects, /events, /task/steps, /support or /comfort_profile. Keep R5 comfort caps: low 40, medium 60, high 80 volume. Instruction: {instruction}. Scene: {spec}"

## What to say to the jury

"Planning runs on Gemini in the cloud. For schools that need it, edits can run on Gemma inside the school, and the same rule layer checks both." Only claim on-premise running if you have actually shown it working.
