---
type: meta-discipline
stage: 3-first-canonical
version: 1.3
established: 2026-05-26
last_amended: 2026-05-27
tags: [meta-discipline, framework-discipline, structural-fix, doc-discipline]
surface: [doc-pipeline, ci-tooling, plan-pipeline]
sister_specs:
  - structural-fix-preferred-decision-framework.md
  - pattern-codification-lifecycle.md
  - implementation-layer-blindspot-taxonomy.md
  - cfg-field-categorization-discipline.md
  - canonical-sister-extension-discipline.md
  - sister-cohort-amendment-completeness-discipline.md
audit_tier: framework-pattern
applies_at_skills: [/readiness, /handoff, /sync-workspace, /capture-audit, /precoding-audit-gate]
canonical_applications:
  - 1st (v5.15.5.F.4d.1.B.4 WIP-10 — B-Plus CI tool v0.3 line-anchor verification at COMMIT layer; Class 14 fabricated-symbol detection)
  - 2nd (v5.15.5.F.4d.1.B.4 WIP-14b — B-Plus v0.4 --gen-deletion-cohort generator mode at OPERATOR-USE layer; B14 multi-surface deletion ordering mechanization)
  - 3rd (v5.15.5.F.4d.1.B.4 WIP-16 — CI Check 8 5-question consumer-pattern verify mechanical sidecar at /capture-audit; cfg field categorization at registry add time)
  - 4th (v5.15.5.F.4d.1.B.4 v1.7.6 Phase Cx-J — /readiness Check 44 cfg field categorization plan-time verification sister to CI Check 8 commit-time)
  - 5th (v5.15.5.F.4d.1.B.7 — RETROACTIVE; Check 9 in tools/check_per_core_registry_integrity.py — paired-access mismatch detector for Class 26 sub-shape A; codification entry was implicit in `.B.7` ship close but never added to this list; added at `.B.8` per /readiness MED-2 + /blindspot-scan M7 forward-promise verification)
  - 6th (v5.15.5.F.4d.1.B.8 — Check 10 in tools/check_per_core_registry_integrity.py — UNINDEXED-GLOBAL detector for Class 26 sub-shape B; sister extension of Check 9 per canonical-sister-extension-discipline.md v1.1 CI-tooling-surface axis; sanity-verified via revert-detect-reapply on HIGH-1)
---

# Structural enforcement when memory codification proves insufficient (M7)

## Why this discipline exists

Memory codification is the codebase's discipline-installation layer. Auto-loaded `memory/*.md` files give Claude per-session access to operator-collaboration rules + bug-class disciplines + recurrence triggers. For many bug classes, this works: the rule loads, fires at the moment of action, prevents the bug.

But some bug classes have **recurrence dynamics that memory alone cannot prevent**. Empirical evidence at `.B.4` v1.7.3 → v1.7.4 cycle:

- v1.7.3 codified `feedback_enumerate_helper_signature_args_before_extract` (M6 META-discipline at body-content layer)
- In SAME v1.7.4 cycle (AFTER M6 codification), Claude introduced **6 NEW Class 14 fabrications** during plan body mechanical fixes
- **5 audit agents + M6 memory codification missed all 6**
- B-Plus CI tool (`tools/check_plan_body_symbol_existence.py`) caught all 6 deterministically at compile time

Pattern: memory loads + audits fire, BUT during high-cognitive-load amendment cycles (9 amendments v1.0 → v1.7.4 with cross-methodology audits + scope expansions + mechanical refactor application), the right-symbol-at-right-time check gets skipped or mis-applied. Memory says "verify symbol exists"; Claude thinks "I just verified that one" and misses the next one introduced 5 lines later.

**Conclusion:** When memory codification of a discipline proves insufficient at next-cycle observation (same bug class recurs DESPITE the codified memory at the SAME surface in the SAME cycle as codification), escalate to STRUCTURAL ENFORCEMENT — CI tool / pre-commit hook / compile-time check / static_assert / linter rule.

## Pattern-codification lifecycle (6 stages)

Each Class N bug class progresses through these stages. Most plateau at Stage 3-5 because discipline-installation works. Bug classes that RECUR AT Stage 5 are candidates for Stage 6 escalation per this discipline.

| Stage | Codification | Mechanism |
|---|---|---|
| 1 — Recognition | Single instance; one-time patch | Commit message references the fix |
| 2 — Recurrence | 2nd-3rd instance; discipline articulated | `RECURRING_BUG_PATTERNS.md` entry + sister memory candidate |
| 3 — Memory codification | Rule load via MEMORY.md index; sister DESIGN_SPECS pattern documented | `memory/*.md` + `DESIGN_SPECS/*.md` |
| 4 — Audit-time check | `/readiness` Check N added; plan-time verification | `/readiness` SKILL.md Check N row |
| 5 — Multi-agent audit fires | `/precoding-audit-gate` orchestrator + parallel agents | Skill cross-refs each other |
| 6 — STRUCTURAL ENFORCEMENT | CI tool / pre-commit hook / static_assert / compile-time check | `tools/check_*.py` + `.git/hooks/pre-commit` + CMake static_assert |

THIS DISCIPLINE governs the Stage 5 → Stage 6 escalation trigger.

## Observational triggers (when to escalate)

| Signal | What it means | Stage 6 action |
|---|---|---|
| Memory codified at vX.Y; bug class recurs at vX.Y+1 of same cycle | Cognitive-load failure mode; memory loads but doesn't fire at action moment | Build CI tool / pre-commit hook / static_assert |
| Multiple agents miss same bug class instance | Audit-shape can't catch this class; needs deterministic check | Build mechanical verifier |
| Bug class has compile-detectable signature (symbol existence / type match / signature parity) | Compile-time check is feasible | Prefer compile-time over runtime check |
| Bug class is amendment-cycle-prone (introduced during edits, not initial drafts) | High-cognitive-load surface | Pre-commit hook gates commits |
| Bug class involves source-code-drift (X renamed to Y; A field removed; signature changed) | Memory can't track HEAD state | Tool that reads HEAD directly |

## Worked examples

### Stage 6 promotion: Class 14 (fabricated symbol) → B-Plus CI tool

- **Stage 3 codification:** `feedback_verify_symbol_existence_at_plan_drafting_time` (v5.15.5.F.4d.1.B.3 v1.5)
- **Stage 4 codification:** `/readiness` Check 32 (planned but pre-tool)
- **Stage 5 codification:** 4-pillar audit checks symbol existence at audit time
- **Recurrence at Stage 5:** v1.7.3 → v1.7.4 cycle introduced 6 NEW Class 14 fabrications (`current_book_imbalance` / `depth_enabled` / `current_spread` / `current_mid_price` / `tick.timestamp_us` / `FPN_IsZero(double)`)
- **Stage 6 enforcement landed:** `tools/check_plan_body_symbol_existence.py` v0.2 + `.git/hooks/pre-commit` + `tools/install-git-hooks.sh`. Tool extracts ```cpp blocks, derives includes per symbol, wraps in templated test harness, compiles via g++. Real fabrications → FABRICATION exit code; caller-scope refs → HARNESS-ISSUE (informational).
- **Outcome:** Tool catches all 6 fabrications + future instances deterministically; pre-commit hook blocks commits containing fabricated symbols.

### Stage 6 promotion: M6 (body-content arg enumeration) → /capture-audit skill

- **Stage 3 codification:** `feedback_enumerate_helper_signature_args_before_extract` (v5.15.5.F.4d.1.B.4 v1.7.3)
- **Stage 4 codification:** `/readiness` Check 33 (planned)
- **Stage 5 codification:** 5-agent comprehensive audit catches body-args at audit time
- **Recurrence:** None yet at sister surface; pre-emptive Stage 6 escalation
- **Stage 6 enforcement landed:** `/capture-audit` skill checks plan body frontmatter + body-content artifact CSV existence

### Candidate Stage 6 promotions (future)

| Bug class | Current stage | Stage 6 escalation candidate? | Trigger to watch |
|---|---|---|---|
| Class 18 (consumer drift on registry-row deletion) | Stage 3 (`feedback_enumerate_consumers_before_registry_row_deletion`) | YES if recurs at Stage 5 | Watch upcoming `.B.5-.B.11` umbrella for consumer-grep drift |
| Class 23 (type punning via reinterpret_cast) | Stage 5 (tt:: type-trait dispatch + 4-pillar audit + H13 invariant) | NO — invariant + compile-time check already in place | — |
| Class 27 (decision-time data binding) | Stage 5 (DESIGN_SPECS + /accounting-audit) | Watch for recurrence at decision-time-data-binding-pattern instances | — |

## Skill integration

Stage 6 escalations integrate with the skill suite:

| Skill | Stage 6 mechanism |
|---|---|
| `/readiness` Check 32 | Invokes B-Plus CI tool (`tools/check_plan_body_symbol_existence.py`) for plan body symbol verification |
| `/capture-audit` | Checks MEMORY.md index sync + plan body audit_tier frontmatter + handoff doc currency + DESIGN_SPECS Stage promotion eligibility |
| Pre-commit hook (`.git/hooks/pre-commit`) | B-Plus CI tool runs on staged plan body .md files; blocks commit on FABRICATION exit code |
| `/sync-workspace` | Invokes `/capture-audit` before commit to verify decision-capture completeness |
| `/handoff` | Invokes `/capture-audit` before writing handoff doc to verify nothing's missing |

## Anti-patterns this prevents

- **Memory-then-forget cycle:** codify discipline → ship → bug class recurs at next cycle → re-codify → repeat
- **Audit-blind-spot proliferation:** new audits added each iteration but bug class slips through cracks between audits
- **Over-reliance on memory:** assuming memory codification is sufficient for ANY discipline; ignoring cognitive-load amplifier surfaces
- **Under-investment in structural enforcement:** "the memory rule should be enough" when empirical evidence says otherwise

## When NOT to escalate to Stage 6

- Bug class has plateau'd at Stage 3-5 (instances STOPPED recurring after codification)
- Bug class has no compile-detectable signature (e.g., subjective design choices)
- Cost of structural enforcement >> cost of bug class instances (rare; usually structural enforcement amortizes quickly)
- Bug class only manifests in one specific surface (Stage 6 tool would be over-engineered for narrow use)

## Cross-references

- `DOCS/DESIGN_PHILOSOPHY.md` § 11.5 (parent meta-discipline registry; M1-M7)
- `DESIGN_SPECS/meta-disciplines/structural-fix-preferred-decision-framework.md` (parent meta-rule)
- `DESIGN_SPECS/meta-disciplines/pattern-codification-lifecycle.md` (sister: 6-stage lifecycle)
- `DESIGN_SPECS/meta-disciplines/implementation-layer-blindspot-taxonomy.md` (M4 sister)
- `memory/feedback_structural_enforcement_when_memory_insufficient.md` (operator-collaboration rule)
- `memory/feedback_structural_fix_for_recurring_class.md` (parent rule)
- `memory/feedback_verify_symbol_existence_at_plan_drafting_time.md` (Class 14 Stage 3 codification)
- `claude-skills/capture-audit/SKILL.md` (Stage 6 enforcement skill)
- `tools/check_plan_body_symbol_existence.py` (Stage 6 enforcement tool — first canonical application)
