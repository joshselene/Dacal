// Records CHYRON product footage from a running site with Chrome's screencast (1920x1080 JPEG frames),
// a visible animated cursor and click ripples. Capture pauses during network waits, so the edit stays tight.
//   cd apps/web && BASE=https://<project>.web.app/ node ../../tools/demo-video/record.mjs OUT_DIR
// Writes OUT_DIR/frames/*.jpg and OUT_DIR/segments.json ([{scene, start, end, frames:[{file,t}]}]).
import fs from "node:fs";
import path from "node:path";
import { chromium } from "@playwright/test";

const OUT = path.resolve(process.argv[2] || "footage");
const BASE = process.env.BASE || "http://localhost:5173/";
const CARDS = process.env.CARDS || path.resolve(path.dirname(new URL(import.meta.url).pathname), "cards");
fs.mkdirSync(path.join(OUT, "frames"), { recursive: true });

const browser = await chromium.launch();
const context = await browser.newContext({ viewport: { width: 1536, height: 864 }, deviceScaleFactor: 1.25 });
const page = await context.newPage();
page.setDefaultTimeout(180000);

await context.addInitScript(() => {
  // Headless Chrome has no speech output; keep the app's calls harmless.
  if (window.speechSynthesis) window.speechSynthesis.speak = () => {};
  const install = () => {
    if (document.getElementById("__cursor")) return;
    const style = document.createElement("style");
    style.textContent = `
      #__cursor{position:fixed;left:0;top:0;width:26px;height:26px;z-index:2147483647;pointer-events:none;
        transform:translate(var(--x,760px),var(--y,430px));transition:transform .7s cubic-bezier(.22,.9,.3,1)}
      #__cursor svg{filter:drop-shadow(0 2px 3px rgba(0,0,0,.35))}
      .__ripple{position:fixed;z-index:2147483646;pointer-events:none;width:44px;height:44px;margin:-22px 0 0 -22px;
        border-radius:50%;background:rgba(0,106,106,.28);border:2px solid rgba(0,106,106,.65);animation:__r .55s ease-out forwards}
      @keyframes __r{from{transform:scale(.3);opacity:1}to{transform:scale(1.6);opacity:0}}
      ::-webkit-scrollbar{width:0;height:0}`;
    document.head.appendChild(style);
    const c = document.createElement("div");
    c.id = "__cursor";
    c.innerHTML = '<svg width="26" height="26" viewBox="0 0 24 24"><path d="M4 2l15 11-6.5 1.2L16 21l-3 1.4-3.6-6.9L4 20z" fill="#fff" stroke="#161d1d" stroke-width="1.4" stroke-linejoin="round"/></svg>';
    document.body.appendChild(c);
  };
  window.__cursorTo = (x, y) => { install(); const c = document.getElementById("__cursor"); c.style.setProperty("--x", `${x - 3}px`); c.style.setProperty("--y", `${y - 2}px`); };
  window.__ripple = (x, y) => { const r = document.createElement("div"); r.className = "__ripple"; r.style.left = `${x}px`; r.style.top = `${y}px`; document.body.appendChild(r); setTimeout(() => r.remove(), 700); };
  document.addEventListener("DOMContentLoaded", install);
});

// ---------------------------------------------------------------- screencast capture
const cdp = await context.newCDPSession(page);
const segments = [];
let current = null;
let frameNo = 0;
cdp.on("Page.screencastFrame", async ({ data, metadata, sessionId }) => {
  cdp.send("Page.screencastFrameAck", { sessionId }).catch(() => {});
  if (!current) return;
  const file = path.join(OUT, "frames", `${String(frameNo++).padStart(6, "0")}.jpg`);
  fs.writeFileSync(file, Buffer.from(data, "base64"));
  current.frames.push({ file, t: metadata.timestamp });
});
await cdp.send("Page.startScreencast", { format: "jpeg", quality: 92, maxWidth: 1920, maxHeight: 1080, everyNthFrame: 1 });

async function capture(scene) {
  // A screenshot opens each segment, because the screencast only emits frames when something changes.
  const file = path.join(OUT, "frames", `${String(frameNo++).padStart(6, "0")}.jpg`);
  const t = Date.now() / 1000;
  await page.screenshot({ path: file, type: "jpeg", quality: 92 });
  current = { scene, start: t, end: null, frames: [{ file, t }] };
  segments.push(current);
  console.log("capture", scene);
}
function pause() { if (current) { current.end = Date.now() / 1000; current = null; } }
const wait = (ms) => page.waitForTimeout(ms);

async function point(locator) {
  await locator.scrollIntoViewIfNeeded();
  const box = await locator.boundingBox();
  const x = box.x + box.width / 2; const y = box.y + Math.min(box.height / 2, 28);
  await page.evaluate(([x, y]) => window.__cursorTo(x, y), [x, y]);
  await wait(750);
  return [x, y];
}
async function click(locator, after = 500) {
  const [x, y] = await point(locator);
  await page.evaluate(([x, y]) => window.__ripple(x, y), [x, y]);
  await locator.click();
  await wait(after);
}
async function type(locator, text, delay = 42) {
  await click(locator, 200);
  await locator.pressSequentially(text, { delay });
}
async function command(locator) {
  // Room/console commands: wait for the API before the next action, like a patient learner.
  const done = page.waitForResponse((r) => r.url().includes("/command"));
  await click(locator, 0);
  await done;
  await wait(380);
}
async function smoothScroll(y) {
  await page.evaluate((y) => window.scrollTo({ top: y, behavior: "smooth" }), y);
  await wait(900);
}
async function recordCard(name, ms) {
  await page.goto(`file://${CARDS}/${name}.html`);
  await page.evaluate(() => document.getElementById("__cursor")?.remove());
  await wait(150);
  await capture(`card:${name}`);
  await wait(ms);
  pause();
}

// ---------------------------------------------------------------- opening card
await recordCard("opening", 7600);
if (process.env.CARDS_ONLY) {
  await recordCard("end", 9800);
  fs.writeFileSync(path.join(OUT, "segments.json"), JSON.stringify(segments, null, 1));
  await browser.close();
  process.exit(0);
}

// ---------------------------------------------------------------- setup (not captured)
await page.goto(BASE);
await page.getByRole("button", { name: "Create an account", exact: true }).click();
await page.getByLabel("Full name", { exact: true }).fill("Meera (demo tutor)");
await page.getByLabel("Email address", { exact: true }).fill(`video-demo-${Date.now()}@example.org`);
await page.getByLabel("School or organisation").fill(`Sunrise Special School ${Date.now() % 10000}`);
await page.locator("#signup-password").fill("PreviewPass42!");
await page.getByLabel("Confirm password").fill("PreviewPass42!");
await page.getByRole("button", { name: "Create account", exact: true }).click();
await page.locator("#login-password").fill("PreviewPass42!");
await page.getByRole("button", { name: "Sign in", exact: true }).click();
await page.getByRole("button", { name: "Classes and modules", exact: true }).click();
await page.getByLabel("Class name", { exact: true }).fill("Life Skills A");
await page.getByRole("button", { name: "＋ Save Class", exact: true }).click();
await page.getByRole("button", { name: "＋ Add Module", exact: true }).click();
await page.getByLabel("Module name", { exact: true }).fill("Shopping");
await page.getByRole("button", { name: "✓ Save Module", exact: true }).click();
await page.getByLabel("Student name", { exact: true }).fill("Learner 01");
await page.getByRole("button", { name: "＋ Add Learner", exact: true }).click();
await page.getByRole("button", { name: "Chyron Studio", exact: true }).click();
await page.locator("#experience-prompt").waitFor();
await page.evaluate(() => window.scrollTo(0, 0));
await page.evaluate(() => window.__cursorTo(900, 520));
await wait(800);

// ---------------------------------------------------------------- 1. describe
await capture("app:describe");
await wait(600);
await point(page.locator(".voice-live button, .voice-intake-note").first());
await wait(500);
await type(page.locator("#experience-prompt"), "A learner buys milk and bread at a kirana shop with ₹200 and pays at the counter.", 38);
await type(page.locator("#experience-title"), "Kirana practice", 50);
await wait(500);
await click(page.getByRole("button", { name: "Continue to questions" }), 900);
await click(page.getByRole("button", { name: "Skip remaining questions & review my idea →" }), 1400);
pause();

// ---------------------------------------------------------------- 2. concepts (wait for Gemini + Nano Banana off camera)
await page.locator(".status-pill", { hasText: "drafting" }).waitFor({ state: "detached", timeout: 120000 }).catch(() => {});
await page.waitForFunction(() => [...document.querySelectorAll(".concept-preview-image")].every((img) => img.complete), null, { timeout: 60000 }).catch(() => {});
await page.locator(".concept-grid").scrollIntoViewIfNeeded();
await wait(600);
await capture("app:concepts");
await wait(700);
const cards = page.locator(".concept-card");
for (let i = 0; i < 3; i += 1) { await point(cards.nth(i)); await wait(900); }
await click(cards.nth(2), 1600);
pause();

// ---------------------------------------------------------------- 3. safety: generating screen + faulty seed repair
await page.getByRole("button", { name: "Approve & Start generating →" }).scrollIntoViewIfNeeded();
await capture("app:safety");
await click(page.getByRole("button", { name: "Approve & Start generating →" }), 1200);
await page.locator(".repair-attempt-card").first().waitFor();
await point(page.locator(".repair-attempt-card").first());
await wait(1600);
const safety = page.getByRole("button", { name: /Run safety check/ });
await click(safety, 200);
await page.locator(".run-safety-btn:not(:disabled)").waitFor();
await wait(600);
await point(page.locator(".attempt-invalid").first());
await wait(2600);
await point(page.locator(".attempt-valid").last());
await wait(2800);
await point(page.locator(".safety-status-note"));
await wait(2200);
pause();
await page.getByRole("button", { name: "Complete generation & unlock configuration →" }).click();

// ---------------------------------------------------------------- 4. configure + plain-language edit
await page.getByRole("button", { name: "Save configuration", exact: true }).waitFor();
await page.evaluate(() => window.scrollTo(0, 0));
await wait(500);
await capture("app:configure");
await wait(800);
await click(page.getByRole("button", { name: "Save configuration", exact: true }), 600);
await page.getByText("Configuration validated against R1–R7 and saved.", { exact: true }).waitFor();
await wait(900);
await type(page.locator("#plain-language-edit-input"), "make pathway A quieter", 55);
pause();
await page.getByRole("button", { name: "Apply patch", exact: true }).click();
await page.locator(".patch-locality-note").waitFor({ timeout: 120000 });
await page.locator(".patch-locality-note").scrollIntoViewIfNeeded();
await capture("app:configure");
await point(page.locator(".patch-locality-note"));
await wait(2600);
pause();

// ---------------------------------------------------------------- 5. room
await page.getByRole("button", { name: "Manage versions", exact: true }).click();
await page.getByRole("button", { name: "✓ Approve current version", exact: true }).click();
await page.getByRole("button", { name: "▶ Launch 4-Wall Room (N/E/S/W)", exact: true }).click();
await page.getByRole("heading", { name: /Live Session/ }).waitFor();
await page.getByRole("button", { name: /^A · most support/ }).click();
await page.waitForResponse((r) => r.url().includes("/command")).catch(() => {});
await page.getByLabel("Scene view").selectOption("overview");
await page.evaluate(() => window.scrollTo(0, 0));
await wait(1200);
await capture("app:room");
await point(page.locator(".scene-viewport"));
await wait(2600);
await page.getByLabel("Scene view").selectOption("laptop");
await wait(900);
const order = ["N", "E", "S", "W"];
const turns = { "Walk forward": 0, "Turn right": 1, "Turn around": 2, "Turn left": 3 };
for (let i = 0; i < 14; i += 1) {
  const text = (await page.locator(".scene-guidance").textContent().catch(() => "")) || "";
  if (text.includes("bread")) break;
  if (text.includes("hand button")) { await command(page.getByRole("button", { name: "Select item", exact: true })); await wait(700); continue; }
  const facing = (await page.locator(".scene-labels").textContent()).trim();
  const turn = Object.keys(turns).find((k) => text.includes(k)) ?? "Walk forward";
  await command(page.getByRole("button", { name: `Move ${order[(order.indexOf(facing) + turns[turn]) % 4]}`, exact: true }));
}
await wait(1200);
await page.getByLabel("Scene view").selectOption("grid2x2");
await wait(2600);
await click(page.getByRole("button", { name: /^C · least support/ }), 0);
await page.waitForResponse((r) => r.url().includes("/command")).catch(() => {});
await page.getByLabel("Scene view").selectOption("overview");
await wait(2600);
pause();

// ---------------------------------------------------------------- 6. console + notebook
await page.locator(".tutor-console-card").scrollIntoViewIfNeeded();
await capture("app:console");
await wait(500);
await click(page.getByRole("button", { name: /^B · some support/ }), 0);
await page.waitForResponse((r) => r.url().includes("/command")).catch(() => {});
await wait(900);
await command(page.getByRole("button", { name: /Give Prompt/ }));
await wait(900);
await command(page.locator(".console-actions-grid button").first());
await wait(1100);
await command(page.locator(".console-actions-grid button").first());
await wait(800);
await click(page.getByRole("button", { name: "Finish & View Session Notebook →" }), 1600);
await smoothScroll(0);
await point(page.locator("main section").first());
await wait(2600);
pause();

// ---------------------------------------------------------------- end card
await recordCard("end", 9800);

fs.writeFileSync(path.join(OUT, "segments.json"), JSON.stringify(segments, null, 1));
console.log("segments", segments.map((s) => `${s.scene} ${(s.end - s.start).toFixed(1)}s ${s.frames.length}f`).join(" | "));
await browser.close();
