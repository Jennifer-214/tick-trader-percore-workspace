# Check 45 — Tests-changed section enumeration

**Added:** v5.15.5.F.4d.1.D.1 (NEW). **Discipline:** `feedback_test_change_enumeration_per_plan_body` (M7 9th canonical structural enforcement). **Sisters:** Check 28 (test-strength anti-regression) + Check 21 (test-count assertion fragility) + Check 33 (M6 body-content arg enumeration).

## What this checks

Any plan body whose **Coding sequence** modifies engine `tests/` source MUST include a dedicated **`## Tests changed`** section enumerating three sub-categories:

- **(a) Modified tests** — existing assertions preserved, mechanically updated for new code shape (rename / signature change / struct field reorder).
- **(b) Broken / replaced tests** — tests exercising now-deleted/absorbed paths; DELETE (with B14 leaves-first ordering + Class 33 consumer-enumeration) OR REPLACE with an equivalent test against the new path.
- **(c) NEW unit tests** — for NEW functions / API surface; every NEW function gets a unit test verifying behavior given controlled inputs.

## When it fires

At `/readiness` run against any plan body. Also runs as a pre-commit hook on `plans/**/subplans/**.md` edits.

## Mechanical invocation (deterministic skill-tool integration)

    python3 /home/caramel/code/FoxML_Trader_v2/tools/check_plan_body_tests_section.py --plan-body <path> --strict

- Exit `0` = PASS (section present + 3 sub-categories enumerated, OR the coding sequence touches no `tests/`).
- Exit `1` = VIOLATION (section missing OR sub-categories incomplete when the coding sequence touches `tests/`).

Deterministic shell-out per `feedback_structural_enforcement_when_memory_insufficient` — NOT LLM-orchestrated discovery (no "remember to run it"; the hook + Check fire mechanically).

## First canonical application

`.E.1` Foundation (Core→Node rename ~200+ test-surface sites + multi-exchange / per-node-mode / cluster-aggregator NEW tests). Aligns with the D-36 `tests/{unit,integration,chaos,benchmark,property}/` reorg toward function-granularity unit tests.
