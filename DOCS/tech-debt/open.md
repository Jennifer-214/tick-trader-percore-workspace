---
type: ledger-template
parent_index: DOCS/TECH_DEBT.md
covers: OPEN-status TECH_DEBT entries (actively deferred work with explicit triggers; includes DEFERRED-INDEFINITE)
established: 2026-05-18
---

# TECH_DEBT — OPEN entries

Sub-file for TECH_DEBT entries with `OPEN` status (or variants: OPEN with explicit trigger / DEFERRED-INDEFINITE / OPEN — partially addressed / PARTIAL CLOSED still-active / PHASE-N applied with subsequent phases OPEN). These are the actively-deferred items `/readiness` Check 25 scans pre-coding.

External cross-refs use canonical ID format `TECH_DEBT-NNN`. The ID is preserved across sub-files; `rg "TECH_DEBT-NNN"` finds the canonical entry in the appropriate sub-file automatically.

## Future debt findings will append here

When `/readiness` Check 25 OR `/merge-scan` OR any audit identifies deferral candidates:
1. Assign next TECH_DEBT-NNN
2. Fill in the format template (see `DOCS/TECH_DEBT.md` INDEX § "Format per entry")
3. Set initial status (usually OPEN) → append entry here
4. Cross-link from the audit report (`plans/plan_checks/*`)
5. Reference in commit message of the closing ship
6. When status flips to CLOSED, MOVE the entry to `closed.md`; leave a 1-line tombstone here ONLY if cross-refs benefit from forwarding

---

## Issues

### TECH_DEBT-144 — Codebase-wide integer-parse migration (111 `atoi`/`atol`/`strtol`/`strtoll`/`strtoul` sites)

```yaml
id: TECH_DEBT-144
severity: LOW
status: OPEN
trigger: .F professionalization sweep / guard-tracked after the .E.0.3 tt:: parse primitive lands
surface_tags: [parse, locale, h5-consistency, professionalization]
```

- **Created:** 2026-05-29 by v5.15.5.F.4d.1.E.0.1 hardened-gate audit (the 181-site `ato*`/`strto*` breadth enumeration).
- **What's deferred:** the **111 base-10 integer-parse sites** are NOT locale-fragile (`LC_NUMERIC` only affects the float decimal separator), so they are NOT determinism/correctness-critical and NOT net-gating. Migrate to the `tt::` integer-parse primitive for SSoT/H5-consistency + minor perf, once `.E.0.3` builds it. The manifest CI guard tracks them as KNOWN-PENDING (shrinking).
- **Why deferred (not effort-avoidance):** the class is *closed* by the `.E.0.3` primitive + guard (no new sites; existing tracked) per [[feedback_close_the_class_vs_migrate_every_site]]; this is the paced mechanical sweep, not a foundation requirement.
- **Cross-ref:** decision-log D-84/D-87; PARITY-034 (the float-parse half, which IS locale-fragile).

### TECH_DEBT-145 — F-107 calib/trade-log float emit not `LC_NUMERIC`-pinned

```yaml
id: TECH_DEBT-145
severity: LOW-MEDIUM
status: OPEN
trigger: PRE-PAPER-TEST correctness mini-ship (TaskList #5)
surface_tags: [locale, log-emit, determinism, output-only]
```

- **Created:** 2026-05-29 by v5.15.5.F.4d.1.E.0.1 hardened-gate audit (determinism-cluster sweep, finding F-107).
- **What's deferred:** calib/trade-log CSV float emit should use the canonical locale-pinned emit (per-thread `uselocale` or the `.E.0.3` format primitive). **Output-only — does NOT feed the replay net/golden** → not net-gating → routed PRE-PAPER-TEST.
- **Cross-ref:** decision-log D-87; PARITY-036 (the recorder-emit, which IS net-gating — distinct from these output-only logs).

### TECH_DEBT-146 — Symbol `lot_step_size`/`qty_decimals` stored as `double`

```yaml
id: TECH_DEBT-146
severity: LOW
status: OPEN
trigger: .E.0.3 review OR PRE-PAPER-TEST
surface_tags: [accounting, symbol-precision, fpn, order-validation]
```

- **Created:** 2026-05-29 by v5.15.5.F.4d.1.E.0.1 hardened-gate audit (symbol-precision question).
- **What's deferred:** `BinanceOrderAPI.hpp:76/80` stores `lot_step_size` as `double` + derives `qty_decimals`. For order-validation precision + consistency with the `.E.0.3` `string→FPN` direction, review whether it should be FPN/decimal-exact. Low-stakes (order validation, not core accounting).
- **Cross-ref:** decision-log D-85.

### TECH_DEBT-147 — True-decimal vs binary-FPN accounting representation (deferred design consideration)

```yaml
id: TECH_DEBT-147
severity: LOW
status: DEFERRED-INDEFINITE
trigger: only if exact-decimal-semantics (regulatory/audit) is ever required
surface_tags: [accounting, fpn, decimal-exactness, architecture]
```

- **Created:** 2026-05-29 by v5.15.5.F.4d.1.E.0.1 design discussion (the bit-packing / "perfect accuracy" thread).
- **What's deferred:** `.E.0.3` chose **binary FPN-direct** (D-85: ~1e-19 precision ≫ crypto tick need; keeps the branchless-binary perf core). A true **decimal fixed-point** type (mantissa + base-10 scale) would give *exact* decimal semantics, but replaces the FPN<64> binary core engine-wide and loses the branchless-binary math perf. Honest CS point: binary fixed-point cannot represent a decimal fraction (e.g. `0.12`) exactly at any width.
- **Why deferred:** binary FPN-direct is proportionate (1e-19 ≫ any need); true-decimal is over-correct (theoretical exactness not needed) at large cost. Namable if exact-decimal-semantics ever required.
- **Cross-ref:** decision-log D-85; [[feedback_two_foundations_determinism_vs_correctness]].

### TECH_DEBT-002 — Centralized engine `ControllerEventLoop` removal

```yaml
id: TECH_DEBT-002
title: Centralized engine ControllerEventLoop removal
severity: low
surface_tags: [slow-path, boot-time]
trigger: next-maintenance-window
status: open
opened: 2026-05-09
related_specs: []
```

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

### TECH_DEBT-007 — Empirically verify regime_trend_strength + regime_vol_zscore add information vs existing features

```yaml
id: TECH_DEBT-007
title: Empirically verify regime_trend_strength + regime_vol_zscore add information vs existing features
severity: low
surface_tags: [ml-inference, training]
trigger: explicit-operator
status: open
opened: 2026-05-09
related_specs: []
```

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

```yaml
id: TECH_DEBT-008
title: Maker order MVP deferred indefinitely (no consistent order book data source)
severity: medium
surface_tags: [live-trading, oms-drainer, backtest]
trigger: explicit-operator
status: open
opened: 2026-05-09
related_specs: []
```

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

```yaml
id: TECH_DEBT-009
title: FOREACH_CFG_FIELD registry for non-stamp-bound cfg fields (partial close, residual phases queued)
severity: low
surface_tags: [registry, cfg-flow, parser, gui-thread]
trigger: sub-ship-.F.4c-.F.4e
status: open
opened: 2026-05-09
related_specs: [DESIGN_SPECS/framework-patterns/universal-cfg-field-registry-pattern.md, DESIGN_SPECS/framework-patterns/heterogeneous-registry-pattern.md, DESIGN_SPECS/framework-patterns/type-trait-dispatch-via-tt-namespace.md]
```

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
- **Cross-ref:** v5.14.9.F-.F.6 ships (boolean subset closure); v5.15.5.F.4b engine commit `160da10` + tag `v5.15.5.F.4b` (KIND_DOUBLE/_PCT subset closure); `DESIGN_SPECS/framework-patterns/heterogeneous-registry-pattern.md` (DOMAIN SPLIT pattern reference impl); `DESIGN_SPECS/framework-patterns/universal-cfg-field-registry-pattern.md` (12-col Option D); `DESIGN_SPECS/framework-patterns/type-trait-dispatch-via-tt-namespace.md` (3-barrier antidote); `DOCS/RECURRING_BUG_PATTERNS.md` Class 23 (structurally extinct); `ML_Headers/StampBoundCfgRegistry.hpp` (sister registry for stamp-bound cfg; pattern precedent); CLAUDE.md item 13 (X-macro audited categories list).

---

### TECH_DEBT-031 — MetricsLog FOREACH registry refactor (multi-writer row-shape mismatch)

```yaml
id: TECH_DEBT-031
title: MetricsLog FOREACH registry refactor (multi-writer row-shape mismatch)
severity: low
surface_tags: [registry, wire-format]
trigger: recurrence-count-3
status: open
opened: 2026-05-10
related_specs: [DESIGN_SPECS/framework-patterns/calibration-log-column-registry.md]
```

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
- **Cross-ref:** v5.14.10.F commit (TBD); `DESIGN_SPECS/framework-patterns/calibration-log-column-registry.md` "Pattern variants" section + "Future application candidates" table; TECH_DEBT-010 (sister entry, CLOSED v5.14.10.D); /merge-scan 2026-05-10 v5.14.10 amended-plan finding N2 (originally bundled MetricsLog + ShardedTradeLog; trade log shipped, metrics deferred).

---

### TECH_DEBT-030 — cfg=2 dual-mode calibration log telemetry columns (deferred from v5.14.10.D)

```yaml
id: TECH_DEBT-030
title: cfg=2 dual-mode calibration log telemetry columns
severity: low
surface_tags: [oms-drainer, ml-inference, wire-format, registry]
trigger: explicit-operator
status: open
opened: 2026-05-10
related_specs: [DESIGN_SPECS/framework-patterns/calibration-log-column-registry.md]
```

- **Created:** 2026-05-10 by v5.14.10.D scope-cap decision (FOREACH_CALIB_LOG_COL refactor shipped; cfg=2-specific columns deferred for cross-component plumbing)
- **Severity:** LOW (operator-facing diagnostic feature; cfg=2 dispatch ships in v5.14.10.B; calibration log columns visualize the A/B comparison offline)
- **Surface:** `DataStream/CalibLogColRegistry.hpp` FOREACH_CALIB_LOG_COL registry; `CoreFrameworks/OrderManager.hpp` HandleFill calibration log row emit; `CoreFrameworks/OrderManager.hpp` OMS state per-slot fields for predict-time → fill-time data flow
- **What's deferred:** Add 3 cfg=2 dual-mode telemetry columns to FOREACH_CALIB_LOG_COL: `exp3_chosen_arm`, `thompson_chosen_arm`, `regime_id_at_pick`. Empty / -1 sentinels when cfg.bandit_algorithm != 2. Requires cross-component plumbing: capture exp3 + thompson chosen arms + regime at predict time (in ML_BuildParameters slow path), persist to fill time (per-slot OMS state OR Order struct field), read at HandleFill calib log row write.
- **Why deferred (not effort-avoidance):** v5.14.10.D ships the FOREACH_CALIB_LOG_COL pattern + REFACTORS the existing 9-column writer (closes TECH_DEBT-010 structurally). Cfg=2 telemetry columns require ADDITIONAL plumbing across 3 components (slow-path predict → OMS state → drainer-thread fill emit) that's a separate concern. Would have grown .D from ~250 LOC to ~400+ LOC. Better as a focused micro-ship (v5.14.10.E or v5.14.11+) once the cross-component data flow is designed.
- **Cost estimate:** ~100-150 LOC. Add 3 OMS per-slot fields (mirror `last_exit_predicted_arm` shape; ~30 LOC). Populate at slow-path predict (mirror `last_exit_was_predicted` population at EngineSharded.hpp:3144-3145; ~20 LOC). Read in HandleFill calib log row (caller scope contract update; ~10 LOC). Add 3 entries to FOREACH_CALIB_LOG_COL (~5 LOC). Tests for round-trip cfg=2 → calib log row (~30 LOC). Total ~95-115 LOC of focused work + tests.
- **Trigger:** Address (a) when operator initiates first paper-test session with cfg.bandit_algorithm=2 (dual-mode A/B), OR (b) when v5.14.10.E ships (would naturally bundle), OR (c) when v5.14.11+ adds another bandit-related per-fill telemetry need (consolidation candidate).
- **Status:** OPEN
- **Cross-ref:** v5.14.10.B (cfg=2 dispatch shipped; data sources `ezoo->last_predicted_horizon_idx` + `ezoo->last_predicted_thompson_arm` + `ezoo->last_predicted_regime_id` available at predict time); v5.14.10.D (closes TECH_DEBT-010 via FOREACH_CALIB_LOG_COL refactor; this entry tracks the deferred cfg=2 columns); `DataStream/CalibLogColRegistry.hpp` "FUTURE COLUMNS" comment block; `DESIGN_SPECS/framework-patterns/calibration-log-column-registry.md` "FUTURE APPLICATION CANDIDATES" table.

---

### TECH_DEBT-011 — FOREACH_PER_CORE_SNAP_FIELD registry for general visible-state snapshot fields

```yaml
id: TECH_DEBT-011
title: FOREACH_PER_CORE_SNAP_FIELD registry for general visible-state snapshot fields
severity: medium
surface_tags: [gui-thread, registry, slow-path]
trigger: recurrence-count-5
status: open
opened: 2026-05-09
related_specs: []
```

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

### TECH_DEBT-012 — FOREACH_OMS_STATE registry for OrderManager state fields

```yaml
id: TECH_DEBT-012
title: FOREACH_OMS_STATE registry for OrderManager state fields
severity: medium
surface_tags: [oms-drainer, registry, wire-format]
trigger: recurrence-count-3
status: open
opened: 2026-05-09
related_specs: []
```

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

### TECH_DEBT-018 — Codify `/precoding-audit` Layer 1 orchestrator skill

```yaml
id: TECH_DEBT-018
title: Codify /precoding-audit Layer 1 orchestrator skill
severity: low
surface_tags: [ci-tooling]
trigger: recurrence-count-5
status: open
opened: 2026-05-10
related_specs: []
```

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

### TECH_DEBT-020 — Per-core override SELECT macro factoring (BITMAP_SELECT)

```yaml
id: TECH_DEBT-020
title: Per-core override SELECT macro factoring (BITMAP_SELECT)
severity: low
surface_tags: [bitmap-packed, registry, cfg-flow]
trigger: recurrence-count-6
status: open
opened: 2026-05-10
related_specs: [DESIGN_SPECS/framework-patterns/bitmap-flag-api.md]
```

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
- **Cross-ref:** v5.14.9.F.6; `DESIGN_SPECS/framework-patterns/bitmap-flag-api.md` (sister BITMAP_* primitives — BITMAP_SELECT would join here when factored)

---

### TECH_DEBT-021 — Post-paper-test profiling: domain bitmap collapse OR further split decisions

```yaml
id: TECH_DEBT-021
title: Post-paper-test profiling — domain bitmap collapse OR further split decisions
severity: low
surface_tags: [bitmap-packed, cfg-flow, slow-path, paper-test]
trigger: paper-test
status: open
opened: 2026-05-10
related_specs: [DESIGN_SPECS/framework-patterns/heterogeneous-registry-pattern.md]
```

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
- **Cross-ref:** v5.14.9.F-.F.6 ships; TECH_DEBT-019 (rejected monolithic — this entry's collapse direction is what 019 rejected at design-time; profiling may flip the decision); `DESIGN_SPECS/framework-patterns/heterogeneous-registry-pattern.md` cache-layout discipline section

---

### TECH_DEBT-022 — Engine.cfg parser perfect-hash / trie dispatch

```yaml
id: TECH_DEBT-022
title: Engine.cfg parser perfect-hash / trie dispatch
severity: low
surface_tags: [parser, boot-time, cfg-flow]
trigger: next-maintenance-window
status: open
opened: 2026-05-10
related_specs: []
```

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

### TECH_DEBT-025 — Convert DESIGN_SPECS docs to invocable skills (long-horizon idea)

```yaml
id: TECH_DEBT-025
title: Convert DESIGN_SPECS docs to invocable skills (long-horizon idea)
severity: low
surface_tags: [ci-tooling]
trigger: explicit-operator
status: open
opened: 2026-05-10
related_specs: []
```

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

```yaml
id: TECH_DEBT-026
title: Per-core override of bandit_algorithm (per-core A/B testing)
severity: low
surface_tags: [cfg-flow, ml-inference, slow-path]
trigger: explicit-operator
status: open
opened: 2026-05-10
related_specs: [DESIGN_SPECS/framework-patterns/per-bit-per-core-override-pattern.md]
```

- **Created:** 2026-05-10 by /dod-audit run on v5.14.10-bayesian-thompson-bandit plan
- **Severity:** LOW
- **Surface:** `Strategies/StrategyParameters.hpp` ML_BuildParameters bandit dispatch (post-v5.14.10 introduction); `CoreFrameworks/PerCoreOverride.hpp` (per-bit-per-core override domains)
- **What's deferred:** Per-core override of `bandit_algorithm` cfg field. Today (post-v5.14.10) the algorithm choice is engine-wide. Future feature: per-core selection (e.g., `core_0_bandit_algorithm=0` Exp3, `core_1_bandit_algorithm=1` Thompson) to run head-to-head A/B comparison at the per-core level — natural extension of the dual-mode (cfg=2) telemetry.
- **Why deferred (not effort-avoidance):** v5.14.10 plan ships engine-wide algorithm choice; per-core override is a separate feature ship. Operator's primary A/B comparison happens via `cfg.bandit_algorithm=2` (both run, telemetry distinguishes) which doesn't need per-core override. Per-core override matters when operator wants to compare TRADING DECISIONS (each core actually trades on its own algorithm) vs telemetry-only. Pattern: `per-bit-per-core-override-pattern.md` (PER_CORE_OVERRIDE_BITMAP_DOMAINS) — but `bandit_algorithm` is INT enum not boolean, so the bitmap pattern doesn't directly apply; a SEPARATE per-core override mechanism is needed for INT-valued cfg fields (precedent: `risk_degradation_curve` per-core override added v5.14.9.C).
- **Cost estimate:** ~2-3h (mirror `risk_degradation_curve` per-core override pattern; add `core_N_bandit_algorithm` cfg parser entry + per-core resolution in ControllerConfig_ResolveForCore + thread through to gate_state). LOW risk (additive; default = engine-wide preserved).
- **Trigger:** Address when (a) operator requests per-core A/B testing of bandit algorithms (head-to-head decisions, not telemetry-only), OR (b) v5.X.Y adds another INT-enum cfg field needing per-core override (consolidation candidate), OR (c) FOREACH_BANDIT_ALGORITHM registry retrofit (TECH_DEBT-026's sister item — making algorithm-extensible amplifies the per-core override value).
- **Status:** OPEN
- **Cross-ref:** v5.14.10 plan (engine-wide algorithm choice ships first); `risk_degradation_curve` per-core override (v5.14.9.C precedent for INT-enum per-core override); `DESIGN_SPECS/framework-patterns/per-bit-per-core-override-pattern.md` (boolean variant; INT variant needs adaptation); /dod-audit 2026-05-10 v5.14.10 thompson report.

---

### TECH_DEBT-029 — Source file length reduction (large headers harm maintainability)

```yaml
id: TECH_DEBT-029
title: Source file length reduction (large headers harm maintainability)
severity: low
surface_tags: [test-infrastructure, source-headers, file-size-discipline]
trigger: n/a (closed)
status: wontfix-per-ai-workflow
opened: 2026-05-10
partial_closed_at: v5.15.5.F.4d.1.B.6
closed_at: v5.15.5.F.4d.1.B.7
closure_rationale: AI-driven solo workflow (per operator C1 directive 2026-05-27); test 5K rule retained for test-reliability; subfolder pattern Stage 3 frozen at file-size-split-discipline.md v1.4
last_amended: 2026-05-27
related_specs: [DESIGN_SPECS/doc-disciplines/file-size-split-discipline.md]
```

- **Created:** 2026-05-10 by Caramel musing during v5.14.10.0 PerCoreSnap layout work
- **Severity:** LOW (cosmetic / maintainability; no behavior or perf impact)
- **Status amendment 2026-05-27 (post-`.B.6` close + code-LOC methodology re-analysis):** OPEN → PARTIAL_CLOSURE. 1 of 6 split candidates structurally closed at `.B.6`; 6 files DROPPED from queue per code-LOC re-analysis (already under threshold by code-LOC methodology); remaining 4 candidates queued for `.B.7-.B.9`.
- **CLOSED at .B.6 (1 candidate):**
  - **`CoreFrameworks/EngineSharded.hpp`** (3,202 → 96-line INDEX SHIM + 4 subfolder sub-files) — `.B.6` first canonical of subfolder split + INDEX-shim pattern per `DESIGN_SPECS/doc-disciplines/file-size-split-discipline.md` v1.3. Sub-files: Boot.hpp (67/12 code) + SlowPath.hpp (188/78 code) + Async.hpp (905/460 code) + Run.hpp (2,436/1,406 code; under threshold per code-LOC counting).
- **DROPPED from split queue 2026-05-27 (6 files; under threshold by code-LOC; previously listed in inventory based on total-lines miscount):** ControllerConfig.hpp / EngineTUI.hpp / ModelInference.hpp / StrategyParameters.hpp / SettingsPanel.cpp / OrderManager.hpp.
- **Remaining split candidates (queued at .B.7-.B.9):**
  - **`Backtest/BacktestPanels.hpp`** (`.B.7`)
  - **`CoreFrameworks/ControllerEventLoop.hpp`** (`.B.8`)
  - **`ML_Headers/CoreModelZoo.hpp`** (`.B.8`)
  - **`Backtest/BacktestEngine.hpp`** (`.B.8`)
  - **`GUI/DashboardPanels.hpp`** (`.B.9`)
  - **`Backtest/PortfolioController.hpp`** (`.B.9`)
- **Surface (pre-`.B.6` inventory snapshot 2026-05-10; refreshed 2026-05-13 post-v5.15.5.B umbrella; re-classified 2026-05-27 per code-LOC methodology):**
  - `CoreFrameworks/ControllerEventLoop.hpp` — post-v5.15.5.B 3640 lines (queued for `.B.8`)
  - `tests/controller_test.cpp` — ~16k lines (covered by CLAUDE.md test file size discipline section; PARTIAL_CLOSURE at `.B.5` via TECH_DEBT-114 PARTIAL_CLOSURE + TECH_DEBT-127 full split queued)
- **Class:** Same maintenance-overhead class as the test file size discipline already in CLAUDE.md (test files > 5k lines must split BEFORE adding more tests). This entry surfaces the SOURCE-side analog for non-test files. Headers above 1500-2000 lines slow IDE navigation, increase merge-conflict surface, and discourage related-concern grouping (developers append to end-of-file rather than locating the relevant section).
- **What's deferred (post-`.B.6` PARTIAL_CLOSURE):** Source-file-size discipline GENERALIZED at `DESIGN_SPECS/doc-disciplines/file-size-split-discipline.md` (now Stage 3 first canonical at v5.15.5.F.4d.1.B.6; subfolder + INDEX-shim pattern is the canonical mechanism). Remaining 4 candidate splits queued at `.B.7-.B.9` per `subplans/2026-05-25-v5.15.5.F.4d.1.B-file-size-maintenance.md` umbrella. Each future split uses code-LOC counting (per [[feedback_count_code_loc_not_total_lines]]) + INDEX-shim pattern (subfolder split when natural seam by concern) + cpp17-inline-variable migration if shared header globals surface (per [[feedback_cpp17_inline_variable_for_shared_state_across_tus]]).
- **Why deferred (not effort-avoidance) — POST-`.B.6` framing:** Subfolder + INDEX-shim pattern + code-LOC counting + sister disciplines (cpp17-inline / SSoT / forward-decl-at-global / block-scope-statics enumeration) all codified at `.B.6` ship close as Stage 3 first canonical. Remaining splits at `.B.7-.B.9` apply established pattern to new candidates per file-size-maintenance umbrella plan; not novel work; mechanical extension of the canonical.
- **Cost estimate:** ~2-4h per file split (audit consumers + plan boundary + edit + build verify + test). Remaining 4 candidates: ~8-16h focused work. Less than original ~10-20h estimate because subfolder-pattern + INDEX-shim is now established + sister disciplines reduce per-split rebuild cycles.
- **Trigger:** Continue applying at `.B.7-.B.9` umbrella ships per `subplans/2026-05-25-v5.15.5.F.4d.1.B-file-size-maintenance.md` schedule.
- **Status:** PARTIAL_CLOSURE (1 of 6 in active queue at `.B.6`; 6 DROPPED from queue per code-LOC re-analysis; 4 remaining queued at `.B.7-.B.9`)
- **Cross-ref:** CLAUDE.md "Test file size discipline (added v5.11.35)" section (test-side analog; sister); v5.14.10.0 PerCoreSnap layout work (occasion for the original musing); `DESIGN_SPECS/doc-disciplines/file-size-split-discipline.md` v1.3 (Stage 3 first canonical at `.B.6`); `DESIGN_SPECS/data-disciplines/cpp17-inline-variable-for-header-shared-state.md` (sister discipline at same surface); `DESIGN_SPECS/meta-disciplines/single-source-of-truth-discipline.md` (sister discipline at same surface); RECURRING_BUG_PATTERNS Class 34 + Class 35 (sister anti-patterns surfaced at `.B.6` header-extract work); `subplans/2026-05-25-v5.15.5.F.4d.1.B-file-size-maintenance.md` umbrella plan; `subplans/2026-05-27-v5.15.5.F.4d.1.B.6-enginesharded-subfolder-split.md` first canonical worked instance.

---

### TECH_DEBT-032 — CLAUDE.md context-management cleanup (trim items 19-24 + handoff-skill-managed context loading)

```yaml
id: TECH_DEBT-032
title: CLAUDE.md context-management cleanup (trim items 19-24 + handoff-skill-managed context loading)
severity: medium
surface_tags: []
trigger: next-maintenance-window
status: open
opened: 2026-05-11
related_specs: []
```

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

### TECH_DEBT-034 — FOREACH_CLI_MODE registry + batch mode CLI infrastructure + per-run logging structure (deferred from v5.15.3)

```yaml
id: TECH_DEBT-034
title: FOREACH_CLI_MODE registry + batch mode CLI infrastructure + per-run logging structure
severity: low
surface_tags: [registry, training, ci-tooling, gui-thread]
trigger: explicit-operator
status: open
opened: 2026-05-12
related_specs: []
```

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

```yaml
id: TECH_DEBT-035
title: Engine-side state-exposure protocol + DoubleBufferedAtomic<T> template extraction
severity: low
surface_tags: [concurrency, gui-thread]
trigger: explicit-operator
status: open
opened: 2026-05-12
related_specs: []
```

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

```yaml
id: TECH_DEBT-036
title: Architectural-field AUTOPOPULATE redesign (registry tuple restructure)
severity: low
surface_tags: [registry, wire-format, ml-inference]
trigger: recurrence-count-5
status: open
opened: 2026-05-12
related_specs: []
```

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

---

### TECH_DEBT-038 — FOREACH_BITMAP_WIDTH X-macro registry deferred (BITMAP_BIT/POPCOUNT/FIRST families)

```yaml
id: TECH_DEBT-038
title: FOREACH_BITMAP_WIDTH X-macro registry deferred (BITMAP_BIT/POPCOUNT/FIRST families)
severity: low
surface_tags: [registry, bitmap-packed]
trigger: recurrence-count-4
status: open
opened: 2026-05-12
related_specs: []
```

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

```yaml
id: TECH_DEBT-039
title: ConfidenceScorer_UpdateAndMark CLOCK_REALTIME residual (drift-history wall-clock dependency)
severity: low
surface_tags: [oms-drainer, ml-inference, slow-path]
trigger: explicit-operator
status: open
opened: 2026-05-12
related_specs: []
```

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

### TECH_DEBT-041 — Multi-bit state encoding codebase audit + remaining candidate applications

```yaml
id: TECH_DEBT-041
title: Multi-bit state encoding codebase audit + remaining candidate applications
severity: medium
surface_tags: [bitmap-packed, slow-path, registry]
trigger: explicit-operator
status: open
opened: 2026-05-13
related_specs: [DESIGN_SPECS/refactor-patterns/multi-bit-state-encoding-pattern.md]
```

- **Created:** 2026-05-13 by v5.15.5.C.2.1 close (first application shipped; codebase audit deferred)
- **Severity:** MEDIUM (~120-150 bytes savable across EventLoopState + per-cycle branchless dispatch wins; bounded scope; design substrate already in place via `DESIGN_SPECS/refactor-patterns/multi-bit-state-encoding-pattern.md` + first application `MemHeaders/OmsExitPredictorMetaRegistry.hpp`)
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
- **Cross-ref:** `DESIGN_SPECS/refactor-patterns/multi-bit-state-encoding-pattern.md` (the design + candidate inventory + 10-item implementation checklist + decision tree + cost-benefit table); `MemHeaders/OmsExitPredictorMetaRegistry.hpp` (first field-tested application; v5.15.5.C.2.1 commit `097f91f`); CLAUDE.local.md "Going-forward rule: prefer multi-bit state encoding for K-state fields (set 2026-05-13)"; CLAUDE.md item 20 (per-record packing discipline) + item 28 (latency-vs-cache framework) + item 13 (X-macro registry).

---

### TECH_DEBT-042 — Registry-driven multi-bit slot overlap static_asserts (OmsStateFlagRegistry hybrid layout)

```yaml
id: TECH_DEBT-042
title: Registry-driven multi-bit slot overlap static_asserts (OmsStateFlagRegistry hybrid layout)
severity: medium
surface_tags: [registry, bitmap-packed, oms-drainer]
trigger: recurrence-count-2
status: open
opened: 2026-05-13
related_specs: [DESIGN_SPECS/refactor-patterns/multi-bit-state-encoding-pattern.md]
```

- **Created:** 2026-05-13 by /dod-audit MEDIUM-1 on commit `d410525` (v5.15.5.C.3 Phase 3b checkpoint)
- **Severity:** MEDIUM
- **Surface:** `MemHeaders/OmsStateFlagRegistry.hpp:190-209`
- **What's deferred:** EVENT_LOG_MODE slot overlap static_asserts are NAMED-EXPLICIT (3 asserts hand-rolled per slot); adding a 2nd multi-bit slot to `FOREACH_OMS_STATE_MULTI_BIT` requires hand-writing parallel asserts. Class-18 mirror at compile-time-check level — the registry currently generates `MASK_OMS_STATE_<name>` + `SHIFT_OMS_STATE_<name>` + `BITS_OMS_STATE_<name>` constants but NOT the safety asserts. Header comment line 190 acknowledges this with "extend with similar checks per added slot". A 4th X-macro consumer (`X_GEN_OMS_STATE_MULTI_BIT_OVERLAP_CHECK`) can auto-generate per-slot overlap pair-asserts via `FOREACH_OMS_STATE_MULTI_BIT(X)` walking the registry: single-bit-region overlap + uint8_t capacity + (for pairwise inter-slot overlap) a running `_OMS_STATE_MULTI_BIT_REGION` bitmask via the walk.
- **Why deferred (not effort-avoidance):** single multi-bit slot today (EVENT_LOG_MODE); deferral cost is one missed-pattern-application; trigger fires at 2nd multi-bit slot addition. Current hand-rolled asserts ARE complete + correct for the 1-slot state; structural fix is preventative.
- **Cost estimate:** ~30 min (8-15 LOC X_GEN_OMS_STATE_MULTI_BIT_OVERLAP_CHECK macro + verify all 3 asserts still fire with current data).
- **Trigger:** (a) next addition to `FOREACH_OMS_STATE_MULTI_BIT` (or first cross-registry multi-bit cohort pattern application introducing a 2nd slot); (b) any 2nd consumer of `FOREACH_OMS_STATE_MULTI_BIT` that requires similar overlap guarantees.
- **Status:** OPEN
- **Cross-ref:** `DESIGN_SPECS/refactor-patterns/multi-bit-state-encoding-pattern.md` Implementation Checklist; CLAUDE.md item 13 (X-macro registry), item 19 (structural fix preferred for recurring class); `plans/plan_checks/dod-audit-2026-05-13-v5.15.5.C.3-phase3b.md` MEDIUM-1.

---

### TECH_DEBT-043 — OmsExitPredictorMetaRegistry custom OMS_META_* duplicates generic MBS_* primitives

```yaml
id: TECH_DEBT-043
title: OmsExitPredictorMetaRegistry custom OMS_META_* duplicates generic MBS_* primitives
severity: low
surface_tags: [oms-drainer, bitmap-packed, registry]
trigger: explicit-operator
status: open
opened: 2026-05-13
related_specs: [DESIGN_SPECS/refactor-patterns/multi-bit-state-encoding-pattern.md]
```

- **Created:** 2026-05-13 by /dod-audit LOW-1 on commit `d410525` (v5.15.5.C.3 Phase 3b checkpoint)
- **Severity:** LOW
- **Surface:** `MemHeaders/OmsExitPredictorMetaRegistry.hpp:126-149` (OMS_META_GET_REGIME / OMS_META_GET_ARM / OMS_META_IS_VALID / OMS_META_PACK / OMS_META_CLEAR)
- **What's deferred:** `OmsExitPredictorMetaRegistry.hpp` (v5.15.5.C.2.1) shipped the FIRST multi-bit application with custom domain-specific accessors. Phase 3b adds generic `MBS_GET_U8` / `MBS_SET_U8` / `MBS_EQ_U8` primitives in `BitmapMacros.hpp` that supersede the domain-specific shorthand. `OMS_META_*` macros are functionally equivalent to `MBS_*` but pre-date the generic API. No bug; duplicated mechanism (CLAUDE.md item 16 reuse-audit principle). Future K-state slot additions should use generic `MBS_*` directly; `OMS_META_*` could migrate to thin convenience aliases or be removed.
- **Why deferred (not effort-avoidance):** functional equivalence; no bug; pure reuse-audit cleanup. Existing `OMS_META_*` consumers work correctly; migration is style + DRY consistency, not load-bearing.
- **Cost estimate:** ~1-2h (4 macros to rewrite as thin wrappers over `MBS_*_U8` + verify all 4-6 consumer sites compile / produce identical bytes / pass round-trip tests).
- **Trigger:** (a) next edit to `MemHeaders/OmsExitPredictorMetaRegistry.hpp` (extending the layout); (b) next edit to its accessor consumers (drainer HandleFill attribution + slow-path submit-time write); (c) focused reuse-audit cleanup sub-sprint.
- **Status:** OPEN
- **Cross-ref:** `DESIGN_SPECS/refactor-patterns/multi-bit-state-encoding-pattern.md` (canonical generic API); CLAUDE.md item 16 (reuse-audit principle); `MemHeaders/BitmapMacros.hpp:192-195` (header doc acknowledges pre-existing first application); `plans/plan_checks/dod-audit-2026-05-13-v5.15.5.C.3-phase3b.md` LOW-1.

---

### TECH_DEBT-044 — OMS_PROJECT_INIT_BIT / RESET_BIT use if/else; branchless mask-select for consistency with item 18(a)

```yaml
id: TECH_DEBT-044
title: OMS_PROJECT_INIT_BIT / RESET_BIT use if/else; branchless mask-select for consistency
severity: low
surface_tags: [oms-drainer, boot-time]
trigger: recurrence-count-2
status: open
opened: 2026-05-13
related_specs: [DESIGN_SPECS/refactor-patterns/latency-vs-cache-decision-framework.md]
```

- **Created:** 2026-05-13 by /dod-audit LOW-2 on commit `d410525` (v5.15.5.C.3 Phase 3b checkpoint)
- **Severity:** LOW
- **Surface:** `MemHeaders/OmsFieldRegistry.hpp:371-375` (OMS_PROJECT_INIT_BIT) + `:410-414` (OMS_PROJECT_RESET_DO_RESET_BIT)
- **What's deferred:** BIT-kind init/reset macros use data-dependent branch on init/reset value (`if ((int)(init)) field |= mask; else field &= ~mask;`). Branchless variant via `mask_val = -(int)!!init & mask; field = (field & ~mask) | mask_val` would be consistent with codebase's branchless mask discipline per CLAUDE.md item 18(a). Compiler likely cmov's the original form for the predictable boot-time path → zero measurable perf impact; style/consistency cleanup.
- **Why deferred (not effort-avoidance):** boot-only paths (zero measurable perf — branch fires few times per boot, predictable, cmov'd by compiler); style/consistency only. Branchy form is also more readable for OR-or-CLR semantics; branchless variant trades readability for instruction-count discipline.
- **Cost estimate:** ~5 min (2-line macro rewrite each × 2 macros = ~8 LOC).
- **Trigger:** (a) next AUTOPOPULATE-shape pattern application running at non-boot cadence (slow-path AUTOPOPULATE, hot-path AUTOPOPULATE); (b) /dod-audit or /merge-scan surfaces this site in a per-cycle context; (c) codebase-wide branchless-discipline sweep.
- **Status:** OPEN
- **Cross-ref:** CLAUDE.md item 18(a) (branchless mask compute), item 28 (latency-vs-cache framework); `DESIGN_SPECS/refactor-patterns/latency-vs-cache-decision-framework.md` Rule 2 "Prefer branchless over data-dependent branches"; `plans/plan_checks/dod-audit-2026-05-13-v5.15.5.C.3-phase3b.md` LOW-2.

---

### TECH_DEBT-045 — Phase 7.B runtime bench gate integration (template-dispatch wrappers + N instrumented sites + TUI surface)

```yaml
id: TECH_DEBT-045
title: Phase 7.B runtime bench gate integration (template-dispatch wrappers + N instrumented sites + TUI surface)
severity: low
surface_tags: [oms-drainer, ci-tooling, gui-thread]
trigger: explicit-operator
status: open
opened: 2026-05-13
related_specs: [DESIGN_SPECS/feature-patterns/runtime-toggleable-bench-gate-pattern.md]
```

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
- **Context:** v5.15.5.C.3 Phase 7.A shipped the SUBSTRATE for runtime bench gate per `DESIGN_SPECS/feature-patterns/runtime-toggleable-bench-gate-pattern.md`. The cfg flag has NO observable effect today; integration requires:
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
- **Cross-ref:** `MemHeaders/LatencyHistogram.hpp` (Phase 7.A substrate); `DESIGN_SPECS/feature-patterns/runtime-toggleable-bench-gate-pattern.md` (full design + 7 composition options); `CoreFrameworks/ControllerConfig.hpp` `oms_bench_enabled` field; CLAUDE.md item 18 (compile-time elision); CLAUDE.md item 25 (cross-thread cluster isolation); CLAUDE.md item 28 (latency-vs-cache framework).

---

### TECH_DEBT-046 — Fast-path companion accessor pattern (`_Fast` suffix for canonical runtime parameter) codification deferred to 2nd application

```yaml
id: TECH_DEBT-046
title: Fast-path companion accessor pattern (_Fast suffix for canonical runtime parameter) codification
severity: low
surface_tags: [ml-inference, slow-path]
trigger: recurrence-count-2
status: open
opened: 2026-05-13
related_specs: [DESIGN_SPECS/meta-disciplines/pattern-codification-lifecycle.md]
```

- **Created:** 2026-05-13 by v5.15.5.D close (first application shipped as `BookImbHistory_MeanShortFast`; codification deferred per pattern-codification-lifecycle.md Stage 0 "Skip when pattern is ONE-OFF" rule)
- **Severity:** LOW (no bug; pattern documentation gap; cohort migration on 2nd application closes the gap)
- **Surface:**
  - `ML_Headers/FlowFeatures.hpp:~115` — first application: `BookImbHistory_MeanShortFast(s)` paired with `BookImbHistory_MeanShort(s, int k)` (general API kept for tests with k=2)
  - Pattern shape: when a public API takes a runtime parameter `k` (or similar) that's almost always one canonical value at the production caller (production: k=64; test: k=2), expose a `_Fast` companion accessor that returns the cached/derived result for the canonical case (no runtime branch on k); keep the general API for non-canonical callers.
  - Other potential application sites (NOT surveyed in v5.15.5.D; surface during 2nd-app trigger investigation):
    - RollingStats accessors that take a window size (currently template-parameterized — different shape; may or may not benefit)
    - Any other "MeanShort(int k)" / "Mean(int k)" / "Variance(int k)" pattern in ML_Headers or Strategies
- **What's deferred:** Writing a DESIGN_SPECS doc for the pattern + applying it via the pattern-codification-lifecycle.md 7-stage process (Stage 0: identification + first reference are done; Stage 1-7: codify when a 2nd application surfaces).
- **Why deferred (not effort-avoidance):** per `DESIGN_SPECS/meta-disciplines/pattern-codification-lifecycle.md` "Skip when: pattern is ONE-OFF — apply structural fix without codification overhead." First application IS valuable on its own (eliminates O(K) walk in BookImbHistory); codification overhead (~4-6h for a focused codification ship) is not justified for 1 application. 2+ applications triggers full codification.
- **Cost estimate (if/when triggered):** ~4-6h for codification per the lifecycle (Stage 1 audit ~1h + Stage 2 DESIGN_SPEC ~1-2h + Stage 3-4 second application ~30 min - 2h + Stage 5 CLAUDE.md ~30 min + Stage 6 tooling ~30 min - 1h + Stage 7 wider audit ~1h).
- **Trigger:** (a) 2nd potential application site surfaces (in a `/merge-scan` or `/dod-audit` finding, or during a new ship's pre-coding); (b) operator-initiated codification request (e.g., as part of a focused pattern-codification sprint).
- **Status:** OPEN (awaiting 2nd-application trigger)
- **Cross-ref:** v5.15.5.D postmortem at `plans/v5.15-live-readiness/postmortems/2026-05-13-v5.15.5-D-postmortem.md` "Pattern B captured for future codification"; `ML_Headers/FlowFeatures.hpp` BookImbHistory_MeanShortFast (first application); `DESIGN_SPECS/meta-disciplines/pattern-codification-lifecycle.md` Stage 0 (identification + first reference complete).

---

### TECH_DEBT-049 — AoS time-series pattern codification deferred to 2nd application

```yaml
id: TECH_DEBT-049
title: AoS time-series pattern codification deferred to 2nd application
severity: low
surface_tags: [ml-inference, slow-path]
trigger: recurrence-count-2
status: open
opened: 2026-05-13
related_specs: [DESIGN_SPECS/meta-disciplines/pattern-codification-lifecycle.md, DESIGN_SPECS/refactor-patterns/latency-vs-cache-decision-framework.md]
```

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
- **Why deferred (not effort-avoidance):** per `DESIGN_SPECS/meta-disciplines/pattern-codification-lifecycle.md` "Skip when: pattern is ONE-OFF — apply structural fix without codification overhead." First application IS valuable on its own (2× CheckBreach cache locality); codification overhead (~4-6h for a focused codification ship) is not justified for 1 application. 2+ applications triggers full codification.
- **Cost estimate (if/when triggered):** ~4-6h for codification per the lifecycle (Stage 1 audit ~1h + Stage 2 DESIGN_SPEC ~1-2h + Stage 3-4 second application ~30 min - 2h + Stage 5 CLAUDE.md ~30 min + Stage 6 tooling ~30 min - 1h + Stage 7 wider audit ~1h).
- **Trigger:** (a) 2nd potential application site surfaces (in a `/merge-scan` or `/dod-audit` finding, or during a new ship's pre-coding); (b) operator-initiated codification request.
- **Status:** OPEN (awaiting 2nd-application trigger)
- **Cross-ref:** v5.15.5.E postmortem at `plans/v5.15-live-readiness/postmortems/2026-05-13-v5.15.5-E-postmortem.md`; `ML_Headers/ConfidenceScore.hpp` DriftSample struct (first application); `DESIGN_SPECS/refactor-patterns/latency-vs-cache-decision-framework.md` (cost framework that justifies the AoS decision); `DESIGN_SPECS/meta-disciplines/pattern-codification-lifecycle.md` Stage 0.

---

### TECH_DEBT-050 — controller.cfg integration into universal cfg field registry deferred to v5.15.6

```yaml
id: TECH_DEBT-050
title: controller.cfg integration into universal cfg field registry deferred to v5.15.6
severity: medium
surface_tags: [cfg-flow, gui-thread, registry]
trigger: sub-ship-v5.15.6.A
status: open
opened: 2026-05-14
related_specs: [DESIGN_SPECS/framework-patterns/categorical-tag-applicability-pattern.md]
```

- **Created:** 2026-05-14 by v5.15.5.F.4 planning (universal cfg field registry sprint scope cap)
- **Severity:** MEDIUM (operator-visible — controller.cfg currently requires manual text edit)
- **Surface:** `controller.cfg` + corresponding ControllerCfg struct + foxml_suite Settings tab
- **What's deferred:** extend FOREACH_CFG_FIELD with controller.cfg fields tagged `lives_in_struct=STRUCT_CONTROLLER_CFG`. Currently controller.cfg fields don't surface in Settings tab; operator edits the file manually.
- **Why deferred (not effort-avoidance):** v5.15.5.F.4 caps scope at engine+backtest unification (9 sub-ships). controller.cfg integration is mechanical extension of design locked at `.F.4b`; ships in v5.15.6.A as a focused follow-on sprint.
- **Cost estimate:** ~2-3h (audit ControllerCfg struct + add ~10-20 rows + verify byte-identical roundtrip + Settings tab dispatch).
- **Trigger:** v5.15.6 sprint kickoff OR earlier if operator complaint surfaces about controller.cfg manual edit friction.
- **Status:** OPEN
- **Cross-ref:** `plans/v5.15-live-readiness/subplans/2026-05-13-v5.15.5.F.4-universal-cfg-registry-sprint.md` (umbrella, v5.15.6 section); `DESIGN_SPECS/framework-patterns/categorical-tag-applicability-pattern.md` § "Cross-file cfg unification"; `plans/v5.15-live-readiness/subplans/2026-05-14-v5.15.5.F.4i-backtest-cfg-integration.md` (sister; backtest is the prototype that this ship inherits the pattern from).

---

### TECH_DEBT-051 — secrets.cfg integration with IS_SECRET metadata deferred to v5.15.6

```yaml
id: TECH_DEBT-051
title: secrets.cfg integration with IS_SECRET metadata deferred to v5.15.6
severity: medium
surface_tags: [cfg-flow, gui-thread, live-trading, registry]
trigger: sub-ship-v5.15.6.B
status: open
opened: 2026-05-14
related_specs: [DESIGN_SPECS/framework-patterns/universal-cfg-field-registry-pattern.md]
```

- **Created:** 2026-05-14 by v5.15.5.F.4 planning
- **Severity:** MEDIUM (operator-visible + security-critical — secrets currently require manual text edit + no UX safeguards)
- **Surface:** `secrets.cfg` + SecretsCfg struct + foxml_suite Settings tab
- **What's deferred:** extend FOREACH_CFG_FIELD with secrets.cfg fields tagged `lives_in_struct=STRUCT_SECRETS_CFG, metadata_flags |= IS_SECRET | LOG_VALUE_FORBIDDEN | SAFETY_CRITICAL`. GUI password masking via ImGuiInputTextFlags_Password; never-log enforcement via `Cfg_DumpForLogging` redaction; HMAC stamps never include IS_SECRET fields.
- **Why deferred:** scope cap; v5.15.6.B. Requires careful UX work (password masking + confirmation modal + security audit pass).
- **Cost estimate:** ~3-4h (audit + IS_SECRET metadata wiring + GUI affordances + security audit).
- **Trigger:** v5.15.6 sprint OR earlier if security concern surfaces.
- **Status:** OPEN
- **Cross-ref:** sister to TECH_DEBT-050; `DESIGN_SPECS/framework-patterns/universal-cfg-field-registry-pattern.md` § "MetadataFlag enum" (IS_SECRET bit reserved at `.F.4b`); `plans/v5.15-live-readiness/subplans/2026-05-13-v5.15.5.F.4d-string-filepath-gui-metadata.md` (IS_SECRET first GUI application).

---

### TECH_DEBT-052 — Training cfg integration deferred to v5.15.6

```yaml
id: TECH_DEBT-052
title: Training cfg integration deferred to v5.15.6
severity: medium
surface_tags: [training, cfg-flow, gui-thread, registry]
trigger: sub-ship-v5.15.6.C
status: open
opened: 2026-05-14
related_specs: [DESIGN_SPECS/framework-patterns/universal-cfg-field-registry-pattern.md]
```

- **Created:** 2026-05-14 by v5.15.5.F.4 planning
- **Severity:** MEDIUM (operator-visible — training params currently scattered between foxml_suite Training panel + Python scripts)
- **Surface:** training cfg (xgb hyperparameters + training pipeline params) + TrainingCfg struct + foxml_suite Training panel
- **What's deferred:** extend FOREACH_CFG_FIELD with training cfg fields tagged `lives_in_struct=STRUCT_TRAINING_CFG, applies_to_op_mode_cat=OP_MODE_CAT_TRAINING`. May require Kind enum extension: KIND_RANGE_INT, KIND_RANGE_DOUBLE for hyperparameter sweep ranges (e.g., `xgb_max_depth_range=4,6,8,12`).
- **Why deferred:** scope cap; v5.15.6.C. New Kind values require additional tt:: dispatch specializations.
- **Cost estimate:** ~3-4h (audit + new KIND_RANGE_* tt:: specializations if needed + Training panel integration).
- **Trigger:** v5.15.6 sprint OR earlier if Training panel UX concern surfaces.
- **Status:** OPEN
- **Cross-ref:** sister to TECH_DEBT-050/051; `DOCS/CLAUDE_FOXML_SUITE.md` (training panel architecture); `DESIGN_SPECS/framework-patterns/universal-cfg-field-registry-pattern.md` (KIND_RANGE_* reserved in descriptor).

---

### TECH_DEBT-053 — Phase 2 cfg struct unification (merge cfg structs into one) deferred to v5.16+

```yaml
id: TECH_DEBT-053
title: Phase 2 cfg struct unification (merge cfg structs into one) deferred to v5.16+
severity: low
surface_tags: [cfg-flow, registry]
trigger: explicit-operator
status: open
opened: 2026-05-14
related_specs: []
```

- **Created:** 2026-05-14 by v5.15.5.F.4 planning
- **Severity:** LOW (architectural cleanup; Phase 1 GUI unification at v5.15.5.F.4 + v5.15.6 covers operator UX needs)
- **Surface:** All 5 cfg structs (ControllerConfig + BacktestCfg + ControllerCfg + SecretsCfg + TrainingCfg)
- **What's deferred:** merge separate cfg structs into ONE struct with nested sections (`cfg.engine.X`, `cfg.backtest.X`, `cfg.controller.X`, etc.). Currently Phase 1 keeps structs separate; `lives_in_struct` discriminator routes parser/save.
- **Why deferred:** Phase 1 covers all operator-visible cfg unification needs without struct refactoring. Phase 2 is downstream code cleanup, not user-facing. Defer until v6.0 architectural pressure or burdensome cross-struct accessor surface.
- **Cost estimate:** ~6-8h (significant — touches Cfg struct definition + all consumers + may break snapshot wire format if Cfg is persisted; would need version bump + migration).
- **Trigger:** (a) v6.0 headless-service split where unified Cfg simplifies cross-process state externalization; (b) cross-struct accessor site count becomes burdensome; (c) Phase 1 validates the unification model + Phase 2 becomes worth the refactor cost.
- **Status:** OPEN
- **Cross-ref:** `plans/v5.15-live-readiness/subplans/2026-05-13-v5.15.5.F.4-universal-cfg-registry-sprint.md` (Phase 2 mentioned in Future Work); `plans/_future/2026-05-12-decoupling-endgoal-roadmap.md` (v6.0 alignment).

---

### TECH_DEBT-054 — Regime + risk-mode + feature categorical rollout deferred to v5.16+

```yaml
id: TECH_DEBT-054
title: Regime + risk-mode + feature categorical rollout deferred to v5.16+
severity: low
surface_tags: [cfg-flow, registry, gui-thread, ml-inference]
trigger: explicit-operator
status: open
opened: 2026-05-14
related_specs: [DESIGN_SPECS/framework-patterns/categorical-tag-applicability-pattern.md]
```

- **Created:** 2026-05-14 by v5.15.5.F.4 planning
- **Severity:** LOW (operator-visible — additional category dimensions provide finer-grained UX filtering)
- **Surface:** CfgFieldDescriptor's `applies_to_regime_cat` / `applies_to_risk_cat` columns (defaulted to `_CAT_ALL` at v5.15.5.F.4); FOREACH_REGIME + FOREACH_RISK_MODE registries; FOREACH_FEATURE for feature categorical
- **What's deferred:** populate regime + risk-mode + feature category masks for relevant cfg fields. Currently descriptor has columns; v5.15.5.F.4 only populates strategy + op_mode dimensions; remaining dimensions use `_CAT_ALL` placeholder.
- **Why deferred:** v5.15.5.F.4 caps scope at strategy + op_mode categorical (2 dimensions). Additional dimensions are extension of the locked design per CLAUDE.local.md "design upfront + ship in waves." Each dimension = audit pass + populate masks; no descriptor changes.
- **Cost estimate:** ~2-3h per dimension; 3 dimensions = ~6-9h total. Plus FOREACH_FEATURE rework with category column for feature dimension.
- **Trigger:** (a) operator complains about UX filtering granularity; (b) v5.16 sprint focused on categorical dimension extension; (c) regime-aware ML feature subset selection needs the categorical surface.
- **Status:** OPEN
- **Cross-ref:** `DESIGN_SPECS/framework-patterns/categorical-tag-applicability-pattern.md` § "Future application catalog"; `plans/v5.15-live-readiness/subplans/2026-05-14-v5.15.5.F.4h-strategy-category-audit-and-bitmap-overflow-audit.md` (strategy audit shipped at .F.4h; regime/risk audits are the analog).

---

### TECH_DEBT-055 — ResolvedCoreCfg AVX-512 batch-load + prefetch + delta-cache deferred to v5.16+

```yaml
id: TECH_DEBT-055
title: ResolvedCoreCfg AVX-512 batch-load + prefetch + delta-cache deferred to v5.16+
severity: low
surface_tags: [slow-path, cfg-flow]
trigger: paper-test
status: open
opened: 2026-05-14
related_specs: [DESIGN_SPECS/refactor-patterns/slow-path-cfg-resolution-cache-pattern.md]
```

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
- **Cross-ref:** `DESIGN_SPECS/refactor-patterns/slow-path-cfg-resolution-cache-pattern.md` § "Future work"; `DESIGN_SPECS/wire-format-patterns/avx512-byte-determinism-pattern.md` (CLAUDE.md item 25); `DOCS/HOT_PATH_CHANGELOG.md` (.F.4e entry logs these optimization paths with cost analysis).

---

### TECH_DEBT-056 — Codebase-wide bitpacking + branchless API audit (Caramel's later-review sweep)

```yaml
id: TECH_DEBT-056
title: Codebase-wide bitpacking + branchless API audit
severity: low
surface_tags: [bitmap-packed, slow-path, registry]
trigger: explicit-operator
status: open
opened: 2026-05-14
related_specs: [DESIGN_SPECS/refactor-patterns/multi-bit-state-encoding-pattern.md, DESIGN_SPECS/framework-patterns/bitmap-flag-api.md]
```

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
- **Cross-ref:** `DESIGN_SPECS/refactor-patterns/multi-bit-state-encoding-pattern.md` (CLAUDE.md item 30; INVARIANT STATUS after 3rd canonical application at .F.4d); `DESIGN_SPECS/framework-patterns/bitmap-flag-api.md`; `DOCS/DESIGN_PHILOSOPHY.md` § 4 (bit-packing-for-state-fields bullet added 2026-05-14); `/dod-audit` skill Stage 6 detection signature.

---

### TECH_DEBT-057 — Migrate ~15 unmigrated registries to FOREACH_REGISTRY meta-registry

```yaml
id: TECH_DEBT-057
title: Migrate ~15 unmigrated registries to FOREACH_REGISTRY meta-registry
severity: low
surface_tags: [registry]
trigger: next-maintenance-window
status: open
opened: 2026-05-14
related_specs: [DESIGN_SPECS/framework-patterns/meta-registry-pattern-for-codebase-registry-discipline.md]
```

- **Created:** 2026-05-14 by v5.15.5.F.4d planning
- **Severity:** LOW (each migration is a 1-line PR; primarily discoverability + CI cross-check benefit)
- **Surface:** ~15 X-macro registries that aren't yet declared in `CoreFrameworks/RegistryRoster.hpp` `FOREACH_REGISTRY` at .F.4d initial ship. Examples: FOREACH_SHALT, FOREACH_DEGRADATION_CURVE, FOREACH_BANDIT_ALGORITHM, FOREACH_BARRIER_BLEND_MODE, FOREACH_SLOW_PATH_GATE, 5 FOREACH_*_CFG_FLAG bitmap registries, FOREACH_CFG_DERIVED_INFERENCE_CFG, FOREACH_STAMP_BOUND_MODEL_CONST_PRE_CFG/_POST_CFG, FOREACH_FEATURE, FOREACH_REGIME, etc.
- **What's deferred:** add a row in `FOREACH_REGISTRY` for each currently-undeclared registry. Each row encodes: NAME, source_file, LEVEL (0=concrete), PARENT (ROOT or meta-registry name), design_spec ref, bug_class (if applicable), wire_format_kind (NOT_WIRE / WIRE_FORMAT / WIRE_FORMAT_TWO_SOURCE / MIXED), doc. Per `DESIGN_SPECS/framework-patterns/meta-registry-pattern-for-codebase-registry-discipline.md`.
- **Why deferred (not effort-avoidance):** .F.4d initial ship populates the FOREACH_REGISTRY with 10-15 most-load-bearing entries (CFG_FIELD, DERIVED_FILTER, STRATEGY, FEATURE, FAILURE_MODE, CFG_DRIFT_CHECK, ARCH_FIELD_DRIFT, ML_CFG_FLAG, etc.). Remaining registries get rows added as time allows; each is mechanical (~5 min per row). Per H14 (pending invariant): every X-macro registry MUST eventually be in FOREACH_REGISTRY; CI test enforces.
- **Cost estimate:** ~5 min per registry × 15 registries = ~75 min total. Best done as a single cleanup pass.
- **Trigger:** (a) batch addition opportunity during quiet period between sub-ships; (b) CI test added at .F.4d ship may flag undeclared registries as build warning → motivates migration; (c) `/precoding-audit-gate` auto-derivation accuracy improves with more roster coverage.
- **Status:** OPEN
- **Cross-ref:** `DESIGN_SPECS/framework-patterns/meta-registry-pattern-for-codebase-registry-discipline.md` (DRAFT v1.0 at .F.4d); H14 invariant (pending codification at .F.4d ship); `CoreFrameworks/RegistryRoster.hpp` (created at .F.4d).

---

### TECH_DEBT-058 — REGISTRY_TOPOLOGY.md auto-generation Python script

```yaml
id: TECH_DEBT-058
title: REGISTRY_TOPOLOGY.md auto-generation Python script
severity: low
surface_tags: [ci-tooling, registry]
trigger: recurrence-count-25
status: open
opened: 2026-05-14
related_specs: [DESIGN_SPECS/framework-patterns/meta-registry-pattern-for-codebase-registry-discipline.md]
```

- **Created:** 2026-05-14 by v5.15.5.F.4d planning
- **Severity:** LOW (manual REGISTRY_TOPOLOGY.md ships at .F.4d; auto-gen is hygiene improvement)
- **Surface:** new file `tools/generate_registry_topology.py` (~50 LOC Python script that parses `CoreFrameworks/RegistryRoster.hpp` `FOREACH_REGISTRY` entries + emits ASCII tree visualization to `workspace/DOCS/REGISTRY_TOPOLOGY.md`)
- **What's deferred:** auto-generation of `REGISTRY_TOPOLOGY.md` from the FOREACH_REGISTRY data. Manual version ships at .F.4d (hand-written ASCII tree); auto-gen converts that to a CI-checked derived artifact (regenerate on every registry change + diff against committed version to ensure freshness).
- **Why deferred:** Manual REGISTRY_TOPOLOGY.md at .F.4d is sufficient for immediate cold-pickup needs (20-25 entries; hand-curatable). Auto-gen pays off once entries grow + manual maintenance drift risks setting in. Scaffolding for the auto-gen pattern at v5.15.6+ when 2nd derived-doc surface (e.g., cfg-by-metadata.md from .F.4e) makes generator generalization worthwhile.
- **Cost estimate:** ~1-2h (Python script + CI integration + test against current FOREACH_REGISTRY content; treat as derived artifact).
- **Trigger:** (a) FOREACH_REGISTRY entry count grows past ~25; (b) manual REGISTRY_TOPOLOGY.md drifts from FOREACH_REGISTRY content; (c) v5.15.6 introduces second derived-doc surface (cfg-by-metadata.md) — generalize the auto-gen pattern.
- **Status:** OPEN
- **Cross-ref:** `DESIGN_SPECS/framework-patterns/meta-registry-pattern-for-codebase-registry-discipline.md`; sister to TECH_DEBT-057 (rate-limiting factor: FOREACH_REGISTRY coverage); `tools/` directory (sibling Python derived-doc tools).

---

### TECH_DEBT-059 — stamp-vs-runtime-drift-detection-registry.md wide variant DEPRECATION (post-.F.4d ship)

```yaml
id: TECH_DEBT-059
title: stamp-vs-runtime-drift-detection-registry.md wide variant DEPRECATION
severity: low
surface_tags: [registry, wire-format]
trigger: sub-ship-.F.4d
status: open
opened: 2026-05-14
related_specs: [DESIGN_SPECS/framework-patterns/sidecar-override-pattern-for-registry-auto-flows.md]
```

- **Created:** 2026-05-14 by v5.15.5.F.4d planning
- **Severity:** LOW (DESIGN_SPEC update; documents the pattern's evolution post-.F.4d superseding by sidecar pattern)
- **Surface:** `workspace/DESIGN_SPECS/framework-patterns/stamp-vs-runtime-drift-detection-registry.md` § "Wide variant (FOREACH_CFG_DRIFT_CHECK — 10-col tuple, multi-axis Y3, ack-aware)"
- **What's deferred:** mark the WIDE variant as DEPRECATED-FOR-CFG-DRIFT in the DESIGN_SPEC. Replaced by `DESIGN_SPECS/framework-patterns/sidecar-override-pattern-for-registry-auto-flows.md` (NEW at .F.4d). Narrow variant (FOREACH_ARCH_FIELD_DRIFT) stays — different surface; not over cfg fields. Wide variant pattern itself remains valid for OTHER non-cfg drift surfaces; only the cfg-drift application supersedes.
- **Why deferred (until .F.4d ships):** Wide variant currently has 1 production application (`CfgDriftCheckRegistry.hpp` 19-entry registry). .F.4d ship retires it (auto-flow via CFG_DRIFT_AUTOPOPULATE + 5-entry FOREACH_DRIFT_OVERRIDE sidecar). After .F.4d ships, update the wide-variant section to add DEPRECATION notice + cross-ref to sidecar pattern.
- **Cost estimate:** ~15 min (light edit to wide-variant section header + Cross-references update + DESIGN_SPECS/README.md catalog status update).
- **Trigger:** **AFTER .F.4d ships** + CfgDriftCheckRegistry deletion verified.
- **Status:** OPEN (blocked on .F.4d ship)
- **Cross-ref:** `DESIGN_SPECS/framework-patterns/sidecar-override-pattern-for-registry-auto-flows.md` (supersedes for cfg-drift surface); `DESIGN_SPECS/framework-patterns/stamp-vs-runtime-drift-detection-registry.md` (wide variant section); H17 invariant (pending codification at .F.4d ship).

---

### TECH_DEBT-064 — Headless operation option (deferred 2026-05-14 — considered, GUI stays primary for now)

```yaml
id: TECH_DEBT-064
title: Headless operation option
severity: low
surface_tags: [gui-thread, ci-tooling]
trigger: explicit-operator
status: open
opened: 2026-05-14
related_specs: []
```

- **Created:** 2026-05-14 by v5.15.5.F.4c session — Caramel considered prioritizing headless operation; decided GUI remains primary for now; metadata-bit hooks (TECH_DEBT-066, 067) kept as future optionality.
- **Severity:** LOW (deferral doc; captures option not commitment)
- **Surface:** `engine` binary (existing ANSI TUI) + future CLI subcommands (TECH_DEBT-066) + structured log output (TECH_DEBT-065/067)
- **What's deferred:** the strategic pivot to headless-first. Considered + deferred. The `engine` binary already builds without SDL/OpenGL/ImGui (no rewrite required); pivot would be promoting it to primary entry point + freezing GUI feature additions. NOT decided.
- **Why deferred:** Caramel preference noted (`tail -f` + CLI workflow appealing) but `tail -f` workflow hasn't been validated against actual operator use. GUI is currently working + maintained; pivot risks unwinding correct work for an unvalidated direction. Revisit when (a) `tail -f` workflow gets dogfooded, OR (b) `.F.4` closes + frameworks are mature enough to make CLI subcommands cheap, OR (c) operator explicitly says "yes, pivot."
- **Cost estimate:** ZERO implementation cost (this entry is the deferral itself; actual pivot is a future strategic decision).
- **Trigger:** operator decision — not auto-fire. Re-evaluate at end of `.F.4` umbrella close OR when GUI maintenance burden becomes blocking.
- **Status:** OPEN (option preserved; not committed)
- **Cross-ref:** TECH_DEBT-063 / 065 / 066 / 067 (related future-optionality entries); `plans/_future/2026-05-14-headless-first-orientation.md` (aspirational roadmap; revisit if/when pivot decision made).

---

### TECH_DEBT-065 — JSON-structured log format for engine status snapshots

```yaml
id: TECH_DEBT-065
title: JSON-structured log format for engine status snapshots
severity: medium
surface_tags: [wire-format, slow-path, gui-thread]
trigger: sub-ship-.F.4-close
status: open
opened: 2026-05-14
related_specs: []
```

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

---

### TECH_DEBT-066 — `engine` CLI subcommands for headless operator workflow

```yaml
id: TECH_DEBT-066
title: engine CLI subcommands for headless operator workflow
severity: high
surface_tags: [cross-tool, cfg-flow, live-trading]
trigger: explicit-operator
status: open
opened: 2026-05-14
related_specs: []
```

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

---

### TECH_DEBT-067 — Per-core + per-path structured log emit (TUI + log granularity)

```yaml
id: TECH_DEBT-067
title: Per-core + per-path structured log emit (TUI + log granularity)
severity: medium
surface_tags: [wire-format, slow-path, hot-path, gui-thread, producer, oms-drainer]
trigger: sub-ship-.F.4-close
status: open
opened: 2026-05-14
related_specs: []
```

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

---

### TECH_DEBT-068 — ML-side enum X-macro registries (ml_backend / regime_model_backend / confidence_ic_variant / csv_sort_check_mode / reconcile_mode / ensemble_blend_mode)

```yaml
id: TECH_DEBT-068
title: ML-side enum X-macro registries (6 cohort)
severity: medium
surface_tags: [registry, ml-inference, cfg-flow]
trigger: sub-ship-.F.4-close
status: open
opened: 2026-05-14
related_specs: [DESIGN_SPECS/framework-patterns/x-macro-registry-with-presence-dispatch.md, DESIGN_SPECS/framework-patterns/universal-registry-bitmap-dispatcher-pattern.md]
```

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
- **Cross-ref:** `Strategies/BanditAlgorithmRegistry.hpp` / `Strategies/BarrierBlendModeRegistry.hpp` / `ML_Headers/ConfidenceScore.hpp::FOREACH_DEGRADATION_CURVE` (canonical precedent); `DESIGN_SPECS/framework-patterns/x-macro-registry-with-presence-dispatch.md`; `.F.4c` Step 2 KIND_INT_ENUM section (these rows ship as KIND_INT pending registry creation); `DESIGN_SPECS/framework-patterns/universal-registry-bitmap-dispatcher-pattern.md` (the bitmap dispatcher framework landed at `.F.4c` applies to these registries once they exist — adds per-bit/per-enum-value filtering + popcount stats + branchless iteration; below ~10 entries the framework overhead may not amortize → judgment per registry).

---

### TECH_DEBT-069 — Codebase-wide registry-table `static const` → `inline constexpr` promotion sweep

```yaml
id: TECH_DEBT-069
title: Codebase-wide registry-table static const → inline constexpr promotion sweep
severity: low
surface_tags: [registry, boot-time]
trigger: sub-ship-v5.15.5.F.6
status: open
opened: 2026-05-14
related_specs: []
```

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

---

### TECH_DEBT-070 — Compile-time SubmitCommand required-field enforcement (C++17 friend-scope wall)

```yaml
id: TECH_DEBT-070
title: Compile-time SubmitCommand required-field enforcement (C++17 friend-scope wall)
severity: low
surface_tags: [oms-drainer, test-infrastructure]
trigger: sub-ship-cpp20-upgrade
status: open
opened: 2026-05-15
related_specs: []
```

- **Created:** 2026-05-15 by v5.15.5.F.4c.3 WIP2d-1.B.1 (option-A `private` default ctor + `friend` access for known producers failed under C++17 friend-scope rules at controller_test scope).
- **Severity:** LOW (current runtime guard works; structural enforcement is "better discipline" not "fixes broken behavior").
- **Surface:** `CoreFrameworks/SubmitCommand.hpp` POD struct + required-field ctor `SubmitCommand(core_id, order_type, qty, intended_price, fee_rate, ...)`. Today: BOTH the default ctor (for SPSC ring slot init) AND the required-field ctor are `public`; the default ctor is named `SubmitCommand{}` and produces a zero-init slot. A caller that forgets to overwrite fields before push silently sends a zero-init command. Runtime guard: ShardedLiveSafety_PreSubmitGate validates per-field non-zero invariants and rejects malformed commands; the rejection logs filename+line.
- **What's deferred:** under C++20, use `concept`-constrained ctors + designated-init compile-time enforcement to make "constructed without all required fields = compile error." The C++17 friend-scope attempt hit a wall: making the default ctor `private` + friending the canonical producer fns (`OMS_DrainSubmit`, `Reconcile_ApplyMissedFills`, backtest seed paths) broke `controller_test.cpp` test fixtures that aggregate-init via `SubmitCommand cmd{}; cmd.core_id = 0; cmd.order_type = ...`. C++17 disallows friend access in aggregate init contexts; refactoring the ~21 test fixtures to use the required-field ctor was viable but the friend declaration list itself drifts (every new producer fn needs adding to the friend list at the SubmitCommand definition site — Class 18 mirror-incomplete risk).
- **Why deferred (not effort-avoidance):** C++17 cannot express "required field at construction" cleanly. C++20 `concepts` + designated init + `[[nodiscard]]` ctors give a clean path. Until C++20 upgrade (TECH_DEBT-073), the runtime guard at ShardedLiveSafety_PreSubmitGate is the discipline anchor. Operator visibility: a malformed-cmd log line = "someone forgot to fill a SubmitCommand field"; same diagnostic surface as compile-time error, just slower feedback loop.
- **Cost estimate:** ~3-4h after C++20 upgrade lands. Refactor: (1) define `Submittable` concept requiring all required fields, (2) change required-field ctor to `requires Submittable<...>`, (3) update ~21 test fixtures to use the required-field ctor consistently, (4) delete default ctor or mark `= delete`, (5) verify SPSC ring slot init still works (likely via `std::array<SubmitCommand, N>{}` with `noinit` policy or explicit `slot.reset()` calls).
- **Trigger:** **after C++20 upgrade ships** (TECH_DEBT-073). Not before; the discipline is C++20-dependent.
- **Status:** OPEN (waiting on C++20 upgrade)
- **Cross-ref:** `CoreFrameworks/SubmitCommand.hpp` (POD definition + dual ctor); `CoreFrameworks/ShardedLiveSafety.hpp::ShardedLiveSafety_PreSubmitGate` (runtime guard); TECH_DEBT-073 (C++20 upgrade); `DESIGN_SPECS/refactor-patterns/cfg-scope-discipline.md` § "Consumer function signatures over per-core slices" (sibling discipline at the cfg layer); `DESIGN_PHILOSOPHY.md` § 8 Failure observability — runtime guards as the C++17-compatible expression of compile-time-preferred invariants.

---

### TECH_DEBT-071 — Portfolio_OpenSlot / CloseSlot + TradeLog_Record* mask-param refactor (Pattern 5 alternative)

```yaml
id: TECH_DEBT-071
title: Portfolio_OpenSlot / CloseSlot + TradeLog_Record* mask-param refactor (Pattern 5 alternative)
severity: low
surface_tags: [oms-drainer, slow-path]
trigger: paper-test
status: open
opened: 2026-05-15
related_specs: [DESIGN_SPECS/framework-patterns/sink-fn-pointer-for-optional-side-effect-pattern.md, DESIGN_SPECS/refactor-patterns/branchless-dispatch-discipline.md]
```

- **Created:** 2026-05-15 by v5.15.5.F.4c.3 WIP2d-1.B.1 (during architectural decision for trade_log + calibration_log emit branch elimination; option B "mask params at call sites" considered but rejected in favor of option C "Pattern 5 sink-fn-pointer").
- **Severity:** LOW (Pattern 5 sink-fn-pointer is already deployed; this is an alternative shape to evaluate post-paper-test).
- **Surface:** `CoreFrameworks/Portfolio.hpp::Portfolio_OpenSlot / Portfolio_CloseSlot` + `CoreFrameworks/TradeLog.hpp::TradeLog_RecordEntry / TradeLog_RecordExit`. Today: Pattern 5 sink-fn-pointer dispatches via `on_entry_fill_emit / on_exit_fill_emit / on_exit_calibration` fn-pointer fields in OmsState, with `noop_fill_emit` as default and `real_*` attached at boot when log paths are configured.
- **What's deferred:** alternative shape — pass a "did this fill open/close a slot" mask BACK from Portfolio_OpenSlot/CloseSlot to the caller, and have the caller branchless-dispatch via mask AND'd against `trade_log_enabled` + `calibration_log_enabled` bitmap fields. Both Pattern 5 and mask-param eliminate the per-fill `if (sink_attached)` branch; mask-param keeps the call-graph flatter (no fn-pointer indirection at the per-fill site) at the cost of widening Portfolio_OpenSlot/CloseSlot signatures and threading mask-flag bookkeeping through HandleFill.
- **Why deferred:** Pattern 5 was chosen at .F.4c.3 because it composes cleanly with the "subsystem state owns its own dispatch policy" principle (OmsState owns its own emit fn-pointers; Portfolio/TradeLog stay narrow). Mask-param would invert that — Portfolio would emit "I opened slot S" bits and the caller would do the multiplexing. Pattern 5 reads cleaner; mask-param may benchmark faster (one less L1d indirect-call line). Without benchmark data we picked the cleaner-reading option; defer the eval until paper-test or live-readiness profiling provides a measurement.
- **Cost estimate:** ~6-8h if pursued. Signature widening (~10 callsites for Portfolio_OpenSlot/CloseSlot) + bitmap encoding for mask-return + ~3 paper-test fixtures to compare branchy vs Pattern 5 vs mask-param on real ticks.
- **Trigger:** **after paper-test data + live-readiness profile data exists** (paper-test session post-v5.15 close OR live-readiness ship). Pursue only if Pattern 5's L1d indirect-call cost shows up as a measurable per-fill penalty (>1% of slow-path budget); otherwise keep Pattern 5.
- **Status:** OPEN (evaluation; not actionable until measurement data exists)
- **Cross-ref:** `DESIGN_SPECS/framework-patterns/sink-fn-pointer-for-optional-side-effect-pattern.md` (Pattern 5 canonical); `DESIGN_SPECS/refactor-patterns/branchless-dispatch-discipline.md` § Pattern 3 (mask-select sub-variants); `CoreFrameworks/OrderManager.hpp` (current Pattern 5 deployment); `DESIGN_PHILOSOPHY.md` § 4 Latency cost framework — when to choose fn-pointer vs mask-param.

---

### TECH_DEBT-072 — Reconcile_ApplyMissedFills exchange-fee-from-source corner case (fully-released Orders fall back to cores[0])

```yaml
id: TECH_DEBT-072
title: Reconcile_ApplyMissedFills exchange-fee-from-source corner case (fully-released Orders fall back to cores[0])
severity: medium
surface_tags: [live-trading, oms-drainer]
trigger: sub-ship-live-readiness
status: open
opened: 2026-05-15
related_specs: [DESIGN_SPECS/refactor-patterns/cfg-scope-discipline.md]
```

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
- **Cross-ref:** `CoreFrameworks/Reconcile.hpp::Reconcile_ApplyMissedFills` (current bitmap-search + cores[0] fallback); `CoreFrameworks/Order.hpp::pre_resolved` sub-struct (the field would live here); `DataStream/BinanceOrderAPI.hpp` (audit source for exchange-reported fee format); `DESIGN_SPECS/refactor-patterns/cfg-scope-discipline.md` § "Recovery-path nullable pointer" (Reconcile's binding shape spec); Class 29 (the broader pre-resolution discipline that this corner case is the edge of).

---

### TECH_DEBT-073 — C++20 upgrade ship (post-v5.15 umbrella)

```yaml
id: TECH_DEBT-073
title: C++20 upgrade ship (post-v5.15 umbrella)
severity: medium
surface_tags: [boot-time, ci-tooling, test-infrastructure]
trigger: sub-ship-v5.16
status: open
opened: 2026-05-15
related_specs: []
```

- **Created:** 2026-05-15 by v5.15.5.F.4c.3 WIP2d-1.B.1 (deferred C++17→C++20 upgrade after C++17 friend-scope wall on SubmitCommand option A; multiple downstream tech debt items depend on C++20 features).
- **Severity:** MEDIUM (infrastructure upgrade; unlocks several deferred items + new branchless patterns; not blocking immediate work but unlocks structural-enforcement options not expressible in C++17).
- **Surface:** entire codebase — build flags (`-std=c++20`), compiler version pin (gcc 12+), `<bit>` header replaces `__builtin_*` intrinsic usage, `[[likely]]`/`[[unlikely]]` annotations replace `__builtin_expect`, `concepts` enable compile-time required-field enforcement, designated-init for clearer struct construction, `<source_location>` for richer assert messages, `consteval` for compile-time-guaranteed evaluation (vs constexpr's "could be runtime"), 3-way comparison operator `<=>` for byte-equivalence contexts (H10/H12 sites).
- **What's deferred:** dedicated infrastructure ship that bumps `-std=c++17` → `-std=c++20` across all build flavors, audits and updates the codebase for new C++20 patterns where they unlock structural-enforcement options. NOT a "convert everything to C++20 idioms" sweep — only sites where C++20 enables a deferred discipline (TECH_DEBT-070 SubmitCommand required-field; future ML capability concepts; future strategy-interface concept-constrained dispatch). Other C++17 code stays as-is.
- **Why deferred (not effort-avoidance):** C++20 upgrade is genuinely a dedicated infrastructure ship — touches build flags, compiler dependency, all 6 build dirs (build/, build_gui/, build_suite/, build_lat/, build_tsan/, build_asan/), CI image, dev-machine compiler version. Cross-cutting; must be its own ship for proper rollback anchor. Several TECH_DEBT items (TECH_DEBT-070 SubmitCommand; future ML concepts) explicitly depend on C++20 features. Doing the upgrade ship FIRST unblocks 2-3 downstream items.
- **Cost estimate:** ~16-24h focused. Phase 1: build flag flip + per-build-dir verification (~4h). Phase 2: existing-code audit for C++17/C++20 incompatibilities (rare; standard library mostly forward-compat but some patterns shift) + fix any (~6h). Phase 3: opportunistic upgrades at sites where C++20 unlocks a deferred discipline (~6-10h, focused on TECH_DEBT-070 first canonical). Phase 4: test sweep + paper-test verification (~2-4h).
- **Trigger:** **after v5.15 umbrella closes** (sprint state confirmed; current sprint stays C++17). Dedicated infrastructure ship; should be its own version (e.g., `v5.16.0` or `v5.15.6.A` depending on umbrella sequencing). Operator decision on naming + timing.
- **Status:** OPEN (queued for post-v5.15 umbrella; sequenced after live-readiness operational items if those are higher priority)
- **Cross-ref:** TECH_DEBT-070 (SubmitCommand required-field enforcement; first canonical C++20 unlock); `CoreFrameworks/SubmitCommand.hpp` (target of first C++20-enabled refactor); `DESIGN_PHILOSOPHY.md` § 11 Process discipline (upgrade-as-dedicated-ship); CLAUDE.md "Build" section (build flag references); `build.sh` (C++ standard flag).

---

### TECH_DEBT-074 — Future `DOCS/DATA_FLOW.md` doc (proposed during .F.4c.4 planning; defer to post-v5.15 umbrella close)

```yaml
id: TECH_DEBT-074
title: Future DOCS/DATA_FLOW.md doc
severity: low
surface_tags: []
trigger: sub-ship-post-v5.15
status: open
opened: 2026-05-16
related_specs: []
```

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
- **Cross-ref:** `DOCS/CODE_MAP.md` (existing module-level catalog); `DOCS/COMPONENTS.md` (component breakdown); `DOCS/ARCHITECTURE.md` (high-level diagram); `DOCS/CLAUDE_INTEGRATION.md` (how-to-add-X recipes); `DOCS/EXECUTION_DISPLAY_INVARIANTS.md` (display↔execution discipline); CLAUDE.md "Architecture (sharded)" section (high-level data flow already documented); `DESIGN_SPECS/refactor-patterns/cfg-scope-discipline.md` + `DESIGN_SPECS/refactor-patterns/decision-time-data-binding-pattern.md` + `DESIGN_SPECS/framework-patterns/sink-fn-pointer-for-optional-side-effect-pattern.md` (key boundary discipline references).

---

### TECH_DEBT-076 — `.F.4c.3` deferred WIP2d-1.B.2/B.3/B.4 — ControllerEventLoop + EngineSharded + Backtest wrapper migrations

```yaml
id: TECH_DEBT-076
title: .F.4c.3 deferred WIP2d-1.B.2/B.3/B.4 — ControllerEventLoop + EngineSharded + Backtest wrapper migrations
severity: medium
surface_tags: [slow-path, cfg-flow, backtest]
trigger: sub-ship-.F.4f
status: open
opened: 2026-05-16
related_specs: [DESIGN_SPECS/refactor-patterns/cfg-scope-discipline.md]
```

- **Created:** 2026-05-16 (backfill per `.F.4d` pre-coding verification audit; `.F.4c.3` ship shipped ~60% of original subplan scope and postmortem was silent on this deferred phase)
- **Severity:** MEDIUM (cleanup discipline; not blocking new framework work)
- **Surface:** ControllerEventLoop wrapper sites (per-core slice param threading; complete the single-param consumer sig discipline established at WIP2c.0/2c.2); EngineSharded boot default paths; Backtest path equivalents. Specific sites enumerated in the original `.F.4c.3` subplan body (Steps 4-7 region).
- **What's deferred:** finish applying single-param `const PerCoreCfg<F>*` discipline to remaining ControllerEventLoop wrapper sites + EngineSharded boot defaults that still read flat `cfg.X` instead of per-core sliced `core_cfg->X`. ~10-15 sites estimated.
- **Why deferred (not effort-avoidance):** `.F.4c.3` scope-shifted mid-flight to absorb the OMS structural closure (Class 27/28/29 + comprehensively branchless OrderManager) when DrainPostFill recompute-from-cfg gap surfaced; the WIP2d-1.B.2/B.3/B.4 wrapper migrations were the next-planned phase but pushed to keep ship boundary focused. Code at HEAD is functional via `ControllerConfig_PopulateCoresFromFlat` shadow walker.
- **Cost estimate:** ~4-6h focused (mechanical migration; sister-canonical pattern to Class 25 sweep at `.F.4c.3`).
- **Trigger:** Bundle with WIP2e+f+g/h into single cleanup ship (`.F.4f` or `.F.5-pre`) post-`.F.4d` per operator decision 2026-05-16 ("finish current then do incomplete items").
- **Status:** OPEN (queued for cleanup ship post-`.F.4d`)
- **Cross-ref:** `.F.4c.3` subplan + postmortem § "Deferred from original subplan scope" (added 2026-05-16); CLAUDE.md item 19 (structural fix preferred); `DESIGN_SPECS/refactor-patterns/cfg-scope-discipline.md` § "Consumer over per-core array" + "single-param sig discipline".

---

### TECH_DEBT-077 — `.F.4c.3` deferred WIP2e — A2 bitmap-bool migration (28 KIND_BOOL flat rows → domain bitmaps)

```yaml
id: TECH_DEBT-077
title: .F.4c.3 deferred WIP2e — A2 bitmap-bool migration (28 KIND_BOOL flat rows → domain bitmaps)
severity: medium
surface_tags: [bitmap-packed, cfg-flow, registry]
trigger: sub-ship-.F.4f
status: open
opened: 2026-05-16
related_specs: [DESIGN_SPECS/framework-patterns/bitmap-flag-api.md, DESIGN_SPECS/framework-patterns/universal-registry-bitmap-dispatcher-pattern.md, DESIGN_SPECS/refactor-patterns/cfg-flag-eligibility-criteria.md]
```

- **Created:** 2026-05-16 (backfill per `.F.4d` pre-coding verification audit)
- **Severity:** MEDIUM (cohort-harmonization discipline; partial coverage today)
- **Surface:** Remaining 28 KIND_BOOL flat cfg rows that should migrate to domain bitmaps (`ml_cfg_flags`, `lifecycle_cfg_flags`, etc.) per the bitmap-dispatcher framework established at `.F.4c`. Specific rows enumerated in original `.F.4c.3` subplan WIP2e section.
- **What's deferred:** identify candidate KIND_BOOL rows (those that pass cfg-flag-eligibility criteria per `DESIGN_SPECS/refactor-patterns/cfg-flag-eligibility-criteria.md`); migrate from `KIND_BOOL` direct-int storage to bitmap-bit storage in appropriate domain (`ml_cfg_flags` or `lifecycle_cfg_flags` or new domain).
- **Why deferred (not effort-avoidance):** `.F.4c.3` shipped the higher-priority registry-split framework infrastructure (WIP1-WIP2d) + emergent OMS work; cohort-uniform bool migration was the next phase.
- **Cost estimate:** ~3-4h focused (mechanical per-flag migration via established bitmap-dispatcher pattern; ~28 rows; sister to `.F.4c.1`'s 18-row STAMP_BOUND cohort migration).
- **Trigger:** Bundle with WIP2d-1.B.2/B.3/B.4 + WIP2f + WIP2g/h into single cleanup ship post-`.F.4d`.
- **Status:** OPEN (queued for cleanup ship post-`.F.4d`)
- **Cross-ref:** `DESIGN_SPECS/framework-patterns/bitmap-flag-api.md`; `DESIGN_SPECS/framework-patterns/universal-registry-bitmap-dispatcher-pattern.md`; `DESIGN_SPECS/refactor-patterns/cfg-flag-eligibility-criteria.md`; TECH_DEBT-013 (BIT_FLAG storage class win for bool patterns) CLOSED at v5.14.9.

---

### TECH_DEBT-078 — `.F.4c.3` deferred WIP2f — Legacy `PerCoreOverrides<F>` + `ControllerConfig_ResolveForCore` + `core_overrides[16]` deletion

```yaml
id: TECH_DEBT-078
title: .F.4c.3 deferred WIP2f — Legacy PerCoreOverrides<F> + ControllerConfig_ResolveForCore + core_overrides[16] deletion
severity: high
surface_tags: [cfg-flow, registry]
trigger: sub-ship-.F.4f
status: open
opened: 2026-05-16
related_specs: [DESIGN_SPECS/refactor-patterns/cfg-scope-discipline.md]
```

- **Created:** 2026-05-16 (backfill per `.F.4d` pre-coding verification audit)
- **Severity:** MEDIUM-HIGH (transitional infrastructure should not persist long-term; can confuse contributors)
- **Surface:** `CoreFrameworks/ControllerConfig.hpp` — `PerCoreOverrides<F>` struct definition (~255) + `ControllerConfig_ResolveForCore` function (~1404) + `core_overrides[16]` field on ControllerConfig + all caller sites still using `ResolveForCore` resolution path.
- **What's deferred:** Mark `PerCoreOverrides<F>` + `ControllerConfig_ResolveForCore` as legacy in `.F.4c.3`'s WIP2f phase but not actually deleted. The `PerCoreCfg<F>` struct + `ControllerConfig_PopulateCoresFromFlat` shadow walker are the new canonical infrastructure; legacy path still works but should be retired. Comment at `CfgFieldRegistry.hpp:700` says "TRANSITIONAL — delete at WIP2f".
- **Why deferred (not effort-avoidance):** WIP2f deletion requires all consumer sites to migrate first (WIP2d-1.B.2/B.3/B.4 per TECH_DEBT-076 + test fixture migrations per TECH_DEBT-079). Deletion CANNOT happen before consumer migration completes (forward dependency).
- **Cost estimate:** ~2-3h focused (after WIP2d-1.B.2/B.3/B.4 + WIP2g/h consumer migrations complete; deletion itself is mechanical).
- **Trigger:** AFTER TECH_DEBT-076 + TECH_DEBT-079 close (dependency chain). Sequenced into cleanup ship post-`.F.4d`.
- **Status:** OPEN (queued for cleanup ship post-`.F.4d`; sequenced after TECH_DEBT-076 + TECH_DEBT-079 within ship)
- **Cross-ref:** `.F.4c.3` subplan WIP2f section; CLAUDE.md item 13 (single source of truth via X-macro); `DESIGN_SPECS/refactor-patterns/cfg-scope-discipline.md` (canonical PerCoreCfg<F> single-param sig discipline supersedes ResolveForCore resolver pattern).

---

### TECH_DEBT-079 — `.F.4c.3` deferred WIP2g/h — Atomic flag-day (89 flat field declarations + ~414 test fixture migrations + 9 band-aid call removals)

```yaml
id: TECH_DEBT-079
title: .F.4c.3 deferred WIP2g/h — Atomic flag-day (89 flat field declarations + ~414 test fixture migrations + 9 band-aid call removals)
severity: high
surface_tags: [cfg-flow, test-infrastructure, registry]
trigger: sub-ship-.F.4f
status: open
opened: 2026-05-16
related_specs: []
```

- **Created:** 2026-05-16 (backfill per `.F.4d` pre-coding verification audit)
- **Severity:** HIGH (largest deferred scope from `.F.4c.3`; ~414 test fixture writes still target legacy flat fields; transitional infrastructure persists)
- **Surface:** ControllerConfig struct (89 flat per-core field declarations like `int core_0_strategy`, `FPN<F> core_0_risk_pct`, etc.); test fixtures across `tests/controller_test.cpp` + sister test files (~414 write sites that target flat fields); 7-9 band-aid `ControllerConfig_PopulateCoresFromFlat(&cfg)` call-sites in tests; final cleanup at consumer sites that still read flat fields.
- **What's deferred:** Atomic flag-day deletion of all 89 flat field declarations from ControllerConfig + sweep migration of ~414 test fixture writes from `cfg.core_0_X = Y` shape to `cfg.cores[0].X = Y` shape + remove the 7-9 band-aid `PopulateCoresFromFlat` calls. After flag-day, the shadow walker becomes orphaned + can be deleted; legacy flat fields gone; PerCoreCfg<F> is sole source-of-truth.
- **Why deferred (not effort-avoidance):** ~414 test fixture writes is a significant migration scope; deferring kept `.F.4c.3` ship boundary focused on framework infrastructure + emergent OMS work. Mechanical migration but high-touch; flag-day discipline (atomic switch + test sweep) is its own focused effort.
- **Cost estimate:** ~6-10h focused (mostly mechanical sed-style migration with verification; risk of breaking tests if migration is imprecise — needs careful per-fixture verification).
- **Trigger:** Bundle with TECH_DEBT-076 + TECH_DEBT-077 + TECH_DEBT-078 into single cleanup ship post-`.F.4d`.
- **Status:** OPEN (queued for cleanup ship post-`.F.4d`)
- **Cross-ref:** `.F.4c.3` subplan WIP2g/h section; CLAUDE.md item 13 (single source of truth); test file size discipline note in CLAUDE.md (tests may get split during this migration if controller_test.cpp grows further).

---

### TECH_DEBT-080 — `.F.4c.3` deferred `[core N]` section parser syntax (operator-facing cfg syntax)

```yaml
id: TECH_DEBT-080
title: .F.4c.3 deferred [core N] section parser syntax (operator-facing cfg syntax)
severity: medium
surface_tags: [parser, cfg-flow]
trigger: sub-ship-.F.4f
status: open
opened: 2026-05-16
related_specs: [DESIGN_SPECS/refactor-patterns/cfg-scope-discipline.md]
```

- **Created:** 2026-05-16 (backfill per `.F.4d` pre-coding verification audit)
- **Severity:** MEDIUM (operator UX improvement; current flat-prefix syntax works but verbose)
- **Surface:** `CoreFrameworks/ControllerConfigParser.hpp` parser; `engine.cfg` example documentation. In-code comment at `ControllerConfig.hpp:2097` explicitly says "Future ship .F.4c.3 Step 3 introduces [core N] section parser".
- **What's deferred:** Add `[core 0]`, `[core 1]`, ... section header syntax to engine.cfg parser. Operator writes section-scoped key=value lines instead of verbose `core_N_X=Y` flat-prefix form. Parser detects `[core N]` header + scopes subsequent key=value lines until next section header or EOF.
- **Why deferred (not effort-avoidance):** Operator UX improvement; not load-bearing for framework correctness. Original `.F.4c.3` Step 3 planned this; ship boundary refocused on infrastructure + OMS work.
- **Cost estimate:** ~2-3h focused (parser changes + cfg.example doc + test coverage).
- **Trigger:** Bundle with WIP2g/h flag-day (TECH_DEBT-079) OR can stand alone post-flag-day. Operator-facing change; should ship with documented migration path (legacy flat-prefix syntax stays acceptable post-shipping; section syntax is sugar).
- **Status:** OPEN (queued for cleanup ship post-`.F.4d`)
- **Cross-ref:** in-code TODO at `ControllerConfig.hpp:2097`; `.F.4c.3` subplan Step 3 section; `DESIGN_SPECS/refactor-patterns/cfg-scope-discipline.md`.

---

### TECH_DEBT-075 — HP_REFACTOR.md O1-O6 bridge entry (cache-audit observations; profile-driven deferral)

```yaml
id: TECH_DEBT-075
title: HP_REFACTOR.md O1-O6 bridge entry (cache-audit observations; profile-driven deferral)
severity: low
surface_tags: [hot-path, slow-path, oms-drainer, ml-inference]
trigger: paper-test
status: open
opened: 2026-05-16
related_specs: [DESIGN_SPECS/refactor-patterns/branchless-dispatch-discipline.md]
```

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
- **Cross-ref:** `tick-trader-percore-workspace/DOCS/HP_REFACTOR.md` (scope document with full observation bodies + triggers); `tick-trader-percore-workspace/DOCS/DESIGN_PHILOSOPHY.md` § 4 Latency cost framework; `DOCS/STRATEGY_AND_CODING_RULES.md` (private; H7+H8 hot path invariants); `plans/_cross-cutting/2026-05-06-latency-path-discipline.md` (7 latency-path rules + anti-pattern history); `DESIGN_SPECS/refactor-patterns/branchless-dispatch-discipline.md`; `feedback_no_defer_for_effort` (operator framing — defer is last-ditch); auto-write contract per `CLAUDE.local.md` "Deferred items → DOCS/TECH_DEBT.md" rule (set 2026-05-09).

---

### TECH_DEBT-081 — `.F.4c.3.A` deferred symbol-axis full migration (KIND_STRING + multi-symbol DataStream + ~9 BinanceConfig.symbol consumer migration)

```yaml
id: TECH_DEBT-081
title: .F.4c.3.A deferred symbol-axis full migration (KIND_STRING + multi-symbol DataStream + ~9 BinanceConfig.symbol consumer migration)
severity: medium
surface_tags: [cfg-flow, producer, parser, registry]
trigger: sub-ship-.F.4e
status: open
opened: 2026-05-16
related_specs: [DESIGN_SPECS/refactor-patterns/cfg-scope-discipline.md]
```

- **Created:** 2026-05-16 (backfill per `.F.4d` pre-coding subplan verification audit; `.F.4c.3.A` plan body self-marked PARTIAL but residual deferred work was not in TECH_DEBT ledger — invisible to `/readiness` Check 25)
- **Severity:** MEDIUM (canonical-shape discipline; symbol axis is single-symbol today via `BinanceConfig.symbol`; per-core symbol heterogeneity is a multi-symbol DataStream extension that depends on `.F.4e` KIND_STRING infrastructure)
- **Surface:** `DataStream/BinanceCrypto.hpp:64` (`BinanceConfig.symbol` global) + `CoreFrameworks/EngineSharded.hpp` (~9 consumer sites that read `BinanceConfig.symbol`) + per-core stamp body (symbol-axis-aware stamp emit) + Backtest path (symbol-aware load). Specific sites enumerated in `.F.4c.3.A` partial-stage subplan body.
- **What's deferred:** Full per-core symbol-axis migration from MANUAL exemption (landed at WIP2d-1.A) to canonical KIND_STRING `FOREACH_PER_CORE_CFG_FIELD` form. Items: (1) KIND_STRING infrastructure (depends on `.F.4e`); (2) per-core symbol UI design (multi-string entry tab); (3) validated-list source (Binance symbol catalog ingestion); (4) multi-symbol DataStream design (one BinanceCrypto stream per unique core symbol, OR one stream filtered per core); (5) per-core stamp body (model stamps `core_N_symbol`); (6) BinanceConfig.symbol consumer migration (~9 sites in EngineSharded.hpp + Backtest path).
- **Why deferred (not effort-avoidance):** WIP2d-1.A landed the MANUAL exemption + boot-uniformity check at `.F.4c.3` (closed the cfg-surface shape gap structurally — `core_symbol[16][32]` field exists + per-core parser case exists + boot check verifies cross-core uniformity until KIND_STRING infrastructure lands). Full migration depends on `.F.4e` KIND_STRING + multi-symbol DataStream redesign + symbol axis UI — each is its own focused work that warrants its own ship boundary.
- **Cost estimate:** ~4-8h focused (varies on multi-symbol DataStream scope). Could split: KIND_STRING migration of `core_symbol` (~1h after `.F.4e` ships) + consumer migration sweep (~2-3h) + multi-symbol DataStream design + impl (~2-4h, dominant cost).
- **Trigger:** **after `.F.4e` ships** (KIND_STRING infrastructure dependency); cleanup ship `.F.4f` OR standalone follow-on (operator decision based on scope appetite).
- **Status:** OPEN (queued post-`.F.4e`)
- **Cross-ref:** `plans/v5.15-live-readiness/subplans/2026-05-15-v5.15.5.F.4c.3.A-symbol-axis-per-core-migration.md` (partial-stage plan; documents deferred items inline); commit `4c6b150 v5.15.5.F.4c.3 WIP2d-1.A: Symbol axis MANUAL exemption (partial .F.4c.3.A advance)`; `MANUAL_FIELDS_INVENTORY.md` Section A `core_symbol[16][32]` entry (migration trigger documented inline); `DataStream/BinanceCrypto.hpp:64` (BinanceConfig.symbol declaration); CLAUDE.md item 19 (structural fix preferred); `DESIGN_SPECS/refactor-patterns/cfg-scope-discipline.md`.

---

### TECH_DEBT-085 — Thread A FULL framework consolidation (DerivedFilterFramework + 24-row migration + sidecar override + bit-packed inventory + CI 9-12 + Layer 5b + ML_CFG_FLAG sig migration + v5.14 fixture regression)

```yaml
id: TECH_DEBT-085
title: Thread A FULL framework consolidation (DerivedFilterFramework + 24-row migration + sidecar override + bit-packed inventory + CI 9-12 + Layer 5b + ML_CFG_FLAG sig migration + v5.14 fixture regression)
severity: medium
surface_tags: [registry, wire-format, cfg-flow, ml-inference, bitmap-packed, ci-tooling]
trigger: sub-ship-.F.4d.1
status: open
opened: 2026-05-16
related_specs: [DESIGN_SPECS/framework-patterns/metadata-bit-driven-derived-filter-framework.md, DESIGN_SPECS/framework-patterns/sidecar-override-pattern-for-registry-auto-flows.md, DESIGN_SPECS/framework-patterns/meta-registry-pattern-for-codebase-registry-discipline.md, DESIGN_SPECS/framework-patterns/framework-composition-overview.md]
```

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
- **Cross-ref:** `subplans/2026-05-16-v5.15.5.F.4d-merged-framework-bandit-thompson.md` Thread A Charters 8-14 (full design); `DESIGN_SPECS/framework-patterns/metadata-bit-driven-derived-filter-framework.md` Stage 3 ACTIVE (mechanism specification — Option B runtime walk filtering on metadata bit); `DESIGN_SPECS/framework-patterns/sidecar-override-pattern-for-registry-auto-flows.md` Stage 3 ACTIVE (companion pattern for FOREACH_DRIFT_OVERRIDE); `DESIGN_SPECS/framework-patterns/meta-registry-pattern-for-codebase-registry-discipline.md` Stage 3 ACTIVE (H19 topology); `DESIGN_SPECS/framework-patterns/framework-composition-overview.md` Stage 3 ACTIVE (composition narrative); CLAUDE.md H15 + H16 + H17 + H18 + H19 (codified .F.4d 2026-05-16); CLAUDE.md item 31 (framework-driven extensibility meta-principle); commit `de41ff2 v5.15.5.F.4d MERGED WIP-checkpoint: Thread A foundation — STAMP_BOUND_CFG_DERIVED metadata bit (bit 13)`.

---

### TECH_DEBT-087 — Consumer-existence enforcement for FOREACH_METADATA_BIT rows

```yaml
id: TECH_DEBT-087
title: Consumer-existence enforcement for FOREACH_METADATA_BIT rows
severity: low
surface_tags: [ci-tooling, registry, cfg-flow]
trigger: sub-ship-.F.4e
status: open
opened: 2026-05-16
related_specs: [DESIGN_SPECS/framework-patterns/composed-filter-mask-pattern.md]
```

- **Created:** 2026-05-16 (at v5.15.5.F.4d.1.A pre-coding audit gate consult — Gap 2 from `plan_checks/2026-05-16-v5.15.5.F.4d.1-tech-debt-audit-findings.md`)
- **Severity:** LOW-MED (silent dead-infrastructure risk; not blocking; surfaces as orphan `.rodata` mask + tooltip-says-feature-exists-but-no-behavior class)
- **Surface:** NEW `tools/check_metadata_bit_consumer_coverage.py` (~80 LOC sister to existing `tools/check_meta_registry.py` + `tools/check_per_core_registry_integrity.py`); CI integration via `build.sh` pre-build invocation
- **What's deferred:** Build CI tool that scans codebase for `g_*_cfg_<bit>_mask` references (consumer sites). Reports each FOREACH_METADATA_BIT row's consumer count. WARN at 0-consumer (orphan mask infrastructure); ERROR if explicit EXEMPT list missing rationale. Sister discipline to H15 (registry enrollment) + H16 (bit-to-mask coverage) — closes the third invariant of the trio: H?? bit-to-consumer coverage.
- **Why deferred (not effort-avoidance):** Path γ at `.F.4d.1.A` adds STAMP_BOUND_CFG_DERIVED → `.B` consumers will exist immediately; no orphan risk in current ship. Risk emerges at `.F.4e` (5 GUI metadata bits) IF a bit is enrolled without its consumer landing same ship. Mitigation deferred to that ship's verification gate (TECH_DEBT-088 handles `.F.4e` specifically). General-purpose tool is Stage 7 wider audit — useful but not urgent.
- **Cost estimate:** ~2-3h (Python script + CI integration + test against existing FOREACH_METADATA_BIT rows). LOW risk (tool-only; no engine code touched).
- **Trigger:** Stage 7 wider audit candidate. Either: (a) `.F.4f` cleanup ship fold-in if catalog count + Caramel-discretion allows; OR (b) separate `tools/`-only mini-ship after `.F.4e` validates the pattern via 5 GUI metadata consumers; OR (c) bundle into TECH_DEBT-058 (REGISTRY_TOPOLOGY auto-gen) which has overlapping scope.
- **Status:** OPEN (logged at `.F.4d.1.A` planning; not addressed in current scope)
- **Cross-ref:** `plan_checks/2026-05-16-v5.15.5.F.4d.1-tech-debt-audit-findings.md` Gap 2 (origin); `tick-trader-percore-workspace/DESIGN_SPECS/framework-patterns/composed-filter-mask-pattern.md` Stage 2 DRAFT (sister — discipline applies to composed masks too); `tick-trader-percore-workspace/DESIGN_SPECS/wire-format-patterns/wire-format-canonical-body-invariants-helper.md` (companion); TECH_DEBT-058 (REGISTRY_TOPOLOGY auto-gen — overlapping scope candidate); `tools/check_meta_registry.py` + `tools/check_per_core_registry_integrity.py` (sister CI tools).

---

### TECH_DEBT-088 — `.F.4e` consumer verification gate

```yaml
id: TECH_DEBT-088
title: .F.4e consumer verification gate
severity: low
surface_tags: [ci-tooling, registry, gui-thread]
trigger: sub-ship-.F.4e
status: open
opened: 2026-05-16
related_specs: [DESIGN_SPECS/framework-patterns/composed-filter-mask-pattern.md]
```

- **Created:** 2026-05-16 (at v5.15.5.F.4d.1.A pre-coding audit gate consult — Gap 3 from `plan_checks/2026-05-16-v5.15.5.F.4d.1-tech-debt-audit-findings.md`)
- **Severity:** LOW (planning-time reminder; mechanical verification at ship-close cadence; ~5 min effort)
- **Surface:** `.F.4e` plan body when drafted — Verification Gate section gains consumer-existence checks for the 5 GUI metadata bits being enrolled (HIDDEN_BY_DEFAULT, RESTART_REQUIRED, SAFETY_CRITICAL, IS_SECRET, DEPRECATED). All 5 are already enrolled in FOREACH_METADATA_BIT today; `.F.4e` adds their consumers (GUI panel logic). Without verification: `.F.4e` could ship framework discipline followed but consumer behavior missing.
- **What's deferred:** `.F.4e` plan body adds grep verification at Step 7 (build verify + tag): confirm at least 1 consumer references each of `g_*_cfg_hidden_by_default_mask` + `g_*_cfg_restart_required_mask` + `g_*_cfg_safety_critical_mask` + `g_*_cfg_is_secret_mask` + `g_*_cfg_deprecated_mask` in non-CfgFieldRegistry code (i.e., NOT just the auto-generator itself). Subsumes TECH_DEBT-087 for the 5 `.F.4e` bits specifically.
- **Why deferred (not effort-avoidance):** Not deferring effort — deferring to the relevant ship's planning cycle. The check belongs in `.F.4e`'s verification gate (it's the ship adding consumers). `.A` Path γ scope doesn't include `.F.4e` planning. Adding to `.F.4e` planning notes (this TECH_DEBT entry) is the right boundary.
- **Cost estimate:** ~5 min at `.F.4e` planning time (add grep verification to plan body Verification Gate section) + ~5 min at `.F.4e` ship close (run grep verification).
- **Trigger:** `.F.4e` planning handoff session. Reminder: when drafting `.F.4e` plan body, include consumer-existence grep verification for each of the 5 GUI metadata bits. Reference this TECH_DEBT entry to confirm scope.
- **Status:** OPEN (logged at `.F.4d.1.A` planning; deferred to `.F.4e` planning time)
- **Cross-ref:** `plan_checks/2026-05-16-v5.15.5.F.4d.1-tech-debt-audit-findings.md` Gap 3 (origin); TECH_DEBT-087 (sister general-purpose CI tool; this entry is the specific `.F.4e` instance); `tick-trader-percore-workspace/DESIGN_SPECS/framework-patterns/composed-filter-mask-pattern.md` (`.F.4e` consumers will likely add new composed masks; composition audit checklist applies); CLAUDE.local.md ship-after sequencing table.

---

### TECH_DEBT-089 — DESIGN_SPECS spec-vs-code drift audit cadence

```yaml
id: TECH_DEBT-089
title: DESIGN_SPECS spec-vs-code drift audit cadence
severity: medium
surface_tags: [ci-tooling]
trigger: sub-ship-.F.4f
status: open
opened: 2026-05-16
related_specs: [DESIGN_SPECS/meta-disciplines/pattern-codification-lifecycle.md]
```

- **Created:** 2026-05-16 (at v5.15.5.F.4d.1.A pre-coding audit gate consult — Gap 4 META from `plan_checks/2026-05-16-v5.15.5.F.4d.1-tech-debt-audit-findings.md`)
- **Severity:** MED (this is the META-class — how we got into Path γ situation in the first place; spec-vs-code drift causes plan-time mechanism mistakes that audit catches but should be caught at spec-write time)
- **Surface:** All `tick-trader-percore-workspace/DESIGN_SPECS/*.md` files (~72 patterns at HEAD; ~25-30 Stage 2 DRAFT / Stage 3 ACTIVE specs are most at-risk; INVARIANT specs are stable; older specs land naturally aligned with code they describe)
- **What's deferred:** Full audit of all Stage 2/3 ACTIVE DESIGN_SPECs for spec-code alignment. Pattern that caused this: spec drafted at planning session OR retroactively codified, code shipped at different session, no reconciliation step verifies the spec describes the actual canonical mechanism. Result: future readers of spec believe Y mechanism is the canonical when actually Z exists. The `metadata-bit-driven-derived-filter-framework.md` Path γ correction is the FIRST instance discovered structurally; predicted N=2-5 more instances exist undiscovered. Also: codify periodic cadence discipline — spec-code reconciliation at sprint close OR at every Stage 2 → Stage 3 promotion (whichever comes first).
- **Why deferred (not effort-avoidance):** Substantial separate work (~2-3h initial sweep + ongoing cadence). Doesn't fit `.F.4d.1.A` scope (Path γ Level 2 is sub-ship-focused). Phase 2 of `.F.4d.1.A` session (Level 4 codebase pattern survey) includes D4 dimension which is a partial down-payment — scans for OTHER spec-code drift instances narrowly scoped to what relates to Path γ findings. Full sweep deferred for dedicated bandwidth.
- **Cost estimate:** ~2-3h initial sweep across all Stage 2/3 ACTIVE specs (~25-30 docs × ~5 min each); ~30 min periodic cadence at each sprint close OR Stage promotion. MED risk per-amendment (some discoveries may require spec-substantial rewrites; mitigated by per-spec scope).
- **Trigger:** Either: (a) `.F.4f` cleanup ship fold-in (spec drift is "cleanup" by another name); OR (b) separate `tick-trader-percore-workspace/`-only mini-ship; OR (c) periodic cadence as TECH_DEBT-058 (REGISTRY_TOPOLOGY auto-gen) sister discipline. Initial sweep first; ongoing cadence codified as DESIGN_SPECS hygiene rule afterward.
- **Status:** OPEN (logged at `.F.4d.1.A` planning; Phase 2 D4 dimension audit is partial down-payment scheduled for this session)
- **Cross-ref:** `plan_checks/2026-05-16-v5.15.5.F.4d.1-tech-debt-audit-findings.md` Gap 4 (origin); `tick-trader-percore-workspace/DESIGN_SPECS/meta-disciplines/pattern-codification-lifecycle.md` Stage 7 wider audit (parent discipline); `tick-trader-percore-workspace/DESIGN_SPECS/framework-patterns/metadata-bit-driven-derived-filter-framework.md` v1.2 Path γ correction (first canonical instance of spec-code drift correction); `tick-trader-percore-workspace/DESIGN_SPECS/framework-patterns/framework-composition-overview.md` v1.1 Path γ correction (second instance same session); CLAUDE.md item 19 (structural fix preferred — applies at META level: codify the cadence so spec-code drift can't accumulate).

---

### TECH_DEBT-090 — Categorical applicability mask precomputation (`applies_to_*_cat` cohorts)

```yaml
id: TECH_DEBT-090
title: Categorical applicability mask precomputation (applies_to_*_cat cohorts)
severity: medium
surface_tags: [cfg-flow, registry, gui-thread, slow-path, bitmap-packed]
trigger: sub-ship-.F.4f
status: open
opened: 2026-05-16
related_specs: [DESIGN_SPECS/framework-patterns/composed-filter-mask-pattern.md, DESIGN_SPECS/framework-patterns/categorical-tag-applicability-pattern.md]
```

- **Created:** 2026-05-16 (at v5.15.5.F.4d.1.A pre-coding audit gate consult — Path γ sister-cohort retrofit candidate from `plan_checks/2026-05-16-v5.15.5.F.4d.1-tech-debt-audit-findings.md`)
- **Severity:** MED (latent latency cost — categorical gating currently does per-row AND at consumer sites; precomputed masks eliminate per-row branching; aligned with H7 + H20 branchless discipline for slow-path consumers; sister to Path γ at `.A`)
- **Surface:** `CoreFrameworks/CfgFieldRegistry.hpp` — sister precomputed-mask infrastructure for `applies_to_strategy_cat` + `applies_to_op_mode_cat` + `applies_to_regime_cat` + `applies_to_risk_cat` enum-bitmap fields per `categorical-tag-applicability-pattern.md`. Existing `FOREACH_LIVES_IN_STRUCT` masks at lines 1099-1133 are precedent for the enum-value-driven version of the pattern. Categorical applicability could follow same shape but per-categorical-enum-value (e.g., `g_*_cfg_applies_strat_ml_mask` = mask of rows where `applies_to_strategy_cat & STRAT_CAT_ML != 0`).
- **What's deferred:** Build precomputed-mask infrastructure for 4 categorical applicability cohorts. Each cohort has N enum values (e.g., STRAT_CAT_ML / STRAT_CAT_SIMPLE_DIP / STRAT_CAT_MOMENTUM / STRAT_CAT_EMA_CROSS / STRAT_CAT_MEAN_REV / STRAT_CAT_AUTO / STRAT_CAT_USES_BANDIT). Per cohort: ~N masks × 2 registries = ~2N precomputed `CfgMaskArray<N_WORDS>` constants in `.rodata`. Total cost: ~30-40 LOC per cohort × 4 cohorts = ~120-160 LOC. Consumer migrations replace per-row `(desc.applies_to_*_cat & TOKEN_X) != 0` predicates with `CFG_FIELD_FOR_EACH_SET_BIT(g_*_cfg_applies_<cohort>_<value>_mask.words, idx, { ... })`. Live consumers: GUI section filtering (`SettingsPanel.hpp`); per-strategy cfg gating at parser/save paths; future audit-gate consumers.
- **Why deferred (not effort-avoidance):** Path γ at `.A` scope is bounded to STAMP_BOUND_CFG_DERIVED + composition audit registry. Categorical applicability is the SISTER application that justifies the composed-filter-mask DESIGN_SPEC's "future application candidates" section. Adding it at `.A` would scope-creep beyond Level 2; addressed at Level 3+ (sister-cohort retrofit Stage 7 wider audit).
- **Cost estimate:** ~3-5h focused (precomputed-mask infrastructure for 4 cohorts + consumer migration verification + tests). MED risk (touches GUI render path + cfg gating; pre-coding audit gate per cohort recommended).
- **Trigger:** Either: (a) `.F.4f` cleanup ship fold-in (sister Path γ-style refactor candidate); OR (b) separate sister-cohort retrofit ship after `.F.4e` ships (consumes the 5 GUI metadata bits + validates the consumer pattern at scale); OR (c) Phase 2 D3 audit dimension at `.F.4d.1.A` session may surface additional retrofit candidates that get bundled into one categorical-precomputation ship.
- **Status:** **OPEN — REFRAMED 2026-05-17** per Phase 2 D3 audit. Was originally "retrofit" framing assuming consumers exist; actually **GREENFIELD framework adoption** — ZERO production consumer sites do bitwise AND filtering on `applies_to_*_cat` fields (verified via `rg "applies_to_strategy_cat\s*&\s*STRAT_CAT"` returns 0). Columns are scaffolding awaiting first consumer. Effort revised ~3-5h → **~7-9h focused** (mask infra + consumer wiring + cohort audit). Top retrofit target: GUI section-filter migration at `SettingsPanel.hpp:1107,1143,1191-1204` (deprecate `per_core_field_strategy()` string-strncmp; migrate to categorical mask intersection — only operator-visible target). STRAT_CAT enum: 13 values × 2 registries = 26 mask declarations. OP_MODE_CAT: 5 values (degenerate today — 144/144 rows tagged ALL); REGIME_CAT + RISK_CAT: 0 named values (placeholder only). Kind enum dispatch ALREADY OPTIMAL (no retrofit needed; `if constexpr` per-row at `tt::cfg_parse_field<T>`).
- **Cross-ref:** `plan_checks/2026-05-16-v5.15.5.F.4d.1-tech-debt-audit-findings.md` sister-cohort retrofit candidate (origin); `plan_checks/d3-categorical-applicability-retrofit-scope-2026-05-16.md` (Phase 2 D3 audit with full enum value counts + consumer survey + revised effort); `tick-trader-percore-workspace/DESIGN_SPECS/framework-patterns/composed-filter-mask-pattern.md` Stage 2 DRAFT § "Future application candidates" (this is the candidate); `tick-trader-percore-workspace/DESIGN_SPECS/framework-patterns/categorical-tag-applicability-pattern.md` Stage 3 ACTIVE (parent pattern; codifies the categorical bitmap shape); `Strategies/StrategyCategories.hpp:27-50` (STRAT_CAT enum 13 values); `Strategies/OpModeCategories.hpp:19-28` (OP_MODE_CAT enum 5 values); `CfgFieldRegistry.hpp:1099-1133` (FOREACH_LIVES_IN_STRUCT — precedent for enum-value-driven precomputed masks); `GUI/SettingsPanel.hpp:1191-1204` (legacy string-strncmp section filter — migration target); CLAUDE.md item 31 (framework-driven extensibility — applies); H7 + H20 (branchless discipline benefit).

---

### TECH_DEBT-091 — Plan-context drift detection cadence (sister Class 18 mirror prevention at planning surface)

```yaml
id: TECH_DEBT-091
title: Plan-context drift detection cadence (sister Class 18 mirror prevention at planning surface)
severity: medium
surface_tags: [ci-tooling]
trigger: sub-ship-.F.4f
status: open
opened: 2026-05-17
related_specs: [DESIGN_SPECS/meta-disciplines/pattern-codification-lifecycle.md]
```

- **Created:** 2026-05-17 (at v5.15.5.F.4d.1.A Path γ+ v2 triage — Finding 5 from `plan_checks/2026-05-16-v5.15.5.F.4d.1-tech-debt-audit-findings.md` + plan-context-sweep audit recommendation)
- **Severity:** MED (recurrence prevention discipline; without it, future spec amendments will accumulate stale plan body references — same shape Path γ caught at `.A`/`.B`/`.D` body residuals)
- **Surface:** Process discipline + possible `/plan-context-sweep` skill enhancement to auto-fire after Stage 3 ACTIVE spec amendment
- **What's deferred:** Codify "after every Stage 3 ACTIVE spec amendment, sweep all queued sub-plans for SUPERSEDED spec mechanism references". Either: (a) embed in `pattern-codification-lifecycle.md` Stage 3 step as mandatory sub-step; (b) add `/plan-context-sweep` invocation as auto-fire trigger when a spec banner changes from "v1.x" → "v1.x+1 SUPERSEDED" or Stage 2 → Stage 3; (c) add to `/handoff` skill spec as planning-handoff verification check. Sister to TECH_DEBT-089 (DESIGN_SPECS drift audit cadence) at the planning surface vs spec surface.
- **Why deferred (not effort-avoidance):** Process discipline codification is best done after concrete recurrence pattern — `.F.4d.1.A` is the FIRST instance where this cadence would have caught drift (`.B`/`.B-examples`/`.D` body residuals + `.F.4e` Step 3 SUPERSEDED scope all caught by Phase 2 plan-context-sweep agent in this session). Codify at next sprint close OR at `.F.4f` cleanup ship.
- **Cost estimate:** ~1-2h focused (spec amendment to lifecycle.md + skill spec touch + CLAUDE.local.md going-forward rule entry). LOW risk (process; no code).
- **Trigger:** Stage 7 wider audit candidate OR `.F.4f` cleanup ship fold-in. Sister to TECH_DEBT-089.
- **Status:** OPEN (logged at `.F.4d.1.A` Path γ+ v2 triage 2026-05-17)
- **Cross-ref:** `plan_checks/2026-05-16-v5.15.5.F.4d.1-tech-debt-audit-findings.md` Finding 5 + Path γ+ v2 LOCKED scope (origin); `plan_checks/plan-context-sweep-2026-05-16-v5.15.5.F.4d.1.md` (canonical first invocation); TECH_DEBT-089 (sister DESIGN_SPECS spec-vs-code drift cadence; planning-surface vs spec-surface variant of same recurrence-prevention discipline); `tick-trader-percore-workspace/DESIGN_SPECS/meta-disciplines/pattern-codification-lifecycle.md` Stage 3 (potential codification site); CLAUDE.md item 19 (structural fix preferred — applies at meta-level: codify cadence so plan-context drift can't accumulate).

---

### TECH_DEBT-093 — `.B.2` deferral: `gap_acceptable_threshold` manual cfg storage cleanup (decl/default/parser)

```yaml
id: TECH_DEBT-093
title: .B.2 deferral — gap_acceptable_threshold manual cfg storage cleanup (decl/default/parser)
severity: low
surface_tags: [cfg-flow, parser, registry]
trigger: sub-ship-.B.3
status: open
opened: 2026-05-17
related_specs: [DESIGN_SPECS/refactor-patterns/cfg-scope-discipline.md]
```

- **Created:** 2026-05-17 (at `v5.15.5.F.4d.1.B.2` ship close per Caramel accountability pushback — "are we actually going to do the things you're deferring")
- **Severity:** LOW (no behavioral defect at HEAD; registry row added at `.B.2` provides descriptor + metadata bit + GUI auto-render; manual decl/default/parser stays but produces correct values)
- **Surface:** `CoreFrameworks/ControllerConfig.hpp:889` (manual decl `FPN<F> gap_acceptable_threshold`) + `:1729` (manual default `FPN_FromDouble<F>(0.05)`) + `:2554` (manual parser `CFG_PARSE_FPN(gap_acceptable_threshold)`)
- **What's deferred:** DELETE the 3 manual sites; rely on FOREACH_GLOBAL_CFG_FIELD struct-gen extension (currently absent — global registry only generates descriptor array + masks + GUI, NOT struct fields).
- **Why deferred (not effort-avoidance):** Coding-time Discovery 8 at `.B.2`: FOREACH_GLOBAL_CFG_FIELD does NOT auto-gen struct fields (only PerCoreCfg<F> auto-gens via FOREACH_PER_CORE_CFG_FIELD). Deletion at `.B.2` would leave `cfg.gap_acceptable_threshold` undefined → build breaks. Requires struct-gen extension to FOREACH_GLOBAL_CFG_FIELD per H17 ("ControllerConfig<F> cfg struct fields auto-generated from FOREACH_CFG_FIELD") — partial implementation today. Cleanup belongs with struct-gen extension landing.
- **Cost estimate:** ~30-45 min for `gap_acceptable_threshold`-specific deletion + ~2-3h for FOREACH_GLOBAL_CFG_FIELD struct-gen extension. Latter is wider scope.
- **Trigger:** `.B.3` Step 1.6.1 OR `.F.4f` cleanup ship (operator decision at `.B.3` planning: do here OR defer with H17 completion). `.B.3` cycle's pre-coding audit gate `/precoding-audit-gate` MUST verify decision documented.
- **Status:** OPEN (logged at `.B.2` ship close 2026-05-17)
- **Accountability mechanism:** `.B.3` plan body Step 1.6.1 explicitly enumerates this item; ship close postmortem MUST mark CLOSED or re-deferred with rationale + new target ship.
- **Cross-ref:** `plans/v5.15-live-readiness/postmortems/2026-05-17-v5.15.5.F.4d.1.B.2-postmortem.md` (Discovery 8); `subplans/2026-05-17-v5.15.5.F.4d.1.B.3-legacy-empty-out.md` Step 1.6.1; `tick-trader-percore-workspace/DESIGN_SPECS/refactor-patterns/cfg-scope-discipline.md` (override-inherit pattern documentation; sister discipline); CLAUDE.md H17 (cfg struct auto-gen invariant — partial at HEAD; .B.3 or .F.4f completes).

---

### TECH_DEBT-094 — `.B.2` deferral: 4 retroactive `.A.7` + bandit_blend_ratio bit-add + inf struct unification (5 fields)

```yaml
id: TECH_DEBT-094
title: .B.2 deferral — 4 retroactive .A.7 + bandit_blend_ratio bit-add + inf struct unification (5 fields)
severity: medium
surface_tags: [registry, ml-inference, wire-format, cfg-flow]
trigger: sub-ship-.B.3
status: open
opened: 2026-05-17
related_specs: []
```

- **Created:** 2026-05-17 (at `v5.15.5.F.4d.1.B.2` ship close per Caramel accountability pushback)
- **Severity:** MED (5 STAMP_BOUND-eligible fields cannot be framework-walked at `.B.2`; PARITY-024 retroactive scope partially open)
- **Surface:** `CoreFrameworks/CfgFieldRegistry.hpp:524-528 + :637` (5 master rows: `ml_tp_pct`, `ml_sl_pct`, `barrier_blend_mode`, `bandit_blend_ratio` — locate; `per_horizon_barrier_blend` in FOREACH_ML_CFG_FLAG at `MlCfgFlagRegistry.hpp:64`) — bit-add. Plus `StampInferenceCfgInputs` + `ModelStampResult` struct-gen at `ML_Headers/ModelInference.hpp:1199 + 1643` — inf struct unification (eliminate `inf.inference_cfg_<name>` prefix OR add unprefixed sister fields).
- **What's deferred:** Bit-add the 5 fields at master registry + inf struct unification at ModelInference.hpp struct-gen. Pre-condition: framework walker must access unprefixed `inf.<name>` (per Decision 5 prefix drop); currently 5 fields only have prefixed POST_CFG versions.
- **Why deferred (not effort-avoidance):** Coding-time Discovery 6 at `.B.2`: 5 fields have ONLY POST_CFG-prefixed inf fields; bit-adding at `.B.2` would cause framework walker to access non-existent `inf.<name>` → build breaks. Adding unprefixed inf fields manually at `.B.2` would create Class 18 mirror at struct layer (duplicate prefixed + unprefixed storage). `.B.3`'s legacy POST_CFG deletion is the natural unification point — eliminates prefixed; ADD unprefixed; cohort bit-add becomes clean.
- **Cost estimate:** ~30-45 min mechanical (bit-add + struct field rename/add) once `.B.3` legacy deletion forces the change.
- **Trigger:** `.B.3` Step 1.6.2 — paired with Step 2 POST_CFG deletion (legacy registry deletion at Step 2 forces this; build BREAKS if not addressed alongside).
- **Status:** OPEN (logged at `.B.2` ship close 2026-05-17)
- **Accountability mechanism:** `.B.3` plan body Step 1.6.2 explicitly enumerates; ship close postmortem MUST mark CLOSED; `.B.3` Step 2 legacy deletion FORCES this — build breaks if not addressed.
- **Cross-ref:** `plans/v5.15-live-readiness/postmortems/2026-05-17-v5.15.5.F.4d.1.B.2-postmortem.md` (Discovery 6); `subplans/2026-05-17-v5.15.5.F.4d.1.B.3-legacy-empty-out.md` Step 1.6.2; TECH_DEBT-100 (sister — same root cause for per_horizon_barrier_blend specifically); audit synthesis CRIT-CONV-2 / CRIT-CONV-5 / HIGH-CONV-F (sister scope items addressed at `.B.2`).

---

### TECH_DEBT-095 — `.B.2` deferral: ModelInference struct-gen migrations (3 sites)

```yaml
id: TECH_DEBT-095
title: .B.2 deferral — ModelInference struct-gen migrations (3 sites)
severity: high
surface_tags: [registry, ml-inference, wire-format, parser]
trigger: sub-ship-.B.3
status: open
opened: 2026-05-17
related_specs: []
```

- **Created:** 2026-05-17 (at `v5.15.5.F.4d.1.B.2` ship close per Caramel accountability pushback)
- **Severity:** MED-HIGH (production stamp emit path; coupled with legacy registry deletion)
- **Surface:** `ML_Headers/ModelInference.hpp:1199` (StampInferenceCfgInputs struct-gen via FOREACH_STAMP_BOUND_CFG); `:1401` (parser walker); `:1643` (ModelStampResult struct-gen)
- **What's deferred:** Replace FOREACH_STAMP_BOUND_CFG(X) walkers at all 3 sites with framework-driven walks over master registry filtered by STAMP_BOUND_CFG_DERIVED bit + FOREACH_ML_CFG_FLAG filtered by same bit. Coupled with TECH_DEBT-094 inf struct unification.
- **Why deferred (not effort-avoidance):** Struct-gen approach decision (Approach A unconditional generation / B macro-level filter / C defer) — unresolved at `.B.2`; deferring let us validate framework via other walker site migrations first. Now post-`.B.2` validation, Approach A (unconditional generation per Decision 5 prefix drop) is the natural choice for `.B.3`.
- **Cost estimate:** ~45-60 min mechanical (3 walker sites; X-macro filter pattern; struct-gen approach decision).
- **Trigger:** `.B.3` Step 1.6.3 — paired with Step 2 legacy registry deletion (Step 2 deletes FOREACH_STAMP_BOUND_CFG body → these 3 walkers reference deleted macro → build BREAKS without migration).
- **Status:** OPEN (logged at `.B.2` ship close 2026-05-17)
- **Accountability mechanism:** `.B.3` plan body Step 1.6.3 enumerates; `.B.3` Step 2 legacy deletion FORCES.
- **Cross-ref:** `plans/v5.15-live-readiness/postmortems/2026-05-17-v5.15.5.F.4d.1.B.2-postmortem.md`; `subplans/2026-05-17-v5.15.5.F.4d.1.B.3-legacy-empty-out.md` Step 1.6.3; audit synthesis MED-1 (struct-gen approach unresolved).

---

### TECH_DEBT-096 — `.B.2` deferral: Production canonical body emit migration (ModelInference.hpp:1788)

```yaml
id: TECH_DEBT-096
title: .B.2 deferral — Production canonical body emit migration (ModelInference.hpp:1788)
severity: high
surface_tags: [registry, ml-inference, wire-format]
trigger: sub-ship-.B.3
status: open
opened: 2026-05-17
related_specs: [DESIGN_SPECS/wire-format-patterns/wire-format-byte-preservation-discipline.md]
```

- **Created:** 2026-05-17 (at `v5.15.5.F.4d.1.B.2` ship close per Caramel accountability pushback)
- **Severity:** HIGH (production wire-format path; coupled with stamp_format_version bump TECH_DEBT-099)
- **Surface:** `ML_Headers/ModelInference.hpp:1788` — `FOREACH_STAMP_BOUND_CFG(X)` walker emits canonical body bytes for HMAC chain
- **What's deferred:** Replace walker with `STAMP_CFG_POPULATE_FROM_DERIVED(canonical, sizeof(canonical), cfg)` framework call. Changes wire byte order (framework walks master registry declaration order; legacy walks hand-crafted FOREACH_STAMP_BOUND_CFG row order). Triggers CRIT-6 byte order change → stamp_format_version bump (TECH_DEBT-099).
- **Why deferred (not effort-avoidance):** Coupled with stamp_format_version bump procedure; both should land together. `.B.3`'s Step 2 legacy registry deletion forces this — build BREAKS without migration (FOREACH_STAMP_BOUND_CFG body deleted).
- **Cost estimate:** ~15-20 min walker replacement + paired with TECH_DEBT-099 stamp_format_version sub-steps.
- **Trigger:** `.B.3` Step 1.6.4 — paired with Step 1.6.7 (stamp_format_version bump) AND Step 2 legacy deletion.
- **Status:** OPEN (logged at `.B.2` ship close 2026-05-17)
- **Accountability mechanism:** `.B.3` Step 1.6.4 enumerates; Step 2 legacy deletion FORCES; ship-close postmortem documents the stamp_format_version bump procedure as canonical reference.
- **Cross-ref:** `plans/v5.15-live-readiness/postmortems/2026-05-17-v5.15.5.F.4d.1.B.2-postmortem.md`; `subplans/2026-05-17-v5.15.5.F.4d.1.B.3-legacy-empty-out.md` Step 1.6.4; TECH_DEBT-099 (coupled stamp_format_version bump); audit synthesis CRIT-6.

---

### TECH_DEBT-097 — `.B.2` deferral: StampHelper.hpp:156 STAMP_CFG_AUTOPOPULATE migration

```yaml
id: TECH_DEBT-097
title: .B.2 deferral — StampHelper.hpp:156 STAMP_CFG_AUTOPOPULATE migration
severity: medium
surface_tags: [registry, wire-format, ml-inference]
trigger: sub-ship-.B.3
status: open
opened: 2026-05-17
related_specs: []
```

- **Created:** 2026-05-17 (at `v5.15.5.F.4d.1.B.2` ship close per Caramel accountability pushback)
- **Severity:** MED (legacy struct-field population path; cleanup after `.B.3` inf struct unification)
- **Surface:** `ML_Headers/StampHelper.hpp:156` — `STAMP_CFG_AUTOPOPULATE(inf, cfg)` macro populates `inf.<name>` fields for cohort
- **What's deferred:** Delete the call (or replace with framework-driven population) once `.B.3` legacy POST_CFG deletion eliminates the prefixed fields; inf struct has only unprefixed fields per Decision 5; framework writes them directly via STAMP_CFG_POPULATE_FROM_DERIVED.
- **Why deferred (not effort-avoidance):** Legacy macro still writes useful state (populates the inf struct fields the legacy parser at :1401 also writes); `.B.3`'s legacy macro body deletion is the trigger for this cleanup.
- **Cost estimate:** ~10-15 min.
- **Trigger:** `.B.3` Step 1.6.5 — paired with Step 2 legacy macro deletion.
- **Status:** OPEN (logged at `.B.2` ship close 2026-05-17)
- **Accountability mechanism:** `.B.3` Step 1.6.5 enumerates; Step 2 forces (STAMP_CFG_AUTOPOPULATE macro body deleted at `.B.3` → callers must migrate).
- **Cross-ref:** `plans/v5.15-live-readiness/postmortems/2026-05-17-v5.15.5.F.4d.1.B.2-postmortem.md`; `subplans/2026-05-17-v5.15.5.F.4d.1.B.3-legacy-empty-out.md` Step 1.6.5.

---

### TECH_DEBT-098 — `.B.2` deferral: CoreModelZoo.hpp:243 drift walker migration (with framework reason-buffer extension)

```yaml
id: TECH_DEBT-098
title: .B.2 deferral — CoreModelZoo.hpp:243 drift walker migration (with framework reason-buffer extension)
severity: medium
surface_tags: [registry, ml-inference, wire-format]
trigger: sub-ship-.B.3
status: open
opened: 2026-05-17
related_specs: []
```

- **Created:** 2026-05-17 (at `v5.15.5.F.4d.1.B.2` ship close per Caramel accountability pushback)
- **Severity:** MED (drift-check semantics + operator-visible error message preservation)
- **Surface:** `ML_Headers/CoreModelZoo.hpp:243` — custom drift walker over FOREACH_STAMP_BOUND_CFG sets `sr.inference_cfg_drift_count` + `sr.reason` (first drift produces operator-visible error message)
- **What's deferred:** Replace walker with `DRIFT_CHECK_FROM_DERIVED(...)` framework macro. Requires framework extension: add `char* reason_buf, size_t reason_cap` args to `cfg_derived::drift_check_from_derived` to preserve "first-drift sets reason" semantic. OR migration accepts behavior change (drift detected via failure_flags only; no human-readable reason; debug via post-fact mask inspection).
- **Why deferred (not effort-avoidance):** Coding-time Discovery 10 at `.B.2`: framework's `DRIFT_CHECK_FROM_DERIVED` uses branchless mask-select (per H20); doesn't have reason buffer. Adding reason buffer changes framework signature + semantics. Decision belongs at `.B.3` framework-extension consideration.
- **Cost estimate:** ~30-45 min (framework extension + walker migration + test).
- **Trigger:** `.B.3` Step 1.6.6 — paired with Step 2 legacy registry deletion (walker references FOREACH_STAMP_BOUND_CFG which gets deleted; migration forced).
- **Status:** OPEN (logged at `.B.2` ship close 2026-05-17)
- **Accountability mechanism:** `.B.3` Step 1.6.6 enumerates; Step 2 forces; postmortem documents framework reason-buffer decision (extend OR accept behavior change).
- **Cross-ref:** `plans/v5.15-live-readiness/postmortems/2026-05-17-v5.15.5.F.4d.1.B.2-postmortem.md` (Discovery 10); `subplans/2026-05-17-v5.15.5.F.4d.1.B.3-legacy-empty-out.md` Step 1.6.6; framework signature at `MemHeaders/CfgGateRegistry.hpp:277-310`.

---

### TECH_DEBT-099 — `.B.2` deferral: stamp_format_version 5 sub-steps (extract + bounds check + bump + fixture test + DESIGN_SPEC amendment)

```yaml
id: TECH_DEBT-099
title: .B.2 deferral — stamp_format_version 5 sub-steps (extract + bounds check + bump + fixture test + DESIGN_SPEC amendment)
severity: high
surface_tags: [wire-format, ml-inference, parser, test-infrastructure]
trigger: sub-ship-.B.3
status: open
opened: 2026-05-17
related_specs: [DESIGN_SPECS/wire-format-patterns/wire-format-byte-preservation-discipline.md]
```

- **Created:** 2026-05-17 (at `v5.15.5.F.4d.1.B.2` ship close per Caramel accountability pushback)
- **Severity:** HIGH (wire-format compatibility signaling; first canonical use of stamp_format_version bump procedure)
- **Surface:** `ML_Headers/ModelInference.hpp:1747` (hardcoded literal `"stamp_format_version=1\n"`) + `:1346-1351` (parser; no upper-bound validation) + `tick-trader-percore-workspace/DESIGN_SPECS/wire-format-patterns/wire-format-byte-preservation-discipline.md` (procedure documentation)
- **What's deferred:** 5 sub-steps:
  1. Extract literal → `static constexpr uint32_t STAMP_FORMAT_VERSION_CURRENT = 1;` named constant
  2. Add `MAX_SUPPORTED_STAMP_FORMAT_VERSION` + parser bounds check (refuse load if version > MAX_SUPPORTED)
  3. Bump `STAMP_FORMAT_VERSION_CURRENT` 1 → 2
  4. Test fixture failure-mode: v1 stamp → operator-visible error message
  5. Write NEW section in `wire-format-byte-preservation-discipline.md` titled "Procedure for wire-format changes during framework refactoring" as first canonical procedure for future bumps
- **Why deferred (not effort-avoidance):** Coupled with TECH_DEBT-096 (production walker migration changes wire byte order). Both should land together. `.B.3`'s legacy registry deletion forces the wire-byte-order change → triggers stamp_format_version bump as the canonical signaling mechanism.
- **Cost estimate:** ~45 min (5 sub-steps).
- **Trigger:** `.B.3` Step 1.6.7 — paired with Step 1.6.4 (production walker migration) AND Step 2 legacy deletion.
- **Status:** OPEN (logged at `.B.2` ship close 2026-05-17)
- **Accountability mechanism:** `.B.3` Step 1.6.7 enumerates; Step 2 forces wire-format change; DESIGN_SPEC amendment is explicit ship deliverable per HIGH-CONV-G audit finding.
- **Cross-ref:** `plans/v5.15-live-readiness/postmortems/2026-05-17-v5.15.5.F.4d.1.B.2-postmortem.md`; `subplans/2026-05-17-v5.15.5.F.4d.1.B.3-legacy-empty-out.md` Step 1.6.7; TECH_DEBT-096 (coupled production walker migration); audit synthesis CRIT-CONV-4 + HIGH-CONV-G + CRIT-6.

---

### TECH_DEBT-100 — `.B.2` deferral: per_horizon_barrier_blend ML_CFG_FLAG STAMP_BOUND_CFG_DERIVED bit-add

```yaml
id: TECH_DEBT-100
title: .B.2 deferral — per_horizon_barrier_blend ML_CFG_FLAG STAMP_BOUND_CFG_DERIVED bit-add
severity: low
surface_tags: [registry, ml-inference, cfg-flow]
trigger: sub-ship-.B.3
status: open
opened: 2026-05-17
related_specs: []
```

- **Created:** 2026-05-17 (at `v5.15.5.F.4d.1.B.2` ship close per Caramel accountability pushback)
- **Severity:** LOW-MED (1 specific field; same structural root cause as TECH_DEBT-094)
- **Surface:** `ML_Headers/MlCfgFlagRegistry.hpp:64` — `PER_HORIZON_BARRIER_BLEND` row metadata_flags column (currently `0`; revert to `CfgFieldDescriptor::STAMP_BOUND_CFG_DERIVED` once inf struct unification lands)
- **What's deferred:** Bit-add for PER_HORIZON_BARRIER_BLEND once `inf.per_horizon_barrier_blend` unprefixed field exists (currently only prefixed POST_CFG version exists). Sister to TECH_DEBT-094 (same root cause; same .B.3 trigger).
- **Why deferred (not effort-avoidance):** Coding-time Discovery 6 at `.B.2`: no unprefixed `inf.per_horizon_barrier_blend` field; bit-add at `.B.2` would cause framework walker to access non-existent field. Inf struct unification at `.B.3` (paired with TECH_DEBT-094) enables this single-row bit-add.
- **Cost estimate:** ~2-3 min (1-row metadata_flags column edit).
- **Trigger:** `.B.3` Step 1.6.2 (paired with TECH_DEBT-094) — same .B.3 Step.
- **Status:** OPEN (logged at `.B.2` ship close 2026-05-17)
- **Accountability mechanism:** `.B.3` Step 1.6.2 enumerates (paired with TECH_DEBT-094); inf struct unification at `.B.3` enables.
- **Cross-ref:** `plans/v5.15-live-readiness/postmortems/2026-05-17-v5.15.5.F.4d.1.B.2-postmortem.md`; `subplans/2026-05-17-v5.15.5.F.4d.1.B.3-legacy-empty-out.md` Step 1.6.2; TECH_DEBT-094 (sister; paired migration); `ML_Headers/MlCfgFlagRegistry.hpp:64` comment block (documents the .B.3 deferral inline at the row).

---

### TECH_DEBT-110 — `tools/stamp_model.sh` deprecation shim deletion target (Phase L retention)

```yaml
id: TECH_DEBT-110
title: tools/stamp_model.sh deprecation shim deletion target (Phase L retention)
severity: low
surface_tags: [cross-tool]
trigger: explicit-operator
status: open
opened: 2026-05-18
related_specs: [DESIGN_SPECS/refactor-patterns/framework-driven-cli-binary-pattern.md]
```

- **Created:** 2026-05-18 (deferred from `.B.3` Phase L per `framework-driven-cli-binary-pattern.md` v1.1 § Deprecation shim discipline)
- **Severity:** LOW (1 file; 1-line shim; operator workflow continuity concern)
- **Surface:** `tools/stamp_model.sh` (1-line `exec` redirect to `build/stamp_model_cli "$@"` introduced at `.B.3` Phase L L5 sub-step)
- **What's deferred:** delete the `tools/stamp_model.sh` deprecation shim entirely. Header preserved at Phase L ship close as deprecation notice cross-ref'd to `DESIGN_SPECS/refactor-patterns/framework-driven-cli-binary-pattern.md` + new `tools/stamp_model_cli.cpp` binary.
- **Why deferred (NOT effort-avoidance):** Operator scripts/aliases hardcoded to `tools/stamp_model.sh --model X` invocation need migration time to `build/stamp_model_cli --model X`. Typical retention: 1-2 ship cycles (matches Decision F SOFT compat philosophy for wire-format back-compat). Premature deletion would break operator workflow continuity per `feedback_surface_operator_migration_path_proactively`.
- **Cost estimate:** ~5 min (delete 1 file + verify no remaining references in operator scripts; `rg "tools/stamp_model.sh"` across workspace + engine repo + operator's scripts directory).
- **Trigger:** Explicit operator confirmation that all CLI invocation sites updated to `build/stamp_model_cli`. Or: 2 sub-ships shipped past Phase L without operator-flagged regression on the shim path.
- **Status:** OPEN (created 2026-05-18 at Phase L planning; will become accountable at Phase L ship close when shim lands).
- **Accountability mechanism:** Sub-ship plan body at the trigger ship will reference TECH_DEBT-110 in scope; ship-close auto-write removes this entry.
- **Cross-ref:** `DESIGN_SPECS/refactor-patterns/framework-driven-cli-binary-pattern.md` v1.1 § Step 4 (Deprecate the bash script) + § Deprecation shim discipline; `plans/v5.15-live-readiness/subplans/2026-05-17-v5.15.5.F.4d.1.B.3-legacy-empty-out.md` Phase L Step L5; `feedback_surface_operator_migration_path_proactively.md`.

---

### TECH_DEBT-111 — CI defense-in-depth: `tools/check_cli_flag_drift.py` (anti-pattern enforcement for X-macro auto-gen CLI flag table)

```yaml
id: TECH_DEBT-111
title: CI defense-in-depth — tools/check_cli_flag_drift.py (anti-pattern enforcement for X-macro auto-gen CLI flag table)
severity: low
surface_tags: [ci-tooling, cross-tool, registry, ai-driven-workflow-scoped]
trigger: v5.16-FOREACH_CLI_MODE-registry-first-canonical
status: open
opened: 2026-05-18
related_specs: [DESIGN_SPECS/refactor-patterns/framework-driven-cli-binary-pattern.md, DESIGN_SPECS/framework-patterns/registry-coverage-ci-check-pattern.md]
```

- **Created:** 2026-05-18 (deferred from `.B.3` Phase L per `framework-driven-cli-binary-pattern.md` v1.1 § Audit detection)
- **Severity:** LOW (defense-in-depth; X-macro discipline is enforced by code review at 1st canonical scale)
- **Surface:** NEW Python CI script `tools/check_cli_flag_drift.py`. Sister to existing `tools/check_struct_field_uniqueness.py` (cross-walker struct-field uniqueness; same pillar B13 + B2 enforcement category).
- **What's deferred:** Python script that:
  - Parses `tools/stamp_model_cli.cpp` (and future framework-driven CLI binaries)
  - Verifies `static struct option longopts[]` array is auto-generated via `FOREACH_*_CFG_FIELD(X_GEN_LONGOPT_*)` X-macro walkers (flags any manual `{"--flag", ...}` entries that bypass the registry walk)
  - Verifies cross-walker collision exclusions match `FOREACH_STAMP_RESULT_FIELD_EXCLUSION` sidecar at `MemHeaders/CfgGateRegistry.hpp:512-515` (per Phase L B13 resolution)
  - Reports per-binary verdict + flag-count + collision-detection summary
- **Why deferred (NOT effort-avoidance):** At 1st canonical framework-driven CLI binary (`.B.3` Phase L), X-macro discipline is enforced by code review + the audit gate. CI tool warranted when 2+ framework-driven CLI binaries exist (per `feedback_framework_layer_payoff_diminishing_returns` — pattern earns its place at 2+ applications). Premature CI tooling at 1 application = framework-layer scope creep.
- **Cost estimate:** ~30-60 min (sister to existing `check_struct_field_uniqueness.py` template; ~150-200 LOC Python script).
- **Trigger:** v5.16+ alongside FOREACH_CLI_MODE registry first canonical (TECH_DEBT-034) — framework-driven-cli-binary-pattern Stage 4 cohort migration triggers warrant CI defense-in-depth at that surface. `.C` skip at v5.15 + Phase L revert at `.B.3` mean no current 2nd canonical surface; previous trigger ("2nd framework-driven CLI binary lands") was moot post-`.C` skip 2026-05-27 PM. UPDATED at `v5.15.5.F.4d.1.D` Phase D.3 per scope-reconciliation cycle.
- **Status:** OPEN with explicit v5.16+ trigger (created 2026-05-18 at Phase L planning; trigger updated 2026-05-28 at `.D`).
- **Accountability mechanism:** Cross-ref in `DESIGN_SPECS/refactor-patterns/framework-driven-cli-binary-pattern.md` v1.1 Pattern lifecycle § Stage 6 (tooling enforcement); future sub-ship adding 2nd canonical references TECH_DEBT-111 in scope.
- **Cross-ref:** `DESIGN_SPECS/refactor-patterns/framework-driven-cli-binary-pattern.md` v1.1 § Audit detection + § Pattern lifecycle Stage 6; `DESIGN_SPECS/framework-patterns/registry-coverage-ci-check-pattern.md` Shape B (anti-pattern enforcement); `tools/check_struct_field_uniqueness.py` (sister CI tool precedent); `feedback_framework_layer_payoff_diminishing_returns.md`.

---

### TECH_DEBT-116 — TECH_DEBT.md split (file-size discipline application)

```yaml
id: TECH_DEBT-116
title: TECH_DEBT.md split (file-size discipline application)
severity: medium
surface_tags: []
trigger: n/a (closed)
status: wontfix-per-ai-workflow
opened: 2026-05-18
closed_at: v5.15.5.F.4d.1.B.7
closure_rationale: AI-driven solo workflow (per operator C1 directive 2026-05-27); ledger 2000-line threshold reviewed inline — ledger access is grep-driven not navigation-driven; AI handles large ledgers trivially
related_specs: [DESIGN_SPECS/doc-disciplines/file-size-split-discipline.md]
```

- **Created:** 2026-05-18 (codified at `.B.3` ship close after `feedback_file_size_split_discipline.md` codification)
- **Severity:** MEDIUM (file currently navigable but at 2013 lines exceeds 2000-line hard threshold per `DESIGN_SPECS/doc-disciplines/file-size-split-discipline.md`)
- **Surface:** `DOCS/TECH_DEBT.md` (currently 2013 lines, ~115 entries)
- **What's deferred:** Split TECH_DEBT.md per file-size-split-discipline pattern:
  - **Recommended split criteria:** by-status (most useful for retrieval workflow)
    - `DOCS/tech-debt/open.md` — status: open (currently in-flight or queued)
    - `DOCS/tech-debt/in-flight.md` — status: being addressed this sprint
    - `DOCS/tech-debt/closed.md` — status: closed (archival; majority of entries)
    - `DOCS/TECH_DEBT.md` — INDEX with `splits_into:` frontmatter + table of contents
  - **Alternative criteria:** by-surface (cohort-aligned; `DOCS/tech-debt/registry-discipline/`, `DOCS/tech-debt/wire-format/`, etc.) — defer decision to ship-planning phase
- **Why deferred (NOT effort-avoidance):** TECH_DEBT entries are heavily cross-referenced (>50 cross-refs to TECH_DEBT-NNN across DESIGN_SPECS / skills / CLAUDE.md / CLAUDE.local.md / memory rules). Split + sed-based cross-ref update warrants dedicated ship with rollback anchor + verification per batch. Same risk class as TECH_DEBT-113 (folder subdivision).
- **Cost estimate:** ~2-3h focused (decide split criteria + extract entries + build INDEX + sed-sweep cross-refs + verify with `check_doc_metadata.py`)
- **Trigger:** dedicated maintenance ship between sub-ships (alongside TECH_DEBT-113 folder subdivision OR independently)
- **Status:** OPEN with explicit trigger (created 2026-05-18 at doc-layer refresh ship close)
- **Cross-ref:** `DESIGN_SPECS/doc-disciplines/file-size-split-discipline.md` (the discipline); TECH_DEBT-113 (sister folder subdivision); `feedback_file_size_split_discipline.md` (going-forward rule).

---

### TECH_DEBT-118 — /readiness SKILL.md split (file-size discipline application)

```yaml
id: TECH_DEBT-118
title: /readiness SKILL.md split (file-size discipline application)
severity: medium
surface_tags: [ci-tooling]
trigger: n/a (closed)
status: wontfix-per-ai-workflow
opened: 2026-05-18
closed_at: v5.15.5.F.4d.1.B.7
closure_rationale: AI-driven solo workflow (per operator C1 directive 2026-05-27); SKILL.md is loaded on skill invocation; AI handles large SKILL.md trivially; if SKILL.md becomes load-bearing concern in future, split is mechanical
related_specs: [DESIGN_SPECS/doc-disciplines/file-size-split-discipline.md]
```

- **Created:** 2026-05-18 (codified at `.B.3` ship close)
- **Severity:** MEDIUM (1674 lines — exceeds 1500-line SKILL.md hard threshold)
- **Surface:** `claude-skills/readiness/SKILL.md`
- **What's deferred:** Split per file-size-split-discipline pattern:
  - **Recommended split criteria:** per-check sidecar files
    - `claude-skills/readiness/SKILL.md` (~300 lines) — invocation + check INDEX
    - `claude-skills/readiness/checks/check-01-<topic>.md` through `check-NN-<topic>.md` (one file per check)
  - Skill spec keeps the orchestration logic + invocation + index of checks; each check's detail body extracts to sidecar
- **Why deferred (NOT effort-avoidance):** Check N references appear in plan body audits (`/readiness Check 25` etc.). Extraction + INDEX shape needs care to preserve cross-ref retrievability.
- **Cost estimate:** ~2-3h focused (extract per-check bodies + build INDEX + verify Check N grep-retrievable)
- **Trigger:** dedicated maintenance ship; can land independently of TECH_DEBT-116/-117 since SKILL is operationally separate from ledgers
- **Status:** OPEN with explicit trigger
- **Cross-ref:** `DESIGN_SPECS/doc-disciplines/file-size-split-discipline.md`; sister TECH_DEBT-116/-117 (ledger splits at same discipline).

---

### TECH_DEBT-113 — DESIGN_SPECS + plans/ subdivision (folder restructure deferred)

```yaml
id: TECH_DEBT-113
title: DESIGN_SPECS + plans/ subdivision (folder restructure deferred)
severity: low
surface_tags: []
trigger: next-maintenance-window
status: open
opened: 2026-05-18
related_specs: [DESIGN_SPECS/doc-disciplines/categorical-triggers-in-always-loaded-docs.md]
```

- **Created:** 2026-05-18 (deferred at `.B.3` doc-layer refresh per Caramel's framing: "at some point we may need to add subdivided folders for design specs and stuff, and plans, since current is kind of bloated and there are some things that are kind of just shoved in places")
- **Severity:** LOW (organizational maintenance; no functional impact)
- **Surface:** `DESIGN_SPECS/` (~80+ specs flat) + `plans/v5.15-live-readiness/subplans/` (many sub-plans flat) + `plans/v5.15-live-readiness/handoffs/` (many handoffs flat)
- **What's deferred:** Subdivide flat directories into concern-grouped subfolders:
  - `DESIGN_SPECS/` subdivisions: `framework-discipline/`, `audit-methodology/`, `wire-format/`, `data-oriented-design/`, `concurrency/`, `process-discipline/`, `plan-templates/` — assignment per `DESIGN_SPECS/README.md` tags
  - `plans/<sprint>/subplans/` subdivisions: by sub-ship version prefix (`.F.4d/`, `.F.4c/`, etc.) OR by sub-ship phase
  - `plans/<sprint>/handoffs/` subdivisions: by sub-ship version prefix
- **Why deferred (NOT effort-avoidance):** Sub-ship cycle currently active (`.B.3` Phase L coding queued); folder restructure with ~100 file moves is high-disruption (breaks cross-refs; requires path-update sweep). Worth doing as a dedicated maintenance ship between sub-ships, with rollback anchor and bulk sed-based cross-ref update.
- **Cost estimate:** ~2-3h focused work (~100 file moves + cross-ref `rg` sweep + verify all DESIGN_SPECS cross-refs resolve + verify all skill SKILL.md `DESIGN_SPECS/<name>.md` refs resolve + commit + tag).
- **Trigger:** Between-sub-ship maintenance window after `.B.3` ships AND before next major sub-ship enters in-flight. Operator-flagged ready when sub-ship cadence stabilizes.
- **Status:** OPEN with explicit trigger (created 2026-05-18 at doc-layer refresh planning).
- **Accountability mechanism:** Cross-ref in CLAUDE.local.md going-forward rule "Doc layer separation" mentions TECH_DEBT-113 as deferred folder restructure surface.
- **Cross-ref:** `DESIGN_SPECS/doc-disciplines/categorical-triggers-in-always-loaded-docs.md` (sister doc-layer discipline that doesn't require folder restructure); `DESIGN_SPECS/README.md` tag organization (categorization basis for subdivision); `feedback_no_defer_for_effort.md` (this defer is rational — sub-ship cycle priority, not effort-avoidance).

---

### TECH_DEBT-114 — `tests/controller_test.cpp` test file split (domain-aligned sub-files)

```yaml
id: TECH_DEBT-114
title: tests/controller_test.cpp test file split (domain-aligned sub-files)
severity: medium
surface_tags: [test-infrastructure]
trigger: n/a (closed; test 5K rule retained for reliability; TECH_DEBT-127 absorbs any test-reliability follow-up if needed)
status: wontfix-per-ai-workflow
opened: 2026-05-18
partial_closed_at: v5.15.5.F.4d.1.B.5 WIP-B1 (2026-05-27; shared infrastructure extract to tests/test_common.hpp landed; full domain split DEFERRED per operator directive "more concerned about actual code" — see TECH_DEBT-127 for follow-up)
closed_at: v5.15.5.F.4d.1.B.7
closure_rationale: AI-driven solo workflow (per operator C1 directive 2026-05-27); test 5K rule retained explicitly for test-reliability concern — TECH_DEBT-127 stays open as the test-reliability surface; this entry's full-domain-split intent is dropped
related_specs: [DESIGN_SPECS/doc-disciplines/file-size-split-discipline.md]
```

- **Created:** 2026-05-18 (codified at doc-layer refresh ship — moved out of CLAUDE.md Test file size discipline TODO sentence to proper TECH_DEBT entry per `feedback_claude_md_guidelines_not_stuff_to_do.md`)
- **Severity:** MEDIUM (compile-time + test-navigation + merge-conflict surface area; 3118 tests at risk during any refactor)
- **Surface:** `tests/controller_test.cpp` (~25k lines + 3118 tests); CLAUDE.md "Test file size discipline" rule (>5k lines OR >100 sections must split BEFORE adding more)
- **Sister:** TECH_DEBT-029 (Source file length reduction — analog SOURCE-side discipline for header/non-test files; same maintenance-overhead class)
- **What's deferred:** Split `controller_test.cpp` into domain-aligned sub-files:
  - `controller_test_engine.cpp` (engine + sharded path)
  - `controller_test_features.cpp` (cfg + feature + parser)
  - `controller_test_stamps.cpp` (stamp body + parity)
  - `controller_test_ml.cpp` (ML feature + inference + scaler)
  - `controller_test_misc.cpp` (catch-all)
  - Helpers extract to `tests/test_common.hpp`
- **Why deferred (NOT effort-avoidance):** 3118 tests at risk warrants focused effort with rollback anchor. Multiple sessions have queued this; deferred each cycle because of in-flight sub-ship priority. The deferral is rational — test-split-without-rollback risks all-tests-broken at a critical sprint phase. Per `feedback_no_defer_for_effort.md` — this is the legitimate-defer category (effort-bounded by safety, not effort-avoidance).
- **Cost estimate:** ~4-6h focused work (file splits + helper extraction + verify all tests still GREEN at each split + dedicated rollback anchor + ship close).
- **Trigger:** Between-sub-ship maintenance window OR when next operator-flagged "must add tests but file too big" event surfaces.
- **Status:** OPEN with explicit trigger (created 2026-05-18 at doc-layer refresh planning; moved from inline CLAUDE.md TODO sentence per doc-layer-separation discipline).
- **Accountability mechanism:** CLAUDE.md Test file size discipline rule now points at TECH_DEBT-114 (this entry) as the trigger ledger for the queued split.
- **Cross-ref:** TECH_DEBT-029 (source-file analog); CLAUDE.md "Test file size discipline" rule; `feedback_no_defer_for_effort.md` (legitimate-defer category); `feedback_claude_md_guidelines_not_stuff_to_do.md` (this entry is the proper home for the deferred work, not CLAUDE.md inline TODO).

---

### TECH_DEBT-115 — Institutional memory rollout (phased doc-system architecture)

```yaml
id: TECH_DEBT-115
title: Institutional memory rollout (phased doc-system architecture)
severity: medium
surface_tags: [ci-tooling, registry]
trigger: sub-ship-.C
status: open
opened: 2026-05-18
related_specs: [DESIGN_SPECS/doc-disciplines/categorical-triggers-in-always-loaded-docs.md, DESIGN_SPECS/meta-disciplines/doc-frontmatter-convention.md, DESIGN_SPECS/meta-disciplines/doc-tag-vocabulary.md, DESIGN_SPECS/ledger-templates/ledger-entry-templates.md]
```

- **Created:** 2026-05-18 (v5.15.5.F.4d.1.B.3 doc-layer refresh — codified after Caramel surfaced institutional-memory architecture vision: "this is basically becoming institutional memory, and i wanna design a system that i never have to think about again that just works based on types and tags, and is searchable by grep, and well organized")
- **Severity:** MEDIUM (foundational doc-system architecture; cumulative drift if not addressed becomes blocker over 2-3 sprints)
- **Surface:** all 80+ DESIGN_SPECS + 30 SKILL.md + TECH_DEBT/PARITY ledger entries + plans + memory rules + CLAUDE.md/CLAUDE.local.md
- **Sister:** TECH_DEBT-112 (skill structural audit — predecessor; addressed sprint-phrasing-level drift); TECH_DEBT-113 (folder subdivision — pairs with this); TECH_DEBT-109 (skill SKILL.md drift triage — earlier predecessor)

#### Phase 1 — Stage 2 DRAFTs landed (this sprint at `.B.3` doc-layer refresh ship close)

Status: **APPLIED** at `.B.3` ship close 2026-05-18.

- **CLAUDE.md additions:** Design philosophy + priorities section / How to find anything section / Latency budget table / Memory budget table / Concurrency model summary
- **CLAUDE.local.md amendments:** 4 stale pointers fixed / "Recent" wording rot fixed / 3 going-forward rules added (doc-layer separation / plans have end goals / categorical triggers > hardcoded refs) / 1 more queued (frontmatter discipline)
- **NEW DESIGN_SPECS (Stage 2 DRAFT v1.0):**
  - `categorical-triggers-in-always-loaded-docs.md` — doc-discipline; 3-bucket audit rubric
  - `sprint-master-plan-template.md` — plan-template for sprint MASTER
  - `doc-tag-vocabulary.md` — canonical CONCERN/SURFACE/LIFECYCLE tag index
  - `doc-frontmatter-convention.md` — universal YAML frontmatter discipline
  - `design-spec-template.md` — type-aware DESIGN_SPEC template
  - `postmortem-template.md` — type-aware postmortem template
  - `cache-line-discipline.md` — DOD codification sketch
  - `concurrency-model-summary.md` — thread architecture codification sketch
  - `audit-report-format.md` — audit skill output standardization sketch
- **NEW memory rules:** `feedback_claude_md_guidelines_not_stuff_to_do.md` / `feedback_plans_have_explicit_end_goal.md` / `feedback_categorical_triggers_over_hardcoded_refs.md` / `feedback_metadata_audit_quarterly.md`
- **Skill audit closure (TECH_DEBT-112):** 39 conversions across 22 SKILL.md files (Agent-applied)
- **Plan template amendment:** `future-oriented-plan-template.md` v1.1 → v1.2 (Ship end goal + plan type metadata)

#### Phase 2 — `.C` candidate ship (institutional-memory first-canonical)

Status: **OPEN** with explicit trigger.

- **Trigger:** between-sub-ship maintenance window after `.B.3` ships AND before next major sub-ship enters in-flight. Operator-flagged ready when sub-ship cadence stabilizes.
- **Scope:**
  - Promote Stage 2 DRAFT DESIGN_SPECS to Stage 3 first canonical: 5-10 high-traffic specs get frontmatter applied
  - CI tool `check_doc_metadata.py` lands — validates frontmatter at commit time
  - NEW `/doc-create` skill — type-aware doc scaffolding
  - NEW `/find` skill — natural language → metadata-filtered grep
  - DESIGN_SPECS folder subdivision (pairs with TECH_DEBT-113): `refactor-patterns/`, `framework-patterns/`, `audit-methodologies/`, `data-disciplines/`, `concurrency-patterns/`, `wire-format-patterns/`, `doc-disciplines/`, `meta-disciplines/`, `plan-templates/`, `ledger-templates/`
  - DOCS/ARCHITECTURE.md refresh per Caramel's data-flow reference request (2026-05-18) — `type: architecture-overview` doc with ASCII data flow + pointers to canonical sources (CODE_MAP / CLAUDE_INVARIANTS / HOT_PATH_CHANGELOG)
- **Cost estimate:** ~6-8h focused (folder restructure ~2-3h; CI tool ~2-3h; skill creation ~2-3h; per-spec frontmatter migration ~30-60 min for 5-10 specs)
- **Acceptance criteria:**
  - All Stage 2 DRAFT specs have frontmatter per `doc-frontmatter-convention.md`
  - CI tool catches frontmatter drift at commit time
  - `/doc-create` scaffolds new specs from `design-spec-template.md`
  - `/find` returns metadata-filtered results
  - Folder subdivision reflects `type:` frontmatter (CI tool verifies)

#### Phase 3 — `.D` candidate ship (cohort migration)

Status: **OPEN** with explicit trigger.

- **Trigger:** `.C` ship landed; 5-10 specs validated with new frontmatter; ready to migrate cohort.
- **Scope:**
  - All 80+ DESIGN_SPECS migrate to frontmatter (Stage 4 cohort)
  - All 30 SKILL.md files get frontmatter (CLAUDE.md skill suite auto-generates)
  - All TECH_DEBT entries migrate to YAML frontmatter shape
  - All PARITY_ISSUES entries migrate to YAML frontmatter
  - All RECURRING_BUG_PATTERNS Class N entries migrate to YAML frontmatter
  - NEW `/index-rebuild` skill — regenerates CLAUDE.md skill suite table + DESIGN_SPECS/README + tag-index snapshot from frontmatter
  - NEW `/metadata-audit` skill — periodic audit (singleton tags / broken sister-doc links / Stage 2 DRAFTs older than N sprints / etc.)
- **Cost estimate:** ~12-20h focused (most files need frontmatter; mostly mechanical sed-based migration; verify each batch)
- **Acceptance criteria:**
  - 100% of cross-referenced docs have frontmatter
  - `/index-rebuild` regenerates canonical indexes
  - `/metadata-audit` reports zero high-severity findings (or all flagged + accepted)

#### Phase 4 — `.E` candidate ship (cadence-locked)

Status: **OPEN** with explicit trigger.

- **Trigger:** `.D` ship landed; cohort migration verified; ready to lock periodic cadence.
- **Scope:**
  - `/metadata-audit` quarterly cadence locked (sister to `/anti-spaghetti` quarterly cadence)
  - `/index-rebuild` fires at sprint-close mechanically
  - CI tool `check_doc_metadata.py` enforced at every commit
  - DESIGN_SPECS lifecycle stage `6-cadence-locked` applied to specs that have proven institutional-memory load-bearing for ≥2 sprints
- **Cost estimate:** ~2-4h (skill cadence locking + CI integration verification)
- **Acceptance criteria:**
  - Periodic audits fire mechanically
  - Drift detection runs at commit time
  - System maintains itself; new doc creation uses canonical templates by default

#### Phase 2-3 MEMORY slice — OMITTED from the original cohort (surfaced 2026-05-29, `.E.0.x`)

Status: **OPEN** — the gap this entry's own vision ("a system... based on types and tags, searchable by grep") was meant to close, but the cohort lists above **omit `memory/`**. Phase-2 `/doc-create` scope has no `memory` type/template; Phase-3 cohort-migration lists DESIGN_SPECS + SKILL.md + TECH_DEBT + PARITY + RECURRING_BUG_PATTERNS but **not the ~58 `memory/*.md` files**. Grounded 2026-05-29: **0/58 memories carry `tags:`/`sister_specs:` frontmatter** — all use the parallel inline-`[[links]]` + hand-maintained `MEMORY.md` index, *outside* the structured system. Memories are the lone doc-type outlier on every structural surface (template / frontmatter / `TAG_INDEX` / `check_doc_metadata` coverage).

- **The memory slice (add to Phases 2-3):**
  - **Template (Phase-2-class):** a memory template + `/doc-create memory` type (per the existing `doc-frontmatter-convention.md` `### memory/*.md` spec). The CREATION side — without it, new memories drift ad-hoc even post-migration.
  - **Migration (Phase-3-class):** the ~58 `memory/*.md` → `tags:` + `sister_specs:` frontmatter (Stage-4 cohort, alongside the others).
  - **Index/query:** memories into `TAG_INDEX` + `/find`.
  - **Check (already-ready):** once memories carry `sister_specs:`, the EXISTING `check_doc_metadata --bidirectional` + broken-ref + tag-vocab checks cover them **for free** — no bespoke memory-link parser (canonical-sister: use the system you already built).
- **M7 priority evidence:** the recurring **CP-1** (sister-link forward-vs-reverse asymmetry — recurred `.E.0.x` *despite* the catalog note) + **WH-1** (kebab-vs-filename `[[link]]` drift) meta-bugs are the COST of the memory-omission; they're caught only by judgment (operator prompt + `/capture-audit` Check 12 + the harvest) until the structured check covers memories. Planned-but-undone + recurring = M7 escalation → finish this slice. See `meta-anti-pattern-index.md` CP-1.
- **Status-reconciliation note (WH-2):** Phase 2-3 *tooling* substantially landed since 2026-05-18 (`check_doc_metadata.py`, `/doc-create`, `/find`, `/index-rebuild`, `/metadata-audit`, folder subdivision, DESIGN_SPECS frontmatter all exist) — so the index-row "PHASE 2-4 OPEN" + per-phase statuses are STALE and due a reconciliation pass; **the memory slice is the principal unfinished part.**
- **Scan quantification (2026-05-29 `/metadata-audit` map of the deferred backlog — `.E.0.x`):** ~245+ UNDEFINED-tag instances (tag-vocabulary uncurated — docs use meaningful tags not registered in `doc-tag-vocabulary.md`; curation gap, not mis-tagging); ~140+ additional sister/bidirectional asymmetries (`--bidirectional` total ~386); **29 stale Stage-2 DRAFTs** (promotion cadence stalled); + the memory-omission (0/58 structured). Frontmatter *coverage* is good (only 2 DESIGN_SPECS missing it). **Read:** mostly **curation-backlog** (tag-vocab + stage-promotion), NOT correctness-threatening; this is exactly TECH_DEBT-115 phases 2-3's deferred cost, now QUANTIFIED → prioritization evidence. Bulk routes to a focused TECH_DEBT-115 rollout + the `/metadata-audit` quarterly cadence; the `.E`-load-bearing subset (active apparatus/catalogs/memory) is small + spot-fixable + does NOT block `.E.0.1` coding.
- **Cross-ref:** `meta-anti-pattern-index.md` CP-1/WH-1; `.E.0.x` capture (decision-log D-81..87); active task #14 (doc-hygiene cadence — the near-term actionable pointing here).

#### Auto-write contracts triggered by this entry

- DESIGN_SPECS frontmatter migration → updates each spec's frontmatter + bumps version
- `/index-rebuild` auto-fires at sprint-close
- `/metadata-audit` auto-fires quarterly
- Each phase ship close → status flip in this entry (`open` → `in-flight` → `closed`)

- **Status:** PHASE 1 APPLIED; PHASE 2-4 OPEN with explicit triggers.
- **Cross-ref:** `DESIGN_SPECS/doc-disciplines/categorical-triggers-in-always-loaded-docs.md` / `DESIGN_SPECS/meta-disciplines/doc-frontmatter-convention.md` / `DESIGN_SPECS/meta-disciplines/doc-tag-vocabulary.md` / `DESIGN_SPECS/plan-templates/design-spec-template.md` / `DESIGN_SPECS/plan-templates/postmortem-template.md` / `DESIGN_SPECS/data-disciplines/cache-line-discipline.md` / `DESIGN_SPECS/concurrency-patterns/concurrency-model-summary.md` / `DESIGN_SPECS/audit-methodologies/audit-report-format.md` / `feedback_claude_md_guidelines_not_stuff_to_do.md` / `feedback_plans_have_explicit_end_goal.md` / `feedback_categorical_triggers_over_hardcoded_refs.md` / `feedback_metadata_audit_quarterly.md` / TECH_DEBT-112 (predecessor) / TECH_DEBT-113 (folder subdivision pairs) / CLAUDE.md § How to find anything (Stage 5 promotion already landed).

### TECH_DEBT-119 — Extract EngineCommon_BootPerCore + EngineCommon_SlowPathCycleOneCore shared helpers (closes 4 train-serve CRITs + 3 HIGHs structurally)

- **Created:** 2026-05-24 by `v5.15.5.F.4d.1.B.3` WIP-8 audit cycle (ML↔LIVE structural sweep)
- **Severity:** HIGH (structural fix that closes 4 critical train-serve breaks per PARITY-026/027/028/029 + 3 HIGH drifts per PARITY-030/031 + TECH_DEBT-120 + B2 arch parity)
- **Surface:** `CoreFrameworks/EngineSharded.hpp` boot block (~lines 670-1160) + `Backtest/BacktestSharded.hpp` boot block (~lines 180-420) + `ShardedBacktestDriver.hpp:189-397` slow-path body; NEW header `CoreFrameworks/EngineCommon.hpp`
- **What's deferred:** Structural extract of shared per-core boot work + per-core slow-path cycle body into shared helpers callable from both EngineSharded_Run + BacktestSharded_Run. Mirror discipline currently relies on `"Mirrors EngineSharded_Run lines X-Y"` comments (15+ explicit citations in BacktestSharded.hpp) — drift accumulates per-patch (PARITY-026/027/028/029/030/031 are direct evidence drift HAS happened).
- **Why deferred (not effort-avoidance):** NOT effort-deferred. Audit surfaced 4 CRITs + 3 HIGHs on 2026-05-24 mid-`.B.3` ship. Per `feedback_proportionate_response_to_audit_findings` Option D ARCHITECT (justified because 1 refactor closes 7 findings simultaneously). Per `feedback_motivated_collaborator_for_caramel` + `feedback_plan_right_not_fast` — gets dedicated `.B.4` sub-ship with full audit-driven pre-coding cycle, NOT folded into `.B.3` close. Hotfix for PARITY-026 (kill_switch) may land separately as 5-LOC mirror-the-backtest patch ahead of `.B.4` structural close.
- **Cost estimate:** ~2-3 days focused; ~200-400 LOC (NEW EngineCommon.hpp + 2 callsite delegations + per-call-site differences via cfg flags / nullable state); MED-HIGH risk (touches both boot paths); EXPLICIT audit gate via /precoding-audit-gate + /blindspot-scan per `.B.4` plan body
- **Trigger:** `.B.3` ship-close hands off to `.B.4`; or earlier if Caramel picks hotfix PARITY-026 standalone
- **Status:** OPEN (in-flight at `.B.4` start)
- **Cross-ref:** PARITY-026 (kill_switch dead) / PARITY-027 (exit-model submit) / PARITY-028 (BindCompositeCfg) / PARITY-029 (Strategy_InitPerCore) / PARITY-030 (BNB fee) / PARITY-031 (per-core regime) / TECH_DEBT-120 (B2 arch parity coverage) / `DESIGN_SPECS/meta-disciplines/structural-fix-preferred-decision-framework.md` / NEW `DESIGN_SPECS/refactor-patterns/shared-helper-extract-for-train-serve-mirror-close.md` DRAFT v0.1 at .B.4 plan-body / NEW `DESIGN_SPECS/meta-disciplines/train-serve-execution-layer-parity.md` DRAFT v0.1 (M5 codification) / `plans/v5.15-live-readiness/plan_checks/2026-05-24-train-serve-asymmetry-sweep.md`

### TECH_DEBT-120 — parity_harness extension for engine_arch=per_core_slow path coverage (live-arch untested)

- **Created:** 2026-05-24 by `v5.15.5.F.4d.1.B.3` WIP-8 audit cycle
- **Severity:** HIGH (architectural arch-asymmetry; production runs untested code path relative to training)
- **Surface:** `tests/parity_harness.cpp` (currently tests `engine_mode=single_core` vs `sharded` — BOTH centralized arch); NEW test for `engine_arch=per_core_slow` vs `centralized`
- **What's deferred:** Add third sweep in existing parity_harness.cpp (or NEW `tests/train_serve_parity_harness.cpp` binary) to explicitly test `engine_arch=per_core_slow` path. Today's harness validates legacy-vs-modern backtest only; NO test exercises the LIVE-default per-core-slow lambda body at EngineSharded:3036-3320.
- **Why deferred (not effort-avoidance):** Test infrastructure work belongs in `.F.5.C` training-harness-1:1-with-live-execution scope per ROADMAP. `.B.4` EngineCommon extract (TECH_DEBT-119) closes the structural mirror (helpers shared → byte-identical by construction); `.F.5.C` adds explicit regression guard. Two-step close per `feedback_proportionate_response_to_audit_findings`.
- **Cost estimate:** ~4-6h (synthetic-data wrapper around EngineSharded that doesn't require Binance WS + explicit per_core_slow sweep + assertion on decision-output identity)
- **Trigger:** `.F.5.C` plan body draft; or earlier if a `.B.4`-scope regression surfaces
- **Status:** OPEN
- **Cross-ref:** TECH_DEBT-119 (closes the structural mirror; this entry closes the test gap) / sister to TECH_DEBT-122 (parity_harness inadequate naming) / `plans/v5.15-live-readiness/plan_checks/2026-05-24-train-serve-asymmetry-sweep.md` finding B2

### TECH_DEBT-121 — Live engine bandit_state_prior_path cfg field (transfer-learning asymmetry with backtest)

- **Created:** 2026-05-24 by `v5.15.5.F.4d.1.B.3` WIP-8 audit cycle
- **Severity:** MEDIUM (rare operator path — surfaces on first transfer-learning attempt to live)
- **Surface:** `CoreFrameworks/ControllerConfig.hpp` (new cfg field row) + `EnsembleModelZoo_PostLoadSetup` (override block); cross-ref `Backtest/BacktestEngine.hpp:205` `bandit_state_prior_path[400]`
- **What's deferred:** Live engine has NO cfg field to specify an explicit bandit state prior path; backtest has `bandit_state_prior_path` as backtest-only operator-explicit override. Operator transfer-learns bandit weights at backtest training; ships to production; live boot ignores the prior + starts from per-bundle default.
- **Why deferred (not effort-avoidance):** Operator-facing cfg surface addition belongs in `.F.5.A` ML framework parity scope per ROADMAP (audit-driven scope sizing at `.F.4f` close). Add cfg row + parser + PostLoadSetup hook. NOT urgent because transfer-learning is rare operator workflow.
- **Cost estimate:** ~2-3h (1 row in FOREACH_GLOBAL_CFG_FIELD + parser + PostLoadSetup override block + tests)
- **Trigger:** `.F.5.A` plan body draft; or earlier if operator surfaces transfer-learning-to-live workflow
- **Status:** OPEN
- **Cross-ref:** `plans/v5.15-live-readiness/plan_checks/2026-05-24-train-serve-asymmetry-sweep.md` finding B5 / `Backtest/BacktestEngine.hpp:205`

### TECH_DEBT-122 — parity_harness.cpp doesn't actually test backtest↔live parity (misleading name; false confidence)

- **Created:** 2026-05-24 by `v5.15.5.F.4d.1.B.3` WIP-8 audit cycle
- **Severity:** MEDIUM (operator believes parity_harness validates train↔serve; it doesn't; findings PARITY-026 to -031 all evade the harness)
- **Surface:** `tests/parity_harness.cpp:8-23`
- **What's deferred:** Rename or extend parity_harness. Current harness tests `engine_mode=single_core` vs `sharded` (BOTH consume Backtest_Run — training-side only). No EngineSharded_Run invocation. No live-path coverage. Either:
  (a) RENAME to `tests/backtest_engine_parity_harness.cpp` to accurately reflect scope + add NEW `tests/train_serve_parity_harness.cpp` for true train↔serve coverage; OR
  (b) EXTEND existing harness to add EngineSharded_Run invocation as third sweep
- **Why deferred (not effort-avoidance):** Sister to TECH_DEBT-120; both close at `.F.5.C` training-harness-1:1-with-live-execution. Per ROADMAP `.F.5.C` is the explicit home.
- **Cost estimate:** ~3-5h (depending on (a)/(b) choice + synthetic-data wrapper for EngineSharded)
- **Trigger:** `.F.5.C` plan body draft
- **Status:** OPEN
- **Cross-ref:** TECH_DEBT-120 (sister; closes per_core_slow arch test gap) / `plans/v5.15-live-readiness/plan_checks/2026-05-24-train-serve-asymmetry-sweep.md` finding C2

### TECH_DEBT-123 — foxml_suite cfg-source-of-truth structural fix (lives_in_struct-aware parser dispatch)

- **Created:** 2026-05-24 by `v5.15.5.F.4d.1.B.3` WIP-8 audit cycle (foxml_suite cfg-source-of-truth audit)
- **Severity:** HIGH (operator-visible cfg drift + dead routing metadata; affects every operator using foxml_suite for backtest training)
- **Surface:** `foxml_suite.cpp:293-311` (boot cfg seed) / `Backtest/BacktestPanels.hpp` (RunControl + Optimizer + RunHistory cfg paths) / `GUI/SettingsPanel.hpp` (no `lives_in_struct` filtering) / `CoreFrameworks/CfgFieldRegistry.hpp:163-166` (STRUCT_BACKTEST_CFG/CONTROLLER_CFG/SECRETS_CFG/TRAINING_CFG enum — dormant; zero consumers gate by `lives_in_struct`)
- **What's deferred:** Implement `lives_in_struct`-aware parser dispatch so backtest.cfg becomes a thin sidecar with only BACKTEST_CFG-tagged fields, NOT a full engine.cfg clone. Today: `backtest.cfg` is byte-for-byte first-boot copy of `engine.cfg`; idempotent-skip on subsequent boots; the two files drift silently. Phase F structurally encoded this drift into stamp HMAC body (stamp_emit reads `results->config_used` from backtest.cfg; live engine reads engine.cfg). Routing enum exists but ZERO consumers; dead metadata accumulating.
- **Why deferred (not effort-avoidance):** Already queued at `v5.15.6.A/B/C` cfg unification follow-on per `plans/_future/2026-05-14-v5.15.6-master-cfg-surface-unification-followon.md`. Sub-ship `.A` covers controller.cfg; `.B` covers secrets.cfg; `.C` covers training.cfg. STRUCT_BACKTEST_CFG (the foxml_suite-specific surface) is implied by the design but explicit binding for the operator-visible cfg drift symptom needs explicit scope addition to one of `.A/.B/.C` or as `.D`. Sister to B4 finding (applies_to_op_mode_cat dormant — same dormant-metadata pattern).
- **Cost estimate:** ~2-3 days focused per cfg-file sub-ship; ~250-350 LOC each per template at `plans/v5.15-live-readiness/subplans/2026-05-14-v5.15.5.F.4i-backtest-cfg-integration.md`
- **Trigger:** `v5.15.6.A` plan body draft kickoff (post-`.F.4f` close)
- **Status:** OPEN
- **Cross-ref:** TECH_DEBT-050/051/052 (predecessor cfg unification entries) / TECH_DEBT-053 (Phase 2 cfg struct unification) / `plans/_future/2026-05-14-v5.15.6-master-cfg-surface-unification-followon.md` / `plans/v5.15-live-readiness/plan_checks/2026-05-24-train-serve-asymmetry-sweep.md` finding B4 (sibling dormant-metadata gap) / `plans/_future/2026-05-12-decoupling-endgoal-roadmap.md` (foxml_suite refactor positioning)

### TECH_DEBT-124 — Cross-tool stamp-emit CI guard (defensive; prevents Path C resurrection)

- **Created:** 2026-05-24 by `v5.15.5.F.4d.1.B.3` WIP-8 audit cycle (/parity-check finding MED-1)
- **Severity:** LOW (defensive only; no current violation; Path C deletion verified clean)
- **Surface:** NEW `tools/check_no_cross_tool_stamp_emit.py` (sister to `tools/check_per_core_registry_integrity.py` shape)
- **What's deferred:** Add CI check that rejects any new file under `tools/` or `scripts/` that emits `stamp_format_version=` or HMAC-stamp bytes. Currently `find tools/ scripts/ -name "*.sh" -o "*.py"` shows ZERO files emit stamp bytes — Path C deletion verified the cross-tool surface is eliminated. Only `Stamp_AssembleAndEmit` → `stamp_write_for_model` chain emits. Layer 7 cross-tool surface effectively closed. The defensive guard prevents a future contributor reintroducing `tools/stamp_*.sh` (resurrecting the surface).
- **Why deferred (not effort-avoidance):** Defensive guard against low-probability future regression. Not blocking any current work. Per `wire-format-byte-preservation-discipline.md` Layer 7 discipline still active for non-framework-driven cross-tool surfaces (preserved correctly today via Path C narrative).
- **Cost estimate:** ~1h (sister Python tool + add to CI sweep + test fixture)
- **Trigger:** `.F.5.A` ML framework parity ship close (consolidate with other CI tools) OR earlier if any cross-tool stamp emit surfaces
- **Status:** OPEN (DEFERRED-INDEFINITE acceptable per low-recurrence-risk shape)
- **Cross-ref:** `DESIGN_SPECS/wire-format-patterns/wire-format-byte-preservation-discipline.md` Layer 7 / `tools/check_per_core_registry_integrity.py` (sister shape) / `plans/v5.15-live-readiness/plan_checks/2026-05-24-train-serve-asymmetry-sweep.md` finding MED-1

### TECH_DEBT-107 — 49-globals registry-default-vs-manual-default sweep (PARTIAL CLOSED at v5.15.5.F.4d.1.B.3 Step 8.6; 16 DIFFER cases follow-up pending)

- **Created:** 2026-05-19 by `v5.15.5.F.4d.1.B.3` v1.16 amendment (Caramel "no defers for effort" directive — promote from defer to active scope at Phase K Step 8.6); historical reference scattered across plan body + handoffs + universal-cfg-field-registry-pattern.md but standalone entry MISSED at creation time. Entry FORMALLY CREATED 2026-05-24 at `.B.3` ship-close documentation gap fix.
- **Severity:** MED (operational-policy defaults divergent from registry-source-of-truth discipline; risk = future operator edits one without the other → silent drift)
- **Surface:** `CoreFrameworks/ControllerConfig.hpp` `ControllerConfig_Default<F>()` body (manual `cfg.X = ...` assignments post-line-1490 `FOREACH_GLOBAL_CFG_FIELD(EMIT_GLOBAL_CFG_DEFAULT)` auto-emit); `CoreFrameworks/CfgFieldRegistry.hpp` `FOREACH_GLOBAL_CFG_FIELD` PAYLOAD column (registry defaults; single source of truth per `DESIGN_SPECS/framework-patterns/universal-cfg-field-registry-pattern.md` v1.1 § "Registry default precedence over manual defaults")
- **What's deferred / status at `.B.3` close:**
  - **12 MATCH cases CLOSED** at Step 8.6 (commit `b4843b0`): registry default == manual default → manual line DELETED (poll_interval / max_positions / init_arena_use_hugepages / acknowledge_hardcoded_strategy_in_live / ml_backend / regime_model_backend / record_ticks + record_depth + record_max_days / notify_backend + notify_cooldown_secs / held_out_gate_strict + allow_cross_major_engine + auto_stamp_on_held_out / acknowledge_hot_swap_with_open_positions / xgb_min_child_weight + xgb_seed / xgb_train_nthread / ws_dead_time_flatten_threshold_secs / trading_mode / engine_arch / sharded_force_synthetic / lazy_rebuild_force_period_us / use_aot_inference / wf_split_max_gb)
  - **16 DIFFER cases PARTIAL CLOSED** with inline rationale comments + KEEP-MANUAL markers — manual override PRESERVED because operational context warrants it; registry-default update could break test fixtures + operator muscle memory if applied without per-row consent. **Follow-up: revisit each DIFFER case to decide (a) update registry default to match manual + delete manual line (preferred structural close per registry-source-of-truth discipline) OR (b) keep manual + document permanent operational-exemption rationale.** 16 DIFFER cases:
    - warmup_ticks (registry INT(0); manual=128 — operational floor for trading-ready boot)
    - min_warmup_samples (registry INT(64); manual=0 — preserves pre-cfg behavior; explicit disable)
    - slow_path_max_secs (registry INT(60); manual=3 — HFT-correct per-cycle budget)
    - require_mlockall (registry BOOL(0); manual=1 — HFT-correct safety-first)
    - danger_enabled (registry BOOL(0); manual=1 — safety gradient ON)
    - xgb_eval_nthread (registry INT(4); manual=1 — per-fold determinism for validation parity)
    - csv_load_workers (registry INT(4); manual=1 — serial back-compat)
    - multi_horizon_max_threads (registry INT(4); manual=1 — **CRITICAL v5.11.45 segfault avoidance**; XGBoost+libgomp+pthread interaction fragile)
    - feature_collect_max_gb (registry INT(8); manual=12 — operator-favored ceiling)
    - held_out_max_gb (registry INT(8); manual=4 — tighter held-out fold)
    - health_log_max_bytes (registry INT(1MB); manual=0 — no rotation back-compat)
    - health_log_keep_count (registry INT(5); manual=0 — keep all back-compat)
    - health_log_level (registry INT(1=debug); manual=0=info — less verbose default)
    - reconcile_interval_sec (registry INT(60=periodic); manual=0=boot-only back-compat)
    - reconcile_mode (registry INT(0=STRICT); manual=1=WARN — matches dry_run=1 legacy)
    - model_verify_strict (registry INT(-1=skip); manual=0=warn — surfaces mismatches)
    - csv_sort_check_mode (registry INT(1=STRICT); manual=CSV_SORT_WARN(0) — log + proceed per v5.9.2c contract)
    - recovery_delay_secs (registry INT(60); manual=30 — tighter reconcile window)
    - param_max_age_ticks (registry INT(100000); manual=1000 — catches stale params sooner)
    - slow_path_pin_offset (registry INT(-1=no-pin); manual=0=auto-derive — operationally distinct semantics)
    - num_execution_cores (registry INT(1); manual=4 — operator-default for 4-core production deployment)
- **Why deferred (not effort-avoidance):** DIFFER cases carry per-row operational context (safety-first / back-compat / segfault avoidance / per-fold determinism / operator-tuned values). Auto-applying registry-default-as-source-of-truth without per-row consent risks: (a) test-fixture breakage (existing tests rely on current default behavior); (b) operator muscle-memory disruption (existing cfg files without these fields would shift behavior on next boot); (c) potential v5.11.45-class regressions (multi_horizon_max_threads is the canonical example — registry default of 4 would re-enable a known segfault class). Per-row revisit needs operator decision at low time-pressure.
- **Cost estimate:** ~2-3h focused (16 rows × per-row analysis + decision + commit + test verify). Risk LOW because changes are bounded to cfg defaults; no algorithmic shifts.
- **Trigger:** Next ship touching `CoreFrameworks/ControllerConfig.hpp` body (likely `.F.4f` cleanup OR `v5.15.6.A/B/C` cfg unification follow-on OR any sub-ship that adds a new global cfg field — that ship absorbs DIFFER revisit naturally). Could also be standalone cleanup ship if scope-bounded preference emerges.
- **Status:** PARTIAL CLOSED at v5.15.5.F.4d.1.B.3 commit `b4843b0` (12 of 28 audit-targeted rows fully closed; 16 DIFFER cases inline-documented with KEEP-MANUAL rationale awaiting operator-decision per-row). Remaining 21 of 49 globals didn't appear in manual default block at all (already handled by FOREACH_GLOBAL_CFG_FIELD(EMIT_GLOBAL_CFG_DEFAULT) auto-emit alone). Original entry stated "OPEN+CLOSE at this ship per Caramel no-defers directive" — closure is now PARTIAL pending per-row DIFFER decisions; status PARTIAL CLOSED is honest (12 sites fully closed; 16 documented but not algorithmically-closed).
- **Cross-ref:** `DESIGN_SPECS/framework-patterns/universal-cfg-field-registry-pattern.md` v1.1 § "Registry default precedence over manual defaults" (the discipline this entry implements) / `CoreFrameworks/ControllerConfig.hpp:1478+` (the sweep target) / `CoreFrameworks/CfgFieldRegistry.hpp:870-1050` (FOREACH_GLOBAL_CFG_FIELD PAYLOAD column source-of-truth) / `plans/v5.15-live-readiness/postmortems/2026-05-24-v5.15.5.F.4d.1.B.3-postmortem.md` § "What went sideways / lessons learned" (DIFFER complexity surfaced; KEEP-MANUAL rationale captured) / `plans/v5.15-live-readiness/subplans/2026-05-17-v5.15.5.F.4d.1.B.3-legacy-empty-out.md` Step 8.6 (v1.16 amendment 2026-05-19) / `feedback_no_defer_for_effort` (parent meta-rule — TECH_DEBT-107 was scope-promoted from defer to active per this rule; PARTIAL CLOSURE preserves the rule's spirit while honoring per-row operator-decision discipline) / `feedback_motivated_collaborator_for_caramel` (DIFFER cases warrant explicit operator review; auto-apply would have produced inferior software per best-software-path discipline)

### TECH_DEBT-126 — Two-axis versioning rework (separate internal ship tag from external SemVer)

- **Created:** 2026-05-25 by `v5.15.5.F.4d.1.B.4` v1.7.3 cycle (Caramel observation during B.3 audit pause; "ENGINE_VERSION is 5.X but the project isn't really a 1.0 yet — i think we should rework versioning")
- **Severity:** MED (external-positioning concern; first-impression load-bearing for active hedge-fund MDs + head-researcher direct outreach per `user_public_work_attracts_hedge_funds` — confirmed live engagement per Caramel 2026-05-25, not theoretical visibility. Pre-1.0 alpha framing sets correct expectation; current `v5.15` looks like mature SemVer to outside readers and may confuse on active breaking-change churn vs implied stability commitments. NOT blocking current work but should not slip past paper-test session entry.)
- **Surface:** `Version.hpp` (ENGINE_VERSION_STRING single value mixing two concerns); `README.md` (public-facing version); GitHub release notes; HMAC stamp `stamp_format_version` field (uses ship tag; preserve current behavior); any docs that cite the version
- **What's deferred:** Separate two version concerns:
  - **SHIP_TAG** (current `5.15.5.F.4d.1.B.4` format) — internal sprint+phase+iteration+ship granularity; bumped per ship; preserves audit-driven discipline + rollback-anchor naming; HMAC stamps + persisted artifacts continue using this for precision
  - **SEMVER** (NEW; e.g., `0.9.0-alpha`) — external operator-facing positioning; bumped at meaningful milestones (alpha→beta→1.0→1.x); README/GitHub releases lead with this
  - Version.hpp gets BOTH macros + a legacy alias for code reading ENGINE_VERSION_STRING; semver added on top of existing field
- **Why this matters:** Current `v5.15` LOOKS like a mature post-1.0 release with backward-compat guarantees that haven't been committed. External readers (hedge funds per `user_public_work_attracts_hedge_funds`; potential contributors per AGPL visibility) may form wrong impression OR get confused by active breaking-change churn vs implied stability. Pre-1.0 alpha framing is honest + sets correct expectations.
- **Why deferred (not effort-avoidance):** Tangential to current `.B.4` train-serve execution-layer parity work; would scope-creep the current ship if absorbed. Versioning convention decision needs sit-with-it time (what's "1.0" mean for this project? probably post-paper-test session validation + a few months live without major churn).
- **Cost estimate:** ~1-2h focused (pick semver starting point; update Version.hpp + README + GitHub release notes; migration note; document two-axis convention; possibly add `.B.4` Phase D CI check for "both macros defined")
- **Trigger:** Sooner-rather-than-later per confirmed hedge-fund engagement. Candidate housekeeping ship after `.B.4` ships + paper-test session entry stabilizes. Options: standalone `v5.16-versioning-rework` micro-sprint OR fold into `v5.16.0.A` early ship if natural fit OR consolidate with `.B.12` umbrella close housekeeping. Should not slip past paper-test session entry given first-impression visibility risk.
- **Status:** OPEN
- **Cross-ref:** `Version.hpp` ENGINE_VERSION_STRING / `README.md` / `user_public_work_attracts_hedge_funds` memory (external visibility positioning) / `user_mvp_to_professional_transition` memory (project lifecycle phase) / SemVer 2.0.0 spec (https://semver.org/) for canonical pre-1.0 + alpha/beta conventions

### TECH_DEBT-127 — Full controller_test.cpp domain-aligned split (sister to -114 PARTIAL_CLOSURE)

```yaml
id: TECH_DEBT-127
title: Full controller_test.cpp domain-aligned split (9 sub-files; 287 sections)
severity: medium
surface_tags: [test-infrastructure, file-size-discipline]
trigger: operator-prioritization OR test-additions blocked by file size
status: open
opened: 2026-05-27
related_specs: [DESIGN_SPECS/doc-disciplines/file-size-split-discipline.md]
sister_debt: TECH_DEBT-114 (PARTIAL_CLOSURE at .B.5)
```

- **Created:** 2026-05-27 at v5.15.5.F.4d.1.B.5 PARTIAL_CLOSURE pivot. Operator directive ("more concerned about actual code") prioritized engine code work (`.B.6+`) over full test split.
- **Severity:** MEDIUM (test infrastructure; engine semantics untouched; navigation cost only). Lower priority than engine code maintainability per operator framing.
- **What's deferred:** Full domain-aligned split of `tests/controller_test.cpp` (currently 26,129 lines / 287 sections post-WIP-B1) into 9 sub-files per Phase A CSV mapping at `plans/v5.15-live-readiness/plan_checks/2026-05-27-v5.15.5.F.4d.1.B.5-section-to-domain-mapping.csv`. Sub-files: engine_boot / engine_oms / engine_position / features / stamps / ml_inference / ml_state / ml_training / misc. Extraction shape needs Python script with brace-matching for 261 inline main() `{...}` blocks (29 standalone test_*() functions are trivial; main() body sections are the complexity).
- **What's already done (.B.5 WIP-B1):** Shared infrastructure extracted to `tests/test_common.hpp` (includes / counters / check() / static_asserts / FP / test_warmup_ctrl); `inline int` C++17 discipline established (counter shared across TUs when linked into umbrella binary; per-binary independent when sub-binaries are separate programs). controller_test.cpp 26,259 → 26,129 lines.
- **Cost estimate:** ~5-15h focused work (Python brace-matching script + per-domain extraction + 9 sub-binary CMakeLists.txt targets + umbrella linking + verify counts at each step + dedicated rollback anchor).
- **Trigger:** Operator-prioritization OR when test additions get blocked by file size. The Phase A CSV + WIP-B1 helper extract remain available as a head-start whenever the work is picked up.
- **Status:** OPEN.
- **Cross-ref:** TECH_DEBT-114 (PARTIAL_CLOSURE; sister); Phase A CSV; `feedback_no_defer_for_effort.md` (this is operator-prioritized defer, not effort-avoidance); `DESIGN_SPECS/doc-disciplines/file-size-split-discipline.md` (parent pattern).

### TECH_DEBT-129 — Per-core drainer architecture exploration

```yaml
id: TECH_DEBT-129
title: Per-core drainer architecture exploration (cache locality + pipeline parallelism)
severity: low
surface_tags: [drainer, threading, cache-locality, dod-architecture]
trigger: post-paper-test-session OR drainer-thread profiling shows bottleneck
status: open
opened: 2026-05-27
related_specs: []
sister_debt: TECH_DEBT-029 (file-size discipline; per-core drainer would touch EngineSharded.hpp Async.hpp + SlowPath.hpp post-.B.6 split)
```

- **Created:** 2026-05-27 at v5.15.5.F.4d.1.B.6 planning during operator-driven architectural exploration. Operator interested specifically in cache locality wins ("cache locality would be the bigger win here, it would give more room to work with").
- **Severity:** LOW (exploration; not blocking). Could become MEDIUM if paper-test session shows drainer-thread bottleneck.
- **Surface:** Drainer thread (currently single; processes all order-flow events for all cores) + per-core slow-path threads (already exist).
- **Future-roadmap doc:** `plans/_future/2026-05-27-percore-drainer-architecture.md` (created at this TECH_DEBT open)
- **What's queued:** Three nested architectural options (Option A → C; increasing scope):
  - **Option A (scoped):** Per-core `drain_manual_closes` only — GUI close events routed to specific core's slow-path queue
  - **Option B (hybrid):** Global drainer keeps market-driven events (fills/post-fill); per-core handles operator/policy-driven events (manual close, kill switch, time exit)
  - **Option C (full):** Per-core drainer architecture — fold all drainer responsibilities into per-core slow-path threads; eliminate central drainer; single API client serialized via threadsafe queue
- **Headline win (per operator):** Cache locality — each core touches ONLY its own `state.cores[c]` cluster (perfect L1 locality vs current sequential walk across all cores). Other wins: pipeline parallelism (N cores process events in parallel), NUMA-aware (per-core threads pinned), latency win for GUI responsiveness, backpressure isolation, removes single-thread-bottleneck risk.
- **Cost estimate:** Option A ~1-2 days; Option B ~3-5 days; Option C ~1-2 weeks (largest because central drainer's API-client integration requires threadsafe serialization layer).
- **Prerequisites:** Paper-test session throughput data showing whether global drainer is actual bottleneck. Decoupling roadmap stability (runtime/viewer split per `plans/_future/2026-05-12-decoupling-endgoal-roadmap.md`).
- **Trigger:** post-paper-test-session (data-driven decision) OR drainer-thread profiling shows >50% CPU during normal ops OR multi-core latency p99 > slow-path budget.
- **Status:** OPEN with explicit trigger (architectural exploration; not immediate priority).
- **Cross-ref:** future-roadmap doc has full pro/con analysis + nested options; `decoupling-endgoal-roadmap.md` (sister architectural-exploration doc); CLAUDE.md § Concurrency model (current architecture diagram).

### TECH_DEBT-130 — Defensive nullptr guards in EngineSharded/Async.hpp fan_out body (runtime-dead under USE_IMGUI_GUI build)

```yaml
id: TECH_DEBT-130
title: 4 defensive nullptr guards in EngineSharded/Async.hpp fan_out body — runtime-dead under USE_IMGUI_GUI build
severity: low
surface_tags: [async-drainer, branch-density, micro-optimization, post-paper-test]
trigger: post-paper-test profiling shows fan_out variance
status: open
opened: 2026-05-27
related_specs: [DESIGN_SPECS/refactor-patterns/branchless-dispatch-discipline.md]
sister_debt: TECH_DEBT-029 (file-size discipline; sister at same Async.hpp surface)
```

- **Created:** 2026-05-27 at v5.15.5.F.4d.1.B.6 Phase C audit gate (4-agent verdict GREEN with 2 YELLOW/cosmetic findings logged for post-paper-test triage).
- **Severity:** LOW (runtime-dead under USE_IMGUI_GUI build; branchless-dispatch discipline H20 sister; optional polish).
- **Surface:** `CoreFrameworks/EngineSharded/Async.hpp` `fan_out` lambda body, 4 nullptr guard sites:
  - Line 238: `if (gui_quit_ptr != nullptr)` — gui-thread signal check (always non-null under USE_IMGUI_GUI; null only in headless build path)
  - Line 286: similar guard at parallel gating site
  - Line 368: similar guard at parallel gating site
  - Line 465: similar guard at parallel gating site
- **Class:** Branchless-dispatch sister (H20). 4 defensive nullptr checks add 4 branch sites in producer-thread fan_out body. Under USE_IMGUI_GUI build, all 4 are runtime-dead (gui_quit_ptr is always non-null). Under headless build path (if reactivated post-paper-test), the guards are load-bearing.
- **What's deferred:** Two optional polish paths:
  1. **`__builtin_expect(ptr != nullptr, 1)` hint** — 1-line change per site; signals to compiler that null path is rare. Branch density unchanged but predicted-correctly-path optimization improves p99 marginally.
  2. **Build-flag-gated body** — `#ifdef USE_IMGUI_GUI` wraps the guarded body without the check; `#else` keeps the guard. Removes 4 branches under GUI build entirely.
- **Why deferred (not effort-avoidance):** Optional polish; not blocking. fan_out is in producer-thread (single-tick budget); 4 branches × 30-100ns mispredict cost is ≤0.4μs worst-case per tick, well below tick budget. Pure perf optimization fits future-headache-vs-optimization-scope-framework `defer` bucket (no anti-pattern instance survives; no class can recur).
- **Cost estimate:** ~30-60 min (per option). Option 2 (build-flag gating) is preferred long-term per branchless-dispatch discipline.
- **Trigger:** Address when (a) post-paper-test profiling shows fan_out variance impacting p99 (data-driven), OR (b) headless build path gets reactivated for v6.X decoupling work + fan_out is on a different latency budget, OR (c) /latency-track skill flags producer-fan-out variance during quarterly cadence.
- **Status:** OPEN with explicit data-driven trigger (post-paper-test).
- **Cross-ref:** v5.15.5.F.4d.1.B.6 Phase C 4-agent audit (YELLOW-1 finding logged); CLAUDE.md H20 (branchless dispatch preferred for SP/HP/drainer/producer); `DESIGN_SPECS/refactor-patterns/branchless-dispatch-discipline.md`; `feedback_future_headache_vs_optimization_scope_framework`.

### TECH_DEBT-131 — Stale `EngineSharded.hpp:LINENO` comment refs in sibling files

```yaml
id: TECH_DEBT-131
title: 7 stale `EngineSharded.hpp:LINENO` comment refs in sibling files (cosmetic; comments-only drift post-subfolder-split)
severity: low
surface_tags: [stale-comments, code-hygiene, post-refactor-residue, doc-discipline]
trigger: next stale-comment audit OR /metadata-audit quarterly cadence
status: open
opened: 2026-05-27
related_specs: []
sister_debt: TECH_DEBT-029 (file-size discipline; sister at same `.B.6` subfolder-split surface)
```

- **Created:** 2026-05-27 at v5.15.5.F.4d.1.B.6 Phase C audit gate (4-agent verdict GREEN with 2 YELLOW/cosmetic findings logged).
- **Severity:** LOW (cosmetic; comments-only drift; no behavior or build impact).
- **Surface:** 7 stale `EngineSharded.hpp:LINENO` comment references in sibling files. Each cites a specific line in the pre-`.B.6`-split monolithic `EngineSharded.hpp` (now 3,202 → 96 INDEX shim; sub-files at `EngineSharded/Boot.hpp` / `SlowPath.hpp` / `Async.hpp` / `Run.hpp` contain the actual referenced code). Sites:
  - `ML_Headers/EnsembleHotSwap.hpp:86` — references monolithic line
  - `CoreFrameworks/EngineCommon.hpp:83` — references monolithic line
  - `CoreFrameworks/EngineCommon.hpp:150` — references monolithic line
  - `CoreFrameworks/EngineCommon.hpp:179` — references monolithic line
  - `CoreFrameworks/ShardedSnapshotPersist.hpp:502` — references monolithic line
  - `ML_Headers/CoreModelZoo.hpp:2879` — references monolithic line
  - `ML_Headers/CoreModelZoo.hpp:2896` — references monolithic line
  - `CoreFrameworks/ControllerEventLoop.hpp:3512` — references monolithic line
- **Class:** Stale-comment drift class. Sister to Class 31 (hardcoded refs in always-loaded docs); same root cause (canonical-list duplication via inline reference vs registry/grep-driven retrieval), different surface (inline comments in sibling source files vs always-loaded docs).
- **What's deferred:** Sweep + update each stale comment to point at correct sub-file:
  - Either `CoreFrameworks/EngineSharded.hpp` (INDEX SHIM)
  - Or specific sub-file (e.g., `CoreFrameworks/EngineSharded/Async.hpp:NNN`)
  - Or REPLACE with categorical reference (e.g., "producer-thread fan_out body in EngineSharded module") per [[feedback_categorical_triggers_over_hardcoded_refs]] — preferable to line-anchored refs since sub-files will continue to grow
- **Why deferred (not effort-avoidance):** Pure cosmetic; no behavior/build impact. Risk of breaking comments via mechanical sed is low but non-zero. Fits future-headache-vs-optimization-scope-framework `defer` bucket (anti-pattern instance is the stale comment itself — but it's NOT an instance of an unclosed bug class survivable past ship; the comments are residue from a NOW-closed `EngineSharded.hpp` monolith).
- **Cost estimate:** ~30-45 min (mechanical sweep + manual review + sed-based update OR categorical-reference rewrite).
- **Trigger:** Address when (a) next stale-comment audit fires, OR (b) /metadata-audit quarterly cadence catches the drift, OR (c) any of the sibling files is touched for unrelated work + comment update folds in naturally.
- **Status:** OPEN with quarterly-cadence trigger.
- **Cross-ref:** v5.15.5.F.4d.1.B.6 Phase C 4-agent audit (YELLOW-2 finding logged); RECURRING_BUG_PATTERNS Class 31 (sister at always-loaded-docs surface); `feedback_categorical_triggers_over_hardcoded_refs`; `feedback_metadata_audit_quarterly`.

**UPDATE 2026-05-27 at v5.15.5.F.4d.1.B.7 — operator-facing-doc cohort scope ADDED + CLOSED; status PARTIAL_CLOSURE:**

Post-`.B.6` codebase-wide sweep (`/dust` + `/trace-deps`) surfaced ADDITIONAL stale `EngineSharded.hpp:LINENO` refs in operator-facing DOCS that were missed at `.B.6` close. Per `feedback_operator_facing_doc_cohort_at_cfg_deletion` (codified `.B.4`; should have applied at `.B.6` close but didn't — Class 33 recurrence). Cohort:

- `DOCS/KNOWN_ISSUES.md:143` — Lambda capture warning ref (was `EngineSharded.hpp:2085` → updated to `EngineSharded/Async.hpp` fan_out body)
- `DOCS/KNOWN_ISSUES.md:319` — CumDelta ref (was `EngineSharded.hpp:2663` → updated to `EngineSharded/SlowPath.hpp` slow-path body)
- `DOCS/PARITY_ISSUES.md:544` — PARITY-009 boot ref (was `EngineSharded.hpp:1075-1240` → updated to `EngineSharded/Run.hpp` boot section)
- `DOCS/PARITY_ISSUES.md:553` — PARITY-009 boot ref (was `EngineSharded.hpp:1157-1240` → updated)
- `DOCS/PARITY_ISSUES.md:610` — PARITY-010 InitExitBandits + LoadExitBanditState (was `:1180` + `:1200` → updated)
- `DOCS/PARITY_ISSUES.md:655` — PARITY-011 VerifyExpected (was `:1108-1131` + `:1114` → updated)
- `DOCS/PARITY_ISSUES.md:697` — PARITY-012 ValidateAgainstCfg (was `:1229` → updated)
- `DOCS/PARITY_ISSUES.md:798/803/810` — PARITY-015 ensemble snapshot publish (was `:646-694` already audit-flagged stale → updated to `ShardedSnapshot.hpp:677-694`)

All 8 doc citations updated with post-`.B.6` sub-file annotation preserving original line refs for historical context (per `feedback_archived_changelog_preservation_discipline` + `feedback_categorical_triggers_over_hardcoded_refs`). Closed by amendment at `.B.7`.

LEAVE per discipline: ~14 ARCHIVED + CLOSED-historical refs in `DOCS/CHANGELOG.md` historical rows + `DOCS/changelogs/2026-04-09-*` + closed PARITY entries (PARITY-003/-023/-025/-026/-027/-028/-029/-030 all `closed_at`) + bug-class historical citations (`class-03-drain-count-under-partials.md:38`).

**Source-file cohort (original 8 sites) STILL OPEN — next stale-comment audit OR quarterly `/metadata-audit` triggers.** Status: PARTIAL_CLOSURE (operator-facing-doc cohort closed; source-file cohort pending). Sister to Class 33 recurrence (consumer-enumeration-undercount on deletion) — `.B.7` confirms the discipline applies to OPERATOR-FACING DOC SURFACES not just source-file consumers.

---

### TECH_DEBT-133 — `EngineSharded_Run` mega-function deferred per code-LOC methodology

```yaml
id: TECH_DEBT-133
title: EngineSharded_Run mega-function deferred per code-LOC methodology (sister to TECH_DEBT-029)
severity: low
surface_tags: [code-organization, file-size, sister-to-029, ai-driven-workflow-scoped]
trigger: future-runtime-decoupling-OR-per-core-drainer-natural-extraction-surfaces
status: open
opened: 2026-05-27
related_specs: [DESIGN_SPECS/doc-disciplines/file-size-split-discipline.md]
```

- **Created:** 2026-05-27 (surfaced at `.B.6` Phase B.4.1 revert with code-LOC methodology codification; deferral confirmed at `.B.7` C1 close-out)
- **Severity:** LOW
- **Surface:** `CoreFrameworks/EngineSharded/Run.hpp` `EngineSharded_Run` function — 2,050 raw lines / 1,406 code-LOC (under file-size threshold per `file-size-split-discipline.md` v1.4 code-LOC methodology, but per-fn body is far over typical-fn limits)
- **Class:** Function-level code organization (sister to TECH_DEBT-029 file-level closure as `wontfix-per-ai-workflow` at `.B.7`)
- **What's deferred:** Function-level split into separate boot + slow-path-orchestrator helpers. Per `feedback_count_code_loc_not_total_lines` discipline + AI-driven workflow scoping (Claude 1M context handles 6K-line files trivially), no urgent compile/cognitive load.
- **Why deferred (not effort-avoidance):** Per-fn-LOC limits are typical-human-readable concern; AI workflow doesn't have same cognitive ceiling. Sister to TECH_DEBT-029 (file-size discipline closed `wontfix-per-ai-workflow` at `.B.7` C1 close-out).
- **Status:** **OPEN — DEFERRED-INDEFINITE.** Natural extraction surfaces will surface during `.E` per-core drainer rework OR future runtime-decoupling work (v6.X). Re-evaluate then.
- **Trigger:** Address when (a) `.E` per-core drainer architecture (TECH_DEBT-129) creates natural extraction surfaces, OR (b) v6.X runtime-decoupling work fragments the file naturally, OR (c) human contributors join project + cognitive-load concern surfaces.
- **Retroactive ledger write:** This entry was claimed OPEN-DEFERRED-INDEFINITE in `.B.6` postmortem + `.B.7` postmortem + multiple plan body amendment sections but missed ledger write at ship close. Retroactively written at 2026-05-27 PM during `/accept-handoff` Stage 4.5 forward-promise verification dogfood.
- **Cross-ref:** TECH_DEBT-029 (sister; closed wontfix-per-ai-workflow at `.B.7`); TECH_DEBT-129 (sister `.E` per-core drainer architecture — natural extraction surface); `feedback_count_code_loc_not_total_lines`; `DESIGN_SPECS/doc-disciplines/file-size-split-discipline.md` v1.4 "AI-driven workflow scoping" section; `.B.6` postmortem (code-LOC methodology codification); `.E` per-core drainer scaffold at `subplans/2026-05-27-v5.15.5.F.4d.1.E-per-core-drainer-architecture-SCAFFOLD.md`.

---

### TECH_DEBT-135 — Class 11 `regime_names[]` hardcoded sibling-array (registry-fit-audit finding)

```yaml
id: TECH_DEBT-135
title: Class 11 regime_names[] hardcoded sibling-array (registry-fit-audit finding)
severity: medium
surface_tags: [registry-fit, class-11, hardcoded-sibling-array, ml-pipeline, regime]
trigger: sub-ship-v5.15.5.F.4d.1.F-professionalization-audit-sweep
status: open
opened: 2026-05-27
related_specs: [DOCS/recurring-bug-patterns/class-11-hardcoded-sibling-array.md]
```

- **Created:** 2026-05-27 (surfaced at post-`.B.6` `/registry-fit-audit` codebase-wide sweep; queued at `.B.7` for `.F`)
- **Severity:** MED
- **Surface:** `regime_names[]` hardcoded array — manual N-site duplication; sister to candidate `FOREACH_REGIME` registry
- **Class:** Class 11 (Hardcoded sibling-array — registry-fit candidate)
- **What's deferred:** Migrate `regime_names[]` to `FOREACH_REGIME` registry walk + auto-flow per regime addition. Removes hardcoded duplication; new regime additions become 1-row registry edits.
- **Why deferred (not effort-avoidance):** Out of `.B.7` scope-bound bugfix cohort + `.B.8` scope-bound accounting cohort. Natural triage at `.F` professionalization audit sweep where `/registry-fit-audit` re-fires against post-framework-lock codebase.
- **Status:** **OPEN** — queued for `.F` triage. Likely fix-now fold at `.F` if `/registry-fit-audit` confirms.
- **Trigger:** `.F` ship (`v5.15.5.F.4d.1.F` comprehensive professionalization audit sweep).
- **Retroactive ledger write:** This entry was claimed OPEN-queued-for-`.F` in `.B.7` postmortem "Followup work" but missed ledger write at ship close. Retroactively written at 2026-05-27 PM during `/accept-handoff` Stage 4.5 forward-promise verification dogfood.
- **Cross-ref:** `plans/v5.15-live-readiness/postmortems/2026-05-27-v5.15.5.F.4d.1.B.7-postmortem.md` "Followup work"; `.F` scaffold at `subplans/2026-05-27-v5.15.5.F.4d.1.F-professionalization-audit-sweep-SCAFFOLD.md`; `DOCS/recurring-bug-patterns/class-11-hardcoded-sibling-array.md`; `feedback_proactive_novel_alternative_consideration` (consider novel alternative at fix time — e.g., metadata-bit categorical tag pattern vs raw FOREACH).

---

### TECH_DEBT-136 — B-Plus v0.5 mechanical-migration audit (Stage 6 escalation candidate)

```yaml
id: TECH_DEBT-136
title: B-Plus v0.5 mechanical-migration audit (Stage 6 M7 escalation candidate)
severity: medium
surface_tags: [ci-tooling, b-plus, mechanical-migration, m7-stage-6, class-14, class-26]
trigger: sub-ship-v5.15.5.F.4d.1.F-professionalization-audit-sweep
status: open
opened: 2026-05-27
related_specs: [DESIGN_SPECS/meta-disciplines/structural-enforcement-when-memory-insufficient.md]
```

- **Created:** 2026-05-27 (surfaced at post-`.B.6` `/bug-check` sweep + `.B.7` AI-introduced-bug pattern recognition; queued at `.B.7` for `.F`)
- **Severity:** MED
- **Surface:** `tools/check_plan_body_symbol_existence.py` (B-Plus CI tool; current version v0.4)
- **Class:** Stage 6 escalation candidate per M7 (`structural-enforcement-when-memory-insufficient.md`). Sister to existing B-Plus v0.4 generator mode + `/capture-audit` Check 8 (cfg-field categorization mechanical sidecar).
- **What's deferred:** Extend B-Plus to v0.5 with mechanical-migration audit feature. Catches AI-introduced bugs from mechanical substitutions:
  - Class 14 (fabricated symbols in plan body code samples)
  - Class 26 sub-shape A (wrong-index paired-access at mechanical migration cohorts — already caught by Check 9 in `check_per_core_registry_integrity.py`)
  - Class 26 sub-shape B (UNINDEXED-GLOBAL — caught by Check 10)
  - NEW: pre-coding plan-body-time detection of mechanical-migration substitution risk
- **Why deferred (not effort-avoidance):** Out of `.B.7`/`.B.8` scope-bound cohort. Natural triage at `.F` audit ship where broader CI tooling consolidation happens (sister to `.D` framework consolidation).
- **Status:** **OPEN** — queued for `.F` triage. Stage 6 escalation per M7 if `.F` audit confirms recurrence pattern.
- **Trigger:** `.F` ship (`v5.15.5.F.4d.1.F` comprehensive professionalization audit sweep) OR earlier sister ship if AI-introduced-bug class recurs.
- **Retroactive ledger write:** This entry was claimed OPEN-queued-for-`.F` in `.B.7` postmortem "Followup work" + `.B.8` postmortem cross-references but missed ledger write at ship close. Retroactively written at 2026-05-27 PM during `/accept-handoff` Stage 4.5 forward-promise verification dogfood.
- **Cross-ref:** `plans/v5.15-live-readiness/postmortems/2026-05-27-v5.15.5.F.4d.1.B.7-postmortem.md` "Followup work"; `.F` scaffold; `feedback_structural_enforcement_when_memory_insufficient` (M7 parent); `tools/check_plan_body_symbol_existence.py` v0.4 (current version); TECH_DEBT-139 (sister Check 11 Python impl — same M7 surface; same trigger ship).

---

### TECH_DEBT-140 — `engine_mode` cfg field vestigial post-`single_core` deletion

```yaml
id: TECH_DEBT-140
title: engine_mode cfg field vestigial post single_core deletion
severity: low
surface_tags: [cfg-flow, boot-time]
trigger: .E.0.1-or-.E.1
status: open
opened: 2026-05-28
related_specs: []
```

- **Created:** 2026-05-28 by v5.15.5.F.4d.1.D.1 (doc-sweep ship; surfaced via rename-candidates running-list entry 2)
- **Severity:** LOW
- **Surface:** `engine.cfg` `engine_mode` field (values `sharded | single_core`) + its parser/consumer
- **What's deferred:** With the legacy `single_core` mode deleted at `.E.0.1`, only `sharded` remains — `engine_mode` becomes vestigial (one surviving value). Delete the field + its parse/consume sites once `single_core` is gone.
- **Why deferred (not effort-avoidance):** `.D.1` is a doc-only sweep (no engine code); `single_core` deletion is `.E.0.1`/`.E.1` scope. Deleting `engine_mode` before `single_core` is gone would be premature.
- **Cost estimate:** ~1h; LOW risk; folds into the `single_core` deletion cohort.
- **Trigger:** `.E.0.1` precursor (legacy `single_core` delete) OR `.E.1` Foundation.
- **Status:** OPEN
- **Cross-ref:** `rename-candidates-running-list.md` entry 2; TECH_DEBT-002 (centralized `ControllerEventLoop` removal — sister legacy-path deletion).

---

### TECH_DEBT-141 — `BacktestSharded_Run` → `Backtest_Run` unification (Sharded qualifier dead weight)

```yaml
id: TECH_DEBT-141
title: BacktestSharded_Run to Backtest_Run unification
severity: low
surface_tags: [backtest]
trigger: .E.1
status: open
opened: 2026-05-28
related_specs: []
```

- **Created:** 2026-05-28 by v5.15.5.F.4d.1.D.1 (surfaced via rename-candidates running-list entry 4)
- **Severity:** LOW
- **Surface:** `Backtest/` — `Backtest_Run` wrapper calling `BacktestSharded_Run`
- **What's deferred:** With `single_core` gone, the "Sharded" qualifier is dead weight (only sharded backtest remains). Unify `Backtest_Run` + `BacktestSharded_Run` into one (drop the wrapper indirection).
- **Why deferred (not effort-avoidance):** Code rename; `.D.1` is doc-only. Folds naturally into the `.E.1` Core→Node code-rename cohort.
- **Cost estimate:** ~1h; LOW risk; mechanical.
- **Trigger:** `.E.1` Foundation (alongside the Core→Node rename).
- **Status:** OPEN
- **Cross-ref:** `rename-candidates-running-list.md` entry 4; `.E.1` plan body.

---

### TECH_DEBT-142 — Doc-rename tool prose-token approach unsafe for `.E.1` CODE rename (needs symbol/AST-aware tooling)

```yaml
id: TECH_DEBT-142
title: doc-rename tool prose-token approach unsafe for E.1 code rename
severity: high
surface_tags: [registry, boot-time]
trigger: .E.1
status: open
opened: 2026-05-28
related_specs: [meta-disciplines/implementation-layer-blindspot-taxonomy.md]
```

- **Created:** 2026-05-28 by v5.15.5.F.4d.1.D.1 (surfaced at Phase F — verified `.E`-plan + running-list rename auto-apply)
- **Severity:** HIGH (load-bearing for `.E.1`'s ~5,000-site Core→Node rename correctness)
- **Surface:** `tools/check_doc_rename_classification.py` (prose-token classifier) + `.E.1`'s code-rename approach
- **What's deferred:** `.D.1`'s doc-rename tool matches `per-core`/`per_core` by prose token + `transition-documentation` heuristics. At Phase F it over-flagged renames in transition-docs (running-list `Old→New` catalog; `.E` plan bodies' Class 26 / TECH_DEBT-129 title citations; accurate "currently per-core" claims). For DOCS this was caught by manual triage (B19 pillar). But `.E.1`'s **CODE** rename (`state.cores`→`state.nodes`, `MAX_CORES`→`MAX_NODES`, `CoreContext`→`NodeContext`, `FOREACH_PER_CORE_CFG_FIELD`→`FOREACH_PER_NODE_CFG_FIELD`, `core_*` cfg fields) spans ~5,000 sites and CANNOT be hand-triaged at that scale. `.E.1` needs **symbol/AST-aware** rename tooling (clang-based or equivalent) — NOT prose-token substitution — plus transition-catalog recognition (`type: running-list` frontmatter, `Old name` columns, catalog-citation context) for the doc surfaces it touches.
- **Why deferred (not effort-avoidance):** the tooling gap is specific to `.E.1`'s code-rename scope; building AST-aware tooling now (before `.E.1` plans the rename approach) would be premature. Captured so `.E.1`'s window designs the rename approach with this constraint up front.
- **Cost estimate:** part of `.E.1` Foundation planning (rename-approach design); MEDIUM-HIGH (wrong tooling corrupts the codebase at scale).
- **Trigger:** `.E.1` Foundation — rename-approach design (do NOT reuse the `.D.1` prose-token tool for code).
- **Status:** OPEN
- **Cross-ref:** B19 pillar (`implementation-layer-blindspot-taxonomy.md`); RECURRING_BUG_PATTERNS Class 36; `.E.1` plan body Core→Node rename section; `E-MASTER-REFERENCE.md` § 7; `feedback_terminology_evolution_bridge_not_history_rewrite`.

---

### TECH_DEBT-143 — Public `CHANGELOG.md` + `DOCS/changelogs/` stale for entire v5.12→v5.15 cycle (backfill)

```yaml
id: TECH_DEBT-143
title: Public CHANGELOG stale for v5.12 to v5.15 cycle
severity: medium
surface_tags: [doc-discipline]
trigger: .F-or-sprint-umbrella-close
status: open
opened: 2026-05-28
related_specs: []
```

- **Created:** 2026-05-28 by v5.15.5.F.4d.1.D.1 (surfaced at Phase H ship-close; operator confirmed the public CHANGELOG had fallen out of workflow)
- **Severity:** MEDIUM (public AGPL repo quality / hedge-fund-visibility surface per `user_public_work_attracts_hedge_funds`; not blocking; accumulating)
- **Surface:** `DOCS/CHANGELOG.md` (elevator-pitch summary) + `DOCS/changelogs/<dated>.md` (detail files)
- **What's deferred:** Both surfaces lapsed mid-May 2026 — CHANGELOG.md summary jumps from a lone floating `5.15.5.F.4d.1.B.7` row to `5.11.58`; dated detail files stop at `2026-05-02-v5.9-ml-hardening.md`. The ENTIRE `v5.12 → v5.15.5.F.4d.1` cycle (current sprint) is uncovered except the anomalous `.B.7` row (no matching detail file). During the sprint the per-ship record lived in workspace postmortems + decision logs + per-ship GPG tags (private). Backfill at a sensible granularity — summary rows per EXTERNAL milestone, NOT per internal sub-ship (there are dozens) + detail files where warranted.
- **Why deferred (not effort-avoidance):** out of `.D.1` doc-sweep scope; substantial reconstruction; best done once the external version scheme is decided (the public CHANGELOG should track coarse external SemVer milestones, not high-velocity internal ship tags — which is partly WHY it fell behind).
- **Cost estimate:** ~3-5h (reconstruct milestone rows from postmortems + git history); LOW risk; align with the external-versioning decision.
- **Trigger:** `.F` professionalization sweep (public-facing polish pass) OR v5.15 sprint-umbrella close OR when TECH_DEBT-126 lands the external version scheme.
- **Status:** OPEN
- **Cross-ref:** **TECH_DEBT-126** (two-axis versioning — separate internal ship tag from external SemVer; CHANGELOG should track external milestones); `DOCS/changelogs/INDEX.md`; `feedback_motivated_collaborator_for_caramel` (public repo quality bar).

---

_(TECH_DEBT-139 moved to closed.md at v5.15.5.F.4d.1.D — Check 11 Python detection logic IMPLEMENTED as NEW `tools/check_forward_promise_audit.py`; M7 7th canonical structural enforcement application; see closed.md for full entry)_
