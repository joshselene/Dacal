---
name: buildathon-demo
description: Prepare and harden the Chyron demo for the Google Startup Buildathon jury, who score with the SPARK rubric (Significance, Pain point, Accessibility, plus R and K - see docs/SPARK.md) and the organiser criteria. Covers the demo path on the kirana-shop seeds, the DEMO_MODE cache fallback, readiness checklist, scope freeze, cut list and submission. Use when planning Day 2 work, deciding what to cut, or checking demo readiness.
---

# Buildathon demo

Every minute of the demo should land at least one SPARK letter. The mapping and one-line pitches are in `docs/SPARK.md`.

## Demo path (about 60–75 seconds; never break it)

| # | On screen | SPARK |
| --- | --- | --- |
| 1 | Tutor signs in, opens New scenario, types or speaks: *"A learner buys milk and bread at a kirana shop with ₹200 and pays at the counter."* | S, P |
| 2 | Three Gemini concepts (guided, explore, calm), with Nano Banana images if enabled. Pick Calm | K |
| 3 | Generating screen: attempt rows with R1–R7 chips turning green. Then "Run safety check" posts `demo_seeds/kirana_shop.faulty.json`: R3, R4, R5 and R6 go red, Gemini repairs, all go green. Say: *"Gemini proposes, our rules decide."* | R, K |
| 4 | Configure: pathway A, B or C segmented button; plain-language edit *"make pathway A quieter"* becomes a patch and a new version | A |
| 5 | Launch the run in laptop mode, walk to a shelf, pick up the milk; switch to four walls (2×2) | A, P |
| 6 | Tutor console: pathway switch live; notebook counts and times. Say: *"No diagnosis, no scores."* | A, R |

## Readiness checklist

- [ ] The path works on `https://$PROJECT_ID.web.app` over a phone hotspot.
- [ ] `DEMO_MODE=cache` local run replays the same path with Wi-Fi off; the cache was warmed the night before.
- [ ] A 90-second screen recording is on the laptop and on a phone.
- [ ] The Monitoring chart (Gemini tokens and attempts per scene) is open in a tab.
- [ ] Architecture slide: every box is a Google product with its job written on it.
- [ ] `docs/PRIOR_WORK.md` is filled in.
- [ ] `docs/SPARK.md`: R and K are confirmed with the organisers' wording.
- [ ] No outcome or clinical claims anywhere: UI, slides or speech.
- [ ] API tests pass, and the Playwright UI test passes.

## Scope freeze and cut list

Freeze by mid-afternoon on Day 2. If time runs short, cut in this order:

1. Gemma private edits (use a slide)
2. Gemini Live voice (type instead)
3. Nano Banana images (CSS art fallback already exists)
4. Live attempt animation (show the final rules summary instead)
5. Full Material Web components (keep the token restyle only)

**Never cut:** Gemini planning, the visible validator and repair, the 3D room, pathways A/B/C, the deployed URL.

## Submission package

The live URL, repo link, deck PDF under 5 MB, 100-character line, short description and backup video. Submit early, then only rehearse.
