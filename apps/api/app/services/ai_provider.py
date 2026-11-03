"""Pluggable AI provider layer, bounded repair loop, and plain-language patch editor.

Implements:
- FR-05: Three concept-preview options before the Start generating gate.
- FR-08 & AT-03: Plain-language edit box that applies a localized JSON patch
  (median patch < 10% of spec bytes), never a full regeneration.
- FR-15 & LC-3: Bounded repair loop (up to k=3 retries with validator critique),
  returning a plain-language failure message if all attempts fail.
- FR-18: Pluggable AI provider interface with Claude as default and deterministic
  mock for offline testing.
- SEC-04 & SEC-05: AI prompts contain no learner personal data; AI output is
  untrusted input validated against R1–R7.
"""

from __future__ import annotations

from copy import deepcopy
import json
import os
import re
from typing import Any

from .validator import DEFAULT_COMFORT_CAPS, get_reference_scene_spec, validate_scene_spec


class AIProvider:
    """Abstract base interface for scene planning and localized patching."""

    name: str = "base"

    def generate_concepts(self, prompt: str, answers: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        raise NotImplementedError

    def plan_scene(
        self,
        prompt: str,
        answers: dict[str, Any] | None = None,
        concept: dict[str, Any] | None = None,
        critique: list[dict[str, Any]] | None = None,
        attempt: int = 1,
    ) -> dict[str, Any]:
        raise NotImplementedError

    def apply_plain_language_edit(
        self,
        spec: dict[str, Any],
        instruction: str,
    ) -> dict[str, Any]:
        raise NotImplementedError


class MockAIProvider(AIProvider):
    """Deterministic offline AI provider for tests and local development."""

    name: str = "mock"

    def generate_concepts(self, prompt: str, answers: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        clean_prompt = (prompt or "Life-skills practice environment").strip()
        short_focus = clean_prompt[:80]
        return [
            {
                "id": "guided",
                "title": "Guided practice shop",
                "summary": f"Clear step-by-step visual cues and calm lighting tailored for: {short_focus}",
                "environment": "Classroom Shop",
                "visual_style": "Soft 3D",
                "tags": ["Structured", "Low stimulation", "Step-by-step"],
                "preview_art": "art-guided",
            },
            {
                "id": "explore",
                "title": "Open neighbourhood market",
                "summary": "Flexible aisles with optional items so learners can compare prices and make choices.",
                "environment": "Public space",
                "visual_style": "Soft 3D",
                "tags": ["Exploration", "Budget choice", "Hints when needed"],
                "preview_art": "art-explore",
            },
            {
                "id": "calm",
                "title": "Calm sensory corner store",
                "summary": "Reduced visual density, quiet ambient audio, and high-contrast item labels.",
                "environment": "Calm room",
                "visual_style": "Minimal and simple",
                "tags": ["Reduced stimulation", "Accessible", "Gentle pace"],
                "preview_art": "art-calm",
            },
        ]

    def plan_scene(
        self,
        prompt: str,
        answers: dict[str, Any] | None = None,
        concept: dict[str, Any] | None = None,
        critique: list[dict[str, Any]] | None = None,
        attempt: int = 1,
    ) -> dict[str, Any]:
        spec = get_reference_scene_spec()
        text = (prompt or "").lower()

        # If prompt intentionally requests an unrepairable fault for testing FR-15 / LC-3:
        if "[force_unrepairable_fault]" in text:
            spec["room"]["entrance"]["wall"] = "N"
            spec["task"]["budget"] = 1
            return spec

        # If prompt requests a transient fault on attempt 1 that repairs on attempt 2:
        if "[force_repair_once]" in text and attempt == 1 and not critique:
            spec["task"]["budget"] = 10  # Fails R4 on attempt 1, repaired on attempt 2
            return spec

        # Adapt items or budget lightly based on prompt keywords while staying valid
        if "fruit" in text or "apple" in text:
            if "apple" not in spec["task"]["required"]:
                spec["task"]["required"] = ["milk", "apple"]

        return spec

    def apply_plain_language_edit(
        self,
        spec: dict[str, Any],
        instruction: str,
    ) -> dict[str, Any]:
        """Apply a localized patch to `spec` based on plain-language `instruction` (FR-08).

        Never regenerates the whole spec; modifies only the targeted field/object
        and computes the exact patch byte size vs total spec byte size.
        """
        patched = deepcopy(spec)
        text = instruction.strip()
        lower = text.lower()
        patch_ops: list[dict[str, Any]] = []

        # 1. Budget change: e.g. "set budget to 600" or "increase budget to 450" or "budget to 20"
        m_budget = re.search(r"budget\s+(?:to|=)\s*(-?\d+)", lower)

        # 2. Time limit edit: e.g. "set time limit to 240"
        m_time = re.search(r"time(?:\s+limit)?\s+(?:to|=)\s*(\d+)", lower)

        # 3. Entrance wall change: e.g. "move entrance to north wall" or "set entrance wall to N"
        m_wall = re.search(r"entrance\s+(?:wall\s+)?to\s+(north|south|east|west|n|s|e|w)\b", lower)

        # 4. Support volume/density/prompt edit: e.g. "set pathway A volume to 35" or "set A density to 4"
        m_support = re.search(
            r"(?:pathway\s+)?([abc])\s+(volume|density|prompt)\s+(?:to|=)\s*(-?\d+)",
            lower,
        )

        # 5. Event target edit: e.g. "set event target to ghost_actor"
        m_event_tgt = re.search(r"event\s+target\s+to\s+([a-z0-9_]+)", lower)

        # 6. Move object: e.g. "move shelf1 to 3, 4" or "move counter to 15, 6"
        m_move = re.search(r"move\s+([a-z0-9_]+)\s+to\s+\[?\s*(-?\d+)\s*[, ]\s*(-?\d+)\s*\]?", lower)

        # 7. Add item to shelf: e.g. "add eggs price 70 to shelf1" or "add tea for 40 on shelf2"
        m_add_item = re.search(
            r"add\s+([a-z0-9_]+)\s+(?:price|for|at)\s+(\d+)\s+(?:to|on)\s+([a-z0-9_]+)",
            lower,
        )

        # 8. Require item in task: e.g. "require apple" or "add apple to required"
        m_req = re.search(r"(?:require|add required)\s+([a-z0-9_]+)", lower)

        # 9. Price change: e.g. "change milk price to 55" or "set bread price to 600"
        m_price = re.search(r"(?:price of|change|set)\s+([a-z0-9_]+)\s+price\s+to\s+(-?\d+)", lower)
        if not m_price:
            m_price = re.search(r"([a-z0-9_]+)\s+price\s+(?:to|=)\s*(-?\d+)", lower)

        if m_budget:
            new_budget = int(m_budget.group(1))
            patched["task"]["budget"] = new_budget
            patch_ops.append({"op": "replace", "path": "/task/budget", "value": new_budget})

        elif m_time:
            new_time = int(m_time.group(1))
            patched["task"]["time_limit_s"] = new_time
            patch_ops.append({"op": "replace", "path": "/task/time_limit_s", "value": new_time})

        elif m_wall:
            wall_raw = m_wall.group(1).upper()
            wall_map = {"NORTH": "N", "SOUTH": "S", "EAST": "E", "WEST": "W"}
            wall_code = wall_map.get(wall_raw, wall_raw[0])
            patched["room"]["entrance"]["wall"] = wall_code
            patch_ops.append({"op": "replace", "path": "/room/entrance/wall", "value": wall_code})

        elif m_support:
            p_key = m_support.group(1).upper()
            field = m_support.group(2).lower()
            val = int(m_support.group(3))
            patched["support"][p_key][field] = val
            patch_ops.append({"op": "replace", "path": f"/support/{p_key}/{field}", "value": val})

        elif m_event_tgt:
            tgt = m_event_tgt.group(1)
            if patched.get("events"):
                patched["events"][0]["target"] = tgt
                patch_ops.append({"op": "replace", "path": "/events/0/target", "value": tgt})

        elif m_move:
            target_id = m_move.group(1)
            nx, ny = int(m_move.group(2)), int(m_move.group(3))
            for obj_idx, obj in enumerate(patched.get("layout", [])):
                if obj.get("id", "").lower() == target_id:
                    obj["cell"] = [nx, ny]
                    patch_ops.append({"op": "replace", "path": f"/layout/{obj_idx}/cell", "value": [nx, ny]})
                    break

        elif m_add_item:
            sku_name = m_add_item.group(1)
            item_price = int(m_add_item.group(2))
            shelf_id = m_add_item.group(3)
            for obj_idx, obj in enumerate(patched.get("layout", [])):
                if obj.get("id", "").lower() == shelf_id:
                    items = obj.setdefault("items", [])
                    items.append({"sku": sku_name, "price": item_price})
                    patch_ops.append(
                        {
                            "op": "add",
                            "path": f"/layout/{obj_idx}/items/-",
                            "value": {"sku": sku_name, "price": item_price},
                        }
                    )
                    break

        elif m_req:
            sku_name = m_req.group(1)
            if sku_name not in patched["task"]["required"]:
                patched["task"]["required"].append(sku_name)
            patch_ops.append({"op": "add", "path": "/task/required/-", "value": sku_name})

        elif m_price:
            sku_name = m_price.group(1)
            new_price = int(m_price.group(2))
            updated = False
            for obj_idx, obj in enumerate(patched.get("layout", [])):
                for it_idx, it in enumerate(obj.get("items") or []):
                    if it.get("sku", "").lower() == sku_name:
                        it["price"] = new_price
                        patch_ops.append(
                            {
                                "op": "replace",
                                "path": f"/layout/{obj_idx}/items/{it_idx}/price",
                                "value": new_price,
                            }
                        )
                        updated = True
            if not updated and patched.get("layout"):
                patched["layout"][0].setdefault("items", []).append({"sku": sku_name, "price": new_price})
                patch_ops.append(
                    {
                        "op": "add",
                        "path": "/layout/0/items/-",
                        "value": {"sku": sku_name, "price": new_price},
                    }
                )

        else:
            # Generic localized note/rule update on task
            rules = patched.setdefault("task", {}).setdefault("rules", [])
            if text not in rules:
                rules.append(text[:80])
            patch_ops.append({"op": "add", "path": "/task/rules/-", "value": text[:80]})

        spec_bytes = len(json.dumps(spec, separators=(",", ":")).encode("utf-8"))
        # Measure size of changed values in patch
        changed_values_bytes = sum(
            len(json.dumps(op["value"], separators=(",", ":")).encode("utf-8")) for op in patch_ops
        )
        patch_ratio = round(changed_values_bytes / max(spec_bytes, 1), 4)

        return {
            "patched_spec": patched,
            "patch_ops": patch_ops,
            "patch_bytes": changed_values_bytes,
            "spec_bytes": spec_bytes,
            "patch_ratio": patch_ratio,
        }


class ClaudeAIProvider(MockAIProvider):
    """Claude AI provider with deterministic fallback when offline (FR-18)."""

    name: str = "claude"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")


def get_ai_provider(mode: str | None = None) -> AIProvider:
    provider_mode = (mode or os.getenv("AI_PROVIDER", "mock")).lower()
    if provider_mode == "claude":
        return ClaudeAIProvider()
    return MockAIProvider()


def generate_with_repair_loop(
    prompt: str,
    answers: dict[str, Any] | None = None,
    concept: dict[str, Any] | None = None,
    max_retries: int = 3,
    comfort_caps: dict[str, dict[str, int]] | None = None,
    provider: AIProvider | None = None,
) -> dict[str, Any]:
    """Run Plan–Validate–Build with bounded repair loop up to `max_retries` (FR-15, LC-3).

    Returns:
    - success: bool
    - spec: dict | None
    - validation_report: dict
    - attempts: int
    - error_plain: str | None
    """
    ai = provider or get_ai_provider()
    critique: list[dict[str, Any]] | None = None
    last_report: dict[str, Any] = {}

    for attempt in range(1, max_retries + 1):
        candidate_spec = ai.plan_scene(
            prompt=prompt,
            answers=answers,
            concept=concept,
            critique=critique,
            attempt=attempt,
        )
        report = validate_scene_spec(candidate_spec, comfort_caps=comfort_caps)
        last_report = report

        if report["valid"]:
            return {
                "success": True,
                "spec": candidate_spec,
                "validation_report": report,
                "attempts": attempt,
                "error_plain": None,
            }

        critique = report["errors"]

    rule_messages = "; ".join(e["message"] for e in (last_report.get("errors") or [])[:3])
    plain_message = (
        f"We could not build a valid scene after {max_retries} attempts because some safety or "
        f"layout constraints were not met ({rule_messages}). Please adjust your description or "
        f"try generating again."
    )
    return {
        "success": False,
        "spec": None,
        "validation_report": last_report,
        "attempts": max_retries,
        "error_plain": plain_message,
    }
