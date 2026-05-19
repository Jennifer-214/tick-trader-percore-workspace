# FUTURE_ML — Research direction + alpha hypotheses

**Private** (gitignored via `FUTURE_*.md` pattern; workspace-backed).

This file captures ML research directions that go beyond the current
engine's capabilities. Each entry has: alpha hypothesis (why this might
be interesting), engineering shape (what would need to change), and
deferral status.

The goal is to keep the "what's possible" surface queryable so we don't
have to re-derive the analysis when an idea resurfaces 3 months from
now. Items here are NOT a backlog — they're a research map. Decide
what to pick up based on paper-trading feedback, not this doc's order.

Cross-reference: `plans/2026-05-07-deferred-items.md` has the
formal deferred-items log with re-trigger conditions per item; this
doc is the higher-level vision.

---

## FPN<32> variant — appropriate for equities (NOT for crypto/BTC)

**Captured 2026-05-13 from v5.15.5.C.5 design discussion.**

A reduced-precision FPN<F=32> variant would have:
- 32 fractional bits → ~2.3e-10 of $1 precision
- ~half the bytes of FPN<F=64> (12B vs 24B)
- Enables Position cold-field bit-packing (entry_fee FPN<32>, original_tp/sl deltas FPN<32>): ~36B savings per Position → Position 128B = 2 cache lines exact
- ~1KB total memory savings per OMS

**Why NOT for crypto/BTC (rejected v5.15.5.C.5):**
- Cumulative rounding drift across thousands of trades. Per-fee FPN<32> precision is fine in isolation but accumulates: 1e-10 × 10K trades/year × multiple positions = drift could reach bps-level (1e-4). For a strategy targeting bps-level edge, that's noise approaching signal magnitude.
- Conversion boundaries (FPN<32> ↔ FPN<64>) break bytewise determinism. CLAUDE.md item 25 (AVX-512 byte-determinism) + item 15 (parity-tested-by-construction) require ULP-exact identity across SIMD/scalar/cross-binary paths. Conversion-induced rounding violates this contract.
- P&L math compounds the drift through gross/fees/net cascade. ML training signal (which uses pnl) gets subtly noisier.
- Total memory savings (~1KB/OMS) is marginal vs OMS state's total KB-MB footprint; not transformative.

**When FPN<32> WOULD be appropriate (equities pivot):**
- Equities prices are integer-cent-denominated (1¢ = 0.01 USD; ~2 decimal digits significant). FPN<32>'s 10-digit precision is FAR more than needed.
- Cumulative drift at 1e-10 over 10K trades = ~1e-6 dollars = 0.0001¢. Below transaction-cost noise. Safe.
- Equities position sizes are integer shares (no fractional shares for typical strategies). FPN<32> precision is overkill but safe.
- Fee structures simpler (flat per-trade or per-share commissions). Easier to model in lower precision.
- Cross-binary determinism still required but easier to maintain at lower precision (less ULP variance).

**Engineering investment (if pivoted to equities):**
- ~1-2 weeks for FPN<32> arithmetic operator overloads
- Conversion functions FPN<32> ↔ FPN<64>
- SHA-256 cross-binary lock tests for byte determinism per `avx512-byte-determinism-pattern.md`
- Migration of cold-field math (entry_fee, original_tp/sl deltas, etc.) to FPN<32> at precision boundaries
- Position 128B target achievable; ~1KB OMS savings real

**Status:** PARKED for crypto era. Re-evaluate IF/WHEN pivoting to equities trading. Trigger: equities-strategy plan emerges in roadmap.

**Cross-references when picked up:**
- `DESIGN_SPECS/wire-format-patterns/avx512-byte-determinism-pattern.md` (8 rules + SHA-256 cross-binary lock test pattern)
- `DESIGN_SPECS/data-disciplines/hot-side-array-element-alignment-for-sparse-access.md` (Position 128B alignas target)
- `DESIGN_SPECS/wire-format-patterns/struct-padding-determinism-pattern.md` (FPN<32> needs explicit padding declarations too)
- `DOCS/TECH_DEBT.md` entry: "FPN<32> variant infrastructure — DEFERRED until equities pivot"

---

## Native gradient boosting on FPN<F> — "FoxBoost" (deferred research project)

**Captured 2026-05-13 from Caramel's note: "getting XGBoost to run native with FPN operations would be a neat project."**

**Alpha hypothesis:** Cross-binary replay determinism extends from PREDICTION (already locked via feature_registry_hash + scaler_sha256 + AVX-512 byte-deterministic kernels) to TRAINING. Today's float64 gradient/hessian/loss computations vary by ULP across compiler/platform/optimization — a model trained on machine A is not bytewise-identical to a model trained on machine B even with the same data + seed. Native FPN<F> gradient boosting would close that gap.

Secondary wins:
- Byte-level train-serve parity (training-time math = serving-time math, not just same-result-to-N-decimals)
- Predictable performance characteristics (branchless FPN AVX-512 ops have known cycle counts; libm transcendentals don't)
- Eliminates the libgomp+pthread landmine (XGBoost C library) — own training thread model

**Infrastructure already shipped (v5.14 / v5.15):**
- FoxLIB branchless FPN math: `FPN_Exp`, `FPN_Log`, `FPN_Sqrt`, `FPN_Mul`, etc. (v5.10.0b.2.5.C)
- AVX-512 byte-deterministic vectorization pattern: `DESIGN_SPECS/wire-format-patterns/avx512-byte-determinism-pattern.md` + CLAUDE.md item 25 (8 rules + SHA-256 cross-binary lock test)
- Branchless math kernels with constant-iter reductions: `DESIGN_SPECS/refactor-patterns/branchless-math-kernel-pattern.md` + CLAUDE.md item 26 (canonical: Cholesky_Solve)
- Struct padding determinism: `DESIGN_SPECS/wire-format-patterns/struct-padding-determinism-pattern.md` + CLAUDE.md item 27 (FPN<F> already padded)
- Ridge blender + sliding-window correlation on FPN<F> + AVX-512 (v5.14.11.A/B)
- Online regression (Ridge) + bandits (Thompson, Exp3) on FPN<F>

**What's missing for native GBM:**
- Tree node layout in FPN<F> (split threshold + leaf weight; padded for byte-determinism)
- Histogram bin accumulator (gradient + hessian sums per bin, per feature, per node) — AVX-512 vectorized FPN<F> additions
- Loss functions: softmax / sigmoid / log-loss / cross-entropy in FPN<F> with sufficient gradient precision
- Split-finding gain comparison: trivially FPN<F> (subtraction + multiplication + comparison)
- Multi-class one-vs-rest accumulation (handled per-class as scalar)

**Engineering approach — 4 options:**

| Option | Scope | Time | Trade-off |
|---|---|---|---|
| A. Fork XGBoost | Massive | 4-8 wk | Replace `double`/`bst_float` throughout. Ongoing maintenance burden; hard to merge upstream changes. Not recommended unless proprietary fork desired. |
| B. Build FoxBoost (full GBM) | Medium | 2-4 wk MVP, 4-6 wk prod | Implement core GBM in FoxLIB. Reusable library; cleaner integration. Production-grade with SIMD + tests. |
| C. Hybrid (train float, serve FPN) | Small | 1 wk | Train via XGBoost as today; quantize trained ensemble to FPN<F> for serving. Training-time variance becomes baked-in noise floor; serve-time determinism preserved. |
| D. Native histogram-method GBM only | Small-Medium | 1-2 wk MVP, 2-3 wk prod | `tree_method=hist` only. Features already int-binned; only gradient accumulator + loss + leaf weights need FPN<F>. **Recommended starting point.** |

**Why Option D first:** XGBoost's histogram method is already integer-friendly (features pre-binned into int8/int16). The only float→FPN work is:
- Per-bin gradient + hessian accumulator: `FPN<F> g_sum[n_bins], h_sum[n_bins]` per node
- Split gain: `FPN<F>` arithmetic on the gradient/hessian sums
- Loss function: log-loss → FPN_Log + FPN_Exp (sigmoid via `1/(1+exp(-x))`)
- Leaf weight: `FPN<F> w = -g_sum / (h_sum + lambda)`
- Tree walk at prediction: int bin → split comparison → next node (already int-friendly)

SIMD opportunity: bin accumulation is the hot loop. AVX-512 FPN<F> kernel per the existing pattern (Rule 8: branchless within vectorized block). Cross-binary determinism enforced via SHA-256 lock on trained tree state.

**Test approach:**
- SHA-256 lock test: train on fixed feature CSV + seed → assert tree state matches reference SHA-256 across rebuild + cross-binary
- Property tests: per-class gradient propagation matches analytical derivative within FPN<F> precision
- Calibration on real data: compare FoxBoost vs XGBoost on representative train set; expect identical SPLIT decisions if features quantize identically (FPN<F> precision in gradient accumulators should not affect split-finding for typical gain magnitudes)

**Deferral status:** PARKED. Compelling but multi-week focused effort. Triggers to revisit:
- After v5.15 + v5.16 ship + paper-trade results inform whether training-time cross-binary determinism is operationally needed
- Regulatory / audit requirement for bytewise reproducibility of training
- Sandbox / research interest

**Cross-references for picker-up:**
- `DESIGN_SPECS/wire-format-patterns/avx512-byte-determinism-pattern.md` (8 rules + SHA-256 cross-binary lock test pattern)
- `DESIGN_SPECS/refactor-patterns/branchless-math-kernel-pattern.md` (constant-iter inner reductions; histogram bin accumulation shape)
- `DESIGN_SPECS/refactor-patterns/sliding-window-online-statistics-pattern.md` (for online training stats — gradient norms, residual variance)
- `DESIGN_SPECS/wire-format-patterns/struct-padding-determinism-pattern.md` (tree node + bin accumulator structs)
- CLAUDE.md items 25 (AVX-512 byte determinism), 26 (branchless math kernels), 27 (struct padding determinism)
- CLAUDE.local.md "Known landmine" 2026-05-07 (XGBoost+libgomp+pthread segfault — eliminated entirely by going native)

---

## Currently active (post-v5.11.62)

What the engine actually does today:

- **Multi-horizon ensemble** with Bandit-Exp3 weighted blend per
  regime. Each horizon trains on the same label_kind; bandit
  learns per-regime weights based on outcome attribution.
- **3-class barrier** (PEAK_VALLEY_STABLE) at each horizon, with
  class-1 (peak) probability as the buy signal.
- **Train-serve parity** locked via FEATURE_REGISTRY_HASH +
  LABEL_REGISTRY_HASH + scaler_sha256 + stamp body schema.
- **Role-agnostic strategy** (v5.11.62) — adding a new model role
  doesn't touch strategy code.
- **Drift watchdog** (v5.10.0e) — per-arm IC tracking with
  auto-demotion when sustained miscalibration.
- **Hot model swap** (v5.10.0c) — swap models without engine
  restart; safety-gated by open-position semantics.

What's structurally there but not exercised:

- Multi-role zoo (barrier + regime + exit_predictor + buy_signal).
  Currently only barrier or buy_signal is loaded; the other roles
  are slots waiting for trained models.
- Confidence scoring infrastructure exists; turning it on requires
  paper-trading data on calibration to set sane thresholds.

---

## 1. Composite-signal extraction (deferred caveat — alpha potential)

**Hypothesis:** A SINGLE model's output can encode richer signals
than just `out_result[buy_class_idx] > threshold`. Examples that may
contain alpha:

- **Class differences** as conviction. A 5-class model with classes
  `[strong_down, down, neutral, up, strong_up]`: signal =
  `P(strong_up) + 0.5×P(up) - 0.5×P(down) - P(strong_down)`. Maps
  directional probability mass to a continuous conviction score.
  Bandit blend works on the conviction directly.
- **Max-of-N fire**: `fire if max(P(up), P(strong_up)) > threshold`.
  Captures "the model is confident SOME up direction will win" even
  when split between classes.
- **Conditional class extraction**: in TRENDING regime, extract
  P(up). In VOLATILE regime, extract `P(stable)` as a "safety gate"
  — fire ONLY when stability prediction is HIGH (don't trade chaos).
  Same model, different extraction per regime.

**Why it's a caveat in v5.11.62:** Model_Predict currently returns
a single class probability. The above need composition.

**Engineering shape:** Per-handle `target_classes[8]` +
`class_weights[8]` arrays. Loader sets them based on stamp metadata
(label_kind + per-class semantics). `Model_Predict` returns the
weighted combination. Default = single-class behavior. Strategy
code unchanged. ~2-3 hours.

**Deferral rationale:** No current trained model uses this. Premature
abstraction without a concrete use case = wrong shape. When you
train a 5-class up/down model OR want regime-conditional class
extraction, ship the extension then.

**Tracked in:** `plans/2026-05-07-deferred-items.md` "v5.11.62 caveat"

---

## 2. Mixed-output ensembles (deferred — significant alpha potential)

**Hypothesis:** Different MODEL TYPES match different time-scales
and regimes. Mixing them in one ensemble lets the bandit learn
per-regime model-TYPE preferences:

- Long-horizon **regression** captures continuous trend strength.
  Best in TRENDING regimes.
- Short-horizon **binary classification** captures dip-buying
  reflexes. Best in RANGING regimes.
- 3-class **barrier** captures regime-conditional direction. Best
  in MILD_TREND or VOLATILE.

If the bandit learns `TRENDING → weight regression high; RANGING →
weight binary high`, you get orthogonal alpha to "same model type
at multiple horizons."

**Why it's broken today:** Bandit blend averages predictions across
ensemble members. Different output scales (regression `[-0.05, +0.05]`
vs probability `[0, 1]`) make averaging meaningless.

**Engineering shape:** Per-handle prediction normalizer that maps
any output to `[0, 1]` buy-probability space:
- Binary: passthrough
- Regression: `clamp(0.5 + pred / (2×tp_pct), 0, 1)`
- 3-class: extract via `buy_class_idx` (current)
Bandit blends normalized values. Two-ship sequence: trainer-side
per-horizon label_kind UI first (~1 day), live-side normalizer
second (~half-day).

**Cheap pre-experiment** (validate alpha hypothesis before
infrastructure):
1. Train 3 separate single-horizon models — regression at h=50000,
   binary at h=1000, 3-class at h=7500.
2. Run 3 paper traders.
3. Measure regime-conditional P&L per model.
4. If clear regime-conditional preferences exist → alpha real,
   build infrastructure.
5. If similar performance per regime → no orthogonal alpha; defer
   permanently.

**Tracked in:** `plans/2026-05-07-deferred-items.md` "Mixed-output
ensembles"

---

## 3. Online learning (continuous gradient updates)

**Hypothesis:** Markets drift. A model trained on Q1 data degrades
gracefully on Q2 if features are robust, BUT online updates that
weight recent outcomes higher could capture regime shifts faster
than periodic retraining.

**What we already have:** Bandit-Exp3 IS a form of online learning —
it learns ensemble member WEIGHTS based on outcomes. The deeper
hypothesis: ALSO online-update the underlying booster.

**Engineering shape:** Online gradient updates per fill outcome.
Each closed trade contributes a (features, outcome) pair to a
small ring buffer. Periodic (every N trades or N hours) lightweight
booster update via XGBoost's `XGBoosterUpdateOneIter` on the recent
buffer. Catches: stamp body needs to record "online_updates_since_train"
counter; train-serve parity becomes "scaler is fixed at train time;
booster drifts but bounded by N online updates."

**Risk:** Online updates can make the model worse if early outcomes
are unrepresentative. Need:
- Confidence interval on the online-updated model vs frozen baseline
- Auto-revert if online model underperforms baseline by margin

**Deferral rationale:** Bandit weights already provide regime-aware
adaptation; full booster online updates are riskier and add a lot
of complexity. Worth experimenting in backtest first. Probably v5.13+.

---

## 4. Multi-objective models (direction + volatility + timing)

**Hypothesis:** A single model output (direction probability) is
the simplest signal but throws away information. A multi-output
model could predict:
- Direction (up/down/stable)
- Expected volatility (predicted stddev over horizon)
- Optimal entry timing (now / wait N ticks)
- Holding period (likely time to TP)

The strategy uses ALL four to size + time entries:
- High direction conviction × low volatility = aggressive size
- High direction × high volatility = defensive size
- Direction signal but timing says "wait 50 ticks" → delay entry

**Engineering shape:** XGBoost supports multi-output regression via
`multi_strategy=multi_output_tree` (recent versions). Stamp body
gains per-output semantic labels. Strategy reads each output via
named getter. Composite-signal extraction (item 1) covers the
extraction layer.

**Deferral rationale:** Big engineering ask + needs labeled training
data for each output. Direction labels are easy (we have them);
volatility labels need post-hoc realized-vol measurement; timing
labels need finer-grained walk-forward. Probably 2-3 weeks of
training-side work.

---

## 5. Calibration-aware sizing (deferred guardrail item)

**Hypothesis:** If the model is well-calibrated (predicted P=0.7
actually wins 70% of the time), high-confidence predictions deserve
higher position sizing. Current flat 5% per-position throws away
this information.

**Engineering shape:** Already documented in
`plans/2026-05-07-deferred-items.md` "Live-side ML guardrails #3"
as a half-day cfg + portfolio change.

**Why it's gated on data:** Need paper-trading calibration data to
verify the model is actually calibrated before turning size-scaling
on. Mis-calibrated model + size scaling = amplified losses.

---

## 6. Feature importance per regime (interpretability + alpha)

**Hypothesis:** Different features matter in different regimes.
Knowing which features the model relies on per regime gives:
- **Interpretability**: operator can validate the model's reasoning
- **Alpha**: feature importance shifts could be a signal in
  themselves (regime-prediction proxy)

**Engineering shape:** XGBoost's `XGBoosterGetAttr` + per-tree gain
extraction. Per-regime predict samples accumulate feature
attribution. Slow-path computes "top-3 features by gain in current
regime"; surfaces in ML Status panel. Could feed back into the
model: if feature X is consistently most-important in TRENDING, the
features-pack reorders X to be more cache-friendly during trending
regimes (perf, not alpha).

**Deferral rationale:** Mostly an observability win, not an alpha
win. Interesting if you ever do regime-specific feature engineering.

---

## 7. Adversarial / market-microstructure features

**Hypothesis:** Some market participants are informed (HFTs, MMs,
informed flow); others are noise. Detecting INFORMED flow lets us
either piggyback (follow informed direction) or avoid (don't trade
into the path of an iceberg refill).

**Examples:**
- **Iceberg detection:** repeated symmetric replenishment at a
  specific price level. Strong signal of hidden size.
- **Spoofing detection:** orders placed > 5 levels deep that get
  cancelled within 100ms × N occurrences. Suppress entries during
  detected spoof activity.
- **Toxic flow indicator:** track our own taker P&L over short
  windows. If our crosses consistently lose money in next N seconds,
  the venue is "toxic" — widen spread thresholds.

**Tracked in:** `plans/2026-05-07-deferred-items.md`
"Orderbook-depth microstructure features" (full set + estimates +
re-trigger conditions)

**Why deferred:** ~4-5 weeks total for the full set; only worth it
post-colo deployment OR if paper trading reveals systematic adverse
selection.

---

## 8. Attention over features (regime-conditional gating)

**Hypothesis:** Not all features matter all the time. A
"feature attention" mechanism — soft mask that weights features
based on current regime — could improve signal-to-noise per
regime.

**Engineering shape:** Per-regime feature mask (similar to v5.11.18's
feature_mask but regime-conditional). At predict time, multiply
feature vector element-wise by current regime's mask before
Model_Predict. Train each regime's mask via gradient on regime-
filtered labels.

**Deferral rationale:** Adds significant training-side complexity
(per-regime mask optimization). Probably gated on item 6 (feature
importance per regime) succeeding first — once we know which
features matter per regime, the mask is the next step.

---

## 9. Transfer learning across symbols

**Hypothesis:** A model trained on BTCUSDT generalizes partially to
ETHUSDT (similar microstructure). Bootstrap a new symbol's model
from the BTC model's weights, then fine-tune on ETH-specific data.
Reduces training data requirement for new symbols.

**Engineering shape:** XGBoost supports `process_type=update` for
incremental tree updates. Train a "base model" on BTC, then `update`
trees on ETH features. Stamp body records `transfer_source` for
provenance.

**Why it's premature:** Single-symbol deployment today. Worth
revisiting when multi-symbol expands.

---

## 10. RL-style execution timing

**Hypothesis:** When the model says "fire," the EXACT entry timing
within the next N ticks matters. RL agent learns to wait for the
optimal microstructure window (e.g. wait until book imbalance
favors entry direction).

**Engineering shape:** Sub-strategy on top of the directional
model. Once buy_signal fires, RL agent (Q-learning or policy
gradient) decides: enter now / wait 1 tick / wait 5 ticks / cancel.
Reward = realized fill price vs prediction-time price.

**Deferral rationale:** Significant new infrastructure (RL agent,
reward attribution at sub-tick granularity, per-fill state machine).
Worth it post-colo where 1ms savings matter; not before.

---

## 11. Drift detection beyond IC

**Hypothesis:** Information Coefficient (current drift watchdog)
measures correlation between predictions and outcomes. Other drift
signals worth tracking:
- **Distribution shift**: feature distribution today vs training-time
  distribution (KL divergence, KS test)
- **Calibration drift**: predicted-P=0.7 actually wins less often
  than 70% (Brier score)
- **Coverage gap**: features hitting NaN/Inf rate increasing over
  time (already tracked, but rate analysis)

**Engineering shape:** Slow-path samples feature distribution
moments. Comparison to stamp body's recorded training-time moments
fires WARN when divergence exceeds threshold. Surfaces in ML Status
panel.

**Deferral rationale:** v5.10.0e drift watchdog catches the most
common case (predictions lose correlation with outcomes). Other
drift modes are second-order; address if v5.10.0e proves
insufficient.

---

## Cross-cutting considerations

**The strategy code never changes.** This is the v5.11.62 invariant.
ALL the above items extend at the loader / Model_Predict / training
layer, NOT in MLStrategy.hpp. If a research direction would require
strategy code changes, that's a sign the design is wrong — push the
composition back into Model_Predict + per-handle metadata.

**Train-serve parity must hold.** Every new training-side capability
(multi-output models, online updates, per-regime masks) must extend
the stamp body via Surface G pattern (`has_*=0` flag for legacy
compat). LABEL_REGISTRY_HASH bumps automatically force retraining
when label semantics change.

**Paper-trading data drives priorities.** Ranking these items today
without paper-test data is guessing. Run the engine for 2-4 weeks
on paper, look at:
- Bandit weight convergence per regime — if uniform stays forever,
  bandit isn't learning → focus on online learning (item 3) or
  feature importance (item 6)
- Adverse selection (taker fills lose money) → microstructure
  features (item 7)
- Calibration plot (predicted vs realized) → calibration-aware
  sizing (item 5) IF calibrated; multi-objective (item 4) if not

The right next step is data-driven, not vision-driven.

---

## Maintenance

When picking up an item from this doc:
- Move the active work to a dated plan in `plans/<date>-<theme>.md`
- Mark the FUTURE_ML.md entry with `**ACTIVE: see <plan>**` at the top
- Add to deferred-items.md the gating decisions made (e.g. "after
  paper-test showed regime-conditional preferences, item 2 is now
  active in plan X")
- Once shipped, mark `**SHIPPED in vX.Y.Z**` and link to the
  changelog row

When deciding to permanently kill an item (vision didn't pan out):
- Move to a `KILLED` section at the bottom with the reason. Don't
  delete — the analysis is reusable next time a similar idea comes
  up.
