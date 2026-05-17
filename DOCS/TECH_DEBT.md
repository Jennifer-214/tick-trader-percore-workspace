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

### TECH_DEBT-003 — `verify_model_stamp` parser refactor to data-driven dispatch ✅ CLOSED v5.15.0

- **Created:** 2026-05-09 by v5.14.2.E.3 (first noted in v5.14.1 post-mortem)
- **Severity:** LOW
- **Surface:** `ML_Headers/ModelInference.hpp` `verify_model_stamp` function
- **What was deferred:** Parser used if-else chain over ~24 PRE_CFG stamp body keys (POST_CFG was already X-macro-driven since v5.14.8.A.merged.4). Adding a new PRE_CFG key required manual `else if (strcmp(key, "...") == 0) { ... }` branch + STAMP_SET dispatch — Class 18 mirror with the registry-driven emit walk.
- **Status:** ✅ **CLOSED v5.15.0 (2026-05-12).** v5.15.0.B refactor migrated the PRE_CFG parser branches to X-macro dispatch walking FOREACH_STAMP_BOUND_MODEL_CONST_PRE_CFG (all 27 entries auto-flow). Uses `tt::stamp_parse_field<T>` templated helper for type dispatch (CLAUDE.md item 23). The 3 hex-encoded uint64 fields (build_flags_hash, label_registry_hash, feature_mask) initially deferred as manual branches were RESOLVED by extending `tt::stamp_parse_field<T>` to take the registry's `fmt` column as an optional parameter and auto-detect base via `strchr(fmt, 'x') || strchr(fmt, 'X')` — DRY: `fmt` is now the single source of truth for emit AND parse format. The originally-proposed `parser_base` tuple column is SUPERSEDED by this approach (no tuple-shape change; future hex fields auto-flow). 1 manual branch remains: `feature_scaler_present` for defensive truthy normalization (any non-zero → 1; production emit always produces 0/1, so the branch is bounded defensive coding against malformed stamps). Closes Class 18 parser/emit mirror at the same surface AUTOPOPULATE closed for emit. ~120 LOC → ~25 LOC X-macro + 1 normalization exception.
- **Cross-ref:** v5.14.1 post-mortem; FOREACH_STAMP_BOUND_CFG (`StampBoundCfgRegistry.hpp`) shows the canonical pattern; v5.15.0 ship; `tt::stamp_parse_field<T>` at `ML_Headers/StampBoundModelConstRegistry.hpp:101+`.

---

### TECH_DEBT-004 — Dual-tau cfg field naming clarity ✅ CLOSED v5.14.9.D

- **Created:** 2026-05-09 by v5.14.2.E.3 (originally PARITY-006; reclassified as TECH_DEBT since not a parity issue)
- **Severity:** LOW
- **Surface:** `ControllerConfig.hpp` cfg fields `confidence_freshness_tau` (legacy IC) + `confidence_freshness_tau_secs` (composite confidence; v5.14.1)
- **What was deferred:** Two distinct cfg fields with overlapping semantics ("freshness tau"). Operator could set one when meaning the other.
- **Status:** ✅ **CLOSED v5.14.9.D (2026-05-10, commit b703e61).** Hard-deletion path: legacy `confidence_freshness_tau` was mathematically inert (`data_age=0` always in production; half-dead via stamp-bound drift check on a value that doesn't affect inference). Deleted entirely from ControllerConfig + 5 ConfidenceScorer_Init callsites adapted (3-arg → 2-arg signature). Legacy stamps with `inference_cfg_freshness_tau` line load successfully (parser ignores unknown key via existing forward-compat semantics; HMAC chain unbroken because HMAC is per-stamp). Operator migration: WARN log if legacy key present in cfg file ("remove from cfg"). Only `confidence_freshness_tau_secs` remains (composite-confidence freshness; not confusable since the legacy field is gone).
- **Cross-ref:** PARITY-006 (originally raised there); v5.14.9.D commit b703e61 (engine repo); v5.14.9 umbrella.

---

### TECH_DEBT-005 — Single-zoo hot-swap strict-mode failure handling unification ✅ CLOSED v5.15.4

- **Created:** 2026-05-09 by v5.14.2.E.3 (surfaced during v5.14.2.E.1 design)
- **Severity:** LOW
- **Surface:** `CoreFrameworks/EngineSharded.hpp` ~line 2820 (single-zoo hot-swap validate failure handling)
- **What was deferred:** Boot does Free + null + flag on validate failure. Hot-swap did flag-only on validate failure (preserved v5.10.0c "log-and-leave" semantics). Asymmetry was intentional pre-v5.15.4 because pre-swap state wasn't snapshotted; true rollback required infrastructure.
- **Status:** ✅ **CLOSED v5.15.4 (2026-05-12).** Single-zoo + ensemble hot-swap unified via shadow-load pattern (per `shadow-load-state-transition-pattern.md` — promoted DRAFT v0.1 → ACTIVE v1.0). Both surfaces use `tt::HotSwap_ShadowLoad_*<F>` helpers in `CoreFrameworks/HotSwap.hpp`:
  - **`aligned_alloc(64, sizeof(T))` allocates NEW zoo container** — pre-swap state untouched
  - **Init + Load + PostLoadSetup into NEW zoo** — failure modes (alloc OOM / load failed / strict validate failed) all Free new + return nonzero with pre-swap pointer preserved
  - **`__atomic_exchange_n` swap** — lock-free; readers see old OR new, never torn
  - **Free OLD zoo** — single-owner reclamation (per-core slow-path thread is sole owner of `state.cores[c].*_handle`; no RCU grace needed)
  - **PARITY-023 capture-pointer-revert anti-pattern eliminated** — no torn moment exists, so revert is unnecessary
- **Bonus implicit fixes:**
  - Boot path migrated from `static CoreModelZoo<F> ml_zoos[]` to per-core `aligned_alloc(64)` (required for `free(old_ezoo)` validity on first swap)
  - `alignas(64)` retrofit on `CoreModelZoo<F>` + `EnsembleModelZoo<F>` so heap allocations satisfy embedded `ModelHandle<F>` + `RidgeWeights<F>` alignment guarantees
  - Legacy `EnsembleHotSwap.hpp::EngineSharded_HotSwapEnsemble` retained for back-compat but production dispatch now goes through shadow-load
- **Cross-ref:** `CoreFrameworks/HotSwap.hpp` (canonical implementation); `DESIGN_SPECS/shadow-load-state-transition-pattern.md` (pattern doc); PARITY-023 closure (workspace `PARITY_ISSUES.md`).

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

### TECH_DEBT-009 — FOREACH_CFG_FIELD registry for non-stamp-bound cfg fields (boolean subset CLOSED v5.14.9.F.4; KIND_DOUBLE/_PCT subset CLOSED v5.15.5.F.4b)

- **Created:** 2026-05-09 by v5.14.8 scope decision (Interpretation B; deferred N-site pattern audit)
- **Severity:** MEDIUM → LOW → LOW (boolean + KIND_DOUBLE/_PCT subsets closed; KIND_INT/_BOOL/_STRING remain as future work; descriptor schema locked at .F.4b — remaining migration is mechanical row additions)
- **Surface:** `CoreFrameworks/ControllerConfig.hpp` (struct), parser body inline in `ControllerConfig_Load<F>` template function, `GUI/SettingsPanel.hpp` field_defs[] (operator-facing render), `engine.cfg.example` (cfg.example doc — generation deferred to .F.4d)
- **Status:** **PARTIAL CLOSED across multiple ships:**
  - **v5.14.9.F.4 (2026-05-10):** Boolean cfg fields (21 across 5 domains) migrated to `FOREACH_<DOMAIN>_CFG_FLAG` registries with single-source-of-truth semantics. Parser auto-flows via 5 FOREACH walks (~21 inline branches → 5 walks, ~90 LOC reduction). GUI field_defs[] auto-extends via 5-col tuple expansion (v5.14.9.F.5 Option D). Per-core override extends via PER_CORE_OVERRIDE_BITMAP_DOMAINS macro (v5.14.9.F.6).
  - **v5.15.5.F.4b (2026-05-14):** KIND_DOUBLE/_PCT subset (~40 fields) migrated to `FOREACH_CFG_FIELD` registry (NEW; `CoreFrameworks/CfgFieldRegistry.hpp`) with 12-col Option D tuple. 3-barrier structural fix for DOCS/RECURRING_BUG_PATTERNS.md Class 23 (`tt::cfg_parse_field<T>` type-trait dispatch + X-macro extractor chokepoint + compile-time type-family static_assert) makes type-erased reinterpret_cast dispatch unreachable. Parser + GUI render + tooltip preservation byte-identical for hand-tuned operator prose. Descriptor schema LOCKS at .F.4b — remaining migration is row additions only.
- **Remaining (still OPEN; RESTRUCTURED 2026-05-14 by Option D+ ship sequence per `/precoding-audit-gate` synthesis):**
  - **.F.4c (RESCOPED non-STAMP_BOUND only):** KIND_INT + KIND_INT_ENUM + KIND_BOOL non-STAMP_BOUND migration (~50-60 fields) + `tt::cfg_render_field<T>` impl + X_GEN_LABEL extern reuse (for BanditAlgorithm / BarrierBlendMode / DegradationCurve enums) + INT_ENUM string-token branch + tooltip byte-identity discipline test. ~280 LOC; LOW risk.
  - **.F.4d (NEW — wire-format framework + structural closure):** STAMP_BOUND derived filter cutover (FOREACH_STAMP_BOUND_CFG_DERIVED via metadata bit) + Layer 5b canonical body hash lock + v5.14 stamp fixture + 12+ consumer migration + cohort migration (~14 STAMP_BOUND fields: 11 doubles + 3 ints; plus 4 bitmap-resident bools via two-source variant). PLUS DERIVED_FILTER framework + FOREACH_REGISTRY meta-registry + sidecar override pattern (replaces wide-variant CfgDriftCheckRegistry) + bit-packed DriftOverride/RegistryRosterEntry/ManualFieldInventoryEntry + branchless dispatch refactor + X-macro struct generation for cfg + ~113-row cfg field audit. PLUS 4 new DESIGN_SPECs (metadata-bit-driven-derived-filter-framework / meta-registry-pattern / sidecar-override-pattern / framework-composition-overview) + 5 new invariants H14-H18 + CLAUDE.md item 31 + DESIGN_PHILOSOPHY §1.5 (Framework discipline). ~1500 LOC code + ~600 LOC specs + ~400 LOC docs + ~3 hr cfg field audit. MED-HIGH risk; full pre-coding audit gate fires before coding.
  - **.F.4e (RENAMED from old .F.4d):** KIND_STRING + KIND_FILE_PATH migration + cfg.example auto-gen + cross-cutting metadata doc + 5 GUI metadata derived filters via framework (HIDDEN_BY_DEFAULT, RESTART_REQUIRED, SAFETY_CRITICAL, IS_SECRET, DEPRECATED) + reverse-drift CI fully closed. Validates the .F.4d framework via 5 real second-source applications.
  - **.F.4f - .F.4j (RENAMED from .F.4e - .F.4i):** ResolvedCoreCfg slow-path cache / K-state enum cohort pack / AoS-by-core override re-layout / strategy-category audit / backtest.cfg integration. Sub-letter renames per `feedback_rename_plans_to_match_ship_order` to preserve monotonic Version.hpp tag sequence.
  - **v5.15.6:** controller/secrets/training cfg integration via STRUCT_CONTROLLER_CFG / STRUCT_SECRETS_CFG / STRUCT_TRAINING_CFG.
- **Why incremental close vs full close:** non-boolean cfg fields are heterogeneous in type + parser semantics (atoi vs atof vs strncpy vs FPN<F>::F-templated); each type needs its own `if constexpr` branch in tt::cfg_parse_field<T>. KIND_DOUBLE/_PCT cohort at .F.4b validates the 3-barrier design + descriptor schema; subsequent sub-ships add rows + extend tt:: dispatch incrementally per-kind.
- **Cost estimate (remaining):** ~2-3h per Kind cohort (.F.4c ~80 fields ~3h; .F.4d ~40 fields + cfg.example ~3-4h; .F.4i + v5.15.6 ~6-9h total).
- **Trigger:** Sequential ship plan within v5.15.5.F.4 + v5.15.6 sprints.
- **Cross-ref:** v5.14.9.F-.F.6 ships (boolean subset closure); v5.15.5.F.4b engine commit `160da10` + tag `v5.15.5.F.4b` (KIND_DOUBLE/_PCT subset closure); `DESIGN_SPECS/heterogeneous-registry-pattern.md` (DOMAIN SPLIT pattern reference impl); `DESIGN_SPECS/universal-cfg-field-registry-pattern.md` (12-col Option D); `DESIGN_SPECS/type-trait-dispatch-via-tt-namespace.md` (3-barrier antidote); `DOCS/RECURRING_BUG_PATTERNS.md` Class 23 (structurally extinct); `ML_Headers/StampBoundCfgRegistry.hpp` (sister registry for stamp-bound cfg; pattern precedent); CLAUDE.md item 13 (X-macro audited categories list).

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
- **What's deferred:** Convert PerCoreSnap general visible-state field additions (positions, gates, predictions, regime, etc.) to a `FOREACH_PER_CORE_SNAP_FIELD` registry. Each entry auto-generates struct field, populator (capture from `CoreContext` / `EventLoopState`), GUI-side accessor. [Stale-name correction 2026-05-12: previously referenced "EventLoopCoreState" — actual struct is `EventLoopState<F>` at `CoreFrameworks/ControllerEventLoop.hpp:526` holding `CoreContext<F>` per-core elements at `:173`.]
- **Why deferred (not effort-avoidance):** Distinct from FOREACH_FAILURE_MODE (v5.14.8 covers failure-mode fields specifically; this would cover the LARGER set of visible state). Performance-sensitive: snapshot capture runs in slow-path tail; registry expansion needs to preserve existing memcpy-friendly layout. Needs design conversation about: (a) whether to split capture into hot/warm/cold tiers, (b) whether registry entries should declare their write cadence, (c) cache-line alignment preservation. NOT a mechanical conversion.
- **Cost estimate:** ~10-15h architectural ship (design + registry + migration of ~30 fields + tests); requires preceding design doc
- **Trigger:** Next ship that adds 5+ PerCoreSnap general fields in one umbrella (likely v5.X+ ML observability work or v6.0 maker), OR ship that audits PerCoreSnap layout for cache performance.
- **Status:** OPEN — partially addressed by v5.14.10.0 (cluster alignment dimension)
- **Progress (v5.14.10.0):** the cache-line alignment dimension (sub-bullet (c) of "Why deferred") is now ADDRESSED via `per-snapshot-cluster-layout-pattern.md` (NEW DESIGN_SPECS) + first reference application (PerCoreSnap bandit telemetry cluster with `alignas(64)` boundary + compile-time `static_assert(offsetof)` enforcement). Future contributors have a documented methodology + working example for cluster boundaries. The FULL `FOREACH_PER_CORE_SNAP_FIELD` registry conversion (sub-bullets (a) and (b): hot/warm/cold tier split + write-cadence-declared registry entries) remains DEFERRED — those are higher-scope architectural changes that warrant their own focused ship.
- **Progress (v5.15.5.B planned 2026-05-12):** further partial close anticipated via two .B sub-ships: (1) .B.2 `CoreContextDisplayMeta<F>` extraction (Rule 1 of cache-layout-discipline-for-hot-side-structs.md) — extracts display-only fields from CoreContext to a sibling struct, applying the writer-side analog of the PerCoreSnap layout discipline; (2) .B.4 `FOREACH_GATE_DIAG(X)` registry — closes the Display↔Execution Invariant (CLAUDE.md item 12) Class-18 mirror for the 12 `diag_*` fields specifically (the gate-diagnostic subset of the larger PerCoreSnap registry concern). New DESIGN_SPECS at .B umbrella: `display-execution-invariant-registry-pattern.md` (codifies FOREACH_GATE_DIAG class as generalizable for regime_signals, ML predictions, OMS state). Full `FOREACH_PER_CORE_SNAP_FIELD` registry conversion still DEFERRED beyond .B.
- **Progress (v5.15.5.B SHIPPED 2026-05-13):** .B.2 + .B.4 closures landed (.B.4 SUBSUMED by .B.2's Option B+ registry-driven ship — dual `FOREACH_GATE_DIAG_PAIR(X)` + `FOREACH_DISPLAY_META_FIELD(X)` registries in `MemHeaders/DisplayMetaRegistry.hpp` close the gate-diag + observability-counter Class-18 mirror at structural level). Plus .B.8 added a 4-walk → 1-walk consolidation in the snapshot publisher (`CoreFrameworks/ShardedSnapshot.hpp`) — adjacent concern; preserves PerCoreSnap output bytewise-identical while saving ~20 MB/s memory bandwidth at 60 Hz publish via loop fusion. .B.2 also shipped `cross-thread-snapshot-publish-cluster-isolation.md` (ND1) + `display-execution-invariant-registry-pattern.md` (ND2) first-reference applications. **Cluster-layout dimension + writer-side gate-diag registry dimension both addressed; full `FOREACH_PER_CORE_SNAP_FIELD` registry conversion (hot/warm/cold tier split + write-cadence-declared entries) still DEFERRED beyond .B.** Cost estimate updated: full registry conversion now closer to ~6-10h (lower than original ~10-15h because the surrounding patterns + DESIGN_SPECS are now well-established).
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
| `CoreContext` boot/decision booleans (dirty, core_kill_tripped, model_load_failed, cfg_drift_strict_refused, warmup_log_emitted) | 5 | uint8_t `core_state_flags` + `FOREACH_CORE_STATE_FLAG` registry + `CORE_STATE_FLAG_{IS_SET,SET,CLR}` accessors | ✅ DONE v5.15.5.B.3 (post-closure 8th application; pattern continues to land new sites) | — |

- **Status:** ✅ **CLOSED v5.14.9 (2026-05-10).** All 7 candidates migrated. **+ v5.15.5.B.3 (post-closure)** added an 8th application (`core_state_flags` on CoreContext via `FOREACH_CORE_STATE_FLAG`) — confirms the BIT_FLAG pattern continues to attract new sites organically; no need to reopen the ticket. Cumulative wins:
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

### TECH_DEBT-014 — ModelHandle migration to FOREACH_STAMP_BOUND_MODEL_CONST X-macro generation ✅ CLOSED v5.15.0

- **Created:** 2026-05-09 by v5.14.8.A.merged.2 (deferred during Option 1 unification scope)
- **Severity:** LOW
- **Surface:** `ML_Headers/ModelInference.hpp` ModelHandle struct
- **What was deferred:** ModelHandle used MANUAL field declarations for stamp-derived runtime fields (inconsistent `stamp_inf_*`, `stamp_xgb_*`, `stamp_label_*`, `stamp_*` prefix policy across groups). v5.14.8.A.merged migrated ModelStampResult + StampInferenceCfgInputs to X-macro generation but ModelHandle stayed manual.
- **Status:** ✅ **CLOSED v5.15.0 (2026-05-12).** ModelHandle migrated to X-macro generation walking FOREACH_STAMP_BOUND_MODEL_CONST with STAMP_HANDLE_GEN_INCLUDE/SKIP_HANDLE presence dispatch. 14 uint8_t has_* direct fields → uint64_t has_flags bit-packed (CLAUDE.md item 20; shared MASK_* constants with ModelStampResult / StampInferenceCfgInputs so a single parser dispatch table row writes both bits). Value fields renamed to canonical wire-key names (stamp_xgb_max_depth → xgb_max_depth, stamp_inf_confidence_threshold_scale → inference_cfg_confidence_threshold_scale, etc.). alignas(64) + 64B HOT cluster (handle, backend, num_*, has_flags) + HOT-2 cluster (target_classes / class_weights at cache line 2) + WARM cluster (scaler) + COLD cluster (X-macro stamp fields + paths). Explicit padding (`_hot_pad0`, `_hot_pad1[4]`) per CLAUDE.md item 27. ~80 caller sites migrated across CoreModelZoo, EngineSharded, ModelValidation, FeatureRegistryOverlay, tests. ~250 LOC delta.
- **Cross-ref:** v5.14.8.A.merged.2 commit (deferral point); v5.15.0 ship; +23 anchor tests at `tests/controller_test.cpp` (v5.15.0.A + v5.15.0.C sections).

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

### TECH_DEBT-024 — `breakeven_on_profit` dormant cfg field ✅ CLOSED v5.15.2

- **Created:** 2026-05-10 by v5.14.9.F step 0 inventory
- **Severity:** LOW (operator-facing dormant feature; no functional impact)
- **Surface:** `CoreFrameworks/ControllerConfig.hpp` declaration + parser; FOREACH_LIFECYCLE_CFG_FLAG bitmap entry
- **What was deferred:** `breakeven_on_profit` cfg bit was declared + parsed + bitmap-allocated (FOREACH_LIFECYCLE_CFG_FLAG via v5.14.9.F migration) but had ZERO read sites. Operators could set it in engine.cfg; engine accepted the value without applying it.
- **Closure (v5.15.2.C):** Wired up via new slow-path helper `EventLoop_BreakevenOnProfit` + `EventLoop_BreakevenOnProfitOneCore` (`CoreFrameworks/ControllerEventLoop.hpp`). Mirrors the existing trailing-SL OneCore/Wrapper precedent. When the bit is set and an open position's gain_pct exceeds round-trip taker fees (2 × fee_rate_taker), ratchets `pending_params.ratchet_sl` to fee-floored breakeven (entry × (1 − 3 × fee_rate_taker)). Max-write semantics compose cleanly with trailing-SL ratchet (trailing wins via max once gain exceeds tp_hold_score; breakeven holds the floor below). Called from both live slow-path (`EngineSharded.hpp` near TrailingSLRatchet call site at ~line 2044) AND backtest driver (`ShardedBacktestDriver.hpp` near TrailingSLRatchet call site at ~line 376). DORMANT marker removed from registry doc string. Cost: ~80-150ns per active position per slow-path cycle when bit set; bit unset → wrapper early-exits in ~1ns. Below 100µs slow-path budget.
- **Status:** ✅ **CLOSED v5.15.2 (2026-05-12).**
- **Cross-ref:** v5.14.9.F (FOREACH_LIFECYCLE_CFG_FLAG bitmap migration); v5.15.2 ship; `CoreFrameworks/ControllerEventLoop.hpp` EventLoop_BreakevenOnProfit; `CoreFrameworks/LifecycleCfgFlagRegistry.hpp:58` (DORMANT marker removed).

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

### TECH_DEBT-028 — Bool-as-uint8_t PerCoreSnap fields migrated to state_flags bitmap ✅ CLOSED v5.15.1

- **Created:** 2026-05-10 by /merge-scan re-audit on v5.14.10 amended plan (finding N4)
- **Severity:** LOW (cosmetic; no functional impact; no parity risk)
- **Surface:** PerCoreSnap struct fields in `DataStream/EngineTUI.hpp`
- **Status:** ✅ **CLOSED v5.15.1 (2026-05-12).** 4 bool-as-uint8_t PerCoreSnap fields (`ml_scaler_present`, `drift_breached`, `drift_kill_tripped`, `core_kill_tripped`) migrated to the existing `state_flags` uint16_t bitmap (4 new entries on `FOREACH_PER_CORE_STATE_FLAG`: ML_SCALER_PRESENT, DRIFT_BREACHED, DRIFT_KILL_TRIPPED, CORE_KILL_TRIPPED). Registry post-migration: 7 + 4 = 11 of 16; 5 bits headroom. Reuses the existing `state_flags` bitmap from v5.14.9.B.2 (no new bitmap surface; cohort homogeneity preserved per CLAUDE.local.md cohort-audit rule). All read sites (MLStatusPanel.hpp, DashboardPanels.hpp ×8) + write sites (ShardedSnapshot.hpp ×2) + tests migrated to STATE_FLAG_IS_SET / SET / CLR. Saves 4 bytes per PerCoreSnap. Engine-side fields (ExecutionCore.core_kill_tripped + drift_history.breached + drift_history.kill_tripped on ControllerEventLoop) intentionally STAY as-is — only the snapshot publication side moves to bitmap.
- **Cross-ref:** v5.14.9.B.2 (`PerCoreSnap state_flags uint16_t` migration; canonical precedent); v5.14.9.H (`ShardedSnapshot.any_scaler_present + any_scaler_failed` bitmap; same pattern); CLAUDE.md item 20 (bit-packed flag storage via BITMAP_* API); `DESIGN_SPECS/bitmap-flag-api.md`; v5.15.1 ship.

---

### TECH_DEBT-029 — Source file length reduction (large headers harm maintainability)

- **Created:** 2026-05-10 by Caramel musing during v5.14.10.0 PerCoreSnap layout work
- **Severity:** LOW (cosmetic / maintainability; no behavior or perf impact)
- **Surface:** Large single-file headers in the codebase. Inventory snapshot 2026-05-10 (refreshed 2026-05-13 post-v5.15.5.B umbrella):
  - `CoreFrameworks/ControllerEventLoop.hpp` — **post-v5.15.5.B GREW to 3640 lines (up from 3550 pre-.B; net +90 LOC). Pre-ship estimate of ~3800 was over-cautious; .B.7 AUTOPOPULATE absorbed ~145 LOC of EventLoopState_Init body into a 1-line registry-driven call but the .B.1 H/W/C cluster reorg comments + .B.2 sibling-struct/cluster definitions + .B.3 bitmap field comments etc. added ~235 LOC of structural documentation + cluster anchors. Net +90 LOC is one-time tech-debt closure investment.** Contents unchanged: EventLoopState + CoreContext + CoreSlowState definitions + Init/Free + RegisterCore + OnEvent + DrainEvents + RebuildAllParameters + UpdateRollingStateOneCore + RebuildOneCore + TimeExitOneCore + TrailingSLRatchetOneCore + helpers.
  - `CoreFrameworks/ControllerConfig.hpp` — 2727 lines (was largest as of 2026-05-10; cfg declarations + parser + defaults + validation)
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
- **Closure (v5.15.2.D):** /readiness Check 31 added (Check 26 placeholder reserved for v5.14.E.1 symmetry-test rule; Check 31 is the next free slot). Runs ALWAYS at audit start. Verifies predecessor postmortem documents `./build.sh gui suite tsan asan all` GREEN result (grep + commit-log scan). Non-blocking but flags risk that GUI/sanitizer-only compile errors lurk in the predecessor's surface area.
- **Status:** ✅ **CLOSED v5.15.2.D (2026-05-12).**
- **Cross-ref:** v5.14.post1 patch + postmortem; `tick-trader-percore-workspace/claude-skills/readiness/SKILL.md` Check 31 (added v5.15.2); v5.15.2 ship.

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

### TECH_DEBT-037 — Cfg-derived inference_cfg_* fields live in FOREACH_STAMP_BOUND_MODEL_CONST, not FOREACH_STAMP_BOUND_CFG (taxonomy drift)

- **Created:** 2026-05-12 by v5.15.3.A.1 helper extraction
- **Severity:** LOW (manual population works; just taxonomic asymmetry)
- **Surface:** `ML_Headers/StampHelper.hpp:158-187` (helper section 2a
  with cfg-derived model-const manual population); registry-tuple
  taxonomy split between FOREACH_STAMP_BOUND_CFG and
  FOREACH_STAMP_BOUND_MODEL_CONST
- **What's deferred:** `inference_cfg_confidence_threshold_scale`,
  `inference_cfg_barrier_gate_enabled`,
  `inference_cfg_confidence_hard_block_threshold`,
  `inference_cfg_held_out_fraction`,
  `inference_cfg_bandit_blend_ratio`,
  `inference_cfg_fee_rate_maker`, `inference_cfg_fee_rate_taker`,
  `training_poll_interval` are cfg-DERIVED but classified as
  model-const in the registry split (v5.14.8.A.merged historical
  taxonomy). STAMP_CFG_AUTOPOPULATE doesn't reach them; helper
  must manually `inf.X = cfg.X` for each. Adding a new cfg-derived
  inference_cfg_* field today needs both a registry entry AND a
  manual line in the helper section 2a.
- **Why deferred:** The proper fix has 2 options: (a) migrate these
  entries from FOREACH_STAMP_BOUND_MODEL_CONST to
  FOREACH_STAMP_BOUND_CFG so STAMP_CFG_AUTOPOPULATE auto-flows
  them (requires byte-equivalence verification + per-entry
  emit_when predicate restructure since registry-row shape
  differs between the two macros); or (b) extend
  STAMP_CFG_AUTOPOPULATE to optionally take cfg→stamp_field
  mappings (requires registry tuple extension; affects all 22
  current FOREACH_STAMP_BOUND_CFG entries). Either option is
  larger than v5.15.3 scope; manual section 2a works correctly
  today.
- **Cost estimate:** ~2-3h (option a; per-entry migration with
  byte-equivalence check) OR ~3-4h (option b; AUTOPOPULATE extension)
- **Trigger:** Address when (a) operator adds 3+ new cfg-derived
  inference_cfg_* fields in one sprint making manual section 2a
  painful, OR (b) v5.X+ AUTOPOPULATE consolidation sprint takes
  this on alongside TECH_DEBT-036 architectural-field redesign.
- **Status:** ✅ **CLOSED v5.15.5.A.7 (2026-05-12).** New
  `MemHeaders/CfgDerivedInferenceCfgRegistry.hpp` introduces single-source-of-truth
  registry for cfg-derived inference_cfg_* fields (3-col tuple:
  `name, cfg_extraction_expr, gate_when`). Companion macro
  `INFERENCE_CFG_AUTOPOPULATE(inf, cfg)` walks the registry + populates
  `inf.inference_cfg_<name>` via prefix-aware token-paste. Replaces the
  ~20-line manual section 2a at `ML_Headers/StampHelper.hpp:168-187`
  with ONE expansion. 11 entries today (7 existing migrated + 4 v5.15.5.A.7
  per-horizon barrier cohort). Future cfg-derived inference_cfg_* fields
  become 2 X-macro registry rows (MODEL_CONST entry for ModelHandle field +
  CFG_DERIVED entry for population); NO manual code; cannot drift.
  3rd application of `autopopulate-pattern-for-production-caller-class.md`
  pattern (after STAMP_CFG_AUTOPOPULATE v5.14.1.E.E.B + STAMP_MODEL_CONST_AUTOPOPULATE
  v5.14.8.A.merged quarantined at v5.15.3.A.1). Closes Class 18 mirror class
  at the cfg-derived MODEL_CONST surface permanently. New audit test asserts
  `FOREACH_CFG_DERIVED_INFERENCE_CFG_COUNT == 11`.
- **Cross-ref:** v5.15.5.A.7 ship; `MemHeaders/CfgDerivedInferenceCfgRegistry.hpp`;
  `ML_Headers/StampHelper.hpp:~165` (refactored to INFERENCE_CFG_AUTOPOPULATE call);
  `tick-trader-percore-workspace/DESIGN_SPECS/autopopulate-pattern-for-production-caller-class.md`
  (3rd application referenced); TECH_DEBT-036 (sister AUTOPOPULATE-MODEL_CONST
  redesign still OPEN; quarantined macro separate concern); CLAUDE.md item 21.

---

### TECH_DEBT-038 — FOREACH_BITMAP_WIDTH X-macro registry deferred (BITMAP_BIT/POPCOUNT/FIRST families)

- **Created:** 2026-05-12 by v5.15.5.A.1 design discussion (operator-
  posed: "would this benefit from a registry?")
- **Severity:** LOW (current explicit per-width macros work + are
  clearer to read; deferral is principled, not effort-avoidance)
- **Surface:** `MemHeaders/BitmapMacros.hpp` lines 156-181 — three
  width-typed macro families (BITMAP_BIT_U<W>, BITMAP_POPCOUNT_U<W>,
  BITMAP_FIRST_U<W>) each with 4 widths (U8/U16/U32/U64); 12 total
  explicit macros.
- **What's deferred:** Convert the 3 families to a single
  FOREACH_BITMAP_WIDTH(X) registry that auto-generates BIT, POPCOUNT,
  and FIRST macros per registered width. Tuple shape:
  `X(W, T, popcount_fn, ctz_fn, full_width_mask_literal)` — e.g.,
  `X(U8, uint8_t, __builtin_popcount, __builtin_ctz, 0xFFu)` etc.
- **Why deferred (not effort-avoidance):** Per CLAUDE.md item 13
  threshold (registry when adding next instance touches ≥2 sites),
  this IS technically eligible. BUT the width family is NATURALLY
  bounded by C integer types — uint128_t isn't standard C++ and
  CLAUDE.md item 20 trade-off note specifies bit-pack within a
  single record (max ~64 flags); cross-record bit-packing is
  anti-pattern. So 5th width is unlikely. The 3 operation families
  (BIT/POPCOUNT/FIRST) cover primary bitmap ops; a 4th family
  (BITMAP_LAST, BITMAP_PARITY, etc.) IS possible but not currently
  needed. Until either trigger fires (5th width OR 4th family), the
  explicit per-width macros are clearer and more self-documenting.
- **Cost estimate:** ~30-50 LOC refactor (registry definition +
  3 family generator blocks + per-width parameter encoding).
  LOW risk (additive macro definitions; existing callers see same
  expanded result; sizeof + bit-mask values byte-identical).
- **Trigger:** Address when (a) v5.X+ adds a 4th BITMAP operation
  family (e.g., BITMAP_LAST_U<W>, BITMAP_PARITY_U<W>, BITMAP_NTH_U<W>)
  — adding 4 macros for the new family across 4 widths is when
  registry value emerges, OR (b) operator wants `__uint128_t`
  support for some reason (not foreseeable but possible), OR
  (c) v5.X cleanup sprint takes this on alongside other
  registry-conversion candidates (TECH_DEBT-009 / -011 / -012
  family).
- **Status:** OPEN — explicit per-width macros for v5.15
  + foreseeable future; future consolidation candidate when one
  of the triggers fires.
- **Cross-ref:** `MemHeaders/BitmapMacros.hpp:156-181`;
  CLAUDE.md item 13 (X-macro registry standard pattern); CLAUDE.md
  item 20 (BITMAP_* API; trade-off note on per-record bit-packing
  bounds the width family); CLAUDE.md item 28 (latency-vs-cache
  decision framework; the explicit macros' marginal differences
  are intentional per-width optimizations); v5.15.5.A.1 audit
  discussion 2026-05-12 establishing the deferral principle.

---

### TECH_DEBT-039 — ConfidenceScorer_UpdateAndMark CLOCK_REALTIME residual (drift-history wall-clock dependency)

- **Created:** 2026-05-12 by /merge-scan during v5.15.5.B pre-coding audit (Finding 2 residual)
- **Severity:** LOW (operationally negligible; per-fill cadence not per-cycle; wall-clock is semantically appropriate for drift-history's age-anchoring)
- **Surface:** `CoreFrameworks/ControllerEventLoop.hpp:1368` — `ConfidenceScorer_UpdateAndMark` call site does its OWN `clock_gettime(CLOCK_REALTIME, &ts)` inside drift-history sampling path
- **Context:** The v5.12.1.B `rebuild_ts_us` hoist pattern (engine-wide `now_us` cached once at slow-path entry + threaded into all consumers) is the canonical clock-read-sharing discipline (CLAUDE.md item 16 reuse-audit). The `ConfidenceScorer_UpdateAndMark` site is a residual exception because drift-history is wall-clock-anchored (CLOCK_REALTIME, drift "age" computed as wall-time delta), distinct from the slow-path cadence which is monotonic (CLOCK_MONOTONIC equivalent via `system_clock`). Two distinct clock domains today; converging is a semantic decision, not a mechanical one.
- **What's deferred:** Migrate drift-history age-anchoring from CLOCK_REALTIME to CLOCK_MONOTONIC (or equivalent monotonic source) — eliminates the per-fill `clock_gettime` call by reusing `rebuild_ts_us` (already in scope at the call site). Alternatively: keep CLOCK_REALTIME but hoist the read to slow-path entry (parallel to `rebuild_ts_us`) + thread into `ConfidenceScorer_UpdateAndMark` via existing scorer context.
- **Why deferred (not effort-avoidance):** Per-fill cadence (typical 1-10 fills/sec at active trading; far less at rest) means the saved `clock_gettime` call is ~50-100 ns × 1-10 Hz = 50-1000 ns/sec engine-wide — operationally negligible. The semantic conversion (wall-clock → monotonic for drift age) is the load-bearing question: drift-history age display in MLStatusPanel uses wall-clock seconds ("3.5 hours since last drift event"); converting to monotonic would shift the operator-visible age semantics. Decision requires confirming whether drift-history wall-clock-anchoring is essential (audit log correlation? operator timezone-aware UX?) or incidental (just-happens-to-be-CLOCK_REALTIME).
- **Cost estimate:** ~30 LOC migration + audit of drift-history age display + ~1h decision discussion with operator about wall-clock semantics. LOW.
- **Trigger:** Address (a) when next ML observability cleanup ship touches DriftHistory / MLStatusPanel; (b) operator-driven decision about drift-history age semantics; (c) if drift-history age computation moves to a context where monotonic is structurally cleaner (e.g., reproducible replay test fixtures).
- **Status:** OPEN
- **Cross-ref:** `CoreFrameworks/ControllerEventLoop.hpp:1368` (the residual call site); `CoreFrameworks/EngineSharded.hpp:3073-3075` (canonical `rebuild_ts_us` hoist; this is the pattern the residual diverges from); CLAUDE.md item 16 (reuse-audit / shared clock reads); `ML_Headers/ConfidenceScore.hpp` (DriftHistory struct using CLOCK_REALTIME); v5.15.5.B `/merge-scan` audit Finding 2 residual identification 2026-05-12.

---

### TECH_DEBT-040 — FOREACH_SESSION_PHASE cfg-side registry for 4 session_*_mult cfg fields

- **Created:** 2026-05-12 by v5.15.5.B audit (.B.5 surfaced consumer-side branchless conversion; cfg-side cohort registry deferred)
- **Severity:** LOW (4-instance cohort; semantically bounded; cfg-side refactor independent of consumer-side branchless dispatch)
- **Surface:**
  - `CoreFrameworks/ControllerConfig.hpp` — 4 `session_asian_mult / session_european_mult / session_us_mult / session_overnight_mult` cfg fields (cfg-side cohort)
  - `CoreFrameworks/ControllerEventLoop.hpp:2101-2106` — consumer-side 4-way if/else dispatch (CLOSED in v5.15.5.B.5 via branchless `SESSION_BY_HOUR[24]` lookup table + `session_mult_lookup[4]` indexed by `SESSION_*` enum)
- **Context:** v5.15.5.B.5 converts the CONSUMER-SIDE 4-way if/else to branchless table-lookup, but the CFG-SIDE remains 4 separate cfg fields with parallel cfg declarations / tooltips / parser entries / GUI inputs / use sites. That's the canonical X-macro registry candidate per CLAUDE.md item 13 (FOREACH_SESSION_PHASE(X) with `X(ASIAN, "asian", 0, 7) X(EUROPEAN, "european", 7, 13) ...` 4 rows; auto-flow cfg field decl + parser + GUI input + the consumer-side SESSION_BY_HOUR lookup table + session_mult_lookup array).
- **What's deferred:** `FOREACH_SESSION_PHASE(X)` registry on the cfg side. Adding a 5th session phase (e.g., extra granularity for Asia open / close) becomes 1 row + auto-flow vs today's 5-site touch.
- **Why deferred (not effort-avoidance):** v5.15.5.B is already a 9-sub-ship + umbrella ~1030-LOC ship; the cfg-side refactor is a separate concern (cfg declarations + parser + GUI). Bundling further bloats blast radius. Consumer-side branchless conversion (.B.5) captures the immediate latency-discipline win; cfg-side registry is a focused future cleanup that doesn't block.
- **Cost estimate:** ~80-120 LOC (registry definition + cfg field auto-gen + parser auto-gen + GUI input auto-gen + tooltip auto-gen + .B.5 lookup table refactor to use registry). MEDIUM-LOW.
- **Trigger:** Address (a) when adding a 5th session phase is required (currently no plans); (b) cfg-system cleanup sprint focused on cfg-field cohort discipline; (c) when FOREACH_<DOMAIN>_CFG_FLAG registry pattern (already established v5.14.9.F for bool cohorts) extends to enum/float cohorts via a new variant.
- **Status:** ✅ **CLOSED v5.15.5.B.5** — `FOREACH_SESSION_PHASE(X)` registry shipped (`CoreFrameworks/SessionPhaseRegistry.hpp`). 6-column tuple `X(NAME_U, name_l, START, END, DEFAULT_MULT, DOC)` drives: cfg field decl + default-init + parser entry (`ControllerConfig.hpp`); branchless `SESSION_BY_HOUR[24]` constexpr lookup table; per-consumer `session_mult_lookup[]` array (3 consumer sites all migrated: ControllerEventLoop.hpp:2305+, ShardedSnapshot.hpp:175+, PortfolioController.hpp:1503+). First explicit FLOAT-cohort cfg-registry variant; pattern documented for promotion in `DESIGN_SPECS/cfg-flag-eligibility-criteria.md` (subsection to add at .B umbrella).
- **Cross-ref:** `CoreFrameworks/SessionPhaseRegistry.hpp` (registry); `CoreFrameworks/ControllerConfig.hpp` (cfg field decl + default + parser auto-flowed via X-macro); `CoreFrameworks/ControllerEventLoop.hpp` + `CoreFrameworks/ShardedSnapshot.hpp` + `CoreFrameworks/PortfolioController.hpp` (3 consumer sites branchless-converted); CLAUDE.md item 13 + item 28.

### TECH_DEBT-041 — Multi-bit state encoding codebase audit + remaining candidate applications

- **Created:** 2026-05-13 by v5.15.5.C.2.1 close (first application shipped; codebase audit deferred)
- **Severity:** MEDIUM (~120-150 bytes savable across EventLoopState + per-cycle branchless dispatch wins; bounded scope; design substrate already in place via `DESIGN_SPECS/multi-bit-state-encoding-pattern.md` + first application `MemHeaders/OmsExitPredictorMetaRegistry.hpp`)
- **Surface:**
  - `CoreFrameworks/ControllerEventLoop.hpp` CoreContext `regime_state.current_regime` + `regime_state.proposed_regime` — 2 × `int` (8 bytes each) = 16 bytes per CoreContext × 16 cores = **256 bytes per EventLoopState**. 4-state field × 2 sub-fields = 4 bits packable into a shared `uint8_t regime_field`.
  - `CoreFrameworks/ControllerEventLoop.hpp` CoreContext `strategy_id` — `uint8_t` per core; 5 strategies (SIMPLE_DIP/MOMENTUM/EMA_CROSS/ML + future) → 3 bits. Modest savings; enables branchless multi-strategy dispatch in slow-path body.
  - `CoreFrameworks/Order.hpp` `OrderType type` — `uint8_t` per Order; 4-8 types (BUY/SELL/LIMIT_*/CANCELED/...). **Cross-record per CLAUDE.md item 20 — likely fails the per-record packing discipline.** Audit must validate against item 20.
  - `CoreFrameworks/Order.hpp` `OrderState state` — `uint8_t` per Order; ~5 states (SUBMITTED/PARTIAL_FILL/FILLED/REJECTED/CANCELED). Same cross-record concern.
  - `DataStream/TradeEvent.hpp` `TradeEventType` — 3 states (ENTRY/EXIT/COMBINED). Per-event, modest savings; cross-record concern.
  - `CoreFrameworks/ControllerEventLoop.hpp` `halt_reason` codes on PerCoreSnap — currently a small enum; adjacent to other state flags; cohort candidate.
- **Context:** v5.15.5.C.2.1 shipped FIRST APPLICATION of `multi-bit-state-encoding-pattern.md` (OMS per-slot exit-predictor cohort: arm + regime + valid in 1 byte; 16 bytes saved per OMS). The design spec includes a candidate inventory section with 6 follow-up candidates. The codebase audit (Caramel's task #7 follow-up) walks each candidate against the design spec's decision tree + CLAUDE.md item 20 per-record-packing discipline. Output: ranked punch list of structural applications.
- **What's deferred:** Walk-through of the candidate inventory + per-candidate decision (apply / defer / reject-per-item-20). For accepted candidates: registry header + struct migration + consumer migration. The biggest unsoaked candidate (rs_current + rs_proposed cohort) saves ~112B per EventLoopState + adds branchless multi-regime predicate in the slow-path body (currently 4-way `switch (rs_current)` dispatch).
- **Why deferred (not effort-avoidance):** v5.15.5.C is already a 4-ship sub-sprint (.C.1 + .C.2 + .C.2.1 + queued .C.3) focused on OrderManagerState; rs_current/rs_proposed migration touches RegimeDetector + load/save + per-core slow-path body — a separate concern. First application via OMS exit-predictor (.C.2.1) field-validates the pattern; subsequent applications can ship as a focused MULTI-BIT-APPLICATIONS sub-sprint with `/dod-audit` + `/test-strength-audit` per migration.
- **Cost estimate:**
  - Per-candidate evaluation + decision: ~5-10 min per candidate × 6 candidates = ~1 hour total
  - rs_current/rs_proposed migration (highest-value candidate): registry header + struct field + ~12 consumer sites in RegimeDetector + ControllerEventLoop + snapshot persist (wire format!) + tests. ~3-5 hours.
  - strategy_id migration: ~1-2 hours.
  - halt_reason cohort: ~2-3 hours.
  - Other candidates likely REJECT per item 20 cross-record-pack rule.
  - Total: ~7-12 hours focused MULTI-BIT-APPLICATIONS sub-sprint.
- **Trigger:** Address (a) when a focused multi-bit applications sub-sprint is scheduled (likely after .C.3 + .C.4 OMS work completes; v5.15.5.F or v5.16); (b) when adding a new K-state field that has K=2-16 sibling cohort fields within the same record (the cohort audit rule from CLAUDE.local.md 2026-05-11 triggers); (c) when memory pressure on EventLoopState becomes a bottleneck.
- **Status:** OPEN
- **Cross-ref:** `DESIGN_SPECS/multi-bit-state-encoding-pattern.md` (the design + candidate inventory + 10-item implementation checklist + decision tree + cost-benefit table); `MemHeaders/OmsExitPredictorMetaRegistry.hpp` (first field-tested application; v5.15.5.C.2.1 commit `097f91f`); CLAUDE.local.md "Going-forward rule: prefer multi-bit state encoding for K-state fields (set 2026-05-13)"; CLAUDE.md item 20 (per-record packing discipline) + item 28 (latency-vs-cache framework) + item 13 (X-macro registry).

### TECH_DEBT-042 — Registry-driven multi-bit slot overlap static_asserts (OmsStateFlagRegistry hybrid layout)

- **Created:** 2026-05-13 by /dod-audit MEDIUM-1 on commit `d410525` (v5.15.5.C.3 Phase 3b checkpoint)
- **Severity:** MEDIUM
- **Surface:** `MemHeaders/OmsStateFlagRegistry.hpp:190-209`
- **What's deferred:** EVENT_LOG_MODE slot overlap static_asserts are NAMED-EXPLICIT (3 asserts hand-rolled per slot); adding a 2nd multi-bit slot to `FOREACH_OMS_STATE_MULTI_BIT` requires hand-writing parallel asserts. Class-18 mirror at compile-time-check level — the registry currently generates `MASK_OMS_STATE_<name>` + `SHIFT_OMS_STATE_<name>` + `BITS_OMS_STATE_<name>` constants but NOT the safety asserts. Header comment line 190 acknowledges this with "extend with similar checks per added slot". A 4th X-macro consumer (`X_GEN_OMS_STATE_MULTI_BIT_OVERLAP_CHECK`) can auto-generate per-slot overlap pair-asserts via `FOREACH_OMS_STATE_MULTI_BIT(X)` walking the registry: single-bit-region overlap + uint8_t capacity + (for pairwise inter-slot overlap) a running `_OMS_STATE_MULTI_BIT_REGION` bitmask via the walk.
- **Why deferred (not effort-avoidance):** single multi-bit slot today (EVENT_LOG_MODE); deferral cost is one missed-pattern-application; trigger fires at 2nd multi-bit slot addition. Current hand-rolled asserts ARE complete + correct for the 1-slot state; structural fix is preventative.
- **Cost estimate:** ~30 min (8-15 LOC X_GEN_OMS_STATE_MULTI_BIT_OVERLAP_CHECK macro + verify all 3 asserts still fire with current data).
- **Trigger:** (a) next addition to `FOREACH_OMS_STATE_MULTI_BIT` (or first cross-registry multi-bit cohort pattern application introducing a 2nd slot); (b) any 2nd consumer of `FOREACH_OMS_STATE_MULTI_BIT` that requires similar overlap guarantees.
- **Status:** OPEN
- **Cross-ref:** `DESIGN_SPECS/multi-bit-state-encoding-pattern.md` Implementation Checklist; CLAUDE.md item 13 (X-macro registry), item 19 (structural fix preferred for recurring class); `plans/plan_checks/dod-audit-2026-05-13-v5.15.5.C.3-phase3b.md` MEDIUM-1.

### TECH_DEBT-043 — OmsExitPredictorMetaRegistry custom OMS_META_* duplicates generic MBS_* primitives

- **Created:** 2026-05-13 by /dod-audit LOW-1 on commit `d410525` (v5.15.5.C.3 Phase 3b checkpoint)
- **Severity:** LOW
- **Surface:** `MemHeaders/OmsExitPredictorMetaRegistry.hpp:126-149` (OMS_META_GET_REGIME / OMS_META_GET_ARM / OMS_META_IS_VALID / OMS_META_PACK / OMS_META_CLEAR)
- **What's deferred:** `OmsExitPredictorMetaRegistry.hpp` (v5.15.5.C.2.1) shipped the FIRST multi-bit application with custom domain-specific accessors. Phase 3b adds generic `MBS_GET_U8` / `MBS_SET_U8` / `MBS_EQ_U8` primitives in `BitmapMacros.hpp` that supersede the domain-specific shorthand. `OMS_META_*` macros are functionally equivalent to `MBS_*` but pre-date the generic API. No bug; duplicated mechanism (CLAUDE.md item 16 reuse-audit principle). Future K-state slot additions should use generic `MBS_*` directly; `OMS_META_*` could migrate to thin convenience aliases or be removed.
- **Why deferred (not effort-avoidance):** functional equivalence; no bug; pure reuse-audit cleanup. Existing `OMS_META_*` consumers work correctly; migration is style + DRY consistency, not load-bearing.
- **Cost estimate:** ~1-2h (4 macros to rewrite as thin wrappers over `MBS_*_U8` + verify all 4-6 consumer sites compile / produce identical bytes / pass round-trip tests).
- **Trigger:** (a) next edit to `MemHeaders/OmsExitPredictorMetaRegistry.hpp` (extending the layout); (b) next edit to its accessor consumers (drainer HandleFill attribution + slow-path submit-time write); (c) focused reuse-audit cleanup sub-sprint.
- **Status:** OPEN
- **Cross-ref:** `DESIGN_SPECS/multi-bit-state-encoding-pattern.md` (canonical generic API); CLAUDE.md item 16 (reuse-audit principle); `MemHeaders/BitmapMacros.hpp:192-195` (header doc acknowledges pre-existing first application); `plans/plan_checks/dod-audit-2026-05-13-v5.15.5.C.3-phase3b.md` LOW-1.

### TECH_DEBT-044 — OMS_PROJECT_INIT_BIT / RESET_BIT use if/else; branchless mask-select for consistency with item 18(a)

- **Created:** 2026-05-13 by /dod-audit LOW-2 on commit `d410525` (v5.15.5.C.3 Phase 3b checkpoint)
- **Severity:** LOW
- **Surface:** `MemHeaders/OmsFieldRegistry.hpp:371-375` (OMS_PROJECT_INIT_BIT) + `:410-414` (OMS_PROJECT_RESET_DO_RESET_BIT)
- **What's deferred:** BIT-kind init/reset macros use data-dependent branch on init/reset value (`if ((int)(init)) field |= mask; else field &= ~mask;`). Branchless variant via `mask_val = -(int)!!init & mask; field = (field & ~mask) | mask_val` would be consistent with codebase's branchless mask discipline per CLAUDE.md item 18(a). Compiler likely cmov's the original form for the predictable boot-time path → zero measurable perf impact; style/consistency cleanup.
- **Why deferred (not effort-avoidance):** boot-only paths (zero measurable perf — branch fires few times per boot, predictable, cmov'd by compiler); style/consistency only. Branchy form is also more readable for OR-or-CLR semantics; branchless variant trades readability for instruction-count discipline.
- **Cost estimate:** ~5 min (2-line macro rewrite each × 2 macros = ~8 LOC).
- **Trigger:** (a) next AUTOPOPULATE-shape pattern application running at non-boot cadence (slow-path AUTOPOPULATE, hot-path AUTOPOPULATE); (b) /dod-audit or /merge-scan surfaces this site in a per-cycle context; (c) codebase-wide branchless-discipline sweep.
- **Status:** OPEN
- **Cross-ref:** CLAUDE.md item 18(a) (branchless mask compute), item 28 (latency-vs-cache framework); `DESIGN_SPECS/latency-vs-cache-decision-framework.md` Rule 2 "Prefer branchless over data-dependent branches"; `plans/plan_checks/dod-audit-2026-05-13-v5.15.5.C.3-phase3b.md` LOW-2.

### TECH_DEBT-045 — Phase 7.B runtime bench gate integration (template-dispatch wrappers + N instrumented sites + TUI surface)

- **Created:** 2026-05-13 by v5.15.5.C.3 Phase 7.A close (cfg + LatencyHistogram substrate shipped; integration deferred to focused follow-up)
- **Severity:** LOW (operator-facing feature; substrate complete; integration is mechanical wiring + TUI display)
- **Surface:**
  - `MemHeaders/LatencyHistogram.hpp` — primitive shipped (Phase 7.A: struct + accumulate + reset + percentile + tests)
  - `CoreFrameworks/ControllerConfig.hpp` — `cfg.oms_bench_enabled` flag shipped (Phase 7.A; default 0)
  - `CoreFrameworks/EngineSharded.hpp` — boot-time template dispatch NOT YET WIRED
  - Instrumented sites NOT YET WIRED:
    - `OrderManager_Tick<F, BENCH>` (wrap existing `OrderManager_Tick_Body`)
    - `OMS_DrainSubmit<F, BENCH>` (wrap existing drain submit body)
    - `DrainPostFill<F, BENCH>` per-fill timing inside the close-mask loop
  - TUI surface NOT YET WIRED: 1-line stderr / TUI bench histogram readout per snapshot publish (BENCH=true only; BENCH=false has zero TUI bench output by compile-time elision)
- **Context:** v5.15.5.C.3 Phase 7.A shipped the SUBSTRATE for runtime bench gate per `DESIGN_SPECS/runtime-toggleable-bench-gate-pattern.md`. The cfg flag has NO observable effect today; integration requires:
  1. Template `<unsigned F, bool BENCH>` propagation through `EngineSharded_Run` → drainer loop → instrumented call sites
  2. Boot-time dispatch in EngineSharded_Run wrapper: `if (cfg.oms_bench_enabled) EngineSharded_Run<F, true>(...) else EngineSharded_Run<F, false>(...)`
  3. Per-site bench bracket: `if constexpr (BENCH) { uint64_t t0 = __rdtsc(); body(); hist.accumulate(__rdtsc() - t0); } else { body(); }`
  4. Histogram allocation site: either on OrderManagerState (COLD cluster sub-cluster) or as static thread_local globals per drainer thread
  5. TUI surface: snapshot publisher reads histograms + emits p50/p99/max line via `LatencyHistogram_Percentile` helper
- **What's deferred:** All 5 items above (template propagation, boot dispatch, per-site brackets, histogram allocation, TUI surface).
- **Why deferred (not effort-avoidance):** v5.15.5.C.3 already covers 8 phases of substantial work (canonical OMS registry refactor + MULTI_BIT + per-strategy emit + per-trade regime + paper-reset archive + per-slot macro consolidation). Phase 7.B integration is mechanical wiring once substrate is in place; deferral lets Phase 7.A ship the foundation cleanly + lets Phase 7.B be a focused ~1-2h follow-up that's easy to audit. Compose-with patterns from the design spec (AUTOPOPULATE for N-site instrumentation, multi-bit bench mode encoding, per-core bench enable) become opt-in extensions during Phase 7.B design.
- **Cost estimate:** ~1-2h (template propagation + 3 instrumented sites + TUI line + integration tests).
- **Trigger:** (a) operator wants to flip `cfg.oms_bench_enabled=1` and see latencies (USER demand); (b) paper-test cadence tightens enough that visibility into slow-path latency matters; (c) specific latency regression investigation needs in-binary bench (avoids rebuild cycle); (d) maker-order ship (v6.0) where slow-path latency is operator-tunable.
- **Status:** OPEN
- **Cross-ref:** `MemHeaders/LatencyHistogram.hpp` (Phase 7.A substrate); `DESIGN_SPECS/runtime-toggleable-bench-gate-pattern.md` (full design + 7 composition options); `CoreFrameworks/ControllerConfig.hpp` `oms_bench_enabled` field; CLAUDE.md item 18 (compile-time elision); CLAUDE.md item 25 (cross-thread cluster isolation); CLAUDE.md item 28 (latency-vs-cache framework).

### TECH_DEBT-046 — Fast-path companion accessor pattern (`_Fast` suffix for canonical runtime parameter) codification deferred to 2nd application

- **Created:** 2026-05-13 by v5.15.5.D close (first application shipped as `BookImbHistory_MeanShortFast`; codification deferred per pattern-codification-lifecycle.md Stage 0 "Skip when pattern is ONE-OFF" rule)
- **Severity:** LOW (no bug; pattern documentation gap; cohort migration on 2nd application closes the gap)
- **Surface:**
  - `ML_Headers/FlowFeatures.hpp:~115` — first application: `BookImbHistory_MeanShortFast(s)` paired with `BookImbHistory_MeanShort(s, int k)` (general API kept for tests with k=2)
  - Pattern shape: when a public API takes a runtime parameter `k` (or similar) that's almost always one canonical value at the production caller (production: k=64; test: k=2), expose a `_Fast` companion accessor that returns the cached/derived result for the canonical case (no runtime branch on k); keep the general API for non-canonical callers.
  - Other potential application sites (NOT surveyed in v5.15.5.D; surface during 2nd-app trigger investigation):
    - RollingStats accessors that take a window size (currently template-parameterized — different shape; may or may not benefit)
    - Any other "MeanShort(int k)" / "Mean(int k)" / "Variance(int k)" pattern in ML_Headers or Strategies
- **What's deferred:** Writing a DESIGN_SPECS doc for the pattern + applying it via the pattern-codification-lifecycle.md 7-stage process (Stage 0: identification + first reference are done; Stage 1-7: codify when a 2nd application surfaces).
- **Why deferred (not effort-avoidance):** per `DESIGN_SPECS/pattern-codification-lifecycle.md` "Skip when: pattern is ONE-OFF — apply structural fix without codification overhead." First application IS valuable on its own (eliminates O(K) walk in BookImbHistory); codification overhead (~4-6h for a focused codification ship) is not justified for 1 application. 2+ applications triggers full codification.
- **Cost estimate (if/when triggered):** ~4-6h for codification per the lifecycle (Stage 1 audit ~1h + Stage 2 DESIGN_SPEC ~1-2h + Stage 3-4 second application ~30 min - 2h + Stage 5 CLAUDE.md ~30 min + Stage 6 tooling ~30 min - 1h + Stage 7 wider audit ~1h).
- **Trigger:** (a) 2nd potential application site surfaces (in a `/merge-scan` or `/dod-audit` finding, or during a new ship's pre-coding); (b) operator-initiated codification request (e.g., as part of a focused pattern-codification sprint).
- **Status:** OPEN (awaiting 2nd-application trigger)
- **Cross-ref:** v5.15.5.D postmortem at `plans/v5.15-live-readiness/postmortems/2026-05-13-v5.15.5-D-postmortem.md` "Pattern B captured for future codification"; `ML_Headers/FlowFeatures.hpp` BookImbHistory_MeanShortFast (first application); `DESIGN_SPECS/pattern-codification-lifecycle.md` Stage 0 (identification + first reference complete).

### TECH_DEBT-049 — AoS time-series pattern codification deferred to 2nd application

- **Created:** 2026-05-13 by v5.15.5.E.B close (first application shipped as DriftHistory AoS DriftSample interleave; codification deferred per pattern-codification-lifecycle.md Stage 0 "Skip when pattern is ONE-OFF" rule)
- **Severity:** LOW (no bug; pattern documentation gap; cohort migration on 2nd application closes the gap)
- **Surface:**
  - `ML_Headers/ConfidenceScore.hpp:~657` (post-.E.B) — first application: `DriftSample {double ic; uint64_t ts;}; samples[256]` replaces parallel `double ic_samples[256] + uint64_t ts_us[256]` arrays.
  - Pattern shape: when a struct stores parallel arrays where each element-index is read at the same iteration step (canonical case: time-series with paired value + timestamp accessed together), prefer AoS `struct Sample {...}; samples[N]` over SoA parallel arrays. Per-iteration cache footprint: 1 line vs 2 lines (when array spacing > cache line size).
  - Other potential application sites (NOT surveyed in v5.15.5.E.B; surface during 2nd-app trigger investigation):
    - Future RollingFoo types that pair (value, timestamp) per sample
    - Per-cycle event-log structs with (event_data, event_time) pairs
    - Any "parallel arrays accessed at same index" pattern in tight loops
- **What's deferred:** Writing a DESIGN_SPECS doc `aos-time-series-pattern.md` for the pattern + applying it via the pattern-codification-lifecycle.md 7-stage process (Stage 0: identification + first reference are done; Stage 1-7: codify when a 2nd application surfaces).
- **Why deferred (not effort-avoidance):** per `DESIGN_SPECS/pattern-codification-lifecycle.md` "Skip when: pattern is ONE-OFF — apply structural fix without codification overhead." First application IS valuable on its own (2× CheckBreach cache locality); codification overhead (~4-6h for a focused codification ship) is not justified for 1 application. 2+ applications triggers full codification.
- **Cost estimate (if/when triggered):** ~4-6h for codification per the lifecycle (Stage 1 audit ~1h + Stage 2 DESIGN_SPEC ~1-2h + Stage 3-4 second application ~30 min - 2h + Stage 5 CLAUDE.md ~30 min + Stage 6 tooling ~30 min - 1h + Stage 7 wider audit ~1h).
- **Trigger:** (a) 2nd potential application site surfaces (in a `/merge-scan` or `/dod-audit` finding, or during a new ship's pre-coding); (b) operator-initiated codification request.
- **Status:** OPEN (awaiting 2nd-application trigger)
- **Cross-ref:** v5.15.5.E postmortem at `plans/v5.15-live-readiness/postmortems/2026-05-13-v5.15.5-E-postmortem.md`; `ML_Headers/ConfidenceScore.hpp` DriftSample struct (first application); `DESIGN_SPECS/latency-vs-cache-decision-framework.md` (cost framework that justifies the AoS decision); `DESIGN_SPECS/pattern-codification-lifecycle.md` Stage 0.

---

## Drift-class closures (v5.15.5.F.4 — universal cfg field registry sprint)

The v5.15.5.F.4 sprint structurally closes 7 recurring drift classes via the universal cfg field registry + categorical-tag applicability + STAMP_BOUND derived filter + bitmap overflow audit. Class-level closures (individual TECH_DEBT-NNN entries flip CLOSED on their addressing ship):

| Class | Closure mechanism | Closure ship |
|---|---|---|
| `parser_gap` (cfg parser drift across files; 123 missed cfg fields proved recurrence) | registry-driven parser via `tt::cfg_parse_field<KIND_X>` + `lives_in_struct` routing | `.F.4b` (DOUBLE/PCT) + `.F.4c` (INT/INT_ENUM/BOOL) + `.F.4d` (STRING/FILE_PATH) |
| `panel_gap` (SettingsPanel field_defs[] drift) | registry-driven GUI render walk | `.F.4b-d` |
| `persist_gap` (manual Cfg_Save drift; cfg.example documentation drift) | registry-driven save dispatch + cfg.example auto-gen per `lives_in_struct` | `.F.4d` |
| `per_core_gap` (per-core override emission drift; PARITY-002/003/004/005/008 4× recurrence) | `PER_CORE_OK` metadata bit auto-emits override storage + AoS-by-core re-layout consolidates scattered arrays | `.F.4b` (auto-emit) + `.F.4g` (AoS-by-core) |
| `stamp_drift_gap` (TECH_DEBT-006: FOREACH_STAMP_BOUND_CFG vs FOREACH_CFG_FIELD dual registry) | `STAMP_BOUND` derived filter + canonical byte order locked via CI hash test (Layer 5b of `wire-format-byte-preservation-discipline.md`) | `.F.4b` |
| `cfg.example_doc_gap` (cfg.example manual drift; 7th gap class from registry spec future work) | AUTOPOPULATE companion emits per-`lives_in_struct` cfg.example | `.F.4d` |
| `silent_bitmap_truncation` (Class 20: FOREACH_X paired with bitmap field, no overflow guard) | `.F.4h` audit pass adds `static_assert` to all existing bitmap-paired registries | `.F.4h` |

**Hardcoded-instance-gating class (Class 19)** was not previously surfaced as TECH_DEBT but would have recurred on next strategy / regime / op_mode addition. Closed proactively by categorical-tag pattern at `.F.4b/h`.

---

### TECH_DEBT-050 — controller.cfg integration into universal cfg field registry deferred to v5.15.6

- **Created:** 2026-05-14 by v5.15.5.F.4 planning (universal cfg field registry sprint scope cap)
- **Severity:** MEDIUM (operator-visible — controller.cfg currently requires manual text edit)
- **Surface:** `controller.cfg` + corresponding ControllerCfg struct + foxml_suite Settings tab
- **What's deferred:** extend FOREACH_CFG_FIELD with controller.cfg fields tagged `lives_in_struct=STRUCT_CONTROLLER_CFG`. Currently controller.cfg fields don't surface in Settings tab; operator edits the file manually.
- **Why deferred (not effort-avoidance):** v5.15.5.F.4 caps scope at engine+backtest unification (9 sub-ships). controller.cfg integration is mechanical extension of design locked at `.F.4b`; ships in v5.15.6.A as a focused follow-on sprint.
- **Cost estimate:** ~2-3h (audit ControllerCfg struct + add ~10-20 rows + verify byte-identical roundtrip + Settings tab dispatch).
- **Trigger:** v5.15.6 sprint kickoff OR earlier if operator complaint surfaces about controller.cfg manual edit friction.
- **Status:** OPEN
- **Cross-ref:** `plans/v5.15-live-readiness/subplans/2026-05-13-v5.15.5.F.4-universal-cfg-registry-sprint.md` (umbrella, v5.15.6 section); `DESIGN_SPECS/categorical-tag-applicability-pattern.md` § "Cross-file cfg unification"; `plans/v5.15-live-readiness/subplans/2026-05-14-v5.15.5.F.4i-backtest-cfg-integration.md` (sister; backtest is the prototype that this ship inherits the pattern from).

### TECH_DEBT-051 — secrets.cfg integration with IS_SECRET metadata deferred to v5.15.6

- **Created:** 2026-05-14 by v5.15.5.F.4 planning
- **Severity:** MEDIUM (operator-visible + security-critical — secrets currently require manual text edit + no UX safeguards)
- **Surface:** `secrets.cfg` + SecretsCfg struct + foxml_suite Settings tab
- **What's deferred:** extend FOREACH_CFG_FIELD with secrets.cfg fields tagged `lives_in_struct=STRUCT_SECRETS_CFG, metadata_flags |= IS_SECRET | LOG_VALUE_FORBIDDEN | SAFETY_CRITICAL`. GUI password masking via ImGuiInputTextFlags_Password; never-log enforcement via `Cfg_DumpForLogging` redaction; HMAC stamps never include IS_SECRET fields.
- **Why deferred:** scope cap; v5.15.6.B. Requires careful UX work (password masking + confirmation modal + security audit pass).
- **Cost estimate:** ~3-4h (audit + IS_SECRET metadata wiring + GUI affordances + security audit).
- **Trigger:** v5.15.6 sprint OR earlier if security concern surfaces.
- **Status:** OPEN
- **Cross-ref:** sister to TECH_DEBT-050; `DESIGN_SPECS/universal-cfg-field-registry-pattern.md` § "MetadataFlag enum" (IS_SECRET bit reserved at `.F.4b`); `plans/v5.15-live-readiness/subplans/2026-05-13-v5.15.5.F.4d-string-filepath-gui-metadata.md` (IS_SECRET first GUI application).

### TECH_DEBT-052 — Training cfg integration deferred to v5.15.6

- **Created:** 2026-05-14 by v5.15.5.F.4 planning
- **Severity:** MEDIUM (operator-visible — training params currently scattered between foxml_suite Training panel + Python scripts)
- **Surface:** training cfg (xgb hyperparameters + training pipeline params) + TrainingCfg struct + foxml_suite Training panel
- **What's deferred:** extend FOREACH_CFG_FIELD with training cfg fields tagged `lives_in_struct=STRUCT_TRAINING_CFG, applies_to_op_mode_cat=OP_MODE_CAT_TRAINING`. May require Kind enum extension: KIND_RANGE_INT, KIND_RANGE_DOUBLE for hyperparameter sweep ranges (e.g., `xgb_max_depth_range=4,6,8,12`).
- **Why deferred:** scope cap; v5.15.6.C. New Kind values require additional tt:: dispatch specializations.
- **Cost estimate:** ~3-4h (audit + new KIND_RANGE_* tt:: specializations if needed + Training panel integration).
- **Trigger:** v5.15.6 sprint OR earlier if Training panel UX concern surfaces.
- **Status:** OPEN
- **Cross-ref:** sister to TECH_DEBT-050/051; `DOCS/CLAUDE_FOXML_SUITE.md` (training panel architecture); `DESIGN_SPECS/universal-cfg-field-registry-pattern.md` (KIND_RANGE_* reserved in descriptor).

### TECH_DEBT-053 — Phase 2 cfg struct unification (merge cfg structs into one) deferred to v5.16+

- **Created:** 2026-05-14 by v5.15.5.F.4 planning
- **Severity:** LOW (architectural cleanup; Phase 1 GUI unification at v5.15.5.F.4 + v5.15.6 covers operator UX needs)
- **Surface:** All 5 cfg structs (ControllerConfig + BacktestCfg + ControllerCfg + SecretsCfg + TrainingCfg)
- **What's deferred:** merge separate cfg structs into ONE struct with nested sections (`cfg.engine.X`, `cfg.backtest.X`, `cfg.controller.X`, etc.). Currently Phase 1 keeps structs separate; `lives_in_struct` discriminator routes parser/save.
- **Why deferred:** Phase 1 covers all operator-visible cfg unification needs without struct refactoring. Phase 2 is downstream code cleanup, not user-facing. Defer until v6.0 architectural pressure or burdensome cross-struct accessor surface.
- **Cost estimate:** ~6-8h (significant — touches Cfg struct definition + all consumers + may break snapshot wire format if Cfg is persisted; would need version bump + migration).
- **Trigger:** (a) v6.0 headless-service split where unified Cfg simplifies cross-process state externalization; (b) cross-struct accessor site count becomes burdensome; (c) Phase 1 validates the unification model + Phase 2 becomes worth the refactor cost.
- **Status:** OPEN
- **Cross-ref:** `plans/v5.15-live-readiness/subplans/2026-05-13-v5.15.5.F.4-universal-cfg-registry-sprint.md` (Phase 2 mentioned in Future Work); `plans/_future/2026-05-12-decoupling-endgoal-roadmap.md` (v6.0 alignment).

### TECH_DEBT-054 — Regime + risk-mode + feature categorical rollout deferred to v5.16+

- **Created:** 2026-05-14 by v5.15.5.F.4 planning
- **Severity:** LOW (operator-visible — additional category dimensions provide finer-grained UX filtering)
- **Surface:** CfgFieldDescriptor's `applies_to_regime_cat` / `applies_to_risk_cat` columns (defaulted to `_CAT_ALL` at v5.15.5.F.4); FOREACH_REGIME + FOREACH_RISK_MODE registries; FOREACH_FEATURE for feature categorical
- **What's deferred:** populate regime + risk-mode + feature category masks for relevant cfg fields. Currently descriptor has columns; v5.15.5.F.4 only populates strategy + op_mode dimensions; remaining dimensions use `_CAT_ALL` placeholder.
- **Why deferred:** v5.15.5.F.4 caps scope at strategy + op_mode categorical (2 dimensions). Additional dimensions are extension of the locked design per CLAUDE.local.md "design upfront + ship in waves." Each dimension = audit pass + populate masks; no descriptor changes.
- **Cost estimate:** ~2-3h per dimension; 3 dimensions = ~6-9h total. Plus FOREACH_FEATURE rework with category column for feature dimension.
- **Trigger:** (a) operator complains about UX filtering granularity; (b) v5.16 sprint focused on categorical dimension extension; (c) regime-aware ML feature subset selection needs the categorical surface.
- **Status:** OPEN
- **Cross-ref:** `DESIGN_SPECS/categorical-tag-applicability-pattern.md` § "Future application catalog"; `plans/v5.15-live-readiness/subplans/2026-05-14-v5.15.5.F.4h-strategy-category-audit-and-bitmap-overflow-audit.md` (strategy audit shipped at .F.4h; regime/risk audits are the analog).

### TECH_DEBT-055 — ResolvedCoreCfg AVX-512 batch-load + prefetch + delta-cache deferred to v5.16+

- **Created:** 2026-05-14 by v5.15.5.F.4 planning (.F.4e ship logs these as Future Work paths)
- **Severity:** LOW (performance optimization stack on top of `.F.4e` resolution cache substrate; activation deferred until measurement shows need)
- **Surface:** `CoreFrameworks/ResolvedCoreCfg.hpp` (struct shipped at .F.4e; sized to 3 × 64 byte cache lines for AVX-512 readiness)
- **What's deferred:** 3 future optimization paths on top of the .F.4e substrate:
  1. **Prefetch** — `__builtin_prefetch(&cfg->per_core_overrides[core_idx])` at slow-path entry (hides L2→L1 latency; ~10ns/cycle/core savings; 1 LOC)
  2. **AVX-512 batch-load** — 3 cache lines × `_mm512_load_pd` = 3 uops vs ~24 scalar loads (~30ns/cycle/core savings; requires AVX-512 CPU support; bytewise determinism preservation per CLAUDE.md item 25)
  3. **Epoch-compare delta-cache** — skip resolution if cfg.epoch + override_set_mask unchanged since last cycle (~60-cycle savings per cycle when cfg stable; epoch tracking required)
- **Why deferred:** v5.15.5.F.4 ships the resolution cache substrate at `.F.4e`; 100-400 ns/cycle warm savings is the primary win. Optimization paths above are stacked wins for when latency budget tightens. Not load-bearing at current operator cadence.
- **Cost estimate:** ~30 min for prefetch; ~2-3h for AVX-512 batch-load (CPU support check + intrinsic discipline + bytewise determinism test); ~1-2h for delta-cache (epoch tracking + invalidation logic).
- **Trigger:** (a) slow-path p99 latency regression or budget tightening; (b) profile shows resolution body in top 3 slow-path hot spots; (c) AVX-512 deployment broadens.
- **Status:** OPEN
- **Cross-ref:** `DESIGN_SPECS/slow-path-cfg-resolution-cache-pattern.md` § "Future work"; `DESIGN_SPECS/avx512-byte-determinism-pattern.md` (CLAUDE.md item 25); `DOCS/HOT_PATH_CHANGELOG.md` (.F.4e entry logs these optimization paths with cost analysis).

### TECH_DEBT-056 — Codebase-wide bitpacking + branchless API audit (Caramel's later-review sweep)

- **Created:** 2026-05-14 by v5.15.5.F.4d planning (Caramel's explicit ask post-Option-D-locked)
- **Severity:** LOW (hygiene; not blocking; DOD discipline reinforcement)
- **Surface:** entire codebase — any struct with ≥2 adjacent `uint8_t state_<N>` fields (where each represents enum ≤4 values); any dispatch endpoint using `if (override.X) { use override } else { use default }` shape instead of branchless mask compute
- **What's deferred:** AFTER most v5.15.5.F.4 frameworks land (.F.4d + .F.4e shipped), Caramel will personally review a codebase-wide sweep flagging:
  1. **Bitpacking candidates:** structs with adjacent `uint8_t state_<N>` fields representing small enums (~4 values each) → consolidate into single byte/word with bit-accessor helpers per `multi-bit-state-encoding-pattern.md` (CLAUDE.md item 30) + `bitmap-flag-api.md`. Anti-pattern detection signature added to `/dod-audit` Stage 6 at v5.15.5.F.4d ship.
  2. **Branchless API endpoints:** dispatch points using `if`-chain selection where branchless mask compute would have equivalent runtime cost AND be more DOD-aligned (mask AND > switch on enum for "any of these states?" queries; mask-mux > if-else for binary selection). Per DESIGN_PHILOSOPHY § 4 "Branchless mask compute for data-dependent dispatch" bullet (added 2026-05-14).
- **Why deferred (not effort-avoidance):** Caramel's explicit framing — "once most of the frameworks are done, I'll look at this." The .F.4d ship establishes the discipline (.F.4d-specific structs are bit-packed + branchless from day 1); this entry tracks the SWEEP of EXISTING codebase structs to apply the same discipline retroactively where the cost-benefit favors it.
- **Cost estimate:** ~3-4h for codebase sweep (scan all struct definitions; identify candidates; prioritize by frequency-of-access × LOC-savings). Per-candidate refactor: ~30-60 min including accessor migration + test verification. Probably 5-15 candidates worth migrating; ~4-8h total refactor work across the sweep.
- **Trigger:** **AFTER .F.4d + .F.4e ship + frameworks validated.** Caramel personally reviews + selects which candidates to migrate. Not auto-fire; operator-gated.
- **Status:** OPEN
- **Cross-ref:** `DESIGN_SPECS/multi-bit-state-encoding-pattern.md` (CLAUDE.md item 30; INVARIANT STATUS after 3rd canonical application at .F.4d); `DESIGN_SPECS/bitmap-flag-api.md`; `DOCS/DESIGN_PHILOSOPHY.md` § 4 (bit-packing-for-state-fields bullet added 2026-05-14); `/dod-audit` skill Stage 6 detection signature.

### TECH_DEBT-057 — Migrate ~15 unmigrated registries to FOREACH_REGISTRY meta-registry

- **Created:** 2026-05-14 by v5.15.5.F.4d planning
- **Severity:** LOW (each migration is a 1-line PR; primarily discoverability + CI cross-check benefit)
- **Surface:** ~15 X-macro registries that aren't yet declared in `CoreFrameworks/RegistryRoster.hpp` `FOREACH_REGISTRY` at .F.4d initial ship. Examples: FOREACH_SHALT, FOREACH_DEGRADATION_CURVE, FOREACH_BANDIT_ALGORITHM, FOREACH_BARRIER_BLEND_MODE, FOREACH_SLOW_PATH_GATE, 5 FOREACH_*_CFG_FLAG bitmap registries, FOREACH_CFG_DERIVED_INFERENCE_CFG, FOREACH_STAMP_BOUND_MODEL_CONST_PRE_CFG/_POST_CFG, FOREACH_FEATURE, FOREACH_REGIME, etc.
- **What's deferred:** add a row in `FOREACH_REGISTRY` for each currently-undeclared registry. Each row encodes: NAME, source_file, LEVEL (0=concrete), PARENT (ROOT or meta-registry name), design_spec ref, bug_class (if applicable), wire_format_kind (NOT_WIRE / WIRE_FORMAT / WIRE_FORMAT_TWO_SOURCE / MIXED), doc. Per `DESIGN_SPECS/meta-registry-pattern-for-codebase-registry-discipline.md`.
- **Why deferred (not effort-avoidance):** .F.4d initial ship populates the FOREACH_REGISTRY with 10-15 most-load-bearing entries (CFG_FIELD, DERIVED_FILTER, STRATEGY, FEATURE, FAILURE_MODE, CFG_DRIFT_CHECK, ARCH_FIELD_DRIFT, ML_CFG_FLAG, etc.). Remaining registries get rows added as time allows; each is mechanical (~5 min per row). Per H14 (pending invariant): every X-macro registry MUST eventually be in FOREACH_REGISTRY; CI test enforces.
- **Cost estimate:** ~5 min per registry × 15 registries = ~75 min total. Best done as a single cleanup pass.
- **Trigger:** (a) batch addition opportunity during quiet period between sub-ships; (b) CI test added at .F.4d ship may flag undeclared registries as build warning → motivates migration; (c) `/precoding-audit-gate` auto-derivation accuracy improves with more roster coverage.
- **Status:** OPEN
- **Cross-ref:** `DESIGN_SPECS/meta-registry-pattern-for-codebase-registry-discipline.md` (DRAFT v1.0 at .F.4d); H14 invariant (pending codification at .F.4d ship); `CoreFrameworks/RegistryRoster.hpp` (created at .F.4d).

### TECH_DEBT-058 — REGISTRY_TOPOLOGY.md auto-generation Python script

- **Created:** 2026-05-14 by v5.15.5.F.4d planning
- **Severity:** LOW (manual REGISTRY_TOPOLOGY.md ships at .F.4d; auto-gen is hygiene improvement)
- **Surface:** new file `tools/generate_registry_topology.py` (~50 LOC Python script that parses `CoreFrameworks/RegistryRoster.hpp` `FOREACH_REGISTRY` entries + emits ASCII tree visualization to `workspace/DOCS/REGISTRY_TOPOLOGY.md`)
- **What's deferred:** auto-generation of `REGISTRY_TOPOLOGY.md` from the FOREACH_REGISTRY data. Manual version ships at .F.4d (hand-written ASCII tree); auto-gen converts that to a CI-checked derived artifact (regenerate on every registry change + diff against committed version to ensure freshness).
- **Why deferred:** Manual REGISTRY_TOPOLOGY.md at .F.4d is sufficient for immediate cold-pickup needs (20-25 entries; hand-curatable). Auto-gen pays off once entries grow + manual maintenance drift risks setting in. Scaffolding for the auto-gen pattern at v5.15.6+ when 2nd derived-doc surface (e.g., cfg-by-metadata.md from .F.4e) makes generator generalization worthwhile.
- **Cost estimate:** ~1-2h (Python script + CI integration + test against current FOREACH_REGISTRY content; treat as derived artifact).
- **Trigger:** (a) FOREACH_REGISTRY entry count grows past ~25; (b) manual REGISTRY_TOPOLOGY.md drifts from FOREACH_REGISTRY content; (c) v5.15.6 introduces second derived-doc surface (cfg-by-metadata.md) — generalize the auto-gen pattern.
- **Status:** OPEN
- **Cross-ref:** `DESIGN_SPECS/meta-registry-pattern-for-codebase-registry-discipline.md`; sister to TECH_DEBT-057 (rate-limiting factor: FOREACH_REGISTRY coverage); `tools/` directory (sibling Python derived-doc tools).

### TECH_DEBT-059 — stamp-vs-runtime-drift-detection-registry.md wide variant DEPRECATION (post-.F.4d ship)

- **Created:** 2026-05-14 by v5.15.5.F.4d planning
- **Severity:** LOW (DESIGN_SPEC update; documents the pattern's evolution post-.F.4d superseding by sidecar pattern)
- **Surface:** `workspace/DESIGN_SPECS/stamp-vs-runtime-drift-detection-registry.md` § "Wide variant (FOREACH_CFG_DRIFT_CHECK — 10-col tuple, multi-axis Y3, ack-aware)"
- **What's deferred:** mark the WIDE variant as DEPRECATED-FOR-CFG-DRIFT in the DESIGN_SPEC. Replaced by `DESIGN_SPECS/sidecar-override-pattern-for-registry-auto-flows.md` (NEW at .F.4d). Narrow variant (FOREACH_ARCH_FIELD_DRIFT) stays — different surface; not over cfg fields. Wide variant pattern itself remains valid for OTHER non-cfg drift surfaces; only the cfg-drift application supersedes.
- **Why deferred (until .F.4d ships):** Wide variant currently has 1 production application (`CfgDriftCheckRegistry.hpp` 19-entry registry). .F.4d ship retires it (auto-flow via CFG_DRIFT_AUTOPOPULATE + 5-entry FOREACH_DRIFT_OVERRIDE sidecar). After .F.4d ships, update the wide-variant section to add DEPRECATION notice + cross-ref to sidecar pattern.
- **Cost estimate:** ~15 min (light edit to wide-variant section header + Cross-references update + DESIGN_SPECS/README.md catalog status update).
- **Trigger:** **AFTER .F.4d ships** + CfgDriftCheckRegistry deletion verified.
- **Status:** OPEN (blocked on .F.4d ship)
- **Cross-ref:** `DESIGN_SPECS/sidecar-override-pattern-for-registry-auto-flows.md` (supersedes for cfg-drift surface); `DESIGN_SPECS/stamp-vs-runtime-drift-detection-registry.md` (wide variant section); H17 invariant (pending codification at .F.4d ship).

### TECH_DEBT-063 — SettingsPanel.hpp `field_defs[]` full elimination (in-progress)

- **Created:** 2026-05-14 by v5.15.5.F.4c session (operator UX considerations conversation)
- **Severity:** LOW (each removal is mechanical; cumulative impact is significant GUI bloat reduction)
- **Surface:** `GUI/SettingsPanel.hpp` lines 48-274 — currently ~213 entries hand-maintained in `field_defs[]` array; `.F.4a/.F.4b` removed ~40 (KIND_DOUBLE/_PCT cohort migrated to FOREACH_CFG_FIELD); `.F.4c` removes ~50-60 (INT/INT_ENUM/BOOL cohort); `.F.4e` removes the remaining ~110 (STRING/FILE_PATH cohort).
- **What's deferred:** as each cohort migrates to `FOREACH_CFG_FIELD`, the corresponding `field_defs[]` entries delete (Step 4 of each migration ship). Target: `field_defs[]` = 0 entries post-`.F.4e`; entire array + supporting `CfgFieldDef` struct + manual render loop deleted; replaced by `FOREACH_CFG_FIELD` walker via `tt::cfg_render_field<T>` dispatch.
- **Why deferred (not effort-avoidance):** sequencing is forced — `field_defs[]` entry deletion happens IN the same ship that migrates the corresponding field to `FOREACH_CFG_FIELD`. Not a separate effort; embedded in cohort migration work.
- **Cost estimate:** ~5 min per cohort batch (mechanical deletion in Step 4 of each ship).
- **Trigger:** progresses with `.F.4c`/`.F.4e` migration cohorts. Verified zero at `.F.4e` ship via test: `static_assert(sizeof(field_defs) == 0)` or `field_defs` declaration deletion + grep verification.
- **Status:** IN PROGRESS — `.F.4a` removed initial ~40 (KIND_DOUBLE/_PCT cohort); `.F.4c` in flight will remove ~50-60 more (KIND_INT/_ENUM/_BOOL scalar Kinds via bitmap-dispatch walker replacing parallel-array indirection — see `.F.4c` plan body amendment + DESIGN_SPECS/universal-registry-bitmap-dispatcher-pattern.md); `.F.4e` removes the remaining ~110 (KIND_STRING/_FILE_PATH). After `.F.4e` ships: field_defs[] = 0; `CfgFieldDef` struct + manual render loop + parallel-array layer all delete; SettingsState shrinks to model-scan + per-core override structures only.
- **Cross-ref:** sister to `.F.4c` (KIND_INT/_ENUM/_BOOL migration; bitmap-dispatch walker replaces field_defs[] auto-extender for scalar Kinds); `.F.4e` (KIND_STRING/_FILE_PATH migration; final field_defs[] elimination); `DESIGN_SPECS/universal-registry-bitmap-dispatcher-pattern.md` (codifies the dispatcher pattern; first canonical application at `.F.4c`); `plans/_future/2026-05-14-headless-first-orientation.md` (deferred option).

### TECH_DEBT-064 — Headless operation option (deferred 2026-05-14 — considered, GUI stays primary for now)

- **Created:** 2026-05-14 by v5.15.5.F.4c session — Caramel considered prioritizing headless operation; decided GUI remains primary for now; metadata-bit hooks (TECH_DEBT-066, 067) kept as future optionality.
- **Severity:** LOW (deferral doc; captures option not commitment)
- **Surface:** `engine` binary (existing ANSI TUI) + future CLI subcommands (TECH_DEBT-066) + structured log output (TECH_DEBT-065/067)
- **What's deferred:** the strategic pivot to headless-first. Considered + deferred. The `engine` binary already builds without SDL/OpenGL/ImGui (no rewrite required); pivot would be promoting it to primary entry point + freezing GUI feature additions. NOT decided.
- **Why deferred:** Caramel preference noted (`tail -f` + CLI workflow appealing) but `tail -f` workflow hasn't been validated against actual operator use. GUI is currently working + maintained; pivot risks unwinding correct work for an unvalidated direction. Revisit when (a) `tail -f` workflow gets dogfooded, OR (b) `.F.4` closes + frameworks are mature enough to make CLI subcommands cheap, OR (c) operator explicitly says "yes, pivot."
- **Cost estimate:** ZERO implementation cost (this entry is the deferral itself; actual pivot is a future strategic decision).
- **Trigger:** operator decision — not auto-fire. Re-evaluate at end of `.F.4` umbrella close OR when GUI maintenance burden becomes blocking.
- **Status:** OPEN (option preserved; not committed)
- **Cross-ref:** TECH_DEBT-063 / 065 / 066 / 067 (related future-optionality entries); `plans/_future/2026-05-14-headless-first-orientation.md` (aspirational roadmap; revisit if/when pivot decision made).

### TECH_DEBT-065 — JSON-structured log format for engine status snapshots

- **Created:** 2026-05-14 by v5.15.5.F.4c session (operator UX considerations conversation)
- **Severity:** LOW-MEDIUM (foundational headless observability feature)
- **Surface:** NEW header `MemHeaders/StructuredLog.hpp` + integration with existing `health_log_path` machinery; per-core slow_state walker emits structured snapshots at configured cadence
- **What's deferred:**
  - Per-N-tick (configurable; e.g., `snapshot_log_interval_ticks=1024`) OR per-N-second (`snapshot_log_interval_ms=1000`) JSON-formatted log line emit
  - One line per slow-path cycle per core: `{ts, core_id, regime, position_qty, position_pnl, slow_path_us_p99, hot_path_ns_p99, fills_this_cycle, ...}`
  - Hot path sampled (1 in N ticks) for latency trend tracking without per-tick overhead
  - Drainer + producer global cadence (per-second)
  - `tail -f logging/structured.json | jq` becomes canonical operator workflow
  - Header includes simple JSON-emit helper (locale-pinned per `wire-format-byte-preservation-discipline.md` Layer 2; no scientific notation; integer-formatted where possible)
- **Why deferred:** requires (1) per-core slow_state walker (separate ship from cfg field walker); (2) `.F.4` umbrella closure for single source of truth on cfg fields used in emit; (3) cadence cfg fields landing first (covered in `.F.4c`).
- **Cost estimate:** ~3-5 sprint days. New `StructuredLog.hpp` (~150 LOC) + per-core emit hook in slow-path body (~30 LOC) + cadence cfg fields (3-5 rows) + tests + paper-test verification of operator workflow.
- **Trigger:** **AFTER `.F.4` umbrella closes** + `.F.4e` CLI infrastructure ships. Becomes its own sub-ship `v5.15.5.G.1` or sibling.
- **Status:** OPEN (future sprint)
- **Cross-ref:** TECH_DEBT-066 (CLI subcommands consume same per-core snapshot machinery); TECH_DEBT-067 (per-core + per-path observability builds on this); `plans/_future/2026-05-14-headless-first-orientation.md` (deferred option).

### TECH_DEBT-066 — `engine` CLI subcommands for headless operator workflow

- **Created:** 2026-05-14 by v5.15.5.F.4c session (operator UX considerations conversation)
- **Severity:** HIGH (load-bearing for headless transition; replaces `.F.4e`'s original "5 GUI metadata bits" scope)
- **Surface:** NEW `engine` main() argument dispatch + 4-6 CLI subcommand handlers; consume derived filters from `.F.4d` framework
- **What's deferred:**
  - `engine --explain-cfg <key>` — walks `FOREACH_CFG_FIELD`, prints field's kind, clamp range, applicability (strategy/op_mode/regime/risk), tooltip, deprecation status, side-effect status, current cfg-file value vs default
  - `engine --list-cfg [--filter=<category>] [--changed-only]` — list all cfg fields (optionally filtered by category, or only fields with non-default values)
  - `engine --validate-cfg [--report]` — boot-style validation pass against cfg file; emit pass/fail per field + warnings + summary; exit code reflects validation result
  - `engine --status --json` — once-and-exit JSON snapshot (P&L, positions, regime per core, latency p99 per path); operator scripts consume for monitoring
  - `engine --kill-switch on|off` — operator-friendly kill switch toggle (writes to cfg + signals running engine if applicable)
  - `engine --version` (likely already exists; verify at scope)
- **Why deferred:** requires `.F.4d` derived-filter framework (consumed by `--list-cfg --filter=<category>` + `--validate-cfg`) + metadata bits (`DEPRECATED` / `BOOT_ONLY` / `HAS_SIDE_EFFECT` / `WARN_ON_CLAMP` / `RESTART_REQUIRED` / `IS_SECRET` / `SAFETY_CRITICAL`) defined at `.F.4c`/`.F.4d`.
- **Cost estimate:** ~3-5 days. Argument parsing (basic argv per codebase no-deps style) + 4-6 subcommand implementations + JSON emit + tests + headless paper-test verification.
- **Trigger:** ship target unset — could ship at `.F.4e` IF/WHEN headless pivot approved (currently deferred per TECH_DEBT-064). Future strategic decision; depends on operator validation of `tail -f` workflow + GUI maintenance burden.
- **Status:** OPEN (future-optionality; not committed)
- **Cross-ref:** TECH_DEBT-064 (parent deferral decision); TECH_DEBT-065 (structured log infrastructure); `plans/_future/2026-05-14-headless-first-orientation.md` (deferred option); `.F.4d` derived filter framework (would be consumed if/when headless pivot approved).

### TECH_DEBT-067 — Per-core + per-path structured log emit (TUI + log granularity)

- **Created:** 2026-05-14 by v5.15.5.F.4c session (operator UX considerations conversation) (Caramel's explicit Q2)
- **Severity:** MEDIUM (operator observability granularity for production debugging)
- **Surface:** Per-core slow_state walker + ANSI TUI per-core row stack (DataStream/EngineTUI.hpp) + per-path log emit (hot/slow/drainer/producer)
- **What's deferred:**
  - **Per-core JSON log line** on each slow-path rebuild per core: `{ts, core_id, path=slow, regime, position_qty, position_pnl, slow_path_us, fills_this_cycle, ...}`
  - **Hot-path sampled emit** (1-per-second or 1-per-1024-ticks) per core: `{ts, core_id, path=hot, hot_p99_ns, hot_max_ns, dispatch_count, ...}`. Cadence configurable.
  - **Drainer/producer global emit** per-second: `{ts, path=drainer, drain_lat_p99_us, submitted, filled, rejected, ...}` and `{ts, path=producer, tick_rate_per_sec, ws_lag_ms, ...}`
  - **ANSI TUI enhancement** (`EngineTUI.hpp`): per-core stacked row layout with `[core 0] BTCUSDT  TRENDING  pos=+0.05  pnl=+$12.34  slow_p99=42us  hot_p99=180ns`
  - **`tail -f logging/structured.json | jq 'select(.core_id==3)'`** per-core filtering workflow
  - **`tail -f | jq 'select(.path=="hot")'`** per-path filtering workflow
- **Why deferred:** builds on TECH_DEBT-065 (`StructuredLog.hpp` infrastructure) + `.F.4` umbrella closure (single source of truth for cfg + per-core state structures). Significant scope; dedicated sub-sprint.
- **Cost estimate:** ~1-2 weeks. Per-core slow_state walker (~80 LOC) + per-path log emit hooks (~50 LOC) + TUI enhancement (~150 LOC) + cfg fields for cadence (3-5 rows) + tests + paper-test verification of operator workflow.
- **Trigger:** **AFTER TECH_DEBT-065 ships + `.F.4` umbrella closes + `.F.4e` CLI infrastructure lands.** Likely v5.15.5.G.2 or similar sub-sprint.
- **Status:** OPEN (future sprint after `.F.4` closure)
- **Cross-ref:** TECH_DEBT-065 (depends on `StructuredLog.hpp` foundation); TECH_DEBT-066 (CLI `--status --json` consumes same per-core walker); `plans/_future/2026-05-14-headless-first-orientation.md` (deferred option); sister to existing `LatencyHistogram` (provides per-path p99 data consumed by emit) + `OrderEventLog` (per-event log; sister channel).

### TECH_DEBT-068 — ML-side enum X-macro registries (ml_backend / regime_model_backend / confidence_ic_variant / csv_sort_check_mode / reconcile_mode / ensemble_blend_mode)

- **Created:** 2026-05-14 by v5.15.5.F.4c session (cfg field audit identified these as currently-open-ended ints; operator flagged as important follow-up)
- **Severity:** MEDIUM (operator-UX quality; not blocking; enables INT_ENUM promotion + warn-on-invalid + label-token parsing)
- **Surface:** create X-macro registries with `_FromString` / `_ToString` / `<NAME>_LABELS[]` per `BanditAlgorithmRegistry.hpp` / `BarrierBlendModeRegistry.hpp` / `ConfidenceScore.hpp::FOREACH_DEGRADATION_CURVE` precedent:
  - **`ml_backend`** — XGBoost / ONNX / AOT-compiled / etc. Currently parsed as plain int. New `FOREACH_ML_BACKEND` registry in `ML_Headers/ModelInference.hpp` or sibling.
  - **`regime_model_backend`** — same family; possibly shares ML_BACKEND registry depending on storage.
  - **`confidence_ic_variant`** — IC variant selection (Pearson / Spearman / rank-IC / etc.); currently plain int.
  - **`csv_sort_check_mode`** — STRICT / LENIENT / DISABLED training-time gate; currently plain int.
  - **`reconcile_mode`** — reconciliation strategy (full / incremental / verify-only); currently plain int.
  - **`ensemble_blend_mode`** — model blend strategy (avg / weighted / vote / etc.); currently plain int.
- **What's deferred:** create the X-macro registries with the canonical 5-component shape (`FOREACH_<NAME>` + `<NAME>_FromString` + `<NAME>_ToString` + `<NAME>_LABELS[]` + `<NAME>_COUNT`). At `.F.4c` migration these fields land as **plain KIND_INT** rows in `FOREACH_CFG_FIELD`. Once registries exist (this TECH_DEBT closes), promotion is a single-row change: KIND_INT → KIND_INT_ENUM + payload macro `INT_ENUM(default_val, count, labels)` referencing the extern labels array.
- **Why deferred (not effort-avoidance):** registries are non-trivial design work (each enum needs operator-meaningful name + semantic doc + numeric value lock for back-compat). Doing them mid-`.F.4c` would balloon scope. Cohort migration approach: ship `.F.4c` with KIND_INT for these 6, then dedicated follow-up ship creates the 6 registries + promotes the rows.
- **Cost estimate:** ~2-3 hr per registry × 6 = ~12-18 hr total. Each registry: ~50-80 LOC (X-macro definition + FromString helper + ToString helper + LABELS extern + COUNT + tests). Plus single-line `.F.4c` row updates to KIND_INT_ENUM + add labels reference.
- **Trigger:** **AFTER `.F.4` umbrella closes** (single-source-of-truth for cfg established) OR earlier if a specific enum needs the FromString helper for operator-UX (e.g., `ml_backend=XGBOOST` text input fails today due to atoi-only parse). Operator-priority decision.
- **Status:** OPEN (high-quality optionality; aligns with `BanditAlgorithm` / `BarrierBlendMode` / `DegradationCurve` existing pattern)
- **Cross-ref:** `Strategies/BanditAlgorithmRegistry.hpp` / `Strategies/BarrierBlendModeRegistry.hpp` / `ML_Headers/ConfidenceScore.hpp::FOREACH_DEGRADATION_CURVE` (canonical precedent); `DESIGN_SPECS/x-macro-registry-with-presence-dispatch.md`; `.F.4c` Step 2 KIND_INT_ENUM section (these rows ship as KIND_INT pending registry creation); `DESIGN_SPECS/universal-registry-bitmap-dispatcher-pattern.md` (the bitmap dispatcher framework landed at `.F.4c` applies to these registries once they exist — adds per-bit/per-enum-value filtering + popcount stats + branchless iteration; below ~10 entries the framework overhead may not amortize → judgment per registry).

### TECH_DEBT-069 — Codebase-wide registry-table `static const` → `inline constexpr` promotion sweep

- **Created:** 2026-05-14 by v5.15.5.F.4c session (`g_cfg_field_descriptors[]` constexpr promotion at `.F.4c` validated the pattern; sweep extends to peer registries)
- **Severity:** LOW (mechanical optimization; not blocking; quality-of-implementation)
- **Surface:** ~6-8 registry tables across `CoreFrameworks/` + `MemHeaders/` + `ML_Headers/`:
  - `MemHeaders/OmsStateFlagRegistry.hpp::g_oms_state_flag_descriptors[]`
  - `MemHeaders/FailureModeRegistry.hpp::g_failure_mode_table[]`
  - `ML_Headers/BanditAlgorithmRegistry.hpp` derivations (mostly constexpr already; verify)
  - `ML_Headers/BarrierBlendModeRegistry.hpp` derivations (mostly constexpr already; verify)
  - `ML_Headers/ConfidenceScore.hpp::FOREACH_DEGRADATION_CURVE` tables (verify per-table)
  - 5 `FOREACH_*_CFG_FLAG` bitmap registry tables (mostly constexpr via X-macro; verify)
  - Other singleton registry data tables surfaced during audit
- **What's deferred:** sweep each registry table; if all members are trivially constexpr-init (no runtime-only construction, no mutation post-init), promote `static const` / `inline const` → `inline constexpr`. Verify nothing breaks (constexpr is stricter; some hidden runtime dependencies may surface). Place each promoted table in `.rodata` (truly read-only; OS-enforced).
- **Why deferred (not effort-avoidance):** these tables work as-is; the promotion is mechanical optimization (slightly smaller binary footprint via `.rodata` consolidation; enables downstream constexpr computations for future framework consumers). Not blocking any current feature. Best done as a single focused sweep rather than scattered across feature sprints.
- **Cost estimate:** ~5 min per table × 6-8 tables = ~30-45 min total + ~30 min for build/test verification per table change. Total ~3-4h focused effort.
- **Trigger:** **near end of v5.15.5.F umbrella** (per operator direction 2026-05-14 — "do the sweep for constexpr sites for like the end of 5.15.5.F"). Specifically: after `.F.4` umbrella closes + `.F.5` per-core Thompson audit ships; before v5.15 umbrella closure. Dedicated focused-effort window; not interleaved with feature work. Could fire as `v5.15.5.F.6` sub-ship.
- **Status:** OPEN
- **Cross-ref:** `CoreFrameworks/CfgFieldRegistry.hpp::g_cfg_field_descriptors[]` (canonical precedent — promoted to `inline constexpr` at `.F.4c`); enables downstream constexpr mask computations via `cfg_compute_mask<Bit>()`.

### TECH_DEBT-070 — Compile-time SubmitCommand required-field enforcement (C++17 friend-scope wall)

- **Created:** 2026-05-15 by v5.15.5.F.4c.3 WIP2d-1.B.1 (option-A `private` default ctor + `friend` access for known producers failed under C++17 friend-scope rules at controller_test scope).
- **Severity:** LOW (current runtime guard works; structural enforcement is "better discipline" not "fixes broken behavior").
- **Surface:** `CoreFrameworks/SubmitCommand.hpp` POD struct + required-field ctor `SubmitCommand(core_id, order_type, qty, intended_price, fee_rate, ...)`. Today: BOTH the default ctor (for SPSC ring slot init) AND the required-field ctor are `public`; the default ctor is named `SubmitCommand{}` and produces a zero-init slot. A caller that forgets to overwrite fields before push silently sends a zero-init command. Runtime guard: ShardedLiveSafety_PreSubmitGate validates per-field non-zero invariants and rejects malformed commands; the rejection logs filename+line.
- **What's deferred:** under C++20, use `concept`-constrained ctors + designated-init compile-time enforcement to make "constructed without all required fields = compile error." The C++17 friend-scope attempt hit a wall: making the default ctor `private` + friending the canonical producer fns (`OMS_DrainSubmit`, `Reconcile_ApplyMissedFills`, backtest seed paths) broke `controller_test.cpp` test fixtures that aggregate-init via `SubmitCommand cmd{}; cmd.core_id = 0; cmd.order_type = ...`. C++17 disallows friend access in aggregate init contexts; refactoring the ~21 test fixtures to use the required-field ctor was viable but the friend declaration list itself drifts (every new producer fn needs adding to the friend list at the SubmitCommand definition site — Class 18 mirror-incomplete risk).
- **Why deferred (not effort-avoidance):** C++17 cannot express "required field at construction" cleanly. C++20 `concepts` + designated init + `[[nodiscard]]` ctors give a clean path. Until C++20 upgrade (TECH_DEBT-073), the runtime guard at ShardedLiveSafety_PreSubmitGate is the discipline anchor. Operator visibility: a malformed-cmd log line = "someone forgot to fill a SubmitCommand field"; same diagnostic surface as compile-time error, just slower feedback loop.
- **Cost estimate:** ~3-4h after C++20 upgrade lands. Refactor: (1) define `Submittable` concept requiring all required fields, (2) change required-field ctor to `requires Submittable<...>`, (3) update ~21 test fixtures to use the required-field ctor consistently, (4) delete default ctor or mark `= delete`, (5) verify SPSC ring slot init still works (likely via `std::array<SubmitCommand, N>{}` with `noinit` policy or explicit `slot.reset()` calls).
- **Trigger:** **after C++20 upgrade ships** (TECH_DEBT-073). Not before; the discipline is C++20-dependent.
- **Status:** OPEN (waiting on C++20 upgrade)
- **Cross-ref:** `CoreFrameworks/SubmitCommand.hpp` (POD definition + dual ctor); `CoreFrameworks/ShardedLiveSafety.hpp::ShardedLiveSafety_PreSubmitGate` (runtime guard); TECH_DEBT-073 (C++20 upgrade); `DESIGN_SPECS/cfg-scope-discipline.md` § "Consumer function signatures over per-core slices" (sibling discipline at the cfg layer); `DESIGN_PHILOSOPHY.md` § 8 Failure observability — runtime guards as the C++17-compatible expression of compile-time-preferred invariants.

### TECH_DEBT-071 — Portfolio_OpenSlot / CloseSlot + TradeLog_Record* mask-param refactor (Pattern 5 alternative)

- **Created:** 2026-05-15 by v5.15.5.F.4c.3 WIP2d-1.B.1 (during architectural decision for trade_log + calibration_log emit branch elimination; option B "mask params at call sites" considered but rejected in favor of option C "Pattern 5 sink-fn-pointer").
- **Severity:** LOW (Pattern 5 sink-fn-pointer is already deployed; this is an alternative shape to evaluate post-paper-test).
- **Surface:** `CoreFrameworks/Portfolio.hpp::Portfolio_OpenSlot / Portfolio_CloseSlot` + `CoreFrameworks/TradeLog.hpp::TradeLog_RecordEntry / TradeLog_RecordExit`. Today: Pattern 5 sink-fn-pointer dispatches via `on_entry_fill_emit / on_exit_fill_emit / on_exit_calibration` fn-pointer fields in OmsState, with `noop_fill_emit` as default and `real_*` attached at boot when log paths are configured.
- **What's deferred:** alternative shape — pass a "did this fill open/close a slot" mask BACK from Portfolio_OpenSlot/CloseSlot to the caller, and have the caller branchless-dispatch via mask AND'd against `trade_log_enabled` + `calibration_log_enabled` bitmap fields. Both Pattern 5 and mask-param eliminate the per-fill `if (sink_attached)` branch; mask-param keeps the call-graph flatter (no fn-pointer indirection at the per-fill site) at the cost of widening Portfolio_OpenSlot/CloseSlot signatures and threading mask-flag bookkeeping through HandleFill.
- **Why deferred:** Pattern 5 was chosen at .F.4c.3 because it composes cleanly with the "subsystem state owns its own dispatch policy" principle (OmsState owns its own emit fn-pointers; Portfolio/TradeLog stay narrow). Mask-param would invert that — Portfolio would emit "I opened slot S" bits and the caller would do the multiplexing. Pattern 5 reads cleaner; mask-param may benchmark faster (one less L1d indirect-call line). Without benchmark data we picked the cleaner-reading option; defer the eval until paper-test or live-readiness profiling provides a measurement.
- **Cost estimate:** ~6-8h if pursued. Signature widening (~10 callsites for Portfolio_OpenSlot/CloseSlot) + bitmap encoding for mask-return + ~3 paper-test fixtures to compare branchy vs Pattern 5 vs mask-param on real ticks.
- **Trigger:** **after paper-test data + live-readiness profile data exists** (paper-test session post-v5.15 close OR live-readiness ship). Pursue only if Pattern 5's L1d indirect-call cost shows up as a measurable per-fill penalty (>1% of slow-path budget); otherwise keep Pattern 5.
- **Status:** OPEN (evaluation; not actionable until measurement data exists)
- **Cross-ref:** `DESIGN_SPECS/sink-fn-pointer-for-optional-side-effect-pattern.md` (Pattern 5 canonical); `DESIGN_SPECS/branchless-dispatch-discipline.md` § Pattern 3 (mask-select sub-variants); `CoreFrameworks/OrderManager.hpp` (current Pattern 5 deployment); `DESIGN_PHILOSOPHY.md` § 4 Latency cost framework — when to choose fn-pointer vs mask-param.

### TECH_DEBT-072 — Reconcile_ApplyMissedFills exchange-fee-from-source corner case (fully-released Orders fall back to cores[0])

- **Created:** 2026-05-15 by v5.15.5.F.4c.3 WIP2d-1.B.1 (during Reconcile branchless bitmap-search closure; surfaced as a corner case the synth-binding can't fully resolve).
- **Severity:** MEDIUM (correctness; rare path — only fires when exchange reports a missed fill for an Order whose in-flight slot has been fully released before reconciliation runs).
- **Surface:** `CoreFrameworks/Reconcile.hpp::Reconcile_ApplyMissedFills`. Today's binding shape: when an exchange reports a missed fill, Reconcile searches the in-flight Order pool via bitmap match-mask + `__builtin_ctz` to find the originating core_id; the recovered core_id picks the right `cores[core_id]` slice for Order_BindPreResolved. If the original Order has been fully released (slot recycled), the bitmap-search returns no match. Current fallback: bind against `cores[0]` (default core) — fee_rate is `cores[0].fee_rate_taker`, which is correct ONLY if the originating core happened to be 0 OR all cores share the same fee schedule.
- **What's deferred:** preserve exchange's reported fee at source. When the exchange reports a missed fill, the fill message itself carries the realized fee (`exchange_fee_quote_amount`). Use THAT fee directly in the bound Order::pre_resolved.fee_rate instead of deriving from cfg. Two implementation paths:
  1. **Backwards-fee-derivation:** when exchange reports fee + notional, compute fee_rate = fee / notional + bind that into pre_resolved.fee_rate. Lossy if exchange reports rounded fees.
  2. **Direct exchange-fee field:** add `Order::pre_resolved.exchange_realized_fee` FPN<F> field; if set (non-zero), use it directly in AccountMakerTakerFee instead of `pre_resolved.fee_rate × notional`. Reconcile sets this field on synth Orders from exchange-reported fills; normal Drainfill paths leave it unset (and AccountMakerTakerFee falls back to the `pre_resolved.fee_rate × notional` path).
- **Why deferred:** rare path (Reconcile only fires on missed-fill reports during live trading; not during backtest or normal-flow paper trading). Current fallback (cores[0]) is correct when all cores share the same fee schedule (typical for single-symbol-per-core layout). Becomes a real bug when per-core fee schedules diverge — e.g., maker-only core vs taker-only core, or per-core VIP-tier overrides. Fix is straightforward (path 2 with exchange_realized_fee field) but requires Binance API audit to confirm fee-amount-in-fill is reliably reported (vs derivable-but-not-reported).
- **Cost estimate:** ~4-5h if path 2 chosen. Add field to Order::pre_resolved; update Reconcile synth to set it; update AccountMakerTakerFee mask-select to prefer exchange_realized_fee if set; ~3 controller_test fixtures for the synth path; ~1 paper-test session to verify the field propagates through live BinanceOrderAPI.
- **Trigger:** **before live trading enable** (live-readiness ship). Must close before any cfg path can enable per-core fee divergence (e.g., per-core `fee_rate_maker_override` flag landing as a `.F.5` capability).
- **Status:** OPEN (waiting on Binance API audit; must close pre-live)
- **Cross-ref:** `CoreFrameworks/Reconcile.hpp::Reconcile_ApplyMissedFills` (current bitmap-search + cores[0] fallback); `CoreFrameworks/Order.hpp::pre_resolved` sub-struct (the field would live here); `DataStream/BinanceOrderAPI.hpp` (audit source for exchange-reported fee format); `DESIGN_SPECS/cfg-scope-discipline.md` § "Recovery-path nullable pointer" (Reconcile's binding shape spec); Class 29 (the broader pre-resolution discipline that this corner case is the edge of).

### TECH_DEBT-073 — C++20 upgrade ship (post-v5.15 umbrella)

- **Created:** 2026-05-15 by v5.15.5.F.4c.3 WIP2d-1.B.1 (deferred C++17→C++20 upgrade after C++17 friend-scope wall on SubmitCommand option A; multiple downstream tech debt items depend on C++20 features).
- **Severity:** MEDIUM (infrastructure upgrade; unlocks several deferred items + new branchless patterns; not blocking immediate work but unlocks structural-enforcement options not expressible in C++17).
- **Surface:** entire codebase — build flags (`-std=c++20`), compiler version pin (gcc 12+), `<bit>` header replaces `__builtin_*` intrinsic usage, `[[likely]]`/`[[unlikely]]` annotations replace `__builtin_expect`, `concepts` enable compile-time required-field enforcement, designated-init for clearer struct construction, `<source_location>` for richer assert messages, `consteval` for compile-time-guaranteed evaluation (vs constexpr's "could be runtime"), 3-way comparison operator `<=>` for byte-equivalence contexts (H10/H12 sites).
- **What's deferred:** dedicated infrastructure ship that bumps `-std=c++17` → `-std=c++20` across all build flavors, audits and updates the codebase for new C++20 patterns where they unlock structural-enforcement options. NOT a "convert everything to C++20 idioms" sweep — only sites where C++20 enables a deferred discipline (TECH_DEBT-070 SubmitCommand required-field; future ML capability concepts; future strategy-interface concept-constrained dispatch). Other C++17 code stays as-is.
- **Why deferred (not effort-avoidance):** C++20 upgrade is genuinely a dedicated infrastructure ship — touches build flags, compiler dependency, all 6 build dirs (build/, build_gui/, build_suite/, build_lat/, build_tsan/, build_asan/), CI image, dev-machine compiler version. Cross-cutting; must be its own ship for proper rollback anchor. Several TECH_DEBT items (TECH_DEBT-070 SubmitCommand; future ML concepts) explicitly depend on C++20 features. Doing the upgrade ship FIRST unblocks 2-3 downstream items.
- **Cost estimate:** ~16-24h focused. Phase 1: build flag flip + per-build-dir verification (~4h). Phase 2: existing-code audit for C++17/C++20 incompatibilities (rare; standard library mostly forward-compat but some patterns shift) + fix any (~6h). Phase 3: opportunistic upgrades at sites where C++20 unlocks a deferred discipline (~6-10h, focused on TECH_DEBT-070 first canonical). Phase 4: test sweep + paper-test verification (~2-4h).
- **Trigger:** **after v5.15 umbrella closes** (sprint state confirmed; current sprint stays C++17). Dedicated infrastructure ship; should be its own version (e.g., `v5.16.0` or `v5.15.6.A` depending on umbrella sequencing). Operator decision on naming + timing.
- **Status:** OPEN (queued for post-v5.15 umbrella; sequenced after live-readiness operational items if those are higher priority)
- **Cross-ref:** TECH_DEBT-070 (SubmitCommand required-field enforcement; first canonical C++20 unlock); `CoreFrameworks/SubmitCommand.hpp` (target of first C++20-enabled refactor); `DESIGN_PHILOSOPHY.md` § 11 Process discipline (upgrade-as-dedicated-ship); CLAUDE.md "Build" section (build flag references); `build.sh` (C++ standard flag).

### TECH_DEBT-074 — Future `DOCS/DATA_FLOW.md` doc (proposed during .F.4c.4 planning; defer to post-v5.15 umbrella close)

- **Created:** 2026-05-16 by v5.15.5.F.4c.4 fresh-context audit session (Decision 13 in decisions-capture bridge doc — Caramel proposed function map / data flow graph during planning).
- **Severity:** LOW (documentation enhancement; operator onboarding + cold-pickup quality).
- **Surface:** workspace `DOCS/DATA_FLOW.md` (NEW; ~200-400 lines proposed). Companion to existing `DOCS/CODE_MAP.md` + `DOCS/COMPONENTS.md` + `DOCS/ARCHITECTURE.md` + `DOCS/CLAUDE_INTEGRATION.md`. Cross-references each existing doc + bridges them with concrete data-flow narratives.
- **What's deferred:**
  - **Hand-crafted data flow narratives** for the system's load-bearing paths:
    - Hot path: `BG_Evaluate → SG_Evaluate ×2 → TradeEvent push` (per-tick; ≤500ns p99)
    - Slow path per-core: `EventLoop_RebuildOneCore → RollingStats_Push → Regime_Classify → Strategy_BuildParameters → ExecutionCore_SetParameters` (seqlock publish; every poll_interval ticks; ≤100µs p99)
    - OMS drainer: `OMS_DrainSubmit → OrderManager_Tick HandleFill BUY/SELL → Pattern 5 sink-fn-pointer dispatch` (trade_log + calib_log)
    - GUI publish: producer thread → `TUISnapshot` double-buffered atomic exchange → ImGui render
    - Snapshot save/load: per-core slow_state + OMS + Position serialize via FOREACH walkers → file write → restart load + drift check
    - Paper reset: archive trade_log + reset OMS state + bump `paper_session_start_us`
    - Regime transitions: hysteresis-bounded `RANGING ↔ TRENDING ↔ VOLATILE ↔ MILD_TREND` state machine
    - Fan-out timing: producer thread tick read → SPSC ring per-core fan_out → per-core consumer
  - **Integration contracts cross-reference INDEX** — one page linking each cross-thread boundary → relevant DESIGN_SPEC (`cfg-scope-discipline.md` / `decision-time-data-binding-pattern.md` / `sink-fn-pointer-for-optional-side-effect-pattern.md` / etc.). Operator can trace any cross-thread interaction to its discipline anchor.
  - **NOT in scope: full function enumeration** — `rg <symbol>` answers in 50ms; static enumeration rots fast as new code lands. Hand-crafted narratives + integration contracts add value that grep doesn't; per-function listings don't.
- **Why deferred (not effort-avoidance):** ~6-10h focused writing window needed to do this WELL (not as ship-rider afterthought); workspace docs are operator-onboarding artifacts that benefit from a focused review pass. Better timing is after `.F` umbrella closes when the architectural shape is stable + the per-instance discipline patterns are canonical — premature writing would document a moving target. Operational safety audit / paper-test prep sprint is the natural home for this doc (operator workflow validation phase).
- **Cost estimate:** ~6-10h focused (~200-400 LOC markdown + cross-ref hyperlinks + 3-4 diagrams in ASCII art or PlantUML). Includes 1-2h cross-ref walking to ensure each DESIGN_SPEC is properly linked from its relevant data-flow narrative position.
- **Trigger:** **after v5.15 umbrella closes** — during operational safety audit / paper-test prep sprint. Specifically: after `.F.5` per-core Thompson audit ships + `.F` umbrella closes + paper-test session lands, the operational items sprint can carve out a focused window for this doc.
- **Status:** OPEN (queued for post-v5.15 operational items sprint)
- **Cross-ref:** `DOCS/CODE_MAP.md` (existing module-level catalog); `DOCS/COMPONENTS.md` (component breakdown); `DOCS/ARCHITECTURE.md` (high-level diagram); `DOCS/CLAUDE_INTEGRATION.md` (how-to-add-X recipes); `DOCS/EXECUTION_DISPLAY_INVARIANTS.md` (display↔execution discipline); CLAUDE.md "Architecture (sharded)" section (high-level data flow already documented); `DESIGN_SPECS/cfg-scope-discipline.md` + `DESIGN_SPECS/decision-time-data-binding-pattern.md` + `DESIGN_SPECS/sink-fn-pointer-for-optional-side-effect-pattern.md` (key boundary discipline references).

### TECH_DEBT-076 — `.F.4c.3` deferred WIP2d-1.B.2/B.3/B.4 — ControllerEventLoop + EngineSharded + Backtest wrapper migrations

- **Created:** 2026-05-16 (backfill per `.F.4d` pre-coding verification audit; `.F.4c.3` ship shipped ~60% of original subplan scope and postmortem was silent on this deferred phase)
- **Severity:** MEDIUM (cleanup discipline; not blocking new framework work)
- **Surface:** ControllerEventLoop wrapper sites (per-core slice param threading; complete the single-param consumer sig discipline established at WIP2c.0/2c.2); EngineSharded boot default paths; Backtest path equivalents. Specific sites enumerated in the original `.F.4c.3` subplan body (Steps 4-7 region).
- **What's deferred:** finish applying single-param `const PerCoreCfg<F>*` discipline to remaining ControllerEventLoop wrapper sites + EngineSharded boot defaults that still read flat `cfg.X` instead of per-core sliced `core_cfg->X`. ~10-15 sites estimated.
- **Why deferred (not effort-avoidance):** `.F.4c.3` scope-shifted mid-flight to absorb the OMS structural closure (Class 27/28/29 + comprehensively branchless OrderManager) when DrainPostFill recompute-from-cfg gap surfaced; the WIP2d-1.B.2/B.3/B.4 wrapper migrations were the next-planned phase but pushed to keep ship boundary focused. Code at HEAD is functional via `ControllerConfig_PopulateCoresFromFlat` shadow walker.
- **Cost estimate:** ~4-6h focused (mechanical migration; sister-canonical pattern to Class 25 sweep at `.F.4c.3`).
- **Trigger:** Bundle with WIP2e+f+g/h into single cleanup ship (`.F.4f` or `.F.5-pre`) post-`.F.4d` per operator decision 2026-05-16 ("finish current then do incomplete items").
- **Status:** OPEN (queued for cleanup ship post-`.F.4d`)
- **Cross-ref:** `.F.4c.3` subplan + postmortem § "Deferred from original subplan scope" (added 2026-05-16); CLAUDE.md item 19 (structural fix preferred); `DESIGN_SPECS/cfg-scope-discipline.md` § "Consumer over per-core array" + "single-param sig discipline".

### TECH_DEBT-077 — `.F.4c.3` deferred WIP2e — A2 bitmap-bool migration (28 KIND_BOOL flat rows → domain bitmaps)

- **Created:** 2026-05-16 (backfill per `.F.4d` pre-coding verification audit)
- **Severity:** MEDIUM (cohort-harmonization discipline; partial coverage today)
- **Surface:** Remaining 28 KIND_BOOL flat cfg rows that should migrate to domain bitmaps (`ml_cfg_flags`, `lifecycle_cfg_flags`, etc.) per the bitmap-dispatcher framework established at `.F.4c`. Specific rows enumerated in original `.F.4c.3` subplan WIP2e section.
- **What's deferred:** identify candidate KIND_BOOL rows (those that pass cfg-flag-eligibility criteria per `DESIGN_SPECS/cfg-flag-eligibility-criteria.md`); migrate from `KIND_BOOL` direct-int storage to bitmap-bit storage in appropriate domain (`ml_cfg_flags` or `lifecycle_cfg_flags` or new domain).
- **Why deferred (not effort-avoidance):** `.F.4c.3` shipped the higher-priority registry-split framework infrastructure (WIP1-WIP2d) + emergent OMS work; cohort-uniform bool migration was the next phase.
- **Cost estimate:** ~3-4h focused (mechanical per-flag migration via established bitmap-dispatcher pattern; ~28 rows; sister to `.F.4c.1`'s 18-row STAMP_BOUND cohort migration).
- **Trigger:** Bundle with WIP2d-1.B.2/B.3/B.4 + WIP2f + WIP2g/h into single cleanup ship post-`.F.4d`.
- **Status:** OPEN (queued for cleanup ship post-`.F.4d`)
- **Cross-ref:** `DESIGN_SPECS/bitmap-flag-api.md`; `DESIGN_SPECS/universal-registry-bitmap-dispatcher-pattern.md`; `DESIGN_SPECS/cfg-flag-eligibility-criteria.md`; TECH_DEBT-013 (BIT_FLAG storage class win for bool patterns) CLOSED at v5.14.9.

### TECH_DEBT-078 — `.F.4c.3` deferred WIP2f — Legacy `PerCoreOverrides<F>` + `ControllerConfig_ResolveForCore` + `core_overrides[16]` deletion

- **Created:** 2026-05-16 (backfill per `.F.4d` pre-coding verification audit)
- **Severity:** MEDIUM-HIGH (transitional infrastructure should not persist long-term; can confuse contributors)
- **Surface:** `CoreFrameworks/ControllerConfig.hpp` — `PerCoreOverrides<F>` struct definition (~255) + `ControllerConfig_ResolveForCore` function (~1404) + `core_overrides[16]` field on ControllerConfig + all caller sites still using `ResolveForCore` resolution path.
- **What's deferred:** Mark `PerCoreOverrides<F>` + `ControllerConfig_ResolveForCore` as legacy in `.F.4c.3`'s WIP2f phase but not actually deleted. The `PerCoreCfg<F>` struct + `ControllerConfig_PopulateCoresFromFlat` shadow walker are the new canonical infrastructure; legacy path still works but should be retired. Comment at `CfgFieldRegistry.hpp:700` says "TRANSITIONAL — delete at WIP2f".
- **Why deferred (not effort-avoidance):** WIP2f deletion requires all consumer sites to migrate first (WIP2d-1.B.2/B.3/B.4 per TECH_DEBT-076 + test fixture migrations per TECH_DEBT-079). Deletion CANNOT happen before consumer migration completes (forward dependency).
- **Cost estimate:** ~2-3h focused (after WIP2d-1.B.2/B.3/B.4 + WIP2g/h consumer migrations complete; deletion itself is mechanical).
- **Trigger:** AFTER TECH_DEBT-076 + TECH_DEBT-079 close (dependency chain). Sequenced into cleanup ship post-`.F.4d`.
- **Status:** OPEN (queued for cleanup ship post-`.F.4d`; sequenced after TECH_DEBT-076 + TECH_DEBT-079 within ship)
- **Cross-ref:** `.F.4c.3` subplan WIP2f section; CLAUDE.md item 13 (single source of truth via X-macro); `DESIGN_SPECS/cfg-scope-discipline.md` (canonical PerCoreCfg<F> single-param sig discipline supersedes ResolveForCore resolver pattern).

### TECH_DEBT-079 — `.F.4c.3` deferred WIP2g/h — Atomic flag-day (89 flat field declarations + ~414 test fixture migrations + 9 band-aid call removals)

- **Created:** 2026-05-16 (backfill per `.F.4d` pre-coding verification audit)
- **Severity:** HIGH (largest deferred scope from `.F.4c.3`; ~414 test fixture writes still target legacy flat fields; transitional infrastructure persists)
- **Surface:** ControllerConfig struct (89 flat per-core field declarations like `int core_0_strategy`, `FPN<F> core_0_risk_pct`, etc.); test fixtures across `tests/controller_test.cpp` + sister test files (~414 write sites that target flat fields); 7-9 band-aid `ControllerConfig_PopulateCoresFromFlat(&cfg)` call-sites in tests; final cleanup at consumer sites that still read flat fields.
- **What's deferred:** Atomic flag-day deletion of all 89 flat field declarations from ControllerConfig + sweep migration of ~414 test fixture writes from `cfg.core_0_X = Y` shape to `cfg.cores[0].X = Y` shape + remove the 7-9 band-aid `PopulateCoresFromFlat` calls. After flag-day, the shadow walker becomes orphaned + can be deleted; legacy flat fields gone; PerCoreCfg<F> is sole source-of-truth.
- **Why deferred (not effort-avoidance):** ~414 test fixture writes is a significant migration scope; deferring kept `.F.4c.3` ship boundary focused on framework infrastructure + emergent OMS work. Mechanical migration but high-touch; flag-day discipline (atomic switch + test sweep) is its own focused effort.
- **Cost estimate:** ~6-10h focused (mostly mechanical sed-style migration with verification; risk of breaking tests if migration is imprecise — needs careful per-fixture verification).
- **Trigger:** Bundle with TECH_DEBT-076 + TECH_DEBT-077 + TECH_DEBT-078 into single cleanup ship post-`.F.4d`.
- **Status:** OPEN (queued for cleanup ship post-`.F.4d`)
- **Cross-ref:** `.F.4c.3` subplan WIP2g/h section; CLAUDE.md item 13 (single source of truth); test file size discipline note in CLAUDE.md (tests may get split during this migration if controller_test.cpp grows further).

### TECH_DEBT-080 — `.F.4c.3` deferred `[core N]` section parser syntax (operator-facing cfg syntax)

- **Created:** 2026-05-16 (backfill per `.F.4d` pre-coding verification audit)
- **Severity:** MEDIUM (operator UX improvement; current flat-prefix syntax works but verbose)
- **Surface:** `CoreFrameworks/ControllerConfigParser.hpp` parser; `engine.cfg` example documentation. In-code comment at `ControllerConfig.hpp:2097` explicitly says "Future ship .F.4c.3 Step 3 introduces [core N] section parser".
- **What's deferred:** Add `[core 0]`, `[core 1]`, ... section header syntax to engine.cfg parser. Operator writes section-scoped key=value lines instead of verbose `core_N_X=Y` flat-prefix form. Parser detects `[core N]` header + scopes subsequent key=value lines until next section header or EOF.
- **Why deferred (not effort-avoidance):** Operator UX improvement; not load-bearing for framework correctness. Original `.F.4c.3` Step 3 planned this; ship boundary refocused on infrastructure + OMS work.
- **Cost estimate:** ~2-3h focused (parser changes + cfg.example doc + test coverage).
- **Trigger:** Bundle with WIP2g/h flag-day (TECH_DEBT-079) OR can stand alone post-flag-day. Operator-facing change; should ship with documented migration path (legacy flat-prefix syntax stays acceptable post-shipping; section syntax is sugar).
- **Status:** OPEN (queued for cleanup ship post-`.F.4d`)
- **Cross-ref:** in-code TODO at `ControllerConfig.hpp:2097`; `.F.4c.3` subplan Step 3 section; `DESIGN_SPECS/cfg-scope-discipline.md`.

### TECH_DEBT-075 — HP_REFACTOR.md O1-O6 bridge entry (cache-audit observations; profile-driven deferral)

- **Created:** 2026-05-16 by v5.15.5.F.4d merged ship planning (Option G decision session; auto-write contract gap closed — `tick-trader-percore-workspace/DOCS/HP_REFACTOR.md` had deferred observations O1-O6 but no TECH_DEBT bridge entry per the auto-write contract on `feedback_no_defer_for_effort` discipline).
- **Severity:** LOW-MED (cache layout optimization; profile-driven; not blocking)
- **Surface:** `tick-trader-percore-workspace/DOCS/HP_REFACTOR.md` cache-audit observations section. 6 deferred items:
  - **O1**: Per-slot data scattered across 3 different owners (Portfolio + OmsState + Order) — drainer at trade-close emits ~3-4 different cache lines. Cross-owner unification could reduce.
  - **O2**: ThompsonBandit SoA layout per-arm field separation — Thompson_Sample reads mu_post[i] + precision_post[i] + total_pulls[i] per-arm = 2-3 cache lines per access × 8 arms. AoS-pack alternative ~50-100ns p99 savings (profile-driven).
  - **O3**: Bandit_GetProbabilities AVX-512 path alignment verification (~30-60 min audit; LOW risk).
  - **O4**: Cross-cutting struct padding determinism audit (~2-4h audit; LOW risk).
  - **O5**: Cluster placement on EnsembleModelZoo + ThompsonBanditState post-multi-side expansion (`.F.4d` adds exit-side mirror; cluster surface grows ~25%; HOT/WARM/COLD cluster boundaries may need rebalancing).
  - **O6**: OmsPerSlotContext named-cluster sub-struct + AoS-by-slot conversion (decoupled from Pattern 4 framework concerns at `.F.4d` per decisions-capture Decision 1; cache-layout-only concern; orthogonal to framework discipline).
- **What's deferred:** all 6 cache-audit observations. Each has its own trigger documented in HP_REFACTOR.md sections O1-O6. Aggregate cache-audit-ship scope: ~2-3 days focused work; MED risk (cross-cutting; cache miss cascade potential); profile-data prerequisite.
- **Why deferred (not effort-avoidance):** profile-driven decisions; without production cache-miss + latency profile data, cache restructure is premature optimization (often regresses unexpectedly per HP_REFACTOR.md "Anti-premature-optimization reminder"). The proper ordering: structural framework consolidation FIRST (this ship `.F.4d`), THEN profile-driven cache optimization in dedicated HP-refactor ship. Per `feedback_no_defer_for_effort` discipline: legitimate timing defer (last-ditch wait for the right time), not effort-avoidance escape hatch.
- **Cost estimate:** O3 + O4 = ~3-5h (audit-only; low risk; could happen at any ship if needed). O1 + O2 + O5 + O6 = ~2-3 days focused effort (cache restructure; MED risk; requires profile data).
- **Trigger:** any of 4 trigger scenarios documented in HP_REFACTOR.md "When to consider an HP-refactor ship" section: (1) hot-path p99 budget pressure observed in production profile data; (2) new latency-sensitive feature requires hot-path expansion (e.g., maker order MVP per TECH_DEBT-008); (3) framework progression stabilizes — `.F.4d` umbrella close + `.F.4e` close + `.F.5` per-core Thompson audit ship + paper-test session is the natural window; (4) hardware/OS environment change.
- **Status:** OPEN (queued for post-framework-progression dedicated HP-refactor ship; profile-data prerequisite gates trigger 1 + 3)
- **Cross-ref:** `tick-trader-percore-workspace/DOCS/HP_REFACTOR.md` (scope document with full observation bodies + triggers); `tick-trader-percore-workspace/DOCS/DESIGN_PHILOSOPHY.md` § 4 Latency cost framework; `DOCS/STRATEGY_AND_CODING_RULES.md` (private; H7+H8 hot path invariants); `plans/_cross-cutting/2026-05-06-latency-path-discipline.md` (7 latency-path rules + anti-pattern history); `DESIGN_SPECS/branchless-dispatch-discipline.md`; `feedback_no_defer_for_effort` (operator framing — defer is last-ditch); auto-write contract per `CLAUDE.local.md` "Deferred items → DOCS/TECH_DEBT.md" rule (set 2026-05-09).

### TECH_DEBT-081 — `.F.4c.3.A` deferred symbol-axis full migration (KIND_STRING + multi-symbol DataStream + ~9 BinanceConfig.symbol consumer migration)

- **Created:** 2026-05-16 (backfill per `.F.4d` pre-coding subplan verification audit; `.F.4c.3.A` plan body self-marked PARTIAL but residual deferred work was not in TECH_DEBT ledger — invisible to `/readiness` Check 25)
- **Severity:** MEDIUM (canonical-shape discipline; symbol axis is single-symbol today via `BinanceConfig.symbol`; per-core symbol heterogeneity is a multi-symbol DataStream extension that depends on `.F.4e` KIND_STRING infrastructure)
- **Surface:** `DataStream/BinanceCrypto.hpp:64` (`BinanceConfig.symbol` global) + `CoreFrameworks/EngineSharded.hpp` (~9 consumer sites that read `BinanceConfig.symbol`) + per-core stamp body (symbol-axis-aware stamp emit) + Backtest path (symbol-aware load). Specific sites enumerated in `.F.4c.3.A` partial-stage subplan body.
- **What's deferred:** Full per-core symbol-axis migration from MANUAL exemption (landed at WIP2d-1.A) to canonical KIND_STRING `FOREACH_PER_CORE_CFG_FIELD` form. Items: (1) KIND_STRING infrastructure (depends on `.F.4e`); (2) per-core symbol UI design (multi-string entry tab); (3) validated-list source (Binance symbol catalog ingestion); (4) multi-symbol DataStream design (one BinanceCrypto stream per unique core symbol, OR one stream filtered per core); (5) per-core stamp body (model stamps `core_N_symbol`); (6) BinanceConfig.symbol consumer migration (~9 sites in EngineSharded.hpp + Backtest path).
- **Why deferred (not effort-avoidance):** WIP2d-1.A landed the MANUAL exemption + boot-uniformity check at `.F.4c.3` (closed the cfg-surface shape gap structurally — `core_symbol[16][32]` field exists + per-core parser case exists + boot check verifies cross-core uniformity until KIND_STRING infrastructure lands). Full migration depends on `.F.4e` KIND_STRING + multi-symbol DataStream redesign + symbol axis UI — each is its own focused work that warrants its own ship boundary.
- **Cost estimate:** ~4-8h focused (varies on multi-symbol DataStream scope). Could split: KIND_STRING migration of `core_symbol` (~1h after `.F.4e` ships) + consumer migration sweep (~2-3h) + multi-symbol DataStream design + impl (~2-4h, dominant cost).
- **Trigger:** **after `.F.4e` ships** (KIND_STRING infrastructure dependency); cleanup ship `.F.4f` OR standalone follow-on (operator decision based on scope appetite).
- **Status:** OPEN (queued post-`.F.4e`)
- **Cross-ref:** `plans/v5.15-live-readiness/subplans/2026-05-15-v5.15.5.F.4c.3.A-symbol-axis-per-core-migration.md` (partial-stage plan; documents deferred items inline); commit `4c6b150 v5.15.5.F.4c.3 WIP2d-1.A: Symbol axis MANUAL exemption (partial .F.4c.3.A advance)`; `MANUAL_FIELDS_INVENTORY.md` Section A `core_symbol[16][32]` entry (migration trigger documented inline); `DataStream/BinanceCrypto.hpp:64` (BinanceConfig.symbol declaration); CLAUDE.md item 19 (structural fix preferred); `DESIGN_SPECS/cfg-scope-discipline.md`.

### TECH_DEBT-082 — `.F.5` 3 unmigrated fields per-core eligibility audit (`confidence_ic_floor`, `lazy_rebuild_price_threshold_pct`, `exit_threshold`)

- **Created:** 2026-05-16 (backfill per `.F.4d` pre-coding subplan verification audit; `.F.5` SKETCH plan listed 13 fields for per-core override; 2 bandit/thompson absorbed by `.F.4d` Thread B; 9 of remaining 11 found in `FOREACH_PER_CORE_CFG_FIELD` at HEAD; **3 still in legacy flat-struct form** at `CoreFrameworks/ControllerConfig.hpp` with manual parser cases)
- **Severity:** LOW-MED (eligibility decision; audit + categorize before migration; one outcome may legitimately be "stay GLOBAL")
- **Surface:** `CoreFrameworks/ControllerConfig.hpp` lines 770 (`lazy_rebuild_price_threshold_pct`), 788 (`exit_threshold`), 970 (`confidence_ic_floor`) — struct fields declared flat. Parser cases at :2360, :2368, :2720 (manual `strcmp` + `atof` blocks). Not enrolled in `FOREACH_PER_CORE_CFG_FIELD` or `FOREACH_GLOBAL_CFG_FIELD` at HEAD.
- **What's deferred:** (1) audit per `DESIGN_SPECS/cfg-flag-eligibility-criteria.md` whether each field should be per-core (`.F.5` SKETCH said yes; sketch may have been wrong) OR stays GLOBAL; (2) for fields eligible for per-core: migrate from flat struct + manual parser to `FOREACH_PER_CORE_CFG_FIELD` row + `tt::cfg_*_field<T>` auto-flow; (3) for fields staying GLOBAL: migrate from flat struct + manual parser to `FOREACH_GLOBAL_CFG_FIELD` row (closes Class 23 manual-parser anti-pattern for these 3 sites regardless of per-core outcome).
- **Why deferred (not effort-avoidance):** `.F.5` SKETCH was SUPERSEDED by `.F.4d` MERGED + the bandit/thompson sub-cohort was absorbed by `.F.4d` Thread B. The remaining 3 fields' migration status was not visibly tracked. The fields are functional at HEAD (manual parser works); discipline is canonical-shape cohort harmonization rather than functionality.
- **Cost estimate:** ~1-2h focused (audit + 3-row registry migration per outcome; mechanical).
- **Trigger:** Bundle with `.F.4f` cleanup ship (TECH_DEBT-076 to -080 plus this for cohort-harmonization completeness) OR include in `.F.4d` Thread B as additional 3-field cohort migration if scope permits (decision: see `.F.4d` merged plan body Thread B Section 5.G-J — operator/coder decision at coding time).
- **Status:** **CLOSED at v5.15.5.F.4d 2026-05-16.** All 3 fields migrated to FOREACH_PER_CORE_CFG_FIELD as KIND_DOUBLE_PCT (lazy_rebuild_price_threshold_pct) + KIND_DOUBLE (exit_threshold + confidence_ic_floor; the latter stays `double` storage per H4 non-accounting threshold). Manual parser cases at ControllerConfig.hpp:2362-2365, 2370-2373, 2722-2725 DELETED. Class 23 manual-parser anti-pattern closed at 3 sites. Legacy flat field decls + ControllerConfig_Default init lines KEPT for legacy compat per .F.4d dual-track pattern (full removal at .F.4f cleanup ship per CLAUDE.local.md sprint state). `.F.5` charter residual closed completely — `.F.4f` Phase 7 conditional fold-in no longer needed.
- **Cross-ref:** `subplans/2026-05-13-v5.15.5.F.5-per-core-thompson-bandit-overrides.md` (SUPERSEDED SKETCH; 13-field cohort enumeration); `DESIGN_SPECS/cfg-flag-eligibility-criteria.md` (per-core eligibility framework); `CoreFrameworks/CfgFieldRegistry.hpp:412+` (`FOREACH_PER_CORE_CFG_FIELD` canonical registry); CLAUDE.md item 23 (Class 23 anti-pattern — manual parser); CLAUDE.md item 19 (structural fix preferred when bug class can recur); commit `fd9ad8e v5.15.5.F.4d MERGED WIP-checkpoint: TECH_DEBT-082 close — 3 .F.5 residual fields migrate to FOREACH_PER_CORE_CFG_FIELD`.

### TECH_DEBT-083 — IWYU hygiene sweep: 8 headers use `uintN_t` without direct `<cstdint>` / `<stdint.h>` include

- **Created:** 2026-05-16 (surfaced during `.F.4d` Step 1.C coding when removing an unused `<cstdint>` include from `ML_Headers/bandit_dispatch_table.hpp` exposed a transitive-include chain dependency; 2 chain-breakers — `CoreFrameworks/ParseFast.hpp` + `ML_Headers/BanditLearning.hpp` — fixed inline; 8 others remain latent)
- **Severity:** LOW (latent IWYU gap; not breaking current build because of transitive include chains in canonical use; would break if include order changes OR if a new header is added before the transitive cstdint-pull lands)
- **Surface:** 8 headers that use `uint64_t` (or `uint32_t`) without directly including `<cstdint>` or `<stdint.h>`:
  - `ML_Headers/CoreModelZoo.hpp`
  - `ML_Headers/ModelInference.hpp`
  - `ML_Headers/RewardTracker.hpp`
  - `ML_Headers/StampBoundModelConstRegistry.hpp`
  - `ML_Headers/WelfordStats.hpp`
  - `Strategies/MeanReversion.hpp`
  - `Strategies/Momentum.hpp`
  - `Strategies/RegimeDetector.hpp`
- **What's deferred:** add `#include <cstdint>` to each of the 8 headers; ~1-line mechanical addition per file; total ~8 lines + brief IWYU-discipline comment. Closes the latent class (any future include-order change won't expose new chain-breakers).
- **Why deferred (not effort-avoidance):** scope guard on `.F.4d` — pre-coding gate set scope at bandit/thompson 5-state + framework consolidation; IWYU hygiene is unrelated to that scope. Mechanical sweep belongs in a cleanup window. Per CLAUDE.local.md `feedback_consult_on_audit_findings` + scope-creep discipline: surface for operator triage, don't auto-sweep.
- **Cost estimate:** ~30 min focused (8 mechanical edits + verify clean build).
- **Trigger:** Bundle with `.F.4f` cleanup ship Phase 2 (TECH_DEBT-077 bitmap-bool migration also touches these surfaces) OR standalone micro-cleanup post-`.F.4d`. Operator decision on timing.
- **Status:** **CLOSED at v5.15.5.F.4d 2026-05-16.** All 7 remaining headers (CoreModelZoo + ModelInference + RewardTracker + WelfordStats + MeanReversion + Momentum + RegimeDetector) gained explicit `#include <cstdint>`. 8th header (StampBoundModelConstRegistry.hpp) was already fixed inline during prior-session WIP. Latent IWYU class closed structurally — any future include-order change can't expose new chain-breakers.
- **Cross-ref:** discovered during `.F.4d` Step 1.C coding (this session 2026-05-16); fixed inline: `CoreFrameworks/ParseFast.hpp:37` + `ML_Headers/BanditLearning.hpp:47` (both got explicit `#include <cstdint>`); CLAUDE.md item 19 (structural fix preferred when bug class can recur — closing the class via codebase-wide sweep is the right structural answer); commit `cf906a7 v5.15.5.F.4d MERGED WIP-checkpoint: TECH_DEBT-083 close — IWYU sweep (7 headers add explicit <cstdint>)`.

### TECH_DEBT-084 — Full symmetric rename of `thompson_bandits` → `buy_thompson_bandits` + FOREACH_BANDIT_SIDE auto-gen across all 6 per-side symbol families

- **Created:** 2026-05-16 during `.F.4d` Step 1.D Pattern 5 sink-fn-pointer design (this session) — explicit design decision to HAND-MIRROR exit-side rather than full FOREACH_BANDIT_SIDE auto-gen now, to avoid a cascade rename of existing `thompson_bandits` field across ~50 call sites. Captured as future cleanup so the design intent isn't lost.
- **Severity:** LOW (design-quality hygiene; current hand-mirror works correctly; future addition of a 3rd side — per-symbol? per-strategy? — would need 4× hand-writing per fn family without this cleanup)
- **Surface:** rename `EnsembleModelZoo<F>::thompson_bandits` → `buy_thompson_bandits` + `thompson_update_fn` → `buy_thompson_update_fn` + `last_predicted_thompson_arm` → `last_predicted_buy_thompson_arm` + `MASK_EZOO_THOMPSON_READY` → `MASK_EZOO_BUY_THOMPSON_READY` + `EnsembleModelZoo_InitThompsonBandits` → `EnsembleModelZoo_InitBuyThompsonBandits` (+ symmetric for `_Save`/`_Load`/`_State` JSON paths). All ~50 call sites + persistence file paths + test fixtures + GUI display references migrate.
- **What's deferred:** full FOREACH_BANDIT_SIDE auto-gen across all 6 per-side symbol families per § G.1 of `.F.4d` merged plan body. Replaces hand-mirror at `.F.4d` (which produces `thompson_bandits` + `thompson_exit_bandits` asymmetric naming + duplicate `_InitThompsonBandits`/`_InitExitThompsonBandits` fn bodies) with single X-macro expansion per consumer site:
  ```cpp
  #define _DEFINE_INIT_FN(side) \
      template <unsigned F> \
      inline void EnsembleModelZoo_Init##side##ThompsonBandits(EnsembleModelZoo<F>* ezoo, ...) { \
          /* body parameterized; field accessed as ezoo->side##_thompson_bandits[r] via token-paste */ \
      }
  FOREACH_BANDIT_SIDE(_DEFINE_INIT_FN)
  ```
  Adding a 3rd side (e.g., per-symbol Thompson) becomes 1 row in `FOREACH_BANDIT_SIDE(X) X(buy) X(exit) X(per_symbol)` → 6 mirror sites auto-generate (init fn / load fn / save fn / dispatch table entry / sink-fn field / init flag).
- **Why deferred (not effort-avoidance):** cascade rename of `thompson_bandits` field affects ~50 call sites across ML_Headers/ + GUI/ + tests/ + persistence file paths. Scope-creep risk for `.F.4d` which is already MED-HIGH risk. Per `feedback_overengineering_boundary_when_future_easier` — at the borderline of "harder now / easier future" the rule is "pick harder when future MUCH easier". Here the future-easier multiplier is modest (2 sides today, 3-4 projected; ~30-50 lines saved per future side). Defer is legitimate cost/benefit call.
- **Cost estimate:** ~6-10h focused (cascade rename via careful Edit replace_all + per-site verification + test fixture sweep + persistence file path migration + GUI display refresh + back-compat alias for old `thompson_state.json` filename → new `buy_thompson_state.json`).
- **Trigger:** when a 3rd per-side axis (per-symbol Thompson? per-strategy Thompson?) is proposed — at that point the rename cost is amortized by the auto-gen value. OR bundled into `.F.4f` cleanup ship if scope permits. OR standalone hygiene ship post-`.F.4e`.
- **Status:** **CLOSED at v5.15.5.F.4d 2026-05-16 (cascade rename portion — Phase 1 + Phase 2 per postmortem).** Cascade rename of 6 patterns across 14 files (200+ refs; word-boundary sed in collision-safe order): thompson_exit_bandits → exit_thompson_bandits + last_predicted_thompson_arm → last_predicted_buy_thompson_arm + MASK_EZOO_THOMPSON_READY → MASK_EZOO_BUY_THOMPSON_READY + EnsembleModelZoo_InitThompsonBandits → EnsembleModelZoo_InitBuyThompsonBandits + thompson_bandits → buy_thompson_bandits + thompson_update_fn → buy_thompson_update_fn. Persistence file path migration: thompson_state.json → buy_thompson_state.json + thompson_exit_state.json → exit_thompson_state.json with Load-side back-compat alias for existing on-disk model bundles. **Naming asymmetry closed.** Full FOREACH_BANDIT_SIDE auto-gen (X-macro expansion across 6 per-side symbol families replacing hand-mirror init/load/save fn bodies) DEFERRED to TECH_DEBT-085 as supplementary work — naming is symmetric so adding a 3rd side is mechanical even with hand-mirror.
- **Cross-ref:** `.F.4d` merged plan body § G (FOREACH_BANDIT_SIDE auto-mirror full design); `ML_Headers/CoreModelZoo.hpp` `EnsembleModelZoo<F>` struct (now symmetric naming); `ML_Headers/ThompsonBandit.hpp` `ThompsonUpdateFn` typedef + noop/real wrappers (sink-fn infrastructure ready for auto-gen consumer); CLAUDE.md item 19 (structural fix preferred when bug class can recur); CLAUDE.md item 31 (framework-driven extensibility); `DESIGN_SPECS/sink-fn-pointer-for-optional-side-effect-pattern.md` Pattern 5 — full auto-gen would generalize this; commit `f9e1882 v5.15.5.F.4d MERGED WIP-checkpoint: TECH_DEBT-084 close — FOREACH_BANDIT_SIDE cascade rename`.

### TECH_DEBT-085 — Thread A FULL framework consolidation (DerivedFilterFramework + 24-row migration + sidecar override + bit-packed inventory + CI 9-12 + Layer 5b + ML_CFG_FLAG sig migration + v5.14 fixture regression)

- **Created:** 2026-05-16 (at v5.15.5.F.4d MERGED ship close — Thread A FULL closure deferred per scope reality audit; foundation landed this ship (H15-H20 codified + 4 Thread A DESIGN_SPECs Stage 3 ACTIVE + STAMP_BOUND_CFG_DERIVED metadata bit (bit 13) reserved + FOREACH_BANDIT_SIDE enrolled in FOREACH_REGISTRY + CLAUDE.md item 31 codified))
- **Severity:** MED (framework consolidation; closes Class 21 at derived-filter surface + Class 18 at meta-Class-18 level; load-bearing for future cfg field additions becoming 1-row mechanical at source registry)
- **Surface:** 8 sub-items per merged plan body Thread A Charters 8-14:
  1. `CoreFrameworks/DerivedFilterFramework.hpp` (NEW) — 3 macro variants: `DERIVED_FILTER_DECLARE_GUI` + `DERIVED_FILTER_DECLARE_WIRE_FORMAT` + `DERIVED_FILTER_DECLARE_WIRE_FORMAT_TWO_SOURCE`
  2. `CoreFrameworks/StampBoundDerivedFilter.hpp` (NEW) — first canonical application via WIRE_FORMAT_TWO_SOURCE variant; consumes FOREACH_CFG_FIELD filtered by STAMP_BOUND + FOREACH_ML_CFG_FLAG filtered by STAMP_BOUND_CFG_DERIVED bit
  3. 24-row FOREACH_STAMP_BOUND_CFG migration — source rows in FOREACH_PER_CORE_CFG_FIELD / FOREACH_GLOBAL_CFG_FIELD get STAMP_BOUND_CFG_DERIVED metadata bit; emit_when expressions transform to drift-check `gate_when` per cohort (always-emit canonical per Q3.G alignment with `.A.7` precedent); legacy FOREACH_STAMP_BOUND_CFG emit body DELETED post-migration
  4. FOREACH_ML_CFG_FLAG 5-col → 6-col tuple migration (12 rows gain `metadata_flags` column; 5 STAMP_BOUND-eligible rows flip to STAMP_BOUND_CFG_DERIVED; X-macro consumer macros X_GEN_ML_CFG_BIT + X_GEN_ML_CFG_MASK get 5→6 arg sig update)
  5. `FOREACH_DRIFT_OVERRIDE(X)` sparse sidecar registry indexed by parent FIELD_IDX (5 rows for XGBoost training-only WARN_ALWAYS + CROSS_BINARY + EPS_TIGHT semantics); 8-byte bit-packed `DriftOverride` struct (multi-bit-state-encoding INVARIANT canonical application #6) carries has_override + severity + category + compare_kind + eps_idx
  6. Bit-packed `RegistryRosterEntry` (meta-registry topology; canonical #7) + `ManualFieldInventoryEntry` (CI cross-check infra; canonical #8)
  7. CI Checks 9-12 candidates per `registry-coverage-ci-check-pattern.md` Shape A — Check 9 (STAMP_BOUND_CFG_DERIVED coverage at .F.4d.1) + Checks 10-12 (GUI-only derived filters at .F.4e)
  8. `CFG_DRIFT_AUTOPOPULATE` companion macro + 12+ consumer migration sites (`ML_Headers/CoreModelZoo.hpp:225-247` inline drift loop replaces manual if-chain with single walker invocation; sister to STAMP_CFG_AUTOPOPULATE + INFERENCE_CFG_AUTOPOPULATE)
  9. Layer 5b hash lock + round-trip HMAC test against `tests/fixtures/v5_14_stamp_canonical.bin` (synthetic populate fn + `LOCKED_STAMP_BOUND_DERIVED_HASH_V5_15_5_F4D_1` constant + fnv1a_64 canonical body hash + Layer 5b methodology validation)
  10. v5.14 stamp fixture regression test verifying pre-migration v5.14 stamps load cleanly on `.F.4d.1` engine (legacy stamp byte format preserved; HMAC chain integrity verified; round-trip parse + re-emit byte-equivalent)
- **What's deferred:** All 10 items above. Foundation laid at v5.15.5.F.4d (H15-H20 codified + STAMP_BOUND_CFG_DERIVED bit reserved + 4 DESIGN_SPECs Stage 3 ACTIVE + FOREACH_BANDIT_SIDE first canonical) so future ship is mechanical: framework code lands → 24-row migration is structural → consumers convert → tests verify byte preservation.
- **Why deferred (not effort-avoidance):** ~15-25h focused work (multi-day project even with AI acceleration). Per `feedback_no_defer_for_effort` + `feedback_evaluate_options_on_robustness_latency_design_not_time` — both apply: effort isn't the deciding factor; scope reality IS (forcing into single session = compromised quality + compaction risk). Honest scoping > heroic single-session push. Foundation landed at v5.15.5.F.4d so .F.4d.1 has clear blueprint.
- **Cost estimate:** ~15-25h focused (dedicated .F.4d.1 ship; multi-day). Breakdown: DerivedFilterFramework.hpp ~2-3h + StampBoundDerivedFilter.hpp + Layer 5b ~2-3h + 24-row migration with always-emit semantic shift ~3-4h + consumer migration 12+ sites ~2-3h + legacy registry empty-out + verify ~1h + FOREACH_ML_CFG_FLAG sig migration ~1-2h + FOREACH_DRIFT_OVERRIDE sidecar + bit-packed DriftOverride ~2-3h + RegistryRosterEntry + ManualFieldInventoryEntry ~1-2h + CI Checks 9-12 ~1-2h + v5.14 fixture regression ~1-2h.
- **Trigger:** **Dedicated `.F.4d.1` ship after `.F.4d` umbrella close.** Per CLAUDE.local.md ship-after sequencing table: `.F.4d` (this ship, MERGED CLOSURE) → `.F.4d.1` (TECH_DEBT-085 Thread A FULL — focused 2-3 days) → `.F.4e` (KIND_STRING + 5 GUI metadata derived filter applications — validates DERIVED_FILTER framework via real second-source apps). `.F.4d.1` is INSERTED into sequencing this ship.
- **Status:** OPEN (queued as `.F.4d.1` dedicated ship; STUB plan body at `plans/v5.15-live-readiness/subplans/2026-05-16-v5.15.5.F.4d.1-thread-a-framework-full.md` per .F.4d ship close)
- **Cross-ref:** `subplans/2026-05-16-v5.15.5.F.4d-merged-framework-bandit-thompson.md` Thread A Charters 8-14 (full design); `DESIGN_SPECS/metadata-bit-driven-derived-filter-framework.md` Stage 3 ACTIVE (mechanism specification — Option B runtime walk filtering on metadata bit); `DESIGN_SPECS/sidecar-override-pattern-for-registry-auto-flows.md` Stage 3 ACTIVE (companion pattern for FOREACH_DRIFT_OVERRIDE); `DESIGN_SPECS/meta-registry-pattern-for-codebase-registry-discipline.md` Stage 3 ACTIVE (H19 topology); `DESIGN_SPECS/framework-composition-overview.md` Stage 3 ACTIVE (composition narrative); CLAUDE.md H15 + H16 + H17 + H18 + H19 (codified .F.4d 2026-05-16); CLAUDE.md item 31 (framework-driven extensibility meta-principle); commit `de41ff2 v5.15.5.F.4d MERGED WIP-checkpoint: Thread A foundation — STAMP_BOUND_CFG_DERIVED metadata bit (bit 13)`.

### TECH_DEBT-086 — `.F.4d` doc residual: RECURRING_BUG_PATTERNS amendments + DESIGN_PHILOSOPHY § 2 H15-H20 narrative + DESIGN_SPECS README catalog verification

- **Created:** 2026-05-16 (at v5.15.5.F.4d.1 planning consult — Decision 2 lock: bundle as TECH_DEBT-086 + fold into `.F.4d.1.D` ship close auto-writes; Option B separate doc-only mini-ship rejected as MVP-shaped per `feedback_no_mvp_for_plumbing_only_for_unknown_unknowns`)
- **Severity:** LOW (doc-residual; no code-functional impact). **Cost-to-defer IS real** though: `/bug-check` accuracy degrades without Class 30 in RECURRING_BUG_PATTERNS registry (next OMS sibling-array enrollment drift goes uncaught); cold-pickup orientation drifts without H15-H20 narrative in DESIGN_PHILOSOPHY § 2; `/handoff` skill load coverage misses 4 Thread A specs without catalog verification.
- **Surface:**
  - `DOCS/RECURRING_BUG_PATTERNS.md` (engine repo) — Class 30 codification + Class 24/25/28 amendments
  - `tick-trader-percore-workspace/DOCS/DESIGN_PHILOSOPHY.md` § 2 — H15-H20 narrative addition (currently codified in CLAUDE.md table; family-grouped philosophy doc narrative still pending)
  - `tick-trader-percore-workspace/DESIGN_SPECS/README.md` — catalog count update + Stage 3 ACTIVE marker verification (4 NEW Thread A specs from `.F.4d`: metadata-bit-driven-derived-filter-framework + sidecar-override-pattern-for-registry-auto-flows + meta-registry-pattern-for-codebase-registry-discipline + framework-composition-overview)
- **What's deferred:**
  1. **Class 30 codification** in RECURRING_BUG_PATTERNS.md — OMS sibling-array enrollment drift (codified `.F.4c.3` WIP2d-1.B.0 + structurally closed at `.F.4d` via FOREACH_OMS_PER_SLOT_FIELD 3→5 row enrollment; sister to Check 8 cohort eligibility CI)
  2. **Class 24 amendments** — bandit/thompson attribution surface sister application + Thompson_Update wired via dispatch tables canonical example at `.F.4d`
  3. **Class 25 amendments** — OMS consumer sweep precedent at `.F.4d` (`PerCoreCfg<F>*` single-param sig threaded through TickRewardsFromLookback + TradeCloseReward + ControllerEventLoop exit-side)
  4. **Class 28 amendments** — 6 cmov sites closed at `.F.4d` (Bandit_Update / Thompson_Sample / ModelInference Predict + WeightedBlend / RollingTurnover / __builtin_expect bounds guard); Pattern 5 sink-fn-pointer canonical added; `/hft-audit` skill extended with branchless dispatch opportunity scan
  5. **DESIGN_PHILOSOPHY § 2 H15-H20 narrative** — family-grouped discussion paralleling CLAUDE.md hard-invariants table (H15 X-macro registry enrollment + H16 metadata-bit derived-filter completeness + H17 cfg struct auto-generated + H18 sidecar override discipline + H19 meta-registry topology + H20 branchless preferred for SP/HP)
  6. **DESIGN_SPECS/README.md catalog verification** — confirm all 4 Thread A specs carry Stage 3 ACTIVE marker; bump total count (currently shows "57+ patterns" + "~71 patterns total" at end; verify against actual file count); confirm Stage 3 ACTIVE rows are present in catalog table; cross-link from `.F.4d` ship-close commit
- **Why deferred (not effort-avoidance):**
  - **Ship-close scope guard at `.F.4d` MERGED** — coder time at `.F.4d` spent on Thread B FULL + Thread A foundation + 3 substantial TECH_DEBT fold-ins (-082/-083/-084 ~9-13h combined). Doc residual is mechanical writes that don't drive functional ship deliverable; bundling into next ship's auto-write boundary preserves single-ship coherence.
  - **Auto-write contract** (CLAUDE.local.md) is mandatory at sub-ship close → `.F.4d.1.D` ship close is the natural ledger boundary
  - **Separate doc-only mini-ship rejected** — MVP-shaped (small bounded ship for one concern) per `feedback_no_mvp_for_plumbing_only_for_unknown_unknowns` rule; doc-only mini-ship adds Version bump + tag + postmortem overhead for ~2-3h of doc work
  - **Per Decision 2 at `.F.4d.1` planning consult 2026-05-16** — Option A (TECH_DEBT-086 + fold into `.D`) selected per philosophy alignment (auto-write contract + no-MVP-for-plumbing + `.D`'s LOW-risk boundary fits doc work + saves ship cycle vs Option B separate mini-ship)
- **Cost estimate:** ~2-3h focused. Breakdown: RECURRING_BUG_PATTERNS amendments (Class 30 codification + 3 class amendments) ~1h + DESIGN_PHILOSOPHY § 2 H15-H20 narrative ~1h + DESIGN_SPECS README catalog verification + Stage 3 ACTIVE marker confirmation + count update ~30 min. LOW risk (doc-only; no code-functional impact).
- **Trigger:** **`.F.4d.1.D` ship close.** Per Decision 2 at `.F.4d.1` planning consult 2026-05-16 + CLAUDE.local.md auto-write contract (mandatory at sub-ship close). `.D` is the natural boundary — CI + fixture is the smallest sub-ship; doc residual is the same flavor (verification + cleanup); ship-close cadence matches. **Revision 2026-05-16:** Caramel directed "we should go ahead and deal with this" → execution moved up from `.F.4d.1.D` ship close to `.F.4d.1` planning session (this session). Doc-only work doesn't need a ship-cycle deferral when it can land in the current planning context; aging it well + closing before plan-body drafts so they reference up-to-date docs.
- **Status:** **CLOSED at v5.15.5.F.4d.1 planning 2026-05-16** (per Caramel revision: executed in planning session vs deferred to `.D`). All 6 deliverables landed:
  1. **Class 30 landing ship note appended** (`RECURRING_BUG_PATTERNS.md` after Severity line; clarifies `.F.4c.4`→`.F.4d` merge per Option G ratification)
  2. **Class 24 .F.4d closure update appended** (Thompson_Update wire gap structurally closed at `.F.4d` via `FOREACH_BANDIT_ALGORITHM` 3→5 + dispatch tables; cross-link to `multi-state-dispatch-with-per-state-update-metadata.md`)
  3. **Class 25 .F.4d sweep extension appended** (OMS consumer surface migration: TickRewardsFromLookback + TradeCloseReward + ControllerEventLoop exit-side; `PerCoreCfg<F>*` single-param sig threaded)
  4. **Class 28 .F.4d canonical additions appended** (6 new cmov sites — Bandit_Update + Thompson_Sample + ModelInference_Predict + WeightedBlend + RollingTurnover + __builtin_expect rare bounds guard; Pattern 5 sink-fn extension for Thompson_Update; H20 ratification cross-ref)
  5. **DESIGN_PHILOSOPHY § 2 H15-H20 promoted** from "Pending codification" sub-table to main hard-invariants table (codified `.F.4d` 2026-05-16); family grouping notes added explaining H1-H6 / H7-H8 / H9-H12 / H13-H14 / H15-H20 partitioning
  6. **DESIGN_SPECS/README.md catalog verified + count bumped 71→72** (4 Thread A specs confirmed Stage 3 ACTIVE; new Stage 2 DRAFT `type-erased-per-core-resource-handle-pattern.md` row added with 3 canonical applications cited)
- **Cross-ref:** `plans/v5.15-live-readiness/postmortems/2026-05-16-v5.15.5.F.4d-merged-postmortem.md` (predecessor; items deferred from `.F.4d` ship close listed in postmortem "Decisions captured" + Version.hpp comment block); `plans/v5.15-live-readiness/handoffs/2026-05-16-v5.15.5.F.4d.1-planning-handoff.md` Decision 3 ("Auto-writes residual from `.F.4d`"); `DOCS/RECURRING_BUG_PATTERNS.md` (target for Class 30 + amendments); `tick-trader-percore-workspace/DOCS/DESIGN_PHILOSOPHY.md` § 2 (target for H15-H20 narrative); `tick-trader-percore-workspace/DESIGN_SPECS/README.md` (catalog verification target); CLAUDE.local.md "Auto-write contracts" rule; `feedback_no_mvp_for_plumbing_only_for_unknown_unknowns` memory; CLAUDE.md item 19 (structural fix preferred — applies here at meta-level: codifying Class 30 in registry is structural fix against future drift recurrence).
