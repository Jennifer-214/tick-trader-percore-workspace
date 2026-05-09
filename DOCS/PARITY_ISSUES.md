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
- **Status:** OPEN
- **Workaround:** Don't enable composite in v5.9.2 replay-determinism
  regression test (`tests/controller_test.cpp:10251`) until fixed.

### PARITY-002 — ConfidenceScorer_UpdateAndMark API exists but production callers still use legacy _Update

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
- **Status:** OPEN
- **Workaround:** Don't enable `confidence_composite_enabled=1` in
  paper-test or live until B.1 ships.

### PARITY-003 — Composite cfg fields not pushed into ConfidenceScorer at boot

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
- **Status:** OPEN
- **Workaround:** Don't enable `cfg.confidence_composite_enabled=1`
  until v5.14.1.B.1 ships; legacy IC-only path is bytewise unchanged.

### PARITY-004 — Ridge cfg fields (5) not stamp-bound; train↔serve cfg drift undetected

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
- **Target ship:** v5.14.2 (Surface G stamp body extension; medium
  effort ~1h)
- **Status:** OPEN-DEFERRED (v5.14.2)
- **Workaround:** Operator manually verifies cfg.ridge_* values
  match training cfg before deploying.

### PARITY-005 — Composite confidence cfg fields (5) not stamp-bound; same class as PARITY-004

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
- **Target ship:** v5.14.2 (bundle with PARITY-004 = ONE Surface G
  stamp body extension covers both)
- **Status:** OPEN-DEFERRED (v5.14.2; bundled with PARITY-004)
- **Workaround:** Don't change composite cfg between train + infer;
  document training values in run notes until stamp-bound.

### PARITY-006 — Two distinct freshness tau cfg fields with overlapping semantics

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
  - Status will move to CLOSED after one full /parity-check rerun
    confirms regression-free.
- PARITY-003: **FIXED** in v5.14.1.B.1.
  - Added `ConfidenceScorer_BindCompositeCfg(cs, enabled, tau, target,
    kappa, baseline)` helper at `ML_Headers/ConfidenceScore.hpp`.
  - Wired at 2 of 3 boot sites:
    - `EngineSharded.hpp:1244` (sharded engine — STRATEGY_ML cores)
    - `PortfolioController.hpp:397` (legacy single_core)
  - 3rd site (`ControllerEventLoop.hpp:580` per-core init) deliberately
    deferred — that site runs BEFORE EngineSharded re-inits with cfg
    values, so BindCompositeCfg there would have no cfg to read.
    EngineSharded re-runs Init + BindCompositeCfg after this site for
    STRATEGY_ML cores; non-ML cores keep safe defaults (their scorer is
    never fed). Comment added inline at the site explaining the design.
  - Status will move to CLOSED after one full /parity-check rerun
    confirms regression-free.
- PARITY-007: **NOT-A-BUG** confirmed. False positive from audit.
  Closed without ship (no fix needed).
- BONUS fix in v5.14.1.B.1: composite cfg block (5 fields) ADDED to
  `engine.cfg.example` (was a v5.14.1.B oversight; not flagged by audit
  but caught during PARITY-007 verification).

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
