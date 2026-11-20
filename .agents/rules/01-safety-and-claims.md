# Safety and honest claims (always on)

- Never build or serve a scene that hasn't passed `validate()`. No bypass flags, not even "for the demo".
- Comfort caps (R5) are enforced on the server. The client clamps volume again; it never raises it.
- No diagnosis, labels or scores for learners, anywhere: code, UI text, logs, prompts, pitch.
- Do not write "improves learning", "therapeutic", "clinically" or any outcome claim in UI copy, README or slides. Say "supports tutors" and "practice".
- Learner data: at most a tutor-chosen nickname. Never send learner data to any model.
- Keep secrets out of the repo. Use `.env` locally (gitignored) and Secret Manager on Cloud Run. API keys never reach the browser.
- Do not name DACAL or show any real child in screenshots unless written consent exists.
