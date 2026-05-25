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

### PARITY-008 — exit_blender_mode not populated in RFV stamp emit

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
status: in-flight
detected_at: v5.14.2 (2026-05-09)
related_specs: [DESIGN_SPECS/framework-patterns/postloadsetup-registry-pattern.md, DESIGN_SPECS/framework-patterns/autopopulate-pattern-for-production-caller-class.md]
```

- **Found:** 2026-05-09 by post-coding /parity-check + /merge-scan +
  manual enumeration of `EngineSharded.hpp:1075-1240` boot block vs
  `CoreFrameworks/EnsembleHotSwap.hpp:54-115` hot-swap helper.
- **Severity:** **HIGH composite** — sub-gap F is CRITICAL on its own
  (bypasses inference_cfg drift detection that PARITY-002/003/004/005
  closed); other sub-gaps are MEDIUM (operator-config silently lost on swap).
- **Class:** Class 18 (mirror data-flow incomplete); same shape as the
  v5.9.5b production-caller field-population class but at the function-
  composition level instead of the field-population level.
- **Sites:**
  - Boot reference: `CoreFrameworks/EngineSharded.hpp:1157-1240`
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
status: in-flight
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
  - Boot reference: `CoreFrameworks/EngineSharded.hpp:1180` (InitExitBandits) + `:1200` (LoadExitBanditState)

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
status: in-flight
detected_at: v5.14.2 (2026-05-09)
related_specs: [DESIGN_SPECS/framework-patterns/postloadsetup-registry-pattern.md]
```

- **Found:** 2026-05-09 during PARITY-009 enumeration sweep across boot / backtest / hot-swap surfaces.
- **Severity:** MEDIUM (silent train-serve drift; subset of VerifyExpected's checks already covered by ValidateAgainstCfg, but unique checks like cadence + feature_format + num_classes are bypassed)
- **Class:** Class 18 (mirror data-flow incomplete; same shape as PARITY-009).
- **Sites:**
  - Boot reference (single-zoo): `CoreFrameworks/EngineSharded.hpp:1108-1131` (calls VerifyExpected at :1114)
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
status: in-flight
detected_at: v5.14.2 (2026-05-09)
related_specs: [DESIGN_SPECS/framework-patterns/postloadsetup-registry-pattern.md]
```

- **Found:** 2026-05-09 during PARITY-009 enumeration sweep.
- **Severity:** MEDIUM (backtest replay-determinism: inference_cfg drift not detected during backtest validation)
- **Class:** Class 18 (mirror data-flow incomplete).
- **Sites:**
  - Boot reference (single-zoo): `CoreFrameworks/EngineSharded.hpp:1229` (calls ValidateAgainstCfg)
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
status: in-flight
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
status: in-flight
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
status: in-flight
detected_at: v5.14.10 (2026-05-10)
related_specs: [DESIGN_SPECS/framework-patterns/display-execution-invariant-registry-pattern.md, DESIGN_SPECS/framework-patterns/calibration-log-column-registry.md]
```

- **Found:** 2026-05-10 during v5.14.10 Thompson bandit pre-coding parity audit (no commit yet — plan-stage finding)
- **Severity:** MEDIUM
  - CLAUDE.md item 12 invariant: every term in BG/SG_Evaluate (and in this case, ML_BuildParameters dispatch — slow-path predicate) must have a corresponding GUI surface
  - Current Exp3 path has `ensemble_bandit_arm_probs` + `ensemble_n_updates_per_regime` snapshot fields populated at `CoreFrameworks/EngineSharded.hpp:646-694`
  - Plan adds parallel ThompsonBanditState; proposes ZERO snapshot fields + ZERO ML Status panel branches → operator can't inspect Thompson posterior state
- **Class:** Display↔execution invariant breach (v5.6.0 pattern); Class 18 sister (asymmetric snapshot coverage between Exp3 and Thompson)
- **Site(s):**
  - Plan: `plans/v5.14-foxml-port-and-maker/subplans/2026-05-08-v5.14.10-bayesian-thompson-bandit.md` (entire file: zero "snapshot" / "panel" / "GUI" mentions per `grep -c`)
  - Snapshot publish reference: `CoreFrameworks/EngineSharded.hpp:646-694` (where `ensemble_bandit_arm_probs[r]` is populated for Exp3; needs parallel Thompson section)
  - Snapshot struct: `CoreFrameworks/ShardedSnapshot.hpp` (search `ensemble_bandit_arm_probs` for parallel additions)
  - ML_BuildParameters dispatch (the new "term"): `Strategies/StrategyParameters.hpp:887-1005`
- **Symptom:** Operator paper-tests Thompson sampling, sees flat P&L, has NO panel surface to ask "is Thompson posterior actually diverging from uniform priors? Is mu_post moving? Are pulls evenly distributed across arms?" Must shell into the binary, dump bandit state via stderr fprintf. Worse: operator can't see which algorithm path is currently active without re-reading cfg (no "Bandit Algorithm: Exp3 / Thompson / Both" indicator). Same telemetry need that drove `ensemble_bandit_arm_probs` for the Exp3 path.
- **Root cause:** Plan focuses on math + persistence; skips snapshot/panel propagation. Cfg=2 dual-mode telemetry mentioned at line 144 ("uses calibration log v5.13.0.B with new columns") but specifics not designed.
- **Fix path:** v5.14.10.B amendment — add Step 7 "Snapshot + ML Status panel surface":
  - Snapshot fields: `thompson_bandit_active` (uint8); `thompson_bandit_chosen_arm[NUM_REGIMES]` (int8); `thompson_bandit_total_pulls_per_regime[NUM_REGIMES][N_ARMS]` (uint32); `thompson_bandit_mu_post_per_regime[NUM_REGIMES][N_ARMS]` (float)
  - Populator extends EngineSharded.hpp:646-694 ensemble snapshot section
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
status: in-flight
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
status: in-flight
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
status: in-flight
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
title: Per-arm trained TP/SL barriers stamped at training but not consumed at serving; ml_tp_pct/ml_sl_pct Tier 1 promotion missing
surface_tags: [slow-path, ml-inference, cfg-flow, wire-format, registry]
severity: high
parity_axis: train↔serve
status: open
detected_at: v5.15.5 (2026-05-12)
related_specs: [DESIGN_SPECS/feature-patterns/per-horizon-barrier-blending-with-shadow-mode.md, DESIGN_SPECS/framework-patterns/autopopulate-pattern-for-production-caller-class.md, DESIGN_SPECS/wire-format-patterns/wire-format-byte-preservation-discipline.md]
```

- **Found:** 2026-05-12 during `/parity-check` audit of v5.15.5 plan (pre-coding gate)
- **Severity:** HIGH (silent decision drift; trades fire at cfg-side TP/SL even when model trained on different barriers; train-serve gap observable in P&L over hours under multi-horizon ensembles)
- **Class:** Train-serve cfg-binding gap (Class similar to PARITY-004/005); also touches Class 18 (parallel path drift — barriers exist on stamp + on cfg but not wired into the slow-path build)
- **Site(s):**
  - `Strategies/StrategyParameters.hpp:1259-1260` — `tp_pct = config->ml_tp_pct; sl_pct = config->ml_sl_pct` reads cfg directly, ignoring stamp's `label_tp_pct`/`label_sl_pct`
  - `ML_Headers/CoreModelZoo.hpp:349-350` — stamp body's `label_tp_pct`/`label_sl_pct` already loaded into `ModelHandle<F>` (since v5.11.42 D.2) but ezoo lacks per-arm tight-pack copy for slow-path consumption
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
status: open
detected_at: v5.15.5.F.4d.1.B.3 WIP-8 (2026-05-24 audit cycle)
target_close: v5.15.5.F.4d.1.B.4 (NEW; train-serve-execution-layer-parity sub-ship) OR earlier hotfix
related_specs: [DESIGN_SPECS/meta-disciplines/structural-fix-preferred-decision-framework.md, DESIGN_SPECS/meta-disciplines/train-serve-execution-layer-parity.md (DRAFT v0.1 at .B.4)]
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
- **Status:** OPEN
- **Workaround:** Operator MUST monitor drawdown manually in live trading until fix lands. Live mode without kill_switch is not safe for unattended trading.

### PARITY-027 — Backtest has no ML exit-prediction submit path (use_exit_model=1 train-serve break)

```yaml
id: PARITY-027
title: Backtest has no ML exit-prediction submit path (use_exit_model train-serve break)
surface_tags: [backtest-slow-path, exit-model-ml-inference, oms-drainer, class-18-mirror, train-serve-asymmetry]
severity: critical
parity_axis: live↔backtest (backtest missing the dispatch)
status: open
detected_at: v5.15.5.F.4d.1.B.3 WIP-8 (2026-05-24 audit cycle)
target_close: v5.15.5.F.4d.1.B.4
related_specs: [DESIGN_SPECS/refactor-patterns/shared-helper-extract-for-train-serve-mirror-close.md (DRAFT v0.1 at .B.4)]
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
- **Status:** OPEN
- **Workaround:** Operator should disable `use_exit_model` (set `MASK_ML_CFG_USE_EXIT_MODEL=0`) until fix lands, OR accept that backtest equity curves systematically diverge from live for any model trained with this flag enabled.

### PARITY-028 — ConfidenceScorer_BindCompositeCfg + RollingTurnover_Init missing in backtest (composite confidence drift)

```yaml
id: PARITY-028
title: ConfidenceScorer_BindCompositeCfg + RollingTurnover_Init missing in backtest
surface_tags: [backtest-boot, confidence-scoring, class-18-mirror, train-serve-asymmetry]
severity: critical
parity_axis: live↔backtest (backtest missing 2 calls)
status: open
detected_at: v5.15.5.F.4d.1.B.3 WIP-8 (2026-05-24 audit cycle)
target_close: v5.15.5.F.4d.1.B.4
related_specs: [PARITY-003 (sister; live side was closed at v5.14.1.B.1 but backtest mirror never enforced)]
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
- **Status:** OPEN
- **Workaround:** Operator should set `confidence_composite_enabled=0` (legacy product mode) until fix lands; composite confidence configs are not safe to train-then-deploy with current backtest path.

### PARITY-029 — Strategy_InitPerCore never called in backtest (pre-v5.4 F7 bug never closed on backtest side)

```yaml
id: PARITY-029
title: Strategy_InitPerCore never called in backtest (pre-v5.4 F7 bug alive on backtest)
surface_tags: [backtest-boot, strategy-lifecycle, class-18-mirror, train-serve-asymmetry, training-data-contamination]
severity: critical
parity_axis: live↔backtest (backtest missing the call)
status: open
detected_at: v5.15.5.F.4d.1.B.3 WIP-8 (2026-05-24 audit cycle)
target_close: v5.15.5.F.4d.1.B.4
related_specs: [postmortem F7 (v5.4.0; live side fix); DESIGN_SPECS/meta-disciplines/structural-fix-preferred-decision-framework.md]
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
- **Status:** OPEN
- **Workaround:** Operator should be aware that any model trained on backtest data since v5.4 may carry pre-convergence stateful-strategy data contamination. Models trained with stateless strategies (SimpleDip, EmaCross) are unaffected. Increasing `min_warmup_samples` is a partial mitigation.

### PARITY-030 — BNB fee discount applied LIVE-only (33% backtest fee inflation; train-serve cost drift)

```yaml
id: PARITY-030
title: BNB fee discount applied LIVE-only (backtest pays 33% higher fees than live)
surface_tags: [backtest-boot, fee-model, train-serve-asymmetry, cost-parity]
severity: high
parity_axis: live↔backtest (backtest missing the discount)
status: open
detected_at: v5.15.5.F.4d.1.B.3 WIP-8 (2026-05-24 audit cycle)
target_close: v5.15.5.F.4d.1.B.4
related_specs: []
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
- **Status:** OPEN
- **Workaround:** Operator should be aware that backtest results with `pay_fees_in_bnb=1` are pessimistic vs live execution by ~33% of fee load.

### PARITY-031 — Per-core regime divergence at backtest feature collect (N→1 collapse)

```yaml
id: PARITY-031
title: Backtest collapses N per-core regime states to 1 at feature compute (live serves N per-core)
surface_tags: [backtest-feature-compute, regime-detection, per-core-state, train-serve-asymmetry]
severity: high
parity_axis: live↔backtest (backtest collapses N→1)
status: open
detected_at: v5.15.5.F.4d.1.B.3 WIP-8 (2026-05-24 audit cycle)
target_close: v5.15.5.F.4d.1.B.4
related_specs: []
```

- **Found:** 2026-05-24 ML↔LIVE structural sweep
- **Severity:** HIGH — silent train-serve drift on per-core-regime-aware cfg shapes; affects ANY operator using per-core `regime_hysteresis` overrides
- **Class:** DIVERGENT FIELDS asymmetry (single-state vs per-core-state)
- **Site(s):**
  - Live: `CoreFrameworks/ControllerEventLoop.hpp:2641` — `ml_ctx.current_regime_id = state->cores[slot].regime_state.current_regime` (per-core regime state per inference call)
  - Backtest: `Backtest/BacktestSharded.hpp:541-548` allocates SINGLE `fc_ctx.regime_state` (not per-core); `:612` collapses N→1 via `ctx.current_regime = fc->regime_state.current_regime`
- **Symptom:** Per-core configs with different `regime_hysteresis` train features with ONE collapsed regime; live serves N separate regimes. `regime_class_onehot` + downstream regime-context features systematically drift between training matrix + serve-time inference.
- **Root cause:** Backtest feature-compute path was simplified to single regime state for simplicity; per-core regime overrides feature came later but never extended backtest collection.
- **Fix path:** Make `fc_ctx.regime_state` `[MAX_EXECUTION_CORES]`; per-core collection per slot. ~30 LOC. Folds into TECH_DEBT-119 C1.
- **Target ship:** `v5.15.5.F.4d.1.B.4`
- **Status:** OPEN
- **Workaround:** Operator should avoid per-core `regime_hysteresis` overrides (use same value across all cores) until fix lands.

---

## Audit log

- **2026-05-10** — `/parity-check` audit of v5.14.10 Thompson bandit plan (pre-coding gate). 3 new findings written: PARITY-013 (HIGH), PARITY-014 (HIGH), PARITY-015 (MEDIUM). Verdict: YELLOW (proceed with 4 plan amendments before scope-lock). Full audit report: `plans/plan_checks/parity-check-2026-05-10-v5.14.10-thompson-bandit.md`.
- **2026-05-11** — `/parity-check` audit of v5.14.11 online-corr-update plan (pre-coding gate). 3 new findings written: PARITY-016 (HIGH), PARITY-017 (HIGH), PARITY-018 (MEDIUM) + 1 LOW (stamp-binding eligibility — Document-only, not assigned PARITY-NNN). Verdict: YELLOW (proceed with ~60 min plan amendments before .A code starts). Default-off bytewise-identity to v5.14.10 confirmed (cfg=0 takes BuildCorr branch unchanged). No train↔serve handoff surface added. Both BuildCorr call sites flagged in plan REUSE claims (buy-side at StrategyParameters.hpp:996 + exit-side at :1195). Full audit report: `plans/plan_checks/parity-check-2026-05-11-v5.14.11.md`.
- **2026-05-10** — `/parity-check` re-audit of v5.14.10 AMENDED plan (4 architectural decisions baked in + 13 mechanical fixes applied + 6-sub-tag structure .0/.A/.B/.C/.D/.E). Verdict: YELLOW (proceed with 7 mechanical plan-text fixes; ~10 min). Confirmed: PARITY-013 RESOLVED in .B Step 9 (FOREACH_STAMP_BOUND_CFG with 4 X-rows + AUTOPOPULATE auto-flow). PARITY-014 RESOLVED in .A Step 2+7 (own Box-Muller via raw mt19937_64::operator() + SHA-256-locked sample-trace test). PARITY-015 RESOLVED in .D Step 1+2+6 (5 PerCoreSnap fields with bit-packed thompson_state byte + ML Status panel branch + cfg=2 calib log via FOREACH_CALIB_LOG_COL). 2 NEW MEDIUM findings flagged as plan-text staleness (NOT new bug class): NEW-1 stale field name `ensemble_bandit_arm_probs` → actual `ensemble_weights[5][8]`; NEW-2 stale file path `EngineSharded.hpp:646-694` → actual `ShardedSnapshot.hpp:677-694` (publish writer). Both propagated from prior parity-check report; PARITY-015 entry's file path citation should be corrected. NO new PARITY-NNN entries. NEW parity surfaces (thompson_state.json wire format Layer 1-6 compliance, PerCoreSnap cluster restructure, 4 stamp-bind drift tests presence dispatch) all GREEN against discipline. Full audit report: `plans/plan_checks/parity-check-2026-05-10-v5.14.10-AMENDED.md`.
- **2026-05-12** — `/parity-check` audit of v5.15 sprint plan (pre-coding gate; HIGH-RISK v5.15.0 ModelHandle migration; MEDIUM-RISK v5.15.2 trading_mode introduction; MEDIUM-RISK v5.15.3 multi-horizon stamping; MEDIUM-RISK v5.15.4 hot-swap unification + strict defaults). Verdict: **YELLOW** (proceed with amendments before .0 / .3 / .4 coding). 4 new findings written: PARITY-020 (HIGH; train_model_worker_fn missing STAMP_CFG_AUTOPOPULATE — asymmetric with RFV across 22 cfg-bound fields; recommend bundle into v5.15.3.A as 1-LOC addition); PARITY-021 (HIGH; v5.15.3 root cause misdiagnosed — multi-horizon DOES stamp via RFV; gap is grid_member_count/_idx orphan registry placeholders never populated; recommend revised approach plumbs req_grid_member_* through FullValidationResults into RFV's existing emit path; reduces v5.15.3 scope from ~150 LOC to ~30 LOC; drops stamp_emit_for_horizon helper); PARITY-022 (MEDIUM; STAMP_MODEL_CONST_AUTOPOPULATE macro defined but self-referential — v5.15.3 plan can't use it; defer wiring to future sprint); PARITY-023 (MEDIUM; v5.15.4 HotSwapSnapshot/Revert design captures only pointers — pre-swap data destroyed in-place by Free; recommend de-scope TECH_DEBT-005 from v5.15.4 OR restructure with shadow-load). Plus 6 MEDIUM + 4 LOW findings on stale line numbers + documentation accuracy. HMAC chain integrity verified GREEN (Surface G has_* flags + appending trading_mode at registry END preserves legacy stamp byte equivalence). NaN-free feature pack chokepoint preserved. Cross-mode byte-equivalence test design needs amendment for executability (xgb_train_nthread + training_timestamp_us require explicit setup). Full audit report: `plans/plan_checks/parity-check-2026-05-12-v5.15.md`.
- **2026-05-11** — `/parity-check` re-audit of v5.14.11 AMENDED plan (post-Caramel-consult: Decision 4 cohort migration + Decision 5 (C) sliding-window Welford + (C) BuildCorr refactor + (D) Cholesky AVX-512 adopted). Verdict: **GREEN** (proceed to .A kickoff). PARITY-016/017/018 status: **PARITY-016 RESOLVED at v5.14.11.A** by structural unification + per-cfg SHA-256 baselines (cfg=0 + cfg=1 each bytewise-locked within v5.14.11; share FinalizeCorrFromSums kernel; cross-cfg tolerance ~1e-13 sum convergence). **PARITY-017 RESOLVED at v5.14.11.B for sites 1+2** (UpdateOnline outer-product + BuildCorr accumulation) via v5.11.7 discipline + per-site SHA-256 lock test; site 3 (Cholesky) split with sub-site 3c new finding (see below). **PARITY-018 RESOLVED BY ELIMINATION** — sliding-window-by-design has no periodic-reset code path; bug class cannot exist. 1 NEW MEDIUM finding: PARITY-019 (Cholesky_Solve back-solve column-access doesn't vectorize via the row-load template; needs explicit .B kickoff strategy decision). 1 LOW recommendation (NOT assigned PARITY-NNN): defensive bounded-input guard at UpdateOnline entry (production default uses BARRIER ensembles → bounded [0,1]; non-BARRIER models risk unbounded predictions → cancellation error blow-up; cheap insurance). PARITY contract reframing at line 73-79 of amended plan verified clean: 3-boundary table (v5.14.10↔v5.14.11 tolerance 1e-9 / within-v5.14.11 cfg=0↔cfg=1 tolerance ~1e-13 / scalar↔AVX-512 bytewise identical) matches the math. Stamp-binding HMAC chain integrity preserved via `BITMAP_IS_SET(...) ? 1 : 0` ternary normalization (3 ridge_* fields are confirmed boolean throughout codebase). Full audit report: `plans/plan_checks/parity-check-2026-05-11-v5.14.11-AMENDED.md`.
- **2026-05-12** — `/parity-check` audit of v5.15.5 per-horizon TP/SL serving plan (pre-coding gate). Verdict: **YELLOW** (proceed with 4 must-fix amendments before Phase A coding). 1 new PARITY entry written: PARITY-024 (HIGH; per-arm trained TP/SL barriers stamped at training but not consumed at serving; closes a v5.13.5 multi-horizon training-side ship that left the serving-side incomplete). 7 findings total: F1 LOW (Tier 1 loose-mode noise — acceptable), F2 MEDIUM (shadow JSON locale pinning missing in plan spec — add `newlocale(LC_NUMERIC_MASK, "C", 0)` per Bandit_SaveJSON precedent), F3 HIGH (missing PerCoreSnap fields for modes 3-4 — bundle `barrier_mode_used` + `barrier_shadow_event_count` into Phase A failure-mode registry extension), F4 MEDIUM (Rule 1 arm_names extraction caller enumeration — plan A.1 must list all 3-4 callers + add sizeof shrinkage static_assert), F5 DOCUMENT-ONLY (AVX-512 sizing without SHA-256 lock — vectorization correctly deferred to v5.15.6), F6 MEDIUM (Q1 fallback semantics for mixed v5.15.5+legacy ensemble — plan answer correct; add rate-limited WARN), F7 HIGH (HMAC byte preservation — barrier_blend_mode row must be APPENDED at END of FOREACH_STAMP_BOUND_CFG after `trading_mode` line 175-176). HMAC chain preservation analyzed clean if append-at-end discipline followed. Per-arm reward observability invariant (CLAUDE.md item 24) verified to HOLD under modes 3 + 4 (barriers are output policy, not the prediction grading signal). STAMP_CFG_AUTOPOPULATE handles `barrier_blend_mode` field-population across all production callers automatically (no PARITY-009-style class can recur). Bandit arm_names extraction analyzed — `Bandit_LoadJSON` does NOT round-trip arm_names so persistence path is safe; only `Bandit_Print` + `Bandit_SaveJSON` + EngineTUI legacy-bandit reader need update. Full audit report: `plans/plan_checks/parity-check-2026-05-12-v5.15.5-per-horizon-tp-sl-serving.md`.
- **2026-05-13** — `/parity-check` audit of v5.15.5.C.3 Phase 3b complete (commit d410525, post-coding gate). Verdict: **GREEN** (proceed to Phase 4 — FOREACH_CORE_CTX_SUMMARY_FIELD + JSON emitter). Focus: snapshot v8 wire-format byte-preservation (FOREACH_OMS_FIELD canonical 8-tuple registry with PERSIST view projection); kill_switch_tripped BIT+PERSIST extraction; event_log_mode int→2-bit-slot SKIP_PERSIST verification; OrderManager_Init signature change (added `int partial_exit_enabled` 4th positional). 1 new PARITY entry written: PARITY-025 (HIGH; BacktestSharded.hpp:194-201 retains stale external SET/CLR mirror for MASK_OMS_STATE_PARTIAL_EXIT_ENABLED — Class 18 mirror NOT fully eliminated by Finding A; EngineSharded was cleaned, sister site missed; ZERO behavioral impact today since both sites derive from same cfg expression, but parity hazard + documentation drift class). 5 findings total: HIGH-1 (PARITY-025), MEDIUM-1 (stale experiments — `experiments/per_core_sharding/test_oms*.cpp` 13 callers don't compile post-3b; not in `./build.sh test`; TECH_DEBT candidate), MEDIUM-2 (round-trip persist test direct-asserts only 3 of 10 PERSIST fields — ks_peak_balance + 6 v6 OMS counters not directly asserted; downstream byte-stream-corruption catches misordering indirectly; ~15 min bundle-fix), LOW-1 (event_log_mode > 1 silent 2-bit truncation; defer until mode 2-3 added), LOW-2 (no static_assert lock on PERSIST view row count = 10; ~10 min defensive lock). WIRE-FORMAT BYTE-PRESERVATION VERIFIED CLEAN row-by-row (10 PERSIST rows match legacy registry order byte-for-byte; SAVE + LOAD + COMMIT macro expansions emit identical bytes to pre-3b; sizeof(int)=4 for kill_switch_tripped wire size preserved). EVENT_LOG_MODE int field removal layout verified clean (alignas(64) cluster anchors hold; 4 byte saving per OMS). Engine/backtest parity for partial_exit_enabled derivation verified (both sites use same `BITMAP_IS_SET(cfg.lifecycle_cfg_flags, MASK_LIFECYCLE_CFG_PARTIAL_EXIT_ENABLED) ? 1 : 0`). All 4 reader sites for event_log_mode migrated correctly (BITMAP_NONE/BITMAP_ANY/MBS_EQ_U8 semantic-equivalent to pre-3b int comparisons). All production callers of OrderManager_Init (4) pass partial_exit_enabled; controller_test.cpp 16 callers + test_event_log_head_to_head.cpp 1 caller updated. Tests pass 3052/3052. ML stamp surfaces UNTOUCHED (verified). Per-arm reward observability invariant (CLAUDE.md item 24) preserved (no bandit / per-arm grading paths touched). Full audit report: `plans/plan_checks/parity-check-2026-05-13-v5.15.5.C.3-phase3b.md`.

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
