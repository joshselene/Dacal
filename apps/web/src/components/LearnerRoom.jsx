import React, { useEffect, useMemo, useRef, useState } from "react";
import { Volume2, VolumeX } from "../m3/icons.jsx";
import FourWallPreview from "./FourWallPreview";
import { guidanceFor, roomSpecFor } from "./roomGuidance";

const MUTE_KEY = "chyron-voice-muted";
const MAX_SPEECH_VOLUME = 80; // never louder than the highest comfort cap (pathway C)

function readMuted() {
  try { return localStorage.getItem(MUTE_KEY) === "1"; } catch { return false; }
}

function writeMuted(value) {
  try { localStorage.setItem(MUTE_KEY, value ? "1" : "0"); } catch { /* storage blocked: keep in memory only */ }
}

// Calm, capped speech. Browser TTS cannot ramp volume mid-utterance, so each prompt starts at the
// pathway's capped level after a short pause instead of cutting in at full volume.
export function speakPrompt(text, volumePercent) {
  const synth = typeof window !== "undefined" ? window.speechSynthesis : null;
  if (!synth || !text || typeof SpeechSynthesisUtterance === "undefined") return;
  synth.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.volume = Math.max(0, Math.min(volumePercent, MAX_SPEECH_VOLUME)) / 100;
  utterance.rate = .9;
  utterance.pitch = 1;
  utterance.lang = "en-IN";
  const voice = synth.getVoices().find((entry) => entry.lang === "en-IN") || synth.getVoices().find((entry) => entry.lang?.startsWith("en"));
  if (voice) utterance.voice = voice;
  setTimeout(() => synth.speak(utterance), 250);
}

function stopSpeech() {
  try { window.speechSynthesis?.cancel(); } catch { /* no speech support */ }
}

/**
 * Learner room: the validated spec rendered by FourWallPreview, plus pathway guidance.
 * A = highlight + floor arrows + spoken next step; B = highlight, speech on tutor prompt; C = speech on tutor prompt only.
 */
export default function LearnerRoom({ spec, run, onCommand }) {
  const [muted, setMuted] = useState(readMuted);
  // Every command returns a fresh run object; key the room on content so moves don't rebuild the 3D scene.
  const merged = roomSpecFor(spec, run);
  const roomKey = JSON.stringify([merged?.room, merged?.layout, merged?.task]);
  const roomSpec = useMemo(() => merged, [roomKey]); // eslint-disable-line react-hooks/exhaustive-deps
  const guidance = useMemo(() => guidanceFor(roomSpec, run, run.pathway), [roomSpec, run]);
  const paused = run.status === "paused";
  const completed = run.status === "completed";
  const atTarget = guidance.path.length === 1;
  const spokenKey = useRef(null);
  const lastPrompts = useRef(run.prompts_given || 0);

  // Pathway A speaks when the goal changes or the learner arrives next to it, not on every step.
  useEffect(() => {
    const key = completed ? "done" : `${run.pathway}|${guidance.targetId}|${guidance.target?.sku}|${atTarget}`;
    if (key === spokenKey.current) return;
    spokenKey.current = key;
    if (muted || paused) return;
    if (guidance.level === "full") speakPrompt(guidance.text, guidance.volume);
  }, [completed, run.pathway, guidance.targetId, atTarget, guidance.level, guidance.text, guidance.volume, muted, paused]);

  // A tutor "Give prompt" is spoken in every pathway.
  useEffect(() => {
    const count = run.prompts_given || 0;
    if (count > lastPrompts.current && !muted && !paused) speakPrompt(guidance.text, guidance.volume);
    lastPrompts.current = count;
  }, [run.prompts_given, guidance.text, guidance.volume, muted, paused]);

  useEffect(() => { if (paused || muted) stopSpeech(); }, [paused, muted]);
  useEffect(() => stopSpeech, []);

  function toggleMuted() {
    setMuted((value) => { writeMuted(!value); return !value; });
  }

  const muteButton = (
    <button type="button" className="icon-button" aria-pressed={muted} onClick={toggleMuted}
      aria-label={muted ? "Turn on spoken prompts" : "Mute spoken prompts"} title={muted ? "Turn on spoken prompts" : "Mute spoken prompts"}>
      {muted ? <VolumeX size={28} /> : <Volume2 size={28} />}
    </button>
  );

  return (
    <FourWallPreview
      spec={roomSpec}
      pathway={run.pathway}
      displayMode={run.mode}
      paused={paused}
      learnerPosition={run.learner_position}
      interactiveKeyboard={!completed}
      guidance={completed ? null : guidance}
      controlsExtra={muteButton}
      onMove={(dir) => onCommand("move", { dir })}
      onSelect={() => onCommand("select", {})}
      onPause={() => onCommand(paused ? "resume" : "pause")}
    />
  );
}
