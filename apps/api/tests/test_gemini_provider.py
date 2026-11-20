"""Offline tests for GeminiAIProvider using a fake google-genai client.

No network and no API key needed. They prove that the Gemini path plugs into
the existing Plan-Validate-Build loop and the R1-R7 validator.
"""

from __future__ import annotations

from copy import deepcopy
import json
from types import SimpleNamespace

import pytest

from app.services.ai_provider import generate_with_repair_loop, get_ai_provider
from app.services.gemini_provider import GeminiAIProvider, apply_patch
from app.services.validator import get_reference_scene_spec, validate_scene_spec


class FakeModels:
    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []

    def generate_content(self, model, contents, config):
        self.calls.append({"model": model, "contents": contents, "config": config})
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        usage = SimpleNamespace(prompt_token_count=900, candidates_token_count=400, cached_content_token_count=600)
        return SimpleNamespace(text=json.dumps(reply), usage_metadata=usage)


def provider_with(replies, tmp_path, monkeypatch):
    monkeypatch.delenv("DEMO_MODE", raising=False)
    monkeypatch.setenv("DEMO_CACHE_DIR", str(tmp_path))
    fake = SimpleNamespace(models=FakeModels(replies))
    return GeminiAIProvider(client=fake, model="test-flash"), fake.models


def broken_spec():
    spec = get_reference_scene_spec()
    spec["support"]["A"]["volume"] = 90  # R5 and R6
    spec["task"]["budget"] = 10  # R4
    return spec


def test_factory_returns_gemini(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "gemini")
    assert get_ai_provider().name == "gemini"


def test_repair_loop_fixes_scene_on_second_attempt(tmp_path, monkeypatch):
    provider, models = provider_with([broken_spec(), get_reference_scene_spec()], tmp_path, monkeypatch)
    result = generate_with_repair_loop("Buy milk and bread at a kirana shop", provider=provider)

    assert result["success"] is True
    assert result["attempts"] == 2
    assert validate_scene_spec(result["spec"])["valid"]
    # Second call is a repair that carries the validator critique and the previous spec
    repair_prompt = models.calls[1]["contents"]
    assert "REPAIR" in repair_prompt and "R4" in repair_prompt
    # Structured output is requested on every call
    assert models.calls[0]["config"].response_mime_type == "application/json"
    assert models.calls[0]["config"].response_json_schema["title"] == "Chyron shop scene spec"
    assert provider.usage[0]["input_tokens"] == 900


def test_repair_loop_stops_after_three_attempts(tmp_path, monkeypatch):
    provider, _ = provider_with([broken_spec()] * 3, tmp_path, monkeypatch)
    result = generate_with_repair_loop("Unsolvable", provider=provider)
    assert result["success"] is False and result["attempts"] == 3
    assert result["spec"] is None and "could not build" in result["error_plain"]


def test_network_error_is_recorded_not_hidden(tmp_path, monkeypatch):
    provider, _ = provider_with([RuntimeError("quota")] * 3, tmp_path, monkeypatch)
    result = generate_with_repair_loop("Anything", provider=provider)
    assert result["success"] is False  # never silently swaps in the mock scene
    assert "could not reach the scene planner" in result["error_plain"]


def test_failed_call_replans_from_tutor_description(tmp_path, monkeypatch):
    # Regression: after a 429 the next attempt used to "repair" the error stub without the tutor's
    # description, so Gemini invented an unrelated shop that still passed R1-R7.
    provider, models = provider_with([RuntimeError("429 RESOURCE_EXHAUSTED"), get_reference_scene_spec()],
                                     tmp_path, monkeypatch)
    result = generate_with_repair_loop("Buy milk and bread at a kirana shop with 200 rupees", provider=provider)
    assert result["success"] is True and result["attempts"] == 2
    second = models.calls[1]["contents"]
    assert "Tutor description: Buy milk and bread at a kirana shop with 200 rupees" in second
    assert "_error" not in second  # re-planned, not a repair of the error stub


def test_repair_prompt_keeps_tutor_description(tmp_path, monkeypatch):
    provider, models = provider_with([broken_spec(), get_reference_scene_spec()], tmp_path, monkeypatch)
    generate_with_repair_loop("Buy milk and bread at a kirana shop", provider=provider)
    assert "Buy milk and bread at a kirana shop" in models.calls[1]["contents"]


def test_demo_cache_replays_without_network(tmp_path, monkeypatch):
    provider, _ = provider_with([get_reference_scene_spec()], tmp_path, monkeypatch)
    first = provider.plan_scene("Buy milk")
    monkeypatch.setenv("DEMO_MODE", "cache")
    offline, models = provider_with([], tmp_path, monkeypatch)
    monkeypatch.setenv("DEMO_MODE", "cache")
    assert offline.plan_scene("Buy milk") == first
    assert models.calls == []


def test_concepts_and_fallback(tmp_path, monkeypatch):
    concepts = [
        {"id": i, "title": f"T{i}", "summary": "s", "environment": "Shop", "visual_style": "Soft 3D", "tags": ["x"]}
        for i in ("guided", "explore", "calm")
    ]
    provider, _ = provider_with([concepts, RuntimeError("down")], tmp_path, monkeypatch)
    got = provider.generate_concepts("Buy fruit")
    assert [c["preview_art"] for c in got] == ["art-guided", "art-explore", "art-calm"]
    fallback = provider.generate_concepts("Buy something else")
    assert len(fallback) == 3  # mock concepts keep the tutor moving


def test_plain_language_edit_applies_small_patch(tmp_path, monkeypatch):
    patch = {"ops": [{"op": "replace", "path": "/support/A/volume", "value_json": "25"}]}
    provider, _ = provider_with([patch], tmp_path, monkeypatch)
    spec = get_reference_scene_spec()
    res = provider.apply_plain_language_edit(spec, "Make the calm pathway quieter")
    assert res["patched_spec"]["support"]["A"]["volume"] == 25
    assert res["patch_ratio"] < 0.1
    assert validate_scene_spec(res["patched_spec"])["valid"]
    assert spec["support"]["A"]["volume"] == 40  # original untouched


def test_patch_rejects_paths_outside_allowed_areas():
    with pytest.raises(ValueError):
        apply_patch(get_reference_scene_spec(), [{"op": "replace", "path": "/room/w", "value": 3}])


def test_patch_add_to_list():
    spec = get_reference_scene_spec()
    out = apply_patch(spec, [{"op": "add", "path": "/task/required/-", "value": "apple"}])
    assert out["task"]["required"][-1] == "apple" and "apple" not in spec["task"]["required"]
    assert validate_scene_spec(deepcopy(out))["valid"]
