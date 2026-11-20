# SPARK: how Chyron meets the jury's rubric

S, P and A come from the organisers, as Josh relayed them. **R and K are assumptions** (marked ⚠). Replace them with the official wording once the rubric is shared. The organiser page also lists founder profile, product potential, market viability, technical architecture and use of Google AI. This table covers both.

| Letter | Meaning | What the jury must see | Where Chyron shows it |
| --- | --- | --- | --- |
| **S** | Significance | A problem that matters to real people, at scale | Special educators can't safely and repeatedly recreate real-world situations such as shopping, paying or talking to a shopkeeper. DACAL is a design partner. Opening slide plus one tutor quote, used only with consent |
| **P** | Pain point addressed | The product removes a specific pain, visibly | Building one practice scenario by hand takes days; Chyron goes from description to validated room in under a minute. The demo is timed on screen |
| **A** | Accessibility | Usable by learners with diverse needs and by busy tutors | Support pathways A/B/C (prompts, density, volume); comfort caps enforced on the server; single-switch and keyboard controls; Material 3 at AA/AAA contrast; voice intake for tutors; laptop or projected room; axe checks in Playwright |
| **R** ⚠ | Real-world readiness / reach (assumed) | It works now and can scale | Deployed on Cloud Run, Cloud SQL and Firebase Hosting in asia-south1; 13 automated tests; R1–R7 safety layer; bounded cost (at most 4 Gemini calls per scene); offline demo cache |
| **K** ⚠ | Key innovation / knowledge (assumed) | What is new, and why AI is essential | Gemini proposes and rules decide: structured JSON planning, a critique-driven repair loop, patch edits, a Gemma private mode, and Nano Banana concept previews. Not a chatbot wrapper |

## One-line pitch per letter (practise these)

- **S:** "Learners understand money in class but freeze in a real shop. Teachers have no safe place for them to practise."
- **P:** "A tutor types one sentence. In under a minute there is a validated practice room."
- **A:** "Every scene has three support pathways. The calmest one has more prompts, fewer people and lower sound, enforced in code."
- **R:** "It is live on Google Cloud today. Every scene passes seven safety rules before a learner sees it."
- **K:** "Gemini plans and repairs, and our rule engine decides. That is how you make generative AI safe for special education."
