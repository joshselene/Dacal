"""Voice intake token endpoint: auth required, honest fallbacks, and the key never reaches the browser."""

from __future__ import annotations

import os
from types import SimpleNamespace

from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "sqlite:///./dev.db")

from app.main import app  # noqa: E402
from app.routers import live  # noqa: E402

client = TestClient(app)


def _headers() -> dict[str, str]:
    suffix = os.urandom(4).hex()
    res = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"voice_{suffix}@school.org",
            "password": "SafePassword123!",
            "full_name": "Voice Tutor",
            "organisation_name": f"Voice School {suffix}",
            "role": "tutor",
            "local_hour": 10,
        },
    )
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def test_live_token_requires_login():
    assert client.post("/api/v1/live-token").status_code == 401


def test_live_token_unavailable_offline_and_unconfigured(monkeypatch):
    headers = _headers()
    monkeypatch.setenv("DEMO_MODE", "cache")
    monkeypatch.setenv("GEMINI_LIVE_MODEL", "live-model")
    res = client.post("/api/v1/live-token", headers=headers)
    assert res.status_code == 503 and "type" in res.json()["detail"]
    assert client.get("/api/v1/live-token/status", headers=headers).json()["available"] is False

    monkeypatch.delenv("DEMO_MODE")
    monkeypatch.setenv("AI_PROVIDER", "mock")
    assert client.post("/api/v1/live-token", headers=headers).status_code == 503


def test_live_token_mints_single_use_ephemeral_token(monkeypatch):
    headers = _headers()
    calls = []

    class FakeTokens:
        def create(self, config):
            calls.append(config)
            return SimpleNamespace(name="auth_tokens/ephemeral-123")

    monkeypatch.delenv("DEMO_MODE", raising=False)
    monkeypatch.setenv("AI_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "server-secret-key")
    monkeypatch.setenv("GEMINI_LIVE_MODEL", "live-model")
    monkeypatch.setattr(live, "_client", SimpleNamespace(auth_tokens=FakeTokens()))

    res = client.post("/api/v1/live-token", headers=headers)
    assert res.status_code == 200
    body = res.json()
    assert body == {"token": "auth_tokens/ephemeral-123", "model": "live-model", "expires_in_s": 600}
    assert "server-secret-key" not in res.text
    assert calls[0]["uses"] == 1
    assert calls[0]["new_session_expire_time"] < calls[0]["expire_time"]


def test_live_token_upstream_failure_is_plain_language(monkeypatch):
    headers = _headers()

    class BrokenTokens:
        def create(self, config):
            raise RuntimeError("quota")

    monkeypatch.delenv("DEMO_MODE", raising=False)
    monkeypatch.setenv("AI_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "k")
    monkeypatch.setenv("GEMINI_LIVE_MODEL", "live-model")
    monkeypatch.setattr(live, "_client", SimpleNamespace(auth_tokens=BrokenTokens()))
    res = client.post("/api/v1/live-token", headers=headers)
    assert res.status_code == 503
    assert res.json()["detail"] == "Voice is unavailable right now. Please type the scenario."
