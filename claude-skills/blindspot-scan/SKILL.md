---
name: blindspot-scan
description: Implementation-layer blind-spot audit. Fires AFTER /precoding-audit-gate SHAPE/SCOPE/CONSUMER audits return GREEN-or-YELLOW, BEFORE substantive coding starts. Walks the 12-category implementation-detail blind-spot taxonomy (DESIGN_SPECS/meta-disciplines/implementation-layer-blindspot-taxonomy.md) against a target plan + current code state. Produces per-category verdict (GUARDED-BY-BUILD / SILENT-RISK / IRRELEVANT / N-A) + concrete punch-list of pre-coding amendments. Honors consult-before-coding — returns synthesis for operator review; never auto-proceeds. Distinct from SHAPE audits (/parity-check / /trace-deps / /readiness / etc.) which catch design-layer concerns.
type: skill
concern: impl-detail-audit
audit_cadence: ad-hoc
tags: [audit-methodology, meta-discipline, framework-discipline]
surface: [registry, wire-format, cfg-flow]
sister_skills: [/precoding-audit-gate, /parity-check, /trace-deps, /readiness, /dod-audit]
loads_dynamically: [DESIGN_SPECS/meta-disciplines/implementation-layer-blindspot-taxonomy.md, DESIGN_SPECS/wire-format-patterns/wire-format-byte-preservation-discipline.md, DESIGN_SPECS/meta-disciplines/skill-knowledge-consultation-and-auto-routing.md, CoreFrameworks/CfgFieldRegistry.hpp, CoreFrameworks/CfgFieldDispatch.hpp]
skill_kind: judgment
associated_anti_patterns: [DOCS/RECURRING_BUG_PATTERNS.md, DESIGN_SPECS/meta-disciplines/meta-anti-pattern-index.md]
associated_decisions: [plans/<active-sprint>/decision-logs/]
associated_postmortems: [plans/<active-sprint>/postmortems/]
associated_ledgers: [DOCS/TECH_DEBT.md, DOCS/PARITY_ISSUES.md]
trigger_heuristics: ["impl-detail blind spots / type-cascade / field-collision -> suggest /blindspot-scan"]
---

# /blindspot-scan — Implementation-detail audit for pre-coding readiness

> **Stage 0 — consult institutional knowledge** (per `skill-knowledge-consultation-and-auto-routing.md`): before judging, load this skill's `associated_*` slice (specs / anti-patterns / decisions / postmortems / ledgers) + run the canonical-sister check; if running as a cold Explore/Plan subagent, ensure CLAUDE.md/MEMORY are loaded first.

## What this does

Walks the 12-category blind-spot taxonomy at `DESIGN_SPECS/meta-disciplines/implementation-layer-blindspot-taxonomy.md` against a target plan + current code state. Per category, classifies risk + produces concrete detection output:

| Pillar | Category | Detection |
|---|---|---|
| B1 | Type-change cascade | Per-field type-diff (OLD vs NEW); TYPE-SENSITIVE consumer count |
| B2 | Field-name collision | Pairwise registry intersection scan |
| B3 | Transitional state coexistence | Struct size peak estimate + budget verify |
| B4 | Surface G applicability per registry | Per-row semantic check |
| B5 | Compile-time scaling | Instantiation count estimate vs threshold |
| B6 | STORAGE_T variant coverage | tt:: branch presence per variant |
| B7 | Include topology cycle | Include-graph delta scan |
| B8 | Type-sensitive consumer classification | Per-site classification (TYPE-SENSITIVE-READ / WRITE / AGNOSTIC) |
| B9 | Unverified audit claim | Claim→file:line evidence check |
| B10 | Struct layout drift | Byte-equivalence context check (H12 applicability) |
| B11 | if-constexpr template context | Host function context check |
| B12 | Cross-registry row ordering | Master vs legacy walker order diff |

Returns synthesis: per-pillar verdict + per-pillar punch-list of pre-coding amendments needed + total pre-coding effort estimate.

**This skill READ-ONLY scans codebase + plan body.** It does NOT modify code. It does NOT auto-proceed past findings — operator review of synthesis is the load-bearing decision point per `feedback_consult_on_audit_findings`.

## When to fire

Fire AFTER `/precoding-audit-gate` returns GREEN-or-YELLOW-with-amendments and BEFORE substantive coding starts, when ANY of the following implementation-detail triggers apply:

- **Struct-gen migration:** unconditional or filtered struct-field auto-generation crosses ≥2 registries (B1+B2+B11 risk)
- **Type unification migration:** STORAGE_T column being adopted; struct field types shift across rows (B1+B6 risk)
- **Cross-registry consumer:** a single struct or function accesses fields from ≥2 registries (B2+B7+B8 risk)
- **Macro hoisting:** X-macro walker bodies extracted from call sites into framework primitive (B11+B12 risk)
- **Include surface change:** new cross-directory includes proposed (B7 risk)
- **Wire-format ordering change:** master registry order differs from legacy walker emit order (B12 risk)
- **Pre-coding audit gate ran 3+ batches with iterative findings:** signals SHAPE-level audits exhausted; IMPLEMENTATION-DETAIL likely still open

**Skip when:**

- Trivial single-file changes (1-row registry addition)
- Pure additive work (new tests, comments, docs)
- Plan body already enumerates type-change deltas + field uniqueness + include direction (e.g., via prior `/blindspot-scan` fire)
- Pre-coding audit gate returned RED on SHAPE layer — fix SHAPE first; rerun gate; THEN fire `/blindspot-scan`

## Invocation

```
/blindspot-scan <plan_path> [pillars] [target_step]
```

**Args:**

- `plan_path` (REQUIRED) — workspace path to the sub-ship plan being audited. Shape: `plans/<sprint-dir>/subplans/<plan-filename>.md`
- `pillars` (OPTIONAL; default = `all`) — comma-separated subset of pillars to audit. Use to narrow scope when only specific risks apply:
  ```
  pillars := all | <pillar>[,<pillar>]...
  pillar  := B1 | B2 | B3 | B4 | B5 | B6 | B7 | B8 | B9 | B10 | B11 | B12 | B13 | B14 | B15
  # B13 = cross-walker struct-field uniqueness (existing pillar)
  # B14 = multi-surface deletion ordering (NEW v5.15.5.F.4d.1.B.4 v1.7.5 WIP-12; Stage 2 DRAFT;
  #       sister memory feedback_multi_surface_deletion_ordering_discipline; sister Check 41;
  #       fires when plan body proposes feature deletion spanning ≥3 files)
  # B15 = unconditionalization latent assumption shift (NEW v5.15.5.F.4d.1.B.4 v1.7.5 WIP-12;
  #       Stage 2 DRAFT — 1st instance only; sister memory feedback_unconditionalization_latent_assumption_audit;
  #       sister Check 42; fires when plan body proposes UNCONDITIONALIZE-body kind sites per
  #       B-Plus v0.4 generator classification)
  ```
  Examples:
  - `all` — full 15-pillar scan (default; updated v5.15.5.F.4d.1.B.4 v1.7.5 to include B13/B14/B15)
  - `B1,B2,B7,B11` — narrow to type-change + collision + include + template-context
  - `B8,B12` — narrow to consumer classification + row order (sister-skill-amendment dependencies)
  - `B14,B15` — narrow to deletion-class disciplines (multi-surface deletion ordering + unconditionalization latent assumption; sister to B-Plus v0.4 `--gen-deletion-cohort` mechanical classification)
- `target_step` (OPTIONAL) — specific Step in plan body to focus on (e.g., `Step 1.6.3`). Defaults to all IN-scope steps.

**Examples:**

```
# Full 12-pillar scan for a struct-gen-migration ship:
/blindspot-scan plans/<sprint-dir>/subplans/<plan>.md

# Narrow scan for a wire-format ship (B1+B12 focus):
/blindspot-scan plans/<sprint>/subplans/<plan>.md B1,B12

# Step-focused scan during multi-step ship:
/blindspot-scan plans/<sprint>/subplans/<plan>.md all "Step 1.6.3"
```

**Exit codes / verdict:**

- `GREEN` — all pillars GUARDED-BY-BUILD or IRRELEVANT or N-A; no pre-coding amendments needed
- `YELLOW` — 1+ pillar has SILENT-RISK or LOAD-BEARING-LOUD warnings; plan body amendments OR coding-time guards recommended
- `RED` — substantial pre-coding amendments needed before coding can proceed safely

Operator decides the next move; skill never auto-proceeds.

## Pillar verdicts (output classification)

Each pillar gets one of:

- **GUARDED-BY-BUILD** — risk exists but compile/test catches if missed; loud failure; recoverable
- **SILENT-RISK** — risk exists; no automated guard; could merge unnoticed; pre-coding amendment NEEDED
- **IRRELEVANT** — pillar doesn't apply to this plan (e.g., B10 only applies if struct is HMAC input; if not, IRRELEVANT)
- **N-A** — plan body or current code already enumerates the discipline (e.g., type-change deltas already in plan body Step X)
- **LOAD-BEARING-LOUD** — risk is LOUD but rebuild cycle cost is high (≥2h); pre-coding amendment EFFICIENT

## Execution model — Layer 2 audit skill

This skill is fired as a Layer-2 subagent by `/precoding-audit-gate` (extended audit set) OR fired manually by operator. When fired as Layer-2:

```
LAYER 2 (this skill, inside Explore subagent):
  - Reads plan_path body
  - Reads referenced DESIGN_SPECS (especially implementation-layer-blindspot-taxonomy.md)
  - Walks 12-category taxonomy against plan body + current code
  - Writes report to plans/plan_checks/blindspot-scan-<YYYY-MM-DD>-<scope>.md
  - Returns concise synthesis (under 700 words)
```

**HARD RULE:** DO NOT spawn nested subagents. This skill performs all 12 pillar walks directly via Read + Bash (grep / rg / ls).

## Pass structure

### Stage 1 — Plan + code-state resolution

1. Read plan body; extract IN-scope steps (Step 0 / Step 0.5 / Step 1.x / etc.)
2. Read current engine `Version.hpp` + `git log -5 --oneline` to determine HEAD state vs plan body assumptions
3. Identify currently-flagged metadata-bit derived filter cohorts: for any metadata-bit derived filter, grep its `<BIT_NAME>` against the registries enumerated in its `FOREACH_DERIVED_FILTER` row
4. For each in-scope Step, identify which pillars to fire (per "When to fire" trigger criteria)

### Stage 2 — Per-pillar walk

For each pillar B1-B12 (or narrowed subset per `pillars` arg):

**B1 — Type-change cascade**
- Read existing struct definition (e.g., ModelStampResult before migration)
- Read master registry STORAGE_T columns for currently-flagged rows
- Diff old type vs new type per row
- Emit punch-list of type-change deltas
- Verdict: LOAD-BEARING-LOUD if any TYPE-SENSITIVE consumer count ≥10; GUARDED-BY-BUILD if <10

**B2 — Field-name collision**
- Extract field-name set from each registry (per-core / global / ml_cfg_flag / gate_cfg_flag)
- Pairwise intersect
- Emit: any non-empty intersection = collision risk + flag intentional vs accidental
- Verdict: SILENT-RISK if any intersection unaccounted; GUARDED-BY-BUILD if all enumerated

**B3 — Transitional state coexistence**
- Enumerate field sets from SOURCE walker + TARGET walker
- Estimate peak struct size during transition
- Check plan body for "transitional budget = N KB" annotation
- Verdict: SILENT-RISK if peak >25KB OR no plan annotation; N-A if plan annotates explicitly

**B4 — Surface G applicability**
- For each registry, identify whether consumer reads `has_<name>` vs `<name>` direct
- Emit per-registry semantic verdict
- Verdict: SILENT-RISK if dead-byte fields generated unconditionally without rationale; N-A if intentional sister-consistency

**B5 — Compile-time scaling**
- Estimate instantiations: rows × template-fn-count × call-site-count
- Threshold: ≥1000 instantiations warn; baseline build time +20% warn
- Verdict: GUARDED-BY-BUILD (build catches if too slow)

**B6 — STORAGE_T variant coverage**
- Enumerate STORAGE_T variants from master registries
- For each: verify `tt::cfg_parse_field<T>` + `tt::cfg_emit_field<T>` + `tt::cfg_drift_compare<T>` + `tt::cfg_set_field<T>` have a covering branch
- Verdict: GUARDED-BY-BUILD (CI tool `check_storage_t_coverage.py` catches at build)

**B7 — Include topology cycle**
- Identify proposed new include edges
- Inspect current include graph (rg "#include" on target files)
- Detect cycles
- Verdict: GUARDED-BY-BUILD (compile fails loud)

**B8 — Type-sensitive consumer classification**
- For each consumer site from `/trace-deps` enumeration, classify:
  - TYPE-SENSITIVE-READ (compares against literal of OLD type)
  - TYPE-SENSITIVE-WRITE (assigns to OLD-type variable)
  - TYPE-AGNOSTIC (passes through)
- Emit per-site classification
- Verdict: LOAD-BEARING-LOUD if TYPE-SENSITIVE total ≥30; GUARDED-BY-BUILD if <30

**B9 — Unverified audit claims**
- For each claim in upstream audit reports about runtime behavior or type compatibility, check file:line citation
- If missing, demand follow-up read
- Verdict: SILENT-RISK if any uncited claim drives subsequent decision

**B10 — Struct layout drift**
- Check if affected struct is used in any byte-equivalence context (memcmp / SHA-256 / HMAC input / wire format)
- If YES: enforce H12 invariant; if NO: cosmetic
- Verdict: IRRELEVANT if not byte-equivalence input; SILENT-RISK if byte-equivalence + H12 not enforced

**B11 — if-constexpr template context**
- Identify host function context for proposed `if constexpr` filter walker
- Verify enclosing function is template-instantiated
- Verdict: GUARDED-BY-BUILD (compile fails loud)

**B12 — Cross-registry row ordering**
- Diff legacy walker emit order vs master registry declaration order
- Verify Layer 5b invariants tolerate the diff OR plan annotates intentional reorder
- Verdict: SILENT-RISK if order differs and not annotated; N-A if annotated

### Stage 3 — Synthesize + write report

Write report to `plans/<sprint-dir>/plan_checks/blindspot-scan-<YYYY-MM-DD>-<scope>.md` with structure:

```
# /blindspot-scan report — <plan> — <YYYY-MM-DD>

## Summary
- Pillars fired: <count>
- GUARDED-BY-BUILD: <count>
- SILENT-RISK: <count>
- LOAD-BEARING-LOUD: <count>
- IRRELEVANT: <count>
- N-A: <count>

## Per-pillar verdicts

| Pillar | Verdict | Finding | Action |
|---|---|---|---|
| B1 | LOAD-BEARING-LOUD | 27 type-change deltas; ~80 TYPE-SENSITIVE consumer sites | Pre-coding diff |
...

## Punch-list (ordered by severity)
1. <action> (closes <pillar>; effort <minutes>)
2. ...

## Recommended next move
- (X) Audit-first: amend plan body before coding (~M min)
- (Y) Coding with annotations: write code; surface remaining via build (~M min coding + ~M min rebuild)
- (Z) Defer pillar X to next ship; document TECH_DEBT

## Inflection check
Per feedback_iteration_spiral_signals_audit_meta_gap:
- Iteration count since last meta-gap codification: <count>
- NEW pillars surfaced this fire: <count> (if >0, add B13+ row to taxonomy DESIGN_SPEC)
```

### Stage 4 — Return synthesis to operator

Print:
- Report location
- GREEN / YELLOW / RED verdict
- Pillar verdict summary table
- Top 3-5 punch-list items
- Recommended next move

**DO NOT auto-proceed past findings.** Per `feedback_consult_on_audit_findings`: present findings + list potential fixes + iterate with operator.

## Auto-write contract

Per CLAUDE.local.md:
- Audit findings → `plans/<sprint-dir>/plan_checks/blindspot-scan-<YYYY-MM-DD>-<scope>.md`
- NEW blind-spot category surfaced (B13+) → DESIGN_SPECS/meta-disciplines/implementation-layer-blindspot-taxonomy.md amendment (add row + worked example)
- NEW TECH_DEBT items → DOCS/TECH_DEBT.md (if defer decisions emerge)

The skill writes the per-audit report. Taxonomy amendments + TECH_DEBT writes are operator-mediated post-synthesis.

## Distinct from sister skills

| Skill | Layer | Catches |
|---|---|---|
| `/parity-check` | SHAPE | train↔serve identity; wire-format byte risks |
| `/trace-deps` | SHAPE | dependency chains; function/symbol existence |
| `/readiness` | SHAPE | plan completeness; cold-pickup |
| `/merge-scan` | SHAPE | reuse opportunities |
| `/dod-audit` | SHAPE | DESIGN_SPECS pattern application |
| `/accounting-audit` | DOMAIN | OMS/fee/P&L paths |
| `/hft-audit` | DOMAIN | universal HFT principles |
| `/registry-fit-audit` | DOMAIN | registry misapplication |
| **`/blindspot-scan`** | **IMPLEMENTATION-DETAIL** | **12 categories of code-layer risks SHAPE audits miss** |

## Cost model

- Per-pillar walk: ~3-5 min wall clock (grep + read + verdict)
- Full 12-pillar scan: ~30-45 min wall clock (sequential pillar walk)
- Synthesis: ~5 min
- **Total: ~30-50 min wall clock per fire**

vs alternative (no `/blindspot-scan`; rely on build to surface): ~1-2 build cycles per LOUD pillar caught late = ~30-60 min × 2 = 60-120 min. ROI positive for migrations crossing ≥2 registries.

## Anti-patterns to avoid

- ❌ Treating SHAPE audit GREEN as implementation-detail GREEN. They're orthogonal layers.
- ❌ Adding new blind-spot categories without DESIGN_SPEC entry. Taxonomy MUST stay synchronized.
- ❌ Spawning nested subagents from inside this skill. Layer 2 only.
- ❌ Auto-proceeding past SILENT-RISK pillars without operator triage.

## Cross-references

- `DESIGN_SPECS/meta-disciplines/implementation-layer-blindspot-taxonomy.md` — the canonical taxonomy this skill instantiates
- `DESIGN_SPECS/audit-methodologies/audit-driven-pre-coding-gate.md` — parent pattern; this skill extends the audit catalog
- `claude-skills/precoding-audit-gate/SKILL.md` — orchestrator that can fire this skill in extended audit_set
- `tools/check_field_name_uniqueness.py` (B2) + `tools/check_storage_t_coverage.py` (B6) — automated CI guards
- engine memory `feedback_implementation_detail_blindspot_recovery_via_taxonomy.md` — operator-collaboration rule
- engine memory `feedback_consult_on_audit_findings` — present + iterate rule
- engine memory `feedback_iteration_spiral_signals_audit_meta_gap` — meta-gap codification trigger
