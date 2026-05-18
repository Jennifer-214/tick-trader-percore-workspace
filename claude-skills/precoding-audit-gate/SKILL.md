---
name: precoding-audit-gate
description: Layer-1 orchestrator for pre-coding audit gate. Fires multiple audit skills (parity-check + trace-deps + readiness + merge-scan + dod-audit) in parallel via general-purpose subagents against a target plan. Synthesizes convergent findings into one report. Returns GREEN/YELLOW/RED verdict + per-finding triage list. Dynamic parameterization — takes plan_path + audit_set + focus_keywords; auto-derives focus from plan content (predecessor/successor metadata + pattern matches in body). NO hardcoded TECH_DEBT references; NO hardcoded sprint refs. Honors consult-before-coding — returns synthesis for operator review; never auto-proceeds.
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
    `DESIGN_SPECS/implementation-layer-blindspot-taxonomy.md`. Distinct from SHAPE audits:
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

### Stage 4 — Synthesize convergent findings

After all subagents return, orchestrator writes a synthesis doc:

`plans/plan_checks/<YYYY-MM-DD>-<plan-shortname>-fresh-audits-synthesis.md`

Synthesis structure:
1. **Per-audit verdict table** — single-row summary per audit
2. **Combined verdict** — GREEN if all GREEN; YELLOW if any YELLOW; RED if any RED
3. **Critical findings (CRITICAL)** — convergent across audits OR ship-blocking design errors
4. **High findings (HIGH)** — should resolve before coding; ~30 min plan edit each
5. **Medium findings (MED)** — Step 0 polish during coding; not blocking
6. **Low findings (LOW)** — notes / future-work
7. **Cold-pickup completeness verdict** — would a fresh session lose >30 min re-deriving context?
8. **Recommended plan amendment list (ordered)** — concrete fixes with effort estimates
9. **Recommendations for path forward** — full amend / partial amend / scope-reduce / proceed

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
- `tick-trader-percore-workspace/DESIGN_SPECS/audit-driven-pre-coding-gate.md` (the canonical pattern this skill instantiates)
- `tick-trader-percore-workspace/CLAUDE.local.md` going-forward rule "Suggest mid-sprint audits when work impacts downstream"
- Engine memory `feedback_consult_on_audit_findings` (consult before coding)
- Engine memory `feedback_compaction_degrades_treat_handoffs_as_hints` (verify on cold pickup)
- Past audit gate fires: see committed synthesis docs at `plans/<sprint-dir>/plan_checks/*-synthesis.md` (multiple ships' canonical references; the most recent multi-batch ship's synthesis is the best reference for current discipline)
