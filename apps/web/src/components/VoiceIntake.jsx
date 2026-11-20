import React, { useEffect, useRef, useState } from "react";
import { classWorkspaceApi } from "../classWorkspaceApi.js";

// Gemini Live voice intake. The tutor speaks a scenario; Gemini asks at most two short questions,
// then calls submit_scenario. The result only fills the authoring form: the normal
// plan -> validate (R1-R7) -> build path still decides what gets built.

const INTAKE_PROMPT = `You help a special-education tutor describe a practice scenario for CHYRON, which builds calm 3D shop rooms.
Supported settings are shops: a kirana store, bakery, pharmacy counter or vegetable stall. If the tutor asks for something else, suggest the closest shop version.
Listen to the tutor. Ask at most two short questions, and only if the shop type, the items to buy, the budget or the comfort level is unclear.
Comfort level means how calm the room should be: low (very calm, few people), medium, or high (busier).
Then call submit_scenario with a one-paragraph description in plain English: the shop, the items to buy, the budget in rupees, and paying at the counter.
Never ask for a learner's name, diagnosis, age or any personal detail. If the tutor mentions any, leave them out of the description.
Keep your spoken replies short and friendly.`;

const SUBMIT_TOOL = {
  name: "submit_scenario",
  description: "Submit the finished shop scenario so CHYRON can plan the practice room.",
  parameters: {
    type: "OBJECT",
    required: ["description", "comfort_profile"],
    properties: {
      description: { type: "STRING", description: "One plain-English paragraph: shop, items, budget, pay at counter. No learner details." },
      comfort_profile: { type: "STRING", enum: ["low", "medium", "high"] },
    },
  },
};

const INPUT_RATE = 16000;
const OUTPUT_RATE = 24000;

// AudioWorklet: batches ~100 ms of mono float samples and posts them to the main thread.
const CAPTURE_WORKLET = `
class Capture extends AudioWorkletProcessor {
  constructor() { super(); this.buffer = []; this.size = Math.round(sampleRate / 10); }
  process(inputs) {
    const channel = inputs[0] && inputs[0][0];
    if (channel) {
      for (let i = 0; i < channel.length; i += 1) this.buffer.push(channel[i]);
      if (this.buffer.length >= this.size) { this.port.postMessage(new Float32Array(this.buffer)); this.buffer = []; }
    }
    return true;
  }
}
registerProcessor("chyron-capture", Capture);`;

function floatToPcmBase64(samples) {
  const bytes = new Uint8Array(samples.length * 2);
  const view = new DataView(bytes.buffer);
  for (let i = 0; i < samples.length; i += 1) {
    const s = Math.max(-1, Math.min(1, samples[i]));
    view.setInt16(i * 2, s < 0 ? s * 0x8000 : s * 0x7fff, true);
  }
  let binary = "";
  for (let i = 0; i < bytes.length; i += 0x8000) binary += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
  return btoa(binary);
}

function pcmBase64ToFloat(data) {
  const binary = atob(data);
  const view = new DataView(new ArrayBuffer(binary.length));
  for (let i = 0; i < binary.length; i += 1) view.setUint8(i, binary.charCodeAt(i));
  const out = new Float32Array(binary.length / 2);
  for (let i = 0; i < out.length; i += 1) out[i] = view.getInt16(i * 2, true) / 0x8000;
  return out;
}

export default function VoiceIntake({ onSubmit, onStatus }) {
  const [available, setAvailable] = useState(null); // null = checking
  const [reason, setReason] = useState("");
  const [state, setState] = useState("idle"); // idle | connecting | listening
  const [lines, setLines] = useState([]);
  const live = useRef({});

  useEffect(() => {
    let cancelled = false;
    classWorkspaceApi.getLiveStatus()
      .then((res) => { if (!cancelled) { setAvailable(Boolean(res?.available)); setReason(res?.reason || ""); } })
      .catch(() => { if (!cancelled) { setAvailable(false); setReason("Voice is unavailable right now. Please type the scenario."); } });
    return () => { cancelled = true; stop(); };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  function addText(speaker, text) {
    if (!text) return;
    setLines((current) => {
      const last = current[current.length - 1];
      if (last && last.speaker === speaker && !last.done) return [...current.slice(0, -1), { ...last, text: last.text + text }];
      return [...current.map((line) => ({ ...line, done: true })), { speaker, text: text.trimStart(), done: false }];
    });
  }

  function playAudio(data) {
    const ctx = live.current.output;
    if (!ctx) return;
    const samples = pcmBase64ToFloat(data);
    const buffer = ctx.createBuffer(1, samples.length, OUTPUT_RATE);
    buffer.copyToChannel(samples, 0);
    const source = ctx.createBufferSource();
    source.buffer = buffer;
    source.connect(live.current.gain);
    const startAt = Math.max(ctx.currentTime + .05, live.current.playhead || 0);
    source.start(startAt);
    live.current.playhead = startAt + buffer.duration;
    live.current.sources.add(source);
    source.onended = () => live.current.sources?.delete(source);
  }

  function stopPlayback() {
    live.current.sources?.forEach((source) => { try { source.stop(); } catch { /* already stopped */ } });
    live.current.sources?.clear();
    live.current.playhead = 0;
  }

  function stop() {
    const current = live.current;
    live.current = {};
    try { current.session?.close(); } catch { /* closed */ }
    current.stream?.getTracks().forEach((track) => track.stop());
    current.input?.close().catch(() => {});
    current.output?.close().catch(() => {});
    setState("idle");
  }

  function fail(message) {
    stop();
    onStatus?.(message);
  }

  function transcriptText() {
    return linesRef.current.map((line) => `${line.speaker === "tutor" ? "Tutor" : "Gemini"}: ${line.text.trim()}`).join("\n");
  }
  const linesRef = useRef(lines);
  useEffect(() => { linesRef.current = lines; }, [lines]);

  function handleMessage(message) {
    const content = message.serverContent;
    if (content?.interrupted) stopPlayback();
    if (content?.inputTranscription?.text) addText("tutor", content.inputTranscription.text);
    if (content?.outputTranscription?.text) addText("gemini", content.outputTranscription.text);
    for (const part of content?.modelTurn?.parts || []) if (part.inlineData?.data) playAudio(part.inlineData.data);
    if (content?.turnComplete) setLines((current) => current.map((line) => ({ ...line, done: true })));
    const calls = message.toolCall?.functionCalls || [];
    const submit = calls.find((call) => call.name === "submit_scenario");
    if (calls.length) {
      live.current.session?.sendToolResponse({
        functionResponses: calls.map((call) => ({ id: call.id, name: call.name, response: { result: call.name === "submit_scenario" ? "Submitted. Say a short goodbye." : "Unknown tool." } })),
      });
    }
    if (submit) {
      const args = submit.args || {};
      const profile = ["low", "medium", "high"].includes(args.comfort_profile) ? args.comfort_profile : "low";
      onSubmit?.({ description: String(args.description || "").trim(), comfortProfile: profile, transcript: transcriptText() });
      setTimeout(stop, 2500); // let the goodbye finish
    }
  }

  async function start() {
    if (state !== "idle") return;
    if (!navigator.mediaDevices?.getUserMedia || typeof AudioWorkletNode === "undefined") {
      onStatus?.("This browser cannot record audio. Please type the scenario.");
      return;
    }
    setState("connecting");
    setLines([]);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true } })
        .catch(() => { throw new Error("Microphone permission was blocked. Please type the scenario."); });
      live.current.stream = stream;
      const { token, model } = await classWorkspaceApi.getLiveToken();
      const { GoogleGenAI, Modality } = await import("@google/genai");
      const ai = new GoogleGenAI({ apiKey: token, httpOptions: { apiVersion: "v1beta" } });

      const output = new AudioContext({ sampleRate: OUTPUT_RATE });
      const gain = output.createGain();
      gain.gain.value = .8;
      gain.connect(output.destination);
      Object.assign(live.current, { output, gain, sources: new Set(), playhead: 0 });

      const session = await ai.live.connect({
        model,
        config: {
          responseModalities: [Modality.AUDIO],
          inputAudioTranscription: {},
          outputAudioTranscription: {},
          systemInstruction: INTAKE_PROMPT,
          tools: [{ functionDeclarations: [SUBMIT_TOOL] }],
        },
        callbacks: {
          onmessage: handleMessage,
          onerror: () => fail("Voice connection had a problem. Please type the scenario, or try again."),
          onclose: () => { if (live.current.session) stop(); },
        },
      });
      live.current.session = session;

      const input = new AudioContext({ sampleRate: INPUT_RATE });
      live.current.input = input;
      const moduleUrl = URL.createObjectURL(new Blob([CAPTURE_WORKLET], { type: "application/javascript" }));
      await input.audioWorklet.addModule(moduleUrl);
      URL.revokeObjectURL(moduleUrl);
      const node = new AudioWorkletNode(input, "chyron-capture");
      node.port.onmessage = (event) => {
        live.current.session?.sendRealtimeInput({ audio: { data: floatToPcmBase64(event.data), mimeType: `audio/pcm;rate=${input.sampleRate}` } });
      };
      input.createMediaStreamSource(stream).connect(node);
      setState("listening");
      onStatus?.("Listening. Describe the shop, what to buy and the budget.");
    } catch (error) {
      fail(error?.message || "Voice is unavailable right now. Please type the scenario.");
    }
  }

  if (available === false) return <p className="voice-intake-note">{reason}</p>;

  return (
    <div className="voice-live">
      <button type="button" className={state === "listening" ? "primary-button" : "secondary-button"}
        aria-pressed={state === "listening"} disabled={available === null || state === "connecting"}
        onClick={state === "listening" ? stop : start}>
        {state === "listening" ? "■ Stop speaking" : state === "connecting" ? "Connecting…" : "🎙 Speak scenario (Gemini Live)"}
      </button>
      {lines.length > 0 && (
        <ol className="voice-live-lines" aria-live="polite" aria-label="Live voice conversation">
          {lines.map((line, index) => (
            <li key={index} className={`voice-line voice-line-${line.speaker}`}>
              <strong>{line.speaker === "tutor" ? "You" : "Gemini"}</strong> {line.text}
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}
