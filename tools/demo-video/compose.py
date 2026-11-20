"""Edit the CHYRON product video: narration-timed scenes, crossfades, captions, labels, ducked Lyria score.

Usage: python compose.py WORK_DIR OUT.mp4
WORK_DIR holds: vo/ (tts.py), music/part1..6.wav (Lyria), art/{hook,tutor,close}.png (Nano Banana),
footage/segments.json (record.mjs), cardsfoot/segments.json (optional card re-take), fonts/RobotoFlex.ttf.
FFMPEG env var points at an ffmpeg binary (default: imageio_ffmpeg's static build).
"""

from __future__ import annotations

import json
import os
import struct
import subprocess
import sys
import wave
from pathlib import Path

W, H, FPS = 1920, 1080, 30
XD = 0.6           # crossfade length (s)
OPEN, END = 7.0, 9.5
GAP, TAIL = 0.45, 2.4
LABELS = {
    "describe": "Plain words or voice  ·  Gemini Live",
    "concepts": "Gemini concepts  ·  Nano Banana previews",
    "safety": "Deterministic R1–R7 validator  ·  repair loop, k = 3",
    "configure": "Plain-language edit  →  small JSON patch  ·  new version",
    "room": "Three.js room  ·  laptop or four projected walls",
    "console": "Tutor console  ·  counts and times only",
}
CARD_TITLES = {
    "hook": ("The everyday\\Ncan feel enormous.", ""),
    "close": ("CHYRON", "Gemini proposes. Rules decide. Learners practise."),
}


def ffmpeg() -> str:
    if os.getenv("FFMPEG"):
        return os.environ["FFMPEG"]
    import imageio_ffmpeg

    return imageio_ffmpeg.get_ffmpeg_exe()


def run(args: list[str]) -> None:
    subprocess.run([ffmpeg(), "-hide_banner", "-loglevel", "error", "-y", *args], check=True)


def wav_frames(path: Path) -> tuple[bytes, int]:
    with wave.open(str(path)) as w:
        assert w.getnchannels() == 1 and w.getsampwidth() == 2
        return w.readframes(w.getnframes()), w.getframerate()


def silence(seconds: float, rate: int) -> bytes:
    return b"\x00\x00" * int(round(seconds * rate))


# ------------------------------------------------------------------ timeline
def build_timeline(work: Path) -> tuple[list[dict], float]:
    tl = json.loads((work / "vo" / "timeline.json").read_text())
    clips = [{"id": "opening", "visual": "card:opening", "dur": OPEN, "lines": []}]
    for scene in tl["scenes"]:
        speech = sum(l["duration"] for l in scene["lines"]) + GAP * (len(scene["lines"]) - 1)
        clips.append({"id": scene["id"], "visual": scene["visual"], "dur": round(speech + TAIL, 3), "lines": scene["lines"]})
    clips.append({"id": "end", "visual": "card:end", "dur": END, "lines": []})
    t = 0.0
    for clip in clips:
        clip["start"] = round(t, 3)
        t += clip["dur"]
    return clips, round(t, 3)


# ------------------------------------------------------------------ voice-over track
def build_vo(work: Path, clips: list[dict], total: float, out: Path) -> None:
    rate = 24000
    pcm = bytearray()
    for clip in clips:
        start_len = len(pcm)
        for n, line in enumerate(clip["lines"]):
            data, r = wav_frames(work / "vo" / line["file"])
            assert r == rate
            line["t0"] = clip["start"] + (len(pcm) - start_len) / 2 / rate
            pcm += data
            line["t1"] = clip["start"] + (len(pcm) - start_len) / 2 / rate
            if n < len(clip["lines"]) - 1:
                pcm += silence(GAP, rate)
        target = int(round(clip["dur"] * rate)) * 2
        pcm += b"\x00" * max(0, target - (len(pcm) - start_len))
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate); w.writeframes(bytes(pcm))


# ------------------------------------------------------------------ footage -> clips
def footage_segments(work: Path) -> dict[str, list[dict]]:
    """Segments grouped by scene, in recording order. A card re-take (cardsfoot/) replaces that card."""
    by_scene: dict[str, list[dict]] = {}
    for seg in json.loads((work / "footage" / "segments.json").read_text()):
        by_scene.setdefault(seg["scene"], []).append(seg)
    retake = work / "cardsfoot" / "segments.json"
    if retake.exists():
        fresh: dict[str, list[dict]] = {}
        for seg in json.loads(retake.read_text()):
            fresh.setdefault(seg["scene"], []).append(seg)
        by_scene.update(fresh)
    return by_scene


def segments_to_video(segs: list[dict], out: Path, tmp: Path) -> float:
    lines, total = [], 0.0
    for seg in segs:
        frames = seg["frames"]
        for i, fr in enumerate(frames):
            nxt = frames[i + 1]["t"] if i + 1 < len(frames) else seg["end"]
            dur = max(1 / 120, nxt - fr["t"])
            lines += [f"file '{fr['file']}'", f"duration {dur:.4f}"]
            total += dur
    lines.append(f"file '{segs[-1]['frames'][-1]['file']}'")
    listing = tmp / (out.stem + ".txt")
    listing.write_text("\n".join(lines))
    run(["-f", "concat", "-safe", "0", "-i", str(listing), "-vf", f"scale={W}:{H}:flags=lanczos,fps={FPS},format=yuv420p",
         "-c:v", "libx264", "-preset", "medium", "-crf", "16", str(out)])
    return total


def fit(src: Path, src_len: float, target: float, out: Path) -> None:
    """Retime footage to the narration: gentle speed change, then hold the last frame or trim."""
    speed = src_len / target
    speed = min(max(speed, 0.78), 1.55)
    new_len = src_len / speed
    pad = max(0.0, target - new_len + 0.05)
    vf = f"setpts=PTS/{speed:.5f},tpad=stop_mode=clone:stop_duration={pad:.3f},trim=duration={target:.3f},setpts=PTS-STARTPTS,fps={FPS},format=yuv420p"
    run(["-i", str(src), "-vf", vf, "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "16", str(out)])


def ken_burns(image: Path, target: float, out: Path, direction: int) -> None:
    frames = int(round(target * FPS))
    zoom = f"1.0+0.10*on/{frames}"
    x = f"(iw-iw/zoom)*{0.15 if direction > 0 else 0.85}+((iw-iw/zoom)*{0.7 if direction > 0 else -0.7})*on/{frames}"
    vf = (f"scale=3840:-2:flags=lanczos,zoompan=z='{zoom}':x='{x}':y='(ih-ih/zoom)/2':d={frames}:s={W}x{H}:fps={FPS},"
          "format=yuv420p")
    run(["-loop", "1", "-i", str(image), "-vf", vf, "-frames:v", str(frames), "-c:v", "libx264", "-preset", "medium",
         "-crf", "16", str(out)])


# ------------------------------------------------------------------ captions + labels (ASS)
def ts(t: float) -> str:
    t = max(0.0, t)
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


def build_ass(clips: list[dict], out: Path) -> None:
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,Roboto Flex,40,&H00FFFFFF,&H00FFFFFF,&H30161D1D,&H30161D1D,0,0,0,0,100,100,0,0,3,14,0,2,220,220,46,1
Style: Label,Roboto Flex,30,&H00FFFFFF,&H00FFFFFF,&H006A6A00,&H006A6A00,1,0,0,0,100,100,0.5,0,3,12,0,9,60,60,120,1
Style: Title,Roboto Flex,92,&H001D1D16,&H001D1D16,&H00FFFFFF,&H00000000,1,0,0,0,100,100,0,0,1,0,0,4,120,900,0,1
Style: Wordmark,Roboto Flex,150,&H006A6A00,&H006A6A00,&H00FFFFFF,&H00000000,1,0,0,0,100,100,22,0,1,0,0,4,120,900,0,1
Style: Sub,Roboto Flex,42,&H00484F3F,&H00484F3F,&H00FFFFFF,&H00000000,0,0,0,0,100,100,0,0,1,0,0,4,124,900,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    for clip in clips:
        for line in clip["lines"]:
            ev.append(f"Dialogue: 2,{ts(line['t0'])},{ts(line['t1'] + 0.25)},Caption,,0,0,0,,{{\\fad(120,120)}}{line['text']}")
        key = clip["visual"].split(":", 1)[1]
        if clip["visual"].startswith("app:") and key in LABELS:
            ev.append(f"Dialogue: 1,{ts(clip['start'] + 0.7)},{ts(clip['start'] + min(clip['dur'] - 0.4, 6.5))},Label,,0,0,0,,"
                      f"{{\\fad(250,300)}}{LABELS[key]}")
        if clip["visual"].startswith("card:") and key in CARD_TITLES:
            title, sub = CARD_TITLES[key]
            style = "Wordmark" if title == "CHYRON" else "Title"
            t0, t1 = clip["start"] + 0.8, clip["start"] + clip["dur"]
            # Soft paper-white wash on the left third so titles read cleanly over the watercolour art.
            ev.append(f"Dialogue: 0,{ts(clip['start'])},{ts(t1)},Title,,0,0,0,,{{\\fad(500,400)\\pos(0,0)\\an7\\1c&HF8FBF6&\\1a&H38&\\bord0\\shad0\\blur60\\p1}}"
                      f"m -80 -80 l 860 -80 l 760 1160 l -80 1160{{\\p0}}")
            ev.append(f"Dialogue: 1,{ts(t0)},{ts(t1)},{style},,0,0,0,,{{\\fad(600,400)\\pos(120,{470 if sub else 520})\\an4}}{title}")
            if sub:
                ev.append(f"Dialogue: 1,{ts(t0 + 0.7)},{ts(t1)},Sub,,0,0,0,,{{\\fad(600,400)\\pos(126,{600 if style == 'Wordmark' else 575})\\an4}}{sub}")
    out.write_text(head + "\n".join(ev) + "\n")
    # Plain SRT of the narration for upload platforms (YouTube, submission forms).
    def srt_ts(t: float) -> str:
        ms = int(round(max(0.0, t) * 1000))
        return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
    cues = [line for clip in clips for line in clip["lines"]]
    out.with_suffix(".srt").write_text("\n".join(
        f"{n}\n{srt_ts(l['t0'])} --> {srt_ts(l['t1'] + 0.25)}\n{l['text']}\n" for n, l in enumerate(cues, 1)))


# ------------------------------------------------------------------ main
def main(work: Path, out_mp4: Path) -> None:
    tmp = work / "build"
    tmp.mkdir(exist_ok=True)
    clips, total = build_timeline(work)
    print(f"timeline {total:.1f}s:", ", ".join(f"{c['id']} {c['dur']:.1f}" for c in clips))

    vo = tmp / "vo.wav"
    build_vo(work, clips, total, vo)

    segs = footage_segments(work)
    art_dir = 1
    for i, clip in enumerate(clips):
        clip_len = clip["dur"] + (XD if i < len(clips) - 1 else 0)
        clip["file"] = tmp / f"clip{i:02d}_{clip['id']}.mp4"
        kind, key = clip["visual"].split(":", 1)
        if kind == "card" and (work / "art" / f"{key}.png").exists():
            ken_burns(work / "art" / f"{key}.png", clip_len, clip["file"], art_dir)
            art_dir *= -1
        else:
            raw = tmp / f"raw{i:02d}_{clip['id']}.mp4"
            src_len = segments_to_video(segs[clip["visual"]], raw, tmp)
            fit(raw, src_len, clip_len, clip["file"])
        print("clip", clip["id"], f"{clip_len:.1f}s")

    # Crossfade chain: clip i+1 starts at its timeline start; each clip carries XD of overlap.
    inputs, chain, last = [], [], "[0:v]"
    for c in clips:
        inputs += ["-i", str(c["file"])]
    for i in range(1, len(clips)):
        label = f"[v{i}]"
        chain.append(f"{last}[{i}:v]xfade=transition=fade:duration={XD}:offset={clips[i]['start']:.3f}{label}")
        last = label
    ass = tmp / "captions.ass"
    build_ass(clips, ass)
    fonts = work / "fonts"
    chain.append(f"{last}subtitles=filename='{ass}':fontsdir='{fonts}',format=yuv420p[vout]")
    video = tmp / "video.mp4"
    run([*inputs, "-filter_complex", ";".join(chain), "-map", "[vout]", "-c:v", "libx264", "-preset", "slow", "-crf", "18",
         "-r", str(FPS), str(video)])

    # Score: Lyria parts crossfaded, trimmed to length, faded; ducked under the narration.
    parts = [work / "music" / f"part{n}.wav" for n in range(1, 7)]
    margs, mchain, mlast = [], [], "[0:a]"
    for p in parts:
        margs += ["-i", str(p)]
    for n in range(1, len(parts)):
        mchain.append(f"{mlast}[{n}:a]acrossfade=d=3:c1=tri:c2=tri[m{n}]")
        mlast = f"[m{n}]"
    music = tmp / "music.wav"
    mchain.append(f"{mlast}atrim=0:{total:.3f},afade=t=in:d=1.2,afade=t=out:st={total - 5:.3f}:d=5[mout]")
    run([*margs, "-filter_complex", ";".join(mchain), "-map", "[mout]", "-ar", "48000", str(music)])

    mix = tmp / "mix.m4a"
    # Fixed levels (no whole-mix loudnorm, which would pull quiet music up to speech level):
    # narration -16 LUFS; score about -21 LUFS alone and ducked ~10 dB under speech; true-peak limit -1 dB.
    afilter = (
        "[0:a]aresample=48000,loudnorm=I=-16:TP=-2:LRA=7,asplit=2[vo][key];"
        "[1:a]loudnorm=I=-21:TP=-4:LRA=11[mus];"
        "[mus][key]sidechaincompress=threshold=0.012:ratio=12:attack=20:release=650:makeup=1[duck];"
        "[vo]pan=stereo|c0=c0|c1=c0[vos];"
        "[vos][duck]amix=inputs=2:duration=longest:normalize=0,alimiter=limit=0.89:level=disabled[aout]"
    )
    run(["-i", str(vo), "-i", str(music), "-filter_complex", afilter, "-map", "[aout]", "-c:a", "aac", "-b:a", "192k",
         "-ar", "48000", str(mix)])

    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    run(["-i", str(video), "-i", str(mix), "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "copy", "-shortest",
         "-movflags", "+faststart", str(out_mp4)])
    print("wrote", out_mp4, f"{total:.1f}s")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
