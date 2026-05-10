# Tech Debt — running ledger of deferred architectural items

**Established 2026-05-09 (v5.14.2.E.3).** Workspace-private (symlinked into engine repo as `DOCS/TECH_DEBT.md`).

## Purpose

Append-only ledger of known-deferred architectural cleanups + their triggers. Same shape as `PARITY_ISSUES.md` (proven mechanism) but for items that aren't bugs (operator policy: not a parity finding, not a known issue, not a recurring class). Just architectural debt that needs to live somewhere queryable.

## Why this exists

Caramel's pushback 2026-05-09 (v5.14.2.E review): "what if I forget about that stuff, like doesn't addressing the deferred items now make future maintenance easier?"

The answer is: address now if architecturally bounded; defer if separate concern. But deferred items hidden in code comments / postmortems / chat memory get forgotten. This ledger surfaces them.

`/readiness` Check 25 enforces: before declaring a ship complete, scan TECH_DEBT.md for items in the ship's surface area. If any apply, decide explicitly — address now OR refresh the entry with current cost estimate. Don't silently leave it stale.

## Format per entry

```
### TECH_DEBT-NNN — <one-line title>

- **Created:** YYYY-MM-DD by <ship that surfaced it>
- **Severity:** LOW / MEDIUM / HIGH (impact if NEVER addressed)
- **Surface:** which subsystem / file path
- **What's deferred:** 1-3 sentence description
- **Why deferred (not effort-avoidance):** explicit rationale (e.g., "wider scope than ship; operator-edge; orthogonal concern")
- **Cost estimate:** hours; LOC; risk
- **Trigger:** specific event that should prompt addressing (e.g., "next time stamp body schema changes", "before v5.X release", "when count > 5")
- **Status:** OPEN / IN-FLIGHT / CLOSED / NOT-A-BUG
- **Cross-ref:** related PARITY entries, code locations, plans

Status transitions:
- OPEN → IN-FLIGHT when ship starts addressing
- IN-FLIGHT → CLOSED when shipped
- OPEN → NOT-A-BUG if review determines it's not actually debt
```

## Status definitions

- **OPEN** — known debt, not yet scheduled
- **IN-FLIGHT** — ship in progress is addressing
- **CLOSED** — fixed in a specific ship (cite commit/tag)
- **NOT-A-BUG** — review determined this isn't actually debt

## Auto-write contract (set 2026-05-09)

When `/readiness` Check 25, `/merge-scan`, `/parity-check`, or any other audit identifies a deferral candidate, the agent **MUST** auto-write the entry here. Don't defer to "operator copies after review" — the ledger is single source of truth. Same discipline as PARITY_ISSUES.md auto-write contract (CLAUDE.local.md).

A finding that exists only in a transient audit report or chat memory gets re-discovered as noise.

## Cross-references

- `DOCS/PARITY_ISSUES.md` — sister ledger for parity findings (different class)
- `DOCS/RECURRING_BUG_PATTERNS.md` — bug class catalog
- `CLAUDE.md` item 19 — "Structural fix > direct patch when bug class can recur" (philosophy)
- `CLAUDE.local.md` — going-forward rules including this auto-write contract

## Issues

### TECH_DEBT-001 — Replace `tools/stamp_model.sh` bash CLI with thin C++ wrapper binary

- **Created:** 2026-05-09 by v5.14.2.E.3 (initial population; debt accrued since v5.10.0a.G.2)
- **Severity:** MEDIUM
- **Surface:** `tools/stamp_model.sh` (operator-side bash CLI; ~382 LOC of shell)
- **Class:** Same shape as v5.9.5b production-caller class — parallel implementation that drifts. Bash CLI duplicates the LOGIC of `stamp_write_for_model` (canonical body construction + HMAC computation + `.stamp` write) in shell, instead of CALLING the C++ function directly.
- **What's deferred:** Replace bash CLI with thin C++ wrapper binary `stamp_writer_cli` that:
  1. Parses command-line args (model_path, secret, role, etc.)
  2. Constructs `StampInferenceCfgInputs` from args
  3. Calls `tt::stamp_write_for_model` (same code path as C++ suite Train Model)
  4. Reports success/failure via exit code

  This eliminates the parallel implementation. Single source of truth in C++. Adding a new stamp body field auto-flows through:
  - C++ X-macro / manual emit code (already in place)
  - C++ wrapper binary (one CLI flag added; calls existing function)
  - Python trainers (call binary instead of bash CLI)
- **Why this is better than "catch up bash":** Catching up bash CLI is recurring debt — every new stamp body field requires bash editing in lockstep. Replacing bash CLI eliminates the class. Same philosophy as STAMP_CFG_AUTOPOPULATE (eliminate the bug class structurally).
- **Why deferred (not effort-avoidance):** Operator-edge tooling — most operators already use C++ suite Train Model button (which has full coverage). Bash CLI is for advanced users stamping Python-trained models outside the suite. The replacement requires:
  - New CMakeLists.txt target for `stamp_writer_cli` binary
  - ~150 LOC C++ wrapper (arg parse + StampInferenceCfgInputs build + call + result handling)
  - Python trainer scripts updated to call binary instead of bash
  - Documentation update (operator migration)
  - Bash CLI eventually deletable

  Cleaner long-term but requires C++ build for users who currently run the bash standalone. Defer because the C++ suite path is the primary recommended workflow.
- **Cost estimate:** ~3-4h (vs ~2h for catch-up); ELIMINATES recurring class. LOW risk (additive binary; bash stays as deprecation path).
- **Trigger:** Address when (a) operator reports CLI-stamped model rejected by engine due to missing field, OR (b) v5.X+ adds another stamp body field (would otherwise compound bash catch-up), OR (c) Python trainer scripts get refactored.
- **Bash catch-up alternative (not recommended):** ~2h of mechanical bash editing for ~18 missing fields:
  - v5.10.0a.G.2: `grid_member_count`, `grid_member_idx`
  - v5.11.41: `label_lookahead_ticks`, `label_tp_pct`, `label_sl_pct`, `xgb_train_nthread`
  - v5.14.1.B.3: 5 Ridge cfg fields, 5 composite cfg fields
  - v5.14.1.D: 2 winsor cfg fields
  - v5.14.1.E: `exit_blender_mode`
  - v5.14.2.E.2.A: `ml_buy_threshold`, `gap_acceptable_threshold`
  - v5.14.2.E.2.B: 4 architectural fields
  Recurring debt class survives.
- **Status:** OPEN
- **Cross-ref:** v5.14.1 post-mortem; v5.14.2.E.2.B commit message; CLAUDE.md item 19 (structural fix > direct patch when bug class can recur) — applies here: replace bash CLI structurally vs catching up the parallel implementation.

---

### TECH_DEBT-002 — Centralized engine `ControllerEventLoop` removal

- **Created:** 2026-05-09 by v5.14.2.E.3
- **Severity:** LOW
- **Surface:** `CoreFrameworks/ControllerEventLoop.hpp` + boot dispatch
- **What's deferred:** Legacy single_core LIVE engine path is deprecated (warns at boot per CLAUDE.md preamble). Code still exists. Legacy backtest already wraps sharded path. Removing centralized engine would clean up the codebase but requires:
  - Audit all references to centralized path
  - Update CLAUDE.md to remove centralized references
  - Migration guide for any users still on centralized path
  - Potentially breaking changes if any cfg fields were centralized-only
- **Why deferred (not effort-avoidance):** Already warned at boot; no active operator known to be using it; removal is its own ship; no architectural pressure to remove now. Path is stable + ignored, not actively maintained.
- **Cost estimate:** ~3h; MEDIUM risk (might break edge cases); should land its own dedicated ship.
- **Trigger:** Address when (a) operator complains about deprecated path warning frequency, OR (b) v6.X major-version cleanup, OR (c) maintaining centralized code blocks a refactor.
- **Status:** OPEN
- **Cross-ref:** CLAUDE.md preamble; v5.14.2.E.1 audit (confirmed: zero ensemble/single-zoo post-load code in centralized path = nothing to refactor in current scope).

---

### TECH_DEBT-003 — `verify_model_stamp` parser refactor to data-driven dispatch

- **Created:** 2026-05-09 by v5.14.2.E.3 (first noted in v5.14.1 post-mortem)
- **Severity:** LOW
- **Surface:** `ML_Headers/ModelInference.hpp` `verify_model_stamp` function (~700 LOC)
- **What's deferred:** Parser uses if-else chain over ~30 stamp body keys. Adding a new key requires manual `else if (strcmp(key, "...") == 0) { ... }` branch. Could be refactored to data-driven dispatch (table of `{key, parser_fn, has_field, value_field}`) so adding a key becomes a 1-line table entry. Same shape as FOREACH_STAMP_BOUND_CFG (which solved this for cfg-bound subset).
- **Why deferred (not effort-avoidance):** Parser is stable + works correctly. Refactor is pure cleanup, not closing bugs. v5.14.1.B.3's X-macro for cfg fields already solved the worst growth-rate subset (cfg fields). Architectural fields (4 today) added in v5.14.2.E.2.B grow slowly enough that manual is acceptable for now.
- **Cost estimate:** ~2h; MEDIUM risk (parser correctness is critical — every stamp loaded depends on it).
- **Trigger:** Address when (a) parser key count grows > 40, OR (b) operator-reports a parser bug + we want to harden the surface, OR (c) v5.X+ adds another major field family.
- **Status:** OPEN
- **Cross-ref:** v5.14.1 post-mortem; FOREACH_STAMP_BOUND_CFG (`StampBoundCfgRegistry.hpp`) shows the canonical pattern.

---

### TECH_DEBT-004 — Dual-tau cfg field naming clarity

- **Created:** 2026-05-09 by v5.14.2.E.3 (originally PARITY-006; reclassified as TECH_DEBT since not a parity issue)
- **Severity:** LOW
- **Surface:** `ControllerConfig.hpp` cfg fields `confidence_freshness_tau` (legacy IC) + `confidence_freshness_tau_secs` (composite confidence; v5.14.1)
- **What's deferred:** Two distinct cfg fields with overlapping semantics ("freshness tau"). Both have legitimate uses (one is bandit IC freshness; other is composite confidence freshness in seconds), but the names are confusable. Operator could set one when meaning the other. Either rename for clarity OR consolidate if they should genuinely be the same value.
- **Why deferred (not effort-avoidance):** Operator-facing rename is a config migration (engine.cfg files in production use the old names). Consolidation requires architectural decision (are they really the same?). Both are minor compared to other v5.X work.
- **Cost estimate:** ~3h (rename + migration code + operator notification + cfg.example update); LOW risk.
- **Trigger:** Address when (a) operator misconfigures one for the other, OR (b) v6.X major-version cfg cleanup, OR (c) someone wants to consolidate them with paired analysis.
- **Status:** OPEN
- **Cross-ref:** PARITY-006 (originally raised there); `ControllerConfig.hpp` (search for `freshness_tau`).

---

### TECH_DEBT-005 — Single-zoo hot-swap strict-mode failure handling unification

- **Created:** 2026-05-09 by v5.14.2.E.3 (surfaced during v5.14.2.E.1 design)
- **Severity:** LOW
- **Surface:** `CoreFrameworks/EngineSharded.hpp` ~line 2820 (single-zoo hot-swap validate failure handling)
- **What's deferred:** Boot does Free + null + flag on validate failure. Hot-swap does flag-only on validate failure (preserves v5.10.0c "log-and-leave" semantics; comment at 2803-2806 explicitly notes "TODO v5.10: free handle + return-from-boot to enforce refuse properly"). The asymmetry is intentional today (pre-swap state isn't snapshotted, so true rollback would require infrastructure) but ideally hot-swap would also free + null on strict refuse.
- **Why deferred (not effort-avoidance):** Pre-swap snapshotting infrastructure is significant scope (would let hot-swap properly roll back to previous model). Today's flag-only behavior is operator-tolerable + documented. v5.14.2.E.1 didn't change this; it stayed at caller level intentionally.
- **Cost estimate:** ~4-6h (snapshot infrastructure + revert logic + tests); MEDIUM risk (must not break in-flight predictions).
- **Trigger:** Address when (a) operator hits a hot-swap that breaks engine + complains about not having safe rollback, OR (b) v5.X+ ships safe-rollback infrastructure for some other purpose (could leverage), OR (c) "true safety" becomes a cfg-policy goal.
- **Status:** OPEN
- **Cross-ref:** `EngineSharded.hpp:2803-2806` comment; v5.14.2.E.1 PARITY-009.F closure (which preserved the asymmetry).

---

### TECH_DEBT-006 — `FOREACH_STAMP_BOUND_MODEL_CONST` registry for architectural fields ✅ CLOSED v5.14.8

- **Created:** 2026-05-09 by v5.14.2.E.3 (during v5.14.2.E.2.B design)
- **Severity:** LOW
- **Surface:** `ML_Headers/ModelInference.hpp` (architectural fields added manually in v5.14.2.E.2.B)
- **What was deferred:** 4 architectural fields (`expected_num_classes`, `expected_role`, `expected_num_features`, `expected_feature_format_version`) added with manual emit + parse + populator (separate from FOREACH_STAMP_BOUND_CFG which only handles cfg-bound fields). Refactor to parallel X-macro registry `FOREACH_STAMP_BOUND_MODEL_CONST(X)` that handles training-time/build-time-derived fields.
- **Cost estimate:** ~2h to design + extract registry; LOW risk (additive refactor).
- **Status:** ✅ **CLOSED v5.14.8 (2026-05-09).** Substantially exceeded original scope:
  - **32 architectural fields** auto-flow from registry (originally 4 named; expanded to cover all v5.14.2 + earlier architectural fields)
  - **Option 1 unification** across ModelStampResult / StampInferenceCfgInputs / ModelHandle to canonical wire-key names
  - **Bit-packed has_flags uint64_t** (TECH_DEBT-013 BIT_FLAG storage class win for stamp body)
  - **PRE_CFG/POST_CFG split** preserves canonical wire format byte-for-byte (HMAC chain unbroken)
  - **STAMP_MODEL_CONST_AUTOPOPULATE** companion macro extinguishes v5.9.5b production-caller class for stamp body
  - **Reusable BITMAP_* API** (`MemHeaders/BitmapMacros.hpp`) used by sister registries
  - **Round-trip HMAC verification test** (v5.14.8.A.7; 32 fields populated; emit→parse→verify)
  - **5 NEW v5.14.8 fields** added via POST_CFG registry (training_timestamp_us, run_name, scaler_fit_data_hash, removal_reasons_csv, environment_meta group of 5)
  - **Stale-model gate** (v5.14.8.E) consumes training_timestamp_us
- **Future field addition:** 1 row in `FOREACH_STAMP_BOUND_MODEL_CONST_PRE_CFG` or `_POST_CFG` → struct fields + parser + emitter + AUTOPOPULATE wiring all auto-flow.
- **Cross-ref:** v5.14.8 umbrella ship; `DESIGN_SPECS/x-macro-registry-with-presence-dispatch.md`, `DESIGN_SPECS/pre-post-cfg-registry-split-for-emit-order-preservation.md`, `DESIGN_SPECS/autopopulate-pattern-for-production-caller-class.md`, `DESIGN_SPECS/bitmap-flag-api.md`; CLAUDE.md items 13, 20, 21, 22, 23.

---

### TECH_DEBT-007 — Empirically verify regime_trend_strength + regime_vol_zscore add information vs existing features

- **Created:** 2026-05-09 by v5.14.5.B (mid-coding audit follow-up; Path C decision)
- **Severity:** LOW
- **Surface:** `ML_Headers/FeatureRegistry.hpp` FOREACH_FEATURE entries `regime_trend_strength` + `regime_vol_zscore`
- **What's deferred:** v5.14.5.B ships 2 features whose semantic differs from existing ones in normalization characteristics:
  - `regime_trend_strength` (regression slope normalized to [-1,1] saturating) vs `SHORT_SLOPE` (slope/avg unbounded ratio)
  - `regime_vol_zscore` (z-score: (x-mean)/stddev; sign-carrying; bounded) vs `VOL_RATIO` (short_var/long_var; positive only ratio)

  The differing normalization MAY produce complementary training signal OR may train identically (depending on operator's data + model architecture). Without empirical verification on real training runs, we don't know which.
- **Why deferred (not effort-avoidance):** Cannot static-analyze whether features add marginal information; requires actual training metrics (feature importance scores, ablation studies, marginal predictive accuracy gain). Operator-decision rather than engineering-decision.
- **Verification trigger:** After v5.14.5 first full retrain cycle:
  - Train with all features enabled → record feature_importance scores
  - If `regime_trend_strength` importance < 0.01 AND `SHORT_SLOPE` importance > 0.05 → likely redundant
  - Same check for `regime_vol_zscore` vs `VOL_RATIO`
  - If both pass redundancy check → drop in v5.X+ ship via FEATURE_REGISTRY_HASH bump (forces operator retrain to clean schema)
  - If at least one shows complementary signal → keep + document the empirical evidence
- **Cost estimate:** ~30 min training-metric review post-first-retrain; ~30 min cleanup ship if drop indicated
- **Trigger:** After v5.14.5's first full retrain cycle (operator runs Multi-Horizon training); review feature_importance dump
- **Status:** OPEN
- **Cross-ref:** v5.14.5.B commit; `ML_Headers/FeatureRegistry.hpp` Compute fn comments cite this entry; v5.14.5.B "empirical-verification discipline" section in plan

---

### TECH_DEBT-008 — Maker order MVP (v5.14.7) deferred until order book data captured

- **Created:** 2026-05-09 by v5.14.6 close (operator decision pre-v5.14.8)
- **Severity:** MEDIUM (blocks maker fee path; engine remains taker-only until addressed)
- **Surface:** `CoreFrameworks/OrderManager.hpp` (Order struct + SubmitCommand), `DataStream/BinanceOrderAPI.hpp` (POST_ONLY submit + cancel REST), `CoreFrameworks/EngineSharded.hpp` (slow-path price-ladder), `Backtest/BacktestSharded.hpp` (queue-position fill simulation for full impl)
- **What's deferred:** Full Maker order path. v5.14.7 plan (`plans/2026-05-08-v5.14.7-maker-order-mvp.md`) was a 4-sub-tag MVP (~550 LOC) for cfg-gated POST_ONLY LIMIT submit + drainer cancel-and-replace. Operator deferred 2026-05-09 because no order book data has been captured (DepthRecorder not run; no historical depth CSVs available for backtest replay). MVP path-ladder logic + drainer cancel sweep + REST endpoints are foundation work the full implementation reuses unchanged (~90% of MVP code is in full impl).
- **Why deferred (not effort-avoidance):** Without order book data, MVP gives no testing surface — backtest can't replay LIMIT fills (no depth CSVs to advance `DepthReplayState`); live paper-test would work but is operator's call. Operator chose: defer entire maker work to a comprehensive master plan once depth data exists, vs ship MVP-now-foundation that can't be paper-validated. NOT effort-avoidance — total effort is the same (~30-45h either path); sequencing differs.
- **Cost estimate:**
  - MVP-now path: ~6h ship + ~25-40h v6.0 full = ~30-45h total
  - Defer-to-master path: ~30-45h v6.0 master plan with comprehensive design (queue-position simulation, depth-aware offset, fill-rate feedback, race reconciliation, fee rebate, multi-level depth)
- **Trigger:** When operator captures order book data (via `DepthRecorder` runs, or external depth-tape feed). At that point either:
  - Reopen v5.14.7 MVP plan + ship as foundation
  - OR draft v6.0 maker master plan covering full scope (recommended: this matches operator's defer-to-master decision)
- **Status:** OPEN
- **Cross-ref:** `plans/2026-05-08-v5.14.7-maker-order-mvp.md` (MVP plan; deferred); `plans/2026-05-08-MASTER-v5.14-foxml-port-and-maker.md` Phase 3 (master plan reference); existing depth infrastructure: `DataStream/BinanceDepth.hpp` (`BookSnapshot<F>` with bids[5]/asks[5]), `DataStream/DepthReplayState.hpp` (per-tick replay; needs CSV input), `DataStream/DepthRecorder.hpp` (capture path; not currently run); v5.14.6 close commit (predecessor)

---

### TECH_DEBT-009 — FOREACH_CFG_FIELD registry for non-stamp-bound cfg fields

- **Created:** 2026-05-09 by v5.14.8 scope decision (Interpretation B; deferred N-site pattern audit)
- **Severity:** MEDIUM (every new cfg field = 4-site manual update: parser line + struct field + engine.cfg.example entry + CHANGELOG note; recurring class)
- **Surface:** `CoreFrameworks/ControllerConfig.hpp` (struct), `CoreFrameworks/ControllerConfigParser.hpp` (parser), `engine.cfg.example` (operator-facing reference), `DOCS/CHANGELOG.md` (migration notes per ship)
- **What's deferred:** Convert non-stamp-bound cfg field additions from manual N-site updates to a `FOREACH_CFG_FIELD` registry + companion `CFG_FIELD_AUTOPOPULATE` macro. Each registry entry would auto-generate: struct field declaration, parser case, default value, engine.cfg.example doc line. Stamp-bound cfg fields are already covered by `FOREACH_STAMP_BOUND_CFG` (StampBoundCfgRegistry.hpp); this would be the sister registry for non-stamped cfg.
- **Why deferred (not effort-avoidance):** v5.14.8 work doesn't touch cfg parser subsystem; conversion would be scope creep into a different file family. Cfg parser has its own discipline (back-compat + boot WARN cadence) that needs design conversation before mechanical conversion. Different blast radius from stamp body work (parser changes affect EVERY operator's cfg loading).
- **Cost estimate:** ~6-8h structural ship (registry + macro + docs); ~30-40 cfg fields to migrate; per-field migration trivial (~5 min each)
- **Trigger:** Next ship that adds 3+ new non-stamp-bound cfg fields in one umbrella, OR ship that touches ControllerConfigParser.hpp for any reason. At that point address structurally instead of compounding the manual pattern.
- **Status:** OPEN
- **Cross-ref:** `ML_Headers/StampBoundCfgRegistry.hpp` (sister registry for stamp-bound cfg; pattern precedent); v5.14.8 (sibling structural ship for stamp body); CLAUDE.md item 13 (X-macro audited categories list — this entry would join)

---

### TECH_DEBT-010 — FOREACH_CALIB_LOG_COL registry for calibration log CSV columns

- **Created:** 2026-05-09 by v5.14.8 scope decision (Interpretation B; deferred N-site pattern audit)
- **Severity:** LOW (small N currently; CSV columns relatively stable; pattern still recurring)
- **Surface:** Calibration log CSV writer (`CoreFrameworks/CalibrationLog.hpp` or similar), reader/parser (post-process tooling), header definition
- **What's deferred:** Convert calibration log CSV column additions from manual 3-site updates (header constant + writer column + reader/parser column) to a `FOREACH_CALIB_LOG_COL` registry. Each registry entry would auto-generate header position, writer printf format, reader scanf format.
- **Why deferred (not effort-avoidance):** v5.14.8 work doesn't touch calibration log path; small N (currently ~20 columns) means manual pattern is tractable. Worth converting only when the next ship tries to add ≥3 columns and would otherwise compound the pattern.
- **Cost estimate:** ~3-4h structural ship; ~20 columns to migrate; trivial per-column
- **Trigger:** Next ship that adds 3+ calibration log columns in one umbrella (e.g., maker-side fill metrics when v6.0 maker ships, or new ML observability columns), OR ship that touches the CSV writer/reader for any reason.
- **Status:** OPEN
- **Cross-ref:** v5.13.0.B calibration log infrastructure; v5.14.7 deferred plan (would have added 4 maker-related columns)

---

### TECH_DEBT-011 — FOREACH_PER_CORE_SNAP_FIELD registry for general visible-state snapshot fields

- **Created:** 2026-05-09 by v5.14.8 scope decision (Interpretation B; deferred N-site pattern audit)
- **Severity:** MEDIUM (large N: ~30+ visible-state fields; recurring class but performance-sensitive)
- **Surface:** `DataStream/EngineTUI.hpp` (PerCoreSnap struct + populator), `GUI/DashboardPanels.hpp` + sister panels (consumers), snapshot capture/copy paths
- **What's deferred:** Convert PerCoreSnap general visible-state field additions (positions, gates, predictions, regime, etc.) to a `FOREACH_PER_CORE_SNAP_FIELD` registry. Each entry auto-generates struct field, populator (capture from CoreContext / EventLoopCoreState), GUI-side accessor.
- **Why deferred (not effort-avoidance):** Distinct from FOREACH_FAILURE_MODE (v5.14.8 covers failure-mode fields specifically; this would cover the LARGER set of visible state). Performance-sensitive: snapshot capture runs in slow-path tail; registry expansion needs to preserve existing memcpy-friendly layout. Needs design conversation about: (a) whether to split capture into hot/warm/cold tiers, (b) whether registry entries should declare their write cadence, (c) cache-line alignment preservation. NOT a mechanical conversion.
- **Cost estimate:** ~10-15h architectural ship (design + registry + migration of ~30 fields + tests); requires preceding design doc
- **Trigger:** Next ship that adds 5+ PerCoreSnap general fields in one umbrella (likely v5.X+ ML observability work or v6.0 maker), OR ship that audits PerCoreSnap layout for cache performance.
- **Status:** OPEN (needs design doc before implementation)
- **Cross-ref:** v5.14.8.B+C (FOREACH_FAILURE_MODE; sister registry for the failure-mode subset); CLAUDE.md item 12 (display ↔ execution invariant — every hot-path predicate term needs PerCoreSnap field; current pattern is manual)

---

### TECH_DEBT-013 — Bit-packed boolean flags (BIT_FLAG storage class) for byte-per-flag patterns across codebase

- **Created:** 2026-05-09 by v5.14.8.B FOREACH_FAILURE_MODE design discussion (operator question: "couldnt we track each one using a single bit since theyre basically 1 or 0?")
- **Severity:** MEDIUM (recurring inefficiency; data-oriented design alignment opportunity; aligns with CLAUDE.md item 1 Portfolio uint16_t bitmap pattern)
- **Surface:** Multiple — see candidate inventory below
- **Pattern definition:** Replace `uint8_t` boolean flag fields with bit-packed `uint16_t` / `uint32_t` / `uint64_t` bitmap. X-macro entries declare `BIT_FLAG` storage class; X-macro auto-allocates bit positions + generates `MASK_##name` constants + ergonomic `IS_SET` / `SET` / `CLR` accessor macros. Wins: memory compactness (16-64 flags in 2-8 bytes), branchless multi-flag check via mask (`flags & (MASK_X | MASK_Y)`), branchless "any flag set?" check (`flags != 0`), atomic multi-flag updates via `__atomic_fetch_or`.
- **Pattern precedent:** `Portfolio<uint16_t>` bitmap (CLAUDE.md item 1); `OrderManagerState.order_bitmap` (uint16_t); v5.14.8.B `FailureModeRegistry.hpp` (newly established X-macro pattern with BIT_FLAG / COUNTER_U32 / PERCENT_U8 storage classes).
- **What's deferred:** Apply BIT_FLAG storage class to byte-per-flag patterns NOT in v5.14.8's active touch surface. Each target gets its own focused ship (or folds into the next ship that touches that surface).

**Candidate inventory (sweep 2026-05-09):**

| Surface | Current flags | Bit-pack target | Effort | Trigger |
|---|---|---|---|---|
| `failure_flags` (FOREACH_FAILURE_MODE) | 2 | uint16_t | DONE in v5.14.8.B | — |
| Stamp body `has_*` (FOREACH_STAMP_BOUND_MODEL_CONST) | 24+ | uint64_t (`has_flags`) | IN-SCOPE v5.14.8.A | — |
| `PerCoreSnap` non-failure state flags (ml_scaler_present, ensemble_active, etc.) | 3-5 | merge into failure_flags OR new `state_flags` uint16_t | ~3-4h | Next ship touching PerCoreSnap layout |
| `FOREACH_FEATURE` `enabled` flag | 40 features | uint64_t (`enabled_bitmap`) + `IS_FEATURE_ENABLED(i)` macro | ~3-4h | Next ship touching FeatureRegistry storage layout |
| `OrderManager.partial_exit_enabled` + `ExecutionCore.lat_enabled` | 2 | engine-wide uint16_t `cfg_flags` | ~1-2h | Next ship adding 3+ engine-wide cfg flags |
| `ControllerEventLoop.partner_pending_active` (per-core) | 1 | merge into per-core flags bitmap (NEW; or fold into `failure_flags`) | ~1h | Next ship adding 2+ per-core boolean flags |
| `ShardedSnapshot.any_scaler_present` + `any_scaler_failed` | 2 | merge into snapshot summary bitmap | ~1h | Next ship touching ShardedSnapshot serialization |

- **Why deferred (not effort-avoidance):** Each surface has DIFFERENT caller-migration scope; bundling all into one ship would explode blast radius. Pattern-as-design-tool: future ships touching any of these surfaces apply BIT_FLAG storage class as part of the work. v5.14.8 demonstrates the pattern + establishes the ergonomic API; subsequent ships extend it.
- **Cost estimate:** ~10-15h cumulative across all candidates (1-4h each); incremental per ship.
- **Trigger:** Each candidate listed above has its own trigger (next ship touching that surface). Pattern documentation in `DOCS/EASY_ADDITIONS_INVARIANTS.md` (added in v5.14.8.0 docs) tells future maintainers to apply BIT_FLAG when adding boolean flags.
- **Memory savings (cumulative if all applied):** ~70-100 bytes per core; cache-line alignment benefits compound. ~16 cores × ~80B = ~1.3 KB system-wide.
- **Status:** OPEN (pattern established in v5.14.8.B; candidates listed for systematic application as triggered)
- **Cross-ref:** v5.14.8.B (pattern establishment in `MemHeaders/FailureModeRegistry.hpp`); CLAUDE.md item 1 (Portfolio uint16_t bitmap precedent); CLAUDE.md item 18 (data-oriented design + branchless mask compute philosophy); `DOCS/EASY_ADDITIONS_INVARIANTS.md` (pattern documentation; updated in v5.14.8.0)

---

### TECH_DEBT-012 — FOREACH_OMS_STATE registry for OrderManager state fields

- **Created:** 2026-05-09 by v5.14.8 scope decision (Interpretation B; deferred N-site pattern audit)
- **Severity:** MEDIUM (recurring pattern; performance-CRITICAL surface — drainer thread reads OMS state every cycle)
- **Surface:** `CoreFrameworks/OrderManager.hpp` (OrderManagerState struct + Init), drainer thread reads, snapshot save/load
- **What's deferred:** Convert OMS state field additions to a `FOREACH_OMS_STATE` registry. Each entry auto-generates struct field, Init zero/default, snapshot serializer/deserializer, drainer-thread accessor.
- **Why deferred (not effort-avoidance):** PERFORMANCE-CRITICAL surface — drainer thread reads OrderManagerState every cycle in production. Registry expansion MUST preserve current cache-line layout + alignas() decorators (RAII destructor on resource-owning structs per CLAUDE.md exception note). Conversion needs benchmarking before/after to verify no slowdown. Distinct concern from stamp body conversion (which is boot-only). Needs design conversation about: (a) whether to use intrusive macro at struct definition site or hoisted registry, (b) snapshot serialization round-trip preservation (Class 4 risk), (c) cache-line span analysis after conversion.
- **Cost estimate:** ~12-18h architectural ship (design + benchmarking + registry + migration + snapshot round-trip tests + cache-line analysis); requires preceding design doc + bench gate
- **Trigger:** Next ship that adds 3+ OMS state fields in one umbrella (likely v6.0 maker order lifecycle states), OR ship that touches OMS struct layout for cache performance optimization.
- **Status:** OPEN (needs design doc + bench plan before implementation)
- **Cross-ref:** v5.14.4 (recent OMS work; added last_seen_trade_id field manually); v5.14.7 deferred (would have added 4 maker-related Order struct fields manually); CLAUDE.md item 5 (OMS submit funneling discipline); RAII destructor exception in OrderManager.hpp:~v5.11.26

---

## Future debt findings will append here

When `/readiness` Check 25 OR `/merge-scan` OR any audit identifies deferral candidates:
1. Assign next TECH_DEBT-NNN
2. Fill in the format template above
3. Set initial status (usually OPEN)
4. Cross-link from the audit report (`plans/plan_checks/*`)
5. Reference in commit message of the closing ship
6. Move to CLOSED only after a follow-up audit confirms regression-free

---

### TECH_DEBT-014 — ModelHandle migration to FOREACH_STAMP_BOUND_MODEL_CONST X-macro generation

- **Created:** 2026-05-09 by v5.14.8.A.merged.2 (deferred during Option 1 unification scope)
- **Severity:** LOW
- **Surface:** `ML_Headers/ModelInference.hpp` ModelHandle struct (~line 238)
- **What's deferred:** ModelHandle currently uses MANUAL field declarations for stamp-derived runtime fields (with `stamp_inf_*`, `stamp_xgb_*`, `stamp_label_*`, `stamp_*` prefix policy that's INCONSISTENT across groups). v5.14.8.A.merged migrated ModelStampResult + StampInferenceCfgInputs to X-macro generation but ModelHandle stayed manual because it's a PARTIAL MIRROR (only fields needed at runtime; ~10 fields exist on ModelStampResult but NOT on ModelHandle; per-group prefix policy diverges).
- **Why deferred (not effort-avoidance):** Migration requires deciding ModelHandle's per-group prefix dispatch (or going full canonical-name). v5.14.8 ship was already large (~2400 LOC across A.0.b + A.merged.X); ModelHandle migration would have added another ~150 LOC of caller migrations. Bounded follow-up work; low risk because the FAILURE_MODE registry's STAMP_HANDLE_GEN_INCLUDE/SKIP_HANDLE token-paste dispatch is already designed for the partial-mirror case.
- **Cost estimate:** ~2-3h (ModelHandle struct rewrite via X-macro + 10-15 caller files: CoreModelZoo_TryLoadRole copy block + EngineSharded boot WARN comparisons + StrategyParameters reads).
- **Trigger:** Address when (a) ModelHandle gains a NEW stamp-derived field (would be the next instance of the manual N-site pattern), OR (b) v5.X+ cleanup ship dedicated to ModelHandle restructuring, OR (c) operator hits ModelHandle-specific naming inconsistency in code review.
- **Status:** OPEN
- **Cross-ref:** v5.14.8.A.merged.2 commit; ModelHandle struct in `ML_Headers/ModelInference.hpp:238`; v5.14.8.E manually added has_training_timestamp_us + has_run_name fields directly to ModelHandle (deferred path).

---

### TECH_DEBT-015 — FOREACH_FEATURE 7-col extension (max_staleness_minutes) + Features_PackAll stale-feature wiring

- **Created:** 2026-05-09 by v5.14.8.E (stale-feature gating scope split)
- **Severity:** LOW
- **Surface:** `ML_Headers/FeatureRegistry.hpp` (FOREACH_FEATURE registry), `ML_Headers/FeatureRegistry.hpp` Features_PackAll, `ML_Headers/FeatureRegistry.hpp` FeatureComputeCtx
- **What's deferred:** v5.14.8.E added the stale_feature_events COUNTER_U32 entry to FOREACH_FAILURE_MODE (registry + counter slot + panel constants ready) but did NOT wire Features_PackAll to actually consume per-feature staleness thresholds. Full wiring requires:
  - FOREACH_FEATURE 7-column extension: append `max_staleness_minutes` column (per-feature threshold; 0 = disabled). All 7+ X-macro caller sites in FeatureRegistry.hpp update to 7-param signature; hash-compute caller body still reads only (name, version) so FEATURE_REGISTRY_HASH stays stable.
  - `feature_last_update_us[NUM_REGISTERED_FEATURES]` array storage on FeatureComputeCtx (or via per-feature compute fn capturing `now_us`).
  - Features_PackAll stale check: `if (max_staleness_minutes[i] > 0 && (now_us - last_update_us[i]) / 60000000ULL > max_staleness_minutes[i]) { features[i] = 0.0f; stale_feature_events_total++; continue; }`
  - Slow-path latency: ~40ns when configured; HOT_PATH_CHANGELOG entry needed.
- **Why deferred (not effort-avoidance):** v5.14.8.E delivered the high-value stale-MODEL gate (boot-time refuse on operator-deploying-expired-models). Stale-FEATURE gate is value-add but not blocking; bounded follow-up. Feature pipeline wiring spans 7+ X-macro caller sites + FeatureComputeCtx + per-feature compute fns + retest.
- **Cost estimate:** ~2-3h (FOREACH_FEATURE column add + 7 caller-site updates + Features_PackAll wiring + HOT_PATH_CHANGELOG entry + tests).
- **Trigger:** Address when (a) operator wants per-feature freshness UI control, OR (b) next feature added to FOREACH_FEATURE (would touch the X-macro anyway; bundle the column extension), OR (c) v5.X+ ML pipeline cleanup ship.
- **Status:** OPEN
- **Cross-ref:** v5.14.8.E commit; FOREACH_FAILURE_MODE entry `stale_feature_events` in `MemHeaders/FailureModeRegistry.hpp` (counter slot + panel infrastructure ready).
