---
name: chyron-scene-spec
description: The Chyron shop scene spec (room w/h and south entrance, layout objects with assets, cells, sizes and priced items, task required/budget/time limit, support pathways A/B/C, events) and its JSON Schema in apps/api/app/services/scene_schema.json used for Gemini structured output. Use when changing spec fields, writing seeds, or adding assets.
---

# Scene spec

The source of truth is `validator.py` (what is checked). `scene_schema.json` mirrors it for Gemini. When you change one, change the other in the same commit, and run `tests/test_gemini_provider.py`.

## Shape (the reference spec is `get_reference_scene_spec()`)

```json
{
  "room":   {"w": 12, "h": 8, "entrance": {"wall": "S", "cells": [[5,7],[6,7]]}},
  "layout": [{"id": "shelf1", "asset": "shelf", "cell": [2,3], "size": [3,1],
              "items": [{"sku": "milk", "price": 62}]},
             {"id": "counter", "asset": "counter", "cell": [10,6], "size": [1,1]}],
  "task":   {"required": ["milk","bread"], "budget": 500, "time_limit_s": 300,
             "difficulty": "Developing", "rules": ["..."], "what_ifs": ["..."]},
  "support": {"A": {"prompt":3,"density":2,"volume":40},
              "B": {"prompt":2,"density":3,"volume":60},
              "C": {"prompt":1,"density":5,"volume":80}},
  "events": [{"trigger": "enter", "target": "shopkeeper"}]
}
```

- The grid uses integer cells. x runs west to east, from 0 to w−1. y runs north to south, from 0 to h−1. The entrance is on the south edge (y = h−1).
- Assets: shelf, counter, fridge, basket_stand, sign, plant, bench, table, kiosk, decor. Adding one means a mesh in `FourWallPreview.jsx`, an entry in `VALID_ASSETS` and the schema enum, and a seed.
- Event triggers: enter, pickup, checkout, timer, what_if, prompt. Targets are a layout id or `shopkeeper`.
- Prices are in rupees. Learner-facing text is plain English with no clinical words.
- No learner data ever goes in a spec.

## Seeds (`apps/api/app/demo_seeds/`)

| File | Use |
| --- | --- |
| `kirana_shop.valid.json` | The reference shop; passes every rule |
| `kirana_shop.faulty.json` | Counter boxed in (R3), budget 50 (R4), pathway A volume 70 (R5, R6). Use it for the live repair demo |

Add two more before Day 2: a bakery and a pharmacy counter. Generate them through Gemini, fix them until valid, and commit them, so the demo cache also has them.

## Not supported yet

Non-shop scenes such as a bus stop, road crossing or bank. These need new assets, new R3 and R4 logic (no counter or budget), and engine work. Treat them as roadmap for the jury, not demo.
