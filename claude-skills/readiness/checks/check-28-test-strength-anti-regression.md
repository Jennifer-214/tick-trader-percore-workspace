---
type: skill-check
check_id: 28
parent_skill: /readiness
parent_path: claude-skills/readiness/SKILL.md
title: Test-strength anti-regression audit
established: 2026-05-18
---

# /readiness Check 28 — Test-strength anti-regression audit (v5.14.9.D+; via /test-strength-audit)

**When this fires:**
EVERY plan that proposes test changes (new tests, modified tests,
deleted tests). Acts as the test-specification-integrity gate
complementing Check 27 (DESIGN_SPECS pattern application) — Check 27
is about CODE patterns; Check 28 is about TEST-SPEC integrity.

**Why this matters (v5.14.9.D 2026-05-10 lesson):**
During v5.14.9.D coding, agent weakened a failing assertion
(`sr.valid == 1` → `sr.model_format_version == 6`) to chase a green
build. Caramel caught it: "we cant just edit a test to make it pass and
lose out on an edge case or something". Reverted by deleting the
redundant test entirely with explicit redundancy-removal justification.
Test weakening is a Class-1 tech-debt source — it hides drift the same
way silent exception swallowing does. Especially critical for financial
trading software where edge case loss = real-money risk.

**What to verify (compose-by-reference per SKILLS_HIERARCHY.md):**

Read `claude-skills/test-strength-audit/SKILL.md` and apply its
5-pattern detection INLINE as a sub-section of this report. DO NOT
spawn a nested subagent.

The /test-strength-audit procedure scans for:
1. **Pattern A:** Count assertion weakenings (`==` → `>=` without
   `_smoke_check` suffix or registry-COUNT justification)
2. **Pattern B:** Strict-to-loose substitutions (`sr.valid == 1` →
   `sr.format_version == N` etc.)
3. **Pattern C:** Test deletion without justification (no commit-message
   citation of "covered by", "property no longer testable", or "test
   was wrong")
4. **Pattern D:** Empty / tautological assertions (`check("foo", true)`)
5. **Pattern E:** Comment-only test deletion (`// check(...)`)

**Plan-mode invocation procedure:**

```bash
# For plan-mode: parse plan body for test-related claims
# (e.g., "Tests: ~13 new", "delete obsolete v5.X.Y tests")

# For commit-mode: scan working tree / staged / commit-range
git diff -- 'tests/**/*.cpp' 'tests/**/*.hpp'
# Apply Pattern A-E detection (see /test-strength-audit SKILL.md)

# For each finding:
# - Cross-reference commit message for justification
# - Verify cited "covered by" tests actually exist + cover property
# - Severity-classify HIGH / MEDIUM / LOW
```

**Verdict mapping:**
- **PASS** ✅ — no weakening patterns found, OR all candidates have
  explicit justification per the deletion convention
- **HIGH** ⚠️ — assertion weakening hides drift. Block ship until
  reverted or explicitly justified per `_smoke_check` suffix or
  redundancy/obsolescence/fix citation
- **MEDIUM** ⚠️ — borderline pattern; weakening mildly justified but
  could be tightened. Address during current sprint.
- **LOW** — legitimate weakening (smoke_check suffix, registry COUNT
  loosening when registry grows). No action required.

**Test naming convention (enforced by Check 28):**

Tests with `_smoke_check` suffix are explicitly weak by design.
Pattern A/B/C reports skip these. Tests without the suffix are STRICT
by contract.

**Test-deletion justification convention (enforced by Check 28):**

When `check(...)` lines are removed, commit message must cite ONE of:
- "covered by `<existing_test_name>`" — REDUNDANCY (auditor verifies)
- "property no longer testable because `<X>`" — OBSOLESCENCE
- "test was wrong; correct invariant is `<new_check>`" — FIX

**Anti-pattern caught (v5.14.9.D 2026-05-10):**
Strict-to-loose substitution (Pattern B): `sr.valid == 1` removed,
replaced with `sr.model_format_version == 6`. No commit-message
justification. Reverted via test-deletion + redundancy citation
(comprehensive coverage by v5.14.1.B.3.E).

**Cross-references:**
- `claude-skills/test-strength-audit/SKILL.md` — full 5-pattern
  detection procedure
- `DOCS/SKILLS_HIERARCHY.md` — compose-by-reference model
- `DOCS/TECH_DEBT.md` — auto-write contract for deferred-weakening entries
- v5.14.9.D commit (b703e61) — pattern documented

**Effort:** 3-5 min per audit (commit-mode); 5-10 min for plan-mode
sweeps that surface multiple test-modifying changes.
