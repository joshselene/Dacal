# CHYRON product video (Google-only pipeline)

| Piece | Google product | Script |
| --- | --- | --- |
| Narration | Cloud Text-to-Speech, Chirp 3 HD (`en-IN-Chirp3-HD-Sulafat`) | `tts.py` + `narration.json` |
| Score | Lyria (`lyria-002`) on Vertex AI, six 33 s sections in D major, 90 BPM | see below |
| Story art | Nano Banana (`gemini-3.1-flash-image`) on Vertex AI | see below |
| Footage | The live app on Firebase Hosting + Cloud Run, Chrome screencast | `record.mjs`, `cards/` |
| Edit | ffmpeg (captions, labels, crossfades, ducking) | `compose.py` |

```bash
W=/tmp/chyron-video                       # work dir (media stays out of git)
python tools/demo-video/tts.py $W/vo      # needs `gcloud auth` on the project
# Lyria: POST .../locations/us-central1/publishers/google/models/lyria-002:predict -> $W/music/part1..6.wav
# Nano Banana: hook/tutor/close illustrations (16:9) -> $W/art/{hook,tutor,close}.png
cp tools/demo-video/record.mjs apps/web/tests/.rec.mjs && (cd apps/web && \
  CARDS=$PWD/../../tools/demo-video/cards BASE=https://chyron-buildathon-70138.web.app/ node tests/.rec.mjs $W/footage)
# $W/fonts/RobotoFlex.ttf from github.com/google/fonts (ofl/robotoflex)
python tools/demo-video/compose.py $W demo_video/chyron-demo.mp4   # also writes captions .srt in $W/build
```

Narration wording follows the project rules: practice and support, no outcome, therapeutic or clinical claims.
The recorder creates one demo tutor account on the target site.
