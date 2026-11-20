"""Gemini Live voice intake: mint a short-lived, single-use token for the browser.

The real API key never leaves Cloud Run. The browser gets an ephemeral token (Live API only, v1beta)
that must open a session within one minute and expires after ten. No learner data is involved:
the token request carries nothing but the tutor's own JWT.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import os
import time

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_current_tutor
from app.models.tutor import Tutor

router = APIRouter(tags=["Voice intake"])
log = logging.getLogger("chyron.live")

_client = None


def _genai_client():
    """Created lazily so the API starts (and tests run) without google-genai credentials."""
    global _client
    if _client is None:
        from google import genai

        # Always the Gemini API with the server key (ephemeral tokens are not a Vertex AI feature),
        # even when the planner runs on Vertex AI via GOOGLE_GENAI_USE_VERTEXAI.
        key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        _client = genai.Client(vertexai=False, api_key=key, http_options={"api_version": "v1beta"})
    return _client


def live_intake_status() -> tuple[bool, str]:
    """Whether voice intake can be offered, and a plain-language reason when it cannot."""
    if os.getenv("DEMO_MODE") == "cache":
        return False, "Voice is off in offline demo mode. Please type the scenario."
    if not os.getenv("GEMINI_LIVE_MODEL"):
        return False, "Voice is not set up on this server. Please type the scenario."
    has_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not has_key or os.getenv("AI_PROVIDER", "mock") != "gemini":
        return False, "Voice is not set up on this server. Please type the scenario."
    return True, ""


@router.get("/live-token/status")
def live_token_status(tutor: Tutor = Depends(get_current_tutor)) -> dict:
    available, reason = live_intake_status()
    return {"available": available, "reason": reason}


@router.post("/live-token")
def live_token(tutor: Tutor = Depends(get_current_tutor)) -> dict:
    available, reason = live_intake_status()
    if not available:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=reason)

    model = os.environ["GEMINI_LIVE_MODEL"]
    now = dt.datetime.now(dt.timezone.utc)
    started = time.perf_counter()
    try:
        token = _genai_client().auth_tokens.create(
            config={
                "uses": 1,
                "expire_time": now + dt.timedelta(minutes=10),
                "new_session_expire_time": now + dt.timedelta(minutes=1),
            }
        )
    except Exception as exc:  # network, quota or credential problems: the UI falls back to typing
        log.warning(json.dumps({"event": "gemini_call", "kind": "live_token", "model": model, "ok": False,
                                "error": type(exc).__name__}))
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="Voice is unavailable right now. Please type the scenario.") from exc

    log.info(json.dumps({"event": "gemini_call", "kind": "live_token", "model": model, "ok": True,
                         "latency_ms": int((time.perf_counter() - started) * 1000)}))
    return {"token": token.name, "model": model, "expires_in_s": 600}
