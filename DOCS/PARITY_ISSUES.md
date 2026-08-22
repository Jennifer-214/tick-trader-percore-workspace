# Parity Issues — running ledger

Companion to `RECURRING_BUG_PATTERNS.md`. That file catalogs **classes**
of bugs (taxonomy + detection scripts). This file catalogs **instances**
— specific parity findings + status + fix history.

Future `/parity-check` runs cross-reference this file to avoid
re-flagging known-issues. Update at the end of every parity audit.

---

## Format per entry

```
### PARITY-NNN — short title
- **Found:** ship tag (commit short SHA)
- **Severity:** CRITICAL / HIGH / MEDIUM / LOW
- **Class:** cross-ref to RECURRING_BUG_PATTERNS Class N if applicable
- **Site(s):** file:line where the issue lives
- **Symptom:** what the user / engine sees
- **Root cause:** why it happens
- **Fix path:** specific proposal + which ship tag will close it
- **Status:** see status definitions below
- **Workaround:** what to do until fix lands (if applicable)
```

## Status definitions

- **OPEN** — found, not yet fixed; blocks dependent ships or features
- **OPEN-DEFERRED** — found, deferred to specific future ship by tag
- **FIXED** — found + fixed; commit cited. Close after ONE full
  `/parity-check` run confirms regression-free
- **DOCUMENTED-RISK** — known, accepted as-is, condition documented in
  cfg/code/operator-facing docs
- **NOT-A-BUG** — initially flagged; investigation showed it's safe.
  Keep entry to prevent re-flagging on future audits.

## ID assignment

- Three-digit zero-padded (PARITY-001 onward)
- Never re-use IDs even after FIXED
- IDs are stable references in commit messages, plan docs,
  operator changelog notes

## Cross-references

- Bug classes: `DOCS/RECURRING_BUG_PATTERNS.md` (taxonomy)
- Audit reports: `plans/plan_checks/parity-YYYY-MM-DD-*.md`
- ML-side invariants: `DOCS/CLAUDE_ML_INVARIANTS.md`
- Parity lifecycle: `DOCS/PARITY_LIFECYCLE.md`
- Verification checklist: `DOCS/PARITY_VERIFICATION_CHECKLIST.md`

---

## Issues

### PARITY-001 — clock_gettime in composite confidence path breaks backtest replay-determinism

```yaml
id: PARITY-001
title: clock_gettime in composite confidence path breaks backtest replay-determinism
surface_tags: [slow-path, ml-inference, backtest]
severity: medium
parity_axis: live↔backtest
status: closed
detected_at: v5.14.1.B (2026-05-09)
closed_at: v5.14.1.B.2 (2026-05-09)
related_specs: []
```

- **Found:** v5.14.1.B (commit 38d4607)
- **Severity:** MEDIUM
  - Only manifests when `cfg.confidence_composite_enabled=1`
  - Default is 0 (legacy IC-only path; bytewise-unchanged from pre-v5.14.1)
  - Today's impact: zero
  - Future impact: blocks composite from being used in deterministic
    backtest regression tests (v5.9.2 contract)
- **Class:** v5.9.2 replay-determinism contract violation
  (related to RECURRING_BUG_PATTERNS Class 17 spirit — assumed-OK
  shortcut without grepping the parity contract)
- **Site:** `Strategies/StrategyParameters.hpp:1118` —
  `clock_gettime(CLOCK_MONOTONIC, &ts)` in the composite branch
- **Symptom:** With `composite_enabled=1` in a backtest, two runs of
  the identical tick file produce different `now_us` →
  `RollingFreshness_Compute` returns different freshness values →
  composite scalar differs → sizing path produces different trade
  outcomes → bytewise replay-determinism broken.
- **Root cause:** Backtest path shares the wiring with live (single
  `ML_BuildParameters` call site). Live wants wall-clock; backtest
  needs tick-derived time. The fix needs `now_us` plumbed as a
  parameter from the slow-path caller (which knows live-vs-backtest
  context), not derived inside `ML_BuildParameters`.
- **Fix path:**
  - Add `uint64_t now_us` parameter to `ML_BuildParameters` signature
  - Live caller (`EventLoop_RebuildOneCore`): passes
    `clock_gettime(CLOCK_MONOTONIC)` result
  - Backtest caller (`BacktestSharded_RebuildOneCore`): passes
    `hist_tick.timestamp_us`
  - Composite branch consumes the parameter instead of doing its own
    `clock_gettime`
  - Mark site (PARITY-002) reuses the same parameter
- **Target ship:** v5.14.1.B.1 (paired with PARITY-002 fix) OR v5.14.2
  (if .B.1 stays minimal)
- **Status:** **CLOSED** (FIXED in v5.14.1.B.2; verified by /parity-check rerun 2026-05-09 against HEAD bb5d57e — Section I PASS)
- **Workaround:** N/A (closed)

### PARITY-002 — ConfidenceScorer_UpdateAndMark API exists but production callers still use legacy _Update

```yaml
id: PARITY-002
title: ConfidenceScorer_UpdateAndMark API exists but production callers still use legacy _Update
surface_tags: [ml-inference, oms-drainer, slow-path]
severity: high
parity_axis: train↔serve
status: closed
detected_at: v5.14.1.B (2026-05-09)
closed_at: v5.14.1.B.1 (2026-05-09)
related_specs: [DESIGN_SPECS/framework-patterns/autopopulate-pattern-for-production-caller-class.md]
```

- **Found:** v5.14.1.B (commit 38d4607)
- **Severity:** HIGH
  - With composite_enabled=1 today: `freshness.last_predict_us=0`
    forever → `RollingFreshness_Compute` returns 0 (cold-start
    semantics) → composite returns 0 → ALL trades blocked
  - Composite is currently NON-FUNCTIONAL in production despite cfg
    flag being available
- **Class:** RECURRING_BUG_PATTERNS Class 12 — Wired-but-unexercised
  ML paths
- **Sites:**
  - `CoreFrameworks/ControllerEventLoop.hpp:1284` (production drainer)
  - `CoreFrameworks/PortfolioController.hpp:607` (legacy single_core)
- **Symptom:** Operator flips `confidence_composite_enabled=1` in
  cfg, expects sizing to scale by composite confidence. Instead,
  every position attempt blocks because composite returns 0.
  Looks like a "model is broken" bug to the operator; actual cause
  is missing Mark wiring.
- **Root cause:** Plumbing-incomplete in v5.14.1.B. The
  `ConfidenceScorer_UpdateAndMark` API was added to ConfidenceScore.hpp
  as the intended Mark site, but the existing `_Update` calls at the
  two production sites were not migrated to it.
- **Fix path:**
  - Replace `ConfidenceScorer_Update(...)` with
    `ConfidenceScorer_UpdateAndMark(...)` at both sites
  - Hoist `clock_gettime(CLOCK_REALTIME, &ts)` BEFORE the call site
    (currently computed inside the `if (drift_floor > 0.0)` block at
    :1294); reuse the same `now_us` for both Mark + drift detection
    (CLAUDE.md item 16 merge-scan win — single clock_gettime serves
    two consumers)
  - Once PARITY-001 fixes the clock-source plumbing, swap the
    backtest path to use tick-derived time at the same Mark site
- **Target ship:** v5.14.1.B.1 (hot patch BEFORE v5.14.1.C tests)
- **Status:** **CLOSED** (FIXED in v5.14.1.B.1; verified by /parity-check rerun 2026-05-09 against HEAD bb5d57e — UpdateAndMark wired at ControllerEventLoop:1299 + PortfolioController:623)
- **Workaround:** N/A (closed)

### PARITY-003 — Composite cfg fields not pushed into ConfidenceScorer at boot

```yaml
id: PARITY-003
title: Composite cfg fields not pushed into ConfidenceScorer at boot
surface_tags: [cfg-flow, ml-inference, boot-time]
severity: blocker
parity_axis: train↔serve
status: closed
detected_at: v5.14.1.B (2026-05-09)
closed_at: v5.14.1.B.1 (2026-05-09)
related_specs: [DESIGN_SPECS/framework-patterns/autopopulate-pattern-for-production-caller-class.md]
```

- **Found:** `/parity-check` full audit 2026-05-09 (against v5.14.1.B HEAD 38d4607)
- **Severity:** CRITICAL
  - Manifests when `cfg.confidence_composite_enabled=1`
  - Even with PARITY-002 fixed (Mark wired), composite still misbehaves:
    - cfg.confidence_freshness_tau_secs (3600s default) IGNORED;
      scorer uses cfg.confidence_freshness_tau (300s legacy) at boot
    - cfg.confidence_capacity_target_dollars IGNORED; scorer
      initialized with target=0 (unbounded → capacity=1.0 always)
    - cfg.confidence_capacity_kappa IGNORED
    - cfg.confidence_rmse_baseline IGNORED; scorer hardcodes 1.0
  - Operator sets cfg fields, expects them to take effect, they don't
- **Class:** RECURRING_BUG_PATTERNS Class 12 — Wired-but-unexercised
  ML paths (sister-bug to PARITY-002; same shape: API extended but
  call sites don't fire it)
- **Sites:**
  - 3 boot sites that call plain `ConfidenceScorer_Init(cs, win, tau)`:
    - `CoreFrameworks/EngineSharded.hpp:1244`
    - `CoreFrameworks/ControllerEventLoop.hpp:580`
    - `CoreFrameworks/PortfolioController.hpp:397`
  - `ConfidenceScorer_InitComposite` was added in v5.14.1.A but NOT
    called from any boot site
- **Symptom:** All 4 composite cfg knobs are silently ignored.
  Operator tunes confidence_capacity_target_dollars=1000, runs paper
  test, sees no behavior difference vs target_dollars=10000 — capacity
  always returns 1.0 because scorer was init'd with target=0.
- **Root cause:** v5.14.1.A added InitComposite but didn't wire it
  in; v5.14.1.B added cfg fields + parser but didn't wire boot sites
  to push cfg → scorer. Comment at `StrategyParameters.hpp:1112-1114`
  CLAIMS "Hot-cfg fields are pushed into the scorer at boot
  (EngineSharded_Init)" — that claim is FALSE (no such push exists).
- **Fix path:**
  - Option A (preferred): replace plain `ConfidenceScorer_Init(cs, win, tau)`
    at 3 boot sites with cfg-aware version that reads all 4 composite
    fields from cfg + populates scorer
  - Option B: add a separate `ConfidenceScorer_RebindCfg(cs, cfg)`
    helper that the slow-path or boot calls per-cycle to re-push cfg
    (handles operator hot-edits to cfg via TUI)
  - Update the false comment at StrategyParameters.hpp:1112-1114
- **Target ship:** v5.14.1.B.1 (paired with PARITY-002 fix)
- **Status:** **CLOSED** (FIXED in v5.14.1.B.1; verified by /parity-check rerun 2026-05-09 against HEAD bb5d57e — BindCompositeCfg wired at EngineSharded:1250 + PortfolioController:403)
- **Workaround:** N/A (closed)

### PARITY-004 — Ridge cfg fields (5) not stamp-bound; train↔serve cfg drift undetected

```yaml
id: PARITY-004
title: Ridge cfg fields (5) not stamp-bound; train↔serve cfg drift undetected
surface_tags: [cfg-flow, ml-inference, wire-format, registry]
severity: high
parity_axis: train↔serve
status: closed
detected_at: v5.14.1.B (2026-05-09)
closed_at: v5.14.1.B.3 (2026-05-09)
related_specs: [DESIGN_SPECS/framework-patterns/autopopulate-pattern-for-production-caller-class.md, DESIGN_SPECS/wire-format-patterns/wire-format-byte-preservation-discipline.md, DESIGN_SPECS/framework-patterns/x-macro-registry-with-presence-dispatch.md]
```

- **Found:** `/parity-check` full audit 2026-05-09 (against v5.14.1.B HEAD 38d4607)
- **Severity:** HIGH (when Ridge enabled; MEDIUM today since
  ridge_*=0 default)
- **Class:** v5.9.5b production-caller field-population gap pattern
- **Sites:**
  - Cfg defs: `ControllerConfig.hpp:515-519` (5 fields)
  - Production use: `Strategies/StrategyParameters.hpp:885-930`
    (cfg-gated branch reads all 5 fields)
  - NOT in stamp body: `ML_Headers/ModelInference.hpp:1794-1899`
    (StampInferenceCfgInputs missing these)
- **Symptom:** Operator trains with `cfg.ridge_lambda=0.15`, deploys
  with `cfg.ridge_lambda=0.25` (intentionally or by cfg drift). No
  verifier check fires; predictions silently diverge from training
  distribution. Detection only via paper-test P&L surprise.
- **Root cause:** v5.14.0 added Ridge cfg fields + production wiring
  but didn't extend StampInferenceCfgInputs to bind them. v5.9.2b
  established the 9 inference cfg fields that ARE stamp-bound; Ridge
  joined the codebase post-v5.9.4a, didn't follow the same discipline.
- **Fix path (Surface G pattern):**
  - Extend StampInferenceCfgInputs with 6 new fields:
    `has_ridge_params`, `ridge_within_horizon`, `ridge_across_horizons`,
    `ridge_lambda`, `ridge_cost_penalty`, `ridge_min_ic_floor`
  - Canonical position 24+ (append after has_xgb_train_nthread at :23)
  - Wire `stamp_write_for_model` callsites to populate when ridge_*=1
  - Add verifier: check ridge params vs cfg, increment drift_count +
    WARN on mismatch
- **Target ship:** v5.14.1.B.3 (FOREACH_STAMP_BOUND_CFG X-macro registry)
- **Status:** **CLOSED** (FIXED in v5.14.1.B.3; verified by /parity-check rerun 2026-05-09 against HEAD bb5d57e — Section L production-caller audit PASS)
- **Workaround:** N/A (closed)

### PARITY-005 — Composite confidence cfg fields (5) not stamp-bound; same class as PARITY-004

```yaml
id: PARITY-005
title: Composite confidence cfg fields (5) not stamp-bound; same class as PARITY-004
surface_tags: [cfg-flow, ml-inference, wire-format, registry]
severity: medium
parity_axis: train↔serve
status: closed
detected_at: v5.14.1.B (2026-05-09)
closed_at: v5.14.1.B.3 (2026-05-09)
related_specs: [DESIGN_SPECS/framework-patterns/autopopulate-pattern-for-production-caller-class.md, DESIGN_SPECS/wire-format-patterns/wire-format-byte-preservation-discipline.md, DESIGN_SPECS/framework-patterns/x-macro-registry-with-presence-dispatch.md]
```

- **Found:** `/parity-check` full audit 2026-05-09 (against v5.14.1.B HEAD 38d4607)
- **Severity:** MEDIUM (composite is opt-in; once enabled, cfg
  retuning between train + infer = silent drift)
- **Class:** v5.9.5b production-caller field-population gap pattern
- **Sites:**
  - Cfg defs: `ControllerConfig.hpp:463-467` (5 fields)
  - Production use: `Strategies/StrategyParameters.hpp:1101-1126`
  - NOT in stamp body: same as PARITY-004 (StampInferenceCfgInputs)
- **Symptom:** Operator trains with `cfg.confidence_freshness_tau_secs=3600`
  + `cfg.confidence_rmse_baseline=0.05` (training-time RMSE), deploys
  with different values → composite scalar drifts → sizing differs
  silently.
- **Root cause:** Sister to PARITY-004; v5.14.1.B added cfg fields
  but didn't follow Surface G stamp-binding discipline.
- **Fix path:** Same as PARITY-004 — extend StampInferenceCfgInputs
  with: `has_composite_confidence`, `confidence_composite_enabled`,
  `confidence_freshness_tau_secs`, `confidence_capacity_target_dollars`,
  `confidence_capacity_kappa`, `confidence_rmse_baseline`. Canonical
  position 25+ (after Ridge fields).
- **Target ship:** v5.14.1.B.3 (bundled with PARITY-004 = ONE X-macro registry covers both)
- **Status:** **CLOSED** (FIXED in v5.14.1.B.3; verified by /parity-check rerun 2026-05-09 against HEAD bb5d57e — Section F + Section L PASS)
- **Workaround:** N/A (closed)

### PARITY-006 — Two distinct freshness tau cfg fields with overlapping semantics

```yaml
id: PARITY-006
title: Two distinct freshness tau cfg fields with overlapping semantics
surface_tags: [cfg-flow, ml-inference]
severity: low
parity_axis: train↔serve
status: open
detected_at: v5.14.1.B (2026-05-09)
related_specs: []
```

- **Found:** `/parity-check` full audit 2026-05-09 (against v5.14.1.B HEAD 38d4607)
- **Severity:** LOW (cosmetic / clarity)
- **Class:** N/A (not a parity bug per se; clarity issue)
- **Sites:**
  - Legacy: `ControllerConfig.hpp:580` —
    `cfg.confidence_freshness_tau` (default 300.0 sec; used by
    legacy IC-only `ConfidenceScorer_Compute`)
  - New: `ControllerConfig.hpp:464` —
    `cfg.confidence_freshness_tau_secs` (default 3600.0 sec;
    intended for composite path)
- **Symptom:** Operator confused which field affects which path.
  Reading either field's name, hard to tell whether changing it
  affects legacy or composite or both.
- **Root cause:** v5.14.1.B added a new field instead of reusing
  the existing one. Two different defaults (300s vs 3600s) suggest
  intentional divergence (legacy is short for IC freshness; composite
  is long for outcome-cadence freshness) — but the naming doesn't
  surface this.
- **Fix path:**
  - Add prominent doc comment to both fields explaining dual-tau
    design + which path consumes which
  - Future: rename `confidence_freshness_tau` →
    `confidence_freshness_tau_legacy_secs` (back-compat parser
    accepts both) so the names are obviously distinct
- **Target ship:** v5.15 (cosmetic; defer)
- **Status:** OPEN-DEFERRED (v5.15)
- **Workaround:** Reference this entry when tuning either field.

### PARITY-007 — Ridge cfg fields not documented in cfg.example [NOT-A-BUG]

```yaml
id: PARITY-007
title: Ridge cfg fields not documented in cfg.example
surface_tags: [cfg-flow]
severity: low
parity_axis: train↔serve
status: closed
detected_at: v5.14.1.B (2026-05-09)
closed_at: v5.14.1.B.1 (2026-05-09)
related_specs: []
```

- **Found:** `/parity-check` full audit 2026-05-09 (against v5.14.1.B HEAD 38d4607)
- **Severity:** LOW
- **Status:** **NOT-A-BUG** (false positive)
- **Investigation:** v5.14.0.C already added the Ridge cfg block to
  `engine.cfg.example:186-213` (5 fields with comments + recommended
  values). The audit agent missed this section.
- **Action:** None. Closed without ship.
- **Note:** Verified during v5.14.1.B.1 prep. Verification did surface
  a SEPARATE real gap: composite cfg fields (v5.14.1.B's 5 fields) were
  NOT in cfg.example. Bonus fix landed in v5.14.1.B.1 alongside the
  PARITY-002/003 fixes.

---

## Status update log

### 2026-05-09 /parity-check full audit

- PARITY-001: STATUS unchanged (OPEN; v5.14.1.B.2 plan in flight).
  Confirmed by audit as CRITICAL-2.
- PARITY-002: STATUS unchanged (OPEN; v5.14.1.B.1). Confirmed by audit
  as HIGH-1. Cross-ref `parity-2026-05-08-v5.14.1.B-full.md`.
- PARITY-003: NEW. CRITICAL — composite cfg→scorer wire-up missing
  at 3 boot sites. Pairs with PARITY-002 in v5.14.1.B.1.
- PARITY-004: NEW. HIGH — Ridge cfg not stamp-bound. Defer v5.14.1.B.3
  (bundled with PARITY-005 in single Surface G ship).
- PARITY-005: NEW. MEDIUM — composite cfg not stamp-bound. Defer
  v5.14.1.B.3 (bundle with PARITY-004).
- PARITY-006: NEW. LOW — dual-tau naming clarity. Defer v5.15.
- PARITY-007: NEW → **NOT-A-BUG**. LOW — alleged "Ridge cfg.example
  missing". Audit was incorrect — Ridge block exists at
  `engine.cfg.example:186-213`. Closed without ship.

### 2026-05-09 v5.14.1.B.1 ship — PARITY-002 + PARITY-003 + PARITY-007 closed

- PARITY-002: **FIXED** in v5.14.1.B.1.
  - Wired `ConfidenceScorer_UpdateAndMark` at both production sites:
    - `CoreFrameworks/ControllerEventLoop.hpp:1284` (sharded drainer;
      hoisted `clock_gettime(CLOCK_REALTIME)` to serve both Mark +
      drift detection per CLAUDE.md item 16 merge-scan rule)
    - `CoreFrameworks/PortfolioController.hpp:613-621` (legacy
      single_core path; preserved for parity-test scenarios)
- PARITY-003: **FIXED** in v5.14.1.B.1.
  - Added `ConfidenceScorer_BindCompositeCfg` helper.
  - Wired at 2 of 3 boot sites (3rd intentionally deferred per design).
- PARITY-007: **NOT-A-BUG** confirmed. False positive from audit.
  Closed without ship (no fix needed).
- BONUS fix in v5.14.1.B.1: composite cfg block (5 fields) ADDED to
  `engine.cfg.example` (was a v5.14.1.B oversight; caught during
  PARITY-007 verification).

### 2026-05-09 v5.14.1.B.2 ship — PARITY-001 closed

- PARITY-001: **FIXED** in v5.14.1.B.2.
  - now_us threaded through ML_BuildParameters via Strategy_BuildParameters
    dispatcher.
  - Live: clock_gettime(CLOCK_MONOTONIC) at slow-path entry.
  - Backtest: tick.timestamp_us (deterministic; same CSV → same now_us
    across replays). v5.9.2 replay-determinism contract restored.

### 2026-05-09 v5.14.1.B.3 ship — PARITY-004 + PARITY-005 closed

- PARITY-004 + PARITY-005: **FIXED** in v5.14.1.B.3 (5 sub-tags A-E).
  - Initial 10-param caller-side helper design abandoned per Caramel
    feedback "is this future proof" — pivoted to FOREACH_STAMP_BOUND_CFG
    X-macro registry per CLAUDE.md item 13.
  - New header ML_Headers/StampBoundCfgRegistry.hpp defines the registry;
    auto-generates struct fields, emit, parser, zero-init.
  - Drift check at CoreModelZoo_TryLoadRole; cfg threaded through
    LoadFromDir → EngineSharded boot/hot-swap call sites.
  - Production stamp emit at BacktestEngine RFV populates new fields.
  - Resurrects v5.9.2b's abandoned inference_cfg_drift_count counter
    (partial — covers the 10 X-macro-registered fields; legacy v5.9.2b
    inference_cfg_* fields await v5.15+ migration per CLEANUP-001).

### 2026-05-09 /parity-check rerun (post-B-series) — ALL CLOSED ✓

Verdict: ALL 5 active PARITY findings FIXED and verified regression-free.
Zero new findings across all 12 sections (A-L). Zero compiler warnings.
Determinism contract restored. 10 new cfg fields fully protected.
Field-population audit (Section L) confirms all production callers wired.

Status transitions (FIXED → CLOSED):
- PARITY-001: FIXED → **CLOSED** ✓ (verified bb5d57e)
- PARITY-002: FIXED → **CLOSED** ✓ (verified bb5d57e)
- PARITY-003: FIXED → **CLOSED** ✓ (verified bb5d57e)
- PARITY-004: FIXED → **CLOSED** ✓ (verified bb5d57e)
- PARITY-005: FIXED → **CLOSED** ✓ (verified bb5d57e)
- PARITY-006: OPEN-DEFERRED (v5.15+ unchanged)
- PARITY-007: NOT-A-BUG (unchanged)

Sprint state: **clean ledger. Resume v5.14.1.C coding** (composite
tests — the original next ship interrupted by parity audit cycle).

### 2026-05-09 v5.14.1.E close — PARITY-008 found + FIXED in same audit cycle

PARITY-008 found by /parity-check rerun against HEAD 9a3e08e
(v5.14.1.E close). Production-caller field-population gap (v5.9.5b
class) — exit_blender_mode auto-generated stamp body slot via
FOREACH_STAMP_BOUND_CFG but RFV stamp emit didn't populate
inf.has_exit_blender_mode. Fix: 3-line addition to BacktestEngine.hpp
matching the existing Ridge + composite + winsor populator pattern.

Status: **FIXED** in v5.14.1.E.E (commit 770ea8f). Sweep verified
all 13 X-macro entries now have populators. No sister gaps.

**Recurring class signal (4 instances now):**
- PARITY-002 / PARITY-003 (v5.14.1.B.1): Mark-wiring + cfg→scorer at boot
- PARITY-004 / PARITY-005 (v5.14.1.B.3): Ridge + composite cfg stamp-binding
- PARITY-008 (v5.14.1.E.E): exit_blender_mode stamp-binding

Pattern: every time we add a stamp-bound cfg field via the X-macro
registry, we have to remember to wire the populator at the production
RFV emit site. This is mechanizable — the X-macro could auto-populate.
Skill update + potential X-macro auto-populate refactor queued
(addresses the recurring class systemically).

### 2026-05-27 v5.15.5.F.4d.1.B.4 ship close — PARITY-026/027/028/029/030/031 closed (+ PARITY-032 already closed at WIP-11)

7 PARITY entries closed by-construction at .B.4 via the M5 train-serve-execution-layer-parity Stage 3 first canonical EngineCommon helper extraction:

- **PARITY-026** (kill_switch dispatch missing in LIVE) — closed at WIP-9 via EngineCommon_BootGlobal containing EventLoopState_ConfigureKillSwitch (gated on MASK_RISK_CFG_KILL_SWITCH_ENABLED); invoked from BOTH LIVE (EngineSharded.hpp:749) + BACKTEST (BacktestSharded.hpp:206) by shared helper
- **PARITY-027** (exit-model dispatch missing in BACKTEST) — closed at WIP-13 via EngineCommon_SlowPathCycleOneCore body containing exit-model dispatch (gated on MASK_ML_CFG_USE_EXIT_MODEL)
- **PARITY-028** (ConfidenceScorer + RollingTurnover init missing in BACKTEST) — closed at WIP-9 via EngineCommon_BootPerCore body containing both ConfidenceScorer_BindCompositeCfg + RollingTurnover_Init
- **PARITY-029** (Strategy_InitPerCore missing in BACKTEST; pre-v5.4 F7 bug alive on backtest) — closed at WIP-9 via EngineCommon_BootPerCore body containing tt::Strategy_InitPerCore OUTSIDE ML branch
- **PARITY-030** (BNB fee discount LIVE-only; 33% backtest fee inflation) — closed at WIP-9 via EngineCommon_ApplyBnbDiscount extracted as non-const cfg one-shot mutator invoked from BOTH LIVE + BACKTEST
- **PARITY-031** (BACKTEST collapses N per-core regime states to 1) — closed at WIP-15 via BACKTEST_REGIME_SAMPLE_CORE named constant preserving pre-.B.4 sample_regimes=0 semantic + 4th consumer added at BacktestSharded.hpp:430
- **PARITY-032** (BREAKEVEN_ON_PROFIT dispatch missing in BACKTEST; already closed at WIP-11) — closed at WIP-11 via EngineCommon_SlowPathCycleOneCore body containing D1-B FOREACH_SLOW_PATH_GATE BREAKEVEN_ON_PROFIT cached-gate dispatch

Tests preserved: **3215 passed / 0 failed** post-ship.

Status: **closed** (per status definitions § 27: code-shipped). Strict **CLOSED + regression-free** requires one full `/parity-check` regression-free run; queued post-paper-test session.

Ledger update lag: entries 026-031 were structurally closed at WIPs 9-15 (2026-05-26 to 2026-05-27) but ledger status fields remained `open` until post-ship-audit Stage 8 caught the gap on 2026-05-27. Root cause: close-session ritual didn't include explicit PARITY ledger update step. Remediation: `/post-ship-audit` integration with `/parity-check` mechanical verification + ledger auto-update will be queued for sister mini-ship per `feedback_structural_enforcement_when_memory_insufficient` (M7) — close-session Stage 8 ledger sync to be Stage 6 of structural enforcement at close-session SKILL spec.



```yaml
id: PARITY-008
title: exit_blender_mode not populated in RFV stamp emit
surface_tags: [wire-format, ml-inference, backtest, registry]
severity: blocker
parity_axis: train↔serve
status: closed
detected_at: v5.14.1.E (2026-05-09)
closed_at: v5.14.1.E.E (2026-05-09)
related_specs: [DESIGN_SPECS/framework-patterns/autopopulate-pattern-for-production-caller-class.md, DESIGN_SPECS/wire-format-patterns/wire-format-byte-preservation-discipline.md]
```

- **Found:** /parity-check 2026-05-09 (v5.14.1.E close, HEAD 9a3e08e)
- **Severity:** CRITICAL (silent drift when operator opts in to feature)
- **Class:** v5.9.5b production-caller field-population gap (4th recurrence)
- **Site:** `Backtest/BacktestEngine.hpp:1289+` (RFV stamp emit block)
- **Symptom:** Operator changes cfg.exit_blender_mode between training
  and deployment; stamp lacks the field; verifier skips drift check;
  exit predictions diverge silently.
- **Root cause:** v5.14.1.E.A added exit_blender_mode to X-macro
  registry but didn't update RFV stamp emit (pattern established in
  v5.14.1.B.3.D for Ridge/composite + v5.14.1.D.C for winsor).
- **Fix path:** Added 3-line gating block matching existing populators.
- **Target ship:** v5.14.1.E.E (10 min hotfix)
- **Status:** **CLOSED** (FIXED in v5.14.1.E.E commit 770ea8f;
  verified by sweep of all 13 X-macro entries; no sister gaps)
- **Workaround:** N/A (closed)

Status transitions:
- PARITY-001: CLOSED (unchanged)
- PARITY-002: CLOSED (unchanged)
- PARITY-003: CLOSED (unchanged)
- PARITY-004: CLOSED (unchanged)
- PARITY-005: CLOSED (unchanged)
- PARITY-006: OPEN-DEFERRED v5.15+ (unchanged)
- PARITY-007: NOT-A-BUG (unchanged)
- PARITY-008: NEW → **FIXED** in same audit cycle

Sprint state: **clean ledger again.** All 8 active PARITY findings
either CLOSED (5), FIXED-pending-rerun-confirmation (1: PARITY-008),
OPEN-DEFERRED (1), or NOT-A-BUG (1). Ready for v5.14.2 audit cycle
+ /plan-check downstream re-audit.

---

### PARITY-009 — Ensemble hot-swap (v5.14.2) bypasses 6 post-load setup steps that boot does

```yaml
id: PARITY-009
title: Ensemble hot-swap (v5.14.2) bypasses 6 post-load setup steps that boot does
surface_tags: [boot-time, ml-inference, cfg-flow, slow-path]
severity: high
parity_axis: train↔serve
status: closed
detected_at: v5.14.2 (2026-05-09)
related_specs: [DESIGN_SPECS/framework-patterns/postloadsetup-registry-pattern.md, DESIGN_SPECS/framework-patterns/autopopulate-pattern-for-production-caller-class.md]
```

- **Found:** 2026-05-09 by post-coding /parity-check + /merge-scan +
  manual enumeration of post-`.B.6` `EngineSharded/Run.hpp` boot section (pre-`.B.6` was `EngineSharded.hpp:1075-1240`) boot block vs
  `CoreFrameworks/EnsembleHotSwap.hpp:54-115` hot-swap helper.
- **Severity:** **HIGH composite** — sub-gap F is CRITICAL on its own
  (bypasses inference_cfg drift detection that PARITY-002/003/004/005
  closed); other sub-gaps are MEDIUM (operator-config silently lost on swap).
- **Class:** Class 18 (mirror data-flow incomplete); same shape as the
  v5.9.5b production-caller field-population class but at the function-
  composition level instead of the field-population level.
- **Sites:**
  - Boot reference: post-`.B.6` `CoreFrameworks/EngineSharded/Run.hpp` boot section (pre-`.B.6` was `EngineSharded.hpp:1157-1240`)
  - Backtest reference: `Backtest/BacktestSharded.hpp:316-359`
  - Hot-swap (NEW v5.14.2): `CoreFrameworks/EnsembleHotSwap.hpp:54-115`

**Sub-gaps:**

| ID | Step | Boot does | Hot-swap does | Severity | Operator impact |
|---|---|---|---|---|---|
| .A | `held_out_stamp_secret` | passes `cfg.held_out_stamp_secret` | hardcodes `nullptr` | MEDIUM | Custom-secret deploys: stamp HMAC verify silently disabled on hot-swap |
| .B | `gap_threshold` | passes `FPN_ToDouble(cfg.gap_acceptable_threshold)` | hardcodes `0.05` | MEDIUM | Non-default gap tolerance silently reverted on hot-swap |
| .C | `blend_mode` strncpy + clamp | reads `cfg.core_ensemble_blend_mode[i]` OR `cfg.ensemble_blend_mode` | not done | MEDIUM | Operator's per-core blend mode override silently lost |
| .D | `SetDisabledHorizons(zoo, csv)` | passes `cfg.core_disabled_horizons[i]` | not done | MEDIUM | Operator's disabled horizon CSV silently re-enabled |
| .E | `SetBanditSaveInterval(zoo, n)` | passes `cfg.ensemble_bandit_save_interval` | not done | LOW | Bandit save cadence reverts to defaults |
| .F | `CoreModelZoo_ValidateAgainstCfg(zoo, ezoo, cfg, ...)` | called at line 1229 | not done | **CRITICAL** | Bypasses all inference_cfg drift checks closed by PARITY-002/003/004/005; Ridge/composite/winsor cfg drift goes undetected for hot-swapped models |

- **Symptom:** Operator hot-swaps a model dir; engine continues with
  silently-altered behavior:
  - Ridge cfg drift not detected (sub-gap .F)
  - Composite confidence cfg drift not detected (sub-gap .F)
  - Winsor cfg drift not detected (sub-gap .F)
  - Per-core blend mode reverts to global default (sub-gap .C)
  - Disabled horizons silently re-enabled (sub-gap .D)
  - Bandit save interval reverts (sub-gap .E)
  - Custom HMAC secret + custom gap threshold ignored (sub-gaps .A/.B)
- **Root cause:** v5.14.2 plan said "mirror existing zoo init for swap-zoo"
  but the mirror enumerated only the model-load-and-bandit-init subset;
  missed the per-core-cfg-application + post-load-validation subset.
  Same Class 18 shape that /trace-deps Step 6 was added to prevent —
  the audit dispatched pre-coding ran Step 6 but didn't enumerate the
  full boot post-load sequence.
- **Fix path:** v5.14.2.E **Extract `EnsembleModelZoo_PostLoadSetup<F>(ezoo, cfg, core_id, base_dir)` helper** containing all 8 steps. Both boot AND hot-swap call it. Closes all 6 sub-gaps structurally + makes future post-load steps impossible to forget. Boundary-stable refactor (callers' API contracts unchanged; only the storage location of the setup logic moves).
- **Target ship:** v5.14.2.E (planned same-session ship; ~80 LOC factor + ~5 LOC at 3 call sites)
- **Status:** **OPEN** (fix in flight)
- **Workaround:** Avoid hot-swap until v5.14.2.E ships — restart engine to apply new model dir if any of the affected operator settings differ between current + new model

---

### PARITY-010 — Backtest ensemble init missing v5.13.4 exit-bandit setup

```yaml
id: PARITY-010
title: Backtest ensemble init missing v5.13.4 exit-bandit setup
surface_tags: [backtest, ml-inference, boot-time]
severity: medium
parity_axis: live↔backtest
status: closed
detected_at: v5.14.2 (2026-05-09)
related_specs: [DESIGN_SPECS/framework-patterns/postloadsetup-registry-pattern.md]
```

- **Found:** 2026-05-09 (during PARITY-009 enumeration sweep across
  boot / backtest / hot-swap surfaces).
- **Severity:** MEDIUM (pre-existing v5.13.4 follow-on gap; not introduced
  by v5.14.2).
- **Class:** Class 18 (mirror data-flow incomplete).
- **Sites:**
  - Backtest: `Backtest/BacktestSharded.hpp:316-359` (missing 2 calls)
  - Boot reference: post-`.B.6` `CoreFrameworks/EngineSharded/Run.hpp` boot section — InitExitBandits + LoadExitBanditState calls (pre-`.B.6` was `EngineSharded.hpp:1180` + `:1200`)

**Sub-gaps:**

| Step | Boot does | Backtest does |
|---|---|---|
| `EnsembleModelZoo_InitExitBandits` | yes (line 1180) | NO |
| `EnsembleModelZoo_LoadExitBanditState` | yes (line 1200) | NO |

- **Symptom:** Backtest replay of paper-traded data produces different
  exit-bandit weights than live engine produced for same data. Train↔
  serve parity violation: backtest bandits stay uniform; live bandits
  evolve. Detected by replay-determinism regression test if it exercised
  exit bandits (currently focused on entry side).
- **Root cause:** v5.13.4 added exit-bandit infrastructure to live engine
  boot; the parallel BacktestSharded boot was overlooked. Same shape as
  the recurring "added to one path, forgotten in the other" class
  (Class 18 mirror).
- **Fix path:** Same as PARITY-009 — extract `EnsembleModelZoo_PostLoadSetup`
  helper, call from both boot AND backtest AND hot-swap. Closes
  PARITY-009 + PARITY-010 in one structural fix.
- **Target ship:** v5.14.2.E (bundled with PARITY-009 closure)
- **Status:** **OPEN** (fix in flight, bundled with PARITY-009)
- **Workaround:** Don't trust backtest replay-determinism for exit-bandit
  attribution until v5.14.2.E ships

---

### PARITY-011 — Single-zoo hot-swap missing VerifyExpected (Class 18 sister of PARITY-009)

```yaml
id: PARITY-011
title: Single-zoo hot-swap missing VerifyExpected (Class 18 sister of PARITY-009)
surface_tags: [boot-time, ml-inference, cfg-flow]
severity: medium
parity_axis: train↔serve
status: closed
detected_at: v5.14.2 (2026-05-09)
related_specs: [DESIGN_SPECS/framework-patterns/postloadsetup-registry-pattern.md]
```

- **Found:** 2026-05-09 during PARITY-009 enumeration sweep across boot / backtest / hot-swap surfaces.
- **Severity:** MEDIUM (silent train-serve drift; subset of VerifyExpected's checks already covered by ValidateAgainstCfg, but unique checks like cadence + feature_format + num_classes are bypassed)
- **Class:** Class 18 (mirror data-flow incomplete; same shape as PARITY-009).
- **Sites:**
  - Boot reference (single-zoo): post-`.B.6` `CoreFrameworks/EngineSharded/Run.hpp` boot section — calls VerifyExpected (pre-`.B.6` was `EngineSharded.hpp:1108-1131` with VerifyExpected at `:1114`)
  - Hot-swap (single-zoo, v5.10.0c): `CoreFrameworks/EngineSharded.hpp:~2796-2820` (calls Free + Init + LoadFromDir + ValidateAgainstCfg, but NOT VerifyExpected)

**What's missing:** `CoreModelZoo_VerifyExpected(zoo, dir, ...)` — checks expected.cfg sidecar for:
- `barrier_gate_enabled` (subset of stamp-bound; partially covered by ValidateAgainstCfg)
- `ml_buy_threshold` (NOT stamp-bound; unique to VerifyExpected)
- `expected_num_classes` (architectural; not stamp-bound; unique to VerifyExpected)
- `expected_role` (architectural; not stamp-bound; unique to VerifyExpected)
- `held_out_fraction` (stamp-bound; covered by ValidateAgainstCfg)
- `gap_acceptable_threshold` (NOT stamp-bound; unique to VerifyExpected)
- `expected_poll_interval` (stamp-bound as `training_poll_interval`; covered by ValidateAgainstCfg)
- `expected_feature_format_version` (build constant; not stamp-bound; unique to VerifyExpected)
- `expected_num_features` (build constant; not stamp-bound; unique to VerifyExpected)

5 of 9 checks are unique to VerifyExpected; bypassing it on hot-swap silently loses those checks for hot-swapped models.

- **Symptom:** Operator hot-swaps a model dir; if the new model has different `ml_buy_threshold`, `expected_num_classes`, `expected_role`, `gap_acceptable_threshold`, or build-constants, the divergence is silently accepted. ValidateAgainstCfg catches some (barrier_gate, held_out_fraction, poll_interval) but not all.
- **Root cause:** v5.10.0c hot-swap added (single-zoo path) only called ValidateAgainstCfg; VerifyExpected was overlooked. Class 18 — mirror missed checks.
- **Fix path:** v5.14.2.E.1 — `CoreModelZoo_PostLoadSetup` helper containing both VerifyExpected + ValidateAgainstCfg. Boot + backtest + hot-swap all call it.
- **Target ship:** v5.14.2.E.1 (bundled with PARITY-009/010/012 closure)
- **Status:** **OPEN** (fix in flight)
- **Workaround:** Avoid hot-swap until v5.14.2.E.1 ships if the new model differs in unique-VerifyExpected fields

---

### PARITY-012 — Backtest single-zoo missing ValidateAgainstCfg (Class 18 sister of PARITY-009/010/011)

```yaml
id: PARITY-012
title: Backtest single-zoo missing ValidateAgainstCfg (Class 18 sister of PARITY-009/010/011)
surface_tags: [backtest, cfg-flow, ml-inference]
severity: medium
parity_axis: live↔backtest
status: closed
detected_at: v5.14.2 (2026-05-09)
related_specs: [DESIGN_SPECS/framework-patterns/postloadsetup-registry-pattern.md]
```

- **Found:** 2026-05-09 during PARITY-009 enumeration sweep.
- **Severity:** MEDIUM (backtest replay-determinism: inference_cfg drift not detected during backtest validation)
- **Class:** Class 18 (mirror data-flow incomplete).
- **Sites:**
  - Boot reference (single-zoo): post-`.B.6` `CoreFrameworks/EngineSharded/Run.hpp` boot section — calls ValidateAgainstCfg (pre-`.B.6` was `EngineSharded.hpp:1229`)
  - Backtest (single-zoo): `Backtest/BacktestSharded.hpp:294` (calls VerifyExpected only; missing ValidateAgainstCfg)

**What's missing:** `CoreModelZoo_ValidateAgainstCfg(zoo, ezoo, cfg, ...)` — checks 13 stamp-bound cfg fields (Ridge ×5 + composite ×5 + winsor ×2 + exit_blender ×1) for inference_cfg drift between training-time stamp body and serving-time live cfg.

- **Symptom:** Backtest validation skips inference_cfg drift detection. If operator changes Ridge / composite / winsor / exit_blender cfg fields between training and backtest replay, the divergence is silently accepted. Backtest may produce results that don't match what live engine would have produced under the same cfg, breaking the train-serve parity claim.
- **Root cause:** v5.10.2.A added ValidateAgainstCfg to live boot but not to backtest boot. Class 18 — added to one path, missed at parallel path.
- **Fix path:** v5.14.2.E.1 — `CoreModelZoo_PostLoadSetup` helper containing both VerifyExpected + ValidateAgainstCfg. Boot + backtest + hot-swap all call it. PARITY-012 closes automatically when backtest calls the helper.
- **Target ship:** v5.14.2.E.1 (bundled with PARITY-009/010/011 closure)
- **Status:** **OPEN** (fix in flight)
- **Workaround:** Don't trust backtest replay-determinism for cfg-drift validation until v5.14.2.E.1 ships

### PARITY-013 — `cfg.bandit_algorithm` not stamp-bound; train↔serve algorithm drift undetected

```yaml
id: PARITY-013
title: cfg.bandit_algorithm not stamp-bound; train↔serve algorithm drift undetected
surface_tags: [cfg-flow, ml-inference, wire-format, registry]
severity: high
parity_axis: train↔serve
status: closed
detected_at: v5.14.10 (2026-05-10)
related_specs: [DESIGN_SPECS/framework-patterns/autopopulate-pattern-for-production-caller-class.md, DESIGN_SPECS/framework-patterns/x-macro-registry-with-presence-dispatch.md]
```

- **Found:** 2026-05-10 during v5.14.10 Thompson bandit pre-coding parity audit (no commit yet — plan-stage finding)
- **Severity:** HIGH
  - Inference-affecting: enum directly governs whether ML_BuildParameters dispatches Bandit_GetProbabilities (Exp3, blended weights) or Thompson_Sample (one-hot weights at chosen arm), or both for telemetry
  - Default cfg=0 (Exp3) preserves pre-v5.14.10 behavior; the drift surface only arms once operator switches to cfg=1 or cfg=2
  - Same shape as PARITY-004 (Ridge cfg) and PARITY-005 (composite cfg) which were both HIGH
- **Class:** v5.14.1.B inference-cfg-drift class (PARITY-004/005 sister); structural fix preferred via FOREACH_STAMP_BOUND_CFG (CLAUDE.md item 19)
- **Site(s):**
  - Plan declaration: `plans/v5.14-foxml-port-and-maker/subplans/2026-05-08-v5.14.10-bayesian-thompson-bandit.md:161` (`cfg.bandit_algorithm` declared without stamp binding)
  - Direct precedent (analogous enum): `cfg.exit_blender_mode` at `CoreFrameworks/ControllerConfig.hpp:1104` IS stamp-bound at `ML_Headers/StampBoundCfgRegistry.hpp:137-138`
  - Sister Thompson hyperparams (`thompson_mu_prior`, `thompson_precision_prior`, `thompson_precision_obs`) also affect bandit-selection trajectory under cfg=1/2; same drift class
- **Symptom:** Operator trains a model under `cfg.bandit_algorithm=0` (Exp3 default), edits engine.cfg to set cfg=1, restarts. No stamp warning fires (because cfg.bandit_algorithm not in FOREACH_STAMP_BOUND_CFG). Live engine quietly switches to Thompson sampling. weights_buf[] is now one-hot (vs Exp3 blend). Strategy dispatcher consumes different weights → different arm chosen → different fills → P&L diverges silently from training-time projections.
- **Root cause:** Plan introduces 1 enum + 4 hyperparam cfg fields (bandit_algorithm + thompson_mu_prior + thompson_precision_prior + thompson_precision_obs + thompson_rng_seed) without stamp-binding the inference-affecting subset. Plan Step 5 doesn't list FOREACH_STAMP_BOUND_CFG additions. (Same gap class as v5.14.1.B.3 closed for Ridge/composite.)
- **Fix path:** v5.14.10.B amendment — add 4 X-rows to FOREACH_STAMP_BOUND_CFG in `ML_Headers/StampBoundCfgRegistry.hpp` (matches `exit_blender_mode` + `ridge_*` shape):
  - X(bandit_algorithm, int, "%d", 0, cfg.bandit_algorithm, (cfg.bandit_algorithm != 0), DIRECT_FIELD)
  - X(thompson_mu_prior, double, "%.17g", 0.0, FPN_ToDouble(cfg.thompson_mu_prior), (cfg.bandit_algorithm != 0), DIRECT_FIELD)
  - X(thompson_precision_prior, double, "%.17g", 0.0, FPN_ToDouble(cfg.thompson_precision_prior), (cfg.bandit_algorithm != 0), DIRECT_FIELD)
  - X(thompson_precision_obs, double, "%.17g", 0.0, FPN_ToDouble(cfg.thompson_precision_obs), (cfg.bandit_algorithm != 0), DIRECT_FIELD)
  - thompson_rng_seed intentionally EXCLUDED (operator should re-seed exploration without invalidating stamp; document the exclusion)
  - STAMP_CFG_AUTOPOPULATE auto-flows per CLAUDE.md item 21; legacy stamps load with has_*=0 per Surface G
- **Target ship:** v5.14.10.B (bundled with cfg field declarations; ~20 min code increment vs original plan)
- **Status:** **OPEN** (plan-stage; pre-coding amendment recommended)
- **Workaround:** Don't switch cfg.bandit_algorithm between training and serving until stamp binding lands

### PARITY-014 — Thompson replay-determinism contract under-specified; std::normal_distribution non-portable

```yaml
id: PARITY-014
title: Thompson replay-determinism contract under-specified; std::normal_distribution non-portable
surface_tags: [ml-inference, backtest, test-infrastructure]
severity: high
parity_axis: live↔backtest
status: closed
detected_at: v5.14.10 (2026-05-10)
related_specs: [DESIGN_SPECS/wire-format-patterns/prng-choice-for-replay-determinism.md, DESIGN_SPECS/wire-format-patterns/avx512-byte-determinism-pattern.md]
```

- **Found:** 2026-05-10 during v5.14.10 Thompson bandit pre-coding parity audit (no commit yet — plan-stage finding)
- **Severity:** HIGH
  - Plan claims (line 199): "Bytewise-deterministic across runs"
  - True for same-binary same-stdlib deployments
  - FALSE across libstdc++ minor-version bumps OR cross-vendor (libc++) deployments
  - v5.9.2 replay-determinism contract is at risk for any backtest replayed on a different machine / build
  - Today's impact: zero (Thompson code doesn't exist yet). Future impact: blocks Thompson from being used in cross-binary deterministic regression tests
- **Class:** v5.9.2 replay-determinism contract violation (related to PARITY-001 spirit — assumed-OK shortcut without grepping the parity contract)
- **Site(s):**
  - Plan struct: `plans/v5.14-foxml-port-and-maker/subplans/2026-05-08-v5.14.10-bayesian-thompson-bandit.md:94` (`uint64_t rng_state`)
  - Plan REUSE list: lines 26-28 ("std::mt19937_64" + "std::normal_distribution"); codebase has zero existing <random> consumers (confirmed by grep against HEAD)
  - Plan Step 1 sample-fn body: line 99 ("Uses Box-Muller for std::normal_distribution alternative")
- **Symptom:** Operator runs replay backtest on dev box (libstdc++-13). Records 1000 ticks of Thompson samples to a CSV. Operator deploys binary to prod (libstdc++-12 or different vendor). Same cfg.thompson_rng_seed=42 + same reward sequence → libc++ runtime computes a different normal sample at step N → divergence point inflates → backtest CSV ≠ live decisions. Backtest replay-determinism contract silently broken.
- **Root cause:** `std::normal_distribution` is implementation-defined per C++ standard. libstdc++ uses Marsaglia polar method (with internal `_M_saved` state); libc++ uses different algorithm. Even within libstdc++, saved-second-draw state can differ across versions. Only `std::mt19937_64::operator()` raw 64-bit output is standardized (§29.6.5.2).
- **Fix path:** v5.14.10.A amendment — own the math directly:
  - ThompsonBanditState stores ONLY uint64_t rng_state (live mt19937_64 internal state, advanced per draw)
  - NO std::normal_distribution member; implement Box-Muller (or Ziggurat) directly using std::mt19937_64::operator()() raw 64-bit output
  - Convert raw uint64 → (0,1) double via deterministic uniform conversion (NOT std::generate_canonical — also implementation-defined)
  - Apply Box-Muller cos transform: z = sqrt(-2 ln u1) * cos(2π u2). Math uses std::log + std::sqrt + std::cos (IEEE-754 deterministic per CLAUDE.md FPN/double determinism discipline)
  - Add snapshot test (CLAUDE.md item 15): fixed seed 42, draw 1000 samples vs 2-arm posterior, compute SHA-256 of sample-trace, lock the hash. Future stdlib-version drift trips the test immediately.
- **Target ship:** v5.14.10.A (struct + math kernel; ~30 min direct Box-Muller + 30 min snapshot test)
- **Status:** **OPEN** (plan-stage; pre-coding amendment recommended)
- **Workaround:** N/A — this needs to be designed correctly before code lands

### PARITY-015 — Thompson display↔execution invariant breach: no PerCoreSnap/panel surface

```yaml
id: PARITY-015
title: Thompson display↔execution invariant breach; no PerCoreSnap/panel surface
surface_tags: [gui-thread, ml-inference, wire-format]
severity: medium
parity_axis: train↔serve
status: closed
detected_at: v5.14.10 (2026-05-10)
related_specs: [DESIGN_SPECS/framework-patterns/display-execution-invariant-registry-pattern.md, DESIGN_SPECS/framework-patterns/calibration-log-column-registry.md]
```

- **Found:** 2026-05-10 during v5.14.10 Thompson bandit pre-coding parity audit (no commit yet — plan-stage finding)
- **Severity:** MEDIUM
  - CLAUDE.md item 12 invariant: every term in BG/SG_Evaluate (and in this case, ML_BuildParameters dispatch — slow-path predicate) must have a corresponding GUI surface
  - Current Exp3 path has `ensemble_bandit_arm_probs` + `ensemble_n_updates_per_regime` snapshot fields populated at `CoreFrameworks/ShardedSnapshot.hpp:677-694` (audit-corrected post-`.B.6`; original cite of `EngineSharded.hpp:646-694` was already audit-flagged stale — actual snapshot publish writer lives in ShardedSnapshot.hpp)
  - Plan adds parallel ThompsonBanditState; proposes ZERO snapshot fields + ZERO ML Status panel branches → operator can't inspect Thompson posterior state
- **Class:** Display↔execution invariant breach (v5.6.0 pattern); Class 18 sister (asymmetric snapshot coverage between Exp3 and Thompson)
- **Site(s):**
  - Plan: `plans/v5.14-foxml-port-and-maker/subplans/2026-05-08-v5.14.10-bayesian-thompson-bandit.md` (entire file: zero "snapshot" / "panel" / "GUI" mentions per `grep -c`)
  - Snapshot publish reference: `CoreFrameworks/ShardedSnapshot.hpp:677-694` (audit-corrected post-`.B.6`; original cite of `EngineSharded.hpp:646-694` was already audit-flagged stale — actual snapshot publish writer lives in ShardedSnapshot.hpp) (where `ensemble_bandit_arm_probs[r]` is populated for Exp3; needs parallel Thompson section)
  - Snapshot struct: `CoreFrameworks/ShardedSnapshot.hpp` (search `ensemble_bandit_arm_probs` for parallel additions)
  - ML_BuildParameters dispatch (the new "term"): `Strategies/StrategyParameters.hpp:887-1005`
- **Symptom:** Operator paper-tests Thompson sampling, sees flat P&L, has NO panel surface to ask "is Thompson posterior actually diverging from uniform priors? Is mu_post moving? Are pulls evenly distributed across arms?" Must shell into the binary, dump bandit state via stderr fprintf. Worse: operator can't see which algorithm path is currently active without re-reading cfg (no "Bandit Algorithm: Exp3 / Thompson / Both" indicator). Same telemetry need that drove `ensemble_bandit_arm_probs` for the Exp3 path.
- **Root cause:** Plan focuses on math + persistence; skips snapshot/panel propagation. Cfg=2 dual-mode telemetry mentioned at line 144 ("uses calibration log v5.13.0.B with new columns") but specifics not designed.
- **Fix path:** v5.14.10.B amendment — add Step 7 "Snapshot + ML Status panel surface":
  - Snapshot fields: `thompson_bandit_active` (uint8); `thompson_bandit_chosen_arm[NUM_REGIMES]` (int8); `thompson_bandit_total_pulls_per_regime[NUM_REGIMES][N_ARMS]` (uint32); `thompson_bandit_mu_post_per_regime[NUM_REGIMES][N_ARMS]` (float)
  - Populator extends post-`.B.6` `CoreFrameworks/ShardedSnapshot.hpp:677-694` ensemble snapshot section (audit-corrected; pre-`.B.6` cite was `EngineSharded.hpp:646-694` — stale path)
  - ML Status panel: new "Bandit Algorithm: Exp3 | Thompson | Both" row; new per-regime per-arm table (mu_post, precision_post, total_pulls) when Thompson active
  - Cfg=2 telemetry: per-fill calibration log gains `exp3_chosen_arm_idx` + `thompson_chosen_arm_idx` columns
- **Target ship:** v5.14.10.B (~60 min snapshot field + populator + panel branch + cfg=2 telemetry log columns)
- **Status:** **OPEN** (plan-stage; pre-coding amendment recommended)
- **Workaround:** Inspect bandit state via stderr dumps until panel surface lands

### PARITY-016 — v5.14.11 Welford↔batch BuildCorr tolerance-vs-bytewise contract mismatch breaks replay-determinism under cfg.ridge_online_corr=1

```yaml
id: PARITY-016
title: v5.14.11 Welford↔batch BuildCorr tolerance-vs-bytewise contract mismatch breaks replay-determinism under cfg.ridge_online_corr=1
surface_tags: [ml-inference, backtest, slow-path]
severity: high
parity_axis: live↔backtest
status: closed
detected_at: v5.14.11 (2026-05-11)
related_specs: [DESIGN_SPECS/wire-format-patterns/avx512-byte-determinism-pattern.md]
```

- **Found:** 2026-05-11 during v5.14.11 online-corr-update pre-coding parity audit (no commit yet — plan-stage finding)
- **Severity:** HIGH
  - Plan Step 5 line 168 specifies "1e-9 tolerance" between Welford-incremental and batch BuildCorr — correct for ML-quality contract but FALSE for v5.9.2 replay-determinism contract
  - Plan Step 5 line 175-176 separately claims "cfg=0: bytewise-identical to v5.14.0" — only true for cfg=0; cfg=1 silently drifts within tolerance
  - Cross-cfg replay (cfg=0 vs cfg=1) produces tolerance-equivalent but bit-different `corr_matrix` → bit-different Cholesky output → bit-different ridge weights → bit-different FPN weights → backtest replay-determinism contract broken under cfg=1
  - Today's impact: zero (cfg=1 doesn't exist yet). Future impact: blocks cfg=1 from being used in v5.9.2 bytewise replay regression tests
- **Class:** v5.9.2 replay-determinism contract violation (PARITY-001 / PARITY-014 sister — assumed-OK tolerance shortcut without grepping the parity contract)
- **Site(s):**
  - Plan declaration: `plans/v5.14-foxml-port-and-maker/subplans/2026-05-08-v5.14.11-online-corr-update.md:168` (tolerance claim) + `:175-176` (cfg=0 bytewise claim)
  - Existing replay-determinism contract: `tests/controller_test.cpp:19506-19526` (FracDiff bytewise identity) + `:3495-3504` (composite confidence bytewise identity)
  - Target function: `RidgeBlender_BuildCorr` at `ML_Headers/RidgeBlender.hpp:287-368` (the batch reference)
  - Target wiring (two sites): `Strategies/StrategyParameters.hpp:996` (buy-side) + `:1195` (exit-side)
- **Symptom:** Operator runs replay backtest on dev box under cfg.ridge_online_corr=1. Records 1000 ticks of Ridge weights to a CSV. Operator re-runs identical backtest under cfg.ridge_online_corr=0. Both produce tolerance-equivalent (≤1e-9) but bit-different corr_matrix values → bit-different Cholesky → bit-different FPN_FromDouble rounding at any double-to-FPN boundary → CSV byte hashes differ. Backtest replay-determinism CSV-byte contract silently broken under cfg=1.
- **Root cause:** Welford one-pass incremental update and the existing two-pass batch formula produce mathematically-equivalent results in infinite precision but NOT in IEEE-754 finite precision. The plan currently treats them as "tolerance-equivalent" which is correct for ML-quality but FALSE for replay-determinism. cfg=0 (default) preserves bytewise; cfg=1 (online) silently does not.
- **Fix path:** v5.14.11.A amendment — reframe the replay-determinism contract:
  - Document that cfg=1 is a distinct replay-determinism regime; same-binary same-cfg replays are still bytewise (Welford accumulation is deterministic given fixed order)
  - Add SHA-256-locked snapshot test for cfg=1 scalar path (mirror shape of `tests/controller_test.cpp:22479-22533` Thompson sample-trace lock); fixed 1000-record prediction trace; lock the corr_matrix SHA-256 hash for cfg=0 and cfg=1 separately
  - Drop the "bytewise-identical" framing for cfg=1 ↔ cfg=0; reframe as "tolerance-equivalent (1e-9) across cfg regimes, bytewise within each regime"
  - Periodic-reset every 1000 cycles does NOT recover bytewise identity to cfg=0 — it recovers tolerance identity at the reset boundary but bit-drifts again over the next 1000 cycles. Document this.
- **Target ship:** v5.14.11.A (plan amendment + scalar online kernel + snapshot test; ~30 min)
- **Status:** **OPEN** (plan-stage; pre-coding amendment recommended)
- **Workaround:** Keep cfg.ridge_online_corr=0 (default) until v5.14.11.A snapshot tests land and operator validates the regime

### PARITY-017 — v5.14.11 AVX-512 vectorization bytewise-determinism: 4 sites need explicit discipline annotation + SHA-256 snapshot lock

```yaml
id: PARITY-017
title: v5.14.11 AVX-512 vectorization bytewise-determinism; 4 sites need explicit discipline annotation + SHA-256 snapshot lock
surface_tags: [ml-inference, slow-path, test-infrastructure]
severity: high
parity_axis: scalar↔SIMD
status: closed
detected_at: v5.14.11 (2026-05-11)
related_specs: [DESIGN_SPECS/wire-format-patterns/avx512-byte-determinism-pattern.md]
```

- **Found:** 2026-05-11 during v5.14.11 online-corr-update pre-coding parity audit (no commit yet — plan-stage finding)
- **Severity:** HIGH
  - Cross-binary determinism contract: backtest replay across binaries (-O level, -ffp-contract flag, AVX-512 vs scalar build) must produce bit-identical corr_matrix output
  - Plan Step 2 line 127-130 cites v5.11.7 discipline but doesn't enumerate the 4 sites where it must apply
  - Plan Step 5 line 172 claims "AVX-512 path: byte-identical to scalar path on test harness" — no SHA-256 snapshot test currently proposed
  - Today's impact: zero (AVX-512 path doesn't exist yet). Future impact: silent cross-binary divergence if any of the 4 sites violate discipline
- **Class:** AVX-512 bytewise-determinism class (v5.11.7 Bandit_GetProbabilities precedent at `ML_Headers/BanditLearning.hpp:138-194` — same shape; same risk pattern)
- **Site(s):**
  - Plan declaration: `plans/v5.14-foxml-port-and-maker/subplans/2026-05-08-v5.14.11-online-corr-update.md:107-131` (AVX-512 design block)
  - Build flags: `CMakeLists.txt:11,128,177,214` (`-O3 -march=native -funroll-loops -flto`); `-ffp-contract=fast` is gcc default at -O3 → fmadd fusion is on
  - Precedent commentary: `ML_Headers/BanditLearning.hpp:146-152` (mul-by-reciprocal avoided, fmadd order matches gcc -O3, scalar reductions stay scalar)
- **Symptom:** Operator builds engine with `-march=native` on AVX-512 box. Builds engine with `-march=x86-64-v3` (no AVX-512) on another box. Same backtest under cfg.ridge_online_corr=1 produces bit-different corr_matrix bytes between the two binaries. Backtest CSV byte hashes differ across binaries → cross-binary replay-determinism contract broken.
- **Root cause:** Plan cites v5.11.7 discipline but doesn't enumerate the 4 sites where it must apply:
  1. UpdateOnline outer-product reduction order — row sweep must preserve left-to-right
  2. UpdateOnline mean-update divider — must use `_mm512_div_pd`, NOT `_mm512_mul_pd(delta, 1/n)`
  3. FinalizeCorr division — same _mm512_div_pd discipline
  4. FinalizeCorr constant-prediction guard — mask-blend with explicit `_mm512_setzero_pd`, NOT NaN-from-0/0
- **Fix path:** v5.14.11.B amendment:
  - Add explicit per-site discipline annotation in plan Step 2 (mirror v5.11.7 commentary at `ML_Headers/BanditLearning.hpp:146-152`)
  - Add SHA-256-locked snapshot test in v5.14.11.B (mirror shape of `tests/controller_test.cpp:22498-22533` Thompson sample-trace lock); feed fixed 1000-record prediction trace through both scalar and AVX-512 paths; SHA-256 both corr_matrix byte-streams; assert hashes match
- **Target ship:** v5.14.11.B (AVX-512 vectorization + snapshot test; ~45 min vs original ~150 LOC estimate)
- **Status:** **OPEN** (plan-stage; pre-coding amendment recommended)
- **Workaround:** Operator can disable AVX-512 path via `-mno-avx512f` for replay-determinism testing until snapshot lock lands

### PARITY-018 — v5.14.11 periodic-recompute path may leave RidgeOnlineState stale; drift bound argument is conditional on reset semantics

```yaml
id: PARITY-018
title: v5.14.11 periodic-recompute path may leave RidgeOnlineState stale; drift bound argument is conditional on reset semantics
surface_tags: [ml-inference, slow-path]
severity: medium
parity_axis: train↔serve
status: closed
detected_at: v5.14.11 (2026-05-11)
related_specs: [DESIGN_SPECS/wire-format-patterns/avx512-byte-determinism-pattern.md]
```

- **Found:** 2026-05-11 during v5.14.11 online-corr-update pre-coding parity audit (no commit yet — plan-stage finding)
- **Severity:** MEDIUM
  - Drift bound (plan line 71-73): "periodic full-recompute reset (~every 1000 cycles) keeps drift bounded" depends on whether the reset path also rebuilds Welford accumulators
  - Plan Step 3 line 144-148 ONLY resets `cycles_since_recompute = 0`; does NOT reset `mean[]`, `M2[]`, `outer_xy[]`, `n` accumulators
  - If interpretation A: drift bound argument is wrong (Welford state keeps drifting; next 1000 cycles re-write drift into corr_matrix via FinalizeCorr)
  - If interpretation B: missing helper to rebuild RidgeOnlineState from ring history
  - Plus sliding-window claim (line 70-72) is unspecified at Step 3 — append-only currently shown
- **Class:** Class 18 mirror gap (PARITY-009/010/011/012 sister — logically-equivalent paths with one accumulator rebuild missing)
- **Site(s):**
  - Plan declaration: `plans/v5.14-foxml-port-and-maker/subplans/2026-05-08-v5.14.11-online-corr-update.md:144-148` (periodic recompute branch)
  - Plan declaration: `plans/v5.14-foxml-port-and-maker/subplans/2026-05-08-v5.14.11-online-corr-update.md:70-72` (sliding-window claim, unspecified)
- **Symptom:** Operator runs cfg=1 backtest. After ~2000 cycles, BuildCorr fires at cycle 1000 and refreshes corr_matrix. But Welford accumulators (mean, M2, outer_xy) keep stale state from cycles 0-999. Next FinalizeCorr at cycle 1001 writes Welford-derived corr_matrix on top of BuildCorr's value, drift resumes immediately. Drift bound argument fails silently. Detectable only by direct corr_matrix observation under long-running test.
- **Root cause:** Plan describes "periodic full-recompute" as a drift-mitigation gate but Step 3 only resets the counter, not the accumulators. Ambiguous spec.
- **Fix path:** v5.14.11.C amendment — decide A vs B before coding:
  - Option A: document that periodic BuildCorr only refreshes `corr_matrix` output snapshot; Welford state keeps drifting. Drift bound argument is loosened to "snapshot resync every 1000 cycles, not full state reset"
  - Option B (recommended): add `RidgeBlender_RebuildOnlineState(state, history, n_history, n_models)` helper called inside the same `if` branch as BuildCorr. Cost O(N²K) one-time per 1000 cycles (~1ns/cycle amortized)
  - Sliding-window: if intended, Step 3 needs `UpdateOnline_DropOldest` arithmetic; if not, drop line 70-72 mention
- **Target ship:** v5.14.11.C (engine wiring + propagation + cfg decision; ~30 min for helper + test)
- **Status:** **OPEN** (plan-stage; pre-coding amendment recommended)
- **Workaround:** N/A — needs design decision before code lands

### PARITY-019 — v5.14.11.B Cholesky_Solve back-solve column-access doesn't vectorize via the row-load AVX-512 template

```yaml
id: PARITY-019
title: v5.14.11.B Cholesky_Solve back-solve column-access doesn't vectorize via the row-load AVX-512 template
surface_tags: [ml-inference, slow-path]
severity: medium
parity_axis: scalar↔SIMD
status: closed
detected_at: v5.14.11 (2026-05-11)
closed_at: v5.14.11.B (2026-05-11)
related_specs: [DESIGN_SPECS/wire-format-patterns/avx512-byte-determinism-pattern.md]
```

- **Found:** 2026-05-11 during v5.14.11 AMENDED plan re-audit (no commit yet — plan-stage finding)
- **Severity:** MEDIUM
  - Plan Step 7 line 339-343 lists 3 Cholesky_Solve sub-sites for AVX-512 vectorization (diagonal, forward solve, back solve)
  - Plan code template at line 318-336 shows a row-load shape `_mm512_loadu_pd(&L_out[i][0])` correct for sites 1+2 (decomposition + forward solve; both ROW-access on L_out)
  - Back solve at `RidgeBlender.hpp:172-174` accesses `L_out[k][i]` — COLUMN access on L_out — does NOT load contiguously via the row-load template
  - Today's impact: zero (.B not coded). Future impact: contributor implementing .B either silently transposes (bug) OR improvises a strategy (byte-determinism not guaranteed) OR uses gather (unverified determinism)
- **Class:** AVX-512 byte-determinism implementation gap (v5.11.7 sister; subset of PARITY-017 closure scope)
- **Site(s):**
  - Plan declaration: `plans/v5.14-foxml-port-and-maker/subplans/2026-05-08-v5.14.11-online-corr-update.md:339-343`
  - Plan code template: same file `:318-336`
  - Engine target: `ML_Headers/RidgeBlender.hpp:169-176` (back solve)
  - Sister sites (row access; row-load template applies cleanly): `:131-141` (decomposition) + `:160-167` (forward solve)
- **Symptom:** During v5.14.11.B implementation, contributor applies plan's row-load template uniformly across the 3 Cholesky sites. Either: (a) silently transposes column-access to row-access (semantic bug → wrong corr_matrix → wrong Ridge weights), (b) improvises an undocumented strategy (byte-determinism varies by author), or (c) uses `_mm512_i64gather_pd` with strided indices (gather byte-determinism unverified for this codebase).
- **Root cause:** Plan Step 7 implicitly treats all 3 Cholesky sites as having uniform row-major access. Back-solve is `L_out[k][i]` (column-major access on lower triangle, since L^T is by column when L is row-major). Code template doesn't address.
- **Fix path:** v5.14.11.B amendment — Step 7 site list needs explicit per-site strategy:
  - Sites 1+2 (decomp, forward solve): row-load template as plan shows. APPLIES CLEANLY.
  - Site 3 (back solve): two options to decide before .B coding:
    - Option A (recommended; simplest): keep scalar for back-solve. Inner loop is ≤7 iterations at n=8; SIMD gain marginal. Decision: "back-solve column access; scalar bytewise-deterministic reference; vectorization gain <50ns not worth column-load complexity." Doesn't affect overall .B latency win materially.
    - Option B: transpose L_out → L_T_out once after decomposition (~50ns); back-solve reads `L_T_out[i][k]` (row access on transposed). ~50ns saved on back-solve, paying ~50ns transpose. Net ~0-50ns at n=8; preserves bytewise-determinism since transpose is deterministic.
- **Target ship:** v5.14.11.B (decision baked into plan at amendment time)
- **Status:** **RESOLVED** 2026-05-11 via partial-vectorization decision (Option A — scalar back-solve). Rationale: per `DESIGN_SPECS/wire-format-patterns/avx512-byte-determinism-pattern.md` Rule 5, scalar fallback is the byte-determinism reference; partial vectorization within a function (2 of 3 sites here) is canonical pattern application, not tech-debt deferral. Quantitative justification: for N=8 inner loop with serial dependency chain, scalar back-solve is ~7 cycles vs gather-based ~17 cycles vs transpose-during-decomp net-zero. Plan Step 7 updated 2026-05-11 to explicitly state 2/3 sites vectorize (decomp + forward solve via row-load template); back-solve stays scalar with rationale documented in plan. avx512-byte-determinism-pattern.md extended with "Partial vectorization within a function" subsection (formalizes the pattern for future SIMD work where access pattern varies per-site).
- **Workaround:** N/A — resolved at plan-amendment time

---

### PARITY-020 — train_model_worker_fn missing STAMP_CFG_AUTOPOPULATE; asymmetric with Backtest_RunFullValidation

```yaml
id: PARITY-020
title: train_model_worker_fn missing STAMP_CFG_AUTOPOPULATE; asymmetric with Backtest_RunFullValidation
surface_tags: [training, wire-format, ml-inference, registry]
severity: high
parity_axis: train↔serve
status: closed
detected_at: v5.15 (2026-05-12)
closed_at: v5.15.3.B.1 (2026-05-12)
related_specs: [DESIGN_SPECS/framework-patterns/autopopulate-pattern-for-production-caller-class.md, DESIGN_SPECS/wire-format-patterns/wire-format-byte-preservation-discipline.md]
```

- **Found:** 2026-05-12 during `/parity-check` audit of v5.15 plan (pre-coding gate)
- **Severity:** HIGH
  - 3 production callers should produce identical stamp body field sets for identical training inputs (parity-tested-by-construction invariant per CLAUDE.md item 15)
  - `Backtest_RunFullValidation` (canonical) at `Backtest/BacktestEngine.hpp:1262` calls `STAMP_CFG_AUTOPOPULATE(inf, cfg)` → populates 22 cfg-bound fields (ridge_*, composite_*, winsor_*, exit_blender_mode, risk_*, ml_buy_threshold, gap_acceptable_threshold, bandit_*)
  - `train_model_worker_fn` at `Backtest/BacktestPanels.hpp:3206-3289` does NOT call STAMP_CFG_AUTOPOPULATE — only manually sets 10 architectural fields (inference_cfg/training_poll_interval/model_num_outputs/xgb_hyperparams/build_flags_hash/label_registry_hash/scaler/no AUTOPOPULATE call)
  - Result: Train Model panel stamps lack drift detection for the 22 cfg-bound fields. Engine boot WARN/REFUSE cfg-binding-drift checks pass silently (has_* flags zero) for Train Model-produced models
- **Class:** Class 18 mirror at production-caller level — same shape as v5.9.5b that PARITY-002/003/004/005/008 closed via AUTOPOPULATE (4× recurrence). This is the 5th recurrence at the SISTER production caller. v5.14.post1 fixed train_model_worker_fn field-name migration but did NOT add AUTOPOPULATE.
- **Site(s):**
  - Reference (correct): `Backtest/BacktestEngine.hpp:1262` (RFV)
  - Gap site: `Backtest/BacktestPanels.hpp:3265` (after manual scaler population, before `stamp_write_for_model` call at :3278)
  - Registry: `ML_Headers/StampBoundCfgRegistry.hpp:99` (FOREACH_STAMP_BOUND_CFG with 22 entries)
- **Symptom:** Operator configures `ridge_lambda=0.5` for training; deploys model trained via Train Model panel with `ridge_lambda=0.7` cfg. Engine load-time drift check passes silently (no ridge_lambda line in stamp because has_ridge=0 because AUTOPOPULATE never ran). No WARN/REFUSE. Operator unaware of cfg drift; ridge-blended predictions diverge from training-time behavior.
- **Root cause:** v5.14.post1 mechanical sweep migrated field NAMES but missed adding AUTOPOPULATE call. Train Model worker has been a silent gap since the AUTOPOPULATE pattern was introduced (v5.14.1.E.E.B).
- **Fix path:** v5.15.3.A bundle (recommended): add `STAMP_CFG_AUTOPOPULATE(inf, run_control->results.config_used);` at `BacktestPanels.hpp:3265` (immediately after the manual scaler block, before `stamp_write_for_model`). 1 LOC + ~30 min total including verification.
- **Target ship:** v5.15.3.A (recommended bundling — same sub-ship as multi-horizon stamping)
- **Status:** **CLOSED v5.15.3.B.1** (2026-05-12). `train_model_worker_fn` now calls `tt::Stamp_AssembleAndEmit<BACKTEST_FP>` at `BacktestPanels.hpp:3204+` which walks `STAMP_CFG_AUTOPOPULATE(inf, cfg)` internally. All 22 cfg-bound fields automatically populated. Anchor test `v5.15.3.B.1 PARITY-020: helper-emitted stamp has has_ridge_within_horizon=1 (cfg-bound)` GREEN; sibling has_* bits for composite + exit_blender also asserted. Structural fix preferred over direct patch (CLAUDE.md item 19): helper extraction closes Class 18 mirror at production-caller level via new `tt::Stamp_AssembleAndEmit<F>` orchestration helper; future stamp-emit callers automatically inherit AUTOPOPULATE call. PARITY-020 cannot recur for callers using the helper.
- **Workaround:** N/A (closed; train_model_worker_fn now emits complete stamps).

---

### PARITY-021 — v5.15.3 plan root cause MISDIAGNOSED: multi-horizon DOES stamp via RFV; gap is grid_member_count/_idx never populated

```yaml
id: PARITY-021
title: v5.15.3 plan root cause misdiagnosed; multi-horizon DOES stamp via RFV; gap is grid_member_count/_idx never populated
surface_tags: [training, wire-format, ml-inference, registry, backtest]
severity: high
parity_axis: train↔serve
status: closed
detected_at: v5.15 (2026-05-12)
closed_at: v5.15.3.B.2 (2026-05-12)
related_specs: [DESIGN_SPECS/framework-patterns/autopopulate-pattern-for-production-caller-class.md, DESIGN_SPECS/wire-format-patterns/wire-format-byte-preservation-discipline.md]
```

- **Found:** 2026-05-12 during `/parity-check` audit of v5.15 plan (pre-coding gate)
- **Severity:** HIGH (plan-level structural error; would create duplicate stamp emit path if uncorrected)
  - Plan v5.15.3 root cause claim "multi-horizon worker writes models but never calls stamp_write_for_model" — FALSE
  - Verified: `mh_run_one_horizon_fv` at `Backtest/BacktestPanels.hpp:3633` calls `Backtest_RunFullValidation` which auto-stamps via canonical RFV emit path
  - Both `train_multi_horizon_worker_fn` (serial loop) AND `mh_per_horizon_parallel_worker` (parallel pthread) delegate to `mh_run_one_horizon_fv` → both already stamp
  - Boot warning "4/4 handles missing grid_member_count" indicates the FIELD (not the stamp file) is missing
  - Verified: `grid_member_count` + `grid_member_idx` exist as 2 entries in FOREACH_STAMP_BOUND_MODEL_CONST_PRE_CFG (NOT POST_CFG as plan claims) at `ML_Headers/StampBoundModelConstRegistry.hpp:337-341`. Both share single `inf->has_grid_member_count` flag (group `grid_member`).
  - Verified: ZERO production callers populate `inf.grid_member_count` or `inf.grid_member_idx` anywhere in BacktestEngine.hpp or BacktestPanels.hpp (grep across both files = 0 hits)
  - Verified: `horizon_idx` and `horizon_count` (as stamp-bound field names) DO NOT EXIST in registry — plan claims they do; FALSE
- **Class:** Plan-level factual error; downstream design (the `stamp_emit_for_horizon` helper) is built on the wrong premise
- **Site(s):**
  - Plan v5.15.3 line 174 claim: "these specific entries are in FOREACH_STAMP_BOUND_MODEL_CONST_POST_CFG"
  - MASTER line 213 claim: "all 3 fields already in FOREACH_STAMP_BOUND_MODEL_CONST (verified during v5.14.8.E)"
  - Registry actual: `StampBoundModelConstRegistry.hpp:337-341` (PRE_CFG; 2 fields, not 3)
  - RFV emit reference: `Backtest/BacktestEngine.hpp:1147-1262` (RFV emits stamps; missing grid_member_* population)
  - Recommended insert: RFV emit block (~line 1230 after label_params, before AUTOPOPULATE call) reads `out->req_grid_member_count` + `out->req_grid_member_idx` and populates inf.* + group bit
  - Caller wiring: `mh_run_one_horizon_fv` (BacktestPanels.hpp:3534) sets `fv->req_grid_member_count = horizon_count; fv->req_grid_member_idx = h;` before RFV call
- **Symptom:** Boot log "4/4 handles missing grid_member_count" warning fires for every multi-horizon ensemble load. Operator interprets as "stamp missing" → opens plan v5.15.3 → plan proposes wrong fix (duplicate stamp emit path).
- **Root cause:** Two-level error: (a) registry fields are orphan placeholders (added v5.14.8.E but no production caller populates them); (b) plan misreads boot warning as "stamp file missing" rather than "field missing within otherwise-valid stamp".
- **Fix path (revised v5.15.3 scope):**
  1. Add `req_grid_member_count` + `req_grid_member_idx` fields to `FullValidationResults` (sibling of existing `req_label_lookahead_ticks` at BacktestEngine.hpp:990-1013)
  2. RFV emit block populates `inf.grid_member_count = out->req_grid_member_count; inf.grid_member_idx = out->req_grid_member_idx; STAMP_SET(inf, grid_member);` when `out->req_grid_member_count > 0`
  3. `mh_run_one_horizon_fv` sets `fv->req_grid_member_count = horizon_count; fv->req_grid_member_idx = h;` before calling RFV
  4. Single-horizon callers leave req_grid_member_count = 0 → group bit stays unset → stamp byte-identical to pre-fix
  5. **DROP the v5.15.3 `stamp_emit_for_horizon` helper entirely** — it would create a parallel emit path that conflicts with RFV's emit. Structural-fix-preferred (CLAUDE.md item 19) — fix via the existing chokepoint.
- **Target ship:** v5.15.3.A (revised scope per HIGH.2 in audit report)
- **Status:** **CLOSED v5.15.3.B.2** (2026-05-12). `FullValidationResults` gained 3 `req_*` fields (`req_grid_member_count`, `req_grid_member_idx`, `req_horizon_count`; defaults 1/0/1 for single-horizon callers). `mh_run_one_horizon_fv` plumbs `horizon_count` from worker arg into `fv->req_grid_member_count`, `h` into `fv->req_grid_member_idx`, `role` into `fv->req_role` before calling RFV. `Backtest_RunFullValidation` reads `out->req_grid_*` into `StampArgs::grid_member_count/idx`; helper always emits the group via `STAMP_SET(inf, grid_member)`. Anchor test `v5.15.3.B.2 PARITY-021: stamp body grid_member_count = 3` GREEN with `args.grid_member_count=3, idx=1`. Multi-horizon stamps now identify grid member; single-horizon stamps emit defaults 1/0 (additive — no MODEL_FORMAT_VERSION bump; legacy stamps load via Surface G forward-compat).
- **Workaround:** N/A (closed; multi-horizon worker now plumbs grid identity through RFV emit path).

---

### PARITY-022 — STAMP_MODEL_CONST_AUTOPOPULATE macro is defined-but-unused stub; expansion is self-referential

```yaml
id: PARITY-022
title: STAMP_MODEL_CONST_AUTOPOPULATE macro is defined-but-unused stub; expansion is self-referential
surface_tags: [registry, wire-format, ml-inference]
severity: medium
parity_axis: train↔serve
status: closed
detected_at: v5.15 (2026-05-12)
closed_at: v5.15.3.A.0 (2026-05-12)
related_specs: [DESIGN_SPECS/framework-patterns/autopopulate-pattern-for-production-caller-class.md, DESIGN_SPECS/framework-patterns/x-macro-registry-with-presence-dispatch.md]
```

- **Found:** 2026-05-12 during `/parity-check` audit of v5.15 plan (pre-coding gate)
- **Severity:** MEDIUM (no production caller today → no live bug; but v5.15.3 plan relies on this macro working)
- **Site:** `ML_Headers/StampBoundModelConstRegistry.hpp:601-607` (definition); :680-688 (per-entry expansion)
- **Symptom:** Zero call sites in production code. The macro IS used INSIDE struct field declarations (via inner X-macro at ModelInference.hpp:1766) — that's the struct gen pass, separate from runtime population. For runtime population, calling `STAMP_MODEL_CONST_AUTOPOPULATE(inf, meta, now_us)` would expand to e.g., `(inf).training_timestamp_us = (uint64_t)((unsigned long)inf->training_timestamp_us)` — a self-referential assignment that does nothing useful (or copies a field to itself if `inf` is a pointer dereference; either way: no field copy from a meta source).
- **Root cause:** v5.14.8.0 introduced FOREACH_STAMP_BOUND_MODEL_CONST registry + this AUTOPOPULATE companion. The companion's `get_value` column was populated with `inf->X` expressions (matching the struct field references used by other expansions like struct field gen). But for a runtime populator, get_value should reference an EXTERNAL source (e.g., `meta.X` or `cfg.X`), not the destination struct itself. Macro definition wasn't completed.
- **Class:** Production-caller pattern incomplete — macro defined as scaffolding but never wired to a real META source
- **Fix path:**
  - **Option A — defer macro wiring:** v5.15 plans must NOT rely on this macro for runtime population. Production callers continue manual architectural-field population (today's pattern at RFV BacktestEngine.hpp:1153-1240). TECH_DEBT entry tracks the deferred macro completion.
  - **Option B — wire properly in future sprint:** registry get_value column changes from `inf->X` to e.g., `cfg.X` (or to per-entry META_* dispatch macros). All production callers can then use the single-call AUTOPOPULATE.
- **Target ship:** Plan v5.15 → Option A (defer); future sprint → Option B (when reviewer revisits architectural-field population)
- **Status:** **CLOSED v5.15.3.A.0** (2026-05-12). Macro body replaced with `static_assert(false, "STAMP_MODEL_CONST_AUTOPOPULATE is QUARANTINED (PARITY-022; v5.15.3.A). Model-const fields populate manually from StampArgs in callers like Stamp_AssembleAndEmit. See TECH_DEBT-036 for architectural-field AUTOPOPULATE redesign.")` at `ML_Headers/StampBoundModelConstRegistry.hpp`. Production callers cannot accidentally invoke; compile-time error fires if they do. TECH_DEBT-036 tracks the future architectural-field AUTOPOPULATE redesign (registry get_value column would need to reference an external META source, e.g., `cfg.X` or per-entry META_* dispatch).
- **Workaround:** N/A (closed; production callers use manual per-call population from StampArgs via `tt::Stamp_AssembleAndEmit<F>` helper).

---

### PARITY-023 — v5.15.4 HotSwapSnapshot/Revert design captures pointers only; pre-swap data destroyed in-place by Free

```yaml
id: PARITY-023
title: v5.15.4 HotSwapSnapshot/Revert design captures pointers only; pre-swap data destroyed in-place by Free
surface_tags: [boot-time, ml-inference, slow-path]
severity: medium
parity_axis: train↔serve
status: closed
detected_at: v5.15 (2026-05-12)
closed_at: v5.15.4 (2026-05-12)
related_specs: [DESIGN_SPECS/feature-patterns/shadow-load-state-transition-pattern.md, DESIGN_SPECS/framework-patterns/postloadsetup-registry-pattern.md]
```

- **Found:** 2026-05-12 during `/parity-check` audit of v5.15 plan (pre-coding gate)
- **Severity:** MEDIUM (plan-stage design flaw; existing behavior is functional — current code uses "log-and-leave" semantics which work; v5.15.4 proposes new revert path that won't work as designed)
- **Site:**
  - `CoreFrameworks/EnsembleHotSwap.hpp:75-76` — `EnsembleModelZoo_Free(swap_ezoo)` destroys pre-swap state in-place
  - `CoreFrameworks/EngineSharded.hpp:2923-2924` — single-zoo branch `CoreModelZoo_Free(swap_zoo); CoreModelZoo_Init(swap_zoo);` destroys + reinits in-place
  - Plan v5.15.4.B line 240-254: `HotSwap_CaptureSnapshot` captures `prev_ezoo = state.cores[core_idx].ensemble_handle` — but the captured pointer is the SAME pointer that gets passed into the Free routine
- **Symptom (under plan as written):** A failed hot-swap that triggers Revert would attempt to restore a pointer to memory that's been Free'd + reinit'd. Either segfault (dereferencing the post-init empty state) or silent corruption (next inference reads garbage from the reinit'd zoo).
- **Root cause:** Plan design assumes capture-by-pointer preserves data; in fact data is destroyed by the subsequent Free call. Deep copy would be needed (expensive — ~1MB per core including booster handles, scaler, bandit state) OR API restructure (load new into SHADOW zoo; atomic swap on validate success; discard SHADOW on failure) OR keep existing "log-and-leave" semantics.
- **Class:** Design-level error not caught by line-level review; would surface as runtime crash or corruption under failed hot-swap test
- **Fix path (v5.15.4 amendment options):**
  - **Option A (RECOMMENDED for v5.15) — de-scope:** Drop TECH_DEBT-005 closure from v5.15.4. Keep current "log-and-leave" semantics (v5.10.0c — flag-only on validate failure; operator manually reverts via cfg+restart). v5.15.4 keeps the trading_mode strict-default flip (cleanly delivers operational safety win) but doesn't restructure hot-swap. TECH_DEBT-005 stays open with effort estimate (300-400 LOC shadow-load) for future sprint.
  - **Option B — shadow-load restructure:** EngineSharded_HotSwapEnsemble + single-zoo Free+Init+Load become: (1) allocate SHADOW zoo; (2) load new model into SHADOW; (3) validate SHADOW; (4) on success: atomic swap shadow into state.cores[c] + Free old; on failure: Free shadow + keep old. ~300-400 LOC + new tests. Deferred to future sprint.
  - **Option C — deep-copy before Free:** Capture function deep-clones the pre-swap zoo (substantial; ~1MB/core; booster handle clone via XGBoosterSaveModelToBuffer + XGBoosterLoadModelFromBuffer; scaler memcpy; bandit state memcpy). Not free; deferred.
- **Target ship:** v5.15.4 (de-scope) → TECH_DEBT-005 stays open
- **Status:** **CLOSED v5.15.4** (2026-05-12). Plan amended to use shadow-load pattern (Option B in original finding) per Caramel's "structural fix > direct patch" direction (CLAUDE.md item 19). Implementation:
  - `tt::HotSwap_ShadowLoad_Ensemble<F>` + `tt::HotSwap_ShadowLoad_SingleZoo<F>` in `CoreFrameworks/HotSwap.hpp`
  - `aligned_alloc(64, sizeof(T))` for new state + Init + Load + PostLoadSetup + `__atomic_exchange_n` + Free OLD
  - **No capture-pointer needed; no revert path needed** — pre-swap state untouched on any failure; caller continues serving from pre-swap zoo
  - Boot path migrated from `static CoreModelZoo<F>[]` to per-core `aligned_alloc(64)` (required for `free(old_ezoo)` validity on first swap)
  - `alignas(64)` retrofit on `CoreModelZoo<F>` + `EnsembleModelZoo<F>` container structs
  - `DESIGN_SPECS/feature-patterns/shadow-load-state-transition-pattern.md` promoted DRAFT v0.1 → ACTIVE v1.0 (2 field-tested applications)
  - Anchor tests verify pre-swap handle preserved after failed shadow-load (PARITY-023 closure proof)
- **Workaround:** N/A (closed; shadow-load eliminates the torn-state moment that revert would have addressed).

---

### PARITY-024 — Per-arm trained TP/SL barriers stamped at training but not consumed at serving; ml_tp_pct/ml_sl_pct Tier 1 promotion missing

```yaml
id: PARITY-024
title: Per-arm trained TP/SL barriers stamped at training but not consumed at serving; ml_tp_pct/ml_sl_pct Tier 1 promotion missing (CLOSED at .B.3 via .A.7+.B.2+.B.3 cohort framework)
surface_tags: [slow-path, ml-inference, cfg-flow, wire-format, registry]
severity: high
parity_axis: train↔serve
status: closed
detected_at: v5.15.5 (2026-05-12)
closed_at: v5.15.5.F.4d.1.B.3
closure_rationale: Per-arm trained TP/SL barriers Tier 1 promotion landed via .A.7 + .B.2 + .B.3 cohort framework (per `.B.3` postmortem line 101); barrier-blend fields wired through engine-side cfg-derived consumer framework + per-horizon barrier-blending pattern. Ledger status flip was missed at `.B.3` ship close; retroactively flipped to closed at `v5.15.5.F.4d.1.D` Phase D.8 after Check 11 dogfood detection (sister to .B.8 + .D forward-promise retroactive ledger writes; same M7 surface).
related_specs: [DESIGN_SPECS/feature-patterns/per-horizon-barrier-blending-with-shadow-mode.md, DESIGN_SPECS/framework-patterns/autopopulate-pattern-for-production-caller-class.md, DESIGN_SPECS/wire-format-patterns/wire-format-byte-preservation-discipline.md]
```

- **Found:** 2026-05-12 during `/parity-check` audit of v5.15.5 plan (pre-coding gate)
- **Severity:** HIGH (silent decision drift; trades fire at cfg-side TP/SL even when model trained on different barriers; train-serve gap observable in P&L over hours under multi-horizon ensembles)
- **Class:** Train-serve cfg-binding gap (Class similar to PARITY-004/005); also touches Class 18 (parallel path drift — barriers exist on stamp + on cfg but not wired into the slow-path build)
- **Site(s):**
  - `Strategies/StrategyParameters.hpp:1259-1260` — `tp_pct = config->ml_tp_pct; sl_pct = config->ml_sl_pct` reads cfg directly, ignoring stamp's `label_tp_pct`/`label_sl_pct`
  - `ML_Headers/NodeModelZoo.hpp:349-350` — stamp body's `label_tp_pct`/`label_sl_pct` already loaded into `ModelHandle<F>` (since v5.11.42 D.2) but ezoo lacks per-arm tight-pack copy for slow-path consumption
  - `CoreFrameworks/ModelValidation.hpp:184-203` — Tier 1 cfg-drift list currently = {`confidence_threshold_scale`, `barrier_gate_enabled`}; `ml_tp_pct`/`ml_sl_pct` not in either tier
- **Symptom:** Multi-horizon ensemble trained against label-specific TP/SL barriers (e.g., 0.03 / 0.05 / 0.07) fires trades with cfg.ml_tp_pct (e.g., 0.015) regardless of which horizon dominated. Train and serve see different barrier policies; cfg-side change after training silently shifts every position's barriers; no observability surface for the divergence.
- **Root cause:** v5.13.5 added per-horizon TP/SL on the TRAINING side (Label Kind CSV + TP/SL CSV CLI inputs; multi-horizon stamp body carries `label_tp_pct`/`label_sl_pct` per `Backtest/BacktestPanels.hpp:3712-3713,5546-5547`); the SERVING side never extended to consume these. EnsembleModelZoo carries no per-arm barrier array; slow-path ML_BuildParameters reads cfg unconditionally.
- **Fix path (v5.15.5 plan):**
  - Phase A: extend `EnsembleModelZoo<F>` with `per_arm_buy_tp_pct[ENSEMBLE_HORIZON_MAX]` + `per_arm_buy_sl_pct[]`; populate from stamp at `CoreModelZoo_TryLoadRole` (the same site that already copies into `handle->label_*_pct`).
  - Phase B: introduce `FOREACH_BARRIER_BLEND_MODE` 5-mode dispatch (LEGACY / BLEND / DOMINANT / BOTH_BLEND_DRIVES / BOTH_DOMINANT_DRIVES); slow-path `ML_BuildParameters` selects barriers per mode; LEGACY mode preserves bytewise pre-v5.15.5 behavior.
  - Phase C: promote `ml_tp_pct`/`ml_sl_pct` + `barrier_blend_mode` to Tier 1 cfg-drift list (REFUSE in strict; WARN in loose); add `barrier_blend_mode` row to `FOREACH_STAMP_BOUND_CFG` registry at END (after `trading_mode`) via STAMP_CFG_AUTOPOPULATE.
- **Target ship:** v5.15.5 (planned 2026-05-12; tag v5.15.5.A through v5.15.5 umbrella)
- **Status:** OPEN (plan stage; ready for coding pending 4 must-fix amendments per pre-coding parity-check)
- **Workaround:** Operators training with non-default `label_tp_pct`/`label_sl_pct` should set `cfg.ml_tp_pct`/`cfg.ml_sl_pct` to match the dominant horizon's training-time barriers + run in single-model mode (no ensemble) until v5.15.5 ships. `acknowledge_inference_cfg_drift=1` suppresses any related WARN if barriers diverge by design.

---

### PARITY-025 — BacktestSharded.hpp retains stale external SET/CLR mirror for MASK_OMS_STATE_PARTIAL_EXIT_ENABLED (Class 18 mirror not fully eliminated by v5.15.5.C.3 Phase 3b Finding A)

```yaml
id: PARITY-025
title: BacktestSharded.hpp retains stale external SET/CLR mirror for MASK_OMS_STATE_PARTIAL_EXIT_ENABLED
surface_tags: [backtest, oms-drainer, registry, bitmap-packed]
severity: high
parity_axis: live↔backtest
status: closed
detected_at: v5.15.5.C.3 (2026-05-13)
closed_at: v5.15.5.C.3.1 (2026-05-13)
related_specs: [DESIGN_SPECS/framework-patterns/autopopulate-pattern-for-production-caller-class.md, DESIGN_SPECS/refactor-patterns/registry-bitmap-set-discipline.md]
```

- **Found:** 2026-05-13 during `/parity-check` audit of v5.15.5.C.3 Phase 3b (commit d410525, post-coding gate)
- **Severity:** HIGH (Class 18 mirror — Phase 3b's Finding A was specifically intended to eliminate this exact mirror class; EngineSharded was correctly cleaned, BacktestSharded sister site was missed)
- **Class:** Class 18 mirror at production-caller level — same root cause shape as PARITY-002/003/004/005/008/009/010/011/012 closed via AUTOPOPULATE / PostLoadSetup registries in prior sprints
- **Site:**
  - Engine (correctly cleaned): `CoreFrameworks/EngineSharded.hpp:670-674` (external SET/CLR mirror DROPPED in Phase 3b; bit set via `OrderManager_Init` parameter + registry walk inside `OMS_INIT_AUTOPOPULATE`)
  - Backtest (STALE MIRROR — gap site): `Backtest/BacktestSharded.hpp:194-201` retains the redundant block:
    ```cpp
    if (BITMAP_IS_SET(cfg.lifecycle_cfg_flags, MASK_LIFECYCLE_CFG_PARTIAL_EXIT_ENABLED)) {
        BITMAP_SET(oms.oms_state_flags, tt::MASK_OMS_STATE_PARTIAL_EXIT_ENABLED);
    } else {
        BITMAP_CLR(oms.oms_state_flags, tt::MASK_OMS_STATE_PARTIAL_EXIT_ENABLED);
    }
    ```
  - Backtest already passes `bt_partial_exit_enabled` to `OrderManager_Init` at line 183, which sets/clears the same bit via the BIT-kind registry row inside `OMS_INIT_AUTOPOPULATE`. Both expressions derive from `cfg.lifecycle_cfg_flags & MASK_LIFECYCLE_CFG_PARTIAL_EXIT_ENABLED` → IDENTICAL values produced. Lines 194-201 are dead code.
- **Symptom:** ZERO behavioral impact today (idempotent SET/CLR with same value). **But:** (a) parity hazard if a future contributor changes one path without the other (e.g., per-core override for partial_exit_enabled would route via OmsInitCtx + registry in EngineSharded while BacktestSharded's lines 194-201 silently desync); (b) Class 18 mirror NOT fully extinguished by Finding A (commit message claims "Drops engine's external OMS_STATE_FLAG_SET(PARTIAL_EXIT_ENABLED) call" — singular; the sister site in BacktestSharded was missed); (c) documentation drift class — remaining BacktestSharded mirror invites future contributors to "follow the existing pattern" of external SET/CLR, defeating the structural-fix discipline.
- **Root cause:** Phase 3b commit (d410525) correctly removed the external SET/CLR block in EngineSharded but missed the same block in BacktestSharded. Likely missed because the BacktestSharded mirror was visually distinct from the engine site (different surrounding comments + adjacent train-serve-parity logic block) and the FOREACH_OMS_FIELD migration sweep didn't tour every BITMAP_SET site on MASK_OMS_STATE_PARTIAL_EXIT_ENABLED.
- **Fix path:** v5.15.5.C.3.x follow-up sub-ship — delete `Backtest/BacktestSharded.hpp:194-201` (8 LOC). Update the leading comment (line 194 `v4.7.15: mirror partials geometry…`) to a 3-line note explaining the migration: "v5.15.5.C.3 (Finding A close completion): PARTIAL_EXIT_ENABLED bit set inside OMS_INIT_AUTOPOPULATE via the BIT-kind registry row (parameter `bt_partial_exit_enabled` above). External SET/CLR mirror removed." ~10 min effort total.
- **Target ship:** v5.15.5.C.3.x (recommended) — bundle into the next sub-ship that touches BacktestSharded.hpp; or standalone cleanup sub-ship if no scheduled touch.
- **Status:** ✅ **CLOSED 2026-05-13 via v5.15.5.C.3.1 fixup commit `1c593a5`** — same finding surfaced concurrently by `/dod-audit` HIGH-1 (both audits cross-flagged the identical Class-18 mirror gap). Fix applied: deleted the 5-line `BITMAP_SET/CLR(MASK_OMS_STATE_PARTIAL_EXIT_ENABLED)` block at `Backtest/BacktestSharded.hpp:197-201`; replaced with a 5-line comment cross-referencing Finding A's structural-fix discipline + the canonical SET site via `OMS_INIT_AUTOPOPULATE`. Both audits independently verified identical fix scope. Build clean (3052/3052 tests passing post-fix). Documented in commit message body.
- **Workaround:** N/A (production behavior was always correct; this was structural cleanup to prevent future drift).

### PARITY-026 — Live engine never calls EventLoopState_ConfigureKillSwitch (kill_switch dead in production)

```yaml
id: PARITY-026
title: Live engine never calls EventLoopState_ConfigureKillSwitch (kill_switch dead in production)
surface_tags: [engine-sharded-boot, kill-switch, live-safety, class-18-mirror, train-serve-asymmetry]
severity: critical
parity_axis: live↔backtest (live missing the call)
status: closed
detected_at: v5.15.5.F.4d.1.B.3 WIP-8 (2026-05-24 audit cycle)
closed_at: v5.15.5.F.4d.1.B.4 WIP-9 (2026-05-26; structural by-construction closure — EngineCommon_BootGlobal extracted with EventLoopState_ConfigureKillSwitch call at EngineCommon.hpp:191 gated on MASK_RISK_CFG_KILL_SWITCH_ENABLED; invoked from LIVE EngineSharded.hpp:749 + BACKTEST BacktestSharded.hpp:206; ledger update at .B.4 post-ship-audit 2026-05-27 per close-session Stage 8). Verification PENDING: `/parity-check` regression-free run after paper-test session.
related_specs: [DESIGN_SPECS/meta-disciplines/structural-fix-preferred-decision-framework.md, DESIGN_SPECS/meta-disciplines/train-serve-execution-layer-parity.md (Stage 3 first canonical at .B.4)]
```

- **Found:** 2026-05-24 via ML↔LIVE structural sweep agent. Full report: `plans/v5.15-live-readiness/plan_checks/2026-05-24-train-serve-asymmetry-sweep.md`
- **Severity:** CRITICAL — live-mode safety primitive non-functional; sprint named `v5.15-LIVE-READINESS`; shipping to paper-test session with dead kill_switch = opposite of sprint goal; worst-case silent unbounded loss
- **Class:** Class 18 mirror at execution layer (sister site to PARITY-025; same shape as PARITY-002/003/004/005/008-012 closed via AUTOPOPULATE / PostLoadSetup in prior sprints)
- **Site(s):**
  - Live (BROKEN): `CoreFrameworks/EngineSharded.hpp:742` — calls ONLY `EventLoopState_Init(&state, &oms)`; NO `EventLoopState_ConfigureKillSwitch` follows
  - Backtest (CORRECT): `Backtest/BacktestSharded.hpp:217-221` — `if (BITMAP_IS_SET(cfg.risk_cfg_flags, MASK_RISK_CFG_KILL_SWITCH_ENABLED)) EventLoopState_ConfigureKillSwitch(&state, 0, cfg.kill_switch_drawdown_pct);`
  - Eval body: `CoreFrameworks/ControllerEventLoop.hpp:3300-3314` — early-returns when `ks_min_balance == 0 && ks_max_drawdown_pct == 0`. Both stay zero-init.
- **Symptom:** Operator sets `kill_switch_enabled=1, kill_switch_drawdown_pct=5.0` in `engine.cfg`. Backtest replays trip the switch correctly; live trading runs IGNORE both fields → no drawdown protection in production.
- **Root cause:** When the sharded path was built, the boot block didn't include `EventLoopState_ConfigureKillSwitch`. Backtest got the call right; live never got it. Sister to PARITY-028 + PARITY-029 — three sister Class 18 mirror instances at the same boot surface.
- **Fix path:** Add `EventLoopState_ConfigureKillSwitch` call to `EngineSharded_Run` boot right next to `:742` `EventLoopState_Init` — mirror the backtest discipline. Better: extract `EngineCommon_BootPerCore(cfg, core_idx, state, oms)` shared helper called from BOTH sites (closes A1+A2+A3+A4+B1+B2+B3 simultaneously per TECH_DEBT-119).
- **Target ship:** `v5.15.5.F.4d.1.B.4` OR earlier hotfix (~5-LOC patch).
- **Status:** CLOSED at `v5.15.5.F.4d.1.B.4` (YAML `closed_at:` above has WIP-detail; prose sync 2026-05-27 per Stage 4.5 finding)
- **Workaround:** (pre-closure historical) Operator MUST monitor drawdown manually in live trading until fix lands. Live mode without kill_switch is not safe for unattended trading.

### PARITY-027 — Backtest has no ML exit-prediction submit path (use_exit_model=1 train-serve break)

```yaml
id: PARITY-027
title: Backtest has no ML exit-prediction submit path (use_exit_model train-serve break)
surface_tags: [backtest-slow-path, exit-model-ml-inference, oms-drainer, class-18-mirror, train-serve-asymmetry]
severity: critical
parity_axis: live↔backtest (backtest missing the dispatch)
status: closed
detected_at: v5.15.5.F.4d.1.B.3 WIP-8 (2026-05-24 audit cycle)
closed_at: v5.15.5.F.4d.1.B.4 WIP-13 (2026-05-26; structural by-construction closure — exit-model dispatch in EngineCommon_SlowPathCycleOneCore body at EngineCommon.hpp:609-644 gated on MASK_ML_CFG_USE_EXIT_MODEL; invoked from LIVE per-core slow thread + BACKTEST via EngineCommon_SlowPathCycleAllCores at BacktestSharded.hpp:362; ledger update at .B.4 post-ship-audit 2026-05-27 per close-session Stage 8). Verification PENDING: `/parity-check` regression-free run after paper-test session.
related_specs: [DESIGN_SPECS/meta-disciplines/train-serve-execution-layer-parity.md (Stage 3 first canonical at .B.4)]
```

- **Found:** 2026-05-24 ML↔LIVE structural sweep
- **Severity:** CRITICAL — silent train-serve break for `use_exit_model=1` users; trained model never sees early-exit pattern in backtest equity curve; bandit reward attribution for exit predictor learns from live with zero training-time signal
- **Class:** Class 18 mirror — dispatch only on live side
- **Site(s):**
  - Live (~85 LOC): `CoreFrameworks/EngineSharded.hpp:3142-3227` — `MASK_ML_CFG_USE_EXIT_MODEL` + `last_exit_prediction > exit_threshold` → `OMS_PushExitForSlot` MARKET_SELL + `last_exit_predicted_bitmap` set for v5.13.4 bandit reward attribution
  - Backtest: `Backtest/BacktestSharded.hpp` + `CoreFrameworks/ShardedBacktestDriver.hpp:189-397` — ZERO hits for `use_exit_model|last_exit_prediction|OMS_PushExitForSlot|MASK_ML_CFG_USE_EXIT_MODEL`
- **Symptom:** When `use_exit_model=1`, backtest exits via TP/SL/time-exit only; live additionally fires ML exit predictions. Live performance diverges from backtest projection; models systematically under-estimate exit-predictor value.
- **Root cause:** Exit-model dispatch added live-only; backtest mirror never written. Distinct from PARITY-010 (covered exit-bandit INIT state parity); this is the DISPATCH parity gap.
- **Fix path:** Extract `EventLoop_ExitPredictionSubmitOneCore(state, oms, cfg, c, price_d)` shared helper called from BOTH `EngineSharded:3142` AND `ShardedBacktest_RunTick` slow-path block. ~40 LOC extract + 5 LOC each callsite. Folds into TECH_DEBT-119 C1 EngineCommon structural extract.
- **Target ship:** `v5.15.5.F.4d.1.B.4`
- **Status:** CLOSED at `v5.15.5.F.4d.1.B.4` (YAML `closed_at:` above has WIP-detail; prose sync 2026-05-27 per Stage 4.5 finding)
- **Workaround:** (pre-closure historical) Operator should disable `use_exit_model` (set `MASK_ML_CFG_USE_EXIT_MODEL=0`) until fix lands, OR accept that backtest equity curves systematically diverge from live for any model trained with this flag enabled.

### PARITY-028 — ConfidenceScorer_BindCompositeCfg + RollingTurnover_Init missing in backtest (composite confidence drift)

```yaml
id: PARITY-028
title: ConfidenceScorer_BindCompositeCfg + RollingTurnover_Init missing in backtest
surface_tags: [backtest-boot, confidence-scoring, class-18-mirror, train-serve-asymmetry]
severity: critical
parity_axis: live↔backtest (backtest missing 2 calls)
status: closed
detected_at: v5.15.5.F.4d.1.B.3 WIP-8 (2026-05-24 audit cycle)
closed_at: v5.15.5.F.4d.1.B.4 WIP-9 (2026-05-26; structural by-construction closure — both ConfidenceScorer_BindCompositeCfg + RollingTurnover_Init in EngineCommon_BootPerCore body at EngineCommon.hpp:394 + :405; invoked from LIVE EngineSharded.hpp + BACKTEST BacktestSharded.hpp via BootPerCore loop; ledger update at .B.4 post-ship-audit 2026-05-27 per close-session Stage 8). Verification PENDING: `/parity-check` regression-free run after paper-test session.
related_specs: [PARITY-003 (sister; live side was closed at v5.14.1.B.1 but backtest mirror never enforced), DESIGN_SPECS/meta-disciplines/train-serve-execution-layer-parity.md (Stage 3 first canonical at .B.4)]
```

- **Found:** 2026-05-24 ML↔LIVE structural sweep
- **Severity:** CRITICAL — silent train-serve drift on composite-confidence configs (new feature path; growing surface)
- **Class:** Class 18 mirror — sister to PARITY-003 (closed live side; didn't enforce backtest mirror)
- **Site(s):**
  - Live (CORRECT): `CoreFrameworks/EngineSharded.hpp:1125-1140` — calls `ConfidenceScorer_Init` + `ConfidenceScorer_BindCompositeCfg` + `RollingTurnover_Init` per-core with cfg values (`confidence_freshness_tau_secs`, `confidence_capacity_target_dollars`, `confidence_capacity_kappa`, `confidence_rmse_baseline`, `confidence_turnover_window`, `confidence_turnover_topk`)
  - Backtest (BROKEN): `Backtest/BacktestSharded.hpp:408-411` — calls only `ConfidenceScorer_Init`; `BindCompositeCfg` + `RollingTurnover_Init` ABSENT
- **Symptom:** With `confidence_composite_enabled=1`, live uses composite freshness/capacity/RMSE blend; backtest scorer falls back to legacy product mode + EventLoopState_Init defaults (100/3). Training labels + features collected with one composite shape; serving emits a different shape. Bandit_blend_ratio + confidence-gated submission decisions diverge.
- **Root cause:** PARITY-003 fix at v5.14.1.B.1 patched live side only. Sister to PARITY-026 + PARITY-029 — three sister Class 18 mirrors at the same boot surface (`EngineSharded.hpp:1125-1154`).
- **Fix path:** 10-LOC copy from `EngineSharded:1130-1140` to `BacktestSharded:411`. Better: extract `Confidence_BindFromCfg(scorer, turnover, cfg, core_idx)` shared helper. Folds into TECH_DEBT-119 C1.
- **Target ship:** `v5.15.5.F.4d.1.B.4`
- **Status:** CLOSED at `v5.15.5.F.4d.1.B.4` (YAML `closed_at:` above has WIP-detail; prose sync 2026-05-27 per Stage 4.5 finding)
- **Workaround:** (pre-closure historical) Operator should set `confidence_composite_enabled=0` (legacy product mode) until fix lands; composite confidence configs are not safe to train-then-deploy with current backtest path.

### PARITY-029 — Strategy_InitPerCore never called in backtest (pre-v5.4 F7 bug never closed on backtest side)

```yaml
id: PARITY-029
title: Strategy_InitPerCore never called in backtest (pre-v5.4 F7 bug alive on backtest)
surface_tags: [backtest-boot, strategy-lifecycle, class-18-mirror, train-serve-asymmetry, training-data-contamination]
severity: critical
parity_axis: live↔backtest (backtest missing the call)
status: closed
detected_at: v5.15.5.F.4d.1.B.3 WIP-8 (2026-05-24 audit cycle)
closed_at: v5.15.5.F.4d.1.B.4 WIP-9 (2026-05-26; structural by-construction closure — Strategy_InitPerCore in EngineCommon_BootPerCore body at EngineCommon.hpp:417 OUTSIDE ML branch gated by strategy_id; invoked from BOTH LIVE + BACKTEST via shared BootPerCore loop; closes pre-v5.4 F7 bug structurally for backtest path; ledger update at .B.4 post-ship-audit 2026-05-27 per close-session Stage 8). Verification PENDING: `/parity-check` regression-free run after paper-test session.
related_specs: [postmortem F7 (v5.4.0; live side fix); DESIGN_SPECS/meta-disciplines/structural-fix-preferred-decision-framework.md; DESIGN_SPECS/meta-disciplines/train-serve-execution-layer-parity.md (Stage 3 first canonical at .B.4)]
```

- **Found:** 2026-05-24 ML↔LIVE structural sweep
- **Severity:** CRITICAL — silent training data contamination affecting ALL stateful strategies; broken since v5.4 (~14 months); every model trained on backtest data since then has training data contamination
- **Class:** Class 18 mirror — F7 postmortem fix patched live side only
- **Site(s):**
  - Live (CORRECT): `CoreFrameworks/EngineSharded.hpp:1154` — `tt::Strategy_InitPerCore(&state, i, state.cores[i].strategy_id, &state.cores[i].slow_state->rolling_short, &cfg)` (v5.4.0 Phase 1.3 fix per postmortem F7)
  - Backtest (BROKEN): `Backtest/BacktestSharded.hpp` — ZERO hits for `Strategy_InitPerCore`. Backtest started with the F7 bug; live got fixed; backtest still has it.
- **Symptom:** Strategies with per-core state structs (MeanReversion stateful, Momentum with state, MLStrategy bandit context) train with garbage initial state on first slow-path cycle. Convergence eventually happens after `min_warmup_samples`, but feature/label rows captured pre-convergence pollute training. Live correctly initializes per-core state on boot.
- **Root cause:** F7 postmortem fix only patched the live side. Sister to PARITY-026 + PARITY-028 — three sister Class 18 mirrors at the same boot surface.
- **Fix path:** 5-LOC add matching `tt::Strategy_InitPerCore` call in `BacktestSharded:411`. Folds into TECH_DEBT-119 C1.
- **Target ship:** `v5.15.5.F.4d.1.B.4`
- **Status:** CLOSED at `v5.15.5.F.4d.1.B.4` (YAML `closed_at:` above has WIP-detail; prose sync 2026-05-27 per Stage 4.5 finding)
- **Workaround:** (pre-closure historical) Operator should be aware that any model trained on backtest data since v5.4 may carry pre-convergence stateful-strategy data contamination. Models trained with stateless strategies (SimpleDip, EmaCross) are unaffected. Increasing `min_warmup_samples` is a partial mitigation.

### PARITY-030 — BNB fee discount applied LIVE-only (33% backtest fee inflation; train-serve cost drift)

```yaml
id: PARITY-030
title: BNB fee discount applied LIVE-only (backtest pays 33% higher fees than live)
surface_tags: [backtest-boot, fee-model, train-serve-asymmetry, cost-parity]
severity: high
parity_axis: live↔backtest (backtest missing the discount)
status: closed
detected_at: v5.15.5.F.4d.1.B.3 WIP-8 (2026-05-24 audit cycle)
closed_at: v5.15.5.F.4d.1.B.4 WIP-9 (2026-05-26; structural by-construction closure — EngineCommon_ApplyBnbDiscount extracted as non-const cfg one-shot mutator at EngineCommon.hpp:154; invoked from LIVE EngineSharded.hpp:696 + BACKTEST BacktestSharded.hpp:203 with identical math; closes 33% fee inflation on backtest path; ledger update at .B.4 post-ship-audit 2026-05-27 per close-session Stage 8). Verification PENDING: `/parity-check` regression-free run after paper-test session.
related_specs: [DESIGN_SPECS/meta-disciplines/train-serve-execution-layer-parity.md (Stage 3 first canonical at .B.4)]
```

- **Found:** 2026-05-24 ML↔LIVE structural sweep
- **Severity:** HIGH — silent train-serve cost drift on real cfg flag (`pay_fees_in_bnb=1`); models trained with inflated costs bias toward conservative entry thresholds; live execution actually pays 0.75x fees → models leave alpha on table
- **Class:** Class 18 mirror at boot surface
- **Site(s):**
  - Live: `CoreFrameworks/EngineSharded.hpp:690-699` — `cfg.pay_fees_in_bnb` multiplies `cfg.cores[c].fee_rate_maker/_taker` by 0.75 per-core at boot
  - Backtest: ZERO hits for `pay_fees_in_bnb|bnb_factor`. Backtest uses raw `cfg.fee_rate_*` per core.
- **Symptom:** Equity curves systematically diverge for users with `pay_fees_in_bnb=1` — backtest projects lower returns than live actually achieves; operator may dismiss this as "live is doing better" without recognizing the cost-model parity break.
- **Root cause:** BNB fee discount feature added live-only; backtest mirror not implemented at addition time.
- **Fix path:** Copy per-core multiply block to `BacktestSharded:215` (before existing kill-switch block). Better: extract `Cfg_ApplyBnbDiscount(&cfg)` shared helper. Folds into TECH_DEBT-119 C1.
- **Target ship:** `v5.15.5.F.4d.1.B.4`
- **Status:** CLOSED at `v5.15.5.F.4d.1.B.4` (YAML `closed_at:` above has WIP-detail; prose sync 2026-05-27 per Stage 4.5 finding)
- **Workaround:** (pre-closure historical) Operator should be aware that backtest results with `pay_fees_in_bnb=1` are pessimistic vs live execution by ~33% of fee load.

### PARITY-031 — Per-core regime divergence at backtest feature collect (N→1 collapse)

```yaml
id: PARITY-031
title: Backtest collapses N per-core regime states to 1 at feature compute (live serves N per-core)
surface_tags: [backtest-feature-compute, regime-detection, per-core-state, train-serve-asymmetry]
severity: high
parity_axis: live↔backtest (backtest collapses N→1)
status: closed
detected_at: v5.15.5.F.4d.1.B.3 WIP-8 (2026-05-24 audit cycle)
closed_at: v5.15.5.F.4d.1.B.4 WIP-15 (2026-05-27; structural by-construction closure — BACKTEST_REGIME_SAMPLE_CORE named constant in EngineCommon.hpp:64-75 preserves pre-.B.4 sample_regimes=0 semantic via single canonical core read; 4th consumer added at BacktestSharded.hpp:430 per F-4 closure; engine commit 4c48d5d; ledger update at .B.4 post-ship-audit 2026-05-27 per close-session Stage 8). Verification PENDING: `/parity-check` regression-free run after paper-test session.
related_specs: [DESIGN_SPECS/meta-disciplines/train-serve-execution-layer-parity.md (Stage 3 first canonical at .B.4)]
```

- **Found:** 2026-05-24 ML↔LIVE structural sweep
- **Severity:** HIGH — silent train-serve drift on per-core-regime-aware cfg shapes; affects ANY operator using per-core `regime_hysteresis` overrides
- **Class:** DIVERGENT FIELDS asymmetry (single-state vs per-core-state)
- **Site(s) (v1.7.5 LINE-NUMBER CORRECTION 2026-05-26 PM per HEAD `e0acb65` post-C.1+C.2+C.3 line shifts; sister to GAP-COHORT-3 4th-consumer addition from v1.7.5 pre-amendment /trace-deps audit):**
  - Live: `CoreFrameworks/ControllerEventLoop.hpp:2641` — `ml_ctx.current_regime_id = state->cores[slot].regime_state.current_regime` (per-core regime state per inference call) [unchanged]
  - Backtest (4 consumers; was 3 pre-v1.7.5):
    - `:423` — allocates SINGLE `fc_ctx.regime_state` (not per-core; was `:541-548` pre-C.1 shift)
    - `:430` — `Regime_Init(&fc_ctx.regime_state, (int)cfg.regime_hysteresis)` (4th consumer; **NEW v1.7.5 enumeration**; was MISSED in pre-v1.7.5 enumeration — sister to v1.4 N5 anti-pattern that B-Plus v0.4 deletion-target consumer-enumeration check closes structurally)
    - `:489` — `Regime_Classify(&fc->regime_state, &sig, fc->cfg)` (write site; was `:607` pre-C.1 shift)
    - `:494` — `ctx.current_regime = fc->regime_state.current_regime` (collapse N→1 read; was `:612` pre-C.1 shift)
- **Symptom:** Per-core configs with different `regime_hysteresis` train features with ONE collapsed regime; live serves N separate regimes. `regime_class_onehot` + downstream regime-context features systematically drift between training matrix + serve-time inference.
- **Root cause:** Backtest feature-compute path was simplified to single regime state for simplicity; per-core regime overrides feature came later but never extended backtest collection.
- **Fix path:** Phase C.4.5 closure per v1.7.5 amendment — DELETE all 4 consumers + ADD `ctx.current_regime = state.cores[BACKTEST_REGIME_SAMPLE_CORE].regime_state.current_regime` (per `EngineCommon.hpp` v1.3 named constant). Per-core regime state populated inside `EngineCommon_SlowPathCycleOneCore` body LANDED at WIP-11 LIVE; same body via SlowPathCycleAllCores populates BACKTEST at WIP-13. ~22-25 LOC delta. Folds into TECH_DEBT-119 C1.
- **Target ship:** `v5.15.5.F.4d.1.B.4`
- **Status:** CLOSED at `v5.15.5.F.4d.1.B.4` WIP-15 (YAML `closed_at:` above has WIP-detail; prose sync 2026-05-27 per Stage 4.5 finding)
- **Workaround:** (pre-closure historical) Operator should avoid per-core `regime_hysteresis` overrides (use same value across all cores) until fix lands.

---

### PARITY-032 — Backtest BREAKEVEN_ON_PROFIT bitmap-gated dispatch missing (live serves; closed at v5.15.5.F.4d.1.B.4 WIP-11)

```yaml
id: PARITY-032
title: Backtest path missing BREAKEVEN_ON_PROFIT lifecycle-bitmap-gated SL ratchet (live serves via per-core slow-path dispatch)
surface_tags: [slow-path, backtest, lifecycle-cfg-flags, breakeven-on-profit, train-serve-asymmetry]
severity: medium
parity_axis: live↔backtest (backtest missing dispatch)
status: closed
detected_at: v5.15.5.F.4d.1.B.4 Phase A audit cycle (2026-05-24)
closed_at: v5.15.5.F.4d.1.B.4 WIP-11 (2026-05-26; engine commit e0acb65; LIVE slow-path migration to EngineCommon_SlowPathCycleOneCore body via D1-B FOREACH_SLOW_PATH_GATE BREAKEVEN_ON_PROFIT cached-gate dispatch); BACKTEST mirror closes by-construction at WIP-13 (Phase C.4 BACKTEST migration to same EngineCommon_SlowPathCycleAllCores call)
related_specs:
  - DESIGN_SPECS/refactor-patterns/slow-path-gate-registry-pattern.md (Stage 3 first-canonical 2026-05-10/v5.14.9.B.0; D1-B applies cache pattern to breakeven for first time)
  - DESIGN_SPECS/refactor-patterns/branchless-dispatch-discipline.md (H20; D1-B sister-instance per cached-gate pattern, NOT new Class 28 hand-wave)
  - DESIGN_SPECS/meta-disciplines/train-serve-execution-layer-parity.md (M5; this ship is first canonical)
```

- **Found:** 2026-05-24 v5.15.5.F.4d.1.B.4 Phase A audit cycle (during EngineCommon helper-extract surface enumeration); decision log F8 + D1-B
- **Severity:** MED — silent train-serve drift on operators with `MASK_LIFECYCLE_CFG_BREAKEVEN_ON_PROFIT` SET in `cfg.lifecycle_cfg_flags`; backtest projections systematically miss the breakeven SL ratchet that live executes; affects backtest fidelity for operators tuning breakeven-based exits
- **Class:** Class 18 sister mirror (live serves via per-core slow-path dispatch; backtest missing equivalent dispatch); also addresses Class 28 by NOT introducing new branch (D1-B sister-instance per H20 branchless-dispatch-discipline via cached-gate pattern)
- **Site(s):**
  - Live (LANDED at WIP-11 engine commit `e0acb65`): `CoreFrameworks/EngineCommon.hpp` `EngineCommon_SlowPathCycleOneCore` body invokes `EventLoop_BreakevenOnProfitOneCore` between TrailingSLRatchet + TRAIL_SL bracket, gated via `BITMAP_IS_SET(state.global_gate_state.flags, MASK_BREAKEVEN_ON_PROFIT)` (cached per FOREACH_SLOW_PATH_GATE BREAKEVEN_ON_PROFIT row scope=ENGINE_WIDE + AUTOPOPULATE_ENGINE_WIDE at body entry)
  - Backtest (LANDS at WIP-13): same `EngineCommon_SlowPathCycleAllCores` body via Phase C.4 BACKTEST migration — by-construction closure
  - Pre-`.B.4` LIVE site: `CoreFrameworks/ControllerEventLoop.hpp:3796-3804` `EventLoop_BreakevenOnProfit` wrapper called from centralized-arch trio (DELETED as cohort at WIP-14 per Class 18 cohort wrapper deletion rationale)
- **Symptom:** Pre-`.B.4`: operators running backtest with `MASK_LIFECYCLE_CFG_BREAKEVEN_ON_PROFIT` SET saw no breakeven SL ratchet in simulation; live execution applied it; backtest underestimated win-rate + overestimated drawdown for breakeven-positive trades.
- **Root cause:** v5.14.9.B.0 introduced FOREACH_SLOW_PATH_GATE registry pattern as first-canonical structural-fix for slow-path-gated dispatch; BREAKEVEN_ON_PROFIT was added as cfg flag but never enrolled in registry (manual wrapper only). Sister to Class 18 mirror — backtest path never extended to match live wrapper add.
- **Fix path:** Phase B.3a + WIP-7 added BREAKEVEN_ON_PROFIT row to FOREACH_SLOW_PATH_GATE registry; WIP-11 LIVE slow-path migration moved dispatch into EngineCommon_SlowPathCycleOneCore body with cached-gate predicate; WIP-13 BACKTEST migration via Phase C.4 EngineCommon_SlowPathCycleAllCores call closes mirror by-construction; WIP-14 deletes ControllerEventLoop.hpp:3796-3804 wrapper as part of Class 18 cohort wrapper deletion. STRUCTURAL CLOSURE — class 18 mirror replaced by single-source-of-truth dispatch in EngineCommon.
- **Target ship:** `v5.15.5.F.4d.1.B.4`
- **Status:** CLOSED (LIVE LANDED at WIP-11 engine commit `e0acb65`; BACKTEST mirror closes by-construction at WIP-13 Phase C.4 migration; wrapper deletion at WIP-14 closes Class 18 cohort)
- **Verification:** parity_harness regression at WIP-15 Phase C.6 with `MASK_LIFECYCLE_CFG_BREAKEVEN_ON_PROFIT` cohort tests live↔backtest dispatch byte-for-byte identical
- **NEW canonical for catalog:** First application of slow-path-gate-registry-pattern to BREAKEVEN_ON_PROFIT lifecycle cfg flag; sister to MASK_LAZY_REBUILD_ACTIVE (canonical at ControllerEventLoop.hpp:2344) + MASK_WS_FLATTEN_ACTIVE (canonical at :3558) ENGINE_WIDE scope precedents.

---

```yaml
id: PARITY-033
title: per-core fee_rate_taker historical calibration tainted-results advisory (Class 26 sub-shape A + B closure at .B.7+.B.8)
surface_tags: [accounting, per-core-indexing, fee-floor, slow-path, historical-calibration, documented-risk]
severity: documented-risk
parity_axis: historical operator calibration vs post-fix execution
status: open
detected_at: v5.15.5.F.4d.1.B.8 (2026-05-27; retroactive closure of `.B.7` forward-promise that was never written)
related_specs:
  - DOCS/recurring-bug-patterns/class-26-global-consumer-reading-per-core-field.md § Sub-shapes (Class 26 sub-shapes A + B)
  - DESIGN_SPECS/meta-disciplines/structural-enforcement-when-memory-insufficient.md v1.3 (Check 9 + Check 10 canonical_applications)
  - tools/check_per_core_registry_integrity.py Check 9 (sub-shape A) + Check 10 (sub-shape B)
  - memory/feedback_forward_promise_auto_write_verification.md (this entry retroactively closes `.B.7` forward-promise)
```

- **Found:** 2026-05-27 v5.15.5.F.4d.1.B.8 ship close per NEW `feedback_forward_promise_auto_write_verification` discipline (retroactively closes `.B.7` Class 26 catalog line 98 forward-promise that promised DOCUMENTED-RISK PARITY entry but was never written; sister to NEW `feedback_sister_cohort_amendment_completeness` discipline at AMENDMENT layer)
- **Severity:** DOCUMENTED-RISK — no production bug post-fix (Class 26 sub-shape A closed at `.B.7` Async.hpp:814+853 + sub-shape B closed at `.B.8` ControllerEventLoop.hpp:3605+3670+3042 + StrategyLifecycle.hpp:272 + ShardedSnapshot.hpp:249); ADVISORY for historical operator calibration runs
- **Class:** Class 26 sub-shape A (WRONG-INDEX paired-access; Check 9 catches mechanically) + Class 26 sub-shape B (UNINDEXED-GLOBAL at per-core consumer site; Check 10 catches mechanically)
- **Symptom:** Operators using per-core fee_rate_taker calibration sweeps over `partial_exit_pct` / `tp2_mult` / SL settings PRIOR to `.B.7` (sub-shape A fixes) + `.B.8` (sub-shape B fixes) may have produced tainted results — calibrations tuned against silently-miscalibrated per-core fee_rate_taker behavior. Affected operators: any using per-core fee_rate_taker values DIFFERENT from each other AND running calibration sweeps over P&L-sensitive cfg fields (partial_exit_pct / tp2_mult / SL ratchet thresholds / breakeven thresholds / etc.).
- **Root cause:** Class 26 silent realized-P&L drift introduced at `.F.4c.3` WIP2d-1.B.1 mechanical migration commit `ea08210` (per-core fee_rate migration missed sub-shape A WRONG-INDEX at Async.hpp drainer body + sub-shape B UNINDEXED-GLOBAL at slow-path fee-floor compute paths). Effect: per-core fee_rate_taker silently flattens to GLOBAL value (sub-shape A: wrong index into per-core array; sub-shape B: no array indexing at all). For operators with uniform per-core fee_rate_taker (== global default), bug INVISIBLE. For operators with DIFFERING per-core fee_rate_taker, calibration sweeps produced systematically wrong P&L estimates.
- **Fix path:** Post-`.B.8`: per-core fee_rate_taker reads correctly per consumer site; Check 9 + Check 10 catch future regressions mechanically. Historical calibration runs (pre-`.B.7`+`.B.8`) may need re-validation.
- **Closure trigger:** operator re-validation at next paper-test cycle OR operator decision that historical calibrations are acceptable (e.g., production runs used uniform per-core fee_rate_taker → bug never manifested in their data → no re-validation needed)
- **Target ship:** N/A (advisory; closure trigger is operator-decided)
- **Verification:** Class 26 catalog Worked Examples documents both sub-shapes A + B closures with exact line refs; Check 9 + Check 10 in `tools/check_per_core_registry_integrity.py` CI-enforce prevention; 16 NEW regression tests at `.B.8` Phase E verify per-core fee_rate_taker reads at all 4 HIGH consumer sites
- **Sister to:** PARITY-026 (similar shape — live-safety hole at kill_switch closed at `.B.2.h1` hotfix; sister discipline of catching silent live-trading bugs at audit time)

---

```yaml
id: PARITY-034
title: cfg-parser locale-fragile atof cluster (~35 unmigrated MANUAL_PARSER FPN cfg fields)
surface_tags: [cfg-parse, locale, determinism, backtest-live-parity, slow-path, boot]
severity: documented-risk
parity_axis: cross-locale cfg parse (C vs non-C) + backtest↔live parser symmetry
status: open
detected_at: v5.15.5.F.4d.1.E.0.1 hardened-gate audit (2026-05-29)
related_specs:
  - CoreFrameworks/ParseFast.hpp (the locale-immune parse_double_fast the registry path already uses)
  - DESIGN_SPECS/wire-format-patterns/wire-format-byte-preservation-discipline.md
```

- **Found:** `.E.0.1` hardened-gate audit (parity quorum 3/3 + verification). ~35 FPN cfg fields parse via locale-dependent `atof` (`ControllerConfig.hpp:~2147-2357`, the unmigrated MANUAL_PARSER branch); NO `setlocale(LC_NUMERIC,"C")` in any `main()`. The registry-migrated fields already use locale-immune `parse_double_fast` + per-thread `uselocale` (`CfgFieldDispatch.hpp:188`) → the parser is MIXED, so the SSoT "ONE parser" claim is aspirational.
- **Severity:** DOCUMENTED-RISK — under the CI's fixed-C locale `atof ≡ from_chars` byte-for-byte (verified `controller_test.cpp:15209` uses atof as its own oracle); cross-locale-fragile. NOT net-gating for `.E.0.1` (no net test loads cfg under a foreign locale).
- **Fix path:** `.E.0.3` — migrate to the `tt::` parse primitive; the manifest CI guard closes the class (cfg seeded KNOWN-PENDING).
- **Target ship:** ~~`.E.0.3` (deterministic-IO foundation)~~ **STALE — `.E.0.3` SUBSUMED (O-2/D-108, 2026-05-30):** money-row members of the atof cluster → Ship B (money-numeric-core) #5/M1 exact `FromString`; non-money remainder → TECH_DEBT-144 guard-tracked paced migration. (Annotated 2026-06-09 Ship-B `/parity-check`.)
- **Cross-ref:** decision-log D-84/D-86; [[feedback_close_the_class_vs_migrate_every_site]]; PARITY-036 (the recorder/replay locale loop).

---

```yaml
id: PARITY-035
title: Fingerprint_Compute raw-byte SHA-256 over un-zero-init ControllerConfig padding (non-deterministic model lineage)
surface_tags: [ml-lineage, fingerprint, h9, h12, determinism, byte-equivalence]
severity: high
parity_axis: cross-run / cross-binary model-fingerprint reproducibility
status: closed
detected_at: v5.15.5.F.4d.1.E.0.1 hardened-gate audit (2026-05-29)
related_specs:
  - DESIGN_SPECS/wire-format-patterns/struct-padding-determinism-pattern.md (H12 — the spec to EXTEND for enforcement)
  - Backtest/Fingerprint.hpp:170-180 (the raw-byte hash; comment CLAIMS canonical field-serialize)
```

- **Found:** `.E.0.1` audit (parity quorum 3/3 + verification empirical: two identical-value configs in differently-dirtied buffers → 16,961/68,224 differing bytes; copy-assign still leaves 9). `Fingerprint_Compute` SHA-256s raw `ControllerConfig` bytes; struct is default-init (not zero-init), mixed-alignment, no `_padding=0` (H12). Consumer: `BacktestPanels.hpp:3157` → `XGBoosterSetAttr("foxml_fingerprint")` → read at `ModelInference.hpp:509` (+ `CoreModelZoo` ComputeBundleId, which IS fatally compared — but reads the embedded string both sides, so lineage-break is low-harm).
- **Severity:** HIGH — non-deterministic model lineage (H9/H12). The header comment (`:170`) claims "serialized in sorted order for canonical hashing" but the code raw-hashes — an SSoT claim-vs-behavior violation.
- **Fix path:** `.E.0.3` — `Fingerprint_CanonicalizeConfig` field-wise into a zeroed buffer (strlen not sizeof for char[]; hash FPN limbs not via ToDouble; preserve the fee_rate-not-maker/taker bundle invariant at `ControllerConfig.hpp:369-370`) + a `static_assert(sizeof==EXPECTED)` coverage-sentinel. CONFIRMED an instance of a recurring H12 class (Class candidate; decision-log D-87).
- **Target ship:** `.E.0.3` (or fold to Net-1 if it golden-masters the fingerprint).
- **Cross-ref:** decision-log D-85/D-87; finding F-076; PARITY-036.
- **Resolution (CLOSED, `.E.0.1` 2026-05-31):** fixed by the zero-init **constructor** `ControllerConfig() { memset(this,0,sizeof(*this)); }` (`ControllerConfig.hpp:371`, committed `4f6a4ec`) — the F-076 design audit chose this (Option A) over the field-wise canonicalize in the Fix-path above (Option B, REJECTED: over-engineered + Class-18-drift-prone on the mixed struct). The struct is padded (`alignas(64)` H6 fields); the ctor zeroes fields + padding at construction → raw hash deterministic for equal field VALUES. (`has_unique_object_representations` does NOT apply to a padded struct — that guard is StampT's, for padding-free `FPN`; a stray agent-authored static_assert asserting it was discarded at ship-close, see postmortem.) Verified: fresh clean build 3241/0 + the `controller_test` characterization checks. Folded into `.E.0.1` (was routed `.E.0.3`).

---

```yaml
id: PARITY-036
title: replay write∧read locale loop — recorder %.8f emit + strtod parse (locale-fragile AND lossy)
surface_tags: [replay, recorder, locale, determinism, backtest-live-parity, lossy-emit]
severity: high
parity_axis: replay determinism (write∧read locale immunity) + backtest↔live parse symmetry
status: closed
detected_at: v5.15.5.F.4d.1.E.0.1 hardened-gate audit (2026-05-29; completeness-critic)
related_specs:
  - DataStream/TickRecorder.hpp:186 + DataStream/DepthRecorder.hpp:249 (the %.8f emit)
  - Backtest/BacktestEngine.hpp:88-96 + DataStream/DepthReplayState.hpp:224-227 (the strtod parse)
```

- **Found:** `.E.0.1` audit completeness-critic. Replay determinism requires write∧read locale-immunity. The recorders WRITE the replayed CSVs with bare `fprintf("%.8f")` (locale-fragile AND lossy — `%.8f` truncates a `double`, doesn't round-trip); the readers PARSE with locale-dependent `strtod`. No process `setlocale`. The golden-master (generated by these recorders) would be corruptible across locales, and the replay-locale CI gate as specced tests PARSE-symmetry only → write side uncovered.
- **Severity:** HIGH — would falsify the ship's own determinism premise if left. No existing recordings (so no byte-compat constraint — free to choose round-trip-exact / raw-string).
- **Fix path:** `.E.0.1` — replay parse → `parse_double_fast` (F-054/55) + recorder emit → `to_chars` shortest-round-trip (locale-immune + kills the `%.8f` precision loss). `.E.0.3` — the raw-string-record end-goal (store bytes, defer parse) + the unified primitive.
- **Target ship:** `.E.0.1` (parse + emit) + `.E.0.3` (raw-string end-goal).
- **Cross-ref:** decision-log D-85/D-86; findings F-054/F-055; PARITY-034.
- **Resolution (CLOSED, `.E.0.1` 2026-05-31):** the `.E.0.1`-scoped write∧read locale loop is closed — replay PARSE → `tt::parse_double_fast_advance` (F-054/55) + recorder EMIT → `std::to_chars` shortest-round-trip (locale-immune, kills the `%.8f` precision loss); committed `2c8830a`/`69f295e`, covered by the replay-locale gate + the determinism net (clean-build verified; gates GREEN). The `.E.0.3` raw-string-record end-goal (store bytes, defer parse) is a separate future enhancement, not this issue's open state.

---

```yaml
id: PARITY-037
title: KIND_DOUBLE_PCT registry defaults stored percent-form vs cfg_assign_field/cfg_diff_field fraction-read (no PCT scaling) — latent 100x money-rate misassign, masked by manual-init ordering
surface_tags: [cfg-defaults, registry-default-ssot, accounting, fee-rate, gui-settings, money]
severity: medium
parity_axis: registry-default ↔ runtime-cfg ↔ GUI agreement (money rates)
status: closed
detected_at: v5.15.5.F.4d.1.E Ship-B pre-coding /parity-check (2026-06-09)
closed_at: Ship-B P0.3 (2026-06-10; D-177)
related_specs:
  - DESIGN_SPECS/framework-patterns/universal-cfg-field-registry-pattern.md § Registry-default precedence (the SSoT rule that ARMS this)
  - CoreFrameworks/CfgFieldDispatch.hpp:240-242 (cfg_assign_field "default is stored as fraction" contract) + :283 (cfg_diff_field same asymmetry)
```

- **Found:** Ship-B (decimal money) pre-coding `/parity-check` (2026-06-09; report `plans/v5.15-live-readiness/plan_checks/parity-check-2026-06-09-ship-b-money.md` finding F5).
- **Severity:** MEDIUM — latent today (no production drift); escalates to money-corrupting if armed (see Root cause).
- **Symptom:** KIND_DOUBLE_PCT money rows store `as_double.default_val` in PERCENT form — `fee_rate_maker` `DBL(0.075,…)` / `fee_rate_taker` `DBL(0.100,…)` (`CfgFieldRegistry.hpp:674-675`; tooltips confirm percent), `ml_tp_pct` `DBL(2.0,…)` / `ml_sl_pct` `DBL(1.0,…)` (`:552-553`) — but `tt::cfg_assign_field` (`CfgFieldDispatch.hpp:240-242`) assigns `FromDouble(default_val)` with NO PCT scaling per its documented "default is stored as fraction" contract → boot default-fill walker (`ControllerConfig.hpp:1498/1505`) writes `fee_rate_taker = 0.1` (= 10% fee, 100× the intended 0.100%). `cfg_diff_field` (`:283`) has the same asymmetry (permanent "modified" badge for PCT money rows). Sister symptom: `cfg_save_field` PCT save (`:193-197`, `v×100` → `%.2f`) is value-mutating for sub-precision rates (default maker 0.00075 → "0.07" → reload 0.0007).
- **Root cause:** percent-vs-fraction convention mismatch between the PCT rows' registry payload and the assign/diff dispatchers' fraction contract. MASKED today purely by ordering: the manual inits at `ControllerConfig.hpp:1527-1528` (`FPN_FromDouble(0.00075/0.00100)`, fraction-form) run AFTER the walker and overwrite. ARMED by: (a) the registry-default-SSoT sweep deleting the masking manual inits, (b) wiring GUI reset-to-defaults through `cfg_assign_field` (`SettingsPanel.hpp:140` notes the primitives shipped for exactly that).
- **Fix path:** pin ONE convention at Ship B (decimal money) while writing the decimal parse/assign/save/diff branches — recommend normalizing `as_double.default_val` to fraction-form for all KIND_DOUBLE_PCT rows (matches the assign contract + wire semantics), OR add PCT scaling to assign/diff; either way add a walker test comparing assign-default vs manual-init vs `parse("default-as-percent")` for every PCT row, and make the decimal save branch emit the exact decimal string (not `%.2f`/`%.4f`).
- **Target ship:** Ship B (money-numeric-core; the decimal dispatcher branches are where the convention gets baked).
- **Workaround:** none needed today (manual inits mask); do NOT delete `ControllerConfig.hpp:1527-1528` (or sister PCT manual inits) under the registry-default-SSoT sweep before this is fixed.
- **Cross-ref:** Ship-B plan B3/B6 (dispatcher decimal forks); `feedback_single_source_of_truth_discipline`; PARITY-033 (sister fee_rate_taker surface).
- **RESOLUTION (Ship-B P0.3, 2026-06-10 — D-177; the framing INVERTED by full-cohort enumeration):** the DBL payload column proved COHERENTLY PERCENT-SPACE (~20 PCT rows + their 0-100 clamp ranges + the file convention `cfg_parse_field` ÷100 + the per-core manual parser `:2840` ÷100 + the GUI ×100 display all agree) — the wrong side was `cfg_assign_field`/`cfg_diff_field` and their "default is stored as fraction" contract comment, NOT the row data as this entry recommended. Fix: ÷100 PCT scaling added to BOTH dispatchers (mirroring the file parser) + the ONE fraction-authored outlier row `lazy_rebuild_price_threshold_pct` re-authored percent-form (`DBL(0.0005,0,0.1)`→`DBL(0.05,0,10.0)`, value-identical through the new scaling — it was also the one row already living UNMASKED on the registry default, and its FILE-parse path was live-wrong 100× pre-fix). Suite 3246/0; boot values byte-unchanged; GUI reset/diff/--changed-only go from 100×-wrong to correct. The Workaround's "do NOT delete manual inits" hold is LIFTED. Residuals ride P2 by design: `cfg_save_field` exact-decimal-string (S-15) + the cfg-file→stored round-trip over all money rows (D-100 gate row).

```yaml
id: PARITY-038
title: per-core vs OMS realized-P&L gross formula divergence (DrainPostFill 2-mul vs books 1-mul)
surface_tags: [accounting, money, realized-pnl, slow-path, decimal-epoch, single-source, drainer]
severity: high
parity_axis: per-core core_realized vs OMS realized_pnl (same-run, same-fills reconciliation)
status: closed
detected_at: v5.15.5.F.4d.1.E.0.10 (2026-06-10; adversarial audit of the Net-1 characterization tests)
related_specs:
  - decision log D-190 (amends D-105)
  - memory/feedback_single_source_the_computation_not_just_the_mode.md
  - memory/feedback_passing_test_is_not_verification.md
```
**Symptom:** the per-core `core_realized` sum does not reconcile `oms.realized_pnl` exactly — they drift by 1 ULP (1e-8) on ~25% of realistic fills, accumulating over the run.

**Root cause:** the realized-P&L gross was open-coded in 3 sites with 2 different formulas. `DrainPostFill` (`ControllerEventLoop.hpp:1536`) computed `round(exit×qty) − round(entry×qty)` (2-mul) while `Portfolio_CloseSlot:395` + mode-0 `:880` + `EventLoop_OnEvent:1962` use `round((exit−entry)×qty)` (1-mul). Under decimal half-even the two diverge. **PREEXISTING** (FPN era `.E.0.6`, ~1e-19 gap, invisible); the Ship-B P2b decimal flip (838bf09) activated it. D-105 fixed the rounding MODE uniformly but missed the FORMULA split + the DrainPostFill site (D-190). Sister landmine: LANDMINES.md Landmine 8.

**Fix path:** NEW canonical `Money_FillGross` (1-mul SSoT, `Portfolio.hpp:397`) — ALL 5 price-diff gross sites (3 realized + 2 unrealized) route through it → reconcile by construction. Regression guard in `controller_test` pins the 1-mul/2-mul divergence as real (catches a reverted formula). LANDED at v5.15.5.F.4d.1.E.0.10 (D-190); suite 3290/0.

**Status:** closed (v5.15.5.F.4d.1.E.0.10; D-190). Pending a confirming `/parity-check` + the backtest-golden regen check (D-105-flagged; unit suite is clean — clean inputs don't diverge).

**Cross-ref:** D-190; D-105 (the incomplete predecessor decision); AP4 (rounding-mode anti-pattern, extended to formula-SSoT); `feedback_single_source_the_computation_not_just_the_mode`.

---

```yaml
id: PARITY-039
title: warm-restart recomputes TP/SL from the GLOBAL take_profit_pct while live entry uses the per-strategy override
surface_tags: [snapshot-restore, tp-sl, per-strategy-override, scale-invariance, slow-path, warm-restart]
severity: high
parity_axis: live entry TP/SL vs post-warm-restart restored TP/SL (same position, same node)
status: closed
detected_at: v5.15.5.F.4d.1.E.0.10 (2026-06-11; Net-1 adversarial money-surface bug-hunt, 5 surface-blind agents)
related_specs:
  - DESIGN_SPECS/data-disciplines/per-node-purity-scale-invariance.md (H22 — this is instance A1)
  - plan_checks/E.0.10-finding-disposition-register.md § bug-hunt A1
```
**Symptom:** A SimpleDip/MR/EmaCross position exits at a DIFFERENT TP/SL after a warm restart than it would have while live — whenever the per-strategy override is set.

**Root cause:** snapshot-restore recomputed `live_tp` / `live_sl` / `live_tp_b` from the GLOBAL `take_profit_pct` (`ShardedSnapshotPersist.hpp:653`), while the live entry path uses the per-strategy override (`simpledip/mr/emacross_tp_pct`, `StrategyParameters.hpp:327`). `ControllerConfig_ResolveForCore` (`:1383`) did not fold the override, so the two paths read different sources for the same quantity.

**Why it is H22 (not merely a restore bug):** this is the canonical **A1** violation of per-node purity — a per-shard path reading a GLOBAL cfg field that HAS a `core_N_*` override. The scale-invariance discipline exists because of this class.

**Resolution:** FIXED 2026-06-11 in `.E.0.10`. Single-sourced via `ResolvePerFillTpPct` / `ResolvePerFillSlPct` across BOTH entry and restore. SimpleDip+MR cohort char-tests GREEN; suite 3368/0; 3-agent independent refute returned SOUND/CORRECT; sealed by orchestrator on the `ResolveForCore` read with 2 agents converged. Momentum/ML were unaffected (`out->tp_pct == take_profit_pct`). TECH_DEBT-168 closed with it.

**Provenance of THIS entry (2026-07-20):** the finding was recorded only as an audit-log bullet in this file (see the 2026-06-11 line in the Audit log below) and never given a defining `id:` row, so `PARITY-039` read as CITED-BUT-UNDEFINED to the citable-ID guard while its content sat in the same file. Every field above is transcribed from that bullet and the disposition register it cites — no history was reconstructed. The formatting defect, not the finding, was what was missing.

---

```yaml
id: PARITY-040
title: trail anchor original_tp non-reproducible across event-log replay (live fill-priced vs replay e.tp expected-entry-priced)
surface_tags: [oms, event-log-replay, trail-stop, original_tp, decision-time-binding, reconstruct-path, class-45]
severity: low-med
parity_axis: live original_tp (fill-priced) vs event-log-replay reconstruct original_tp (expected-entry-priced)
status: open-deferred
detected_at: v5.15.5.F.4d.1.E.0.10 (2026-06-12; A25 pre-impl DECISION #5 + the A25-close armed deep-check M1)
related_specs:
  - decision log D-208 (the #5 resolution = option b) + D-204/D-205 (A25)
  - DOCS/recurring-bug-patterns/class-45-reconstruct-path-reads-different-source-field.md
  - DESIGN_SPECS/refactor-patterns/decision-time-data-binding-pattern.md (v1.3 reconstruct corollary)
```
**Symptom:** Post-A25 the LIVE entry path arms the trail anchor `Position::original_tp` FILL-priced (`handle_buy_fill`: `original_tp = fill×(1+tp_pct)`). The event-log REPLAY reconstruct (`Portfolio_FromEventLog`, `OrderEventLog.hpp:726/732`) rebuilds `original_tp` from the logged `e.tp`, which the append site writes EXPECTED-ENTRY-priced (`e.tp = o->intended_tp`). → a position whose entry slipped arms its trail at the fill price live, but reconstructs it at the expected-entry price on an event-log replay → **live ≠ replay** for `original_tp`. Class 45 (reconstruct path re-derives from a different source field than the forward path).

**Root cause:** `OrderEvent` persists the expected-entry `intended_tp`, not the fill-priced TP; the fold has no access to the fill-priced anchor A25 introduced. The forward (live) and reconstruct (replay) paths single-source `original_tp` from DIFFERENT fields.

**AMENDMENT 2026-08-15 (D-421 step 2) — a SECOND way the same log diverges, found while verifying the NodeContext persist exemptions.** Exits are not permission-gated (`ExecutionCore.hpp`: `can_enter` consults `perm`, `can_exit_a/b` do not), and the snapshot loader sets `active = 1` and arms `live_tp`/`live_sl` directly on the ExecutionCore. So a snapshot-restored position **can exit on the first tick, before any slow-path rebuild has run** — and that exit path reads `ctx.intended_tp` / `intended_sl`, which are still `Money_Zero()` from init. `OrderManager_HandleFill` appends them to the audit log unconditionally, so that `OrderEvent` carries `tp=0, sl=0`.

**No capital impact** — `handle_sell_fill` never reads them; only `handle_buy_fill` does. But a replay over a log containing such a record reconstructs `original_tp` from a logged **zero** rather than from a merely-differently-sourced value, which is a strictly worse input than the divergence this entry already tracks. Both are fixed by the same move (persist/log the fill-priced anchor, or gate the append on a derived-this-pass predicate), so they should be closed together rather than separately. Evidence: `plans/v5.15-live-readiness/reports/2026-08-15-nodectx-exemption-verification/P2-eval-transient-display.md` § C F-4.

**Reachability (AR-11 code-read, D-208):** LOW-MED, confined to the SECONDARY replay path. The fold IS reached by a production caller (`OMS_INIT_AUTOPOPULATE` Layer 4, `OmsFieldRegistry.hpp:741-744`, `event_log_mode==1`-gated), BUT `original_tp` is also persisted in the binary snapshot (`ShardedSnapshot.hpp:248`, the PRIMARY recovery) and live recovery uses Reconcile, not replay (`Run.hpp:974` "Live mode skips load" → `:1019`). The primary recovery preserves the fill-priced anchor; only the secondary event-log-replay reconstruct diverges.

**Decision (D-208 = option b):** DOCUMENT the non-reproducibility (this entry) + have F-059 (the exit-chain golden-master) FREEZE-FLAG `original_tp` as non-byte-reproducible across replay. NO `OrderEvent` format-version bump now — the structural single-source (persist the fill-priced TP on `OrderEvent` + H21 event-log VERSION bump + tombstone the old field) couples to the deferred version rework (TECH_DEBT-126), so forcing it now is wrong. Structural fix rides the version rework.

**NOT a backtest↔live divergence (F2 verified-FALSE 2026-06-12, code-read):** the sharded BACKTEST shares the live submit producer (`Async.hpp:909` sets `cmd.tp_pct`) AND the live fill path (`handle_buy_fill`; `event_log_mode==1` "same fill+drain" per `BacktestSharded.hpp:162-189`, for train-serve parity) → backtest `original_tp` is fill-priced, IDENTICAL to live. The deep-check's "backtest never sets cmd.tp_pct" (F2) was refuted by grounding: the only set-site `Async.hpp:909` is the SHARED producer, not live-gated, and `handle_buy_fill` is not `event_log_mode`-gated. The only expected-priced path is this replay reconstruct, which applies equally to live and backtest on restart — there is no backtest-SPECIFIC gap.

**Status:** open-deferred. Homed: D-208 (option b documented here), F-059 freeze-flag, TECH_DEBT-126 version-rework (the structural fix).

**Cross-ref:** D-208 / D-204 / D-205; RBP Class 45; F-059; `decision-time-data-binding-pattern.md` v1.3; A25 (the live fill-priced anchor this is the reconstruct-twin of).

---

## Audit log

- **2026-05-10** — `/parity-check` audit of v5.14.10 Thompson bandit plan (pre-coding gate). 3 new findings written: PARITY-013 (HIGH), PARITY-014 (HIGH), PARITY-015 (MEDIUM). Verdict: YELLOW (proceed with 4 plan amendments before scope-lock). Full audit report: `plans/plan_checks/parity-check-2026-05-10-v5.14.10-thompson-bandit.md`.
- **2026-05-11** — `/parity-check` audit of v5.14.11 online-corr-update plan (pre-coding gate). 3 new findings written: PARITY-016 (HIGH), PARITY-017 (HIGH), PARITY-018 (MEDIUM) + 1 LOW (stamp-binding eligibility — Document-only, not assigned PARITY-NNN). Verdict: YELLOW (proceed with ~60 min plan amendments before .A code starts). Default-off bytewise-identity to v5.14.10 confirmed (cfg=0 takes BuildCorr branch unchanged). No train↔serve handoff surface added. Both BuildCorr call sites flagged in plan REUSE claims (buy-side at StrategyParameters.hpp:996 + exit-side at :1195). Full audit report: `plans/plan_checks/parity-check-2026-05-11-v5.14.11.md`.
- **2026-05-10** — `/parity-check` re-audit of v5.14.10 AMENDED plan (4 architectural decisions baked in + 13 mechanical fixes applied + 6-sub-tag structure .0/.A/.B/.C/.D/.E). Verdict: YELLOW (proceed with 7 mechanical plan-text fixes; ~10 min). Confirmed: PARITY-013 RESOLVED in .B Step 9 (FOREACH_STAMP_BOUND_CFG with 4 X-rows + AUTOPOPULATE auto-flow). PARITY-014 RESOLVED in .A Step 2+7 (own Box-Muller via raw mt19937_64::operator() + SHA-256-locked sample-trace test). PARITY-015 RESOLVED in .D Step 1+2+6 (5 PerCoreSnap fields with bit-packed thompson_state byte + ML Status panel branch + cfg=2 calib log via FOREACH_CALIB_LOG_COL). 2 NEW MEDIUM findings flagged as plan-text staleness (NOT new bug class): NEW-1 stale field name `ensemble_bandit_arm_probs` → actual `ensemble_weights[5][8]`; NEW-2 stale file path `EngineSharded.hpp:646-694` → actual `ShardedSnapshot.hpp:677-694` (publish writer). Both propagated from prior parity-check report; PARITY-015 entry's file path citation should be corrected. NO new PARITY-NNN entries. NEW parity surfaces (thompson_state.json wire format Layer 1-6 compliance, PerCoreSnap cluster restructure, 4 stamp-bind drift tests presence dispatch) all GREEN against discipline. Full audit report: `plans/plan_checks/parity-check-2026-05-10-v5.14.10-AMENDED.md`.
- **2026-05-12** — `/parity-check` audit of v5.15 sprint plan (pre-coding gate; HIGH-RISK v5.15.0 ModelHandle migration; MEDIUM-RISK v5.15.2 trading_mode introduction; MEDIUM-RISK v5.15.3 multi-horizon stamping; MEDIUM-RISK v5.15.4 hot-swap unification + strict defaults). Verdict: **YELLOW** (proceed with amendments before .0 / .3 / .4 coding). 4 new findings written: PARITY-020 (HIGH; train_model_worker_fn missing STAMP_CFG_AUTOPOPULATE — asymmetric with RFV across 22 cfg-bound fields; recommend bundle into v5.15.3.A as 1-LOC addition); PARITY-021 (HIGH; v5.15.3 root cause misdiagnosed — multi-horizon DOES stamp via RFV; gap is grid_member_count/_idx orphan registry placeholders never populated; recommend revised approach plumbs req_grid_member_* through FullValidationResults into RFV's existing emit path; reduces v5.15.3 scope from ~150 LOC to ~30 LOC; drops stamp_emit_for_horizon helper); PARITY-022 (MEDIUM; STAMP_MODEL_CONST_AUTOPOPULATE macro defined but self-referential — v5.15.3 plan can't use it; defer wiring to future sprint); PARITY-023 (MEDIUM; v5.15.4 HotSwapSnapshot/Revert design captures only pointers — pre-swap data destroyed in-place by Free; recommend de-scope TECH_DEBT-005 from v5.15.4 OR restructure with shadow-load). Plus 6 MEDIUM + 4 LOW findings on stale line numbers + documentation accuracy. HMAC chain integrity verified GREEN (Surface G has_* flags + appending trading_mode at registry END preserves legacy stamp byte equivalence). NaN-free feature pack chokepoint preserved. Cross-mode byte-equivalence test design needs amendment for executability (xgb_train_nthread + training_timestamp_us require explicit setup). Full audit report: `plans/plan_checks/parity-check-2026-05-12-v5.15.md`.
- **2026-05-11** — `/parity-check` re-audit of v5.14.11 AMENDED plan (post-Caramel-consult: Decision 4 cohort migration + Decision 5 (C) sliding-window Welford + (C) BuildCorr refactor + (D) Cholesky AVX-512 adopted). Verdict: **GREEN** (proceed to .A kickoff). PARITY-016/017/018 status: **PARITY-016 RESOLVED at v5.14.11.A** by structural unification + per-cfg SHA-256 baselines (cfg=0 + cfg=1 each bytewise-locked within v5.14.11; share FinalizeCorrFromSums kernel; cross-cfg tolerance ~1e-13 sum convergence). **PARITY-017 RESOLVED at v5.14.11.B for sites 1+2** (UpdateOnline outer-product + BuildCorr accumulation) via v5.11.7 discipline + per-site SHA-256 lock test; site 3 (Cholesky) split with sub-site 3c new finding (see below). **PARITY-018 RESOLVED BY ELIMINATION** — sliding-window-by-design has no periodic-reset code path; bug class cannot exist. 1 NEW MEDIUM finding: PARITY-019 (Cholesky_Solve back-solve column-access doesn't vectorize via the row-load template; needs explicit .B kickoff strategy decision). 1 LOW recommendation (NOT assigned PARITY-NNN): defensive bounded-input guard at UpdateOnline entry (production default uses BARRIER ensembles → bounded [0,1]; non-BARRIER models risk unbounded predictions → cancellation error blow-up; cheap insurance). PARITY contract reframing at line 73-79 of amended plan verified clean: 3-boundary table (v5.14.10↔v5.14.11 tolerance 1e-9 / within-v5.14.11 cfg=0↔cfg=1 tolerance ~1e-13 / scalar↔AVX-512 bytewise identical) matches the math. Stamp-binding HMAC chain integrity preserved via `BITMAP_IS_SET(...) ? 1 : 0` ternary normalization (3 ridge_* fields are confirmed boolean throughout codebase). Full audit report: `plans/plan_checks/parity-check-2026-05-11-v5.14.11-AMENDED.md`.
- **2026-05-12** — `/parity-check` audit of v5.15.5 per-horizon TP/SL serving plan (pre-coding gate). Verdict: **YELLOW** (proceed with 4 must-fix amendments before Phase A coding). 1 new PARITY entry written: PARITY-024 (HIGH; per-arm trained TP/SL barriers stamped at training but not consumed at serving; closes a v5.13.5 multi-horizon training-side ship that left the serving-side incomplete). 7 findings total: F1 LOW (Tier 1 loose-mode noise — acceptable), F2 MEDIUM (shadow JSON locale pinning missing in plan spec — add `newlocale(LC_NUMERIC_MASK, "C", 0)` per Bandit_SaveJSON precedent), F3 HIGH (missing PerCoreSnap fields for modes 3-4 — bundle `barrier_mode_used` + `barrier_shadow_event_count` into Phase A failure-mode registry extension), F4 MEDIUM (Rule 1 arm_names extraction caller enumeration — plan A.1 must list all 3-4 callers + add sizeof shrinkage static_assert), F5 DOCUMENT-ONLY (AVX-512 sizing without SHA-256 lock — vectorization correctly deferred to v5.15.6), F6 MEDIUM (Q1 fallback semantics for mixed v5.15.5+legacy ensemble — plan answer correct; add rate-limited WARN), F7 HIGH (HMAC byte preservation — barrier_blend_mode row must be APPENDED at END of FOREACH_STAMP_BOUND_CFG after `trading_mode` line 175-176). HMAC chain preservation analyzed clean if append-at-end discipline followed. Per-arm reward observability invariant (CLAUDE.md item 24) verified to HOLD under modes 3 + 4 (barriers are output policy, not the prediction grading signal). STAMP_CFG_AUTOPOPULATE handles `barrier_blend_mode` field-population across all production callers automatically (no PARITY-009-style class can recur). Bandit arm_names extraction analyzed — `Bandit_LoadJSON` does NOT round-trip arm_names so persistence path is safe; only `Bandit_Print` + `Bandit_SaveJSON` + EngineTUI legacy-bandit reader need update. Full audit report: `plans/plan_checks/parity-check-2026-05-12-v5.15.5-per-horizon-tp-sl-serving.md`.
- **2026-05-13** — `/parity-check` audit of v5.15.5.C.3 Phase 3b complete (commit d410525, post-coding gate). Verdict: **GREEN** (proceed to Phase 4 — FOREACH_CORE_CTX_SUMMARY_FIELD + JSON emitter). Focus: snapshot v8 wire-format byte-preservation (FOREACH_OMS_FIELD canonical 8-tuple registry with PERSIST view projection); kill_switch_tripped BIT+PERSIST extraction; event_log_mode int→2-bit-slot SKIP_PERSIST verification; OrderManager_Init signature change (added `int partial_exit_enabled` 4th positional). 1 new PARITY entry written: PARITY-025 (HIGH; BacktestSharded.hpp:194-201 retains stale external SET/CLR mirror for MASK_OMS_STATE_PARTIAL_EXIT_ENABLED — Class 18 mirror NOT fully eliminated by Finding A; EngineSharded was cleaned, sister site missed; ZERO behavioral impact today since both sites derive from same cfg expression, but parity hazard + documentation drift class). 5 findings total: HIGH-1 (PARITY-025), MEDIUM-1 (stale experiments — `experiments/per_core_sharding/test_oms*.cpp` 13 callers don't compile post-3b; not in `./build.sh test`; TECH_DEBT candidate), MEDIUM-2 (round-trip persist test direct-asserts only 3 of 10 PERSIST fields — ks_peak_balance + 6 v6 OMS counters not directly asserted; downstream byte-stream-corruption catches misordering indirectly; ~15 min bundle-fix), LOW-1 (event_log_mode > 1 silent 2-bit truncation; defer until mode 2-3 added), LOW-2 (no static_assert lock on PERSIST view row count = 10; ~10 min defensive lock). WIRE-FORMAT BYTE-PRESERVATION VERIFIED CLEAN row-by-row (10 PERSIST rows match legacy registry order byte-for-byte; SAVE + LOAD + COMMIT macro expansions emit identical bytes to pre-3b; sizeof(int)=4 for kill_switch_tripped wire size preserved). EVENT_LOG_MODE int field removal layout verified clean (alignas(64) cluster anchors hold; 4 byte saving per OMS). Engine/backtest parity for partial_exit_enabled derivation verified (both sites use same `BITMAP_IS_SET(cfg.lifecycle_cfg_flags, MASK_LIFECYCLE_CFG_PARTIAL_EXIT_ENABLED) ? 1 : 0`). All 4 reader sites for event_log_mode migrated correctly (BITMAP_NONE/BITMAP_ANY/MBS_EQ_U8 semantic-equivalent to pre-3b int comparisons). All production callers of OrderManager_Init (4) pass partial_exit_enabled; controller_test.cpp 16 callers + test_event_log_head_to_head.cpp 1 caller updated. Tests pass 3052/3052. ML stamp surfaces UNTOUCHED (verified). Per-arm reward observability invariant (CLAUDE.md item 24) preserved (no bandit / per-arm grading paths touched). Full audit report: `plans/plan_checks/parity-check-2026-05-13-v5.15.5.C.3-phase3b.md`.
- **2026-05-29** — hardened `/precoding-audit-gate` (Piece 4 first live firing) on `.E.0.1` (13 agents: parity ×3 quorum + trace/readiness/dod/accounting/blindspot + verification + completeness-critic). Verdict: **YELLOW**. 3 new PARITY entries: PARITY-034 (cfg-`atof` cluster, documented-risk → `.E.0.3`), PARITY-035 (F-076 fingerprint raw-byte hash, HIGH → `.E.0.3`), PARITY-036 (replay write∧read locale loop, HIGH → `.E.0.1`+`.E.0.3`). Empirically refuted R1 (native vs generic FPN<64> byte-identical at F=64 — sqrt is the sole non-conformer); quorum killed a false FPN-trace-test-breakage prediction; completeness-critic found the recorder-emit net-gating gap 7 find-lenses missed. Synthesis: `plans/v5.15-live-readiness/plan_checks/E.0.1-audit-reports/2026-05-29-E.0.1-fresh-audits-synthesis.md`.
- **2026-06-09** — `/parity-check` audit of Ship B (decimal money) — money-numeric-core foundation plan v0.3, pre-coding gate (HEAD `0e48150`, 3246/0; scoped to Ship-B remaining work per gate invocation; decided set D-97..D-167 honored). Verdict: **YELLOW**. 1 new PARITY entry: PARITY-037 (MEDIUM; KIND_DOUBLE_PCT percent-form registry defaults vs unscaled cfg_assign/diff — latent 100× money-rate misassign, masked by manual-init ordering). Top findings: F1 HIGH — `cfg_drift_compare`/`cfg_drift_format_reason` static_assert covers StampT ONLY + no always_false final-else (`CfgFieldDispatch.hpp:456-461/:486`, `:505-510/:532`) → `cfg_drift_compare<double, FixedPoint<10,8>>` COMPILES and silently returns no-drift via the walker at `CoreModelZoo.hpp:238` — B3's "silent → compile-error" claim is FALSE for the two-template dispatchers; sequence B6's exhaustive-else BEFORE/WITH the money flip. F2 HIGH — no mechanical pre-epoch stamp rejection (`STAMP_FORMAT_VERSION_CURRENT=2/MAX=2` accepts [1,2]; `training_fingerprint` display-only; cross-major never fires intra-5.x) → D-100 retrain is checklist-enforced; plan must name the stamp_format_version bump (Layer 6b HARD row recommended). F3 MED — decimal dispatcher fork scope is 9 (file footer `CfgFieldDispatch.hpp:539-548`), not "3 + drift-compare"; `cfg_save_field` PCT `%.2f` already value-mutating for money rates. F4 MED — B1 booking exchange-reported commission must pin the commission_asset dimension (base/BNB-denominated `n` booked raw into quote fee = units error; promotes F-B). PARITY-035/036 confirmed CLOSED (fingerprint zero-init ctor verified `ControllerConfig.hpp:371`); PARITY-033 STILL-OPEN cited; PARITY-034 target-ship annotated stale (subsumed per D-108). Layer 5b GREEN (Option F invariants value-format tolerant). Full audit report: `plans/v5.15-live-readiness/plan_checks/parity-check-2026-06-09-ship-b-money.md`.

- **2026-06-10** — Ship-B P0.3 closes **PARITY-037** (see RESOLUTION in the entry — the percent-vs-fraction framing inverted by enumeration; fix = PCT scaling in `cfg_assign_field`/`cfg_diff_field` + the `lazy_rebuild_price_threshold_pct` outlier row re-authored percent-form, value-identical; suite 3246/0; boot bytes unchanged). Recorded at decision log D-177.

- **2026-06-11** — `.E.0.10` Net-1 adversarial money-surface bug-hunt (5 independent surface-blind agents) surfaced **PARITY-039** (HIGH; restore↔live TP/SL parity): snapshot-restore recomputes `live_tp/live_sl/live_tp_b` from the GLOBAL `take_profit_pct` (`ShardedSnapshotPersist.hpp:653`) while the live entry path uses the per-strategy override (`simpledip/mr/emacross_tp_pct`, `StrategyParameters.hpp:327`); `ControllerConfig_ResolveForCore` (`:1383`) does NOT fold the override → a SimpleDip/MR/EmaCross position exits at a DIFFERENT TP/SL after a warm-restart than while live (whenever the override is set). Status: **FIXED 2026-06-11 in `.E.0.10`** (single-sourced via `ResolvePerFillTpPct/SlPct`, entry + restore; SimpleDip+MR cohort char-tests GREEN, suite 3368/0; 3-agent independent refute SOUND/CORRECT; TECH_DEBT-168 closed; final `/parity-check` re-confirm at ship close). The do-it-twice defer to `.E.1` was the adjacency-defer the bidirectional rule corrected — the fix is durable, so it closed now. Sealed by orchestrator (ResolveForCore read); 2 agents converged. Momentum/ML unaffected (`out->tp_pct==take_profit_pct`). Register: `plan_checks/E.0.10-finding-disposition-register.md` bug-hunt § A1.

- **2026-06-20** — **batch closure: PARITY-009..018 status-drift corrected** (`.E.1.1` state-audit housekeeping; HEAD `3eadb53`). The 10 entries carried `status: in-flight` but were all genuinely RESOLVED long ago — the header fields were never flipped at fix-time (the drift an 8-agent state-audit surfaced 2026-06-20). **Code-grounded before flipping** (their bodies still read "OPEN (fix in flight)", so a blind flip was refused per `feedback_tag_disposition_at_fix_time` — never reconstruct disposition by archaeology): **009/010/011/012 → CLOSED** (the v5.14.2.E.1 `PostLoadSetup` structural fix shipped — `EnsembleModelZoo_PostLoadSetup`/`CoreModelZoo_PostLoadSetup` at `ML_Headers/NodeModelZoo.hpp:3007/3067`, driven by `FOREACH_ENSEMBLE_POST_LOAD`/`FOREACH_SINGLE_ZOO_POST_LOAD`, all three callers wired: boot+backtest `EngineCommon.hpp:313/348`, hot-swap `HotSwap.hpp:154/260` + `EnsembleHotSwap.hpp:109` → Class-18 mirror structurally eliminated); **013 → CLOSED** (`bandit_algorithm` is stamp-bound + drift-checked: `CfgDriftCheckRegistry.hpp:254` + `StampBoundModelConstRegistry.hpp:464`); **014/015/016/018 → CLOSED** (resolved at v5.14.10/.11 per the 2026-05-10/-11 audit-log entries above; long shipped); **017 → CLOSED** (sites 1+2 resolved at v5.14.11.B; sub-site 3c spun to **PARITY-019**, itself closed). The yaml `status:` field (queryable SSoT) is now `closed` for all 10; inline body `**Status:**` narratives preserved as detection-time record. No code change — ledger-truth correction only. Surfaced by the `.E.1.1` mid-dive state-audit (doc-currency agent flagged the drift; the over-broad "009..018 all resolved" claim was code-verified before action).

---

## Future audit findings will append here

When `/parity-check` finds a new issue:
1. Assign next PARITY-NNN
2. Fill in the format template above
3. Set initial status (usually OPEN or OPEN-DEFERRED)
4. Cross-link from the audit report (`plans/plan_checks/parity-*.md`)
5. Reference in commit message of the closing ship
6. Move to FIXED only after a follow-up `/parity-check` confirms
   regression-free

---

id: PARITY-041
title: corpus enumeration order diverged THREE ways (contract=merged-bytewise / Python=unsorted readdir / C++=hpp-grouped) with every gate structurally blind to it
surface_tags: [toolchain, corpus-contract, foxtag, two-walker, ordering, doc-tag-system]
severity: med
parity_axis: Python `engine_source_files()` order vs C++ `scan_files()` order vs the contract's declared `sort.within_root`
status: closed
detected_at: E.1.2.B `0.2` (2026-07-20, at BB-1 pickup — found by reading both walkers, not by any gate)
closed_at: E.1.2.B `0.2` (2026-07-20, commit `ee28ef2`)

**The divergence.** Three different orderings coexisted: `corpus_contract.json` declares
`sort.within_root = bytewise-ascending-relative-path` (MERGED); `check_code_tag_blocks.engine_source_files()`
returned raw `rglob` readdir order (**UNSORTED** — verified: first three were `Version.hpp`,
`Licensing.hpp`, `Limits.hpp`); `foxtag.hpp scan_files()` sorted `.hpp` and `.cpp` SEPARATELY then
concatenated (**GROUPED**, not merged).

**Why every gate was blind.** `parity_check.sh:24-25` sorts both legs before diffing, and §2's
parity-dump sorts its rows — so ordering is washed out everywhere it is compared. The membership
GOLDEN pins order exactly, but it could not discriminate either: the tracked engine corpus holds
only 2 `.cpp`, both lowercase-rooted (`main.cpp`), so merged-bytewise and hpp-grouped **coincide by
accident**. A single `.cpp` under a capitalised directory (`CoreFrameworks/Foo.cpp`) would have
broken the coincidence and RED'd one reader against the golden.

**Closure.** Both walkers now read `sort.within_root` from the contract. Verified BY CONSEQUENCE
rather than by reading that both call the same function: planted violations in `Bravo.cpp` and
`Charlie.hpp` (whose merged and grouped orders differ) and read the UNSORTED violation-emission
order — both emit `Bravo.cpp` first. Probe confirmed discriminating (the old grouped rule yields
`Charlie.hpp` first), so it is not a vacuous check.

**Lesson for the ledger.** Two hand-written walkers over one corpus will diverge on ordering, and
ordering is the axis a diff-based parity gate cannot see. Single-source the RULE, then prove
agreement on an artifact that is order-SENSITIVE.

**Related:** D-393 / C-396 item 3 (the sort clause) · `differential-to-absolute-gate-contract-widening.md`
· TECH_DEBT-245.

### PARITY note 2026-08-16 — feature_mask train↔serve gate was vacuous; now emits

- **status:** closed · **surface:** stamp body / train↔serve binding · **ship:** v5.15.5.F.4d.1.E.1.2
- **Finding.** The per-node feature-subset parity gate (`ML_Headers/ModelInference.hpp:1880-1893`,
  documented as closing "a CRITICAL gap from /parity-check 2026-05-07") had **never fired**. No
  producer ever set `feature_mask`, so no stamp carried the key, so `STAMP_HAS` was always false and
  the engine always took the WARN arm — whose text blames "pre-v5.11.18a" stamps, pointing every
  reader at stamp age rather than at the missing emit.
- **Fix.** `tt::Stamp_AssembleAndEmit` now stamps the all-features sentinel. That is the truthful
  value: the stamp is a MODEL document and the trainer has no feature-subset concept at all
  (`rg feature_mask Backtest/` is empty — it always trains on the full registered set). Reading it as
  "which node's mask?" is a category error; that is the RUNTIME half, supplied by the loading node as
  `expected_feature_mask`.
- **Blast radius at landing: ZERO.** No cfg on disk sets a mask, and an unmasked node resolves
  `expected_feature_mask` to 0, which skips the consumer entirely. It matters the first time a node
  IS masked: stamp(all) vs expected(subset) now REFUSES, correctly — the registry pins input shape,
  so a masked feed is drift rather than a smaller model.
- **Sister finding, same ship.** The `fees` stamp group was DELETED: its two rows lost their producer
  at the `.B.3` migration while the emit walk kept printing their zero defaults, so a signed body
  carried both the true `fee_rate_maker` (cfg-derived half) and `inference_cfg_fee_rate_maker=0`.
  Codified as H21 spec **Rule 1a** — a row retired from its PRODUCER but left in its EMITTER does not
  go dead, it goes lying.

---

### PARITY-044 — exit-side training and exit-side serving were built to different conventions and never joined; nothing records or checks a model's side

```yaml
id: PARITY-044
title: the trainer's exit tree is unloadable by the live loader, exit_signal_model_dir is parsed-never-read, labels are side-blind, and no stamp key records the side — so entry/exit models are mechanically interchangeable while semantically opposite
surface_tags: [train-serve-parity, ml-inference, exit-side, cfg-orphan, class-44, class-24, capital-safety]
severity: high
parity_axis: train↔serve (the exit half of the Path 3 architecture — producer and consumer disagree on layout, filename, and label semantics; no gate can detect a cross-side load)
status: closed
detected_at: 2026-08-20 (operator question "does training train pairs for entry and exit side, or will they work interchangeably?" — answered by tracing at engine HEAD 417e524; every claim below is file:line-grounded, side-blindness legs by uncapped all-roots grep)
related_specs:
  - DESIGN_SPECS/meta-disciplines/train-serve-execution-layer-parity.md
  - DESIGN_SPECS/meta-disciplines/advertised-capability-never-exercised.md
```

- **The four measured facts:**
  1. **Trainer half** (`Backtest/BacktestPanels.hpp`): `training_side` has exactly TWO consumption sites in the tree (:4303, :4309), both directory routing — `models/exit/<subdir>/<run>_horizon_<H>/`. The role FILENAME stays label-type-derived (`buy_signal`/`barrier`/`regime`, :4291-4293; save at :4337). **No code path ever writes `exit.json`.**
  2. **Labels are side-blind:** `training_side` appears nowhere in `BacktestEngine.hpp` / `LabelFunctions.hpp` / `BacktestSharded.hpp`, and `FOREACH_TARGET` carries no mirrored/sell label kind. An exit-side run with the default `WIN_LOSS` trains an ENTRY-goodness model into the exit tree. (`WILL_PEAK` / `PEAK_VALLEY_STABLE`'s peak class are the closest exit-appropriate kinds, operator-hand-picked only.)
  3. **Serve half:** the live discovery is `EnsembleModelZoo_LoadFromCfg` (production callers `CoreFrameworks/HotSwap.hpp:128` + `CoreFrameworks/EnsembleHotSwap.hpp:77`) walking `<base>_horizon_<H>/` for a role file **`exit.json` CO-LOCATED with the buy roles** (`ML_Headers/NodeModelZoo.hpp:2148`; the zoo's own header comment labels `exit.json` "(future)" at :49). **`cfg.exit_signal_model_dir` (`ControllerConfig.hpp:856`) is declared, defaulted, parsed — and read by NOTHING**: its only other mentions are two parse-round-trip tests and FIVE trainer-side comments/tooltips instructing the operator to point it at the exit tree (`BacktestPanels.hpp:3115, 4300, 4988, 4998, 5977`). Advertised, unconsumable.
  4. **No side marker anywhere:** no `training_side`/role key in the stamp registries (`StampHelper.hpp` + `StampBoundModelConstRegistry.hpp` + `StampBoundCfgRegistry.hpp`: zero hits); features and scaler are shared across roles by design. A buy model placed in an exit slot (or vice versa) loads CLEAN and no gate can ever notice.
- **Why it's capital:** the exit consumer (`Strategies/StrategyParameters.hpp:1425-1499`; `exit_threshold` row `CfgFieldRegistry.hpp:787`) fires an early market-exit when blended P > `exit_threshold` (default 0.6). For an entry-trained model that rule is INVERTED — it exits precisely when the position looks best. Mechanically interchangeable + semantically opposite + zero detection = silent-wrongness by construction the day someone joins the seam by hand-renaming files.
- **Interlock:** `MASK_ML_CFG_USE_EXIT_MODEL` gates a real read path (live once models exist). The D-423 exit-bandit SELECT sits downstream of `exit_predictor_count >= 2` — so the exit-learning loop currently has **no production model source** either; its proven loop-closure runs on hand-placed fixtures only.
- **Fix path (design decision needed — consult, options fork):** (a) pick ONE layout+filename convention — smallest is the trainer emitting role name `exit` when `training_side=1` into the co-located per-horizon dirs; wiring `exit_signal_model_dir` as a loader base is the bigger alternative; (b) give the side a SEMANTIC leg — an exit-appropriate label kind default or an explicit label mirror, not just routing; (c) stamp a `training_side`/role key + load-time side check so cross-use REFUSES (the guard leg; H21 append-only new key; epoch-free per `project_no_live_models_dev_test_only`); (d) or retire the exit-side trainer routing + tooltips until (a)-(c) land — the D-422 three end-states: wire it, retire it, or mark it explicitly unproven.
- **Cross-ref:** PARITY-042/-043 (same drift-gate neighborhood; the side key lands beside the `.B.3` parse→handle leg) · TECH_DEBT-094 (surviving slice = the ML exit-barrier params) · TECH_DEBT-034 (CLI/batch training) · the D-422 unwired-capability register · D-423 (exit-bandit, downstream consumer) · Classes 44 / 24 / 12.
- **Resolution:** CLOSED 2026-08-20 at E.1.2.C legs 3-pre / 3-retire / 3-role (engine `6fc5655` / `a81859d` / `22433b0`; guard shape = the D2 verdict, O1-only). All four fix legs landed:
  **(a) convention JOINED** — `training_side=1` emits role file `exit.json` CO-LOCATED in the per-horizon dirs (`Training_ResolveRole`, the ONE role derivation — relocated to `Backtest/LabelFunctions.hpp` and exhaustively table-pinned as C.3g, workspace `e8acc06`); the serve half was made REACHABLE by the R1 ensemble-aware dispatch fix + its 3 blind sisters + the R2 scaler seam (C.3f sentinel pin).
  **(b) semantic leg** — the side flip defaults the label kind to `WILL_PEAK`; the F3 trainer-side side×label gate refuses entry-semantics kinds on side=1.
  **(c) the guard, NO new wire key** — the EXISTING `expected_role` stamp key is ENFORCED at the `TryLoadRole` chokepoint via `Model_RoleCheckDecide` (the D2 decision table, pinned cell-by-cell as C.3h incl. the buy-stamp-in-exit-slot inverted-trading cell); F1 closes the FV re-stamp emit hole (`req_role` derived from the model basename); NEW `ml_role_mismatch` failure row (count pin 15→16). Cross-side load now REFUSES in strict / WARNs+flags in non-strict; exit slots have ZERO legacy population so a keyless stamp there REFUSES in strict.
  **(d) retirement** — `exit_signal_model_dir` + the `models/exit` tree DELETED; the name BURNED in `RETIRED_NAMES` (first proactively-burned cfg name key); all five advertisements died with it.
  Boot now reports the exit-predictor count on the ensemble-active line (the leg-4 Stage-1 oracle). Suite 3824/0 at the table-test close; determinism GREEN; identifier guard GREEN (93, burn included).

---

### PARITY-043 — the `.B.3` migration has no parse→handle leg, so two REFUSE_STRICT drift rows compare a permanent 0 against a live cfg default

```yaml
id: PARITY-043
title: cfg-derived ModelHandle fields are declared and read but written by NOTHING; the reachable REFUSE_STRICT rows therefore always fire
surface_tags: [train-serve-parity, cfg-derived, drift-gate, ml-inference, capital-safety, boot-time]
severity: high
parity_axis: train↔serve (the gate fires FALSELY — the inverse of PARITY-042, where it cannot fire at all)
status: closed
detected_at: v5.15.5.F.4d.1.E.1.2 (2026-08-17, D-426 i-class; discharged by compiled probe, not by reading)
related_specs:
  - DESIGN_SPECS/meta-disciplines/train-serve-execution-layer-parity.md
```

- **MINTED 2026-08-17** at the D-426 close, on the adversarial review's finding that this leg was **unhomed** — it existed only as prose inside PARITY-042, while the outbound handoff tagged it "PARITY-042". Two findings under one ID on a capital safety-control surface is exactly `feedback_no_unhomed_debt_code_smell`.
- **⚠️ NOT the same as PARITY-042 — the inverse symptom, same root.** PARITY-042 = the gate **cannot fire** (`MASK_inference_cfg` has no production producer, so the whole cfg-derived drift walk is skipped). PARITY-043 = the gate **always fires falsely** (these rows sit behind a **cfg-only** cohort gate, not `STAMP_HAS`, so they ARE reachable and DO compare). Closing one does not close the other.
- **Site(s):** `ML_Headers/CfgDriftCheckRegistry.hpp` — `thompson_precision_prior` + `thompson_precision_obs` rows, both `REFUSE_STRICT`, both `COHORT_GATE_BANDIT_ENABLED`. Handle-side reads are spelled `h->`, NOT `handle->` (a probe using the latter returns EMPTY for reads as well as writes and cannot fail — Class 51; see the handoff's replacement write-side probe).
- **Severity shape — NOT "the engine won't boot"** (a compiled probe corrected that prediction). At the shipped default it returns 0. **OFF:** every load emits guaranteed-false drift lines that saturate a capital safety channel, so real drift is indistinguishable from noise. **ON** (`held_out_gate_strict=1`, the live-readiness posture): every model refuses, so the rational operator response is to disable the gate. **A safety control that pressures you into switching it off is the Knight shape.**
- **Evidence:** `plans/v5.15-live-readiness/reports/2026-08-17-stamp-emit-gate-audit/orchestrator-drift-probe.md` (committed; prefer it over the machine-local `~/.cache/foxml_probe/`).
- **Fix path:** write the parse→handle leg so the cfg-derived fields are populated, OR re-scope the gate so unpopulated rows cannot compare. Enumerate the cohort from the registry (`STAMP_BOUND_CFG_DERIVED` rows) rather than trusting a carried "~30".
- **⚠️ Apply AR-19 when working it:** trace each field to every reader; do not scope the sweep by the last fix's blast radius. That mistake hid two consumers during the D-426 deletion.
- **Resolution:** CLOSED 2026-08-20 at E.1.2.C leg 2 (engine `7168953`). The FIFTH walker — `COPY_RESULT_TO_HANDLE_FROM_DERIVED` in the `cfg_derived` family — copies the stamp-parsed cfg-derived values onto the ModelHandle (per-field `has_` gating), called from `NodeModelZoo_TryLoadRole` after `Model_Load` success. Cohort enumerated FROM THE REGISTRY per this entry's own instruction: 36 fields measured, not the carried "~30". The two REFUSE_STRICT rows now compare REAL stamp values; C.3e pins the PRODUCTION round-trip (emit→parse→copy→`ValidateAgainstCfg`) with a before/after oracle — the false-firing tiers went >0 → 0/0 — and the trained-without-feature positive control still fires on the same load shape. Comment-truth sweep rode the commit; AR-19 honored (every reader traced). RESIDUALS tracked elsewhere, NOT re-opened here: ensemble loads still pass no cfg_ptr (E.1.2.C plan register #6) · `NodeModelZoo_LoadLegacy` stamp-less loads dispositioned document-as-intended (A-6: on `node_N_model_path` deployments the drift lines are TRUE "cannot verify an unstamped model" signals, in the e2e protocol's noise-list caveats).

---
### PARITY-042 — the ENTIRE stamp↔cfg drift gate layer is vacuous in production (the train→serve cfg-parity apparatus never compares)

```yaml
id: PARITY-042
title: MASK_inference_cfg has no production producer, so every cfg-derived drift row and 4 FOREACH_CFG_DRIFT_CHECK rows (3 REFUSE_STRICT) silently skip — train→serve cfg parity is unverified for the whole cohort
surface_tags: [train-serve-parity, stamp-wire, cfg-derived, drift-gate, false-green, ml-inference, boot-time]
severity: high
parity_axis: train↔serve (the gate that exists to detect divergence cannot fire)
status: open
detected_at: v5.15.5.F.4d.1.E.1.2 (2026-08-17, D-426 i-class; discharges the 9 verifications MASTER UPDATE at 2026-08-16 recorded as PENDING)
related_specs:
  - DESIGN_SPECS/meta-disciplines/advertised-capability-never-exercised.md (the class; this is its THIRD unit — bits, then functions, now registry rows / wire keys)
  - DESIGN_SPECS/meta-disciplines/train-serve-execution-layer-parity.md (M5 — this is the gate M5 exists to protect)
  - DESIGN_SPECS/wire-format-patterns/wire-format-byte-preservation-discipline.md (H9)
```

- **Found:** 2026-08-17, D-426 adversarial pass (i-class), independently corroborated by an a-class on the same surface. Both were armed to REFUTE, not confirm.
- **⏩ SURFACE UPDATE 2026-08-17 (D-426 close) — one LYING row removed from this cohort; the vacuity itself is UNCHANGED and still open.** `inference_cfg_bandit_blend_ratio` was deleted outright (row + bit + MASK + STANDALONE entry + the emit-side bit-set + BOTH consumers), and its name burned in `RETIRED_NAMES`. It sat on this exact surface and was the sharpest instance of the shape: the emit half set its presence bit and assigned nothing, so it shipped a zero into the signed body while the cfg-derived half emitted the truthful value beside it. **What this does NOT fix:** `MASK_inference_cfg` still has no production producer, the 9 remaining `inference_cfg_*` rows still have no value producer, and the 4 `FOREACH_CFG_DRIFT_CHECK` rows (3 `REFUSE_STRICT`) still skip. **Do NOT read the deletion as progress on this entry** — it removed a lie from the surface, not the blindness. The parse→handle leg is **PARITY-043**, a SEPARATE finding — this entry's own "Related but SEPARATE (do not conflate)" bullet says so, and an earlier version of THIS line called it "the actual fix" for PARITY-042, which contradicted that bullet inside one entry. Corrected: **PARITY-042's fix path is its own** (delete the orphan rows on the `fees` precedent + re-key the drift gates onto per-row `r.has_<name>` presence). Closing PARITY-043 does NOT close this. ⚠️ Also note for whoever works it: two of this cohort's consumers (a panel display and an sr→handle copy) were found only while SCOPING the deletion, not by the sweep that removed the sibling defect a day earlier — catalogued as **AR-19** in the meta-anti-pattern index. Trace each field to every reader; do not scope by the last fix's blast radius.
- **⏩ SURFACE UPDATE 2026-08-20 (E.1.2.C leg 2) — the "Related but SEPARATE" sibling is CLOSED; THIS entry's vacuity is UNCHANGED and still open.** PARITY-043 closed at `7168953`: the parse→handle leg now EXISTS (the fifth walker; 36 cfg-derived fields, superseding this entry's "~30 … never written" phrasing below), so the false-firing half of the neighborhood is dead and the sibling bullet's present-tense "those rows ARE reachable and DO fire" is historical. NOTHING here moved: `MASK_inference_cfg` still has no production producer, the 9 `inference_cfg_*` rows still have no value producer, and the 4 group-bit-gated `FOREACH_CFG_DRIFT_CHECK` rows still skip. The fix path stays this entry's own (delete the 9 orphan rows on the `fees` precedent + re-key onto per-row `r.has_<name>` presence).
- **Severity:** HIGH — a model trained under one `ml_tp_pct` / `thompson_*` / `barrier_blend_mode` and served under different values loads **clean**, with no WARN and no REFUSE, **in every mode including `held_out_gate_strict=1`**. Serving-time barrier distances, bandit posteriors, ridge blending and fee-aware gating can all diverge silently from the calibration the model was fit to. This is precisely the failure `FAILURE_MASK_cfg_binding_drift` and the `acknowledge_inference_cfg_drift` operator ack exist to make impossible to hit by accident.
- **Class:** Class 58 sub-shape B (gate-reachability — the rows are correct and the gate reading them is unreachable) sitting under Class 51 (vacuously-green guard). The distinguishing feature, and why a value-oriented trace misses it: **nothing reads the 9 keys' VALUES.** The consumer is the *presence bit* their emission would set. Trace values and you conclude "no consumer" and stop.
- **Site(s) / the chain, every link measured:**
  - Producer of the bit: the PARSE walk only — `ML_Headers/ModelInference.hpp:1757-1763` → `STAMP_PARSER_SET_HAS_inference_cfg` (`StampBoundModelConstRegistry.hpp:759`). No stamp key ⇒ bit never set. `ModelStampResult r{}` zero-inits.
  - No emit-side producer exists: the 9 `inference_cfg_*` rows have no value producer either, so the whole group never emits.
  - Gate A — `MemHeaders/CfgGateRegistry.hpp:814` passes `STAMP_HAS((sr), inference_cfg)` into `lookup_drift` (`:186-208`), where **every** branch returns `stamp_has_inference_cfg && (expr)`; the ML/gate-flag walkers (`:568`, `:588`) use it as a bare conjunct. `sr.inference_cfg_drift_count` therefore stays 0 and `NodeModelZoo.hpp:305-307`'s REFUSE never fires.
  - Gate B — 4 rows of `FOREACH_CFG_DRIFT_CHECK` gated on `STAMP_HAS(*h, inference_cfg)` (`ML_Headers/CfgDriftCheckRegistry.hpp:257, :261, :266, :332`), **three of them `REFUSE_STRICT`**.
  - The same guard also gates the sr→handle VALUE copy (`NodeModelZoo.hpp:458-468`), so even a forced-true gate would compare `0` against cfg.
- **Symptom:** none visible. `NodeContextDisplayMeta.cfg_drift_tier1_count` / `tier2_count` read 0 — not because there is no drift, but because nothing was compared. `NODE_STATE_FLAG_CLR(CFG_DRIFT_STRICT_REFUSED)` issues a clean bill of health that was never earned. That silence is the defect.
- **Root cause:** the `.B.3` prefix migration moved the cfg-derived cohort onto framework walkers for **emit** and **parse** and left the group-bit producer behind — the same migration-tail shape as the `fees` group and `inference_cfg_bandit_blend_ratio` (D-426). Class 58 sub-shape C.
- **⚠️ DO NOT "just add the producer".** Setting `STAMP_SET(inf, inference_cfg)` in the emit path would emit **nine zeros into an HMAC-signed body**, because those rows have no value producer either. That is bit-for-bit the `fees` failure, whose own retirement comment states the rule: *a row retired from its PRODUCER but left in its EMITTER does not go dead, it goes LYING.* Refuted explicitly as option O2 in the i-class report.
- **Fix path (i-class recommendation, operator's call):** delete the 9 orphan rows on the `fees` precedent and re-key the drift gates onto a signal the cfg-derived parse actually produces — the per-row `r.has_<name>` presence, so each drift row gates on **its own** field rather than a group bit. Strictly more precise than the group bit and preserves per-field forward-compat. Removes the last consumer of `MASK_inference_cfg`, so the group bit and its three dispatchers go with it.
- **Related but SEPARATE (do not conflate):** the `.B.3` migration also has **no parse→handle leg**, so ~30 cfg-derived `ModelHandle` fields are never written and two `REFUSE_STRICT` rows compare `0` against a cfg default of `1.0` behind a **cfg-only** gate — those rows ARE reachable and DO fire. Measured by compiled probe (`plans/v5.15-live-readiness/reports/2026-08-17-stamp-emit-gate-audit/orchestrator-drift-probe.md`). Same root cause, opposite symptom: this entry is the gate that *cannot* fire; that one is the gate that *always* fires falsely.
- **Target ship:** `v5.15.5.F.4d.1.E.1.2` (queued; see D-426's reordered queue — this is item 1)
- **Status:** OPEN
- **Verification (owed):** a test asserting `STAMP_HAS(vr, inference_cfg) == 1` for at least one production-path emit — currently expected to FAIL, which is the point: it pins the vacuity and prevents any future gate change from freezing it permanently dead. Plus the generalized form: for every row whose gate is set on the default path, set a **distinctive non-default** value and assert the round-trip carries *that* value. A row with no path from any input to a distinctive output is a row with no producer.
- **Evidence:** `plans/v5.15-live-readiness/reports/2026-08-17-stamp-emit-gate-audit/i-class-18-key-consumer-trace.md` (full chain, every link cited) · `a-class-refute-byte-identical.md` § 3 (independent corroboration) · the fixture that hid it: `tests/controller_test.cpp:15566-15584`, which hand-sets the group bit and whose own comment already says *"THIS FIXTURE IS WHY THE VACUITY SURVIVED."*


### PARITY-045 — the validation harness trained a different ARCHITECTURE than the shipped model, and the stamp recorded a third story

```yaml
id: PARITY-045
status: closed
opened: 2026-08-21
closed: 2026-08-21
severity: high
surface_tags: [train-serve, ml-inference, stamp-body, validation]
found_by: i-class training-surface scan (S1-F3) + orchestrator verification
closed_by: engine f99e102
```

**The divergence.** One training run produced FOUR descriptions of itself:

| consumer | architecture used | source |
|---|---|---|
| the SHIPPED model | the operator's panel values (measured: `2 / 0.050 / 350`) | eight LIVE `state->` reads |
| the walk-forward folds | `6 / 0.1 / 200` + four cfg overrides | `XGBHyperparams_Defaults()` + `eff_cfg` |
| the held-out model | pure `6 / 0.1 / 200 / 0.8 / 0.8 / 5 / 42` | `XGBHyperparams_Defaults()`, **no overrides at all** |
| the STAMP | `6 / 0.1 / 200` | the same hardcoded defaults |

**Why it is a parity issue and not merely a bug.** `held_out_metric` is the figure that gates
deployment, and it described a model that was never trained and never shipped. The operator's
hyperparameter tuning could not appear in the numbers used to judge it — a closed loop that was
open. It survived because **no artifact on disk could contradict the stamp**: the stamp drew from
the same hardcoded defaults the validation did, so the two agreed with each other and with nothing
real.

**Mechanism of the fix.** One `const tt::XGBHyperparams *hp_override` (default `nullptr` =
prior behaviour bytewise) threaded `Backtest_RunFullValidation` → `Backtest_RunWalkForward` +
`HeldOutSplit_TrainEval`, built once by the worker from the click-time snaps. NOT via
`ControllerConfig` — see Landmine 22.

**Residual (not part of this closure):** the plumbing needs XGBoost + real data to exercise, so the
acceptance oracle is PARTIAL — `C.3k` pins only the shared `XGBHyperparams_Defaults()` fallback.
Dogfood verification is owed: train one horizon, then grep the stamp for the operator's values.
