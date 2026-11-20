"""Synthesize the narration with Google Cloud Text-to-Speech (Chirp 3 HD), one clip per sentence.

Usage: python tts.py OUT_DIR
Auth: a gcloud access token (gcloud auth print-access-token) for the project in GOOGLE_CLOUD_PROJECT.
Writes OUT_DIR/{scene}_{n}.wav (24 kHz mono LINEAR16) and OUT_DIR/timeline.json with per-sentence durations.
"""

from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
import urllib.request
import wave
from pathlib import Path

HERE = Path(__file__).parent


def token() -> str:
    return subprocess.check_output(["gcloud", "auth", "print-access-token"], text=True).strip()


def synth(text: str, cfg: dict, tok: str, project: str) -> bytes:
    body = {
        "input": {"text": text},
        "voice": {"languageCode": cfg["language"], "name": cfg["voice"]},
        "audioConfig": {"audioEncoding": "LINEAR16", "sampleRateHertz": 24000, "speakingRate": cfg["speaking_rate"]},
    }
    req = urllib.request.Request(
        "https://texttospeech.googleapis.com/v1/text:synthesize",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {tok}", "x-goog-user-project": project, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return base64.b64decode(json.load(resp)["audioContent"])


def main(out: Path) -> None:
    cfg = json.loads((HERE / "narration.json").read_text())
    project = os.environ.get("GOOGLE_CLOUD_PROJECT", "chyron-buildathon-70138")
    tok = token()
    out.mkdir(parents=True, exist_ok=True)
    timeline = []
    for scene in cfg["scenes"]:
        lines = []
        for n, text in enumerate(scene["lines"]):
            path = out / f"{scene['id']}_{n}.wav"
            if not path.exists():
                path.write_bytes(synth(text, cfg, tok, project))
            with wave.open(str(path)) as w:
                dur = w.getnframes() / w.getframerate()
            lines.append({"text": text, "file": path.name, "duration": round(dur, 3)})
        timeline.append({"id": scene["id"], "visual": scene["visual"], "lines": lines})
        print(scene["id"], round(sum(l["duration"] for l in lines), 1), "s")
    (out / "timeline.json").write_text(json.dumps({"config": cfg, "scenes": timeline}, indent=1))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
