# DACAL Immersive AI Classroom — Application Development Brief

**Project:** AI-powered immersive learning platform for special educators
**Partners:** Chernyx AI Labs × DACAL (AHI-DACAL Special Education Department)
**Sources synthesized:** `Immersive AI Classroom Redesign.pdf` / `.pptx`, `SPED-Term 1 Curriculum.docx`
**Status:** Pre-development specification (Phase 1–2 scope)

---

## 1. Problem Statement

Special educators don't need more content — they need more ways to **practice**. Students often understand a concept in the classroom but struggle when it appears in the real world:

| Classroom concept | Real-world situation |
|---|---|
| Learning about money | Buying something in a shop |
| Learning about communication | Speaking to a shopkeeper |
| Learning about transportation | Navigating a railway station |

### The environmental gap

| Real world | Traditional classroom |
|---|---|
| Too unpredictable | Worksheets |
| Difficult to control | Flashcards |
| Potentially overwhelming | Role play |
| Hard to repeat | Verbal explanation |
| Difficult to personalize | Limited physical simulation |

**The missing layer is an environment that educators can control** — enabling repeated, contextualized practice.

### Core shift

Move from teaching **ABOUT** a situation (explain → show → discuss/worksheet → real-world exposure) to practicing **IN** the situation (create environment → enter situation → practice & make decisions → repeat & adapt).

---

## 2. Product Vision

> Give educators the power to create worlds where students can practice life.

```
EDUCATOR INTENT  →  AI  →  IMMERSIVE ROOM  →  LEARNING EXPERIENCE
Decides what        Translates intent     Delivery            Educator remains
needs learning      into an activity      mechanism           in control
```

**Key principle:** The projector system is infrastructure. **The product is the intelligence and authoring layer.** Every new activity should *not* require a software development cycle.

| Current model | Proposed model |
|---|---|
| Developer builds activity (code) | Educator describes objective (natural language) |
| Deploy | AI configures activity |
| Teacher uses activity | Educator teaches |

### Non-negotiables

- AI does **NOT** replace the educator. The educator is the absolute decision-maker.
- System-generated observations **support** educators; they **do not diagnose** students.
- No headset required for the core concept.
- Muted/simplified sensory modes are **mandatory** (sensory-overload risk).

---

## 3. Users & Personas

| Persona | Role in system | Primary needs |
|---|---|---|
| **Special Educator** | Author, operator, observer | Describe objectives in plain language; control runtime; review observations; low prep effort |
| **Student** | Participant in immersive scenario | Clear, predictable, adjustable-intensity environment; appropriate prompting level |
| **Department Lead / Admin** | Oversight | Group-level curriculum alignment; usage and outcome reporting |
| **Chernyx Engineering** | Platform maintainers | Scenario templates, model guardrails, hardware calibration tools |

---

## 4. The Physical Room (Infrastructure Context)

- Four projection surfaces (Front, Right, Back/Top, Left) forming one shared environment.
- Student in the center; educator inside the experience.
- Physical educator interface: directional keys (↑ ← ↓ →) for Navigate, `SPACE` = Select/Action, `ESC` = Pause.
- Spatial audio: minimum 4.1 surround installed alongside projection.
- Requires controlled ambient lighting and standardized room geometry (rigid 90° corners) for edge-blending and keystone correction.

---

## 5. Core Workflow (End-to-End)

```
01 Educator Describes   "Create a supermarket activity for Arun…"
02 AI Structures        Defines objective, task sequence, prompts
03 AI Configures        Builds 3D environment, audio, objects
04 Room Transforms      Projectors display the environment
05 Student Practices    Student performs the designated task
06 Educator Observes    Teacher controls and intervenes if needed
07 Next Activity        System helps prepare the next session
```

### Continuous improvement loop

`CREATE → PRACTICE → OBSERVE & REVIEW → ADAPT`

---

## 6. Functional Requirements

### 6.1 Authoring Interface (L1 – Educator Platform)

**FR-A1** Natural-language objective input. Example:

```
Create a shopping activity for Arun.
Objective:
- Identify products.
- Read prices.
- Stay within ₹500.
- Practice asking for help.
- Complete purchase independently.
Difficulty: Intermediate
```

**FR-A2** On "Generate Environment", the system produces and displays five structured artifacts for educator review/edit before launch:

1. **Learning Objective** (normalized)
2. **Task Sequence** (ordered steps)
3. **Environment Map** (layout, objects, characters)
4. **Interaction Rules** (what triggers what)
5. **Success Criteria** (measurable)

**FR-A3** Educator can edit any generated artifact before launch (human-in-the-loop).

**FR-A4** Dynamic decision points configurable in natural language, e.g. for Shopping:

| Edge case | Prompt to educator |
|---|---|
| Budget Exceeded | What happens if the student's chosen product exceeds the budget? |
| Item Location | What happens if the student cannot find an item? |
| Social Interruption | What happens if the shopkeeper asks a question? |

**FR-A5** Student profile binding — select a student and auto-suggest adaptations (see §7).

**FR-A6** Curriculum tagging — link each activity to a curriculum group, domain, and sub-domain (see §9).

**FR-A7** Save, duplicate, version, and re-use scenarios.

### 6.2 Runtime Control (L1 – Scenario Controls)

**FR-R1** Live scenario variables adjustable mid-session:

- Difficulty
- Prompting Level
- Time Limit
- Number of Items
- Budget Limit
- Environment Complexity

**FR-R2** Pause / Resume / Reset / End session.

**FR-R3** Manual intervention: educator can trigger a prompt, skip a step, or hide a distractor.

**FR-R4** Sensory controls: mute audio, reduce motion, simplify visuals (mandatory "calm mode").

### 6.3 AI Orchestration (L2)

**FR-O1** Intent understanding — parse NL input into structured objective + constraints.
**FR-O2** Activity planning — decompose a scenario into a chain of skills/steps.
**FR-O3** Scenario generation — populate a **pre-defined structural template** (not free-form 3D generation) with objects, prices, characters, prompts, and rules.
**FR-O4** Guardrails — output strictly sandboxed; reject inappropriate or off-objective artifacts; whitelist of object/character/dialogue types.
**FR-O5** Adaptation engine — map student profile → environment and prompting parameters.
**FR-O6** Next-session suggestion — use logged observations to propose adjusted parameters (suggestion only, never auto-applied).

### 6.4 Experience Engine (L3)

**FR-E1** Scene graph with objects, characters, and interaction zones.
**FR-E2** Student navigation and selection via educator-held controls (Phase 2–3) and later gesture recognition (Phase 4+).
**FR-E3** Scripted NPC dialogue (shopkeeper) with branching driven by decision points.
**FR-E4** Spatial audio cues tied to objects/locations.
**FR-E5** Spatial looping for large scenarios where physical walking space is limited.

### 6.5 Immersive Rendering (L4)

**FR-I1** Four-output projection with projection mapping.
**FR-I2** Calibration tool: edge-blending, keystone, colour matching.
**FR-I3** Single-screen / digital simulation fallback (Phase 3) that runs the same scenario on one display.

### 6.6 Observation & Reporting

**FR-B1** Log per session: **Task completion, Prompts required, Decisions made, Errors, Time.**
**FR-B2** Per-step timeline view for the educator after each session.
**FR-B3** Trend view across sessions for a student on the same scenario.
**FR-B4** Qualitative educator notes field per session.
**FR-B5** Observation language must be descriptive, never diagnostic.

---

## 7. Adaptability Model

Same lesson, different pathway. One environment, multiple learning pathways.

| Student profile | Adaptations |
|---|---|
| **A — Requires high visual support** | Simplified environment · Fewer background products · Frequent system prompts · Visual wayfinding lines |
| **B — Requires moderate prompting** | Standard product density · Strict budget constraint · Reduced visual prompts · Audio assistance only |
| **C — Ready for independent challenge** | Complex store layout · Unexpected social situations · Zero automated prompts · Strict time limit |

### Adaptation parameters (data model)

```yaml
adaptation:
  environment_complexity: low | medium | high
  distractor_density: 0..1
  prompt_frequency: none | low | medium | high
  prompt_modality: [visual, audio, text]
  wayfinding_lines: bool
  budget_strictness: lenient | strict
  time_limit_seconds: int | null
  social_interruptions: none | scripted | unexpected
  sensory_mode: standard | reduced | calm
```

---

## 8. Reference Scenario: Shopping (Phase 2 MVP)

Shopping is not one skill — it is a **chain of skills**.

| Step | Skill exercised |
|---|---|
| Enter store | Spatial orientation |
| Read list | Task memory |
| Find product | Visual scanning |
| Compare price | Number recognition |
| Make decision | Executive function |
| Calculate | Basic math |
| Pay | Motor / process sequencing |
| Communicate | Social interaction |
| Leave | Task completion |

### Example configuration

```yaml
scenario: shopping
mission: "Buy milk, bread and apples. You have ₹500."
budget: 500
products:
  - { name: Milk,   price: 62 }
  - { name: Bread,  price: 45 }
  - { name: Apples, price: 120 }
target_total: 227
decision_points:
  budget_exceeded:    "<educator-defined response>"
  item_not_found:     "<educator-defined response>"
  social_interruption:"<educator-defined response>"
```

### Scenario template schema (generalizable)

```yaml
ScenarioTemplate:
  id: string
  category: daily_life | community | social | vocational | safety
  layout_variants: [simple, standard, complex]
  object_slots: [{ slot_id, allowed_types, default }]
  npc_slots:    [{ slot_id, role, dialogue_tree_id }]
  step_schema:  [{ step_id, skill_tag, success_condition, failure_modes }]
  decision_points: [{ id, trigger, educator_prompt, default_branch }]
  adaptation_hooks: [param_name]
```

---

## 9. Curriculum Alignment (DACAL Term 1 SPED Curriculum)

The app must tag scenarios and students against DACAL's real curriculum structure so activities map to what educators already teach.

### 9.1 Student groups (24 levels)

| # | Group | # | Group |
|---|---|---|---|
| 1 | Early Intervention – Level 1 | 13 | Primary 1 – Group 1 |
| 2 | Early Intervention – Level 2 | 14 | Primary 1 – Group 2 |
| 3 | Transition 1 – Level 1 | 15 | Primary 1 – Group 3 |
| 4 | Transition 1 – Level 2 | 16 | Primary 2 |
| 5 | Transition 2 – Level 1 | 17 | Primary 3 |
| 6 | Transition 2 – Level 2 | 18 | Trainable Group 1 |
| 7 | Transition 2 – Level 3 | 19 | Trainable Group 2 |
| 8 | Pre-Primary 1 | 20 | Educable Group |
| 9 | Pre-Primary 2 – Level 1 | 21 | Pre-OBE 1 |
| 10 | Pre-Primary 2 – Level 2 | 22 | Pre-OBE 2 |
| 11 | Pre-Primary 2 – Level 3 | 23 | Remedial – Level 1 |
| 12 | *(not present in source)* | 24 | Remedial – Level 2 |

### 9.2 Domain taxonomy

**Functional Academics**
- Tamil · English · Maths · EVS · GK · Computer Skills · Comprehension · Literacy/Numeracy (EI levels) · **MVB** (MyViewBoard / ViewSonic smart-board activities)

**Life Skills**
- ADL (Activities of Daily Living) · Motor Skills · Communication Skills · Social Skills · Multiple Intelligence · Library · Creative Arts · Culinary Skills · Art & Craft · Weaving · Movement Therapy · Islamic Studies / Value Education

### 9.3 Curriculum items that map directly to immersive scenarios

| Curriculum item (group) | Scenario candidate |
|---|---|
| Money concept (Primary 1 G2/G3), addition/subtraction up to 10 (Pre-OBE), numbers up to 50/100 | **Shopping** — reading prices, budget |
| Modes of transportation (Primary 1) | **Bus Station / Railway Platform** |
| Greeting politely: Hi, Hello, Sorry, Thank You, Bye (Pre-Primary 2, Primary, Remedial) | **Conversation Basics / Shopkeeper interaction** |
| Express needs / seek permission using words or gestures (Primary 1) | **Asking for Help** |
| Waiting for a turn (Pre-Primary 1, Educable, Pre-OBE) | **Waiting in Line** |
| Identifying common food items: rice, fruits, vegetables, snacks (Primary 1) | **Shopping — product identification** |
| Edible/non-edible, separating food from waste (Pre-OBE, Pre-Primary 2) | **Cooking / Kitchen** |
| Seeking help from a neighbouring class (Primary 3) | **Seeking Assistance** |
| Good Touch and Bad Touch (Primary 3, Pre-OBE) | **Safety** (content requires educator-led design) |
| Left/right directions, applying directions in daily activities (Remedial) | **Wayfinding / Getting Lost Simulation** |
| Personal space, moving safely around people/objects (Pre-Primary 2) | **Community navigation** |
| Communication: Yes/No responses, 2–3 word phrases, requesting water/washroom | **Any NPC interaction with prompting-level control** |
| Culinary: peeling, spreading jam, no-cook snacks | **Kitchen scenario (Phase 5)** |

### 9.4 Curriculum data model

```yaml
CurriculumGroup:
  id, name, order
CurriculumDomain:
  id, name, category: functional_academics | life_skills
CurriculumItem:
  id, group_id, domain_id, term: 1, description
Scenario:
  curriculum_item_ids: [..]        # many-to-many
Student:
  group_id, profile (see §7), active_curriculum_item_ids
```

Seed data: parse `SPED-Term 1 Curriculum.docx` into `CurriculumGroup / Domain / Item` rows (structure is consistent: Group → Domain → Term 1 description).

---

## 10. System Architecture (5 Layers)

```
┌─────────────────────────────────────────────────────────────┐
│ L1  EDUCATOR PLATFORM                                        │
│     Natural language · Activity authoring · Scenario controls│
├─────────────────────────────────────────────────────────────┤
│ L2  AI ORCHESTRATION                                         │
│     Intent understanding · Activity planning · Scenario gen  │
├─────────────────────────────────────────────────────────────┤
│ L3  EXPERIENCE ENGINE                                        │
│     3D scenes · Objects & characters · Interactions          │
├─────────────────────────────────────────────────────────────┤
│ L4  IMMERSIVE RENDERING                                      │
│     4-projector output · Projection mapping · Calibration    │
├─────────────────────────────────────────────────────────────┤
│ L5  CLASSROOM                                                │
│     Student · Educator · Physical environment                │
└─────────────────────────────────────────────────────────────┘
```

### Suggested technical stack (to be validated)

| Layer | Candidate |
|---|---|
| L1 Educator web app | React/Next.js or Flutter (tablet-first); works offline-tolerant |
| L1 Runtime controller | Same app in "session mode" on tablet + physical keypad/USB controller |
| L2 Orchestration service | Python (FastAPI) · LLM with structured-output (JSON schema) · template library · guardrail validators |
| L3 Experience engine | Unity or Unreal (multi-display), or Three.js/WebGL for Phase 3 single-screen |
| L4 Rendering | Engine multi-camera output → 4 projectors; calibration via warping/blending middleware |
| Data | PostgreSQL (students, scenarios, sessions, curriculum) · object store for scene assets |
| Realtime | WebSocket between controller app ↔ engine for live variable changes |
| Auth | Role-based (educator / admin); student data treated as sensitive |

### Key architectural decisions

1. **Templates over generation.** Real-time generation of realistic 3D scenes is computationally bound; AI fills pre-defined structural templates.
2. **Structured LLM output.** L2 emits strictly schema-validated JSON (objective, steps, env map, rules, criteria). No free text reaches the engine.
3. **Engine-agnostic scenario spec.** The scenario JSON is the contract; Phase 3 (single screen) and Phase 4 (four-wall) consume the same spec.
4. **Local-first runtime.** Session must run without cloud dependency once a scenario is generated (classroom connectivity).

---

## 11. Data Model (Core Entities)

```
Educator      (id, name, role)
Student       (id, display_name, group_id, profile_json, sensory_flags)
ScenarioTemplate (id, category, schema_json, version)
Scenario      (id, template_id, author_id, nl_input, objective, task_sequence_json,
               environment_map_json, interaction_rules_json, success_criteria_json,
               decision_points_json, curriculum_item_ids[], version)
Session       (id, scenario_id, student_id, educator_id, adaptation_json,
               started_at, ended_at, status)
SessionEvent  (id, session_id, ts, step_id, type: step_start|step_complete|prompt|
               decision|error|intervention|variable_change, payload_json)
SessionSummary(session_id, task_completion, prompts_required, decisions_made,
               errors, duration_s, educator_notes)
CurriculumGroup / CurriculumDomain / CurriculumItem (see §9.4)
```

---

## 12. Market Positioning

| Capability | VR Learning | Standard Projection | AI Lesson Gen | **Proposed Platform** |
|---|---|---|---|---|
| Immersive environments | ✓ | ✓ | – | ✓ |
| No headset required | – | ✓ | ✓ | ✓ |
| Real-world scenario focus | partial | – | – | ✓ |
| Educator authoring control | – | – | partial | ✓ |
| Natural-language creation | – | – | ✓ | ✓ |
| Real-time personalization | – | – | – | ✓ |

---

## 13. Extensibility — Scenario Roadmap

| Category | Scenarios |
|---|---|
| **Daily Life** | Shopping · Money Management · Cooking / Kitchen · Home Organization |
| **Community** | Bus Station · Railway Platform · Hospital / Clinic · Restaurant Dining |
| **Social** | Conversation Basics · Waiting in Line · Asking for Help · Conflict Resolution |
| **Vocational** | Office Workplace · Job Interview · Routine Task Training · Customer Interaction |
| **Safety** | Road Crossing · Emergency Response · Getting Lost Simulation · Seeking Assistance |

---

## 14. Deployment Phases

| Phase | Name | Deliverable | Exit criteria |
|---|---|---|---|
| **1** | Educator Discovery | Interviews with DACAL educators; curriculum mapping (§9); authoring UX prototypes | Validated objective-input format and must-have runtime controls |
| **2** | One Scenario: Shopping | Shopping template + L2 orchestration + authoring UI producing the 5 artifacts | Educator can author & edit a shopping activity in < 10 min |
| **3** | Digital Immersive Simulation | Single-screen runtime (L3 on one display) + runtime controls + session logging | Full CREATE → PRACTICE → OBSERVE loop on one screen |
| **4** | Four-Wall Pilot | Projection-mapped room, calibration tool, spatial audio, physical interface | Pilot with small educator cohort; metrics in §15 collected |
| **5** | Additional Scenarios | Template library expansion per §13; adaptation engine refinement | ≥ 3 additional scenarios authored by educators without developer involvement |

---

## 15. Pilot Measurement Criteria (Phase 4)

**Setup:** 1 physical classroom · 1 immersive scenario (Shopping) · small educator cohort · defined learning objectives.

**Metrics:**
- Educator usability
- Preparation effort
- Student engagement
- Task completion
- Prompt dependency
- Repeatability
- Qualitative educator feedback

---

## 16. Technical Assumptions & Constraints (Appendix A1)

- **Latency limits:** Real-time generation of highly realistic 3D scenes is computationally bound → pre-defined structural templates.
- **Hardware calibration:** Edge-blending and keystone correction require standardized room geometry (rigid 90° corners).
- **Lighting:** Controlled ambient lighting required for projection visibility.
- **Audio fidelity:** Spatial audio requires minimum 4.1 surround.
- **Model guardrails:** AI output generation must be strictly sandboxed to prevent inappropriate or off-objective environmental artifacts.

---

## 17. Risks & Limitations (Appendix A2)

### Pedagogical risks

| Risk | Mitigation |
|---|---|
| **Over-stimulation** — immersive environments may trigger sensory overload | Muted/simplified modes are mandatory; per-student sensory flags; instant ESC/pause |
| **False transfer** — simulated success ≠ real-world success | Observation language stays descriptive; app frames results as practice data, not mastery |
| **Automation bias** — educators over-rely on AI parameters | All AI outputs are suggestions requiring confirmation; edit-before-launch is default |

### Technical limitations

| Limitation | Approach |
|---|---|
| **Physical interaction** — students cannot pick up virtual objects | Abstraction via educator controller (Phase 2–4), gesture recognition later |
| **Space constraints** — large scenarios exceed walkable space | Spatial looping / teleport-style transitions |
| **Cost scaling** — hardware per room is capital-intensive | Software scales; Phase 3 single-screen mode runs on existing MVB/ViewSonic boards already in DACAL classrooms |

---

## 18. Privacy, Safety & Compliance

- Student records are sensitive (minors, disability context): encrypt at rest, role-based access, minimal PII (use display names/IDs in scenario text).
- No student data sent to third-party LLMs; NL authoring inputs are stripped of identifying details or routed to a self-hosted/contracted model.
- Content guardrails: whitelist object/character/dialogue categories; block list for unsafe content; human review for Safety-category scenarios.
- Audit log of every AI suggestion and educator override.

---

## 19. Open Questions for Phase 1 Discovery

1. Which DACAL groups are the first pilot cohort (likely Primary 1 G2/G3, Pre-OBE, Remedial — where money concepts appear)?
2. Does the existing MVB / ViewSonic board serve as the Phase 3 single-screen target?
3. Preferred authoring device (tablet vs laptop) and language(s) for the educator UI (English / Tamil)?
4. Currency, product set, and shop style that are culturally familiar to students (₹ pricing, local store layout).
5. How should "Islamic Studies / Value Education" and "Good Touch / Bad Touch" content be handled — likely out of scope for AI generation, educator-authored only.
6. What prompting hierarchy do educators currently use (gesture → verbal → physical) so the system's Prompting Level maps to practice?
7. Data retention policy for session logs.

---

## 20. Partnership Model

> We don't want to build this **FOR** DACAL. We want to build it **WITH** DACAL.

| DACAL brings | Chernyx AI brings |
|---|---|
| Domain expertise | AI models |
| Educator insight | Software engineering |
| Student needs | Immersive tech |
| Learning objectives | Systems architecture |

**Outcome:** a co-designed platform — a specialized tool built precisely for the people who will use it.

---

*©2026 Chernyx AI Labs | Proprietary and Confidential*
