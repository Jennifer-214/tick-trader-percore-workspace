---
type: skill-check
check_id: 29
parent_skill: /readiness
parent_path: claude-skills/readiness/SKILL.md
title: Mechanical citation drift discipline
established: 2026-05-18
---

# /readiness Check 29 — Mechanical citation drift discipline (v5.14.10+)

**When this fires:**
EVERY plan with file:line citations OR named function/struct/macro references in the body. Pre-coding gate; runs as Step 1 of /readiness on any plan older than ~1 sprint cycle.

**Why this matters (v5.14.10 lesson — most-common audit finding type):**

The v5.14.10 sprint's pre-coding audit caught 8 mechanical citation drift items in the v5.14.10 plan (which was drafted 2026-05-08 and ran through pre-coding gate 2026-05-10 after intervening v5.14.9.F.2 ML_CFG_FLAG migration). Examples:

- `EnsembleModelZoo.hpp` cited 8+ times — actual file is `CoreModelZoo.hpp` (filename misleading; struct EnsembleModelZoo lives there alongside CoreModelZoo struct)
- ML_BuildParameters dispatch cited at `:~835` — actual location post-v5.14.9.F.2 was `:887-1009` (~80-line shift)
- Plan heading + body said "v5.14.11" — renumbered to "v5.14.10" in MASTER on 2026-05-10
- Predecessor refs said "v5.14.7" (DEFERRED-INDEFINITE) — should be "v5.14.9" (actual predecessor)

These would have tripped Step 0 of coding immediately ("identify what's adjacent to X" fails when X doesn't exist by that name). Catching them at audit time vs coding time is ~zero-cost vs ~30-60 min lost to figuring-out-what's-real per drift item.

**What to verify:**

For each file:line reference in the plan body, run:

```bash
# Verify the claimed file exists
[ -f <plan-cited-path> ] && echo PASS || echo MISSING

# Verify the cited line range matches what the plan describes
sed -n '<start>,<end>p' <plan-cited-path> | head -20
# Compare against plan's "the dispatch site does X" claim
```

For each named function/struct/macro reference in the plan body, run:

```bash
# Verify the symbol exists with the cited shape
rg -n "\b<symbol>\b" --glob '*.hpp' --glob '*.cpp' | head -10
# If 0 hits → MISSING
# If hits in different file than plan claims → DRIFT
# If signature/shape differs from plan claim → DRIFT
```

For each version reference in the plan body (predecessor, rollback anchor, sub-tag refs), run:

```bash
git tag --list 'v5.14.*' | sort -V
# Verify the cited version exists + chronologically precedes the planned ship
```

Verdict per drift item:
- **PASS** — citation matches HEAD
- **DRIFT — line ref shifted** — file exists; line range moved; update plan
- **DRIFT — symbol renamed** — symbol exists at different path or different signature
- **MISSING — symbol absent** — plan claim is stale; reject or research current state
- **MISSING — version absent** — predecessor / rollback anchor doesn't exist; correct to actual

**Output format:**

Append a "Mechanical citation drift" sub-section to the /readiness report:

```
### Mechanical citation drift findings

| Plan claim | Actual at HEAD | Verdict |
|---|---|---|
| `EnsembleModelZoo.hpp:820` | `ML_Headers/CoreModelZoo.hpp:820` | DRIFT — filename misleading; struct EnsembleModelZoo lives in CoreModelZoo.hpp |
| `ML_BuildParameters dispatch ~835` | `Strategies/StrategyParameters.hpp:887-1009` | DRIFT — line shifted ~80 lines post-v5.14.9.F.2 |
| ... | ... | ... |
```

Drift items are NOT blocking by themselves (they're mechanical); but ALL drifts must be corrected in the plan body before coding starts (otherwise Step 0 of coding trips immediately).

**Effort:** 5-10 min per audit (depending on plan size + age). Plans drafted in current sprint cycle: ~2-3 min. Plans 1+ week old: ~10-15 min.
