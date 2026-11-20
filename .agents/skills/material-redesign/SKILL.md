---
name: material-redesign
description: Restyle the Chyron web app (apps/web) from the Apple-style glass look in style.css, ClassWorkspace.css and FourWallPreview.css to Google Material 3 - M3 colour, type, shape and elevation tokens from one seed colour, Google Sans Flex or Roboto Flex, Material Symbols, accessible special-education layouts - while keeping the Playwright and axe tests passing. Use for any UI, CSS, theming, layout or component work.
---

# Material 3 redesign

**Strategy: tokens first, components second.** The app is one big `main.jsx` with class-based CSS. The fastest, safest route is to replace the glass design tokens with Material 3 tokens and restyle the existing class names. Then adopt Material Web components only where they clearly help. This keeps every accessible name the tests rely on.

## Step 1: Token swap (`apps/web/src/style.css`)

Generate light and dark schemes from one seed with `@material/material-color-utilities` (a one-off script, `scripts/m3-tokens.mjs`). Write them as `--md-sys-color-*`, then map the existing tokens onto them so the rest of the CSS keeps working:

| Existing token | Material 3 token |
| --- | --- |
| `--bg` | `--md-sys-color-surface` |
| `--ink` | `--md-sys-color-on-surface` |
| `--muted` | `--md-sys-color-on-surface-variant` |
| `--accent` / `--on-accent` | `--md-sys-color-primary` / `--md-sys-color-on-primary` |
| `--accent-soft` | `--md-sys-color-primary-container` |
| `--surface` | `--md-sys-color-surface-container-low` |
| `--surface-strong` | `--md-sys-color-surface-container-high` |
| `--line` / `--edge` | `--md-sys-color-outline-variant` |
| `--danger`, `--success`, `--warning` | `--md-sys-color-error`, plus custom success and warning roles built from the scheme's tonal palettes |

Then:

- **Remove glass.** Delete `--blur`, the `backdrop-filter` rules and the `--mesh` background (`body::before`). Use M3 tonal surfaces with elevation levels 0–3 (`box-shadow` from M3 elevation tokens) instead.
- **Type.** Load Google Sans Flex from Google Fonts if it is available there at build time, otherwise Roboto Flex, with `system-ui` as the fallback. Replace the `-apple-system`/SF Pro stack. Use the M3 type scale: display, headline, title, body and label.
- **Shape.** Buttons are full pill (already the case), cards use 16 px corners (`--md-sys-shape-corner-large`), and dialogs 28 px.
- **Seed colour.** A calm teal suits sensory-sensitive users (for example `#006A6A`). Respect the existing `data-theme` toggle and keep its localStorage key.

## Step 2: Components

- **Icons:** swap lucide for Material Symbols Rounded (Google Fonts) in the main navigation and primary actions. lucide can stay inside `FourWallPreview` during the event.
- **Material Web (`@material/web`):** use it for new pieces only: segmented buttons for pathway A/B/C, filled and tonal buttons, outlined text fields, chips for the R1–R7 rule badges, and a linear progress indicator for generation. React 18 needs `ref`-based event listeners for custom elements, so wrap each one in a small component under `src/m3/`.
- **Generating screen:** an M3 list where each attempt is a row, with seven assist chips (R1–R7) that turn green or red, plus a model and tokens caption. This is the screen that sells the architecture.

## Step 3: Accessibility (SPARK "A")

- Touch targets of at least 48 dp, and at least 72 dp on the learner and room controls.
- Contrast: AA everywhere and AAA for learner text. Check that `@axe-core/playwright` stays clean in both themes.
- Full keyboard use and a single-switch scan mode in the room. Visible focus uses the M3 focus ring (3 px `--md-sys-color-secondary`).
- `prefers-reduced-motion`: turn off non-essential motion.
- Plain-language labels, no clinical words.

## Keep tests green

`apps/web/tests/glass-ui.spec.js` finds elements by role and accessible name ("Create an account", "Use dark theme", "Classes and modules", "＋ Save Class" and so on). **Don't rename labels.** Rename the file to `ui.spec.js` and update `package.json` `test:ui`. Run it at 320, 390, 768 and 1440 px after every styling commit.

## Branding

Product name: **Chyron**. Change the `<title>` in `apps/web/index.html` from "Chernyx AI Studio" to "Chyron". The footer reads "Built with Gemini and Google Cloud" in plain text. No Google logos unless the organisers provide approved assets. No pricing in the UI.
