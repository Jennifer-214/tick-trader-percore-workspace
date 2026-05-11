# v5.14 — FoxML_Core math port + operational infra + maker MVP — MASTER

**Date drafted:** 2026-05-08 (post v5.13 sprint close)
**Branch:** `feat/v5.14-foxml-port-and-maker` (CREATE from `v5.13.6`)
**Predecessor:** v5.13.6 (sell-side ML + bandit + trainer UI all
shipped + audited)
**Rollback anchor:** `pre-v5.14` = `v5.13.6` umbrella tag
**Sister plans:**
- `2026-05-08-v5.14.0-ridge-blending.md` — Phase 1
- `2026-05-08-v5.14.1-composite-confidence.md` — Phase 1
- `2026-05-08-v5.14.2-hot-swap-ensemble.md` — Phase 1
- `2026-05-08-v5.14.3-three-layer-fingerprint.md` — Phase 2
- `2026-05-08-v5.14.4-multi-mode-reconciliation.md` — Phase 2
- `2026-05-08-v5.14.5-cs-target-plumbing.md` — Phase 2
- `2026-05-08-v5.14.6-bug-check-skill.md` — Phase 2 (already drafted
  separately at `2026-05-09-v5.14-bug-check-skill.md`; will integrate)
- `2026-05-08-v5.14.7-maker-order-mvp.md` — Phase 3

---

## Why this sprint exists

v5.12 + v5.13 shipped ENGINE infrastructure for sell-side ML +
bandit + slow-path opt + pre-live safety. v5.14 ships the
**math + operational layer** that makes it WORTH PAPER-TESTING:

1. **Math wins** (Ridge blending + composite confidence) that
   convert "we have models" → "we combine them intelligently"
2. **Operational safety** (multi-mode reconciliation + 3-layer
   fingerprint + hot-swap ensemble) that converts "engine runs"
   → "engine runs reliably under live conditions"
3. **CS plumbing** so multi-symbol future is easy
4. **Maker MVP** (off-by-default) so dedicated maker-mode paper-
   test sessions become possible without code change
5. **/bug-check skill** mechanizing RECURRING_BUG_PATTERNS

Operator decision 2026-05-08: ship ALL of this before paper-test;
"i wanna get this all setup before testing." Each phase ships
independently + is paper-testable in isolation.

---

## Architectural invariants (PRESERVE through sprint)

| Invariant | Verification |
|---|---|
| **Hot path UNTOUCHED** | All new math is slow-path-only or boot-only. `BG_Evaluate` / `SG_Evaluate` / `ExecutionCore_Tick` zero changes. Verified via tools/calls_graph_diff.sh + bench gate. |
| **FPN at boundaries** | Public API types (cfg fields, struct interfaces, snapshot fields) stay FPN<F>. Internal math kernels (Cholesky decomp in Ridge) MAY use double for numerical stability — boundary-stable refactor pattern (CLAUDE.local.md memory). |
| **Branchless on hot path** | Hot path adds zero branches. Slow-path branches use predicted-not-taken cfg flags (CLAUDE.md item 18). |
| **Data-oriented design** | Per-core arrays remain SoA for cache locality. New per-core fields slot into existing CoreContext (no new struct allocation in hot path). New ML state goes into EnsembleModelZoo (already cache-line-aware). |
| **Single source of truth** | New label kinds go through FOREACH_TARGET X-macro (auto-generates LABEL_*, table rows, dispatcher entries). New cfg fields use established CFG_PARSE_* macros. New stamp body fields use Surface G `has_*` flag pattern. |
| **LABEL_REGISTRY_HASH bumps when expected** | v5.14.5 (CS target append) bumps the hash → operator must retrain models. Documented as deliberate exception in master plan. v5.14.0/.1/.2/.3/.4/.6/.7 do NOT bump. |
| **FEATURE_REGISTRY_HASH bumps when expected** | v5.14.5 bumps the hash via .B (regime features: 3 new) + .C (frac diff: 3 new) = 6 new features → bundled with .A's LABEL_REGISTRY_HASH bump = ONE retrain cycle. Documented as deliberate exception. v5.14.0/.1/.2/.3/.4/.6/.7/.8/.9/.11/.12 do NOT bump. |
| **MODEL_FORMAT_VERSION stays at 6** | All stamp body extensions use Surface G `has_*` flag pattern. |
| **Default cfg = pre-v5.14 behavior** | Every new cfg field defaults to "off" or "no-op." First paper-test uses default cfg. |

---

## Sub-ship phasing

### Phase 1 — Math + safety (~6-8 days; load-bearing for paper-test alpha)

**v5.14.0 — Ridge risk-parity blending** [3-5 days]
- New `ML_Headers/RidgeBlender.hpp` with `Cholesky_Solve()` +
  `RidgeBlender_Compute()` kernels
- Replaces / complements bandit weight selection at
  `EnsembleModelZoo_dispatch` (StrategyParameters.hpp ML path)
- Per-horizon mode: blend models WITHIN a horizon
- Across-horizon mode: blend horizons via Ridge instead of bandit
  selection (operator opt-in via `cfg.ridge_across_horizons=1`;
  default 0 keeps bandit weight selection)
- FPN at boundaries (IC/cost/output weights); double internally
  for Cholesky numerical stability
- Cfg: `cfg.ridge_lambda` (default 0.15), `cfg.ridge_cost_penalty`
  (default 0.5), `cfg.ridge_min_ic_floor` (default 0.001),
  `cfg.ridge_within_horizon=1` (default on if Ridge available),
  `cfg.ridge_across_horizons=0` (default off)
- Sub-tags: .A struct + math kernel; .B engine wiring; .C tests +
  propagation (~14 new tests for Ridge math + integration)

**v5.14.1 — Composite confidence + winsorization + Spearman IC + portfolio turnover** [5-6 days; EXTENDED per operator 2026-05-08]
- Original scope: composite confidence (4-component) + winsorization
- Extensions:
  - **Spearman IC** (1-2d): rank-correlation IC alongside existing
    Pearson IC at `RollingIC`; `cfg.confidence_ic_variant` enum
    (0=Pearson default, 1=Spearman). Mirrored RollingICSpearman struct.
  - **Portfolio turnover tracking** (2d): rolling rank-set-difference
    metric on top of ConfidenceScorer; tracks how much the model's
    "top picks" change per N bars. High turnover → unstable model.
- Sub-tag plan extended with .E (Spearman IC) + .F (turnover)

**v5.14.1.A/B/C/D scope (original):**

**.A/.B/.C Composite confidence (2-3 days):**
- Extends `ConfidenceScorer` with Freshness / Capacity / Stability
  rolling buffers (currently has IC only via RollingIC)
- Composite = `IC × Freshness × Capacity × Stability` (clipped to
  [0, 1]; 0 = total degradation; 1 = perfect confidence)
- Feeds existing v5.12.1.D sizing-multiplier path that already
  shipped infrastructure-only
- Cfg: `cfg.confidence_freshness_tau_secs` (default 3600),
  `cfg.confidence_capacity_target_dollars` (default 0=unbounded),
  `cfg.confidence_stability_window` (default 10 samples),
  `cfg.confidence_composite_enabled` (default 0 = use IC alone;
  preserves pre-v5.14 behavior)

**.D Feature winsorization (1-2 days; NEW per operator 2026-05-08):**
- Robust feature scaling: clip per-feature values to [low, high]
  percentile bounds BEFORE standardization (mean-center + unit-var)
- Extends `FeatureStandardizer` sidecar binary format with two
  `float[]` arrays: `winsor_low[NUM_FEATURES]` + `winsor_high[NUM_FEATURES]`
- Python trainer fits the percentiles (e.g., 0.5% / 99.5%) at scaler-
  build time; writes to sidecar
- C++ engine reads sidecar at boot; applies clip in
  `FeatureStandardizer_Apply` BEFORE the existing mean/std transform
- Stamp body extension via Surface G: `has_winsor_bounds` flag (default
  0 = legacy sidecar without bounds = no-op identity clip; preserves
  pre-v5.14 behavior)
- LATENCY: per-feature `fmin(fmax(x, low), high)` is 2 branchless cmovs
  per feature per inference; ~5-15ns overhead total at slow-path
- Cfg: NONE — clipping bounds live on the sidecar (operator scales
  via training-time percentile choice, not runtime cfg)

**Sub-tags:**
- .A ConfidenceScorer struct extension (Freshness/Capacity/Stability)
- .B wiring (composite into v5.12.1.D sizing path)
- .C tests for composite confidence
- .D FeatureStandardizer winsor_low/high + sidecar format extension
  + Python trainer side + tests

**v5.14.2 — Hot-swap exit_predictor coverage** [2 days]
- Closes v5.13.6.B finding: hot-swap currently REFUSES when
  ensemble inference is active
- Extend `EngineSharded` hot-swap path to call
  `EnsembleModelZoo_LoadFromCfg` (which already handles
  exit_predictor) on swap request when ensemble is active
- Reuse existing v5.10.0c `acknowledge_hot_swap_with_open_positions`
  cfg flag (no new flag needed)
- Atomic free + reload of EnsembleModelZoo + bandit state
  (bandit_state.json + exit_bandit_state.json reload via existing
  helpers)
- Sub-tags: .A audit + design; .B implementation; .C tests

### Phase 2 — Operational infra (~6-8 days; live-mode safety)

**v5.14.3 — 3-layer registry fingerprinting** [3-4 days]
- Extend FEATURE_REGISTRY_HASH (current single-layer SHA256) into
  three-layer model:
  - Layer 1: base registry hash (current = FEATURE_REGISTRY_HASH)
  - Layer 2: overlay patches hash (per-target overrides; new)
  - Layer 3: effective merged hash (composite of 1 + 2)
- Add to stamp body via Surface G: `has_registry_overlay_hash`,
  `has_effective_registry_hash`
- Boot-time WARN/REFUSE on layer-2 mismatch (overlay drift)
- Sub-tags: .A overlay-patch infra in Python trainer (sidecar);
  .B C++ stamp body extension; .C verify_model_stamp + tests

**v5.14.4 — Multi-mode reconciliation** [2-3 days]
- Extend `Reconcile.hpp` enum (currently binary dry_run) to
  3 modes:
  - STRICT: fail boot on mismatch
  - WARN: log + continue
  - AUTO_SYNC: replay missed fills + restore positions
- Cfg: `cfg.reconcile_mode` (enum: 0=STRICT, 1=WARN, 2=AUTO_SYNC;
  default 1=WARN preserves current behavior)
- New helper `Reconcile_ReplayMissedFills()` reads Binance
  myTrades and applies via existing OMS HandleFill path
- Sub-tags: .A enum + cfg + STRICT/WARN refactor; .B AUTO_SYNC
  replay logic; .C tests

**v5.14.5 — CS targets + regime-conditional features + fractional differentiation (X-macro appends; bundled retrain)** [5-7 days; EXTENDED per operator 2026-05-08]
- **Bundling rationale**: CS targets bump LABEL_REGISTRY_HASH;
  regime-conditional features + fractional differentiation bump
  FEATURE_REGISTRY_HASH. Bundling all three = ONE retrain cycle for
  v5.14, not three.
- Original scope: CS percentile/z-score/vol-scaled targets (3 X-macro
  appends to FOREACH_TARGET)
- Extensions:
  - **Regime-conditional features** (2-3d): trend strength via
    `corr(close, time_index)`, volatility regime z-score, 3-regime
    classification (Choppy/Trending/HighVol). Adds N rows to
    FOREACH_FEATURE.
  - **Fractional differentiation** (2d): Δ^d x_t = Σ(-1)^k · C(d, k) · x_{t-k}
    (Lopez de Prado 2018). Reduces autocorrelation while preserving
    long-range memory; better feature engineering for mean-reversion.
    Precomputed binomial coefficients × sliding-window dot product
    over `ctx->short_rolling->price_buf[]` (raw ring already exists
    on RollingStats; zero new infrastructure). Adds 3 rows to
    FOREACH_FEATURE for d ∈ {0.4, 0.5, 0.6}.
    **Design discovery 2026-05-08:** initial trace-deps audit deferred
    this with rationale "no raw history accessible"; operator caught
    the gap (we have raw tick data; `RollingStats::price_buf[W=128]`
    IS the ring). Documented as Class 17 (architectural deferral
    without grepping adjacent struct fields) in RECURRING_BUG_PATTERNS.
- Sub-tag plan extended with .B (regime features) + .C (frac diff)

**v5.14.5.A scope (original CS targets):**
- Append to `Backtest/LabelFunctions.hpp` FOREACH_TARGET registry:
  - `LABEL_CS_PERCENTILE_RANK` (per-timestamp rank / N+1)
  - `LABEL_CS_ZSCORE_ROBUST` (median + MAD-based)
  - `LABEL_CS_VOLSCALED_DEMEANED` (vol-scaled + CS-mean-subtract)
- For single-symbol case: degenerates to identity (rank=0.5,
  z-score=0, demeaned=raw); meaningful for future multi-symbol
- Bumps LABEL_REGISTRY_HASH (deliberate; documented exception)
- Operator must retrain models that use new labels; existing
  models continue to work (label_kind on stamp body is per-handle)
- Sub-tags: .A registry append; .B Compute fns + tests

**v5.14.6 — `/bug-check` skill** [4-6 hours]
- See separate plan `2026-05-09-v5.14-bug-check-skill.md`
- Reads RECURRING_BUG_PATTERNS.md + runs detection greps + reports
  matches
- Sub-tag: single ship; no sub-tags

**v5.14.9 — Soft risk degradation ladder + adjacent debt closes** [9-11 days; EXPANDED 2026-05-10 per operator pre-coding consult]

Original scope (3-4d) was the soft ladder alone; expanded to mega-bundle
covering all adjacent confidence-cfg debt + cross-surface BITMAP_*
universalization, mirroring v5.14.8's TECH_DEBT-006 closure shape.

**Charter ship work:**
- Activates v5.12.1.D's confidence-conditional sizing path (currently
  broken-for-composite-scale: `conf_now ∈ [0.001, 0.3]` compared against
  `ml_buy_threshold ∈ [0.5, 0.7]` → factor=0 silently)
- Direct dep on v5.14.1's composite confidence (already shipped)
- Replaces broken math with `FOREACH_DEGRADATION_CURVE(X)` registry +
  X-macro-generated function-pointer dispatch table + 4 branchless
  curve compute fns (OFF / LINEAR / EXP / STEP)
- Per-core override pattern (`core_N_*` 4 cfg fields)
- Composite-required-for-ladder boot REFUSE (engine-wide validation)
- PerCoreSnap.ml_confidence_factor field for observability
- SHALT_LOW_CONFIDENCE emission at factor=0 (preserves attribution)
- Cfg field rename: `risk_scale_by_confidence` → `risk_degradation_curve`
  (back-compat parser shim; structural-fix-preferred per CLAUDE.md item 19)
- Cfg fields stamp-bound via FOREACH_STAMP_BOUND_CFG (drift detection
  through STAMP_CFG_AUTOPOPULATE)

**Adjacent debt closes folded in:**
- TECH_DEBT-004 hard close (Path A): delete legacy `confidence_freshness_tau`
  cfg field — mathematically inert in production (`data_age=0` always);
  half-dead via stamp-bound drift check on a value that doesn't affect
  inference. Eliminates parallel maintenance surface.
- TECH_DEBT-013 universalization sweep (all 5 remaining candidates):
  * (3) PerCoreSnap state_flags uint16_t (3-5 existing bools + new
        MASK_LADDER_BOTTOM_HIT migrate to bitmap)
  * (4) FOREACH_FEATURE enabled-flag bitmap (40 features → uint64_t
        enabled_bitmap + IS_FEATURE_ENABLED macro), bundled with
        TECH_DEBT-015 (FOREACH_FEATURE 7-col extension for
        max_staleness_minutes + Features_PackAll wiring)
  * (5) OrderManager + ExecutionCore engine-wide cfg_flags uint16_t
  * (6) ControllerEventLoop.partner_pending_active per-core bitmap
  * (7) ShardedSnapshot.any_scaler_present + any_scaler_failed →
        snapshot summary bitmap (with back-compat parser for legacy
        snapshots)
- TECH_DEBT-015 close: bundled with TECH_DEBT-013 candidate (4)
- TECH_DEBT-016 opens: calibration-table-driven sizing curve (defer to
  v5.X+ post-paper-test)

**Sub-tags:**
- .A FOREACH_DEGRADATION_CURVE registry + branchless compute fns +
  function-pointer dispatch table + cfg fields + parser + tests
- .B wire into StrategyParameters.hpp + slow-path predicate cache
  (`ladder_active`) + composite-required REFUSE + PerCoreSnap factor
  field + ML Status panel update + SHALT emission
- .B.1 per-core override (4 core_N_* fields + per-core resolution)
- .B.2 TECH_DEBT-013 (3): PerCoreSnap state_flags uint16_t migration
- .C stamp-bind 4 cfg fields via FOREACH_STAMP_BOUND_CFG
- .D TECH_DEBT-004 hard close (delete legacy field + 5 caller updates)
- .E TECH_DEBT-013 (4) + TECH_DEBT-015 bundled: FOREACH_FEATURE
  enabled_bitmap + 7-col extension + Features_PackAll wiring
- .F TECH_DEBT-013 (5): OMS + ExecutionCore cfg_flags
- .G TECH_DEBT-013 (6): ControllerEventLoop per-core bitmap
- .H TECH_DEBT-013 (7): ShardedSnapshot summary bitmap
- .I docs ship: DESIGN_SPECS/curve-registry-pattern.md + CHANGELOG
  + close TECH_DEBT-004 / -013 / -015 + open -016 + workspace sync

**Predecessor:** v5.14.8 close (commit 165a988); /dod-audit micro-ship
(skill spec lands before .A coding starts so v5.14.9's pre-coding gate
uses it).

**Numbering note (set 2026-05-10):** Phase 4 Thompson + online-corr
ships renumber from .11/.12 → .10/.11 since v5.14.9 absorbs adjacent
debt closures (no separate cleanup ship needed). Original .10 slot
(regime features, bundled into v5.14.5 for one-retrain-cycle efficiency)
is preserved as a sealed historical absorption; the .10 slot is reused
for Thompson going forward. Plan files renamed correspondingly:
`plans/2026-05-08-v5.14.11-bayesian-thompson-bandit.md` →
`plans/2026-05-08-v5.14.10-bayesian-thompson-bandit.md`;
`plans/2026-05-08-v5.14.12-online-corr-update.md` →
`plans/2026-05-08-v5.14.11-online-corr-update.md`.

**v5.14.8 — Stamp body lineage + stale gating** [4-5 days; NEW from Pass 3 audit]
- Five Pass 3 training-side findings consolidated into one ship:
  - Stale-model age check (cfg `model_max_age_hours`; loader WARN/REFUSE)
  - Stale-feature gating per-feature (`max_staleness_minutes` per
    FeatureRegistry row; Features_PackAll skip-if-stale)
  - Scaler fit-on-data fingerprint (Surface G `has_scaler_fit_data_hash`)
  - Feature `removal_reasons` lineage (stamp body CSV column)
  - Environment metadata in stamp (TF/PyTorch versions, CUDA info;
    Surface G `has_environment_meta`)
- Boot-time WARN/REFUSE on stale model + feature drift detection
- Sub-tags: .A stale-model + stale-feature; .B scaler fingerprint
  + removal_reasons; .C environment metadata + tests

### Phase 3 — Maker MVP — **DEFERRED INDEFINITELY 2026-05-10**

**v5.14.7 — Maker order MVP (POST_ONLY + cancel-and-replace)** — **DEFERRED INDEFINITELY** (no consistent order book data source)

**Deferral updated 2026-05-10:** Caramel: "we should permenantly defer this, im not sure when ill ever get a consistent source for orderbook data." TECH_DEBT-008 status flipped from OPEN → **DEFERRED-INDEFINITE**.

Initial deferral 2026-05-09 was framed as "until depth data is captured" with v6.0 master plan as the reactivation path. Updated framing 2026-05-10: no near-term plan to capture depth data (free archives don't expose full depth history; commercial feeds cost $$ with no budget allocation; self-bootstrap via DepthRecorder feasible but no firm start date). Maker work parks indefinitely.

**Trigger to reopen (status flips DEFERRED-INDEFINITE → OPEN):**
- Caramel runs `DepthRecorder` long enough to bootstrap a usable depth corpus (months of capture for one symbol), OR
- External depth-tape feed becomes accessible (Tardis subscription, Kaiko sample, etc.), OR
- Architectural decision to ship live-only maker path without backtest validation (currently policy is "backtest validation required before live").

**Phase 4 succession:** v5.14.8+ no longer block on Phase 3; predecessors re-anchored to v5.14.6 close 2026-05-09. v5.14 sprint umbrella does not block on TECH_DEBT-008.

### Phase 4 — Optimization + bandit alternatives (~7-9 days; NEW per operator 2026-05-08; renumbered 2026-05-10)

**v5.14.10 — Bayesian Thompson sampling bandit + PerCoreSnap layout
restructure + log-column registry generalization (mega-bundle)** [10-12
days; EXPANDED 2026-05-10 per pre-coding audit gate + Caramel consult]

Original scope (5-6d) was Thompson sampling alone; expanded to mega-bundle
covering: (1) curve-registry-pattern retrofit FOREACH_BANDIT_ALGORITHM,
(2) PerCoreSnap layout audit + unified bandit telemetry cluster, (3)
generalize log column registry across calib + metrics + trade logs.

**Charter ship work:**
- Adds Thompson sampling as ALTERNATIVE bandit weight provider via
  uniform 4-arg dispatch contract
- `cfg.bandit_algorithm` enum: 0=Exp3 (default), 1=Thompson, 2=Both
  (cfg=2 is valid parallel-training because per-arm rewards are
  observable independent of arm selection — see CoreModelZoo.hpp:881-882)
- ThompsonBanditState struct (parallel to BanditState; per-arm Gaussian
  conjugate posterior + own Box-Muller via raw mt19937_64::operator())
- FOREACH_BANDIT_ALGORITHM registry per curve-registry-pattern.md (3
  algos today; future UCB1/EXP4/Bayesian linear = 1 row each)
- thompson_state.json persistence with full wire-format byte-preservation
  (locale pin + format_version + %.17g + hex rng_state)
- 4 cfg fields stamp-bound via FOREACH_STAMP_BOUND_CFG (Surface G)
- 2 slow-path-gate predicates (THOMPSON_ACTIVE + BANDIT_BOTH_ACTIVE)
- FULL Bayesian dashboard: 5 PerCoreSnap fields (bit-packed state byte
  + float arrays + uint32 pulls)
- FOREACH_CALIB_LOG_COL registry for per-fill cfg=2 telemetry

**Adjacent debt closes folded in:**
- TECH_DEBT-010 close: FOREACH_CALIB_LOG_COL registry shipped via .D;
  4-col tuple template
- TECH_DEBT-011 substantial close: PerCoreSnap layout audit (.0) +
  unified bandit telemetry cluster + per-snapshot-cluster-layout-pattern.md
  DESIGN_SPECS doc (NEW)
- TECH_DEBT-027 resolved opportunistically: locale pinning gap in
  Bandit_SaveJSON fixed during .C
- N2 finding from /merge-scan absorbed: generalize FOREACH_LOG_COL
  pattern to MetricsLog + ShardedTradeLog (.F; closes recurring
  sister-literal pattern across 3 logs)

**Sub-tags (7-sub-tag structure):**
- .0 PerCoreSnap layout audit + unified bandit telemetry cluster
  + per-snapshot-cluster-layout-pattern.md DESIGN_SPECS doc
- .A FOREACH_BANDIT_ALGORITHM registry + ThompsonBanditState struct
  + Thompson math kernel + own Box-Muller + SHA-256 sample-trace test
- .B Engine wiring + 5 cfg fields + slow-path-gate predicates +
  4 stamp-binds via STAMP_CFG_AUTOPOPULATE
- .C Persistence (thompson_state.json) + tt::json_io extraction +
  FOREACH_ENSEMBLE_POST_LOAD extension (Class 18 mirror prevention)
- .D FULL Bayesian dashboard + FOREACH_CALIB_LOG_COL registry +
  cfg=2 calib telemetry + calibration-log-column-registry.md DESIGN_SPECS doc
- .E Tests (~+19) + propagation (CHANGELOG + cfg.example +
  HOT_PATH_CHANGELOG) + Version.hpp bumps per sub-tag
- .F Generalize log column registry to MetricsLog + ShardedTradeLog
  (FOREACH_METRICS_LOG_COL + FOREACH_TRADE_LOG_COL) + snapshot
  byte-preservation tests

**Predecessor:** v5.14.9 umbrella (b09b2d5) + docs commit 490618b
**Pre-coding audits (5):** synthesis at
`plans/plan_checks/2026-05-10-v5.14.10-fresh-audits-synthesis.md` +
amendment re-audits at `*-AMENDED.md` siblings
**LOC est:** ~1450-1750 across 7 sub-tags
**Closes:** 2 TECH_DEBT (-010 + -011 substantial); resolves -027
opportunistically; opens 0 new TECH_DEBT

**v5.14.11 — Online correlation matrix updates (Ridge optimization)** [2-3 days; renumbered from .12 2026-05-10]
- Replaces full O(N²K) BuildCorr recompute per cycle with incremental
  outer-product accumulator: `Σ_new = (Σ × (n-1) + outer_product(p_t, p_t)) / n`
- Saves ~1µs/cycle of Ridge (~30% reduction; current 3µs → ~2µs at N=8)
- Marginal vs slow-path budget (100µs); ships as cleanup once Ridge
  validated useful in paper-test
- Sub-tags: .A incremental kernel + tests; .B engine wiring (swap full
  recompute for incremental); .C propagation

---

## Ship order rationale

Phase 1 is load-bearing (math wins paper-test alpha + safety
infra prevents bricked engine). Phase 2 is post-paper-test value
(operational infra surfaces gaps you don't know you have). Phase 3
is opt-in upside (maker savings).

Recommended sequence: ship Phase 1 → run dedicated paper-test
session per the SAFETY → PERF → STRATEGY → LEARNING order from
v5.13 sprint close → ship Phase 2 → run another session → ship
Phase 3 → enable in dedicated maker-mode session.

OR ship all three phases in one go (operator preference 2026-05-08:
"get this all setup before testing"). The cfg-flag-default-off
pattern means everything stays inert until enabled.

---

## Sub-ship tag summary

```
v5.14.0     — Ridge risk-parity blending                  [SHIPPED 2026-05-09]
v5.14.1     — Composite confidence + winsor + IC variants
              + portfolio turnover + parity infra          [SHIPPED 2026-05-09]
v5.14.2     — Hot-swap ensemble coverage                   [SHIPPED 2026-05-09]
v5.14.3     — 3-layer registry fingerprinting              [SHIPPED 2026-05-09]
v5.14.4     — Multi-mode reconciliation (STRICT/WARN/SYNC) [SHIPPED 2026-05-09]
v5.14.5     — CS targets + regime features + frac diff     [SHIPPED 2026-05-09]
              (absorbed original v5.14.10 regime-features ship to bundle
               LABEL_REGISTRY_HASH + FEATURE_REGISTRY_HASH bump)
v5.14.6     — /bug-check skill                             [SHIPPED 2026-05-09]
v5.14.7     — Maker order MVP                              [DEFERRED-INDEFINITE 2026-05-10]
              See TECH_DEBT-008. No consistent order book data source.
v5.14.8     — Stamp body lineage + stale gating            [SHIPPED 2026-05-09]
              v5.14.8.0/.A.0.b/.A.merged/.A.6/.A.7/.B/.C/.D/.E/.F sub-tags
              + umbrella commit 165a988. Closed TECH_DEBT-006 fully (32 fields).

tools/dod-audit-v0.1
            — /dod-audit skill micro-ship                  [PENDING — pre-v5.14.9]
              Skill spec at .claude/skills/dod-audit/SKILL.md;
              /readiness Check 27 invokes it on plan files;
              SKILLS_HIERARCHY major/minor classification updated.
              Used by v5.14.9's pre-coding gate (first user).

v5.14.9     — Soft risk degradation ladder
              + adjacent debt closures                      [PENDING; 9-11 days]
              v5.14.9.A — FOREACH_DEGRADATION_CURVE registry +
                          branchless compute fns + dispatch table +
                          cfg fields + parser shim
              v5.14.9.B — wiring + slow-path predicate cache +
                          composite-required REFUSE +
                          PerCoreSnap.ml_confidence_factor +
                          SHALT_LOW_CONFIDENCE emission
              v5.14.9.B.1 — per-core override (4 core_N_* fields)
              v5.14.9.B.2 — TECH_DEBT-013 candidate (3): PerCoreSnap
                            state_flags uint16_t bitmap migration
              v5.14.9.C — stamp-bind 4 cfg fields via FOREACH_STAMP_BOUND_CFG
              v5.14.9.D — TECH_DEBT-004 hard close: delete legacy
                          confidence_freshness_tau (5 caller updates)
              v5.14.9.E — TECH_DEBT-013 (4) + TECH_DEBT-015 bundled:
                          FOREACH_FEATURE enabled_bitmap + 7-col extension
              v5.14.9.F — TECH_DEBT-013 (5): OMS + ExecutionCore cfg_flags
              v5.14.9.G — TECH_DEBT-013 (6): ControllerEventLoop per-core bitmap
              v5.14.9.H — TECH_DEBT-013 (7): ShardedSnapshot summary bitmap
              v5.14.9.I — DESIGN_SPECS/curve-registry-pattern.md +
                          CHANGELOG + close TECH_DEBT-004 / -013 / -015
                          + open TECH_DEBT-016 + workspace sync
              Closes 3 TECH_DEBT items + establishes BITMAP_* universally.

v5.14.10    — Bayesian Thompson sampling bandit + mega-bundle      [PENDING; 10-12 days]
              (renumbered from v5.14.11 2026-05-10; EXPANDED 2026-05-10
               via pre-coding audit gate + Caramel consult)
              v5.14.10.0 — PerCoreSnap layout audit + unified bandit
                           telemetry cluster + per-snapshot-cluster-layout-pattern.md
              v5.14.10.A — FOREACH_BANDIT_ALGORITHM registry + ThompsonBanditState
                           + own Box-Muller + SHA-256 sample-trace test
              v5.14.10.B — Wiring + 5 cfg fields + 2 slow-path-gate
                           predicates + 4 stamp-binds (STAMP_CFG_AUTOPOPULATE)
              v5.14.10.C — Persistence (thompson_state.json) + tt::json_io
                           + FOREACH_ENSEMBLE_POST_LOAD extension
              v5.14.10.D — FULL Bayesian dashboard + FOREACH_CALIB_LOG_COL
                           + calibration-log-column-registry.md
              v5.14.10.E — Tests (~+19) + propagation + Version.hpp bumps
              v5.14.10.F — Generalize FOREACH_LOG_COL to MetricsLog +
                           ShardedTradeLog (closes /merge-scan N2 finding)
              Closes 2 TECH_DEBT items + opens 0 new (-010 + -011 substantial;
              -027 resolved opportunistically).

v5.14.11    — Online correlation matrix updates            [PENDING; 2-3 days]
              (renumbered from v5.14.12 2026-05-10)
              v5.14.11.A — incremental outer-product kernel + tests
              v5.14.11.B — engine wiring (swap full recompute → incremental)
              v5.14.11.C — propagation

v5.14       — sprint umbrella (after all above ship)       [PENDING]
```

`git reset --hard <tag>` for surgical rollback at any granularity.

---

## Sprint kickoff checklist

Before opening v5.14.0:
- [ ] Branch `feat/v5.14-foxml-port-and-maker` created from `v5.13.6`
- [ ] Pre-tag rollback anchor `pre-v5.14` = `v5.13.6` umbrella
- [ ] /readiness GREEN on this master plan
- [ ] /parity-check GREEN at `v5.13.6` baseline
- [ ] /bug-check (NEW) shows no Class 1-13 instances at baseline
  (will be possible after v5.14.6 ships; until then, manual scan)
- [ ] Workspace synced + pushed
- [ ] FoxML_Core port-ideas + math-deep-audit reports re-read
- [ ] Confirm operator hardware time blocked for first paper-test
  session (Phase 1 alpha-relevant features want to be tested
  before Phase 2 ships to isolate variables)

---

## Verification gate (sprint close)

- All tests pass (~2062 + new ~50-80 = ~2120-2140)
- /parity-check GREEN at v5.14 (Section L for every new struct
  field; Section J for every new GUI surface)
- /merge-scan GREEN (no missed reuse of existing infra)
- /latency-track entries for every slow-path / drainer addition
- /bug-check CLEAN (no new Class 13 instances or other regressions)
- Hot path bench unchanged (calls_graph_diff)
- ASAN run on full suite ($ ./build.sh asan && ./build_asan/controller_test)
- Engine boot smoke (paper mode) shows new cfg fields parse cleanly

---

## What this sprint is NOT

- Not paper-testing (operator hardware time; separate)
- Not multi-symbol (CS plumbing v5.14.5 is just X-macro append;
  multi-symbol architecture is v5.16+ separate sprint)
- Not options trading (Binance/Deribit options is ~2-4 week
  separate sprint; deferred until spot paper-test validates)
- Not online learning beyond bandit (Bayesian Thompson sampling
  alternative deferred to v5.15)
- Not loss-function changes (training-time only; offline Python
  trainer modifications)
- Not engine rewrite — additive on top of existing v5.13.6 base

---

## Cross-references

- FoxML_Core port ideas (Pass 1):
  `plans/2026-05-08-foxml-core-port-ideas.md`
- FoxML_Core math deep audit (Pass 2):
  `plans/2026-05-08-foxml-core-math-deep-audit.md`
- /bug-check skill plan:
  `plans/2026-05-09-v5.14-bug-check-skill.md`
- v5.13 sprint close:
  `plans/2026-05-08-MASTER-v5.13-sell-side-ml.md`
- v5.13.6.B hot-swap finding context:
  v5.13.6.B/C/D commit message (240752e)
- DOCS/RECURRING_BUG_PATTERNS.md Class 13 (worker-arg use-after-
  free; v5.14.6 /bug-check will scan for this + other classes)

---

## Open questions for operator

1. **v5.14.5 LABEL_REGISTRY_HASH bump** — operator retrains all
   active models on flip. Acceptable cost for the multi-symbol-
   readiness benefit?
2. **v5.14.0 Ridge across-horizons mode** — default off. After
   paper-test, if Ridge-within-horizon shows good results, do we
   flip across-horizons default to on in v5.15?
3. **v5.14.7 maker MVP** — calibration log extension for "submitted
   vs filled vs cancelled" — is this a v5.14.7.D scope item or
   defer to v5.15+ post-process tooling?

These don't block sprint kickoff; queue for mid-sprint discussion.
