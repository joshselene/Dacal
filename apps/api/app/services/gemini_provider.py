"""Gemini implementation of the AIProvider interface (Google Startup Buildathon build).

Plan-Validate-Build is unchanged: Gemini only *proposes* a scene spec. Every
output still goes through validator.validate_scene_spec (R1-R7) via
ai_provider.generate_with_repair_loop before anything reaches a learner.

What Gemini does here
- generate_concepts: three short concept directions for the tutor to choose from
  (FR-05). Optionally one Nano Banana preview image per concept.
- plan_scene: structured JSON scene spec using response_json_schema
  (scene_schema.json). On repair attempts it receives the validator critique
  and the previous spec, and returns a corrected full spec (FR-15, k=3).
- apply_plain_language_edit: a small RFC 6902 patch limited to safe paths,
  never a full regeneration (FR-08). Falls back to the deterministic regex
  editor if Gemini is unavailable.

Environment
- GEMINI_API_KEY, or GOOGLE_GENAI_USE_VERTEXAI=true plus GOOGLE_CLOUD_PROJECT
  and GOOGLE_CLOUD_LOCATION
- GEMINI_PLANNER_MODEL   Flash-class model id (confirm in AI Studio)
- GEMINI_IMAGE_MODEL     Nano Banana model id (optional)
- GEMINI_PREVIEW_IMAGES  "inline" to attach data-URL previews (demo only)
- DEMO_MODE              "cache" replays saved responses from DEMO_CACHE_DIR
- DEMO_CACHE_DIR         default ./demo_cache

Privacy (SEC-04): only the tutor's description, the tutor's answers and the
scene spec are sent. Never pass learner records to this module.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import logging
import os
from pathlib import Path
import time
from typing import Any

from .ai_provider import AIProvider, MockAIProvider
from .previews import attach_previews

log = logging.getLogger("chyron.gemini")

SCHEMA_PATH = Path(__file__).with_name("scene_schema.json")
SCENE_SCHEMA: dict[str, Any] = json.loads(SCHEMA_PATH.read_text())

DEFAULT_PLANNER_MODEL = "gemini-3.8-flash"  # placeholder; always set GEMINI_PLANNER_MODEL

PLANNER_SYSTEM = """You are Chyron's scene planner for special-education life-skills practice.
A tutor describes a shop scenario in plain words. Return ONE JSON scene spec that matches the
response schema. The spec is checked by strict rules before anything is built, so obey them:

Grid: cells are integers. x runs 0..room.w-1 (west to east), y runs 0..room.h-1 (north to south).
R2 geometry: the entrance is on the south wall; every entrance cell has y = room.h - 1. Every object
  stays inside the room (cell.x + size.w <= room.w, cell.y + size.h <= room.h). Objects never overlap
  each other and never cover an entrance cell.
R3 reachability: keep a walking lane at least 2 cells wide from the entrance to every shelf holding a
  required item and to the counter. Exactly one object has asset "counter"; put it near the entrance.
  Do not box objects in.
R4 solvability: every sku in task.required is in some shelf's items, and the sum of the cheapest price of
  each required sku is at most task.budget. Leave a comfortable margin (budget at least 1.3x that sum).
R5 comfort caps: support A volume<=40 density<=2; B volume<=60 density<=3; C volume<=80 density<=5.
R6 monotone support: prompt A>=B>=C, density A<=B<=C, volume A<=B<=C. A is the most supported, calmest.
  Typical: A {prompt 3, density 1, volume 30}, B {2, 2, 45}, C {1, 3, 60}.
R7 references: ids are unique; every event target is a layout id or "shopkeeper".

Style: familiar Indian shop settings (kirana store, bakery, pharmacy counter, vegetable stall), prices in
rupees, short kind rules in plain English, no clinical words, no names of real people or brands.
Use 4 to 10 layout objects and 1 to 4 required items unless the tutor asks otherwise."""

REPAIR_INSTRUCTION = (
    "REPAIR the scene below. The validator reported these errors. Change only what is needed to fix "
    "them, keep everything else identical, and return the full corrected spec."
)

CONCEPT_SCHEMA: dict[str, Any] = {
    "type": "array",
    "minItems": 3,
    "maxItems": 3,
    "items": {
        "type": "object",
        "required": ["id", "title", "summary", "environment", "visual_style", "tags"],
        "properties": {
            "id": {"type": "string", "enum": ["guided", "explore", "calm"]},
            "title": {"type": "string"},
            "summary": {"type": "string"},
            "environment": {"type": "string"},
            "visual_style": {"type": "string"},
            "tags": {"type": "array", "maxItems": 3, "items": {"type": "string"}},
        },
    },
}

PATCH_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["ops"],
    "properties": {
        "ops": {
            "type": "array",
            "minItems": 1,
            "maxItems": 6,
            "items": {
                "type": "object",
                "required": ["op", "path"],
                "properties": {
                    "op": {"type": "string", "enum": ["add", "replace", "remove"]},
                    "path": {"type": "string", "description": "JSON Pointer, e.g. /task/budget"},
                    "value_json": {"type": "string", "description": "the new value encoded as JSON text"},
                },
            },
        }
    },
}

ALLOWED_PATCH_PREFIXES = ("/layout", "/task", "/support", "/events")
PREVIEW_ART = {"guided": "art-guided", "explore": "art-explore", "calm": "art-calm"}


class GeminiUnavailable(RuntimeError):
    pass


class GeminiAIProvider(AIProvider):
    name: str = "gemini"

    def __init__(self, client: Any | None = None, model: str | None = None, image_model: str | None = None):
        self._client = client
        self.model = model or os.getenv("GEMINI_PLANNER_MODEL", DEFAULT_PLANNER_MODEL)
        self.image_model = image_model or os.getenv("GEMINI_IMAGE_MODEL")
        self.cache_dir = Path(os.getenv("DEMO_CACHE_DIR", "demo_cache"))
        self._fallback = MockAIProvider()
        self._last_spec: dict[str, Any] | None = None
        self.usage: list[dict[str, Any]] = []  # one entry per Gemini call, for logs and the jury chart

    # ------------------------------------------------------------------ plumbing
    @property
    def client(self) -> Any:
        if self._client is None:
            try:
                from google import genai
            except ImportError as exc:  # pragma: no cover
                raise GeminiUnavailable("google-genai is not installed") from exc
            self._client = genai.Client()
        return self._client

    def _json_call(self, kind: str, contents: str, schema: dict[str, Any], temperature: float) -> Any:
        key = hashlib.sha256(f"{self.model}|{kind}|{contents}".encode()).hexdigest()[:20]
        cache_file = self.cache_dir / f"{kind}-{key}.json"
        if os.getenv("DEMO_MODE") == "cache" and cache_file.exists():
            self.usage.append({"kind": kind, "cached_replay": True})
            return json.loads(cache_file.read_text())

        from google.genai import types

        started = time.perf_counter()
        resp = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=PLANNER_SYSTEM,
                response_mime_type="application/json",
                response_json_schema=schema,
                temperature=temperature,
            ),
        )
        meta = getattr(resp, "usage_metadata", None)
        record = {
            "kind": kind,
            "model": self.model,
            "latency_ms": round((time.perf_counter() - started) * 1000),
            "input_tokens": getattr(meta, "prompt_token_count", None),
            "output_tokens": getattr(meta, "candidates_token_count", None),
            "cached_tokens": getattr(meta, "cached_content_token_count", None),
        }
        self.usage.append(record)
        log.info(json.dumps({"event": "gemini_call", **record}))

        data = json.loads(resp.text)
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            cache_file.write_text(json.dumps(data))
        except OSError:
            pass  # read-only filesystem on Cloud Run is fine; the cache is a demo aid
        return data

    # ------------------------------------------------------------------ FR-05 concepts
    def generate_concepts(self, prompt: str, answers: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        contents = (
            "Propose three concept directions for this practice scenario: one guided (most structure), "
            "one explore (more choice), one calm (lowest stimulation). Each summary is one sentence.\n"
            f"Tutor description: {prompt.strip()}\nTutor answers: {json.dumps(answers or {})}"
        )
        try:
            concepts = self._json_call("concepts", contents, CONCEPT_SCHEMA, temperature=0.7)
            if not (isinstance(concepts, list) and len(concepts) == 3):
                raise ValueError("expected three concepts")
        except Exception as exc:  # network, quota, parse: never block the tutor
            log.warning("concepts fell back to mock: %s", exc)
            return self._fallback.generate_concepts(prompt, answers)

        for concept in concepts:
            concept["preview_art"] = PREVIEW_ART.get(concept.get("id"), "art-guided")
        return concepts

    def attach_preview_images(self, concepts: list[dict[str, Any]], scenario: str) -> list[dict[str, Any]]:
        """Nano Banana previews (see app/services/previews.py). Called by the concepts endpoints only,
        so creating a scenario never waits on image generation."""
        return attach_previews(concepts, scenario, lambda: self.client, self.image_model)

    # ------------------------------------------------------------------ FR-15 plan + repair
    def plan_scene(
        self,
        prompt: str,
        answers: dict[str, Any] | None = None,
        concept: dict[str, Any] | None = None,
        critique: list[dict[str, Any]] | None = None,
        attempt: int = 1,
    ) -> dict[str, Any]:
        if critique and self._last_spec is not None:
            contents = (
                f"{REPAIR_INSTRUCTION}\nErrors:\n{json.dumps(critique, indent=1)}\n"
                f"Current spec:\n{json.dumps(self._last_spec)}"
            )
            kind, temperature = "repair", 0.2
        else:
            chosen = {k: concept[k] for k in ("title", "summary", "tags") if k in concept} if concept else {}
            contents = (
                f"Tutor description: {prompt.strip()}\n"
                f"Tutor answers: {json.dumps(answers or {})}\n"
                f"Chosen concept: {json.dumps(chosen)}\n"
                "Return the scene spec."
            )
            kind, temperature = "plan", 0.5
        try:
            spec = self._json_call(kind, contents, SCENE_SCHEMA, temperature)
        except Exception as exc:
            # Returning a non-dict makes the validator raise R1, so the repair loop
            # records the failure honestly instead of silently using the mock scene.
            log.error("plan_scene attempt %s failed: %s", attempt, exc)
            spec = {"_error": str(exc)[:200]}
        self._last_spec = deepcopy(spec) if isinstance(spec, dict) else None
        return spec

    # ------------------------------------------------------------------ FR-08 plain-language edit
    def apply_plain_language_edit(self, spec: dict[str, Any], instruction: str) -> dict[str, Any]:
        contents = (
            "Turn the tutor's instruction into the smallest JSON Patch that achieves it. Only touch paths "
            "under /layout, /task, /support or /events. Encode each new value as JSON text in value_json. "
            "Keep comfort caps and monotone support rules.\n"
            f"Instruction: {instruction.strip()}\nScene: {json.dumps(spec)}"
        )
        try:
            result = self._json_call("patch", contents, PATCH_SCHEMA, temperature=0.2)
            ops = [_decode_op(op) for op in result["ops"]]
            patched = apply_patch(spec, ops)
        except Exception as exc:
            log.warning("edit fell back to rule-based editor: %s", exc)
            return self._fallback.apply_plain_language_edit(spec, instruction)

        spec_bytes = len(json.dumps(spec, separators=(",", ":")).encode())
        patch_bytes = sum(len(json.dumps(op.get("value"), separators=(",", ":")).encode()) for op in ops)
        return {
            "patched_spec": patched,
            "patch_ops": ops,
            "patch_bytes": patch_bytes,
            "spec_bytes": spec_bytes,
            "patch_ratio": round(patch_bytes / max(spec_bytes, 1), 4),
        }


# ---------------------------------------------------------------------- JSON Patch (subset)
def _decode_op(op: dict[str, Any]) -> dict[str, Any]:
    out = {"op": op["op"], "path": op["path"]}
    if op["op"] in ("add", "replace"):
        out["value"] = json.loads(op["value_json"])
    return out


def _pointer(path: str) -> list[str]:
    if not path.startswith("/") or not path.startswith(ALLOWED_PATCH_PREFIXES):
        raise ValueError(f"path not allowed: {path}")
    return [p.replace("~1", "/").replace("~0", "~") for p in path[1:].split("/")]


def apply_patch(spec: dict[str, Any], ops: list[dict[str, Any]]) -> dict[str, Any]:
    """Apply add/replace/remove ops to a copy. Raises on any invalid op."""
    doc = deepcopy(spec)
    for op in ops:
        parts = _pointer(op["path"])
        parent: Any = doc
        for key in parts[:-1]:
            parent = parent[int(key)] if isinstance(parent, list) else parent[key]
        last = parts[-1]
        if isinstance(parent, list):
            if op["op"] == "add":
                idx = len(parent) if last == "-" else int(last)
                parent.insert(idx, op["value"])
            elif op["op"] == "replace":
                parent[int(last)] = op["value"]
            else:
                del parent[int(last)]
        else:
            if op["op"] == "replace" and last not in parent:
                raise KeyError(f"cannot replace missing key {op['path']}")
            if op["op"] == "remove":
                del parent[last]
            else:
                parent[last] = op["value"]
    return doc
