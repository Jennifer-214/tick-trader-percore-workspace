---
type: plan-template
stage: 2-draft
version: 1.0
established: 2026-05-18
tags: [plan-template, doc-discipline, framework-discipline]
surface: []
sister_specs: [future-oriented-plan-template.md, pattern-codification-lifecycle.md, audit-driven-pre-coding-gate.md]
applies_at_skills: [/plan-draft]
---

# Sprint MASTER plan template

**Established:** 2026-05-18 (v5.15.5.F.4d.1.B.3 doc-layer refresh — codified after Caramel surfaced that plans rely on ship-name to convey purpose, which fails for cold-pickup; sister to sub-plan template at `future-oriented-plan-template.md`)
**Status:** **Stage 2 DRAFT v1.0** (first canonical application: retrofit at next MASTER plan update — likely v5.15-live-readiness/MASTER.md OR next new umbrella plan)
**Tags:** plan-template, framework-discipline, sprint-orchestration, end-goal-codification; serves CLAUDE.local.md going-forward rule "Plans + sub-plans codify explicit end goals" (2026-05-18); companion to `future-oriented-plan-template.md` (sub-plan template)

**Cross-references:**
- Sister: `future-oriented-plan-template.md` (sub-plan template; this template orchestrates the sub-plans at sprint level)
- Sister: `pattern-codification-lifecycle.md` (sprint-level pattern accumulation tracking)
- Sister: `audit-driven-pre-coding-gate.md` (per-sub-ship audit cycle within sprint)
- Memory: `feedback_plans_have_explicit_end_goal.md` (the going-forward rule)
- Memory: `feedback_claude_md_guidelines_not_stuff_to_do.md` (companion: plans must self-bound so they don't leak into always-loaded docs)
- CLAUDE.local.md going-forward rule: "Plans + sub-plans codify explicit end goals" (2026-05-18)

---

## Problem statement

Existing MASTER plans (e.g., `plans/v5.15-live-readiness/MASTER.md`) carry the sprint state implicitly — sprint goal lives in narrative paragraphs, sub-ship pipeline lives in pipeline tables, end-state verification lives in scattered notes. Cold-pickup readers (fresh-Claude, post-compaction-Claude, returning-Caramel after time away) have to reconstruct the sprint's purpose from ship names + scattered context.

This template encodes the MASTER plan structure mechanically:
- **Sprint end goal** (explicit; 1-2 sentences answering "what does this sprint deliver?")
- **Per-sub-ship end goal column** in the ship pipeline (each sub-ship's contribution to sprint goal)
- **Sprint-end verification** (what proves the sprint succeeded)

Companion to `future-oriented-plan-template.md` (sub-plan template); both required per `feedback_plans_have_explicit_end_goal.md`.

---

## The template

```markdown
# v<VERSION-PREFIX> — <SPRINT NAME> — MASTER plan

**Branch:** `<branch>` (typically a sprint-long branch; sub-ships may or may not get their own branches)
**Predecessor sprint:** `<previous-sprint-name>` (status: shipped / cancelled / split)
**Master tag prefix:** `v<VERSION-PREFIX>` (e.g., `v5.15-live-readiness` or `v5.15.5.F.4d` umbrella)
**Status:** **DRAFT v1.0 (<date>)** OR **ACTIVE — <sub-ship-in-flight>** OR **SHIPPED <date>**

---

## Sprint end goal

(REQUIRED.)

**One-line statement:** What this sprint delivers. The META-goal that ALL sub-ships serve.

Examples:
- "Make the codebase more maintainable for future development" (v5.15.5.F.4d.1.B.3 retrofit)
- "Close cfg-derived consumer drift via framework consolidation" (umbrella sprint hypothetical)
- "Migrate engine off legacy single_core LIVE; harden replay determinism" (live-readiness umbrella)

**Why this sprint exists:** 2-4 paragraph problem statement. What triggered it; what's the cost of NOT doing it; what alternative sprints were considered + rejected.

**Sprint-end verification (acceptance criteria):**
- What proves the sprint achieved its end goal?
- Specific bug classes closed (Class N N→0 verified by `/bug-check`)
- Specific TECH_DEBT entries closed (status flip in ledger)
- Specific DESIGN_SPECs Stage 3+ promoted
- Hot path verification (UNTOUCHED with calls_graph_diff GREEN OR TOUCHED with HOT_PATH_CHANGELOG entries)
- CI checks PASS at sprint-close commit
- Cross-binary build verify (5 binaries clean — engine + engine_gui + foxml_suite + controller_test + parity_harness)
- Tests GREEN baseline maintained

---

## Sub-ship pipeline

(REQUIRED.)

| Sub-ship | Ship name | End goal (1 sentence) | Status | Acceptance criteria |
|---|---|---|---|---|
| `vX.Y.Z.A` | <ship-name> | <what this ship closes / delivers> | shipped / in-flight / queued / deferred | <CLOSED bug classes / TECH_DEBT / DESIGN_SPECs / hot-path verification> |
| `vX.Y.Z.B` | <ship-name> | <what this ship closes / delivers> | ... | ... |
| ... | ... | ... | ... | ... |

**Per-sub-ship end goal contribution:** Each sub-ship's end goal must explicitly contribute to the Sprint end goal. If a sub-ship doesn't tie back, scope-check — does it belong in this sprint?

**Sub-plan paths:** Each sub-ship's full plan body lives at `subplans/<YYYY-MM-DD>-<version>-<name>.md` using `future-oriented-plan-template.md`. Sub-plans cite back to this MASTER for sprint context.

---

## Deferrals (explicit scope exclusion)

(REQUIRED.)

| Item | Defers to (future sprint / future ship / TECH_DEBT entry) | Why deferred |
|---|---|---|
| <item> | <target> | <rationale per `feedback_no_defer_for_effort`> |
| ... | ... | ... |

(Per `feedback_no_defer_for_effort` — deferrals are last-ditch, not effort-avoidance. Each deferral cites the future home it lands at.)

---

## Pattern codification tracking

(OPTIONAL — required if sprint codifies new patterns.)

**NEW DESIGN_SPECs at this sprint:**
- `<spec-name>.md` v<version> — <one-line description>

**AMENDED DESIGN_SPECs at this sprint:**
- `<spec-name>.md` v<old> → v<new> — <change summary>

**NEW Hard Invariants at this sprint (codified in CLAUDE.md H-table):**
- H<N>: <invariant>

**NEW Meta-disciplines at this sprint (codified in DESIGN_PHILOSOPHY § 11.5):**
- M<N>: <discipline>

**NEW anti-pattern classes at this sprint (codified in RECURRING_BUG_PATTERNS):**
- Class <N>: <title>

---

## Auto-write contracts triggered by this sprint

(REQUIRED if sprint involves cross-cutting work.)

| Trigger | Ledger | Entries expected |
|---|---|---|
| Sub-ship close | `DOCS/TECH_DEBT.md` | <list of TECH_DEBT-NNN entries opened/closed per sprint> |
| Parity findings | `DOCS/PARITY_ISSUES.md` | <list> |
| Feature additions | `FEATURE_LOOKUP.md` | <list> |
| Decoupling positioning | `plans/_future/2026-05-12-decoupling-endgoal-roadmap.md` | <updates> |
| Landmines surfaced | `DOCS/LANDMINES.md` | <list> |

---

## Sprint-wide invariants

(OPTIONAL — required when sprint locks structural invariants.)

| Invariant | Codified at | Verification |
|---|---|---|
| <invariant statement> | <sub-ship + date> | <CI check / test / audit> |

Examples:
- "CfgFieldDescriptor schema LOCKED — Kind enum is GUI metadata only, never drives storage" (v5.15.5.F.4d.1.B.3 sprint-wide invariant)
- "All registries enrolled in FOREACH_REGISTRY meta-registry" (H15; codified .F.4d)

---

## Cross-references

- Predecessor sprint plan: `<plans/<previous-sprint>/MASTER.md>`
- Decoupling positioning: `plans/_future/2026-05-12-decoupling-endgoal-roadmap.md` (long-horizon roadmap)
- Sub-plan template: `DESIGN_SPECS/future-oriented-plan-template.md`
- Audit-driven pre-coding gate: `DESIGN_SPECS/audit-driven-pre-coding-gate.md`
- Pattern codification lifecycle: `DESIGN_SPECS/pattern-codification-lifecycle.md`
- CLAUDE.local.md going-forward rule: "Plans + sub-plans codify explicit end goals" (2026-05-18)

---

**End of MASTER plan template v1.0.**
```

---

## How to use the template

### For NEW sprint MASTER plan creation:

1. **Copy template** to `plans/<sprint-name>/MASTER.md`
2. **Fill Sprint end goal** — 1-sentence statement of what this sprint delivers; this is the META-goal that grounds every sub-ship
3. **Enumerate sub-ship pipeline** — at least skeletal entries for foreseeable sub-ships; mark `queued` initially
4. **Define sprint-end verification** — acceptance criteria; what proves the sprint succeeded
5. **List deferrals** — what's explicitly OUT of scope; cite where deferred items will land

### For RETROFITTING existing MASTER plans:

Older MASTER plans (pre-2026-05-18) may not have explicit Sprint end goal sections. At per-sub-ship cycle update step OR sprint review boundary, retrofit:

- Add explicit Sprint end goal (1 sentence + Why-this-sprint paragraph)
- Reformat existing sub-ship pipeline to include End goal column
- Add Sprint-end verification section
- v5.15-live-readiness/MASTER.md retrofit is the FIRST canonical application (post-2026-05-18)

### For sub-master plans (umbrella ships):

Umbrella sub-masters (e.g., `v5.15.5.F.4d.1` umbrella spanning multiple sub-ships) use the abbreviated template:

- Header (Branch / Predecessor / Master tag prefix / Status)
- Umbrella end goal (1 sentence)
- Sub-ship breakdown table (End goal column required)
- Out-of-scope (deferrals)
- Cross-references back to parent MASTER

### For `/plan-draft` skill invocation:

The `/plan-draft` skill scaffolds sub-plans (per `future-oriented-plan-template.md`). For NEW MASTER plans, manual copy-paste of THIS template is the workflow (less frequent than sub-plan drafting; doesn't warrant skill scaffolding yet).

If MASTER plan creation becomes frequent enough, extend `/plan-draft` skill with a `--master` flag to scaffold MASTER template.

---

## Worked example: v5.15-live-readiness MASTER plan retrofit (hypothetical)

```markdown
# v5.15-live-readiness — MASTER plan

**Branch:** `feat/v5.15-live-readiness` (sprint-long)
**Predecessor sprint:** `v5.14-ml-hardening` (shipped 2026-05-10)
**Master tag prefix:** `v5.15.*`
**Status:** **ACTIVE — in-flight ship v5.15.5.F.4d.1.B.3** (Phase L coding-ready)

---

## Sprint end goal

**One-line statement:** Make the codebase more maintainable for future development — frame the engine for paper-test live readiness while consolidating framework discipline (auto-flowing registries, structural-fix-over-patch, audit-driven pre-coding) so future development stays mechanical rather than reactive.

**Why this sprint exists:** Post-MVP professionalization phase. Codebase had functional MVP shipped through v5.14; v5.15 sprint addresses (1) live-trade readiness gates (kill switch, recovery, OMS hardening), (2) framework consolidation (cfg-field auto-flow, derived-filter sidecar, meta-registry, X-macro discipline), (3) audit-driven pre-coding discipline (SHAPE + IMPLEMENTATION-DETAIL audit layers, meta-discipline registry M1-M4).

**Sprint-end verification:**
- All H15-H19 invariants codified + CI-enforced
- All Class 18-32 closures have CI tests or audit-skill coverage
- Phase L cross-tool decoupling complete (bash tools → C++ CLI binaries; framework single-source-of-truth)
- 5 binaries clean + all tests GREEN at sprint close
- Paper-test session demonstrates kill switch + recovery work
- HOT_PATH_CHANGELOG documents all hot-path additions

---

## Sub-ship pipeline

| Sub-ship | Ship name | End goal | Status | Acceptance criteria |
|---|---|---|---|---|
| `v5.15.0.A` | Initial readiness gate | Establish v5.15 baseline + boot-time gate | shipped | <details> |
| `v5.15.5.F.4d` | Merged framework bandit Thompson | Consolidate bandit + Thompson framework | shipped | H15-H19 codified |
| `v5.15.5.F.4d.1.B.3` | Legacy empty-out + Phase L | Close cfg-derived consumer drift; decouple cross-tool wire format from bash | in-flight | TECH_DEBT-001 + -018 + -109 + -110 closures; H20 codified; Phase L coding complete |
| `v5.15.5.F.4d.1.B.4+` | TBD | ... | queued | ... |
| ... | ... | ... | ... | ... |

---

(rest of template filled per actual sprint state)
```

---

## Trade-offs + when to apply

### Apply when:

- Drafting a new sprint MASTER plan (umbrella OR linear)
- Retrofitting existing MASTER plan during sprint review boundary
- Drafting umbrella sub-master plan (abbreviated template)

### Skip when:

- One-off hotfix ships outside of sprint structure (no MASTER plan needed)
- Documentation-only sprints (template overkill)
- Pre-MVP exploratory work (sprint structure not yet load-bearing)

### Cost:

- ~30-45 min initial MASTER draft using template vs ~10-15 min ad-hoc narrative
- ~45-60 min retrofit for existing MASTER plan (one-time cost per plan)

### Win:

- Sprint purpose codified explicitly (cold-pickup readers know what sprint delivers)
- Sub-ships tied back to sprint end goal mechanically
- Acceptance criteria visible from MASTER (not scattered across sub-plans)
- Deferrals explicit (no implicit "we'll deal with that later" leaking)
- Pattern codification tracked at sprint level (compounds over sprints → DESIGN_SPECS / Class catalog / H invariants stay accurate)

---

## Lessons / gotchas

### Sprint end goal must be ONE sentence

Multi-sentence sprint goals fragment scope. If the goal won't fit one sentence, sprint scope is too broad — split into separate sprints OR use umbrella structure with sub-sprints.

### Sub-ship end goals must tie back to sprint goal

Every sub-ship's End goal column should explicitly contribute to the Sprint end goal. If a sub-ship doesn't tie back, it's scope-creep — either re-scope the sub-ship OR add a new sprint goal (which usually means sprint scope is wrong).

### Sprint state pointers (CLAUDE.local.md) should point at MASTER

Going-forward rules + always-loaded docs (CLAUDE.local.md § Current sprint state) should be INDEX pointers to MASTER plan, not bodies of current state. MASTER plan owns sprint state; CLAUDE.local.md just points at it.

### Retrofit triggers update of in-flight sub-plans

Retrofitting a MASTER plan with explicit Sprint end goal may surface that in-flight sub-plans don't have Ship end goals — those need retrofitting too (via `future-oriented-plan-template.md`).

### Don't over-specify pipeline upfront

Queued sub-ships should have skeletal entries (ship name + end goal placeholder); detailed acceptance criteria land when sub-ship enters in-flight phase. Over-specifying queued ships locks scope prematurely.

---

## Pattern lifecycle (per `pattern-codification-lifecycle.md`)

- **Stage 1 (audit / problem identification):** Caramel surfaced 2026-05-18 "plans should have like plan end goal and stuff laid out in a master plan, and sub plan end goals right?" finding-issues concern; MASTER plans lack explicit end-goal section structurally
- **Stage 2 (DESIGN_SPEC draft):** THIS DOC (2026-05-18)
- **Stage 3 (first canonical application):** v5.15-live-readiness/MASTER.md retrofit (queued post-doc-sprint) OR next new umbrella plan
- **Stage 4 (cohort migration):** existing MASTER plans retrofitted at sprint review boundary; new MASTER plans use template from day 1
- **Stage 5+ (CLAUDE.md item promotion):** when 3+ MASTER plans use template + the discipline is load-bearing for sprint orchestration

---

## Cross-references

- Sister: `future-oriented-plan-template.md` (sub-plan template; this MASTER template orchestrates the sub-plans)
- Sister: `pattern-codification-lifecycle.md` (pattern accumulation tracking at sprint scope)
- Sister: `audit-driven-pre-coding-gate.md` (per-sub-ship audit cycle within sprint)
- Memory: `feedback_plans_have_explicit_end_goal.md` (going-forward rule)
- Memory: `feedback_claude_md_guidelines_not_stuff_to_do.md` (companion: plans must self-bound so they don't leak into always-loaded docs)
- Memory: `feedback_new_plans_use_future_oriented_template.md` (sub-plan template companion)
- CLAUDE.local.md going-forward rule: "Plans + sub-plans codify explicit end goals" (2026-05-18)

---

**End of MASTER plan template v1.0 DRAFT.** Stage 3 first canonical application queued: v5.15-live-readiness/MASTER.md retrofit OR next new umbrella plan.
