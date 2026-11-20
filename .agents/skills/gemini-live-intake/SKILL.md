---
name: gemini-live-intake
description: Voice intake for tutors using the Gemini Live API. The tutor speaks a scenario, Gemini asks at most two clarifying questions, then calls a submit_scenario tool that feeds the scene planner. Covers ephemeral tokens minted on Cloud Run, the browser Live session, and fallbacks. Use for any microphone, speech or Live API work.
---

# Gemini Live voice intake

Tutors are busy and often standing in a classroom, so speaking a scenario is faster than typing one. It also shows a second, distinct Google AI capability. **It is a stretch goal**: build it only after the main demo path works, and keep the text box as the default.

## Flow

```text
Tutor taps the mic → browser asks /api/live-token → Cloud Run mints an ephemeral token
→ browser opens a Live session (model from GEMINI_LIVE_MODEL) with that token
→ Gemini listens, asks up to 2 short clarifying questions (setting? comfort profile?)
→ Gemini calls tool submit_scenario({description, comfort_profile})
→ browser fills the authoring form: prompt = description, voice_transcript = full transcript,
  answers.comfort_profile = profile → POST /api/v1/scenarios (ScenarioCreateRequest already has
  voice_transcript) → concepts → generate → the normal plan → validate → build path
```

## Server: mint a short-lived token (never ship the API key to the browser)

```python
# apps/api/app/routers/live.py  (mount at /api/v1, reuse the existing JWT dependency)
import datetime as dt, os
from google import genai

client = genai.Client(http_options={"api_version": "v1alpha"})

@router.post("/live-token")
def live_token(tutor=Depends(get_current_tutor)):        # existing JWT dependency in app/dependencies.py
    now = dt.datetime.now(dt.timezone.utc)
    tok = client.auth_tokens.create(config={
        "uses": 1,
        "expire_time": now + dt.timedelta(minutes=10),
        "new_session_expire_time": now + dt.timedelta(minutes=1),
        "http_options": {"api_version": "v1alpha"},
    })
    return {"token": tok.name, "model": os.environ["GEMINI_LIVE_MODEL"]}
```

## Browser: connect with `@google/genai`

```jsx
import { GoogleGenAI, Modality, Type } from "@google/genai";

// npm --prefix apps/web i @google/genai   (component: apps/web/src/components/VoiceIntake.jsx)
const { data: { token, model } } = await axios.post(`${API_BASE}/live-token`, {}, authHeaders());
const ai = new GoogleGenAI({ apiKey: token, httpOptions: { apiVersion: "v1alpha" } });

const session = await ai.live.connect({
  model,
  config: {
    responseModalities: [Modality.AUDIO],
    inputAudioTranscription: {},            // show the tutor's words live on screen
    outputAudioTranscription: {},
    systemInstruction: INTAKE_PROMPT,
    tools: [{ functionDeclarations: [{
      name: "submit_scenario",
      description: "Submit the finished scenario for scene planning",
      parameters: { type: Type.OBJECT, required: ["description", "comfort_profile"], properties: {
        description: { type: Type.STRING },
        comfort_profile: { type: Type.STRING, enum: ["low", "medium", "high"] },
      }},
    }]}],
  },
  callbacks: { onmessage: handleLiveMessage, onerror: fallbackToText, onclose: stopMic },
});
// Stream 16 kHz mono PCM from an AudioWorklet with session.sendRealtimeInput({ audio: {...} })
```

The ephemeral-token API and its field names have changed between SDK versions. Confirm them against the current page at ai.google.dev/gemini-api/docs/live-api/ephemeral-tokens before you build.

## INTAKE_PROMPT essentials

- You help a special-education tutor describe a practice scenario. Ask at most two short questions, only if the setting or comfort profile is unclear.
- Then call `submit_scenario` with a one-paragraph description in plain English.
- Never ask about a learner's name, diagnosis or personal details. If the tutor offers them, leave them out of the description.

## Fallbacks

- Microphone permission denied, Live error or no network: show the text box, with the transcript so far pre-filled.
- On stage, use a headset microphone, because the venue will be noisy. Rehearse the exact sentence you will speak.
