---
type: skill-check
check_id: 32
parent_skill: /readiness
parent_path: claude-skills/readiness/SKILL.md
title: Plan-body symbol-existence verification (B-Plus CI tool)
established: 2026-05-26
sister_checks: [check-33-body-content-arg-enumeration, check-34-audit-tier-declaration-and-scope-match]
---

# /readiness Check 32 — Plan-body symbol-existence verification (v5.15.5.F.4d.1.B.4+)

**When this fires:**
ALWAYS for plan bodies containing ```cpp code samples (the typical case). Runs the B-Plus CI tool `tools/check_plan_body_symbol_existence.py` against the plan body file at plan-time. Catches Class 14 fabricated-symbol bugs at compile time deterministically.

**Why this matters (v5.15.5.F.4d.1.B.3 + .B.4 lesson):**

`feedback_verify_symbol_existence_at_plan_drafting_time` (Class 14 / v1.5 codification) was promoted to Stage 6 cadence-locked at v1.7 D3 of `.B.4` with the rationale that **memory codification + audit cycles alone cannot prevent in-cycle recurrence**. Worked example: v1.7.3 → v1.7.4 cycle introduced 6 NEW Class 14 fabrications in Step C.4 BACKTEST caller code block AFTER M6 codification + 5 audit agents had passed the plan body. Pattern was:

- Plan body code samples reference helper functions / cfg fields / struct members / macros that look plausible (drift from refactor) but don't exist or have different signatures at HEAD
- Audit agents read the plan body for *intent* + *structural soundness*; they miss specific field/path/signature drift
- Coding-time grep-verify catches most cases BUT in-cycle plan-body amendments BETWEEN audit cycles still introduce fabrications

The CI tool extracts every ```cpp block, derives includes per symbol, wraps each block in a templated test harness, and tries to compile via g++. Real fabrications cause compile errors classifying as `FABRICATION` (vs `HARNESS-ISSUE` for caller-scope statics / X-macro expansion fragments / shim-context references). Cycle: amend plan body → run tool → fix any FABRICATION findings → commit.

**What to verify:**

Run the CI tool against the plan body:

```bash
python3 tools/check_plan_body_symbol_existence.py <plan-body.md>
```

Exit codes:
- `0` — all code blocks compile (no fabrications)
- `1` — at least one fabrication detected
- `2` — script error / missing dependencies

For HARNESS-ISSUE blocks (caller-scope statics / X-macro fragments / shim-context refs) → use `--strict` to see them; they're informational, not blocking.

Verdict:
- **PASS** — exit 0; zero FABRICATIONS detected
- **GAP** — exit 1 with FABRICATION findings; report each (line + symbol + compile error) and require operator-decision fix-vs-defer
- **DEFERRED** — exit 1 BUT operator explicitly tagged the block as HARNESS-ISSUE with documented rationale (rare; expect to extend tool's classification instead)

**Output:**

If FAIL, add to the /readiness report:

```
### Plan-body symbol-existence finding (Check 32)

CI tool tools/check_plan_body_symbol_existence.py detected N FABRICATION(s):

  ❌ FABRICATION at <plan>.md:line~<N>
    block excerpt: '<first line of block>'
    error: <compiler error line>
  [...]

Action required: amend plan body before next coding step. Each FABRICATION is
a Class 14 instance — either correct the symbol/field/signature against HEAD
OR remove the citation if speculative.

Run `python3 tools/check_plan_body_symbol_existence.py --strict <plan>` to see
HARNESS-ISSUE blocks (informational; tool's shim doesn't model the caller scope).
```

**Effort:** 30-60 seconds per plan body audit (one tool invocation; g++ runs ~10 compile checks per typical plan body). Tool maintains include map at `SYMBOL_INCLUDES` constant — extend as new symbols surface.

**Sister checks:**

- **Check 33** — body-content arg enumeration completeness (sister M6 discipline; helper-extract signature verification at plan-time; this Check 32 runs at code-sample layer)
- **Check 34** — audit tier declared in plan frontmatter (orchestration; matches audit depth to plan risk)

**Trigger origin:** v5.15.5.F.4d.1.B.4 v1.7.4 cycle (6 NEW Class 14 fabrications introduced in-cycle AFTER M6 codification proved memory-only enforcement insufficient). Tool catches at compile-time what audit agents miss; structural enforcement of `feedback_verify_symbol_existence_at_plan_drafting_time` Stage 6 promotion.

**Tool maintenance:**

- New symbols → add to `SYMBOL_INCLUDES` map in `tools/check_plan_body_symbol_existence.py`
- New caller-scope patterns surfacing as false-positives → add regex to `CALLER_SCOPE_PREFIXES`
- New known-harness-fn signature mismatches → add to `KNOWN_HARNESS_FN_MISMATCHES`
- Quarterly review of HARNESS-ISSUE count — if > 30% of blocks classify as harness-issue, refresh shim model
