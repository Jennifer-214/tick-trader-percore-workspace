---
type: ledger-template
class_id: 33
title: Consumer-enumeration undercount on deletion (sister to Class 14 fabricated-symbols, flipped)
parent_index: DOCS/RECURRING_BUG_PATTERNS.md
established: 2026-05-26
surface_tags: [plan-time, registry, deletion-cohort]
severity: high
recurrence_count: 2
first_instance: 2026-05-25 (v5.15.5.F.4d.1.B.4 v1.4 amendment — N5 missed Regime_Classify write site at BacktestSharded.hpp:607 when planning consumer-enumeration for fc_ctx.regime_state deletion)
closure_mechanism: B-Plus v0.4 deletion-target consumer-enumeration helper (operator-facing planning helper at COMMIT layer; sister to v0.3 line-anchor) + sister memories feedback_multi_surface_deletion_ordering_discipline + feedback_operator_facing_doc_cohort_at_cfg_deletion + /readiness Check 41/37 audit-time enforcement
sister_classes: [14, 18, 31]
---

# Class 33 — Consumer-enumeration undercount on deletion (sister to Class 14 fabricated-symbols, flipped)

**Detected:** 2026-05-26 PM at `.B.4` v1.7.5 pre-amendment audit gate. /trace-deps + /merge-scan + /blindspot-scan multi-audit cross-validation surfaced cohort-undercount finding pattern with 2 ship-level instances. Class 33 NEW catalog entry codified at WIP-12 per pattern-codification-lifecycle.md Stage 2 Recurrence trigger (≥2-instance threshold met).
**Severity:** HIGH — undercount in deletion-cohort enumeration causes downstream consumers to be missed when deletion lands; either (a) compile fails at consumer site mid-WIP (LOUD but wasteful rebuild cycles) or (b) silent stale reference accumulates (SILENT regression class).

## Recurring symptom

Plan body declares deletion of feature/cfg/symbol/struct-member X. Lists expected consumer sites for deletion. **Misses N consumers** — actual codebase has more sites than enumerated. Class 33 instances share the flipped shape of Class 14:

- Class 14 = "cite X that doesn't exist" (fabricated symbol; plan body invents reference)
- Class 33 = "delete X but miss N consumers" (consumer-enumeration undercount; plan body misses real reference)

Both are catch-class for plan-body precision failures. Class 14 caught at compile time (symbol doesn't exist); Class 33 caught at consumer site (missed reference still exists post-deletion).

## Why this is a class (not a one-off bug)

Consumer-enumeration discipline (per [[feedback_enumerate_consumers_before_registry_row_deletion]]) is hard to apply mechanically at plan-drafting time:
- Each deletion target may have references across multiple file types (`.cpp/.hpp/.md/.cfg/.example/tests/`)
- Consumer enumeration via manual `rg` is error-prone (operator may run wrong pattern, miss surfaces, omit archived sites incorrectly)
- 4-pillar self-audit by Claude may converge on smaller cohort than actual (audits focus on code; miss operator-facing docs)

Recurrence is FORESEEABLE without structural enforcement:
- v1.4 N5 (2026-05-25): missed Regime_Classify write site at BacktestSharded.hpp:607 in planning consumer-enumeration for fc_ctx.regime_state struct-member deletion; caught at v1.4 amendment cycle after `/parity-check` re-audit
- v1.7.5 (2026-05-26 PM): missed 9 of 17 file surfaces (operator-facing docs + stale comments + archived changelogs LEAVE classification) in planning consumer-enumeration for `engine_arch` cfg-field deletion; v1.7.4 D17 framing said "8 branches + 3 wrappers + cfg field + parser + TUISnapshot + GUI gating" — actual = 17 files / 81 occurrences via operator-directed comprehensive `rg`

Both share shape: declared cohort < actual cohort.

## False-positive surface (per M3 discipline)

Not all enumeration mismatches are Class 33:
- **Per-WIP incremental delete-by-WIP is OK** — multi-WIP plan body intentionally enumerates per-WIP scope (e.g., WIP-13 deletes consumer A; WIP-14 deletes consumer B); not Class 33 if each WIP's enumeration is comprehensive for that WIP's scope
- **Amendment-history references in plan body frontmatter (KEEP):** prior amendment cycle line `v1_X_amended: ... reference to deleted symbol ...` is HISTORICAL CONTEXT, not a deletion target; Class 33 false-positive if mechanical tool flags
- **Archived changelogs (KEEP):** `DOCS/changelogs/<old-date>-*.md` files record what shipped at version X; LEAVE per [[feedback_archived_changelog_preservation_discipline]]; Class 33 false-positive if mechanical tool flags
- **Current CHANGELOG.md historical rows (KEEP):** rows dated PRIOR to current ship recorded context at that ship; LEAVE per same discipline
- **Sister-rule citations in memory files (KEEP):** memory file citing sister memory `feedback_X` (deleted feature reference) is sister-rule context, NOT a deletion target
- **DESIGN_SPECS pattern body references (KEEP):** spec body citing example pattern that was deleted in code is DOCUMENTATION RESIDUE acceptable per stage-life of the spec

## Closure mechanism

**Stage 6 STRUCTURAL ENFORCEMENT** per `DESIGN_SPECS/meta-disciplines/structural-enforcement-when-memory-insufficient.md` (M7 cadence-locked at this ship — B-Plus v0.4 = 3rd canonical):

1. **B-Plus v0.4 generator mode** (tools/check_plan_body_symbol_existence.py): `--gen-deletion-cohort PATTERN` — runs comprehensive `rg` over engine + workspace production code (excludes archived changelogs by default); classifies each match per deletion-kind heuristic (per [[feedback_multi_surface_deletion_ordering_discipline]] B14 leaves-first ordering); prints structured enumeration suitable for paste into plan body Phase A.6.5.c CSV artifact + Phase C deletion-step enumeration. Operator-facing planning helper at COMMIT layer; sister to v0.3 line-anchor mode.

2. **Audit-time check via /readiness Check 41** (sister to Check 32 + 33): when plan body proposes feature/cfg/symbol deletion spanning ≥3 files, verify cohort enumeration matches B-Plus v0.4 generator output (operator runs tool; manually verifies plan body matches). Future enhancement to /readiness or sister audit could automate verification.

3. **Sister memory codification** per `feedback_multi_surface_deletion_ordering_discipline` (B14) + `feedback_operator_facing_doc_cohort_at_cfg_deletion` + `feedback_archived_changelog_preservation_discipline`: discipline rules load at every session; covers deletion-ordering + operator-facing surface + archived-doc preservation specifically.

4. **Codification at deletion-class scope:** for ships with deletion-class scope (cfg field removal / API surface removal / cohort wrapper deletion / centralized-arch deprecation), the discipline is mandatory pre-coding gate via /readiness Check 41 + B-Plus v0.4 mechanical generation.

## Worked instances

- **v1.4 amendment (2026-05-25):** Plan body for `.B.4` v1.4 listed consumer enumeration of `fc_ctx.regime_state` field at BacktestSharded.hpp:541-548 (allocation) + :612 (read). Missed `:607` `Regime_Classify(&fc->regime_state, ...)` write site. Caught by `/parity-check` re-audit after v1.4 amendment lock. N5 amendment extended enumeration to 3 consumers. **Meta-observation at v1.4:** extends `feedback_enumerate_consumers_before_registry_row_deletion` from registry-row deletion to struct-member deletion discipline; sister catch shape.

- **v1.7.5 (2026-05-26 PM):** Plan body for `.B.4` v1.7.4 D17 listed cohort scope as "8 conditional branches at EngineSharded.hpp + 3 sister wrappers + cfg field + parser + TUISnapshot + GUI gating". Operator-directed `rg "engine_arch|ENGINE_ARCH_"` + `/trace-deps` + `/merge-scan` audits surfaced actual cohort: **17 files / 81 occurrences** spanning 9 code files + 4 operator-facing docs + 6 archived changelogs (LEAVE) + 3 stale comments. v1.7.5 amendment cycle expanded cohort enumeration via comprehensive surface sweep + codified B14 + B15 pillars + Class 33 NEW catalog entry + B-Plus v0.4 inline at WIP-12 per [[feedback_no_defer_for_effort]] + [[feedback_structural_fix_for_recurring_class]] M7 Stage 6 trigger.

## Sister classes

- **Class 14** (Plan calls a function or struct field that doesn't exist) — **FLIPPED sister** at fabricated-symbol layer; Class 14 cites X that doesn't exist, Class 33 deletes X but misses consumers; both catch plan-body precision failures via B-Plus CI tool (Class 14 via v0.2 + v0.3; Class 33 via v0.4)
- **Class 18** (Mirror plans missing data-flow dependencies) — parent family at mirror-incomplete layer; Class 33 is consumer-enumeration shape of Class 18 mirror discipline
- **Class 31** (Hardcoded refs in always-loaded docs) — sister at doc-layer drift family; both involve enumeration drift over time

## Cross-references

- `DESIGN_SPECS/meta-disciplines/structural-enforcement-when-memory-insufficient.md` (M7 parent; Stage 6 cadence-locked at this ship per B-Plus v0.4 = 3rd canonical)
- `DESIGN_SPECS/meta-disciplines/implementation-layer-blindspot-taxonomy.md` (B14 multi-surface deletion ordering pillar Stage 2 DRAFT; sister to this class at audit-layer)
- `tools/check_plan_body_symbol_existence.py` (B-Plus tool v0.4 generator mode; CI enforcement)
- `claude-skills/readiness/SKILL.md` (Check 41 sidecar at WIP-12; audit-time enforcement)
- `feedback_enumerate_consumers_before_registry_row_deletion.md` (parent meta-rule)
- `feedback_multi_surface_deletion_ordering_discipline.md` (B14 sister codification)
- `feedback_operator_facing_doc_cohort_at_cfg_deletion.md` (operator-facing-doc cohort sister)
- `feedback_archived_changelog_preservation_discipline.md` (archived-doc LEAVE classification sister)
- `feedback_verify_symbol_existence_at_plan_drafting_time.md` (Class 14 sister rule; this class is flipped sister)
- `feedback_structural_fix_for_recurring_class.md` (parent meta-rule for Stage 6 escalation)
- `feedback_no_defer_for_effort.md` (parent meta-rule for inline-at-recurrence vs defer-to-future-ship decision)
- v1.7.5 amendment summary at `plans/v5.15-live-readiness/subplans/2026-05-24-v5.15.5.F.4d.1.B.4-train-serve-execution-layer-parity.md` (this ship's first Class 33 codification cycle)
- Synthesis at `plans/v5.15-live-readiness/plan_checks/2026-05-26-v5.15.5.F.4d.1.B.4-v1.7.5-pre-amendment-gate-synthesis.md`
