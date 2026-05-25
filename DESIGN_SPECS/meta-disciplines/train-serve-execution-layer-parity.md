---
name: train-serve-execution-layer-parity
type: meta-discipline
stage: 2-draft
version: 0.1
established: 2026-05-24
first_canonical_target: v5.15.5.F.4d.1.B.4 ship close
description: Audit-methodology M5 — train-serve parity walk at boot + slow-path-cycle layer (distinct from M1 cfg/stamp surface parity)
tags: [audit-methodology, meta-discipline, structural-fix]
surface: [boot-time, slow-path, oms-drainer, ml-inference, backtest]
sister_specs:
  - structural-fix-preferred-decision-framework.md
  - canonical-sister-extension-discipline.md
  - implementation-layer-blindspot-taxonomy.md
  - autopopulate-pattern-for-production-caller-class.md
applies_at_skills:
  - /precoding-audit-gate (extended audit_set; HIGH-RISK ships touching boot or slow-path-cycle)
  - /train-serve-asymmetry-sweep (NEW; parameterized by layer keyword at .B.4)
  - /readiness (NEW Check 40: train-serve mirror verification for boot Init/Bind/Configure calls)
---

# Train-serve execution-layer parity (M5 meta-discipline)

**Stage 2 DRAFT v0.1.** First canonical landing at `v5.15.5.F.4d.1.B.4` ship close (alongside `EngineCommon_BootPerCore` + `EngineCommon_SlowPathCycleOneCore` extract that demonstrates the discipline).

## Why this discipline exists

Codified 2026-05-24 mid-`v5.15.5.F.4d.1.B.3` ship cycle. Pre-coding audit gate fired 6 audits (`/precoding-audit-gate` + `/parity-check` + `/dod-audit` + `/readiness` + `/trace-deps` + `/merge-scan` + `/accounting-audit`) against cfg-derived consumer framework consolidation surface. All returned GREEN-or-YELLOW. ZERO flagged 4 CRIT train-serve execution-layer breaks that an ad-hoc ML↔LIVE structural sweep surfaced:

- PARITY-026 — Live kill_switch dead (no `EventLoopState_ConfigureKillSwitch` call in EngineSharded boot; backtest correctly calls it). 14+ months silent.
- PARITY-027 — Backtest has no ML exit-prediction submit path (entire `MASK_ML_CFG_USE_EXIT_MODEL` dispatch is live-only).
- PARITY-028 — `ConfidenceScorer_BindCompositeCfg` + `RollingTurnover_Init` absent in backtest boot (sister to PARITY-003 closed only on live side).
- PARITY-029 — `Strategy_InitPerCore` never called in backtest (pre-v5.4 F7 bug never closed on backtest mirror).

The audit suite was layer-specific (cfg/stamp/wire-format surface). The gap was layer-coverage, not audit-rigor. The framework consolidation paid off — it gave us audit tools that found these — but the audit cadence missed the boot + slow-path-cycle layer entirely.

## Sister meta-disciplines (cohort)

Per `DOCS/DESIGN_PHILOSOPHY.md § 11.5` meta-discipline registry:

- **M1** sister-registry parity verification (cfg-domain bitmaps; FOREACH_*_FLAG sigs)
- **M2** cross-tool emit-site enumeration (`.sh` / `.py` / `awk` parallel emitters of wire format)
- **M3** anti-pattern codification false-positive surface (distinguishing legitimate-namespacing from drift)
- **M4** implementation-detail blindspot taxonomy (12 categories B1-B13; struct-gen / type-trait / cohort-extension)
- **M5** train-serve EXECUTION-LAYER parity (THIS DOC; boot calls + slow-path-cycle dispatch)

M1/M2/M3 cover cfg/stamp/wire-format surfaces; M4 covers implementation-detail surfaces below cfg/stamp; M5 covers the lifecycle-cycle layer that M1-M4 don't reach.

## Audit walk procedure

When `/train-serve-asymmetry-sweep <layer>` fires (manually invoked or auto-triggered by `/precoding-audit-gate` on HIGH-RISK ships touching boot or slow-path-cycle):

### Per-call-site enumeration (BOOT side)

For every `Init/Bind/Configure(...)` call in `CoreFrameworks/EngineSharded.hpp` (the live boot block, typically lines ~670-1160):

1. `grep` BacktestSharded.hpp for matching call site
2. If matching call: verify args + sequencing identical (or documented divergence rationale)
3. If NO matching call: classify finding shape
   - LIVE-ONLY safety/correctness call (PARITY-026 shape — kill_switch) → CRIT
   - LIVE-ONLY ML-feature dispatch enable (PARITY-028 shape — composite confidence) → CRIT for users of the feature
   - LIVE-ONLY operator-feature (cfg-flag-gated) → severity depends on operator-impact
4. For every `Init/Bind/Configure(...)` call in `Backtest/BacktestSharded.hpp` boot block:
   - Symmetric check: if no matching live call, classify (BACKTEST-ONLY shape — e.g., `bandit_state_prior_path` operator override per PARITY-031/TECH_DEBT-121)

### Per-dispatch enumeration (SLOW-PATH CYCLE side)

For every cohort-gated dispatch in `CoreFrameworks/EngineSharded.hpp` slow-path body (`MASK_ML_CFG_*` BITMAP_IS_SET gate; `state.cores[c].X > threshold` trigger; `OMS_PushExitForSlot`-style submit):

1. `grep` `Backtest/BacktestSharded.hpp` + `CoreFrameworks/ShardedBacktestDriver.hpp` slow-path block for matching dispatch
2. Same classification as boot side

### Cohort detection

After enumeration, look for finding clusters (≥3 train-serve breaks at adjacent surface area). Cluster = strong signal of underlying Class 18 mirror that warrants ARCHITECT response (per [[structural-fix-preferred-decision-framework]] Option D — shared helper extract).

PARITY-026 + PARITY-028 + PARITY-029 were 3 sister mirrors at the same `EngineSharded.hpp:1125-1154` boot surface — strong cohort signal → `EngineCommon_BootPerCore` extract justified.

PARITY-027 + B3 per-core regime + B1 BNB fee were 3 sister mirrors at slow-path-cycle surface → `EngineCommon_SlowPathCycleOneCore` extract justified.

### False-positive surface (M3 sister)

NOT every BACKTEST-ONLY or LIVE-ONLY call is a parity break. Document legitimate exemptions:

- LIVE-ONLY threading primitives (pthread spawn / SPSC ring init) — backtest is single-threaded by design
- LIVE-ONLY Binance WS subscription / DepthRecorder spawn — backtest reads pre-recorded tick file
- BACKTEST-ONLY synthetic data wrapper / replay state — live consumes WS in realtime
- BACKTEST-ONLY operator-explicit override (e.g., `bandit_state_prior_path` for transfer-learning)

Exemptions get documented in the audit report's "Verified NOT-a-bug" section.

## When this discipline applies

Categorical trigger (per [[feedback_categorical_triggers_over_hardcoded_refs]]):

- Any HIGH-RISK ship touching `EngineSharded.hpp` boot block OR slow-path-cycle body
- Any HIGH-RISK ship touching `BacktestSharded.hpp` boot block OR slow-path-cycle body
- Any new `Init/Bind/Configure(...)` call added at boot
- Any new cohort-gated dispatch added at slow-path-cycle

NOT applicable when:
- Pure cfg/stamp/wire-format work (M1/M2 cover this)
- Pure feature-pipeline / scaler work (PARITY axes A-H of `/parity-check` cover this)
- Pure GUI panel work (M5 doesn't reach this — covered by Layer 2 GUI panel parallelism sweep separately)

## NEW skill: `/train-serve-asymmetry-sweep <layer>`

Lands at `.B.4` ship close. Parameterized by layer keyword:
- `execution` — boot calls + slow-path-cycle (the first canonical surface this discipline targets)
- `oms` — OMS / order submission layer (Layer 1 of 6 in the cadence doc)
- `gui` — GUI panel parallelism (Layer 2)
- `boot` — main.cpp / engine_gui / foxml_suite triple-entry parity (Layer 3)
- `logging` — trade log / calibration log / metrics CSV (Layer 4)
- `stamp-cohort` — PRE_CFG / POST_CFG model-state cohort (Layer 5)
- `datastream` — replay parser vs live WS parser (Layer 6)

Each layer-specific firing captures findings per the same shape used by today's execution-layer first canonical at `plan_checks/2026-05-24-train-serve-asymmetry-sweep.md`.

## CI check candidates

Static-assert candidates (deferred to defensive sub-ship; would close discipline at compile time):
- For every `EventLoopState_Configure*` call → matching call must exist in backtest path (compile-time enforceable via X-macro registry of boot-time configure functions)
- For every `MASK_ML_CFG_*` BITMAP_IS_SET in EngineSharded slow-path → matching dispatch site in BacktestSharded (harder; requires AST walk via clang tool)

Python tool candidates (sister to `check_per_core_registry_integrity.py` shape):
- `tools/check_train_serve_mirror_parity.py` — greps for known boot-side calls; verifies matching backtest call exists; reports asymmetries

Decision deferred to `.B.4` ship close planning.

## /readiness Check 40 (NEW)

Lands at `.B.4` ship close. New `/readiness` Check 40:

> **Check 40: train-serve execution-layer parity** — for HIGH-RISK ships touching `EngineSharded.hpp` boot OR slow-path-cycle body, verify any NEW `Init/Bind/Configure(...)` call has matching backtest mirror site at `BacktestSharded.hpp` boot OR documented exemption per train-serve-execution-layer-parity.md § False-positive surface.

## Cross-references

- `~/.claude/projects/.../memory/feedback_train_serve_execution_layer_meta_gap.md` (operator-collaboration rule)
- `~/.claude/projects/.../memory/feedback_iteration_spiral_signals_audit_meta_gap.md` (parent meta-discipline recognition pattern)
- `~/.claude/projects/.../memory/feedback_implementation_detail_blindspot_recovery_via_taxonomy.md` (M4 sister; same shape at implementation-detail layer)
- `DESIGN_SPECS/refactor-patterns/shared-helper-extract-for-train-serve-mirror-close.md` v0.1 (sister pattern; the implementation pattern that closes findings)
- `DESIGN_SPECS/meta-disciplines/structural-fix-preferred-decision-framework.md` (Option D ARCHITECT framework for cluster-finding response)
- `DESIGN_SPECS/meta-disciplines/canonical-sister-extension-discipline.md` (sister-registry inspection at producer side)
- `DOCS/DESIGN_PHILOSOPHY.md § 11.5` (meta-discipline registry; M5 row at `.B.4` ship close)
- `DOCS/RECURRING_BUG_PATTERNS.md` Class 18 (mirror with comment-pinned "Mirrors X" that drifts per-patch)
- `plans/v5.15-live-readiness/plan_checks/2026-05-24-train-serve-asymmetry-sweep.md` (first canonical execution-layer sweep)
- `plans/v5.15-live-readiness/plan_checks/2026-05-24-future-asymmetry-sweep-cadence.md` (6-layer cadence model)
- PARITY-026 / PARITY-027 / PARITY-028 / PARITY-029 / PARITY-030 / PARITY-031 (first canonical findings the discipline catches)
- TECH_DEBT-119 (EngineCommon extract; first canonical implementation closing per the discipline)
