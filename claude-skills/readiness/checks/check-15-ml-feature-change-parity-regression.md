---
type: skill-check
check_id: 15
parent_skill: /readiness
parent_path: claude-skills/readiness/SKILL.md
title: ML feature change requires parity regression update
established: 2026-05-18
---

# /readiness Check 15 — ML feature change requires parity regression update

Trigger keywords in plan: `FOREACH_FEATURE`, `ML_Compute_`,
`Regime_ComputeSignals`, `RollingStats_Push`, `feature_matrix`,
`Features_PackAll`. When any present, require the plan to:

- Identify which snapshot test will fail post-change.
  Snapshot tests live at canonical snapshot location (currently
  `tests/controller_test.cpp` EXTENSIBILITY block; consult current
  location via grep for FOREACH_FEATURE / FOREACH_TARGET registry-hash
  test blocks).
- For each test that will fail, plan must specify EITHER:
  - **Bytewise-equivalent refactor** — change is provably
    output-identical; no snapshot update needed (verify by running
    `./build.sh test` and confirming snapshot tests still pass).
  - **Intentional semantic shift** — recorded snapshot values
    will be updated AND the relevant `FOREACH_FEATURE` row's
    `version` field will be bumped. CHANGELOG must list the bump
    with retrain requirement.
- For pure-additive changes (new features), `FEATURE_REGISTRY_HASH`
  flips automatically (X-macro adds a row). Plan must specify the
  retrain trigger.

**Why this matters:** v5.9.2a snapshot test discipline. Pre-v5.9.2a,
function-body changes silently passed `FEATURE_REGISTRY_HASH`
verification (no X-macro change → no hash flip). Models loaded fine,
predictions silently drifted. Snapshot tests catch this at PR time;
this check catches it at plan time.
