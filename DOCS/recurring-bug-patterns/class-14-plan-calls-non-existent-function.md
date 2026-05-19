---
type: ledger-template
class_id: 14
title: Plan calls a function or struct field that doesn't exist
parent_index: DOCS/RECURRING_BUG_PATTERNS.md
established: 2026-05-18
---

## Class 14 — Plan calls a function or struct field that doesn't exist

**Surface:** plan-time. (Detail: any plan in `plans/` that names a callee or struct
member without verifying it exists in the current codebase. Catches
silent staleness ("v5.10 plan claimed X exists; v5.13 deleted X")
AND wishful planning ("plan author meant to add X but forgot to
list it as NEW").

**Symptom:** plan-driven coding fails to link or compile partway
through implementation. Operator + Claude lose 30-90 minutes
investigating "why doesn't this build" when the answer is "the
function the plan referenced doesn't exist." Worse: if the plan
loosely references "the existing cancel API" without naming it,
implementation may invent a wrong signature → runtime UB instead
of compile failure.

**Detection:** [delegates to /trace-deps — that skill performs the plan-vs-codebase grep walk. Body below documents the pattern.]

**Root cause:** plan author wrote against assumed-existing surface
without `grep`ping the codebase. Common when:
- The plan references a function from an adjacent codebase (e.g.,
  v5.10 trader had it but v5.14 trader doesn't)
- The plan author saw a related function (e.g., `_MarketBuy`) and
  assumed siblings exist (`_CancelOrder`)
- The struct field was renamed in a recent ship the plan author
  didn't see (e.g., `dry_run` → `reconcile_mode`)
- Cross-ship coordination missed (Plan A adds field; Plan B claims
  to use it but A hasn't shipped yet — plans don't list dependency
  edge)

**Detection:**

```bash
# For each function name mentioned in a plan:
grep -rn "^inline.*PROPOSED_FN_NAME\|^.*PROPOSED_FN_NAME\s*(" \
   --include="*.hpp" --include="*.cpp" \
   CoreFrameworks/ ML_Headers/ Strategies/ DataStream/ Backtest/
# Empty result → BLOCKING gap; either add NEW claim or rename in plan

# For each struct field referenced (e.g., obj->field_name):
grep -A100 "^struct StructName" CoreFrameworks/<file>.hpp | \
   grep "field_name"
# Empty result → BLOCKING gap; either add field as NEW or fix plan

# For pre-coding plan audits, /trace-deps automates both walks +
# reports BLOCKING vs verified-PASS per callee.
```

**Known instances:**

- **v5.14.4 plan**: `BinanceOrderAPI_CancelOrder` — plan Step 4
  called the function; grep showed no such function exists in
  `DataStream/BinanceOrderAPI.hpp`. Detected by /trace-deps before
  coding. Fixed by adding v5.14.4.0 Phase 0 sub-tag to create the
  function (mirror `_MarketBuy`/`_MarketSell` pattern at :503/:549).
- **v5.14.4 plan**: `OrderManagerState.last_seen_trade_id` — plan
  Step 3 read the field; struct doesn't have it. Same fix
  (v5.14.4.0 adds field + zero-init in `OrderManager_Init`).
- **v5.14.7 plan (caught via cross-ship coordination)**: also
  claimed to add `BinanceOrderAPI_CancelOrder` as NEW. Master plan
  ordering: v5.14.4 ships first → v5.14.7's claim updated to
  REUSE v5.14.4.0's API instead of creating a duplicate.
- **v5.15.5.F.4b plan (2026-05-14 — caught at pre-coding audit gate)**:
  plan referenced 5 functions that don't exist — `CfgParser_HandleKV`,
  `Cfg_Save`, `Cfg_LoadFromString`, `Cfg_LoadFromFile`,
  `parse_csv_engine_config`. Actual API surface: parser is the inline
  body of `ControllerConfig_Load<F>` at
  `CoreFrameworks/ControllerConfig.hpp:1798` (single function; no
  extracted KV handler); save is per-field text-splice via
  `cfg_write_field(path, key, value)` at `GUI/SettingsPanel.hpp:472`
  (comment-preserving operator UX; NOT a monolithic `Cfg_Save(FILE*)`).
  Caught by `/readiness` RED #1 (5 missing functions) + `/trace-deps`
  BL-2 (actual API surface identified). Reported in
  `plans/plan_checks/2026-05-14-v5.15.5.F.4b-fresh-audits-synthesis.md`.
  Cold-pickup hostility: fresh session would have lost ~1h re-auditing
  actual API surface before coding could start. Plan amended to
  rewrite Steps 4/5/6 against the real API. **4th detection event
  for Class 14** — pattern remains active; pre-coding mitigation
  via `/readiness` + `/trace-deps` skills working as intended (zero
  production occurrences across all 4 detection events).
- **v5.15.5.F.4c plan body (2026-05-14 — caught at `/precoding-audit-gate`
  Layer-1 orchestrator)**: 6 fictional APIs surfaced again — `Cfg_LoadFromString`,
  `Cfg_Save`, `Cfg_LoadFromFile`, `cfg_field_offset`, `cfg_dispatch_target<KIND>`,
  `template <Kind K> void cfg_parse_field<KIND_X>`. The `.F.4c` plan had an
  authoritative amendment notice at lines 15-66 explicitly invalidating these,
  but the PLAN BODY preserved the stale code samples as "scope intent."
  Caught by `/trace-deps` GAP-B + GAP-D + `/dod-audit` Class 14 detection;
  reported in `plans/plan_checks/2026-05-14-v5.15.5.F.4c-fresh-audits-synthesis.md`.
  **5th detection event for Class 14 + lesson learned:** amendment-notice
  scaffolding is INSUFFICIENT. A fresh-context coder reading top-down might
  copy body samples verbatim before noticing the notice. **Going forward:
  when amending a plan with stale code samples, DELETE the stale body —
  don't preserve-with-notice.** Plan amended at v5.15.5.F.4d planning to
  delete Step 1 entirely ("nothing to do — tt:: covers integers via shipped
  infrastructure") and rewrite Step 6 tests against canonical T1-T6 shape
  at `tests/controller_test.cpp:1548`. Lesson codified in
  `DESIGN_SPECS/audit-methodologies/audit-driven-pre-coding-gate.md` § Lessons + CLAUDE.local.md
  Sprint State Tracker.

**Prevention:**

- **`/trace-deps` skill** (created v5.14): pre-coding audit walks
  every callee + struct-field reference in a plan, runs the
  detection greps above, reports per-callee PASS/GAP. Run BEFORE
  starting any sub-plan's `.A` coding.
- **`/readiness` Check 19** (strengthened v5.14, ship-blocking):
  procedural 6-step grep for plan-to-code references. Catches
  same class via different invocation path.
- **Cross-ship dependency edges**: master plan's Integration Matrix
  lists "Plan B depends on Plan A's deliverable X". `/plan-check`
  verifies the edge.
- **Phase 0 sub-tag pattern**: when a plan needs pre-requisite
  infra that doesn't exist yet, add a `.0` sub-tag at the top
  of the sub-tag table that ships BEFORE `.A`. Example:
  v5.14.4.0 (pre-req) → v5.14.4.A (main). Makes the sequencing
  explicit + prevents stalled coding.
