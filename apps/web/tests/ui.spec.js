import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test("workspace: authoring, themes, responsive views and scene controls", async ({ page }) => {
  test.setTimeout(120000);
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto(process.env.UI_URL || "http://127.0.0.1:5173/");
  await page.getByRole("button", { name: "Create an account", exact: true }).click();
  await page.getByLabel("Full name", { exact: true }).fill("Meera Preview");
  await page.getByLabel("Email address", { exact: true }).fill(`glass-${Date.now()}@example.org`);
  await page.getByLabel("School or organisation").fill(`UI test school ${Date.now()}`);
  await page.locator("#signup-password").fill("PreviewPass42!");
  await page.getByLabel("Confirm password").fill("PreviewPass42!");
  await page.getByRole("button", { name: "Create account", exact: true }).click();
  await page.locator("#login-password").fill("PreviewPass42!");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page.getByRole("navigation", { name: "Main navigation" })).toBeVisible();

  await page.getByRole("button", { name: "Use dark theme", exact: true }).click();
  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await expect(page.getByRole("navigation", { name: "Main navigation" })).toBeVisible();
  await page.getByRole("button", { name: "Use light theme", exact: true }).click();

  await page.getByRole("button", { name: "Classes and modules", exact: true }).click();
  await page.getByLabel("Class name", { exact: true }).fill("Life Skills A");
  await page.getByRole("button", { name: "＋ Save Class", exact: true }).click();
  await expect(page.getByRole("button", { name: "＋ Add Module", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "＋ Add Module", exact: true }).click();
  await page.getByLabel("Module name", { exact: true }).fill("Shopping");
  await page.getByRole("button", { name: "✓ Save Module", exact: true }).click();
  await page.getByLabel("Student name", { exact: true }).fill("Learner 01");
  await page.getByRole("button", { name: "＋ Add Learner", exact: true }).click();
  await expect(page.getByText("Learner 01", { exact: true })).toBeVisible();

  await page.getByRole("button", { name: "Chyron Studio", exact: true }).click();
  await page.locator("#experience-prompt").fill("A grocery shop with milk and bread and a budget of 500.");
  await page.locator("#experience-title").fill("Shopping practice");
  await page.getByRole("button", { name: "Continue to questions" }).click();
  await page.getByRole("button", { name: "Skip remaining questions & review my idea →" }).click();
  await expect(page.locator(".concept-card canvas")).toHaveCount(3);
  await page.getByRole("button", { name: "Approve & Start generating →" }).click();
  await page.getByRole("button", { name: "Complete generation & unlock configuration →" }).click();
  await page.getByRole("button", { name: "Save configuration", exact: true }).click();
  await expect(page.getByText("Configuration validated against R1–R7 and saved.", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Manage versions", exact: true }).click();
  await page.getByRole("button", { name: "✓ Approve current version", exact: true }).click();
  await page.getByRole("button", { name: "▶ Launch 4-Wall Room (N/E/S/W)", exact: true }).click();
  await expect(page.getByRole("heading", { name: /Live Session/ })).toBeVisible();
  await page.getByRole("button", { name: "Move N", exact: true }).click();
  await page.getByRole("button", { name: "Pause", exact: true }).click();
  await expect(page.locator(".scene-paused")).toBeVisible();
  await page.getByRole("button", { name: "Resume", exact: true }).click();
  await expect(page.locator(".scene-paused")).toHaveCount(0);

  const colors = await page.locator("canvas").evaluate((canvas) => {
    const gl = canvas.getContext("webgl2");
    const pixels = new Uint8Array(canvas.width * canvas.height * 4);
    gl.readPixels(0, 0, canvas.width, canvas.height, gl.RGBA, gl.UNSIGNED_BYTE, pixels);
    const unique = new Set();
    for (let offset = 0; offset < pixels.length; offset += 64) unique.add(`${pixels[offset]},${pixels[offset + 1]},${pixels[offset + 2]}`);
    return unique.size;
  });
  expect(colors).toBeGreaterThan(30);
  await page.getByLabel("Scene view").selectOption("S");
  await expect(page.locator(".scene-labels")).toHaveText("S");
  await page.getByLabel("Scene view").selectOption("room");

  for (const width of [320, 390, 768, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    for (const name of ["Home", "Classes and modules", "Projects", "Session notebook", "Learning hub", "Chyron Studio"]) {
      await page.getByRole("navigation").getByRole("button", { name, exact: true }).click();
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `${name} at ${width}px`).toBe(true);
    }
  }
  await page.getByRole("button", { name: "Home", exact: true }).click();
  for (const mode of ["light", "dark"]) {
    if (mode === "dark") await page.getByRole("button", { name: "Use dark theme", exact: true }).click();
    await page.evaluate(async () => {
      await Promise.all(document.getAnimations().map((animation) => animation.finished.catch(() => {})));
    });
    const result = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
    expect(result.violations.map(({ id, nodes }) => ({ id, count: nodes.length }))).toEqual([]);
  }
  expect(errors).toEqual([]);
});