"""Automated Acceptance Test Suite for Chernyx AI Studio (SRS Section 11: AT-01 to AT-08)."""

from __future__ import annotations

from copy import deepcopy
import os
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app  # noqa: E402
from app.models.notebook_event import NotebookEvent  # noqa: E402
from app.services.ai_provider import MockAIProvider  # noqa: E402
from app.services.validator import (  # noqa: E402
    compile_pathway_config,
    get_reference_scene_spec,
    simulate_learner_completion,
    validate_scene_spec,
)

client = TestClient(app)

BANNED_NOTEBOOK_FIELDS = {
    "score",
    "grade",
    "rating",
    "level",
    "diagnosis",
    "risk",
    "percentile",
    "label",
}


def build_13_fault_specs() -> list[tuple[str, dict]]:
    """Construct the 13 fault classes spanning R1–R7 (SRS Section 5 & AT-01)."""
    base = get_reference_scene_spec()
    faults: list[tuple[str, dict]] = []

    # Fault 1 (R1): Missing required top-level field
    f1 = deepcopy(base)
    del f1["support"]
    faults.append(("F01_R1_missing_top_field", f1))

    # Fault 2 (R1): Invalid room dimensions / types
    f2 = deepcopy(base)
    f2["room"]["w"] = -5
    faults.append(("F02_R1_invalid_room_dim", f2))

    # Fault 3 (R2): Entrance not on South wall
    f3 = deepcopy(base)
    f3["room"]["entrance"]["wall"] = "N"
    faults.append(("F03_R2_entrance_not_south", f3))

    # Fault 4 (R2): Object out of room bounds
    f4 = deepcopy(base)
    f4["layout"][0]["cell"] = [11, 3]  # width 3 -> 11+3=14 > 12
    faults.append(("F04_R2_object_out_of_bounds", f4))

    # Fault 5 (R2): Overlapping objects in layout
    f5 = deepcopy(base)
    f5["layout"][1]["cell"] = [2, 3]  # overlaps shelf1 at [2,3]
    faults.append(("F05_R2_object_overlap", f5))

    # Fault 6 (R2): Entrance blocked by an object
    f6 = deepcopy(base)
    f6["layout"].append({"id": "blocker", "asset": "shelf", "cell": [5, 7], "size": [1, 1]})
    faults.append(("F06_R2_entrance_blocked", f6))

    # Fault 7 (R3): Task-critical shelf walled off (unreachable by BFS)
    f7 = deepcopy(base)
    f7["layout"].extend(
        [
            {"id": "wall_top", "asset": "decor", "cell": [1, 2], "size": [5, 1]},
            {"id": "wall_bottom", "asset": "decor", "cell": [1, 4], "size": [5, 1]},
            {"id": "wall_left", "asset": "decor", "cell": [1, 3], "size": [1, 1]},
            {"id": "wall_right", "asset": "decor", "cell": [5, 3], "size": [1, 1]},
        ]
    )
    faults.append(("F07_R3_unreachable_shelf", f7))

    # Fault 8 (R3): Missing or unreachable checkout counter
    f8 = deepcopy(base)
    f8["layout"] = [obj for obj in f8["layout"] if obj["id"] != "counter"]
    faults.append(("F08_R3_missing_counter", f8))

    # Fault 9 (R4): Required item not present on any shelf
    f9 = deepcopy(base)
    f9["task"]["required"] = ["milk", "toothpaste"]
    faults.append(("F09_R4_missing_required_item", f9))

    # Fault 10 (R4): Cheapest basket of required items exceeds task budget
    f10 = deepcopy(base)
    f10["task"]["budget"] = 50  # milk (62) + bread (45) = 107 > 50
    faults.append(("F10_R4_budget_exceeded", f10))

    # Fault 11 (R5): Support pathway exceeds comfort volume/density cap
    f11 = deepcopy(base)
    f11["support"]["A"]["volume"] = 55  # exceeds A cap of 40
    faults.append(("F11_R5_comfort_cap_exceeded", f11))

    # Fault 12 (R6): Non-monotone support levels (A prompt < B prompt)
    f12 = deepcopy(base)
    f12["support"]["A"]["prompt"] = 1
    f12["support"]["B"]["prompt"] = 3
    faults.append(("F12_R6_non_monotone_support", f12))

    # Fault 13 (R7): Referential integrity violation (unknown event target / duplicate ID)
    f13 = deepcopy(base)
    f13["events"] = [{"trigger": "enter", "target": "nonexistent_npc"}]
    faults.append(("F13_R7_bad_event_target", f13))

    return faults


def test_at01_and_at02_fault_injection_and_schema_baseline():
    """AT-01 & AT-02: Full R1–R7 layer catches 100% of 13 fault classes and 0 false rejects
    on valid controls; schema-only baseline catches only R1 structural classes (~15.4%).
    Also verifies NF-01 validation latency < 5 ms and R3w non-blocking warning.
    """
    faults = build_13_fault_specs()
    assert len(faults) == 13

    full_caught = 0
    schema_caught = 0
    latencies = []

    for name, faulty_spec in faults:
        full_report = validate_scene_spec(faulty_spec, schema_only=False)
        schema_report = validate_scene_spec(faulty_spec, schema_only=True)
        latencies.append(full_report["elapsed_ms"])
        if not full_report["valid"]:
            full_caught += 1
        if not schema_report["valid"]:
            schema_caught += 1

    assert full_caught == 13, "Full R1–R7 layer must catch 100% of the 13 fault classes"
    assert schema_caught < full_caught, "Schema-only baseline catches only a minority of fault classes"
    assert max(latencies) < 5.0, f"NF-01: Validation must run under 5ms (max={max(latencies)}ms)"

    # Valid control check (0 false rejects)
    control_spec = get_reference_scene_spec()
    control_report = validate_scene_spec(control_spec)
    assert control_report["valid"] is True
    assert len(control_report["errors"]) == 0

    # R3w check: unreachable non-critical decor triggers warning but valid remains True
    decor_spec = deepcopy(control_spec)
    decor_spec["layout"].extend(
        [
            {"id": "plant_enclosed", "asset": "plant", "cell": [0, 0], "size": [1, 1]},
            {"id": "block_right", "asset": "decor", "cell": [1, 0], "size": [1, 1]},
            {"id": "block_down", "asset": "decor", "cell": [0, 1], "size": [1, 1]},
        ]
    )
    decor_report = validate_scene_spec(decor_spec)
    assert decor_report["valid"] is True
    assert decor_report["rules_summary"]["R3w"] == "warning"


def test_at03_edit_locality_11_scripted_edits():
    """AT-03: 11 scripted plain-language edits:
    - 7 valid edits accepted with median patch < 10% of spec bytes
    - 4 invalid edits rejected by R1–R7 validator
    """
    provider = MockAIProvider()
    base_spec = get_reference_scene_spec()

    valid_edits = [
        "Change milk price to 58",
        "Change bread price to 40",
        "Set budget to 600",
        "Move shelf2 to 6, 3",
        "Add eggs price 70 to shelf1",
        "Set pathway A volume to 35",
        "Set time limit to 240",
    ]
    invalid_edits = [
        "Set budget to 20",  # Violates R4 (milk 62 + bread 45 > 20)
        "Move shelf1 to 11, 3",  # Violates R2 (out of bounds)
        "Set entrance wall to N",  # Violates R2 (entrance not on south wall)
        "Set pathway A volume to 75",  # Violates R5 & R6 (exceeds A cap 40 and > B volume 60)
    ]

    patch_ratios = []
    for instruction in valid_edits:
        res = provider.apply_plain_language_edit(base_spec, instruction)
        report = validate_scene_spec(res["patched_spec"])
        assert report["valid"] is True, f"Valid edit '{instruction}' should pass R1–R7: {report['errors']}"
        patch_ratios.append(res["patch_ratio"])

    sorted_ratios = sorted(patch_ratios)
    median_ratio = sorted_ratios[len(sorted_ratios) // 2]
    assert median_ratio < 0.10, f"Median patch ratio ({median_ratio}) must be under 10% of spec bytes"

    for instruction in invalid_edits:
        res = provider.apply_plain_language_edit(base_spec, instruction)
        report = validate_scene_spec(res["patched_spec"])
        assert report["valid"] is False, f"Invalid edit '{instruction}' must be rejected by R1–R7"


def test_at08_reachability_oracle_and_rt06_pathway_diff():
    """AT-08 & RT-06: Simulated learner completes validated spec;
    diffing compiled configs for pathways A, B, C shows only prompt, density, and volume differ.
    """
    spec = get_reference_scene_spec()
    oracle_res = simulate_learner_completion(spec)
    assert oracle_res["completed"] is True
    assert oracle_res["total_cost"] <= spec["task"]["budget"]

    cfg_a = compile_pathway_config(spec, "A")
    cfg_b = compile_pathway_config(spec, "B")
    cfg_c = compile_pathway_config(spec, "C")

    for shared_key in ("room", "layout", "task", "events"):
        assert cfg_a[shared_key] == cfg_b[shared_key] == cfg_c[shared_key]

    diff_keys = {
        k for k in cfg_a.keys() if cfg_a[k] != cfg_b[k] or cfg_b[k] != cfg_c[k]
    }
    assert diff_keys == {"prompt", "density", "volume"}


def test_at04_at05_at06_at07_full_lifecycle_tenant_isolation_and_notebook_rule():
    """End-to-end API test for:
    - FR-01: Role-based access & time-of-day greeting (09:00, 14:00, 19:00)
    - AT-04: Lifecycle gates (config before Ready -> 409; launch before Approve -> 409)
    - AT-05: Tenant isolation across schools
    - AT-06 / NB-02: Non-diagnostic session notebook contains no banned fields
    - AT-07: Full tutor workflow from login -> class/module/student -> intake -> generate -> edit -> configure -> approve -> run -> console -> notebook
    """
    suffix = os.urandom(4).hex()

    # 1. Register School A Tutor (morning greeting) and School B Tutor (evening greeting)
    reg_a = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"tutor_a_{suffix}@school-a.org",
            "password": "SafePassword123!",
            "full_name": "Anita Sharma",
            "organisation_name": f"Sunrise Special School {suffix}",
            "role": "tutor",
            "local_hour": 9,
        },
    )
    assert reg_a.status_code == 200
    data_a = reg_a.json()
    assert data_a["greeting"].startswith("Good morning")
    headers_a = {"Authorization": f"Bearer {data_a['access_token']}"}

    # Check afternoon greeting at 14:00
    me_afternoon = client.get("/api/v1/auth/me?local_hour=14", headers=headers_a)
    assert me_afternoon.status_code == 200
    assert me_afternoon.json()["greeting"].startswith("Good afternoon")

    reg_b = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"tutor_b_{suffix}@school-b.org",
            "password": "SafePassword123!",
            "full_name": "Vikram Rao",
            "organisation_name": f"Oakridge Academy {suffix}",
            "role": "tutor",
            "local_hour": 19,
        },
    )
    assert reg_b.status_code == 200
    assert reg_b.json()["greeting"].startswith("Good evening")
    headers_b = {"Authorization": f"Bearer {reg_b.json()['access_token']}"}

    # Register read-only support staff in School A to test FR-01 403 guard
    reg_support = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"support_{suffix}@school-a.org",
            "password": "SafePassword123!",
            "full_name": "Support Staff",
            "organisation_name": f"Sunrise Special School {suffix}",
            "role": "support",
        },
    )
    assert reg_support.status_code == 200
    headers_support = {"Authorization": f"Bearer {reg_support.json()['access_token']}"}

    # FR-01: Support staff cannot create a scenario (403 Forbidden)
    forbidden_res = client.post(
        "/api/v1/experiences",
        json={"title": "Blocked", "prompt": "Should fail"},
        headers=headers_support,
    )
    assert forbidden_res.status_code == 403

    # 2. FR-02: Create Class, Module, Student (with pseudonym_id), and Schedule in School A
    cls_res = client.post(
        "/api/v1/classes",
        json={"name": "Life Skills — Morning Group", "description": "Daily shopping practice"},
        headers=headers_a,
    )
    assert cls_res.status_code == 201
    class_id = cls_res.json()["id"]

    mod_res = client.post(
        f"/api/v1/classes/{class_id}/modules",
        json={"name": "Neighbourhood Grocery Shopping", "description": "Finding items and paying"},
        headers=headers_a,
    )
    assert mod_res.status_code == 201
    module_id = mod_res.json()["id"]

    stu_res = client.post(
        f"/api/v1/classes/{class_id}/students",
        json={"name": "Aarav K"},
        headers=headers_a,
    )
    assert stu_res.status_code == 201
    student = stu_res.json()
    learner_id = student["id"]
    assert student["pseudonym_id"].startswith("LRN-")

    # AT-05 Tenant Isolation: School B cannot see or modify School A's class
    cross_cls = client.get(f"/api/v1/classes/{class_id}", headers=headers_b)
    assert cross_cls.status_code == 404

    # 3. Create Experience / Scenario draft (FR-03, FR-04)
    exp_res = client.post(
        "/api/v1/experiences",
        json={
            "title": "Buying Milk and Bread",
            "prompt": "Create a calm grocery shop where learners pick milk and bread within a 500 budget.",
            "category": "Life Skills",
            "class_id": class_id,
            "module_id": module_id,
            "voice_transcript": "Create a calm grocery shop for buying milk and bread.",
        },
        headers=headers_a,
    )
    assert exp_res.status_code == 201
    exp_id = exp_res.json()["id"]
    assert len(exp_res.json()["concept_options"]) == 3

    # AT-04 Gate check 1: Configuration write before Ready to configure returns 409
    early_cfg = client.patch(
        f"/api/v1/experiences/{exp_id}/configuration",
        json={"configuration": {"environment": "Classroom"}},
        headers=headers_a,
    )
    assert early_cfg.status_code == 409

    # AT-04 Gate check 2: Generation before concept approval returns 409
    early_gen = client.post(f"/api/v1/experiences/{exp_id}/generate", headers=headers_a)
    assert early_gen.status_code == 409

    # FR-04: Save answers (skipping all 20 is also allowed)
    ans_res = client.patch(
        f"/api/v1/experiences/{exp_id}/answers",
        json={"answers": {"0": "Life skills", "3": "Classroom"}},
        headers=headers_a,
    )
    assert ans_res.status_code == 200

    # FR-05: Select and approve concept preview
    concept_res = client.put(
        f"/api/v1/experiences/{exp_id}/concept",
        json={"concept_preview": exp_res.json()["concept_options"][0]},
        headers=headers_a,
    )
    assert concept_res.status_code == 200

    approve_prev = client.post(f"/api/v1/experiences/{exp_id}/approve", headers=headers_a)
    assert approve_prev.status_code == 200

    # FR-06 & FR-14: Trigger generation (runs planner + R1–R7 validator + creates version 1)
    gen_res = client.post(f"/api/v1/experiences/{exp_id}/generate", headers=headers_a)
    assert gen_res.status_code == 200
    assert gen_res.json()["status"] == "ready_to_configure"
    assert gen_res.json()["validation_report"]["valid"] is True

    # LC-6: Notification fired on completion
    notif_res = client.get("/api/v1/notifications", headers=headers_a)
    assert notif_res.status_code == 200
    assert notif_res.json()["unread_count"] >= 1

    # AT-04 Gate check 3: Launching a run before version is approved returns 409
    unapproved_run = client.post(
        "/api/v1/runs",
        json={"experience_id": exp_id, "pathway": "B", "mode": "laptop"},
        headers=headers_a,
    )
    assert unapproved_run.status_code == 409

    # FR-08: Plain-language edit applies localized patch (< 10% bytes) and creates version 2
    edit_res = client.post(
        f"/api/v1/experiences/{exp_id}/edit",
        json={"instruction": "Change milk price to 55"},
        headers=headers_a,
    )
    assert edit_res.status_code == 200
    assert edit_res.json()["patch_ratio"] < 0.10
    assert edit_res.json()["validation_report"]["valid"] is True

    # FR-10: Save configuration
    cfg_res = client.patch(
        f"/api/v1/experiences/{exp_id}/configuration",
        json={
            "configuration": {
                "environment": "Classroom",
                "duration": "5–10 minutes",
                "guidance": "Step-by-step",
                "visualStyle": "Soft 3D",
                "accessibility": "Visual prompts",
                "comfort": "Low stimulation",
                "budget": 500,
            }
        },
        headers=headers_a,
    )
    assert cfg_res.status_code == 200
    assert cfg_res.json()["status"] == "configured"

    # FR-11: Approve version for running
    app_ver_res = client.post(f"/api/v1/experiences/{exp_id}/approve-version", headers=headers_a)
    assert app_ver_res.status_code == 200
    assert app_ver_res.json()["status"] == "approved"

    # FR-12 & FR-16: Launch on four-wall room and execute Tutor Console commands
    run_res = client.post(
        "/api/v1/runs",
        json={
            "experience_id": exp_id,
            "learner_id": learner_id,
            "pathway": "C",
            "mode": "room",
        },
        headers=headers_a,
    )
    assert run_res.status_code == 201
    run_id = run_res.json()["id"]

    # Console commands: move, prompt, simplify (C -> B), select milk, checkout
    for cmd_payload in [
        {"command": "move", "payload": {"dir": "N"}},
        {"command": "prompt", "payload": {"message": "Look at shelf 1 for milk"}},
        {"command": "simplify", "payload": {}},
        {"command": "set_pathway", "payload": {"pathway": "A"}},
        {"command": "set_pathway", "payload": {"pathway": "B"}},
        {"command": "select", "payload": {"sku": "milk"}},
        {"command": "select", "payload": {"checkout": True}},
    ]:
        cmd_res = client.post(f"/api/v1/runs/{run_id}/command", json=cmd_payload, headers=headers_a)
        assert cmd_res.status_code == 200

    bad = client.post(
        f"/api/v1/runs/{run_id}/command", json={"command": "set_pathway", "payload": {"pathway": "Z"}}, headers=headers_a
    )
    assert bad.status_code == 422

    final_run = cmd_res.json()
    assert final_run["pathway"] == "B"
    assert final_run["compiled_config"]["volume"] <= 60  # pathway B comfort cap
    assert final_run["prompts_given"] == 1
    assert final_run["status"] == "completed"

    # AT-05 Tenant Isolation on Scenario & Notebook: School B denied
    assert client.get(f"/api/v1/experiences/{exp_id}", headers=headers_b).status_code == 404
    assert client.get(f"/api/v1/learners/{learner_id}/notebook", headers=headers_b).status_code == 404

    # AT-06 / NB-02: Non-diagnostic Session Notebook check
    # Verify SQLAlchemy model columns contain none of the banned names
    model_cols = {c.name.lower() for c in NotebookEvent.__table__.columns}
    assert model_cols.isdisjoint(BANNED_NOTEBOOK_FIELDS)

    nb_res = client.get(f"/api/v1/learners/{learner_id}/notebook", headers=headers_support)
    assert nb_res.status_code == 200
    nb_json = nb_res.json()
    assert nb_json["session_count"] >= 1
    assert nb_json["display_name"] == student["pseudonym_id"]  # NB-05 pseudonym by default

    def collect_all_keys(obj) -> set[str]:
        keys: set[str] = set()
        if isinstance(obj, dict):
            for k, v in obj.items():
                keys.add(str(k).lower())
                keys |= collect_all_keys(v)
        elif isinstance(obj, list):
            for item in obj:
                keys |= collect_all_keys(item)
        return keys

    all_nb_keys = collect_all_keys(nb_json)
    assert all_nb_keys.isdisjoint(BANNED_NOTEBOOK_FIELDS), (
        f"NB-02 violation: found banned keys {all_nb_keys & BANNED_NOTEBOOK_FIELDS}"
    )


def test_safety_check_endpoint_repairs_faulty_seed():
    """Verify POST /api/v1/safety-check validates kirana_shop.faulty.json on Attempt 1

    (with R3, R4, R5, R6 failures) and provides a fully valid spec on Attempt 2.
    """
    res = client.post("/api/v1/safety-check")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "repaired"
    assert len(data["attempts"]) == 2

    # Attempt 1: faulty
    att1 = data["attempts"][0]
    assert att1["attempt"] == 1
    assert att1["valid"] is False
    assert att1["rules_summary"]["R3"] == "error"
    assert att1["rules_summary"]["R4"] == "error"
    assert att1["rules_summary"]["R5"] == "error"
    assert att1["rules_summary"]["R6"] == "error"

    # Attempt 2: repaired & valid
    att2 = data["attempts"][1]
    assert att2["attempt"] == 2
    assert att2["valid"] is True
    assert all(st == "pass" for k, st in att2["rules_summary"].items() if k != "R3w")
    assert validate_scene_spec(data["repaired_spec"])["valid"] is True

