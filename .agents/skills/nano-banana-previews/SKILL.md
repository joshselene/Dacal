---
name: nano-banana-previews
description: Generate three concept preview images of a planned Chyron scene with Nano Banana (Gemini image models) so the tutor can approve the look before the 3D build, stored in Cloud Storage. Use for preview thumbnails, image prompts, or the Preview approved lifecycle step.
---

# Nano Banana concept previews

Before the 3D room is configured, the tutor sees three quick illustrations of the scene and taps one to approve it. This makes the "Preview approved" lifecycle gate visible and adds an image model to the Google AI story. **It is on the cut list**: drop it before the validator or the 3D room.

## Already wired

**Implemented (2026-11-21):** `app/services/previews.py` (modes `off`/`inline`/`gcs`, parallel, local cache for `DEMO_MODE=cache`, `gemini_call` logs), `GET /api/v1/previews/{key}.png`, and the concept cards in `main.jsx` (image + "Concept preview" label, 3D fallback). Images are generated only by the concepts endpoints, never on scenario create. The notes below are the original plan.

`GeminiAIProvider._preview_image` adds `preview_image` (a data URL) to each concept when `GEMINI_PREVIEW_IMAGES=inline` and `GEMINI_IMAGE_MODEL` are set. In `main.jsx`, the concept cards (the `threeConcepts` block around "Choose one of three concepts") use CSS art classes (`art-guided` and others). Render `<img src={concept.preview_image}>` when it is present and keep the CSS art as the fallback.

Data URLs are fine for the demo but bloat `scenario.concept_preview` in the database. For production, upload to Cloud Storage and store a URL, using the sketch below.

## Call (production sketch)

```python
from google import genai
from google.genai import types
client = genai.Client()
MODEL = os.environ["GEMINI_IMAGE_MODEL"]   # a Nano Banana model; confirm the ID on Day 1

def previews(spec: dict) -> list[bytes]:
    prompt = preview_prompt(spec)
    images = []
    for style in ("soft flat illustration", "simple 3D clay render", "calm watercolor"):
        r = client.models.generate_content(
            model=MODEL,
            contents=f"{prompt}\nStyle: {style}.",
            config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
        )
        for part in r.candidates[0].content.parts:
            if part.inline_data:
                images.append(part.inline_data.data)
    return images
```

Run the three styles in parallel (`asyncio.gather` with `client.aio.models.generate_content`) so previews arrive together.

## Prompt builder

Build the prompt **from the validated spec**, not from the tutor's raw text, so the picture matches what will be built: theme, the 3–6 main objects with rough positions ("ticket machine on the right wall, bench at the back"), and the task goal.

Always add: "Calm, uncluttered, soft lighting, low visual noise, no text, no logos, no real people's faces, suitable for learners with sensory sensitivities."

## Storage and UI

- Save each image to Cloud Storage at `gs://$BUCKET/previews/{scene_id}/{version}/{n}.png`, and return V4 signed URLs that expire after 1 hour.
- The UI shows three cards. Approving one sets `status = "preview_approved"` on the version and records which image was chosen.
- When `DEMO_MODE=cache`, serve the three stored images for each seed scene.

## Honesty note

The previews are illustrations, not the 3D output. The UI labels them "Concept preview".
