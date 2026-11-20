"""Nano Banana concept previews: one illustration per concept direction, generated in parallel.

Modes (GEMINI_PREVIEW_IMAGES):
  off     no images; the UI keeps its 3D/CSS fallback
  inline  data URLs stored with the concept (demo only: bloats the database)
  gcs     PNGs in gs://$BUCKET/previews/{key}.png, served by GET /api/v1/previews/{key}.png

Every generated image is also written to DEMO_CACHE_DIR, so DEMO_MODE=cache replays previews with no network.
Prompts are built from the concept and the tutor's scenario text only; no learner data is ever included.
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Callable

log = logging.getLogger("chyron.previews")

KEY_RE = re.compile(r"^[0-9a-f]{32}$")
SAFETY = (
    "Calm, uncluttered, soft lighting, low visual noise, no text, no logos, no real people's faces, "
    "suitable for learners with sensory sensitivities."
)
STYLE = {"guided": "soft flat illustration", "explore": "simple 3D clay render", "calm": "calm watercolor"}


def preview_mode() -> str:
    mode = os.getenv("GEMINI_PREVIEW_IMAGES", "off").strip().lower()
    return mode if mode in {"inline", "gcs"} else "off"


def preview_prompt(concept: dict[str, Any], scenario: str) -> str:
    style = STYLE.get(str(concept.get("id")), "soft flat illustration")
    return (
        f"Concept preview of a small practice shop for a life-skills lesson. Direction: {concept.get('title', '')}. "
        f"{concept.get('summary', '')} Scenario: {scenario.strip()[:400]} "
        "Show a grid-like shop floor with an entrance at the front, shelves with a few grocery items, and a checkout "
        f"counter. Style: {style}. {SAFETY}"
    )


def preview_key(model: str, prompt: str) -> str:
    return hashlib.sha256(f"{model}|{prompt}".encode()).hexdigest()[:32]


def _cache_dir() -> Path:
    return Path(os.getenv("DEMO_CACHE_DIR", "demo_cache")) / "previews"


def read_cached(key: str) -> bytes | None:
    path = _cache_dir() / f"{key}.png"
    return path.read_bytes() if path.exists() else None


def _write_cache(key: str, data: bytes) -> None:
    try:
        _cache_dir().mkdir(parents=True, exist_ok=True)
        (_cache_dir() / f"{key}.png").write_bytes(data)
    except OSError:
        pass  # read-only filesystem is fine; the cache is a demo aid


def _bucket() -> Any:
    from google.cloud import storage

    name = os.getenv("BUCKET")
    if not name:
        raise RuntimeError("BUCKET is not set")
    return storage.Client().bucket(name)


def read_stored(key: str) -> bytes | None:
    """Bytes for GET /previews/{key}.png: local cache first, then Cloud Storage."""
    if not KEY_RE.match(key):
        return None
    cached = read_cached(key)
    if cached is not None or os.getenv("DEMO_MODE") == "cache" or preview_mode() != "gcs":
        return cached
    try:
        blob = _bucket().blob(f"previews/{key}.png")
        return blob.download_as_bytes() if blob.exists() else None
    except Exception as exc:
        log.warning("preview download failed: %s", type(exc).__name__)
        return None


def _generate_bytes(client: Any, model: str, prompt: str) -> tuple[bytes, str] | None:
    from google.genai import types

    started = time.perf_counter()
    resp = client.models.generate_content(
        model=model, contents=prompt, config=types.GenerateContentConfig(response_modalities=["IMAGE"])
    )
    log.info(json.dumps({"event": "gemini_call", "kind": "preview_image", "model": model,
                         "latency_ms": round((time.perf_counter() - started) * 1000)}))
    for part in resp.candidates[0].content.parts:
        inline = getattr(part, "inline_data", None)
        if inline and inline.data:
            return inline.data, inline.mime_type or "image/png"
    return None


def attach_previews(concepts: list[dict[str, Any]], scenario: str, client_factory: Callable[[], Any],
                    model: str | None = None) -> list[dict[str, Any]]:
    """Add preview_image to each concept when enabled. Never raises: previews are optional."""
    mode = preview_mode()
    model = model or os.getenv("GEMINI_IMAGE_MODEL")
    if mode == "off" or not model or not concepts:
        return concepts
    offline = os.getenv("DEMO_MODE") == "cache"

    def one(concept: dict[str, Any]) -> dict[str, Any]:
        prompt = preview_prompt(concept, scenario)
        key = preview_key(model, prompt)
        data, mime = read_cached(key), "image/png"
        if data is None and not offline:
            try:
                made = _generate_bytes(client_factory(), model, prompt)
            except Exception as exc:
                log.warning("preview image skipped: %s", type(exc).__name__)
                made = None
            if made:
                data, mime = made
                _write_cache(key, data)
                if mode == "gcs":
                    try:
                        _bucket().blob(f"previews/{key}.png").upload_from_string(data, content_type=mime)
                    except Exception as exc:
                        log.warning("preview upload failed, using inline: %s", type(exc).__name__)
                        return {**concept, "preview_image": _data_url(data, mime), "preview_label": "Concept preview"}
        if data is None:
            return concept
        # In gcs mode the local cache (or the bucket) backs GET /api/v1/previews/{key}.png.
        url = f"/api/v1/previews/{key}.png" if mode == "gcs" else _data_url(data, mime)
        return {**concept, "preview_image": url, "preview_label": "Concept preview"}

    with ThreadPoolExecutor(max_workers=3) as pool:
        return list(pool.map(one, concepts))


def _data_url(data: bytes, mime: str) -> str:
    return f"data:{mime};base64,{base64.b64encode(data).decode()}"
