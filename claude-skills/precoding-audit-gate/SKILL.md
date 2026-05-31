---
name: precoding-audit-gate
description: Layer-1 orchestrator for pre-coding audit gate. Fires multiple audit skills (parity-check + trace-deps + readiness + merge-scan + dod-audit) in parallel via general-purpose subagents against a target plan. Synthesizes convergent findings into one report. Returns GREEN/YELLOW/RED verdict + per-finding triage list. Dynamic parameterization — takes plan_path + audit_set + focus_keywords; auto-derives focus from plan content (predecessor/successor metadata + pattern matches in body). NO hardcoded TECH_DEBT references; NO hardcoded sprint refs. Honors consult-before-coding — returns synthesis for operator review; never auto-proceeds.
type: skill
concern: pre-coding-gate
audit_cadence: per-ship
tags: [audit-methodology, framework-discipline, operator-collaboration]
surface: [registry, cfg-flow, wire-format, hot-path, slow-path]
sister_skills: [/readiness, /parity-check, /trace-deps, /merge-scan, /dod-audit, /blindspot-scan, /accounting-audit, /hft-audit, /registry-fit-audit]
loads_dynamically: [DESIGN_SPECS/audit-methodologies/audit-scope-taxonomy.md, DESIGN_SPECS/meta-disciplines/implementation-layer-blindspot-taxonomy.md, DOCS/DESIGN_PHILOSOPHY.md]
---

# /precoding-audit-gate — Layer 1 orchestrator for parallel audit fire

## What this does

Spawns N audit skills in parallel as Layer 2 general-purpose subagents,
each running its own SKILL.md contract against a target plan. Collects
all findings, synthesizes convergent + divergent observations, writes
per-audit reports + one synthesis doc to `plans/plan_checks/`, and
returns a structured GREEN/YELLOW/RED verdict to the operator.

**This skill DOES execute audits via subagent dispatch.** It does NOT
modify code. It does NOT auto-proceed past audit findings — operator
review of synthesis is the load-bearing decision point per
`feedback_consult_on_audit_findings` memory rule.

## Audit posture: HEAVIER by default (D-77 / `.E.0.2` Piece 4)

This gate defaults to the HEAVIER pass. The LIGHT pass is an EARNED exception, not the lazy default (refines `feedback_tiered_audit_discipline_per_plan_scope`). Empirical mandate: the majority of the existing codebase was light-pass-audited + the `.E.0` read-only audit surfaced 141 findings → light passes leak correctness errors at a material rate, and this engine runs real money (`feedback_heavier_default_audit_posture_for_capital`).

**Decision rule — audit weight ∝ inverse deterministic coverage.** Decide heavy-vs-light by the touched surface's *deterministic* guard coverage (read it off the guard-coverage-matrix, `plans/<sprint>/E-guard-coverage-matrix.md`):
- Surface is a guard-matrix **HOLE** (convention-only) → **HEAVY**: the LLM pass is the only guard there → full `audit_set` + Stage 3.5 quorum + verification pass.
- Surface already has a Tier-1/2 **deterministic guard** (CI gate / `static_assert` / golden-master / determinism+replay) → **LIGHT** is earned: that guard is the real floor; the LLM pass is a sanity layer.

**The gate consumes the meta corpus as checks.** It reads `DESIGN_SPECS/meta-disciplines/meta-anti-pattern-index.md` (the META anti-pattern catalog) + the memory corpus (Classes 1-36 + M1-M7 + B14-B19 + `feedback_*`): mechanical rows (CP/WH) run in the deterministic pre-gate (Stage 2.5); reflection rows (AR-*) seed the verification pass (Stage 3.5). As the `/close-session` harvest grows the catalog, this gate auto-gains coverage — the memory→catalog→gate→harvest loop.

**Calibration provenance (D-78):** this hardening is tuned against REAL ships — backward (mined `.D.1`/`.B.8` postmortems for missed-then-caught) + forward (`.E.0.1` as the live bench) — NOT designed against imagined gaps.

## When to fire

Per CLAUDE.local.md going-forward rule "Suggest mid-sprint audits when
work impacts downstream" + DESIGN_PHILOSOPHY § 11 (Process discipline —
audit-driven pre-coding gate):

- HIGH-RISK ship before coding starts (structural-fix ships / wire-format-affecting ships / ships with wide cross-cutting blast radius)
- First application of a new pattern (e.g., first STAMP_BOUND derived
  filter ship; first 3-barrier structural fix application)
- Cross-cutting changes (touches ≥4 files; touches multiple subsystems)
- Picking up work from a compaction-degraded handoff (per
  `feedback_compaction_degrades_treat_handoffs_as_hints`)
- Sprint pivots (operator priority shift; new pattern emerges from prior ship)
- **Substantive plan amendment mid-cycle** (architectural decision shift /
  scope reframing / categorization change / framework-pattern application
  question) — re-fire against amended scope BEFORE coding starts. Sister to
  feedback_iteration_spiral_signals_audit_meta_gap (3+ amendment cycles =
  audit-methodology-gap signal) + feedback_operator_pushback_as_audit_signal
  (operator "are you sure?" → STOP do code analysis). Codified at v5.15.5.F.4d.1.B.4
  v1.7.6 mid-cycle after Path 1 → Path 2 → Path 2 v3 → Path 2 v4 flip-flopping
  proved planning-time audit re-fire missing as structural enforcement.

**Skip when:** routine pattern-application (new cfg field row in registry
that's already locked), pure additive work (new test entries with no
infrastructure change), one-off bug fix.

## Invocation

```
/precoding-audit-gate <plan_path> [audit_set] [focus_keywords...]
```

**Args:**

- `plan_path` (REQUIRED) — workspace path to the sub-ship plan being audited. Shape: `plans/<sprint-dir>/subplans/<plan-filename>.md`
- `audit_set` (OPTIONAL; default = `parity,trace,readiness,merge,dod`) —
  comma-separated subset of the available audits to fire. Use to skip irrelevant
  audits for narrow ships, OR EXTEND to include accounting + registry-fit + hft when
  scope warrants. **Per-audit scope shapes supported** per `audit-scope-taxonomy.md` —
  each audit in the set can carry its own scope shape:

  ```
  audit_set := <audit>[:<scope>][,<audit>[:<scope>]]...
  scope     := current | wide | module:<name> | scoped:<glob>
  ```

  Examples:
  - `parity,trace,readiness,merge,dod` — all audits default scope (current)
  - `parity:wide,trace,readiness,merge,dod:module:OMS` — parity wide-sweep + DOD scoped to OMS
  - `parity,trace,readiness,merge,dod,hft:module:OMS,accounting:module:accounting` — extended set with per-audit module scopes
  - `dod:module:wire-format,parity:current` — narrow audit gate for wire-format ship

  When scope is omitted, defaults to `current`. The per-audit-scope discipline minimizes
  context budget overflow on large plans while giving appropriate depth per concern.

  **Extended audit set:**
  - `accounting` — fires `/accounting-audit` for plans touching OMS / drainer / fee/commission /
    kill switches / fee floors / slippage / P&L / balance / backtest accounting paths. Scans
    for Class 27 (scalar cfg-mirror), per-core fee indexing, H4 violations, cross-path parity,
    static cache hazards.
  - `registry-fit` — fires `/registry-fit-audit` for plans introducing a NEW registry, OR
    touching framework selection.
  - `hft` — fires `/hft-audit` for plans touching SP/HP/drainer code. Includes branchless
    dispatch opportunity scan + cache layout discipline + Class 28 prevention.
  - `blindspot` — fires `/blindspot-scan` (IMPLEMENTATION-DETAIL layer per DESIGN_PHILOSOPHY § 11.5
    meta-discipline M4) for plans where SHAPE audits return GREEN/YELLOW after 3+ iterations, OR
    struct-gen migration crosses ≥2 registries, OR type unification migration, OR cross-registry
    consumer, OR macro hoisting into framework primitive, OR include surface change, OR wire-format
    ordering change. Walks 12-category implementation-detail blind-spot taxonomy at
    `DESIGN_SPECS/meta-disciplines/implementation-layer-blindspot-taxonomy.md`. Distinct from SHAPE audits:
    SHAPE catches design-layer issues; `/blindspot-scan` catches code-layer issues (type-change
    cascades, field-name collisions, context-dependent C++, include cycles, row-order drift).

  **Recommended audit set per ship type (default scope = current per-audit unless noted):**
  | Ship type | Recommended `audit_set` |
  |---|---|
  | Cfg field / parser / GUI / settings | `parity,trace,readiness,merge,dod` (default) |
  | OMS / drainer / fee / commission / P&L / accounting | `parity,trace,readiness,merge,dod:module:OMS,accounting:module:OMS,hft:module:OMS` |
  | NEW registry introduction OR per-instance cache | `parity,trace,readiness,merge,dod,accounting,registry-fit,hft` |
  | ML pipeline / model / inference | `parity:module:ML-pipeline,trace,readiness,merge,dod:module:ML-pipeline,accounting:module:ML-pipeline` |
  | Wire-format / stamp / drift / Layer 5b | `parity:module:wire-format,trace,readiness,merge,dod:module:wire-format,blindspot` |
  | SP/HP/drainer touching ships | Add `hft:module:<area>` to the base set per branchless discipline |
  | Struct-gen migration / type unification / cross-registry consumer | Base set + `blindspot` (IMPLEMENTATION-DETAIL layer; meta-discipline M4 per DESIGN_PHILOSOPHY § 11.5) |
  | SHAPE audits returned GREEN/YELLOW after 3+ iterations on same plan | Add `blindspot` (iteration-spiral inflection signal per `feedback_iteration_spiral_signals_audit_meta_gap`) |
- `focus_keywords` (OPTIONAL; trailing args) — extra context phrases
  injected into each subagent prompt to narrow scope. E.g., `"STAMP_BOUND
  derived filter" "Layer 5b hash lock"` to focus audits on a specific
  surface within the plan.

**Examples (generic invocation shapes):**

```
# Full pre-coding audit gate (default 5-audit set) for any plan:
/precoding-audit-gate plans/<sprint-dir>/subplans/<plan-filename>.md

# Focused audit on wire-format work only (subset; with focus keyword):
/precoding-audit-gate plans/<sprint-dir>/subplans/<plan-filename>.md parity,dod "<focus phrase>"

# Skip merge-scan (mostly mechanical row-additions — no reuse to find):
/precoding-audit-gate plans/<sprint-dir>/subplans/<plan-filename>.md parity,trace,readiness,dod

# Extended audit set with per-audit module scope:
/precoding-audit-gate plans/<sprint-dir>/subplans/<plan-filename>.md parity,trace,readiness,merge,dod:module:<area>,accounting:module:<area>
```

For canonical real-world invocations on shipped plans, see `plans/<sprint-dir>/plan_checks/*-synthesis.md` files — each synthesis doc names the `audit_set` it was generated from.

**Exit codes / verdict:**

- `GREEN` — all audits pass; proceed to coding
- `YELLOW` — minor findings to amend before coding (~≤30 min plan edit)
- `RED` — substantial findings; plan needs major amendment OR re-design

Operator decides the next move; skill never auto-proceeds.

## Execution model — Layer 1 orchestrator

**ONE-WAY HIERARCHY. NO LAYER 3.**

```
LAYER 1: ORCHESTRATION (this skill, in main session)
  - Resolves plan_path + audit_set + focus_keywords
  - Reads plan content; derives auto-focus per audit
  - Spawns N general-purpose subagents in parallel via Agent tool
  - Waits for all to complete
  - Synthesizes findings to one report
  - Returns verdict to operator

LAYER 2: EXECUTION (subagents spawned by this skill)
  - Each subagent reads its target SKILL.md (e.g., parity-check/SKILL.md)
  - Each subagent executes that skill's workflow against the target plan
  - Each subagent writes its per-audit report to plans/plan_checks/
  - Each subagent returns a concise summary to Layer 1

LAYER 3: FORBIDDEN
  - Subagents do NOT spawn further subagents
  - If you are reading this spec inside a Layer 2 subagent: STOP. You
    are NOT the orchestrator. Run your single audit + return.
```

## Pass structure

### Stage 1 — Resolve target + derive focus

1. Validate `plan_path` exists; resolve to absolute workspace path
2. Read first 50 lines of plan to extract metadata:
   - Predecessor + Successor (sprint pipeline context)
   - Status (COLD-PICKUP-READY / DRAFT / etc.)
   - Goal + Estimated effort + Risk (audit emphasis hints)
3. Scan plan body for pattern keywords (auto-focus derivation):
   - "wire format" / "HMAC" / "stamp" / "byte preservation" → emphasize /parity-check
   - "tt::" / "type-trait" / "reinterpret_cast" / "bitmap" / "bit-pack" / "alignas" → emphasize /dod-audit
   - "registry" / "FOREACH_" / "X-macro" → emphasize /trace-deps + /merge-scan
   - "slow path" / "hot path" / "latency" → emphasize /merge-scan + /dod-audit
   - "categorical" / "applies_to" / "lives_in_struct" → emphasize /dod-audit + /readiness
   - **NEW v5.15.5.F.4d.1.B.4 v1.7.5 WIP-12 — deletion-class auto-fire:** "DELETE" / "REMOVE" / "deprecate" / "full surface deletion" / "cohort delete" keyword in plan body AND `audit_tier: HIGH-RISK` frontmatter → auto-add `blindspot` to `audit_set` (forces /blindspot-scan B14 multi-surface deletion ordering + B15 unconditionalization latent assumption pillar walk; sister to existing struct-gen migration auto-fire). Sister: `feedback_multi_surface_deletion_ordering_discipline` + `feedback_unconditionalization_latent_assumption_audit` + /readiness Check 41/42 sidecars.
4. Parse `audit_set` (default all 5); intersect with auto-derived
   recommended set; if operator narrowed, honor narrowing
5. Compose focus_keywords from explicit args + auto-derived keywords

### Stage 2 — Read source docs (DYNAMIC catalog ingestion)

For each audit subagent's prompt, the orchestrator pre-loads context
the subagent will need. Reads at invocation time (NOT cached):

| Source | Used by |
|---|---|
| `tick-trader-percore-workspace/CLAUDE.md` (slim; always-loaded) | Hard invariants reference |
| `tick-trader-percore-workspace/DOCS/DESIGN_PHILOSOPHY.md` | Family sections matched to focus_keywords |
| `tick-trader-percore-workspace/DESIGN_SPECS/README.md` | Pattern catalog index |
| `DOCS/RECURRING_BUG_PATTERNS.md` | Bug class catalog (for /bug-check correlation) |
| Engine `CLAUDE.local.md` | Sprint State Tracker + going-forward rules in force |
| Plan file | Full body |
| Engine `Version.hpp` + `git log -5` | Current ship state for staleness detection |

### Stage 2.5 — Deterministic pre-gate (mechanize-down; runs BEFORE any LLM agent) [NEW `.E.0.2`]

Per the D-70 enforcement ladder + heavier-default posture: anything mechanizable is checked DETERMINISTICALLY first, so a finding never rests on a stochastic agent noticing it. Run as ground truth before Stage 3 spawns:

1. **Python checkers** (exit-code authoritative):
   - **One-shot (preferred — D-112/.E Session-4):** `/home/caramel/code/FoxML_Trader_v2/tools/check_session_docs.sh` runs the WHOLE mechanical floor in one call (B-Plus symbol-existence + bidirectional+index memories + capture-audit-mechanical [index/sentinels/skill-linkage] + forward-promise + meta-registry). Use as the Stage-2.5 default; the granular checkers below target a single concern.
   - `python3 /home/caramel/code/FoxML_Trader_v2/tools/check_plan_body_symbol_existence.py <plan_path>` (Class 14 fabrication)
   - `python3 /home/caramel/code/FoxML_Trader_v2/tools/check_plan_body_tests_section.py <plan_path>` (Check 45 — if the coding sequence touches `tests/`)
   - `python3 /home/caramel/code/FoxML_Trader_v2/tools/check_forward_promise_audit.py --since <predecessor-tag>` (Check 11 forward-promise)
2. **Mechanical catalog rows** — apply the CP/WH rows of `meta-anti-pattern-index.md` that have mechanical detection (CP-1 cascade via `/capture-audit` Check 12; WH-1 link-resolution; WH-2 index-pointer). (Full CP-1 mechanization tracked as `tools/check_amendment_cascade.py` — until built, run the Check-12 semi-mechanical procedure.)
3. **Coverage read** — pull the touched surface's rows from the guard-coverage-matrix → decide per-lens HEAVY/LIGHT (the posture rule above) → set the effective `audit_set`.

Stage-0 findings are ground truth handed to Stage 4 synthesis; the LLM agents (Stage 3) do NOT re-derive them — they focus on judgment-layer concerns. A Stage-0 HARD failure (fabricated symbol / missing tests-section) → surface immediately; don't spend LLM agents on a plan that fails the mechanical floor.

### Stage 3 — Spawn N subagents in parallel

For each audit in resolved `audit_set`, spawn a general-purpose subagent
with this prompt template:

```
Run /<audit_skill> against plan: <plan_path>

CONTEXT:
- Engine: /home/caramel/code/FoxML_Trader_v2 (HEAD = <git_sha>)
- Workspace: /home/caramel/code/tick-trader-percore-workspace
- Skill spec: workspace/claude-skills/<audit_skill>/SKILL.md — READ FIRST
- Plan target: <plan_path>
- Sprint context: <predecessor> → <plan> → <successor>
- Focus keywords: <focus_keywords>
- DESIGN_PHILOSOPHY family preload: <matched_sections>
- Date: <YYYY-MM-DD>

The user is Caramel (she/her); reports persist for her review.

[Audit-skill-specific focus per Stage 1 auto-derivation]

OUTPUT:
Write findings report to:
  /home/caramel/code/tick-trader-percore-workspace/plans/plan_checks/<audit>-<YYYY-MM-DD>-<scope>.md
(workspace direct path — NEVER engine symlink)

RETURN SYNTHESIS (under <word_cap> words):
- Per-focus-area verdict (GREEN/YELLOW/RED)
- Top 3-5 findings with file:line refs
- Blocking gaps that must resolve before coding starts
```

**Word caps per audit (synthesis brevity):**
- `/parity-check`: 600 words
- `/trace-deps`: 600 words
- `/readiness`: 800 words (most comprehensive)
- `/merge-scan`: 600 words
- `/dod-audit`: 700 words

All subagents fire **in parallel** via single tool-use message with
multiple `Agent` calls. NOT sequential.

### Stage 3.5 — Quorum + verification (HIGH-RISK) + completeness-critic (STANDING, all tiers) [quorum/verify `.E.0.2`; completeness-critic elevated to standing D-119]

The consistency layer — the answer to "same gate, different findings on reruns." For HIGH-RISK ships:

1. **Quorum on the highest-risk dimension** (Decision D; default lean **k=2-of-3**): run the single most consequential lens (typically correctness/parity, or whichever covers the guard-matrix HOLE) as N=3 INDEPENDENT agents; a finding counts CONFIRMED only if ≥2 agree. Kills run-to-run variance on the part that matters most. (Tune k/N + dimension per ship; default 2-of-3 on correctness/parity.)
2. **Verification pass** — one agent adversarially re-checks each CRITICAL/HIGH from Stage 3: real, or plausible-but-wrong? Default-skeptical. Seeded with the catalog's AR-* reflection prompts (AR-1 "is a risk dismissed over an un-enumerated set?"; AR-2 "does a claim quantify over an unlisted set?").
3. **Completeness critic (STANDING — see below)** — one agent asks "what surface did NO audit cover?" against the guard-matrix touched-surface rows + an explicit EDGE checklist (the boundaries formal audits systematically miss because they sit outside the engine's core paths): **order-submit / quantization · logs + metrics + observability emit · GUI + display · deploy + operational (warm-restart / version-reject) · persistence + recovery · external-tooling consumers**. → surfaces false-negatives a find-only gate can't. (This is the SURFACE-COVERAGE axis of "what are we missing"; the CODE-DETAIL counterpart is `/blindspot-scan` / `implementation-layer-blindspot-taxonomy.md` — complementary, not duplicate.)

Confirmed findings (survived quorum + verification) + completeness gaps flow to Stage 4. **Steps 1-2 (quorum + verification) fire ONLY for HIGH-RISK** (expensive; coverage-gated; LIGHT/MED skip them). **Step 3 (completeness-critic) is STANDING — it runs on EVERY gate fire, regardless of tier** (D-119, 2026-05-31): it is one cheap agent, and uncovered-surface misses are tier-INDEPENDENT. Evidence — the #11 money-core gate: 7 formal audits all covered the engine money paths and ALL missed the edges; the completeness pass found 6 edge-bites, **6/6 grep-confirmed real** (B-α…B-ζ). Cost stays bounded (`.E.0.2` R6): quorum on ONE dimension; the completeness-critic is a single agent.

### Stage 4 — Synthesize convergent findings + DESIGN_SPECS cross-ref (M7 sister; codified v5.15.5.F.4d.1.B.4 v1.7.6)

After all subagents return, orchestrator performs SYNTHESIS with explicit DESIGN_SPECS cross-reference (structural enforcement of `feedback_audit_canonical_sister_before_new_infra` at synthesis-stage planning surface; M7 4th canonical structural enforcement candidate per `meta-disciplines/structural-enforcement-when-memory-insufficient.md`).

Synthesis steps:

1. **Collect audit findings** — extract per-audit verdicts + findings tables
2. **DESIGN_SPECS cross-ref grep** — for each finding category, search canonical sister patterns in `DESIGN_SPECS/`:
   - Grep `DESIGN_SPECS/framework-patterns/` for existing pattern that addresses finding
   - Grep `DESIGN_SPECS/refactor-patterns/` for existing refactor closure pattern
   - Grep `DESIGN_SPECS/meta-disciplines/` for codified meta-discipline addressing finding shape
   - Grep memory files at `~/.claude/projects/-home-caramel-code-FoxML-Trader-v2/memory/` for operator-collaboration rules
3. **Cfg field categorization 5-question mechanical verify** (for any cfg-field-touching plan; per `framework-patterns/cfg-field-categorization-discipline.md` decision tree):
   - What macro family is the field in? (FOREACH_PER_CORE / FOREACH_GLOBAL / FOREACH_*_CFG_FLAG / OVERRIDE_INT_FIELDS)
   - Does the field have a global manual struct field? (yes = load-bearing for walker propagation; no = NO_FLAT_FIELD candidate)
   - What's the walker behavior at this row? (NO_FLAT_FIELD skip vs EMIT_PER_CORE_COPY propagation)
   - What consumer reads exist + scope of each? (`cfg.X` global / `cfg.cores[c].X` per-core / `core_cfg->X` per-core resolved)
   - Does the field have per-core override syntax? (PER_CORE_OVERRIDE_INT_FIELDS macro membership)
4. **Identify existing infrastructure** — explicitly enumerate canonical sisters that address findings BEFORE proposing new infrastructure
5. **Flag NEW infrastructure proposals** with rationale — if existing infrastructure addresses, REJECT new proposal; if no canonical sister exists, surface as NEW infrastructure candidate with explicit justification
6. **Write synthesis doc** at `plans/plan_checks/<YYYY-MM-DD>-<plan-shortname>-fresh-audits-synthesis.md`

Synthesis structure (extended at v1.7.6):
1. **Per-audit verdict table** — single-row summary per audit
2. **Combined verdict** — GREEN if all GREEN; YELLOW if any YELLOW; RED if any RED
3. **DESIGN_SPECS cross-ref findings** — per-finding canonical sister citations OR NEW infrastructure justification
4. **Critical findings (CRITICAL)** — convergent across audits OR ship-blocking design errors
5. **High findings (HIGH)** — should resolve before coding; ~30 min plan edit each
6. **Medium findings (MED)** — addressed-as-found, NOT "skip because not blocking": fix in-ship when correctness-adjacent + the surface is already open, else fold-to-named-task or ledger with an ID + fix-home
7. **Low findings (LOW)** — addressed-as-found, NOT "drop as notes/future-work": ledger with an ID + fix-home at minimum, or fix in-ship if cheap + adjacent

**Disposition-completeness rule (per `feedback_address_med_low_findings_not_just_high_crit`, 2026-05-30):** EVERY finding at EVERY severity carries exactly one disposition — fix-in-ship / fold-to-named-task / ledger-with-ID-and-fix-home / document. None left severity-only. Severity gates urgency + sequencing, never whether-to-address; a bare "low, skip" is the anti-pattern (silently accrues tech debt under a severity label). The synthesis is incomplete until every CRITICAL→LOW row has a disposition column filled.

**Kind-tagging rule (per `audit-methodologies/audit-finding-kind-taxonomy.md`, D-116):** every finding ALSO carries a KIND {mechanical | structural | design} + a WIDESPREAD flag, written as the shorthand `<SEV>·<kind>[·wide]` (e.g. `CRIT·design`, `HIGH·structural·wide`) in a KIND column of the findings tables (items 4-7). Severity = urgency; kind = work-type — it partitions findings into ordered work-streams (**design → structural → mechanical**), so the KIND column IS the sequencing; widespread = needs-an-enumeration-sweep. Kind feeds the proportionate-response menu (mechanical→inline / structural→fold-or-accept / design→architect-or-design-pass). The synthesis is incomplete until every finding row carries its `<SEV>·<kind>` tag + disposition.
8. **Cold-pickup completeness verdict** — would a fresh session lose >30 min re-deriving context?
9. **Recommended plan amendment list (ordered)** — concrete fixes with effort estimates + DESIGN_SPECS citations
10. **Recommendations for path forward** — full amend / partial amend / scope-reduce / proceed
11. **Anti-pattern verdict** — list of Class N anti-patterns this scope closes (Class 25/26/27/33 etc. with recurrence_count updates)
12. **M7 escalation check** — if findings reveal codified-memory-insufficient pattern (3+ recurrent violations of codified rule at same surface), flag for future Stage 6 cadence-locked promotion

**Why this Stage 4 extension exists:** Codified at v5.15.5.F.4d.1.B.4 v1.7.6 cycle 2026-05-27. v1.7.6 Path 1 framing error was caught by operator pushback AFTER plan body amendment because synthesis stage didn't cross-ref existing canonical patterns (NO_FLAT_FIELD pattern existed at `CfgFieldRegistry.hpp:682` strategy row but plan body proposed misapplication). Memory-only discipline (`feedback_audit_canonical_sister_before_new_infra`) insufficient at synthesis-stage planning surface; structural enforcement via Stage 4 procedure addresses gap.

### Stage 5 — Return verdict to operator

Print synthesis location + GREEN/YELLOW/RED + count of CRITICAL/HIGH/MED/LOW findings.

**DO NOT auto-proceed past audit findings.** Per CLAUDE.local.md
"After pre-coding audits, ALWAYS consult before coding": present
findings + list potential fixes + iterate with operator. Skill ends
here; operator decides the next move.

## Auto-write contract

Per CLAUDE.local.md:
- Audit findings → `plans/plan_checks/` (per-audit + synthesis)
- New PARITY findings → `DOCS/PARITY_ISSUES.md` audit-log entry (if /parity-check surfaces them)
- New TECH_DEBT items → `DOCS/TECH_DEBT.md` (if defer decisions emerge from synthesis)
- New bug class candidates → `DOCS/RECURRING_BUG_PATTERNS.md` (if 2+ recurrence pattern detected)

The orchestrator does NOT write these — the subagents (or operator
post-synthesis) do, per their respective auto-write contracts.

## Distinct from sister skills

| Skill | Scope | Relationship to /precoding-audit-gate |
|---|---|---|
| `/parity-check` | Train↔serve identity audit | LAYER 2 child — fired by this orchestrator |
| `/trace-deps` | Plan-vs-code function-existence + signature-drift | LAYER 2 child |
| `/readiness` | Plan completeness 28-check | LAYER 2 child |
| `/merge-scan` | Reuse-merge opportunities | LAYER 2 child |
| `/dod-audit` | DESIGN_SPECS pattern application | LAYER 2 child |
| `/plan-context-sweep` | Lighter variant — `/bug-check` + `/trace-deps` only | Sister orchestrator (lighter scope) |
| `/handoff` | Generates pickup prompt | Sister Layer 1; `/handoff` may invoke `/precoding-audit-gate` as part of pickup discipline |
| `/bug-check` | Codebase + plans/ scan against RECURRING_BUG_PATTERNS | Orthogonal — `/bug-check` is anti-pattern-detection in shipped state; `/precoding-audit-gate` is plan-validation pre-coding |

## When to skip

- Routine pattern-application (1 row in established registry) — overhead exceeds value
- Pure additive work (new tests; no infrastructure change)
- Bug-fix-only ship (no design surface)
- One-line changes
- When operator explicitly opts to skip per consult-before-coding judgment

## Examples — past audit gate fires

Past audit gate fires are documented as committed synthesis docs in `plans/<sprint-dir>/plan_checks/*-synthesis.md` — each captures the ship audited, audit set fired, severity counts, and operator triage decisions. Review committed synthesis docs for canonical examples of HIGH-RISK ship audit outcomes (CRITICAL findings caught pre-coding; structural anti-pattern reintroduction prevention; fictional symbol surfacing; etc.).

## Cost model

- Per-audit subagent: ~5-10 min wall clock
- 5 subagents in parallel: ~10 min total (longest-pole)
- Orchestrator synthesis: ~5 min
- **Total: ~15 min wall clock; ~150K tokens across all subagents combined**

vs alternative (no audit gate): ~6-8 hr debug per CRITICAL finding that escapes to production. ROI is overwhelmingly positive when ship is HIGH-RISK / first-pattern / cross-cutting.

## Anti-patterns to avoid

- ❌ Hardcoding TECH_DEBT-N or sprint-N references in this skill spec or in subagent prompts. Skill is dynamic — `plan_path` arg drives focus; subagent prompts are templated from plan content.
- ❌ Spawning Layer 3 subagents (subagents within subagents). Hard rule.
- ❌ Auto-proceeding past audit findings. Always consult operator.
- ❌ Skipping the synthesis doc. The synthesis is the load-bearing operator-review surface.
- ❌ Firing this on routine ships (cost > value).

## Cross-references

- `tick-trader-percore-workspace/DOCS/DESIGN_PHILOSOPHY.md` § 11 (Process discipline — audit-driven pre-coding gate)
- `tick-trader-percore-workspace/DESIGN_SPECS/audit-methodologies/audit-driven-pre-coding-gate.md` (the canonical pattern this skill instantiates)
- `tick-trader-percore-workspace/CLAUDE.local.md` going-forward rule "Suggest mid-sprint audits when work impacts downstream"
- Engine memory `feedback_consult_on_audit_findings` (consult before coding)
- Engine memory `feedback_compaction_degrades_treat_handoffs_as_hints` (verify on cold pickup)
- Past audit gate fires: see committed synthesis docs at `plans/<sprint-dir>/plan_checks/*-synthesis.md` (multiple ships' canonical references; the most recent multi-batch ship's synthesis is the best reference for current discipline)
