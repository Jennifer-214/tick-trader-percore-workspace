---
type: skill-check
check_id: 27
parent_skill: /readiness
parent_path: claude-skills/readiness/SKILL.md
title: DESIGN_SPECS pattern-application audit
established: 2026-05-18
---

# /readiness Check 27 — DESIGN_SPECS pattern-application audit (v5.14.9+; via /dod-audit)

**When this fires:**
EVERY plan with proposed code surface (new functions, structs, registry
entries, cfg fields, hot/slow path additions). Acts as the
data-oriented-design pre-coding gate complementing Check 11
(architectural sprint detection), Check 13 (strategy lifecycle), and
Check 18 (reuse audit).

**What to verify (compose-by-reference per SKILLS_HIERARCHY.md):**

Read `claude-skills/dod-audit/SKILL.md` and apply its audit procedure
INLINE as a sub-section of this report. DO NOT spawn a nested subagent.

The /dod-audit procedure:
1. Reads `tick-trader-percore-workspace/DESIGN_SPECS/*.md` catalog
   dynamically (registry-driven; new patterns auto-included)
2. Walks the plan's proposed code/structures
3. Scans for missed pattern applications across 10 baseline check
   categories: cache alignment, cache miss / false sharing,
   concurrency invariants, branchless candidates, bit-packing
   candidates, bit-field dispatchers, wire-format byte preservation,
   structural-fix-preferred decisions, math kernel constant-iter +
   branchless (v5.14.11.B.5+), struct byte-equivalence padding
   (v5.14.11.B.5+)
4. Cross-references each finding to the relevant DESIGN_SPECS doc
5. Severity-classifies (CRITICAL / HIGH / MEDIUM / LOW)

**Verdict mapping:**
- **PASS** ✅ — no missed pattern applications, OR all candidates
  acknowledged in plan with explicit application or DEFERRED rationale
- **APPLIED-N** — N existing applications correctly follow patterns
  (sanity check; no triage needed)
- **MISSED-N** ⚠️ — N candidate sites would benefit from pattern;
  plan should fold in OR document deferral with `// FUTURE
  OPPORTUNITY:` comment + TECH_DEBT entry
- **CRITICAL** 🛑 — pattern violation has correctness/perf risk
  (e.g., HMAC chain break, false sharing on hot path). Block ship.

**Procedure for plan-mode invocation:**

```bash
# Step 1: catalog ingest
# Walk DESIGN_SPECS/*.md (skipping README) and extract pattern signatures
ls tick-trader-percore-workspace/DESIGN_SPECS/*.md | grep -v README

# Step 2: surface enumeration from plan
# Parse plan body for: new fns / structs / X-macro entries / cfg fields /
# hot-path additions / slow-path additions / wire-format-affecting changes

# Step 3-5: per-pattern checks (full procedure in dod-audit SKILL.md)
# For each pattern in catalog, scan plan surface for missed applications
# using detection signatures + symptom-based heuristics.
```

**Anti-pattern caught (v5.14.9 plan-mode pre-coding 2026-05-10):**
v5.14.9 plan adds 4 new cfg fields + per-core override + PerCoreSnap
factor field. /dod-audit confirms: stamp-binding via FOREACH_STAMP_BOUND_CFG
is applied (item 21 AUTOPOPULATE pattern); FOREACH_DEGRADATION_CURVE
registry is applied (items 13, 22); branchless curve compute fns +
dispatch table is applied (items 18, 13); slow-path predicate cache
is applied (item 18(c)); PerCoreSnap state_flags bitmap is applied
(items 1, 20). MISSED would have been: bit-packing for ≥3 colocated
bools / X-macro for ≥3 parallel sites / AUTOPOPULATE for ≥2
production-callers. Plan-mode caught all candidates; coding starts
with patterns intentionally-applied.

**Cross-references:**
- `claude-skills/dod-audit/SKILL.md` — full procedure + check categories
- `tick-trader-percore-workspace/DESIGN_SPECS/` — pattern catalog
- `DOCS/SKILLS_HIERARCHY.md` — compose-by-reference model
- `DOCS/TECH_DEBT.md` — auto-write contract for deferred candidates
- `CLAUDE.md` items 13, 16, 18, 19, 20, 21, 22, 23 — pattern doctrine

**Effort:** 5-10 min per audit (10-15 min for full plans with
multiple subsystems touched).
