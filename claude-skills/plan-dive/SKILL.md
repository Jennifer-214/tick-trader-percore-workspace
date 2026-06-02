---
name: plan-dive
skill_kind: judgment
loads_dynamically: [DESIGN_SPECS/meta-disciplines/skill-knowledge-consultation-and-auto-routing.md]
associated_anti_patterns: [DOCS/RECURRING_BUG_PATTERNS.md, DESIGN_SPECS/meta-disciplines/meta-anti-pattern-index.md]
associated_decisions: [plans/<active-sprint>/decision-logs/]
associated_postmortems: [plans/<active-sprint>/postmortems/]
associated_ledgers: [DOCS/TECH_DEBT.md, DOCS/PARITY_ISSUES.md]
trigger_heuristics: ["multi-layer per-plan correctness dive / rolling-window sub-sprint audit -> suggest /plan-dive"]
description: Multi-layer per-plan correctness dive for a rolling-window sub-sprint audit. Runs ONE plan body through 6 layered lenses — mechanical/soundness (dedupe_findings + plan-body symbol-existence + tests-section + intent-match vs current decisions), design/SHAPE (composes /precoding-audit-gate), implementation-detail (/blindspot-scan), anti-pattern (/bug-check), findings-ingestion (plan vs its slice of the canonical deduped findings index), and seam (rolling-window inbound/outbound forward-promise + cross-ship-invariant verification) — then synthesizes ONE RED/YELLOW/GREEN verdict + a per-finding punch-list. COMPOSES existing audit skills (never re-implements them — canonical-sister discipline). Honors consult-before-coding — returns synthesis for operator triage; never auto-proceeds. Layer-1 orchestrator; one invocation per plan, fired sequentially across a sub-sprint per the rolling-window cadence.
---

# /plan-dive — multi-layer rolling-window dive for ONE plan

> **Stage 0 — consult institutional knowledge** (per `skill-knowledge-consultation-and-auto-routing.md`): before judging, load this skill's `associated_*` slice (specs / anti-patterns / decisions / postmortems / ledgers) + run the canonical-sister check; if running as a cold Explore/Plan subagent, ensure CLAUDE.md/MEMORY are loaded first.

## What this does + why

A sub-sprint audit gate (e.g. `.E.0`) verifies each plan body before any coding. A **single audit pass misses things** — the deep-sweep that found the 141 `.E` findings was multi-lens (9 sections × 5 audit skills), and the seam-scan caught a slow→hot clobber **no per-surface scan could see**. So a plan dive is **layered**: one plan, run through N distinct lenses, each catching a different bug class. Defense-in-depth, not gold-plating.

`/plan-dive` is the reproducible instantiation of that — the per-plan **rolling-window dive**: it audits plan N together with its **inbound seam** (did the predecessor deliver what N assumes?) and **outbound seam** (does N satisfy what successors assume?), so a decision in one plan can't silently break the next.

**The 6 layers** (each contributes to the final verdict):

| # | Layer | Mechanism | Catches |
|---|---|---|---|
| 1 | **Mechanical / soundness** | `tools/dedupe_findings.py` (clean slice) + `tools/check_plan_body_symbol_existence.py` + `tools/check_plan_body_tests_section.py` + intent-match grep vs current decisions | fabricated/missing symbols, stale anchors, missing Tests-changed section, plan predates current decisions |
| 2 | **Design / SHAPE** | **composes `/precoding-audit-gate`** (`parity,trace,dod,readiness,merge`) | train-serve drift, cross-symbol impact, missed DOD patterns, plan-completeness gaps, missed reuse |
| 3 | **Implementation-detail** | **composes `/blindspot-scan`** (12-pillar) | struct-gen / type-unification / wire-order / deletion-ordering / unconditionalization blind spots (M4) |
| 4 | **Anti-pattern** | **composes `/bug-check`** (Class 1-36) | reintroduction of any catalogued anti-pattern; class the plan *claims* to close but reintroduces |
| 5 | **Findings-ingestion** | plan vs its `fix_ship` slice of `CANONICAL-FINDINGS.md` | routed finding with NO fix-design in the plan; missing `findings_sidecar:` frontmatter + D-52 cite |
| 6 | **Seam (rolling-window)** | dependency-graph forward-promises + cross-ship invariants, inbound + outbound | predecessor didn't deliver an assumed substrate; this plan's forward-promise isn't picked up by a successor |

Layers 2-4 are existing skills (composed, not duplicated). Layers 1, 5, 6 are dive-specific and run inline.

## When to fire

- Per-plan, inside a sub-sprint audit gate (the `.E.0`-style gate), **one invocation per plan body**.
- **Sequentially across the sub-sprint** (per `feedback_sequential_audit_for_granular_operator_triage`): dive plan N fully, operator-triage, then plan N+1 — not a parallel mass-fire that returns an overwhelming dump. The rolling window means each dive overlaps its neighbors only at the seam.
- Re-fire after a substantive plan amendment (cycle 2), per `feedback_iteration_spiral_signals_audit_meta_gap` — convergence expected; if cycle 2 still YELLOW after the same findings, surface a META-gap.

## Invocation

```
/plan-dive <plan_path> [predecessor=<auto>] [successors=<auto>] [findings_index=<auto>]
```

- `plan_path` (REQUIRED) — the plan body to dive.
- `predecessor` / `successors` — OPTIONAL; default auto-derived from the plan's `predecessor:`/`successor:` frontmatter + the sub-sprint dependency graph (the `dependency_graph:` frontmatter field). Used for the seam layer.
- `findings_index` — OPTIONAL; default `<sprint>/plan_checks/E.0-audit-reports/pre-implementation-findings/CANONICAL-FINDINGS.md` (the deduped canonical index). The plan's `fix_ship` slice is the findings-ingestion input.

NO hardcoded sprint/version refs — all resolved from the plan's frontmatter + the active sprint (per `/precoding-audit-gate` convention).

## Execution model — Layer-1 orchestrator

ONE-WAY HIERARCHY. `/plan-dive` runs Layers 1/5/6 inline (Bash + Read), and composes Layers 2-4 by reference.

```
LAYER 1: ORCHESTRATION
  - Main session invokes /plan-dive <plan>
  - Resolves plan + predecessor/successors + findings slice
  - Runs mechanical tools (Layer 1), findings-ingestion (Layer 5), seam (Layer 6) inline
LAYER 2: COMPOSED SKILLS
  - /precoding-audit-gate <plan> parity,trace,dod,readiness,merge,blindspot   (Layers 2+3; spawns its own Layer-3 subagents)
  - /bug-check (Layer 4)
LAYER 3: (precoding-audit-gate's own) parallel audit subagents
```

If reading this inside an Explore subagent: return error. `/plan-dive` is main-session only (it mutates the per-plan synthesis + reports to operator).

## Stages

### Stage 0 — Resolve + clean findings slice
Read the plan body + frontmatter (`predecessor`/`successor`/`dependency_graph`/`fix_ship`/`findings_sidecar`). Regenerate the clean canonical findings (so the slice is current):
```bash
python3 tools/dedupe_findings.py \
    --merge-map  <findings-dir>/findings-merge-map.txt \
    --emit-index <findings-dir>/CANONICAL-FINDINGS.md
```
Extract this plan's slice = canonical entries whose `fix_ship` matches the plan's ship tag (plus any `standalone(pre-.E.1)` flagged as prerequisites).

### Stage 1 — Mechanical / soundness (deterministic; explicit tool calls per M7)
```bash
python3 tools/check_plan_body_symbol_existence.py <plan_path>     # Class 14 — fabricated/missing symbols (note: <F> template snippets may false-positive; verify)
python3 tools/check_plan_body_tests_section.py --plan-body <plan_path>   # Check 45 — Tests-changed section if it touches tests/
```
Then intent-match: grep the plan's `predecessor:` + cited decision range against the current decision log + Version.hpp — flag stale anchors (wrong predecessor SHA/tag, `D-1..D-NN` lower than the log's current max, missing `findings_sidecar:`/safeguard-phases if the plan predates current decisions).

### Stage 2+3 — Design + implementation-detail (compose /precoding-audit-gate)
```
/precoding-audit-gate <plan_path> parity,trace,dod,readiness,merge,blindspot
```
Honor its auto-fire rules (deletion-class → blindspot, etc.). Collect its GREEN/YELLOW/RED + findings.

### Stage 4 — Anti-pattern (compose /bug-check)
Fire `/bug-check` scoped to the plan's surface + its code samples. Flag any class the plan **claims to close** but reintroduces (the `conc-5` shape — claimed closed, design relocates it).

### Stage 5 — Findings-ingestion
For each finding in the plan's canonical slice: does the plan body contain a concrete **per-finding fix-design**? Is `findings_sidecar:` wired into frontmatter + cited in the D-52 section? Missing fix-design for a HIGH/CRITICAL finding = RED contribution. Also surface this plan's **standalone(pre-X) prerequisites** (findings that must be fixed BEFORE this plan codes).

### Stage 6 — Seam (rolling-window)
- **Inbound:** for each substrate the plan assumes from its predecessor(s), grep the predecessor plan's "forward promises" / deliverables — confirm it's actually promised. A missing inbound promise = the predecessor must be amended (or this plan's assumption is wrong).
- **Outbound:** for each forward-promise this plan makes, grep the successor plan(s) for a matching "substrate landed at…" / assumption — confirm it's picked up. An orphan forward-promise = surface for reconciliation.

### Stage 7 — Synthesize + return
Write per-plan synthesis to `<sprint>/plan_checks/<gate>-audit-reports/<plan-name>-dive-synthesis.md` (per-layer verdict + classified findings + punch-list). Update the plan's rows in the guard-coverage matrix. Print ONE verdict + the punch-list. **Do not auto-proceed** — return for operator triage (`feedback_consult_on_audit_findings`).

## Verdict semantics

- **GREEN** — all 6 layers clear; every routed finding has a fix-design; both seams hold. Ready to code this plan.
- **YELLOW** — only LOW/MED findings or operator-accepted items; seams hold. Codeable with documented amendments.
- **RED** — any of: a HIGH/CRITICAL soundness gap (fabricated symbol, undesigned primitive, claimed-closed-but-reintroduced class), a routed CRITICAL/HIGH finding with no fix-design, a broken seam (assumed substrate not promised), or the plan predates load-bearing current decisions. **Amendment before coding** — not a coding ship.

## Rolling-window seam — carried by the handoff

The seam (Stage 6) is what the inter-dive handoff carries (per decision D-72 + `/handoff` Stage 2.8 / `/accept-handoff` Stage 4.5): dive N's **outbound seam** = dive N+1's **inbound seam** to re-verify on pickup. So `/plan-dive` and the seam-structured handoff template are two halves of the same rolling-window discipline.

## Distinct from sister skills

- **`/precoding-audit-gate`** — `/plan-dive` COMPOSES it (Layers 2+3). The gate is general pre-coding audit; `/plan-dive` adds the dive-specific layers (mechanical tools, findings-ingestion against the canonical index, the rolling-window seam) and the per-plan-in-a-trajectory framing. Use the gate alone for a one-off plan; use `/plan-dive` for a plan inside a sub-sprint trajectory with a findings backlog.
- **`/accept-handoff`** — receiver-side handoff verification; `/plan-dive` is the per-plan audit it feeds into.
- **`/blindspot-scan` / `/bug-check` / `/parity-check` / …** — individual lenses; `/plan-dive` orchestrates the relevant set.

## Reproducibility (M7 — deterministic skill-tool integration)

The mechanical layer invokes its tools EXPLICITLY (`python3 tools/dedupe_findings.py`, `tools/check_plan_body_symbol_existence.py`, `tools/check_plan_body_tests_section.py`) — never LLM-discovered. Re-running `/plan-dive` on the same plan + same findings index is deterministic for Layers 1/5/6; Layers 2-4 inherit `/precoding-audit-gate`'s convergence discipline.

## Sister disciplines

- `feedback_sequential_audit_for_granular_operator_triage` — sequential per-plan firing
- `feedback_iteration_spiral_signals_audit_meta_gap` — cycle-2 convergence; META-gap if it spirals
- `feedback_audit_canonical_sister_before_new_infra` — why this composes, not re-implements
- `E-guard-coverage-matrix.md` — the matrix this dive fills per plan
- decision D-72 (rolling-window seam cadence) + D-60 (audit-driven sub-sprint trajectory verification)
