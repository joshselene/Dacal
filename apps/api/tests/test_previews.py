"""Nano Banana concept previews: offline fakes only (no network, no key)."""

from __future__ import annotations

import os
from types import SimpleNamespace

from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "sqlite:///./dev.db")

from app.main import app  # noqa: E402
from app.services import previews  # noqa: E402
from app.services.ai_provider import MockAIProvider, with_preview_images  # noqa: E402

PNG = b"\x89PNG\r\n\x1a\nfake-image-bytes"
CONCEPTS = [
    {"id": "guided", "title": "Guided shop", "summary": "Clear steps."},
    {"id": "explore", "title": "Open market", "summary": "More choice."},
    {"id": "calm", "title": "Calm corner store", "summary": "Fewest people."},
]


class FakeImageModels:
    def __init__(self, fail: bool = False):
        self.prompts: list[str] = []
        self.fail = fail

    def generate_content(self, model, contents, config):
        self.prompts.append(contents)
        if self.fail:
            raise RuntimeError("quota")
        part = SimpleNamespace(inline_data=SimpleNamespace(data=PNG, mime_type="image/png"))
        return SimpleNamespace(candidates=[SimpleNamespace(content=SimpleNamespace(parts=[part]))])


def _env(monkeypatch, tmp_path, mode: str) -> None:
    monkeypatch.setenv("DEMO_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("GEMINI_PREVIEW_IMAGES", mode)
    monkeypatch.delenv("DEMO_MODE", raising=False)


def test_off_mode_and_mock_provider_leave_concepts_unchanged(monkeypatch, tmp_path):
    _env(monkeypatch, tmp_path, "off")
    models = FakeImageModels()
    out = previews.attach_previews(CONCEPTS, "kirana", lambda: SimpleNamespace(models=models), "img-model")
    assert out == CONCEPTS and models.prompts == []
    assert with_preview_images(MockAIProvider(), CONCEPTS, "kirana") == CONCEPTS


def test_inline_mode_three_parallel_images_with_safe_prompts(monkeypatch, tmp_path):
    _env(monkeypatch, tmp_path, "inline")
    models = FakeImageModels()
    out = previews.attach_previews(CONCEPTS, "Buy milk and bread with 200 rupees.", lambda: SimpleNamespace(models=models),
                                   "img-model")
    assert len(models.prompts) == 3
    assert all(c["preview_image"].startswith("data:image/png;base64,") for c in out)
    assert all(c["preview_label"] == "Concept preview" for c in out)
    assert all("no real people's faces" in p and "no text" in p for p in models.prompts)
    assert [c["id"] for c in out] == ["guided", "explore", "calm"]  # order preserved


def test_cache_replays_offline_with_no_model_calls(monkeypatch, tmp_path):
    _env(monkeypatch, tmp_path, "inline")
    previews.attach_previews(CONCEPTS, "kirana", lambda: SimpleNamespace(models=FakeImageModels()), "img-model")
    monkeypatch.setenv("DEMO_MODE", "cache")

    def no_network():
        raise AssertionError("must not create a client offline")

    out = previews.attach_previews(CONCEPTS, "kirana", no_network, "img-model")
    assert all("preview_image" in c for c in out)


def test_failures_never_block_and_gcs_mode_serves_from_api(monkeypatch, tmp_path):
    _env(monkeypatch, tmp_path, "inline")
    out = previews.attach_previews(CONCEPTS, "x", lambda: SimpleNamespace(models=FakeImageModels(fail=True)), "img-model")
    assert out == CONCEPTS

    _env(monkeypatch, tmp_path, "gcs")
    uploads = {}

    class FakeBlob:
        def __init__(self, name):
            self.name = name

        def upload_from_string(self, data, content_type):
            uploads[self.name] = (data, content_type)

    monkeypatch.setattr(previews, "_bucket", lambda: SimpleNamespace(blob=FakeBlob))
    out = previews.attach_previews(CONCEPTS, "kirana gcs", lambda: SimpleNamespace(models=FakeImageModels()), "img-model")
    urls = [c["preview_image"] for c in out]
    assert all(u.startswith("/api/v1/previews/") and u.endswith(".png") for u in urls)
    assert len(uploads) == 3 and all(name.startswith("previews/") for name in uploads)

    client = TestClient(app)
    res = client.get(urls[0])
    assert res.status_code == 200 and res.content == PNG and res.headers["content-type"] == "image/png"
    assert client.get("/api/v1/previews/not-a-key.png").status_code == 404
    assert client.get("/api/v1/previews/" + "0" * 32 + ".png").status_code == 404
