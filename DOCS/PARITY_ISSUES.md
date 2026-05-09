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
- **Status:** **CLOSED** (FIXED in v5.14.1.B.2; verified by /parity-check rerun 2026-05-09 against HEAD bb5d57e — Section I PASS)
- **Workaround:** N/A (closed)

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
- **Status:** **CLOSED** (FIXED in v5.14.1.B.1; verified by /parity-check rerun 2026-05-09 against HEAD bb5d57e — UpdateAndMark wired at ControllerEventLoop:1299 + PortfolioController:623)
- **Workaround:** N/A (closed)

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
- **Status:** **CLOSED** (FIXED in v5.14.1.B.1; verified by /parity-check rerun 2026-05-09 against HEAD bb5d57e — BindCompositeCfg wired at EngineSharded:1250 + PortfolioController:403)
- **Workaround:** N/A (closed)

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
- **Target ship:** v5.14.1.B.3 (FOREACH_STAMP_BOUND_CFG X-macro registry)
- **Status:** **CLOSED** (FIXED in v5.14.1.B.3; verified by /parity-check rerun 2026-05-09 against HEAD bb5d57e — Section L production-caller audit PASS)
- **Workaround:** N/A (closed)

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
- **Target ship:** v5.14.1.B.3 (bundled with PARITY-004 = ONE X-macro registry covers both)
- **Status:** **CLOSED** (FIXED in v5.14.1.B.3; verified by /parity-check rerun 2026-05-09 against HEAD bb5d57e — Section F + Section L PASS)
- **Workaround:** N/A (closed)

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
