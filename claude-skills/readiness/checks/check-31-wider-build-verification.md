---
type: skill-check
check_id: 31
parent_skill: /readiness
parent_path: claude-skills/readiness/SKILL.md
title: Wider-build verification at last sprint close
established: 2026-05-18
---

# /readiness Check 31 — Wider-build verification at last sprint close (v5.15.2+; TECH_DEBT-033 closure)

**When this fires:**
ALWAYS — runs at the start of every /readiness audit. Verifies the predecessor sprint's close ran the wider build (`./build.sh gui suite tsan asan all`) not just the test target (`./build.sh test`).

**Why this matters (v5.14.post1 lesson):**

v5.14.11.C close ran `./build.sh test` (controller_test compiles + 2904 tests pass) but did NOT run `./build.sh gui suite tsan asan all`. v5.14.11.C's stamp body migration touched `train_model_worker_fn` in `Backtest/BacktestPanels.hpp` — a file ONLY compiled by `gui`/`suite` targets, not by the `test` target's narrow build. The miss surfaced post-merge when operator ran `./build.sh gui` and got compile errors. v5.14.post1 was the patch.

The class: sprint-close verification that only runs the test target HIDES compile errors in GUI/sanitizer-only consumers (BacktestPanels, MLStatusPanel, DashboardPanels, ASan/TSan instrumentation paths). These surface days/weeks later when someone runs the wider build. The fix is to run wider-build AT sprint close, not later.

**What to verify:**

For the predecessor sprint's umbrella postmortem + closing commits, check for evidence that the wider build was run:

```bash
# Search predecessor postmortems for the wider-build phrase
rg -i "build\.sh gui suite tsan asan all|wider build|gui suite tsan asan" \
    plans/<predecessor-sprint>/postmortems/ 2>/dev/null

# Search closing commit messages
git log --grep="gui suite tsan asan" \
    <pre-predecessor-anchor>..<predecessor-umbrella-tag> 2>/dev/null
```

Verdict:
- **PASS** — predecessor postmortem documents `./build.sh gui suite tsan asan all` GREEN result; commit messages reference the wider build
- **FAIL** — only `./build.sh test` evidence; predecessor MAY have missed GUI/sanitizer compile errors

**Output:**

If FAIL, add to the /readiness report:

```
### Wider-build verification finding (Check 31)

Predecessor sprint <name> postmortem documents only `./build.sh test` GREEN. The
`./build.sh gui suite tsan asan all` wider build was NOT verified at sprint close.

Risk: GUI panel / BacktestPanels / ASan/TSan consumers may have silent compile
errors that surface days later (v5.14.post1 class precedent).

Recommended action: run `./build.sh gui suite tsan asan all` on the predecessor
sprint's tag BEFORE the current sprint coding starts. If wider build fails, patch
the predecessor sprint with a `.postN` tag (matching v5.14.post1 convention).
```

This is non-blocking but flags risk. The current sprint can proceed; just be aware that pre-existing GUI/sanitizer compile errors will surface when the current sprint runs wider builds.

**Effort:** 1-2 min per audit (one grep + one commit-log scan). Always runs.

**Trigger origin:** v5.14.post1 patched a `train_model_worker_fn` migration gap that `./build.sh test` missed but `./build.sh gui suite` would have caught. TECH_DEBT-033 closure (v5.15.2.D).
