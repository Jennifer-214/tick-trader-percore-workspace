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
- **DEFERRED-INDEFINITE** — debt acknowledged but no near-term plan to ship; trigger documented (often external dependency outside operator's control). Distinct from OPEN (which implies "scheduled or schedulable"). If/when trigger event occurs, status flips back to OPEN.

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

### TECH_DEBT-004 — Dual-tau cfg field naming clarity ✅ CLOSED v5.14.9.D

- **Created:** 2026-05-09 by v5.14.2.E.3 (originally PARITY-006; reclassified as TECH_DEBT since not a parity issue)
- **Severity:** LOW
- **Surface:** `ControllerConfig.hpp` cfg fields `confidence_freshness_tau` (legacy IC) + `confidence_freshness_tau_secs` (composite confidence; v5.14.1)
- **What was deferred:** Two distinct cfg fields with overlapping semantics ("freshness tau"). Operator could set one when meaning the other.
- **Status:** ✅ **CLOSED v5.14.9.D (2026-05-10, commit b703e61).** Hard-deletion path: legacy `confidence_freshness_tau` was mathematically inert (`data_age=0` always in production; half-dead via stamp-bound drift check on a value that doesn't affect inference). Deleted entirely from ControllerConfig + 5 ConfidenceScorer_Init callsites adapted (3-arg → 2-arg signature). Legacy stamps with `inference_cfg_freshness_tau` line load successfully (parser ignores unknown key via existing forward-compat semantics; HMAC chain unbroken because HMAC is per-stamp). Operator migration: WARN log if legacy key present in cfg file ("remove from cfg"). Only `confidence_freshness_tau_secs` remains (composite-confidence freshness; not confusable since the legacy field is gone).
- **Cross-ref:** PARITY-006 (originally raised there); v5.14.9.D commit b703e61 (engine repo); v5.14.9 umbrella.

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

### TECH_DEBT-008 — Maker order MVP (v5.14.7) deferred indefinitely (no consistent order book data source)

- **Created:** 2026-05-09 by v5.14.6 close (initial decision pre-v5.14.8)
- **Status changed:** 2026-05-09 (post-v5.14.8 close) → **DEFERRED-INDEFINITE**. Caramel's framing: "permanently defer this, im not sure when ill ever get a consistent source for orderbook data."
- **Severity:** MEDIUM-DEFERRED (blocks maker fee path; engine stays taker-only indefinitely; not actively scheduled)
- **Surface:** `CoreFrameworks/OrderManager.hpp` (Order struct + SubmitCommand), `DataStream/BinanceOrderAPI.hpp` (POST_ONLY submit + cancel REST), `CoreFrameworks/EngineSharded.hpp` (slow-path price-ladder), `Backtest/BacktestSharded.hpp` (queue-position fill simulation for full impl)
- **What's deferred:** Full Maker order path. v5.14.7 plan (`plans/v5.14-foxml-port-and-maker/subplans/2026-05-08-v5.14.7-maker-order-mvp.md`) was a 4-sub-tag MVP (~550 LOC) for cfg-gated POST_ONLY LIMIT submit + drainer cancel-and-replace. MVP path-ladder logic + drainer cancel sweep + REST endpoints are foundation work the full implementation reuses unchanged (~90% of MVP code is in full impl).
- **Why deferred indefinitely (NOT effort-avoidance):** No reliable / consistent source for historical order book depth data has been identified. Without depth data:
  - Backtest can't replay LIMIT fills (no depth CSVs to advance `DepthReplayState`)
  - Queue-position simulation (the core of full impl realism) has nothing to simulate against
  - Live paper-test alone is insufficient validation — engine would ship taker-only without backtest parity
  - Free Binance archives don't expose full depth history; commercial tape feeds (Tardis, Kaiko, CoinAPI) cost $$ ongoing and Caramel has no current budget allocation; running DepthRecorder live for months to bootstrap own corpus is feasible but no firm start date and no commitment
- **Total effort if reactivated:** ~30-45h (split as MVP-foundation ~6h + v6.0 master plan ~25-40h, OR single comprehensive v6.0 plan ~30-45h)
- **Trigger to reopen (status flips DEFERRED-INDEFINITE → OPEN):** Any of:
  - Caramel runs `DepthRecorder` long enough to bootstrap a usable depth corpus (months of capture for one symbol)
  - External depth-tape feed becomes accessible (Tardis subscription, Kaiko sample, etc.)
  - Architectural decision to ship live-only maker path without backtest validation (currently policy is "backtest validation required before live")
- **What this means operationally:**
  - v5.14 sprint umbrella DOES NOT block on this entry (already excluded from Phase 4)
  - `/readiness` Check 25 (TECH_DEBT scan) may still surface this entry when it greps for files-touched overlap — operator dismisses by status (DEFERRED-INDEFINITE = no action expected). Convention: don't re-debate the dismissal each ship; only revisit if the trigger conditions above appear met.
  - Maker-related comments in code (e.g., RESERVED enums in OrderType) stay as-is — they're cheap forward-compat hooks, not orphan WIP
- **Status:** **DEFERRED-INDEFINITE**
- **Cross-ref:** `plans/v5.14-foxml-port-and-maker/subplans/2026-05-08-v5.14.7-maker-order-mvp.md` (MVP plan; deferred); `plans/v5.14-foxml-port-and-maker/MASTER.md` Phase 3 (master plan reference); existing depth infrastructure: `DataStream/BinanceDepth.hpp` (`BookSnapshot<F>` with bids[5]/asks[5]), `DataStream/DepthReplayState.hpp` (per-tick replay; needs CSV input), `DataStream/DepthRecorder.hpp` (capture path; not currently run); v5.14.6 close commit (predecessor)

---

### TECH_DEBT-009 — FOREACH_CFG_FIELD registry for non-stamp-bound cfg fields (boolean subset CLOSED v5.14.9.F.4)

- **Created:** 2026-05-09 by v5.14.8 scope decision (Interpretation B; deferred N-site pattern audit)
- **Severity:** MEDIUM → LOW (boolean subset closed; non-boolean field registry remains as future work)
- **Surface:** `CoreFrameworks/ControllerConfig.hpp` (struct), `CoreFrameworks/ControllerConfigParser.hpp` (parser), `engine.cfg.example` (operator-facing reference), `DOCS/CHANGELOG.md` (migration notes per ship)
- **Status:** **PARTIAL CLOSED v5.14.9.F.4 (2026-05-10).** Boolean cfg fields (21 booleans across 5 domains) migrated to `FOREACH_<DOMAIN>_CFG_FLAG` registries with single-source-of-truth semantics. Parser auto-flows via 5 FOREACH walks (~21 inline branches → 5 walks, ~90 LOC reduction). GUI field_defs[] auto-extends via 5-col tuple expansion (v5.14.9.F.5 Option D). Per-core override extends via PER_CORE_OVERRIDE_BITMAP_DOMAINS macro (v5.14.9.F.6).
- **Remaining (still OPEN as broader scope):** non-boolean cfg fields (FPN<F> thresholds, ints, strings, paths). Still touched manually per-field today. Future ship: `FOREACH_CFG_FIELD` registry for non-boolean fields (mirrors boolean subset's auto-flow discipline; same pattern with type-trait dispatch).
- **Why partial close not full:** non-boolean cfg fields are heterogeneous in type + parser semantics (atoi vs atof vs strncpy); each type needs its own auto-flow path. Boolean subset was tractable (all parse identically via `int v = atoi(val); set/clr bit`). Type-trait dispatch via templated helpers (per CLAUDE.md item 23) can extend to other types but adds design surface.
- **Cost estimate (remaining):** ~6-8h for FOREACH_CFG_FIELD registry covering ~30-40 non-boolean fields; per-field migration trivial.
- **Trigger:** Next ship that adds 3+ new non-boolean cfg fields in one umbrella, OR ship that touches ControllerConfigParser.hpp for non-boolean reasons.
- **Cross-ref:** v5.14.9.F-.F.6 ships (boolean subset closure); `DESIGN_SPECS/heterogeneous-registry-pattern.md` (DOMAIN SPLIT pattern reference impl); `ML_Headers/StampBoundCfgRegistry.hpp` (sister registry for stamp-bound cfg; pattern precedent); CLAUDE.md item 13 (X-macro audited categories list).

---

### TECH_DEBT-010 — FOREACH_CALIB_LOG_COL registry for calibration log CSV columns ✅ CLOSED v5.14.10.D

- **Created:** 2026-05-09 by v5.14.8 scope decision (Interpretation B; deferred N-site pattern audit)
- **Severity:** LOW (small N currently; CSV columns relatively stable; pattern still recurring)
- **Surface:** Calibration log CSV writer (`CoreFrameworks/CalibrationLog.hpp` or similar), reader/parser (post-process tooling), header definition
- **What's deferred:** Convert calibration log CSV column additions from manual 3-site updates (header constant + writer column + reader/parser column) to a `FOREACH_CALIB_LOG_COL` registry. Each registry entry would auto-generate header position, writer printf format, reader scanf format.
- **Why deferred (not effort-avoidance):** v5.14.8 work doesn't touch calibration log path; small N (currently ~20 columns) means manual pattern is tractable. Worth converting only when the next ship tries to add ≥3 columns and would otherwise compound the pattern.
- **Cost estimate:** ~3-4h structural ship; ~20 columns to migrate; trivial per-column
- **Trigger:** Next ship that adds 3+ calibration log columns in one umbrella (e.g., maker-side fill metrics when v6.0 maker ships, or new ML observability columns), OR ship that touches the CSV writer/reader for any reason.
- **Status:** **CLOSED v5.14.10.D** — `DataStream/CalibLogColRegistry.hpp` (NEW) defines FOREACH_CALIB_LOG_COL with the existing 9 columns; `OrderManager_HandleFill` row emit + `OpenCalibrationLog` header emit refactored to walk the registry; byte-format preservation (operator-parser compat) maintained. DESIGN_SPECS doc `calibration-log-column-registry.md` (NEW) captures the methodology + lists future candidate logs (MetricsLog + ShardedTradeLog scheduled for v5.14.10.F per /merge-scan N2 finding).
- **Cross-ref:** v5.13.0.B calibration log infrastructure; v5.14.7 deferred plan (would have added 4 maker-related columns); v5.14.10.D commit (TBD); `DESIGN_SPECS/calibration-log-column-registry.md`.

---

### TECH_DEBT-031 — MetricsLog FOREACH registry refactor (multi-writer row-shape mismatch)

- **Created:** 2026-05-10 by v5.14.10.F scope-cap decision (ShardedTradeLog migration shipped via FOREACH_TRADE_LOG_COL; MetricsLog deferred due to writer-shape heterogeneity)
- **Severity:** LOW (cosmetic; existing 2-writer pattern works; pattern would help future column additions but not blocking)
- **Surface:** `DataStream/MetricsLog.hpp` — 27-column CSV with 2 writers producing DIFFERENT row shapes:
  - `MetricsLog_SlowPath`: cols 1-26 populated; col 27 (details) blank
  - `MetricsLog_Event`: cols 1-13 populated; cols 14-26 blank (12 commas); col 27 (details) populated
- **Class:** Same N-site sister-literal class as TECH_DEBT-010 (header constant + writer fprintf + reader parser updated in lockstep when adding a column). But the row-SHAPE divergence between the 2 writers makes a single-registry awkward — neither Variant A (fprintf direct) nor Variant B (snprintf to buffer) of `calibration-log-column-registry.md` cleanly fits.
- **What's deferred:** Apply FOREACH_METRICS_LOG_COL registry to MetricsLog. Requires design pass on how to handle the writer-shape divergence:
  - Option 1: 27-col registry; each writer fills caller-scope variables (with empty-string sentinel for non-populated cols); registry walk emits "" for empty-marked cols. Requires per-column NULLABILITY semantic.
  - Option 2: SHAPE column in registry tuple (X(name, fmt, expr_slow, expr_event)); registry walk dispatches per-writer. Requires 4-col tuple instead of 3-col.
  - Option 3: Per-writer registry walks (FOREACH_METRICS_LOG_COL_SLOW_PATH + FOREACH_METRICS_LOG_COL_EVENT). Defeats single-source-of-truth (now 2 registries to keep in sync — exactly what we're trying to avoid).
- **Why deferred (not effort-avoidance):** v5.14.10.F's primary win is establishing the registry pattern across log writers (calib + trade). MetricsLog requires a design decision (Option 1 vs 2 vs 3) that's better made with operator input on how MetricsLog SlowPath vs Event semantics should evolve. Forcing a choice now risks locking in the wrong shape; deferring lets the next contributor decide based on what the next column needing addition actually looks like.
- **Cost estimate:** ~150-250 LOC for the registry + writer refactors + snapshot tests; design discussion time ~30-60 min. Per CLAUDE.md "Three similar lines is better than a premature abstraction" — wait until 3rd MetricsLog column addition forces the question.
- **Trigger:** Address (a) when next ship adds 3+ columns to MetricsLog (forcing the design decision), OR (b) operator-driven cleanup sprint targeting MetricsLog architecture.
- **Status:** OPEN
- **Cross-ref:** v5.14.10.F commit (TBD); `DESIGN_SPECS/calibration-log-column-registry.md` "Pattern variants" section + "Future application candidates" table; TECH_DEBT-010 (sister entry, CLOSED v5.14.10.D); /merge-scan 2026-05-10 v5.14.10 amended-plan finding N2 (originally bundled MetricsLog + ShardedTradeLog; trade log shipped, metrics deferred).

---

### TECH_DEBT-030 — cfg=2 dual-mode calibration log telemetry columns (deferred from v5.14.10.D)

- **Created:** 2026-05-10 by v5.14.10.D scope-cap decision (FOREACH_CALIB_LOG_COL refactor shipped; cfg=2-specific columns deferred for cross-component plumbing)
- **Severity:** LOW (operator-facing diagnostic feature; cfg=2 dispatch ships in v5.14.10.B; calibration log columns visualize the A/B comparison offline)
- **Surface:** `DataStream/CalibLogColRegistry.hpp` FOREACH_CALIB_LOG_COL registry; `CoreFrameworks/OrderManager.hpp` HandleFill calibration log row emit; `CoreFrameworks/OrderManager.hpp` OMS state per-slot fields for predict-time → fill-time data flow
- **What's deferred:** Add 3 cfg=2 dual-mode telemetry columns to FOREACH_CALIB_LOG_COL: `exp3_chosen_arm`, `thompson_chosen_arm`, `regime_id_at_pick`. Empty / -1 sentinels when cfg.bandit_algorithm != 2. Requires cross-component plumbing: capture exp3 + thompson chosen arms + regime at predict time (in ML_BuildParameters slow path), persist to fill time (per-slot OMS state OR Order struct field), read at HandleFill calib log row write.
- **Why deferred (not effort-avoidance):** v5.14.10.D ships the FOREACH_CALIB_LOG_COL pattern + REFACTORS the existing 9-column writer (closes TECH_DEBT-010 structurally). Cfg=2 telemetry columns require ADDITIONAL plumbing across 3 components (slow-path predict → OMS state → drainer-thread fill emit) that's a separate concern. Would have grown .D from ~250 LOC to ~400+ LOC. Better as a focused micro-ship (v5.14.10.E or v5.14.11+) once the cross-component data flow is designed.
- **Cost estimate:** ~100-150 LOC. Add 3 OMS per-slot fields (mirror `last_exit_predicted_arm` shape; ~30 LOC). Populate at slow-path predict (mirror `last_exit_was_predicted` population at EngineSharded.hpp:3144-3145; ~20 LOC). Read in HandleFill calib log row (caller scope contract update; ~10 LOC). Add 3 entries to FOREACH_CALIB_LOG_COL (~5 LOC). Tests for round-trip cfg=2 → calib log row (~30 LOC). Total ~95-115 LOC of focused work + tests.
- **Trigger:** Address (a) when operator initiates first paper-test session with cfg.bandit_algorithm=2 (dual-mode A/B), OR (b) when v5.14.10.E ships (would naturally bundle), OR (c) when v5.14.11+ adds another bandit-related per-fill telemetry need (consolidation candidate).
- **Status:** OPEN
- **Cross-ref:** v5.14.10.B (cfg=2 dispatch shipped; data sources `ezoo->last_predicted_horizon_idx` + `ezoo->last_predicted_thompson_arm` + `ezoo->last_predicted_regime_id` available at predict time); v5.14.10.D (closes TECH_DEBT-010 via FOREACH_CALIB_LOG_COL refactor; this entry tracks the deferred cfg=2 columns); `DataStream/CalibLogColRegistry.hpp` "FUTURE COLUMNS" comment block; `DESIGN_SPECS/calibration-log-column-registry.md` "FUTURE APPLICATION CANDIDATES" table.

---

### TECH_DEBT-011 — FOREACH_PER_CORE_SNAP_FIELD registry for general visible-state snapshot fields

- **Created:** 2026-05-09 by v5.14.8 scope decision (Interpretation B; deferred N-site pattern audit)
- **Severity:** MEDIUM (large N: ~30+ visible-state fields; recurring class but performance-sensitive)
- **Surface:** `DataStream/EngineTUI.hpp` (PerCoreSnap struct + populator), `GUI/DashboardPanels.hpp` + sister panels (consumers), snapshot capture/copy paths
- **What's deferred:** Convert PerCoreSnap general visible-state field additions (positions, gates, predictions, regime, etc.) to a `FOREACH_PER_CORE_SNAP_FIELD` registry. Each entry auto-generates struct field, populator (capture from CoreContext / EventLoopCoreState), GUI-side accessor.
- **Why deferred (not effort-avoidance):** Distinct from FOREACH_FAILURE_MODE (v5.14.8 covers failure-mode fields specifically; this would cover the LARGER set of visible state). Performance-sensitive: snapshot capture runs in slow-path tail; registry expansion needs to preserve existing memcpy-friendly layout. Needs design conversation about: (a) whether to split capture into hot/warm/cold tiers, (b) whether registry entries should declare their write cadence, (c) cache-line alignment preservation. NOT a mechanical conversion.
- **Cost estimate:** ~10-15h architectural ship (design + registry + migration of ~30 fields + tests); requires preceding design doc
- **Trigger:** Next ship that adds 5+ PerCoreSnap general fields in one umbrella (likely v5.X+ ML observability work or v6.0 maker), OR ship that audits PerCoreSnap layout for cache performance.
- **Status:** OPEN — partially addressed by v5.14.10.0 (cluster alignment dimension)
- **Progress (v5.14.10.0):** the cache-line alignment dimension (sub-bullet (c) of "Why deferred") is now ADDRESSED via `per-snapshot-cluster-layout-pattern.md` (NEW DESIGN_SPECS) + first reference application (PerCoreSnap bandit telemetry cluster with `alignas(64)` boundary + compile-time `static_assert(offsetof)` enforcement). Future contributors have a documented methodology + working example for cluster boundaries. The FULL `FOREACH_PER_CORE_SNAP_FIELD` registry conversion (sub-bullets (a) and (b): hot/warm/cold tier split + write-cadence-declared registry entries) remains DEFERRED — those are higher-scope architectural changes that warrant their own focused ship.
- **Cross-ref:** v5.14.8.B+C (FOREACH_FAILURE_MODE; sister registry for the failure-mode subset); v5.14.10.0 (`per-snapshot-cluster-layout-pattern.md` DESIGN_SPECS + first application); CLAUDE.md item 12 (display ↔ execution invariant — every hot-path predicate term needs PerCoreSnap field; current pattern is manual)

---

### TECH_DEBT-013 — Bit-packed boolean flags (BIT_FLAG storage class) for byte-per-flag patterns across codebase ✅ CLOSED v5.14.9

- **Created:** 2026-05-09 by v5.14.8.B FOREACH_FAILURE_MODE design discussion (operator question: "couldnt we track each one using a single bit since theyre basically 1 or 0?")
- **Severity:** MEDIUM (recurring inefficiency; data-oriented design alignment opportunity; aligns with CLAUDE.md item 1 Portfolio uint16_t bitmap pattern)
- **Surface:** Multiple — see candidate inventory below
- **Pattern definition:** Replace `uint8_t` boolean flag fields with bit-packed `uint16_t` / `uint32_t` / `uint64_t` bitmap. X-macro entries declare `BIT_FLAG` storage class; X-macro auto-allocates bit positions + generates `MASK_##name` constants + ergonomic `IS_SET` / `SET` / `CLR` accessor macros. Wins: memory compactness (16-64 flags in 2-8 bytes), branchless multi-flag check via mask (`flags & (MASK_X | MASK_Y)`), branchless "any flag set?" check (`flags != 0`), atomic multi-flag updates via `__atomic_fetch_or`.
- **Pattern precedent:** `Portfolio<uint16_t>` bitmap (CLAUDE.md item 1); `OrderManagerState.order_bitmap` (uint16_t); v5.14.8.B `FailureModeRegistry.hpp` (newly established X-macro pattern with BIT_FLAG / COUNTER_U32 / PERCENT_U8 storage classes).
- **What's deferred:** Apply BIT_FLAG storage class to byte-per-flag patterns NOT in v5.14.8's active touch surface. Each target gets its own focused ship (or folds into the next ship that touches that surface).

**Candidate inventory (sweep 2026-05-09):**

| Surface | Current flags | Bit-pack target | Effort | Trigger |
|---|---|---|---|---|
| `failure_flags` (FOREACH_FAILURE_MODE) | 2 | uint16_t | ✅ DONE v5.14.8.B | — |
| Stamp body `has_*` (FOREACH_STAMP_BOUND_MODEL_CONST) | 24+ | uint64_t (`has_flags`) | ✅ DONE v5.14.8.A | — |
| `PerCoreSnap` non-failure state flags (permission, bitmap_consistency, gate_direction, is_ml, ml_model_loaded, strategy_was_explicit_set, ladder_bottom_hit) | 6→7 | uint16_t `state_flags` + MASK_* registry | ✅ DONE v5.14.9.B.2 | — |
| `FOREACH_FEATURE` `enabled` flag | 40 features | uint64_t `FEATURE_ENABLED_BITMAP` + `IS_FEATURE_ENABLED(i)` macro | ✅ DONE v5.14.9.E | — |
| Engine-wide cfg bool flags (21 across 5 domains) | 21 | 5 domain bitmaps via `FOREACH_<DOMAIN>_CFG_FLAG` registries | ✅ DONE v5.14.9.F-.F.6 | — |
| `ControllerEventLoop.partner_pending_active` (per-core) | 1 | uint16_t `partner_pending_bitmap` on EventLoopState (1 bit per core) | ✅ DONE v5.14.9.G | — |
| `ShardedSnapshot.any_scaler_present` + `any_scaler_failed` | 2 | uint8_t `scaler_summary_flags` transient local with 6-bit headroom | ✅ DONE v5.14.9.H | — |

- **Status:** ✅ **CLOSED v5.14.9 (2026-05-10).** All 7 candidates migrated. Cumulative wins:
  - Memory saved: 15B per ControllerConfig (21 scattered ints → 5 bitmap fields) + 126B per EventLoopState (per-core bool → 2-byte bitmap) + scaler aggregation tightened
  - Single-source-of-truth registries: registry = enum + MASK + parser + AUTOPOPULATE + GUI label + section + tooltip + per-core override (Option D 5-col tuple expansion v5.14.9.F.5)
  - HMAC chain byte-equivalence proven for stamp-bound bit-extract entries (v5.14.9.F.2 Y3 dispatch)
  - Per-bit per-core override capability via PER_CORE_OVERRIDE_BITMAP_DOMAINS (v5.14.9.F.6)
  - Cache-layout discipline applied (HOT-CLUSTER alignas(8) at start of 5 domain bitmaps; cold-cluster split deferred to TECH_DEBT-021 post-paper-test profiling)
  - Pattern documented in `DESIGN_SPECS/heterogeneous-registry-pattern.md` (DRAFT v0.1 → ACTIVE v1.0 after .F-.F.6 field tests validated all 4 pre-field-test concerns)
- **Why valuable:** every future bool cfg flag = 1 row in registry → ALL downstream consumers auto-flow. Recurring "add bool flag = N-site update" class extinguished structurally for booleans (FOREACH_CFG_FIELD broader closure for non-boolean fields tracked under TECH_DEBT-009 partial).
- **Cross-ref:** v5.14.9.F-.F.6 + .G + .H ships; `DESIGN_SPECS/heterogeneous-registry-pattern.md` (canonical pattern doc); CLAUDE.md item 1 (Portfolio bitmap precedent); item 18 (data-oriented design + branchless mask compute philosophy); `DOCS/EASY_ADDITIONS_INVARIANTS.md` (pattern documentation).

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

### TECH_DEBT-015 — FOREACH_FEATURE 7-col extension (max_staleness_minutes) + Features_PackAll stale-feature wiring ✅ CLOSED v5.14.9.E

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
- **Status:** ✅ **CLOSED v5.14.9.E (2026-05-10).** FOREACH_FEATURE extended 6→7 columns with `max_staleness_minutes`; `FEATURE_ENABLED_BITMAP` uint64_t replaces 40 uint8_t bool fields (312 bytes saved per FeatureComputeCtx); `IS_FEATURE_ENABLED(i)` macro; Features_PackAll do-while wrapper for staleness check skip; `feature_last_update_us[NUM_REGISTERED_FEATURES]` array storage on FeatureComputeCtx; stale_feature_events_total counter (was infrastructure-only since v5.14.8.E; now functional).
- **Cross-ref:** v5.14.8.E commit (infrastructure); v5.14.9.E commit (wiring closed); FOREACH_FAILURE_MODE entry `stale_feature_events` in `MemHeaders/FailureModeRegistry.hpp`; CHANGELOG v5.14.9 row.

---

### TECH_DEBT-017 — Direct-int cfg-flag cohort migration to FOREACH_ML_CFG_FLAG (ridge_within_horizon / ridge_across_horizons / exit_blender_mode / ridge_online_corr) ✅ CLOSED v5.14.11.C

- **Created:** 2026-05-11 by /readiness Check 16 + /dod-audit HIGH-1 finding during v5.14.11 pre-coding gate
- **Severity:** LOW (cosmetic / discipline; no behavior or perf impact)
- **Surface:** `ControllerConfig.hpp` (3 direct `int` cfg fields prior to .C: `ridge_within_horizon`, `ridge_across_horizons`, `exit_blender_mode`); `ML_Headers/MlCfgFlagRegistry.hpp` (already housing 7 ML/confidence flags pre-.C); `CoreFrameworks/SlowPathGateRegistry.hpp` (cached gate predicates); `ML_Headers/StampBoundCfgRegistry.hpp` (stamp-binding entries for ridge_within + ridge_across + exit_blender + ridge_lambda + ridge_cost_penalty + ridge_min_ic_floor); `Strategies/StrategyParameters.hpp` (buy + exit Ridge dispatch sites + their fallback paths)
- **Class:** Same shape as `confidence_composite_enabled` migration (v5.14.9.F.2) — direct `int` cfg field that's load-bearingly toggled at slow-path gate + stamp-bound at the wire boundary; cohort-eligibility per `DESIGN_SPECS/cfg-flag-eligibility-criteria.md` (passes all 5 criteria: boolean semantics, slow-path predicate, parser-friendly key=value form, no analog-knob ambiguity, hot-path cache-line participation). Per CLAUDE.md item 19 (structural fix preferred when bug class can recur), single-row registry addition >> N-site duplication risk.
- **What's deferred → done:** Migrate 3 direct fields off `ControllerConfig` into `FOREACH_ML_CFG_FLAG` bitmap entries (RIDGE_WITHIN_HORIZON, RIDGE_ACROSS_HORIZONS, EXIT_BLENDER_MODE); add new RIDGE_ONLINE_CORR entry for the v5.14.11 online-correlation toggle landing in same ship; flip 3 stamp-binding `emit_source=DIRECT_FIELD` entries to `BITMAP_BIT` with ternary normalization `? 1 : 0` for byte-equivalence on the HMAC chain; update 2 SlowPath gate predicates + add new RIDGE_ONLINE_CORR_ACTIVE gate; refactor 2 Ridge dispatch sites for branchless multi-flag mask check (CLAUDE.md item 18) — single AND+compare when gate_state present; wire `use_online` from gate_state via MASK_RIDGE_ONLINE_CORR_ACTIVE; migrate 4 cfg parser tests + 4 stamp-body autopopulate tests + 4 slow-path gate state tests in `tests/controller_test.cpp`.
- **Why valuable:** Every future ML/confidence boolean cfg flag = 1 row in FOREACH_ML_CFG_FLAG + AUTOPOPULATE handles fan-out across stamp-binding + slow-path gate + dispatch sites + parser + tests. Recurring "add bool flag = N-site update" class extinguished structurally for the Ridge cohort. Slow-path branch density reduced via multi-flag mask check at buy-side Ridge dispatch (2 separate scalar branches → 1 mask AND+compare when gate_state wired).
- **Status:** ✅ **CLOSED v5.14.11.C (2026-05-11).** 4 entries added to FOREACH_ML_CFG_FLAG (Ridge cohort + ridge_online_corr); 3 ControllerConfig direct field declarations + defaults + CFG_PARSE_INT removed (parser auto-routes via FOREACH_ML_CFG_FLAG legacy_field column); 3 stamp-binding entries flipped to BITMAP_BIT with byte-equivalence ternary; 2 SlowPath gate predicates migrated + 1 new RIDGE_ONLINE_CORR_ACTIVE gate added (10 total gates; 6 bits headroom); branchless multi-flag dispatch refactor at buy-side; exit-side migrated; all 2904 tests pass (zero regression).
- **Cross-ref:** v5.14.11.C commit; v5.14.9.F.2 commit (canonical confidence_composite_enabled migration precedent); `DESIGN_SPECS/cfg-flag-eligibility-criteria.md` (decision criteria); `DESIGN_SPECS/heterogeneous-registry-pattern.md` (Y3 dispatch for stamp-binding integration); CLAUDE.md items 18 (branchless mask compute), 19 (structural fix preferred), 20 (BITMAP_* API), 22 (Y3 dispatch); /readiness 2026-05-11 Check 16 + /dod-audit 2026-05-11 HIGH-1 finding (both flagged the cohort migration eligibility pre-coding).

---

### TECH_DEBT-018 — Codify `/precoding-audit` Layer 1 orchestrator skill

- **Created:** 2026-05-10 by v5.14.9.D (post-test-strength-audit ship discussion)
- **Severity:** LOW (workflow improvement; manual dispatch already works)
- **Surface:** `tick-trader-percore-workspace/claude-skills/precoding-audit/SKILL.md` (NEW; doesn't exist yet)
- **What's deferred:** Layer 1 orchestrator skill that dispatches `/readiness` + `/trace-deps` + `/dod-audit` + `/test-strength-audit` + `/merge-scan` as parallel Layer 2 subagents on a plan file, aggregates findings, emits combined report. Codifies the manual 4-agent dispatch pattern that ran successfully during v5.14.9 pre-coding gate.

- **Why deferred (not effort-avoidance):** Manual 4-parallel-agent dispatch from main Layer 1 session worked for v5.14.9 pre-coding gate. Codifying as `/precoding-audit` is workflow improvement, not blocker. Want 3-5 more ship cycles using the manual pattern to identify what the orchestrator should aggregate vs forward (e.g., severity-cross-skill rollup, GREEN/YELLOW/RED unified verdict, conflict detection).

- **Pattern precedent:** `/finding-analyzer` is already a Layer 1 orchestrator skill that "chains existing workspace skills (/trace-deps, /latency-track, /parity-check)". Same shape applies for `/precoding-audit`.

- **Why NOT just modify `/readiness` to spawn nested subagents:** SKILLS_HIERARCHY.md establishes one-way Layer 1 → Layer 2 hierarchy after v5.14.1.G recursion-via-over-delegation incident. Layer 2 skills must NOT spawn further subagents (silently fails / hangs). Adding nested dispatch to `/readiness` would recreate that trap. The right answer is a separate Layer 1 orchestrator.

- **Cost estimate:** ~3-4h (skill spec ~400 lines mirroring `/finding-analyzer` shape + skill registration + SKILLS_HIERARCHY entry + `/readiness` cross-ref)

- **Trigger:** Address when ANY of:
  - 3-5 ship cycles complete using the manual 4-parallel-agent pattern (signal: workflow stable; codify-worthy)
  - Manual dispatch hits friction the orchestrator could fix (e.g., result aggregation pain, missed cross-skill conflicts, race conditions on shared resources)
  - Operator wants single-command pre-coding gate (`/precoding-audit plan-file`) instead of explicit per-skill dispatch

- **Status:** OPEN

- **Cross-ref:** SKILLS_HIERARCHY.md (Layer 1/2 model), `/finding-analyzer` SKILL.md (orchestrator pattern precedent), v5.14.9 pre-coding gate session log (manual 4-agent dispatch worked but had friction — `/trace-deps` report didn't auto-save to disk; agent-dispatch-friction class).

---

### TECH_DEBT-019 — Rejected monolithic FOREACH_ENGINE_CFG_FLAG registry (design rationale preservation)

- **Created:** 2026-05-10 by v5.14.9.F Option C decomposition (post-/dod-audit auto-write per CLAUDE.local.md contract)
- **Severity:** N/A (NOT-A-BUG; rationale-preservation entry)
- **Surface:** Conceptual / design-record only; no code surface
- **What was considered:** Monolithic FOREACH_ENGINE_CFG_FLAG registry covering ~18 boolean cfg fields (partial_exit_enabled, depth_enabled, kill_switch_enabled, confidence_enabled, etc.) → single uint32_t engine_cfg_flags bitmap on ControllerConfig.
- **Why rejected (post-2026-05-10 audits):** /dod-audit + /merge-scan independently identified 4 fatal heterogeneity factors that made the COLUMN form (single registry, single bitmap) wrong fit:
  1. **Read cadences differ:** drainer reads partial_exit_enabled every cycle (hot-path-adjacent); kill_switch_enabled mutated by slow-path; depth_enabled boot-frozen; bandit_enabled slow-path-only. Single bitmap = mixed cache-line semantics.
  2. **Mutation patterns differ:** read-only cfg booleans (depth_enabled) vs runtime-mutated state-like booleans (kill_switch_tripped) vs cfg-loadable-but-immutable-runtime (partial_exit_enabled). Single struct field = false-sharing risk.
  3. **Coupling unrelated features:** bandit_enabled, barrier_gate_enabled, cost_gate_enabled, foxml_vol_scaling_enabled have no semantic overlap; grouping them in one registry is convenience-over-architecture.
  4. **Future-flexibility:** ML domain growing fast (bandit warmup, ridge weights, calibration enables); RISK domain stable. Want to split independently in v5.X+ without restructuring; monolithic doesn't permit.
- **Decision:** DOMAIN SPLIT chosen instead. 5 separate FOREACH_<DOMAIN>_CFG_FLAG registries (OMS / GATE / RISK / ML / OPS). Each domain has homogeneous read cadence + mutation pattern + cache-line concerns. Pattern documented in `DESIGN_SPECS/heterogeneous-registry-pattern.md`.
- **Why this entry exists (NOT-A-BUG):** future sessions reading the codebase may notice "5 small registries; could combine into 1 big one" + propose monolithic refactor. This entry preserves the rejection rationale so that proposal is recognized as design-considered + correctly rejected. Also serves as canonical reference for "when domain-split wins over monolithic" on future heterogeneous-registry decisions.
- **Cost:** 0h (no work to do; this entry is documentation)
- **Trigger to re-litigate:** if, after v5.14.10+ paper-test profiling, the 5 small registries' overhead becomes measurable (e.g., 5 separate AUTOPOPULATE walks at slow-path entry costs >100ns) AND consolidation would actually save cycles AND the heterogeneity factors above no longer apply (e.g., all flags become uniformly slow-path-only with same cache concerns), then revisit. Until then: status NOT-A-BUG.
- **Status:** NOT-A-BUG (preserved as rationale)
- **Cross-ref:** v5.14.9.F-.F.3 (DOMAIN SPLIT implementation); `DESIGN_SPECS/heterogeneous-registry-pattern.md` (decision framework codified); `plans/plan_checks/dod-audit-2026-05-10-v5.14.9-postE.md` + `merge-scan-2026-05-10-v5.14.9-postE.md` (audit findings that drove the rejection)

---

### TECH_DEBT-020 — Per-core override SELECT macro factoring (BITMAP_SELECT)

- **Created:** 2026-05-10 by v5.14.9.F.6 design (/dod-audit MEDIUM.1 finding)
- **Severity:** LOW (micro-opt; defer until threshold met)
- **Surface:** Per-core override resolution sites across cfg-flag domains (5 sites in .F.6); future bitmap-merge sites where override + global must combine branchlessly
- **What's deferred:** Factor the per-core override resolution idiom into a reusable BITMAP_SELECT macro:

  ```cpp
  // Current (.F.6 inline pattern):
  uint8_t effective_oms_flags = ((cfg.cores[c].oms_cfg_flags_override_set & cfg.cores[c].oms_cfg_flags_override) |
                                  (~cfg.cores[c].oms_cfg_flags_override_set & cfg.oms_cfg_flags));

  // Proposed BITMAP_SELECT macro (in MemHeaders/BitmapMacros.hpp):
  #define BITMAP_SELECT(mask, when_set, when_clear) \
      (((mask) & (when_set)) | (~(mask) & (when_clear)))

  // Usage:
  uint8_t effective_oms_flags = BITMAP_SELECT(cfg.cores[c].oms_cfg_flags_override_set,
                                                cfg.cores[c].oms_cfg_flags_override,
                                                cfg.oms_cfg_flags);
  ```

  Branchless bit-by-bit select: bit set in mask → use when_set; bit clear → use when_clear. Single uint op; zero branches.

- **Why deferred (not effort-avoidance):** v5.14.9.F.6 has 5 use sites; CLAUDE.md item 13 threshold (≥3 entries + ≥2 caller sites) is barely met. Premature factor would extract before pattern crystallizes. Mid-flight v5.X+ work may need slight variations (tri-state select; per-bit lifetime), so factoring now risks lock-in.
- **Cost estimate:** ~1h (write macro + migrate 5 call sites + test)
- **Trigger:** Address when (a) 6+ use sites exist (clear pattern with bounded variations), OR (b) v5.X+ ship adds another override-resolution surface (snapshot hot-state vs cfg, OMS state vs cfg), OR (c) operator notices the inline form duplicating across files.
- **Status:** OPEN
- **Cross-ref:** v5.14.9.F.6; `DESIGN_SPECS/bitmap-flag-api.md` (sister BITMAP_* primitives — BITMAP_SELECT would join here when factored)

---

### TECH_DEBT-021 — Post-paper-test profiling: domain bitmap collapse OR further split decisions

- **Created:** 2026-05-10 by v5.14.9.F Option C decomposition (/dod-audit MEDIUM.2 finding + .I scope plan)
- **Severity:** LOW (profiling-driven optimization; depends on paper-test signal)
- **Surface:** ControllerConfig 5 domain bitmap fields (oms_cfg_flags + gate_cfg_flags + risk_cfg_flags + ml_cfg_flags + ops_cfg_flags); FOREACH_<DOMAIN>_CFG_FLAG registries
- **What's deferred:** After v5.14.9.F-.F.6 lands + paper-test runs surface real-world performance signal, profile and decide:

  - **Domain bitmap collapse** (if profiling shows overhead from 5 separate AUTOPOPULATE walks + 5 cache-line accesses per slow-path cycle): collapse to single uint64_t engine_cfg_flags. Trade-offs: lose per-domain cache-line granularity (re-introduces false-sharing risk per TECH_DEBT-019); gain single-load reads for compound predicates.

  - **Further domain split** (if profiling shows one domain growing dominant — e.g., FOREACH_ML_CFG_FLAG hits 8+ entries due to bandit warmup, ridge weights, calibration enables): split FOREACH_ML_CFG_FLAG → FOREACH_ML_CONFIDENCE_CFG_FLAG + FOREACH_ML_BANDIT_CFG_FLAG. Trade-offs: more registry boilerplate; better future-flexibility.

  Decision data: paper-test p99 latency profile per slow-path cycle; per-domain AUTOPOPULATE cost; per-domain cache-line miss rate; per-domain entry growth trajectory.

- **Why deferred (not effort-avoidance):** Cannot profile until paper-test runs. Both alternatives are valid + the choice depends on real signal. Premature optimization either direction would lock in wrong abstraction. v5.14.9 ships baseline; v5.14.10+ ship profiles + decides.
- **Cost estimate:** ~30 min profiling review post-paper-test; ~3-6h ship if collapse OR further split chosen.
- **Trigger:** After first paper-test cycle post-v5.14.9 close (typically v5.14.10+ kickoff). Operator reviews profile data; decides direction or "no change needed".
- **Status:** OPEN
- **Cross-ref:** v5.14.9.F-.F.6 ships; TECH_DEBT-019 (rejected monolithic — this entry's collapse direction is what 019 rejected at design-time; profiling may flip the decision); `DESIGN_SPECS/heterogeneous-registry-pattern.md` cache-layout discipline section

---

### TECH_DEBT-022 — Engine.cfg parser perfect-hash / trie dispatch

- **Created:** 2026-05-10 by v5.14.9.F.4 design (/dod-audit LOW finding — not blocking but flagged for awareness)
- **Severity:** LOW (boot-only path; not latency-critical)
- **Surface:** `CoreFrameworks/ControllerConfigParser.hpp` parse_csv_engine_config function
- **What's deferred:** parse_csv_engine_config currently does ~50 strcmp calls per cfg key (linear scan). After v5.14.9.F.4 closes the boolean subset via 5 macro-walked strcmp loops, ~30 strcmp branches remain for non-boolean cfg fields. A perfect-hash dispatch (gperf-generated) or trie-based prefix tree would eliminate the linear scan, replacing strcmp loops with O(log N) or O(1) dispatch.
- **Why deferred (not effort-avoidance):** Parser is BOOT-ONLY (not on hot/slow path); current ~50 strcmp per key for ~100 cfg keys = ~5000 strcmp at boot. At ~5ns each, total parse overhead ~25µs at boot. Below operator-perceptible threshold. Optimization would shave maybe 10-20µs from boot time — invisible to operators.
- **Cost estimate:** ~4-6h (gperf integration + build-time generation + parser refactor + tests). Plus ongoing maintenance burden if perfect-hash table needs regeneration when registry entries change.
- **Trigger:** Address when (a) operator reports boot latency complaint, OR (b) v6.X cleanup ship batches engine.cfg parser improvements, OR (c) registry entry count grows to >200 (perfect-hash savings start to matter).
- **Status:** OPEN
- **Cross-ref:** v5.14.9.F.4 (boolean subset closed via macro-walk; non-boolean fields remain manual); TECH_DEBT-009 (broader FOREACH_CFG_FIELD scope; would also benefit from perfect-hash dispatch).

---

### TECH_DEBT-023 — `lat_enabled` is NOT cfg-flag-eligible (rationale preservation)

- **Created:** 2026-05-10 by v5.14.9.F step 0 verification (caught audit subagent misread; cfg-flag eligibility criteria need explicit doc to prevent recurrence)
- **Severity:** N/A (NOT-A-BUG; rationale-preservation entry to prevent future re-litigation)
- **Surface:** `CoreFrameworks/ExecutionCore.hpp:295` (`lat_enabled` local var inside `ExecutionCore_Tick_Impl`)
- **Class:** Same shape as TECH_DEBT-019 (rationale preservation for rejected design choice)
- **What was considered (and rejected):** Migrating `lat_enabled` into the new `oms_cfg_flags` / `lifecycle_cfg_flags` bitmap as part of v5.14.9.F. The /readiness audit subagent flagged it as "NOT FOUND in ControllerConfig — must add" because the original plan claimed both partial_exit_enabled + lat_enabled would migrate.
- **Why rejected (verified during step 0 inventory):** `lat_enabled` is NOT a cfg field. It's a per-Tick local variable inside `ExecutionCore_Tick_Impl<F, LAT_ENABLED, PAIR_BRANCHLESS>` template function. Three structural reasons it can't migrate:

  1. **Compile-time elision:** When `LAT_ENABLED=false` (production builds without `-DLATENCY_PROFILING`), `if constexpr (LAT_ENABLED)` block compiles out entirely. **Zero runtime cost** — no atomic load, no branch, no instructions. Migrating to a runtime cfg-flag bitmap REGRESSES this to ~1-2ns per tick perpetually paid in production. At 10M ticks/sec hot-path, that's ~10-20ms/sec of pure waste. Compounds against the 40-400ns hot-path budget that's been carefully tuned.

  2. **Per-core runtime mutability:** When `LAT_ENABLED=true`, the actual gate is `core->latency_stats.enabled.load(std::memory_order_relaxed)` — a per-core atomic. Operator can flip latency sampling on/off per-core via GUI live within a profiled binary. Migrating to engine-wide boot-frozen cfg LOSES this capability.

  3. **CLAUDE.md item 18(a) violation:** "DEFAULT-OFF safety gates use compile-time elision via `template <bool ENABLED>` + `if constexpr` so disabled state has zero cost (no branch, no instruction)". `lat_enabled` is the canonical example of this discipline. Cfg-flag migration is an active violation.

- **Decision:** v5.14.9.F migrates only OMS-DOMAIN-PROPER cfg booleans. `lat_enabled` stays as-is (template-bool + per-core atomic). Domain reframed: `FOREACH_OMS_CFG_FLAG` → `FOREACH_LIFECYCLE_CFG_FLAG` covering 3 position-exit-mechanic flags (partial_exit_enabled + breakeven_on_partial + breakeven_on_profit).

- **Cfg-flag eligibility criteria (codified by this entry):** for a boolean to be cfg-flag-bitmap-eligible, ALL of the following must hold:
  1. **Boot-frozen:** value loaded at startup; not mutated at runtime
  2. **Engine-wide OR per-core-via-override:** not per-core via runtime atomic (those use ParameterSlot pattern)
  3. **Hot-path-tolerant:** runtime read of bitmap bit (~1-2ns) is acceptable cost
  4. **No compile-time elision benefit:** the flag isn't a candidate for `template <bool>` + `if constexpr` removal
  5. **Cfg-domain-coherent:** semantically belongs to one of the 5 domains (LIFECYCLE / GATE / RISK / ML / OPS) or warrants a new domain

  If ANY of (1)-(4) fails, the boolean is NOT cfg-flag-eligible. Use ParameterSlot atomic, template-bool elision, or local computation instead.

- **Why this entry exists (NOT-A-BUG):** future audit subagents may make the same mistake (assuming "boolean used in code = cfg-flag-eligible"). This entry codifies the eligibility criteria as a queryable check. Future /dod-audit Pattern 3e (bit-packing candidates) should reference this entry; future /readiness Check 19 (file:line claims) should validate cfg-flag eligibility against these criteria.

- **Cost:** 0h (no work to do; documentation only)

- **Trigger to revisit:** if the latency-profiling subsystem itself is rewritten (e.g., replaced with hardware perf counters that don't need per-core atomic flip), revisit whether the compile-time-elision pattern is still load-bearing. Until then: status NOT-A-BUG.

- **Status:** NOT-A-BUG (preserved as rationale)

- **Cross-ref:** v5.14.9.F step 0 finding (2026-05-10); `CoreFrameworks/ExecutionCore.hpp:288` (template signature); CLAUDE.md item 18 (slow-path latency reduction priority — sub-clause (a)); `DESIGN_SPECS/heterogeneous-registry-pattern.md` "What's NOT cfg-flag-eligible" section (codifies criteria above).

---

### TECH_DEBT-024 — `breakeven_on_profit` dormant cfg field (defined + parsed; no read sites)

- **Created:** 2026-05-10 by v5.14.9.F step 0 inventory
- **Severity:** LOW (operator-facing dormant feature; no functional impact)
- **Surface:** `CoreFrameworks/ControllerConfig.hpp:377` (declaration), `:1229` (default), `:1887` (parser)
- **What's deferred:** `breakeven_on_profit` is an operator-facing cfg boolean ("ratchet SL to breakeven when position crosses net profit") declared + defaulted + parsed, but has ZERO read sites in the codebase. Operators can set it in engine.cfg; the engine accepts the value without applying it. Either:
  - **Wire it up:** find the intended application site (likely `Strategies/StrategyParameters.hpp` near other SL-ratchet logic) + implement the breakeven-on-profit ratchet
  - **Remove it:** if abandoned, delete from cfg with operator notification (engine.cfg.example update)
- **Why deferred:** v5.14.9.F migrates this flag into FOREACH_LIFECYCLE_CFG_FLAG bitmap as part of TECH_DEBT-013(5) close. The migration is forward-compat with either wire-up or removal. After .F ships, this entry surfaces the decision: wire up vs remove.
- **Cost estimate:** ~30 min if wire-up (locate application site + add BITMAP_IS_SET check + test); ~15 min if removal (delete + cfg.example update + operator migration WARN at boot). **Defer the decision until after .F ships.**
- **Trigger:** Address at v5.14.9.I umbrella close OR next ship that touches lifecycle/exit logic. Operator decides "wire up" vs "remove" then.
- **Status:** OPEN
- **Cross-ref:** v5.14.9.F (migrates flag into bitmap); `CoreFrameworks/ControllerConfig.hpp:377-1229-1887`.

### TECH_DEBT-025 — Convert DESIGN_SPECS docs to invocable skills (long-horizon idea)

- **Created:** 2026-05-10 by v5.14.9.I post-mortem closure (Caramel suggestion)
- **Severity:** LOW (workflow ergonomics, not architecture)
- **Surface:** `DESIGN_SPECS/*.md` (currently 9 → 16 after this sprint); `.claude/skills/` analog
- **What's deferred:** DESIGN_SPECS docs today are read-only reference: a future Claude session picks up the pattern by reading the markdown. Caramel's framing 2026-05-10: "we could probably convert the design specs to skills, or something in the future". The conversion would let each pattern be invoked as a slash command (e.g. `/use-curve-registry-pattern <surface>`) — the skill would auto-apply the canonical shape (registry header, parser auto-flow, GUI extension, AUTOPOPULATE companion) given a target surface description, rather than the agent re-reading + re-deriving each time.
- **Why deferred:** (a) DESIGN_SPECS catalog is still growing rapidly (9 → 16 in v5.14.9 alone); skill conversion is more useful once the catalog stabilizes. (b) Skill invocation model is for ACTION (auto-apply pattern); reference-pattern docs are for COMPREHENSION (understand + adapt). The split may stay valuable — not every doc needs to become a skill. (c) The 3 HIGH-priority new docs (curve-registry, autopopulate-arity-family, registry-tuple-SSOT) are the strongest skill-conversion candidates; LOW-priority docs (transient-aggregation, partner-core) might stay reference-only.
- **Cost estimate:** ~2-4h per skill (spec write + example application + integration with /readiness). Conservative inventory at conversion time: 5-7 skills from the HIGH+MEDIUM patterns; LOWs stay reference. Total ~15-30h spread across multiple sprints.
- **Trigger:** When DESIGN_SPECS catalog count stabilizes (no new pattern in 2+ sprints) AND when a Layer 2 orchestrator skill (/precoding-audit per TECH_DEBT-018, or new) emerges that would invoke pattern-application skills as sub-steps. Re-evaluate at v5.16 sprint planning.
- **Status:** OPEN
- **Cross-ref:** `tick-trader-percore-workspace/DESIGN_SPECS/README.md` catalog; TECH_DEBT-018 (precoding-audit Layer 1 orchestrator — sibling); CLAUDE.local.md "DESIGN_SPECS catalog discipline" entry.

---

### TECH_DEBT-026 — Per-core override of `bandit_algorithm` (per-core A/B testing)

- **Created:** 2026-05-10 by /dod-audit run on v5.14.10-bayesian-thompson-bandit plan
- **Severity:** LOW
- **Surface:** `Strategies/StrategyParameters.hpp` ML_BuildParameters bandit dispatch (post-v5.14.10 introduction); `CoreFrameworks/PerCoreOverride.hpp` (per-bit-per-core override domains)
- **What's deferred:** Per-core override of `bandit_algorithm` cfg field. Today (post-v5.14.10) the algorithm choice is engine-wide. Future feature: per-core selection (e.g., `core_0_bandit_algorithm=0` Exp3, `core_1_bandit_algorithm=1` Thompson) to run head-to-head A/B comparison at the per-core level — natural extension of the dual-mode (cfg=2) telemetry.
- **Why deferred (not effort-avoidance):** v5.14.10 plan ships engine-wide algorithm choice; per-core override is a separate feature ship. Operator's primary A/B comparison happens via `cfg.bandit_algorithm=2` (both run, telemetry distinguishes) which doesn't need per-core override. Per-core override matters when operator wants to compare TRADING DECISIONS (each core actually trades on its own algorithm) vs telemetry-only. Pattern: `per-bit-per-core-override-pattern.md` (PER_CORE_OVERRIDE_BITMAP_DOMAINS) — but `bandit_algorithm` is INT enum not boolean, so the bitmap pattern doesn't directly apply; a SEPARATE per-core override mechanism is needed for INT-valued cfg fields (precedent: `risk_degradation_curve` per-core override added v5.14.9.C).
- **Cost estimate:** ~2-3h (mirror `risk_degradation_curve` per-core override pattern; add `core_N_bandit_algorithm` cfg parser entry + per-core resolution in ControllerConfig_ResolveForCore + thread through to gate_state). LOW risk (additive; default = engine-wide preserved).
- **Trigger:** Address when (a) operator requests per-core A/B testing of bandit algorithms (head-to-head decisions, not telemetry-only), OR (b) v5.X.Y adds another INT-enum cfg field needing per-core override (consolidation candidate), OR (c) FOREACH_BANDIT_ALGORITHM registry retrofit (TECH_DEBT-026's sister item — making algorithm-extensible amplifies the per-core override value).
- **Status:** OPEN
- **Cross-ref:** v5.14.10 plan (engine-wide algorithm choice ships first); `risk_degradation_curve` per-core override (v5.14.9.C precedent for INT-enum per-core override); `DESIGN_SPECS/per-bit-per-core-override-pattern.md` (boolean variant; INT variant needs adaptation); /dod-audit 2026-05-10 v5.14.10 thompson report.

---

### TECH_DEBT-027 — Locale pinning gap in `Bandit_SaveJSON` (LC_NUMERIC drift risk)

- **Created:** 2026-05-10 by /dod-audit run on v5.14.10-bayesian-thompson-bandit plan
- **Severity:** MEDIUM
- **Surface:** `ML_Headers/BanditLearning.hpp:369-435` (Bandit_SaveJSON); also `ML_Headers/BanditLearning.hpp:503-...` (Bandit_LoadJSON parser side)
- **What's deferred:** Bandit_SaveJSON does NOT pin `LC_NUMERIC=C` via `uselocale(newlocale(LC_NUMERIC_MASK, "C", 0))` before its `fprintf(..., "%.17g", ...)` calls for `weights[]` + `cum_reward[]`. Engine running under non-C locale (e.g., `LC_NUMERIC=de_DE`) would write `0,55` instead of `0.55`; load round-trip via `tt::parse_double_fast_advance` (locale-immune via `from_chars`) would parse `0` (truncated at comma) → silent state corruption. Same gap exists in any other JSON writer using `%g` family without pinning.
- **Why deferred (not effort-avoidance):** v5.14.10's MEDIUM-2 finding (Thompson_SaveJSON locale pinning) addresses the Thompson side; opportunistic to fold Bandit_SaveJSON fix in same ship. But Bandit_SaveJSON gap pre-dates v5.14.10 and isn't strictly v5.14.10's scope. Current production deployments operate under default `LC_NUMERIC=C` so the bug is dormant. Real-world trigger requires operator to set non-C locale environment before launching engine — uncommon but possible (e.g., systemd unit inheriting user locale; Docker container with locale config).
- **Cost estimate:** ~15-20 LOC across save + load (add `uselocale` save-restore around fprintf body; verify `tt::parse_double_fast_advance` is locale-immune already — it is per v5.11.4.C migration). NEGLIGIBLE risk (additive defensive code; preserves existing format bytes when LC_NUMERIC=C — the common case).
- **Trigger:** Address (a) opportunistically when v5.14.10's MEDIUM-2 Thompson_SaveJSON locale pinning is implemented (same file family; same pattern; ~5 extra LOC), OR (b) when an operator reports non-C locale corruption, OR (c) at next /parity-check that walks wire-format byte-preservation surfaces.
- **Status:** CLOSED 2026-05-10 by v5.14.10.C (ca4259f) — locale pinning added to Bandit_SaveJSON via uselocale(newlocale(LC_NUMERIC_MASK, "C", 0)) around fprintf body + uselocale(prev) + freelocale before fclose. Same pattern as ModelInference.hpp:1830-1940 stamp_write_for_model precedent. Applied opportunistically with v5.14.10.C's Thompson_SaveJSON locale pinning.
- **Cross-ref:** /dod-audit 2026-05-10 v5.14.10 thompson report MEDIUM-2 finding; `DESIGN_SPECS/wire-format-byte-preservation-discipline.md` Layer 2 (locale pinning at emit construction); `ML_Headers/ModelInference.hpp` stamp_write_for_model v5.14.8.A.merged precedent for the canonical 3-line pattern; v5.14.10.C commit ca4259f.

---

### TECH_DEBT-028 — Bool-as-uint8_t fields eligible for FOREACH_PER_CORE_STATE_FLAG bitmap migration

- **Created:** 2026-05-10 by /merge-scan re-audit on v5.14.10 amended plan (finding N4)
- **Severity:** LOW (cosmetic; no functional impact; no parity risk)
- **Surface:** PerCoreSnap struct fields in `DataStream/EngineTUI.hpp` (~line 980-1198):
  - `ml_scaler_present` (uint8_t boolean)
  - `drift_breached` (uint8_t boolean)
  - `drift_kill_tripped` (uint8_t boolean)
  - `core_kill_tripped` (uint8_t boolean)
- **Class:** Same shape as v5.14.9.B.2 / .H bitmap migrations (per-core boolean fields → uint8 bitmap with MASK_* + BITMAP_IS_SET API per CLAUDE.md item 20). Inventory caught by /merge-scan during the v5.14.10 amendment re-audit (finding N4) — surfaced as FUTURE candidate, NOT amendment-required.
- **What's deferred:** Migrate the 4 bool-as-uint8_t fields above into a single `uint8_t per_core_state_flags` bitmap with `MASK_PER_CORE_*` constants + accessor macros. Saves 3 bytes per PerCoreSnap (4 bytes → 1 byte); enables branchless multi-flag check via single AND mask; consistent with v5.14.9 BITMAP_* universalization sweep.
- **Why deferred (not effort-avoidance):** v5.14.10 sprint focus is Thompson sampling + PerCoreSnap layout audit (.0) + log column registry generalization (.F). Bit-packing 4 unrelated boolean PerCoreSnap fields is a separate cleanup concern. Folding it in would scope-creep .0 from "bandit telemetry cluster" to "all PerCoreSnap bools." Better as a focused follow-up ship.
- **Cost estimate:** ~30-50 LOC (define new uint8 field + 4 MASK_* constants + accessor macros; refactor 4 read sites + 4 write sites; tests for byte-packing). LOW risk (isolated boolean fields; backward-compat for snapshot consumers via field rename).
- **Trigger:** Address (a) when 2+ MORE bool-as-uint8_t PerCoreSnap fields land (consolidation candidates accumulate), OR (b) when next ship touches PerCoreSnap layout for unrelated reasons (opportunistic absorb), OR (c) v5.14.10.0 PerCoreSnap layout audit may identify additional cluster opportunities that warrant a follow-up "PerCoreSnap state-flag bitmap" sub-ship.
- **Status:** OPEN
- **Cross-ref:** v5.14.9.B.2 (`PerCoreSnap state_flags uint16_t` migration; canonical precedent); v5.14.9.H (`ShardedSnapshot.any_scaler_present + any_scaler_failed` bitmap; same pattern); CLAUDE.md item 20 (bit-packed flag storage via BITMAP_* API); `DESIGN_SPECS/bitmap-flag-api.md`; /merge-scan 2026-05-10 v5.14.10 AMENDED report (finding N4); v5.14.10 amendment-re-audit synthesis at `plans/plan_checks/2026-05-10-v5.14.10-amended-plan-fresh-audits-synthesis.md`.

---

### TECH_DEBT-029 — Source file length reduction (large headers harm maintainability)

- **Created:** 2026-05-10 by Caramel musing during v5.14.10.0 PerCoreSnap layout work
- **Severity:** LOW (cosmetic / maintainability; no behavior or perf impact)
- **Surface:** Large single-file headers in the codebase. Inventory snapshot 2026-05-10:
  - `CoreFrameworks/ControllerConfig.hpp` — 2727 lines (largest header in repo; cfg declarations + parser + defaults + validation)
  - `ML_Headers/CoreModelZoo.hpp` — 2239 lines (CoreModelZoo + EnsembleModelZoo + bandit + ridge state + persistence)
  - `Strategies/StrategyParameters.hpp` — 1693 lines (ML_BuildParameters + dispatch + ridge override + composite confidence)
  - `DataStream/EngineTUI.hpp` — 1382 lines (TUI infrastructure + TUISnapshot + PerCoreSnap)
  - `tests/controller_test.cpp` — ~16k lines (already covered by CLAUDE.md test file size discipline section)
- **Class:** Same maintenance-overhead class as the test file size discipline already in CLAUDE.md (test files > 5k lines must split BEFORE adding more tests). This entry surfaces the SOURCE-side analog for non-test files. Headers above 1500-2000 lines slow IDE navigation, increase merge-conflict surface, and discourage related-concern grouping (developers append to end-of-file rather than locating the relevant section).
- **What's deferred:** Establish a SOURCE file size discipline analog to CLAUDE.md's test file discipline (e.g., "any source file > 1500 lines OR > 50 logical sections must be split BEFORE adding more"). When triggered, split candidate files into focused sub-files by concern (e.g., `ControllerConfig.hpp` → `ControllerConfigDecl.hpp` + `ControllerConfigParser.hpp` + `ControllerConfigDefaults.hpp` + `ControllerConfigValidate.hpp`).
- **Why deferred (not effort-avoidance):** File splits are HIGH-RISK refactors (every consumer's `#include` chain shifts; build dependency graph re-evaluates; sometimes circular-include headaches surface). Each split warrants its own focused ship with rollback anchor + comprehensive build verification. Doing it ad-hoc during feature ships is risky. Better as dedicated refactor sub-ship per file (e.g., v5.X.Y "ControllerConfig.hpp → 4-file split").
- **Cost estimate:** ~2-4h per file split (audit consumers + plan boundary + edit + build verify + test). Total inventory above: ~10-20h to address all candidate files.
- **Trigger:** Address (a) when a specific file makes a feature ship genuinely awkward (e.g., 6+ developer hours lost to "where is X in this 2700-line file?"), OR (b) before a major refactor of one of the candidate files that would significantly increase its size further, OR (c) operator-driven cleanup sprint focused on maintainability.
- **Status:** OPEN
- **Cross-ref:** CLAUDE.md "Test file size discipline (added v5.11.35)" section (test-side analog; this entry is the source-side counterpart); v5.14.10.0 PerCoreSnap layout work (occasion for the musing).

---

### TECH_DEBT-032 — CLAUDE.md context-management cleanup (trim items 19-24 + handoff-skill-managed context loading)

- **Created:** 2026-05-11 by Caramel observation during v5.14.11 plan-synthesis CLAUDE.md item 25 addition
- **Severity:** MEDIUM (maintainability + per-session context efficiency; no functional impact)
- **Surface:** `CLAUDE.md` (always-loaded into every Claude Code session); reference docs `DOCS/CLAUDE_INTEGRATION.md` + `DOCS/CLAUDE_INVARIANTS.md` + `DOCS/CLAUDE_ML_INVARIANTS.md` + `DOCS/CLAUDE_REVIEW.md` + `DOCS/CLAUDE_FOXML_SUITE.md` (split-load on-demand); handoff skill spec at `.claude/skills/handoff/SKILL.md`
- **Class:** Context-window bloat — CLAUDE.md is ~227 lines / ~5000 words always-loaded. Items 19-24 each have multi-paragraph + sub-clauses + code snippets + reference-application lists, accumulated as the codebase pattern library grew. Item 25 (v5.14.11) is intentionally terser (1 paragraph + DESIGN_SPEC pointer); demonstrates the cleaner direction.
- **What's deferred:** Two-layer cleanup:
  1. **Trim CLAUDE.md items 19-24 to "rule statement + DESIGN_SPEC pointer" form** — keep the rule declaration; move 7-rule lists, code snippets, multi-paragraph why-explanations, and reference-application detail into the corresponding `DESIGN_SPECS/<pattern>.md` (where most already live). Each item becomes 3-5 sentences. Estimated CLAUDE.md size reduction: ~227 → ~120 lines.
  2. **Consider handoff-skill-managed context loading** — instead of always-loading the full invariant set, have the `/handoff` skill at session-start include the relevant subset based on ship surface area (e.g., a Ridge-math ship loads items 12/14/15/16/17/18/19/20/25 + relevant DESIGN_SPECS; a cfg-field-addition ship loads items 13/16/20/21 + integration docs). CLAUDE.md trims to truly universal rules (architecture invariants 1-11 + reuse/latency/structural-fix discipline 16-19).
- **Why deferred (not effort-avoidance):** Layer 1 (trim) is mechanical (~1-2h per item × 6 items = ~6-12h) but high-value-per-hour for context efficiency. Layer 2 (handoff-skill context loading) is architecturally meaningful — changes how the session bootstraps + may require handoff-skill spec rewrite. Both warrant a focused cleanup ship, not feature-ship absorption. v5.14.11 ships first; cleanup follows when scheduled.
- **Cost estimate:** Layer 1 (trim items 19-24): ~6-12h. Layer 2 (handoff context loading): ~4-8h skill spec + verify across sample ship types. Total: ~10-20h focused cleanup ship.
- **Trigger:** Address (a) when CLAUDE.md grows past ~250 lines (next 1-2 new items would breach), OR (b) when operator reports context-window pressure during a session (handoff prompts feel cramped), OR (c) operator-scheduled maintainability sprint, OR (d) when handoff skill is rewritten for other reasons (consolidate the changes).
- **Status:** OPEN
- **Cross-ref:** Caramel framing 2026-05-11 "this code base is too big to shove it all into the CLAUDE.md file, thats why it has ref links"; v5.14.11 plan-synthesis item 25 addition (already trimmed to demonstrate direction); `DOCS/CLAUDE_INTEGRATION.md` / `CLAUDE_INVARIANTS.md` / `CLAUDE_ML_INVARIANTS.md` / `CLAUDE_REVIEW.md` / `CLAUDE_FOXML_SUITE.md` (existing split-load infrastructure); `.claude/skills/handoff/SKILL.md` (skill that would orchestrate Layer 2 context loading); related discipline: CLAUDE.local.md "codify design principles in CLAUDE.md as patterns mature" (set 2026-05-09) — this entry is the reciprocal "and trim them back to terse form once DESIGN_SPECS carries the depth."

---

### TECH_DEBT-033 — `/readiness` skill wider-build verification check ✅ CLOSED v5.15.2

- **Created:** 2026-05-12 by v5.14.post1 patch (train_model_worker_fn migration gap)
- **Severity:** MEDIUM (discipline gap; missed sites in mechanical migration sweeps)
- **Surface:** `tick-trader-percore-workspace/claude-skills/readiness/SKILL.md`
- **What was deferred:** /readiness audited ~24 items pre-coding; none verified
  that the previous sprint's close ran `./build.sh gui suite tsan asan all`
  (not just `test`). v5.14.post1 was the warning shot — the wider build
  catches BacktestPanels.hpp + GUI panel consumers that test target skips.
- **Closure (v5.15.2.D):** /readiness Check 26 added — verify last sprint's
  postmortem documents `./build.sh gui suite tsan asan all` GREEN result;
  flag if only `./build.sh test` was run.
- **Status:** ✅ **CLOSED v5.15.2.D** (planned for v5.15 sprint).
- **Cross-ref:** v5.14.post1 patch + postmortem; `/readiness` SKILL.md
  v5.15.2 update; plans/v5.15-live-readiness/MASTER.md.

---

### TECH_DEBT-034 — FOREACH_CLI_MODE registry + batch mode CLI infrastructure + per-run logging structure (deferred from v5.15.3)

- **Created:** 2026-05-12 by v5.15.3 plan-synthesis (post-audit reframe;
  speculative scope cut to focus v5.15.3 on root-cause structural fix)
- **Severity:** LOW (foundation work for headless workflows; not blocking)
- **Surface:** `foxml_suite.cpp:main()` (NEW batch mode entry), NEW
  `Backtest/CliModeRegistry.hpp` (FOREACH_CLI_MODE X-macro), GUI button
  handlers (rewire to spawn execv children), `logging/foxml_suite/<run_name>/`
  structure (per-run dir + per-horizon `.progress` files + per-horizon `.log` files)
- **What's deferred:** FOREACH_CLI_MODE X-macro registry (curve-registry-pattern.md
  shape) for cmdline-invocable training operations. Each mode = 1 row:
  mode name (wire-key for `--mode=...`), args struct, dispatch fn ptr, GUI
  invoke entry, help text. Plus headless training path that skips
  SDL/ImGui init in batch mode. Plus per-run logging structure. Plus
  GUI button handlers rewired to spawn execv children + parent-side
  waitpid + progress IPC via file polling at 200ms cadence.
- **Why deferred (not effort-avoidance):** v5.15.3's actual root-cause
  fix is ~200 LOC (helper extraction + plumb + libgomp setenv). The
  FOREACH_CLI_MODE infrastructure (~300+ LOC) was speculative scope
  added to my v5.15.3 plan draft based on a MISDIAGNOSED root cause
  (multi-horizon stamping isn't missing; it's just missing
  grid_member_count population). The proper structural foundation
  helper extraction (v5.15.3.A Stamp_AssembleAndEmit) IS the
  precursor — adding FOREACH_CLI_MODE on top of pure-function helpers
  becomes much cleaner once helpers exist.
- **Cost estimate:** ~300-400 LOC across batch mode entry + registry +
  GUI rewire + progress IPC + tests. Time: ~6-8 hr dedicated focus.
- **Trigger:** Address when ANY of:
  - (a) CI training automation needed (Docker-based scheduled retrains)
  - (b) Remote training via SSH requested
  - (c) Operator wants to script grid training overnight
  - (d) v5.16+ headless-foundation ship opens (likely sequenced after
        paper-test era stabilizes the engine side)
- **Status:** OPEN — foundation prepared by v5.15.3.A helper extraction
- **Cross-ref:** v5.15.3 subplan (helper extraction is the precursor);
  `plans/_future/2026-05-12-decoupling-endgoal-roadmap.md` (running
  breadcrumbs; v5.15.3 entry); `plans/_future/2026-05-08-v6.0-CANDIDATE-headless-service-colo.md`
  (companion architecture doc); CLAUDE.local.md "decoupling-endgoal
  positioning at each fix" (set 2026-05-12)

---

### TECH_DEBT-035 — Engine-side state-exposure protocol + DoubleBufferedAtomic<T> template extraction (deferred from v5.15.4)

- **Created:** 2026-05-12 by v5.15.4 plan-synthesis (post-audit reframe;
  DoubleBufferedAtomic<T> template extract premature because HotSwap
  has single-owner threading model)
- **Severity:** LOW (foundation work for engine→viewer decoupling;
  blocked on operator commitment to colo deployment)
- **Surface:** NEW `MemHeaders/DoubleBufferedAtomic.hpp` (template extracted
  from `DataStream/BinanceDepth.hpp:80-89` pattern); engine binary
  TUISnapshot durable mmap region; viewer process separation;
  `engine_gui` as separate binary attached via mmap
- **What's deferred:** Template-extract `DoubleBufferedAtomic<T>` from
  BinanceDepth's existing `snapshots[2] + active_idx + __ATOMIC_RELEASE/_ACQUIRE`
  pattern. Make it reusable across HotSwap (NOT needed there per
  v5.15.4 reframe; single-owner suffices) + future engine→viewer mmap
  state exposure. Plus engine-side: replace in-process TUISnapshot
  double-buffer with mmap'd region using the template. Plus viewer-side:
  attach to mmap region; render ImGui or TUI from snapshot.
- **Why deferred (not effort-avoidance):** v5.15.4's HotSwap use case
  doesn't actually need DoubleBufferedAtomic (writer = reader = same
  per-core slow-path thread; `__atomic_exchange_n` on pointer
  suffices). Template extraction is premature for v5.15.4. Engine→viewer
  protocol design needs: versioning scheme, viewer-side cfg, reconnect
  semantics, multi-viewer support, mmap region path conventions —
  multi-week design + implementation. Triggered by operator commitment
  to colo deployment (separate hardware → viewer connection a real
  need), not by v5.15 in-sprint work.
- **Cost estimate:** ~50 LOC template + ~5-15 days for full
  engine→viewer protocol + viewer process refactor + testing
- **Trigger:** Address when ANY of:
  - (a) Operator commits to colo deployment (separate hardware → SSH
        attach pattern stabilizes)
  - (b) Operator requests multi-viewer access (multiple GUIs to one
        engine)
  - (c) Engine binary needs to survive viewer crashes (today: GUI
        crash kills engine)
  - (d) v6.0 architecture sprint opens (per `2026-05-08-v6.0-CANDIDATE-headless-service-colo.md`)
- **Status:** OPEN — BinanceDepth.hpp:80-89 stays as canonical precedent
- **Cross-ref:** `DataStream/BinanceDepth.hpp:80-89` (canonical precedent
  for template extraction); `plans/_future/2026-05-08-v6.0-CANDIDATE-headless-service-colo.md`
  (companion architecture doc); `plans/_future/2026-05-12-decoupling-endgoal-roadmap.md`
  (running breadcrumbs); CLAUDE.local.md "decoupling-endgoal positioning
  at each fix" (set 2026-05-12); v5.15.4 subplan (HotSwap reframe
  documenting why template is NOT needed for v5.15.4 itself)

---

### TECH_DEBT-036 — Architectural-field AUTOPOPULATE redesign (registry tuple restructure)

- **Created:** 2026-05-12 by v5.15.3.A PARITY-022 discovery
- **Severity:** LOW (no active issue; macro is unused; latent bug
  quarantined at v5.15.3.A)
- **Surface:** `ML_Headers/StampBoundModelConstRegistry.hpp:601-689`
  (STAMP_MODEL_CONST_AUTOPOPULATE macro + _ONE expansion); registry
  tuple `get_value` column semantics
- **What's deferred:** The STAMP_MODEL_CONST_AUTOPOPULATE macro expansion
  was semantically broken (self-referential: `(inf).X = (type)(inf->X)`
  because registry tuples pass `inf->X` as the get_value column). At
  v5.15.3.A the macro was QUARANTINED with a static_assert error to
  prevent accidental use. Helper Stamp_AssembleAndEmit manually
  populates model-const fields from StampArgs instead.
- **Why deferred:** The proper structural fix requires restructuring the
  registry tuple to add a SEPARATE column for the AUTOPOPULATE value
  source (distinct from `inf->X` references that parser/emit consumers
  use for the same tuple). This affects 4 consumer-site macros + ~30
  registry entries + would require comprehensive byte-equivalence
  verification. Too large for v5.15.3 scope; model-const manual
  population matches RFV's existing working pattern.
- **Cost estimate:** ~4-6h architectural refactor (new tuple column +
  4 consumer-site macros updated + 32 registry entries restructured +
  byte-equivalence test suite). MEDIUM risk (parser/emit byte-format
  must stay byte-identical).
- **Trigger:** Address when (a) operator wants to add an AUTOPOPULATE-
  driven architectural field (would discover the broken macro at
  quarantine static_assert), OR (b) v5.X+ wider AUTOPOPULATE
  consolidation ship, OR (c) ~5+ new model-const fields land in one
  sprint making manual population painful.
- **Status:** OPEN — macro quarantined at v5.15.3.A; manual population
  for v5.15 + foreseeable future
- **Cross-ref:** PARITY-022 (workspace PARITY_ISSUES.md); v5.15.3.A
  quarantine implementation; `ML_Headers/StampBoundModelConstRegistry.hpp:601-689`
  (macro definition); `Backtest/BacktestEngine.hpp:1039+` (RFV manual
  population pattern; canonical reference); CLAUDE.md item 19
  (structural-fix preferred — quarantine + manual is the correct trade-
  off here because the registry restructure is its own focused work)
