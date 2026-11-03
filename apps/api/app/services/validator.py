"""Scene specification constraint layer (R1–R7) and reachability oracle.

Governing principle (SRS Section 1 & Section 5):
The AI plans, the backend validates, the engine builds (Plan–Validate–Build).
No AI output reaches a learner without passing rules R1–R7.
Errors block; warnings (R3w) do not.
"""

from __future__ import annotations

from collections import deque
from copy import deepcopy
import time
from typing import Any

DEFAULT_COMFORT_CAPS: dict[str, dict[str, int]] = {
    "A": {"volume": 40, "density": 2},
    "B": {"volume": 60, "density": 3},
    "C": {"volume": 80, "density": 5},
}

VALID_WALLS = {"N", "S", "E", "W"}
VALID_ASSETS = {
    "shelf",
    "counter",
    "fridge",
    "basket_stand",
    "sign",
    "plant",
    "bench",
    "table",
    "kiosk",
    "decor",
}
VALID_EVENT_TRIGGERS = {"enter", "pickup", "checkout", "timer", "what_if", "prompt"}
BUILTIN_ACTORS = {"shopkeeper"}


def get_reference_scene_spec() -> dict[str, Any]:
    """Return the reference 12x8 shop scene specification from SRS Section 5."""
    return {
        "room": {
            "w": 12,
            "h": 8,
            "entrance": {"wall": "S", "cells": [[5, 7], [6, 7]]},
        },
        "layout": [
            {
                "id": "shelf1",
                "asset": "shelf",
                "cell": [2, 3],
                "size": [3, 1],
                "items": [
                    {"sku": "milk", "price": 62},
                    {"sku": "bread", "price": 45},
                ],
            },
            {
                "id": "shelf2",
                "asset": "shelf",
                "cell": [6, 2],
                "size": [2, 1],
                "items": [
                    {"sku": "apple", "price": 30},
                    {"sku": "juice", "price": 55},
                ],
            },
            {
                "id": "counter",
                "asset": "counter",
                "cell": [10, 6],
                "size": [1, 1],
            },
        ],
        "task": {
            "required": ["milk", "bread"],
            "budget": 500,
            "time_limit_s": 300,
            "difficulty": "Developing",
            "rules": [
                "Pick up every item on the shopping list",
                "Keep total basket cost within budget",
                "Pay at the counter when finished",
            ],
            "what_ifs": [
                "Preferred brand is out of stock",
                "Shopkeeper asks if you need a bag",
            ],
        },
        "support": {
            "A": {"prompt": 3, "density": 2, "volume": 40},
            "B": {"prompt": 2, "density": 3, "volume": 60},
            "C": {"prompt": 1, "density": 5, "volume": 80},
        },
        "events": [
            {"trigger": "enter", "target": "shopkeeper"},
        ],
    }


def _is_int(val: Any) -> bool:
    return isinstance(val, int) and not isinstance(val, bool)


def _is_num(val: Any) -> bool:
    return isinstance(val, (int, float)) and not isinstance(val, bool)


def validate_scene_spec(
    spec: Any,
    comfort_caps: dict[str, dict[str, int]] | None = None,
    schema_only: bool = False,
) -> dict[str, Any]:
    """Validate a scene spec against rules R1–R7 (and R3w warning).

    Returns a dictionary containing:
    - valid: bool (True if zero errors)
    - errors: list of {rule, code, message, target}
    - warnings: list of {rule, code, message, target}
    - rules_summary: dict mapping R1..R7 and R3w to status ("pass"|"error"|"warning")
    - elapsed_ms: float
    """
    start_ns = time.perf_counter_ns()
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    caps = comfort_caps or DEFAULT_COMFORT_CAPS

    def add_error(rule: str, code: str, message: str, target: str | None = None):
        errors.append({"rule": rule, "code": code, "message": message, "target": target})

    def add_warning(rule: str, code: str, message: str, target: str | None = None):
        warnings.append({"rule": rule, "code": code, "message": message, "target": target})

    # -------------------------------------------------------------------------
    # R1: Structure (JSON schema, types, required fields, enums)
    # -------------------------------------------------------------------------
    if not isinstance(spec, dict):
        add_error("R1", "invalid_root", "Scene specification must be a JSON object.")
        return _finalize_report(errors, warnings, start_ns)

    required_top = {"room", "layout", "task", "support", "events"}
    missing_top = required_top - set(spec.keys())
    if missing_top:
        add_error(
            "R1",
            "missing_required_fields",
            f"Missing required top-level fields: {', '.join(sorted(missing_top))}.",
        )
        return _finalize_report(errors, warnings, start_ns)

    room = spec.get("room")
    layout = spec.get("layout")
    task = spec.get("task")
    support = spec.get("support")
    events = spec.get("events")

    if not isinstance(room, dict):
        add_error("R1", "invalid_room", "'room' must be an object.")
    else:
        w = room.get("w")
        h = room.get("h")
        entrance = room.get("entrance")
        if not (_is_int(w) and _is_int(h) and 3 <= w <= 64 and 3 <= h <= 64):
            add_error("R1", "invalid_room_dimensions", "'room.w' and 'room.h' must be integers between 3 and 64.")
        if not isinstance(entrance, dict):
            add_error("R1", "invalid_entrance", "'room.entrance' must be an object.")
        else:
            wall = entrance.get("wall")
            cells = entrance.get("cells")
            if not isinstance(wall, str) or wall not in VALID_WALLS:
                add_error("R1", "invalid_entrance_wall", "'room.entrance.wall' must be one of N, S, E, W.")
            if not isinstance(cells, list) or len(cells) == 0:
                add_error("R1", "invalid_entrance_cells", "'room.entrance.cells' must be a non-empty list of [x, y] pairs.")
            else:
                for c in cells:
                    if not (isinstance(c, (list, tuple)) and len(c) == 2 and _is_int(c[0]) and _is_int(c[1])):
                        add_error("R1", "invalid_entrance_cell_coord", "Each entrance cell must be an [x, y] integer pair.")
                        break

    if not isinstance(layout, list) or len(layout) == 0:
        add_error("R1", "invalid_layout", "'layout' must be a non-empty list of scene objects.")
    else:
        for idx, obj in enumerate(layout):
            if not isinstance(obj, dict):
                add_error("R1", "invalid_layout_object", f"layout[{idx}] must be an object.")
                continue
            obj_id = obj.get("id")
            asset = obj.get("asset")
            cell = obj.get("cell")
            size = obj.get("size")
            if not isinstance(obj_id, str) or not obj_id.strip():
                add_error("R1", "invalid_object_id", f"layout[{idx}].id must be a non-empty string.")
            if not isinstance(asset, str) or not asset.strip():
                add_error("R1", "invalid_object_asset", f"layout[{idx}].asset must be a non-empty string.")
            if not (isinstance(cell, (list, tuple)) and len(cell) == 2 and _is_int(cell[0]) and _is_int(cell[1])):
                add_error("R1", "invalid_object_cell", f"layout[{idx}].cell must be an [x, y] integer pair.", str(obj_id))
            if not (
                isinstance(size, (list, tuple))
                and len(size) == 2
                and _is_int(size[0])
                and _is_int(size[1])
                and size[0] > 0
                and size[1] > 0
            ):
                add_error("R1", "invalid_object_size", f"layout[{idx}].size must be a positive [w, h] integer pair.", str(obj_id))
            if "items" in obj and obj["items"] is not None:
                if not isinstance(obj["items"], list):
                    add_error("R1", "invalid_object_items", f"layout[{idx}].items must be a list.", str(obj_id))
                else:
                    for item in obj["items"]:
                        if not isinstance(item, dict):
                            add_error("R1", "invalid_item", f"Item in {obj_id} must be an object.", str(obj_id))
                            continue
                        sku = item.get("sku")
                        price = item.get("price")
                        if not isinstance(sku, str) or not sku.strip():
                            add_error("R1", "invalid_item_sku", f"Item in {obj_id} requires a string 'sku'.", str(obj_id))
                        if not _is_num(price) or price < 0:
                            add_error("R1", "invalid_item_price", f"Item '{sku}' in {obj_id} requires a non-negative price.", str(obj_id))

    if not isinstance(task, dict):
        add_error("R1", "invalid_task", "'task' must be an object.")
    else:
        req_items = task.get("required")
        budget = task.get("budget")
        if not isinstance(req_items, list) or len(req_items) == 0 or not all(isinstance(x, str) and x.strip() for x in req_items):
            add_error("R1", "invalid_task_required", "'task.required' must be a non-empty list of item SKU strings.")
        if not _is_num(budget) or budget <= 0:
            add_error("R1", "invalid_task_budget", "'task.budget' must be a positive number.")

    if not isinstance(support, dict) or set(support.keys()) < {"A", "B", "C"}:
        add_error("R1", "invalid_support", "'support' must define pathways 'A', 'B', and 'C'.")
    else:
        for pathway_key in ("A", "B", "C"):
            p_cfg = support.get(pathway_key)
            if not isinstance(p_cfg, dict):
                add_error("R1", "invalid_pathway", f"'support.{pathway_key}' must be an object.")
                continue
            for field_name in ("prompt", "density", "volume"):
                val = p_cfg.get(field_name)
                if not _is_num(val) or val < 0:
                    add_error(
                        "R1",
                        "invalid_pathway_field",
                        f"'support.{pathway_key}.{field_name}' must be a non-negative number.",
                    )

    if not isinstance(events, list):
        add_error("R1", "invalid_events", "'events' must be a list.")
    else:
        for idx, ev in enumerate(events):
            if not isinstance(ev, dict):
                add_error("R1", "invalid_event", f"events[{idx}] must be an object.")
                continue
            trig = ev.get("trigger")
            tgt = ev.get("target")
            if not isinstance(trig, str) or trig not in VALID_EVENT_TRIGGERS:
                add_error("R1", "invalid_event_trigger", f"events[{idx}].trigger must be one of {sorted(VALID_EVENT_TRIGGERS)}.")
            if not isinstance(tgt, str) or not tgt.strip():
                add_error("R1", "invalid_event_target", f"events[{idx}].target must be a non-empty string.")

    if errors or schema_only:
        return _finalize_report(errors, warnings, start_ns)

    # -------------------------------------------------------------------------
    # R7: Referential integrity (Unique IDs; every event target exists)
    # -------------------------------------------------------------------------
    seen_ids: set[str] = set()
    for obj in layout:
        oid = obj["id"]
        if oid in seen_ids:
            add_error("R7", "duplicate_object_id", f"Duplicate object id '{oid}' in layout.", oid)
        seen_ids.add(oid)

    valid_targets = seen_ids | BUILTIN_ACTORS | set(spec.get("actors", []))
    for ev in events:
        tgt = ev["target"]
        if tgt not in valid_targets:
            add_error("R7", "unknown_event_target", f"Event target '{tgt}' does not exist in scene layout.", tgt)

    # -------------------------------------------------------------------------
    # R2: Geometry (Objects inside room bounds; no overlaps; entrance on S wall and clear)
    # -------------------------------------------------------------------------
    w = room["w"]
    h = room["h"]
    entrance = room["entrance"]
    entrance_wall = entrance["wall"]
    entrance_cells: list[tuple[int, int]] = [(int(c[0]), int(c[1])) for c in entrance["cells"]]

    if entrance_wall != "S":
        add_error("R2", "entrance_not_south", f"Entrance must be on the south wall ('S'), got '{entrance_wall}'.")

    for ex, ey in entrance_cells:
        if not (0 <= ex < w and 0 <= ey < h):
            add_error("R2", "entrance_out_of_bounds", f"Entrance cell [{ex}, {ey}] is outside room bounds ({w}x{h}).")
        elif ey != h - 1:
            add_error("R2", "entrance_not_on_south_edge", f"Entrance cell [{ex}, {ey}] must lie on south edge y={h - 1}.")

    occupied_by: dict[tuple[int, int], str] = {}
    object_Footprints: dict[str, list[tuple[int, int]]] = {}

    for obj in layout:
        oid = obj["id"]
        ox, oy = int(obj["cell"][0]), int(obj["cell"][1])
        ow, oh = int(obj["size"][0]), int(obj["size"][1])

        if ox < 0 or oy < 0 or ox + ow > w or oy + oh > h:
            add_error(
                "R2",
                "object_out_of_bounds",
                f"Object '{oid}' at [{ox}, {oy}] size [{ow}, {oh}] exceeds room bounds ({w}x{h}).",
                oid,
            )

        footprint: list[tuple[int, int]] = []
        for cx in range(ox, ox + ow):
            for cy in range(oy, oy + oh):
                footprint.append((cx, cy))
                if (cx, cy) in occupied_by:
                    other_id = occupied_by[(cx, cy)]
                    add_error(
                        "R2",
                        "object_overlap",
                        f"Object '{oid}' overlaps with '{other_id}' at cell [{cx}, {cy}].",
                        oid,
                    )
                else:
                    occupied_by[(cx, cy)] = oid
        object_Footprints[oid] = footprint

    entrance_set = set(entrance_cells)
    for ex, ey in entrance_set:
        if (ex, ey) in occupied_by:
            blocker = occupied_by[(ex, ey)]
            add_error(
                "R2",
                "entrance_blocked",
                f"Entrance cell [{ex}, {ey}] is blocked by object '{blocker}'.",
                blocker,
            )

    # -------------------------------------------------------------------------
    # R3 & R3w: Reachability (BFS from entrance to every task-critical object & counter)
    # -------------------------------------------------------------------------
    reachable_walkable = _bfs_reachable_cells(w, h, entrance_cells, set(occupied_by.keys()))
    required_skus = set(task["required"])

    has_counter = False
    for obj in layout:
        oid = obj["id"]
        asset = obj["asset"]
        items = obj.get("items") or []
        obj_skus = {it["sku"] for it in items if isinstance(it, dict) and "sku" in it}
        is_counter = asset == "counter" or oid == "counter"
        if is_counter:
            has_counter = True
        is_critical = (
            is_counter
            or bool(obj_skus & required_skus)
            or bool(obj.get("critical", False))
            or asset == "shelf" and len(items) > 0 and bool(obj_skus & required_skus)
        )

        adj_cells = _adjacent_walkable_cells(object_Footprints.get(oid, []), w, h, set(occupied_by.keys()))
        is_obj_reachable = any(c in reachable_walkable for c in adj_cells)

        if not is_obj_reachable:
            if is_critical:
                add_error(
                    "R3",
                    "unreachable_critical_object",
                    f"Task-critical object '{oid}' is not reachable from the entrance.",
                    oid,
                )
            else:
                add_warning(
                    "R3w",
                    "unreachable_decor",
                    f"Non-critical decor object '{oid}' is unreachable from the entrance.",
                    oid,
                )

    if not has_counter:
        add_error("R3", "missing_counter", "Scene layout must include a reachable checkout counter.")

    # -------------------------------------------------------------------------
    # R4: Solvability (Every required item on a shelf; cheapest basket <= budget)
    # -------------------------------------------------------------------------
    cheapest_price_by_sku: dict[str, float] = {}
    for obj in layout:
        for it in obj.get("items") or []:
            sku = it["sku"]
            price = float(it["price"])
            if sku not in cheapest_price_by_sku or price < cheapest_price_by_sku[sku]:
                cheapest_price_by_sku[sku] = price

    missing_skus = [sku for sku in task["required"] if sku not in cheapest_price_by_sku]
    if missing_skus:
        add_error(
            "R4",
            "missing_required_items",
            f"Required task items not found on any shelf: {', '.join(missing_skus)}.",
        )
    else:
        cheapest_basket = sum(cheapest_price_by_sku[sku] for sku in task["required"])
        if cheapest_basket > float(task["budget"]):
            add_error(
                "R4",
                "budget_insufficient",
                f"Cheapest basket of required items ({cheapest_basket:.0f}) exceeds task budget ({task['budget']}).",
            )

    # -------------------------------------------------------------------------
    # R5: Comfort caps (Volume and density within caps per profile A, B, C)
    # -------------------------------------------------------------------------
    for p_key in ("A", "B", "C"):
        p_cfg = support[p_key]
        p_caps = caps.get(p_key, DEFAULT_COMFORT_CAPS[p_key])
        if p_cfg["volume"] > p_caps["volume"]:
            add_error(
                "R5",
                "volume_exceeds_cap",
                f"Pathway {p_key} volume ({p_cfg['volume']}) exceeds cap ({p_caps['volume']}).",
                p_key,
            )
        if p_cfg["density"] > p_caps["density"]:
            add_error(
                "R5",
                "density_exceeds_cap",
                f"Pathway {p_key} density ({p_cfg['density']}) exceeds cap ({p_caps['density']}).",
                p_key,
            )

    # -------------------------------------------------------------------------
    # R6: Monotone support (Prompt A >= B >= C; Density A <= B <= C; Volume A <= B <= C)
    # -------------------------------------------------------------------------
    a, b, c = support["A"], support["B"], support["C"]
    if not (a["prompt"] >= b["prompt"] >= c["prompt"]):
        add_error(
            "R6",
            "non_monotone_prompt",
            f"Support prompt levels must satisfy A >= B >= C (got A={a['prompt']}, B={b['prompt']}, C={c['prompt']}).",
        )
    if not (a["density"] <= b["density"] <= c["density"]):
        add_error(
            "R6",
            "non_monotone_density",
            f"Support density must satisfy A <= B <= C (got A={a['density']}, B={b['density']}, C={c['density']}).",
        )
    if not (a["volume"] <= b["volume"] <= c["volume"]):
        add_error(
            "R6",
            "non_monotone_volume",
            f"Support volume must satisfy A <= B <= C (got A={a['volume']}, B={b['volume']}, C={c['volume']}).",
        )

    return _finalize_report(errors, warnings, start_ns)


def _bfs_reachable_cells(
    w: int,
    h: int,
    start_cells: list[tuple[int, int]],
    occupied: set[tuple[int, int]],
) -> set[tuple[int, int]]:
    visited: set[tuple[int, int]] = set()
    queue: deque[tuple[int, int]] = deque()

    for sx, sy in start_cells:
        if 0 <= sx < w and 0 <= sy < h and (sx, sy) not in occupied:
            visited.add((sx, sy))
            queue.append((sx, sy))

    while queue:
        cx, cy = queue.popleft()
        for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in occupied and (nx, ny) not in visited:
                visited.add((nx, ny))
                queue.append((nx, ny))

    return visited


def _adjacent_walkable_cells(
    footprint: list[tuple[int, int]],
    w: int,
    h: int,
    occupied: set[tuple[int, int]],
) -> list[tuple[int, int]]:
    adj: list[tuple[int, int]] = []
    for fx, fy in footprint:
        for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            nx, ny = fx + dx, fy + dy
            if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in occupied:
                adj.append((nx, ny))
    return adj


def _finalize_report(
    errors: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
    start_ns: int,
) -> dict[str, Any]:
    elapsed_ms = round((time.perf_counter_ns() - start_ns) / 1_000_000, 3)
    error_rules = {e["rule"] for e in errors}
    warn_rules = {w["rule"] for w in warnings}
    rules_summary = {}
    for r in ("R1", "R2", "R3", "R4", "R5", "R6", "R7"):
        rules_summary[r] = "error" if r in error_rules else "pass"
    rules_summary["R3w"] = "warning" if "R3w" in warn_rules else "pass"

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "rules_summary": rules_summary,
        "elapsed_ms": elapsed_ms,
    }


def compile_pathway_config(spec: dict[str, Any], pathway: str = "B") -> dict[str, Any]:
    """Compile runtime scene configuration for pathway A, B, or C (RT-06).

    Support pathway A/B/C changes prompt level, scene density and volume only;
    the layout and task are identical across pathways.
    """
    pathway_key = pathway if pathway in ("A", "B", "C") else "B"
    support_cfg = deepcopy(spec.get("support", {}).get(pathway_key, {"prompt": 2, "density": 3, "volume": 60}))
    return {
        "room": deepcopy(spec.get("room", {})),
        "layout": deepcopy(spec.get("layout", [])),
        "task": deepcopy(spec.get("task", {})),
        "events": deepcopy(spec.get("events", [])),
        "prompt": support_cfg["prompt"],
        "density": support_cfg["density"],
        "volume": support_cfg["volume"],
    }


def simulate_learner_completion(spec: dict[str, Any]) -> dict[str, Any]:
    """Reachability and solvability oracle (AT-08).

    Simulates a learner starting at the entrance, navigating via BFS shortest paths
    to pick up every required item within budget, and checking out at the counter.
    """
    report = validate_scene_spec(spec)
    if not report["valid"]:
        return {"completed": False, "reason": "Spec failed validation", "steps": [], "total_cost": 0}

    room = spec["room"]
    w, h = int(room["w"]), int(room["h"])
    layout = spec["layout"]
    occupied: set[tuple[int, int]] = set()
    footprints: dict[str, list[tuple[int, int]]] = {}

    for obj in layout:
        ox, oy = int(obj["cell"][0]), int(obj["cell"][1])
        ow, oh = int(obj["size"][0]), int(obj["size"][1])
        fp = [(cx, cy) for cx in range(ox, ox + ow) for cy in range(oy, oy + oh)]
        footprints[obj["id"]] = fp
        occupied.update(fp)

    reachable = _bfs_reachable_cells(w, h, [(int(c[0]), int(c[1])) for c in room["entrance"]["cells"]], occupied)
    current_pos = (int(room["entrance"]["cells"][0][0]), int(room["entrance"]["cells"][0][1]))
    steps: list[dict[str, Any]] = [{"action": "enter", "cell": list(current_pos)}]
    total_cost = 0

    for req_sku in spec["task"]["required"]:
        # Find reachable shelf with cheapest price for req_sku
        best_candidate = None
        for obj in layout:
            adj = [c for c in _adjacent_walkable_cells(footprints[obj["id"]], w, h, occupied) if c in reachable]
            if not adj:
                continue
            for it in obj.get("items") or []:
                if it["sku"] == req_sku:
                    price = float(it["price"])
                    if best_candidate is None or price < best_candidate[0]:
                        best_candidate = (price, obj["id"], adj[0])
        if best_candidate is None:
            return {"completed": False, "reason": f"Cannot reach item {req_sku}", "steps": steps, "total_cost": total_cost}

        price, shelf_id, target_cell = best_candidate
        current_pos = target_cell
        total_cost += price
        steps.append({"action": "pickup", "sku": req_sku, "shelf_id": shelf_id, "price": price, "cell": list(current_pos)})

    # Navigate to counter
    counter_obj = next((o for o in layout if o["asset"] == "counter" or o["id"] == "counter"), None)
    if not counter_obj:
        return {"completed": False, "reason": "No counter", "steps": steps, "total_cost": total_cost}

    counter_adj = [c for c in _adjacent_walkable_cells(footprints[counter_obj["id"]], w, h, occupied) if c in reachable]
    if not counter_adj:
        return {"completed": False, "reason": "Counter unreachable", "steps": steps, "total_cost": total_cost}

    current_pos = counter_adj[0]
    steps.append({"action": "checkout", "counter_id": counter_obj["id"], "cell": list(current_pos), "total_cost": total_cost})

    return {
        "completed": total_cost <= float(spec["task"]["budget"]),
        "steps": steps,
        "total_cost": total_cost,
        "budget": spec["task"]["budget"],
    }
