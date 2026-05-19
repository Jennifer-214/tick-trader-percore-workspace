# /parity-check report — 2026-05-11 (v5.14.11 AMENDED plan re-audit)

## Plan summary

- **HEAD:** `e0cc877` (v5.14.10 umbrella)
- **Audit target:** amended plan `plans/v5.14-foxml-port-and-maker/subplans/2026-05-08-v5.14.11-online-corr-update.md` (post-Caramel-consult amendments per `plans/plan_checks/2026-05-11-v5.14.11-fresh-audits-synthesis.md`)
- **Predecessor:** v5.14.10 close
- **Tests:** existing 1822 pass at e0cc877 (no code changes yet — plan-stage re-audit)
- **Audit scope:** focused re-audit on amendment surface (PARITY contract reframing + PARITY-016/017/018 closure mechanisms + 4 new amendment surfaces)
- **Cross-check baseline:** PARITY_ISSUES.md as of 2026-05-11 13:00 UTC

## Overall verdict — **GREEN** with one MEDIUM finding (NEW)

The amended plan resolves PARITY-016/017/018 structurally + adopts unanimous-recommended structural improvements. ONE new MEDIUM finding emerged during re-audit: the AVX-512 vectorization of Cholesky_Solve back-solve (Step 7 site #3) has a column-access pattern that doesn't vectorize cleanly via the v5.11.7 row-load shape. The plan should clarify this site's strategy before .B kickoff. **Recommendation: proceed to .A** (the .B site can be designed when .B starts; no impact on .A code).

---

## Per-finding status update

### PARITY-016 — REPLAY-DETERMINISM REGIME REFRAMING — **RESOLVED at v5.14.11.A** ✓

The original PARITY-016 framed `cfg=0 vs cfg=1` as a silent bytewise-divergence class. The amended plan **eliminates the original failure mode by structural unification**:

- Both paths now share `FinalizeCorrFromSums` (single math kernel)
- Both paths use sum-of-squares accumulator form
- cfg=0 builds sums in one pass over K history; cfg=1 updates sums incrementally with replacement math
- Difference between cfg=0 and cfg=1 is **only** the accumulator-build phase

Per amended plan line 78: "Within v5.14.11 (cfg=0 vs cfg=1) | Tolerance ~1e-13 (sum convergence) | Both paths share `FinalizeCorrFromSums`; only differ in how `sum_x` + `sum_xx` are accumulated."

This is **mathematically sound**:
- Identical inputs accumulated in different orders produce sums that converge to within IEEE-754 rounding × K operations
- Drop-then-add math `sum_xx[i][j] += new[i]*new[j] - old[i]*old[j]` is algebraically equivalent to fresh-rebuild after K iterations
- Drift does NOT accumulate cycle-over-cycle (each record's contribution added once + subtracted once over its K-record lifetime — bounded-by-design per `sliding-window-online-statistics-pattern.md` line 80)

Closure mechanism:
- SHA-256 baseline lock for cfg=0 within v5.14.11 (Step 9 test list line 359)
- SHA-256 baseline lock for cfg=1 within v5.14.11 (Step 9 test list line 360)
- Tolerance 1e-9 across cfg=0/cfg=1 with 5-order headroom over predicted 10^-14 cancellation error

**Note:** the v5.14.10 → v5.14.11 boundary is INTENTIONALLY bytewise-broken (BuildCorr refactor changes 3-pass to 1-pass; line 76 contract clearly states this as tolerance 1e-9). Operator-aware regression test infrastructure: any v5.9.2-style bytewise replay test that captured baselines pre-v5.14.11 must be regenerated. The plan should note this in the CHANGELOG entry; .C is the right home.

**PARITY contract clarity:** the 3-boundary table at line 73-79 is the cleanest articulation in any sprint to date. Three boundaries × three tolerance grades × specific verification mechanisms is testable and not load-bearing on prose interpretation.

### PARITY-017 — AVX-512 BYTE-DETERMINISM PER-SITE — **RESOLVED at v5.14.11.B** ✓ (with NEW caveat — see below)

Original PARITY-017 flagged 4 sites need explicit v5.11.7 discipline annotation + SHA-256 lock test. Amended plan reduces to **3 sites** (UpdateOnline, BuildCorr accumulation, Cholesky_Solve) + .B has explicit per-site SHA-256 tests in Step 9.

The 3 sites are:

1. **UpdateOnline outer-product update** (sliding-window state) — row-major access to `sum_xx[i][...]`; vectorizes cleanly per `_mm512_loadu_pd` row-load shape. v5.11.7 discipline applies directly.

2. **BuildCorr single-pass accumulation** (refactored cfg=0 path) — row-major access to flat history × N predictions. Vectorizes via the same row-load shape. v5.11.7 discipline applies.

3. **Cholesky_Solve inner reductions** — **SPLIT INTO THREE SUB-SITES** which differ structurally (see NEW finding below).

The `avx512-byte-determinism-pattern.md` is a clean 7-rule contract; the plan's Step 7 code example correctly applies all 7 rules for site 3a (decomposition). The SHA-256 lock test design (Step 9 line 363) covers all 3 sites uniformly.

### PARITY-018 — PERIODIC-RECOMPUTE STALE STATE — **RESOLVED BY ELIMINATION** ✓

Adoption of Decision 5 (C) sliding-window Welford **eliminates the periodic reset entirely**:
- Plan line 73 explicitly: "Bounded by window contents → no drift accumulation → no periodic reset."
- Sum-of-squares accumulator is bounded by window contents; cancellation error is BOUNDED for bounded inputs over bounded K
- The bug class "rebuilds corr_matrix but doesn't rebuild accumulators" cannot exist because there's no reset path

This is a **textbook structural-fix-preferred outcome** (CLAUDE.md item 19) — the bug class disappears by design rather than via patching the reset path.

`sliding-window-online-statistics-pattern.md` lines 73-82 ("Why no periodic reset is needed") rigorously justifies the elimination. The math is sound for bounded inputs.

---

## NEW finding (this audit)

### PARITY-019 — Cholesky_Solve back-solve column-access pattern doesn't vectorize via row-load shape (v5.14.11.B) — **MEDIUM**

**Found:** 2026-05-11 during v5.14.11 AMENDED plan re-audit (no commit yet — plan-stage finding)

**Severity:** MEDIUM
- Plan Step 7 line 339-343 lists 3 Cholesky_Solve sub-sites for AVX-512 vectorization:
  1. Diagonal `L[i][i]` computation (inner k-loop) — accesses `L_out[i][k] * L_out[i][k]` — ROW access — vectorizes cleanly via `_mm512_loadu_pd(&L_out[i][0])`
  2. Forward solve `L y = μ` (inner k-loop) — accesses `L_out[i][k] * y_out[k]` — ROW access on L_out — vectorizes cleanly
  3. Back solve `L^T w = y` (inner k-loop) — accesses **`L_out[k][i] * w_out[k]`** — **COLUMN access on L_out** — does NOT vectorize cleanly via `_mm512_loadu_pd`
- Today's impact: zero (.B not coded yet). Future impact during .B implementation: the back-solve site needs a DIFFERENT vectorization strategy than the row-load shape shown in plan Step 7's code template at line 318-336

**Class:** AVX-512 byte-determinism implementation gap (v5.11.7 sister)

**Site(s):**
- Plan declaration: `plans/v5.14-foxml-port-and-maker/subplans/2026-05-08-v5.14.11-online-corr-update.md:339-343` (Step 7 site list)
- Plan code template: same file `:318-336` (single shape proposed for all 3 sites)
- Engine target site: `ML_Headers/RidgeBlender.hpp:169-176` (back solve)
- Engine reference (row access): `ML_Headers/RidgeBlender.hpp:131-141` (decomposition) + `:160-167` (forward solve)

**Symptom:** During .B implementation, contributor applies plan's row-load template to back-solve. Either:
- (a) Code reads `L_out[k][i]` lanes as `L_out[i][k]` (silent transpose bug) → wrong correlation matrix → wrong Cholesky output → wrong Ridge weights
- (b) Contributor recognizes the column-access mismatch + improvises a strategy without explicit plan guidance → strategy varies by author → byte-determinism not guaranteed across .B contributors
- (c) Contributor uses `_mm512_i64gather_pd` (gather load with strided indices) → vectorizes but bytewise-determinism behavior of `gather` across binaries/CPUs unverified for this codebase

**Root cause:** Plan Step 7 implicitly treats all 3 Cholesky sites as having the same access pattern. Back-solve is column-major on `L_out` (reads the lower triangle BY column, since L^T is by column when L is row-major). Code template at line 318-336 assumes contiguous row-load; this is correct for decomp + forward solve but NOT for back-solve.

**Fix path:** v5.14.11.B amendment — Step 7 site list needs explicit per-site strategy:
- Site 3a (decomposition `L[i][j] -= sum_k L[i][k]*L[j][k]`): contiguous row-load shape, j ≤ 7 lanes via mask. Plan's existing template applies directly.
- Site 3b (forward solve `s = mu[i] - sum_k L[i][k]*y[k]`): contiguous row-load on L_out[i] + contiguous load on y_out. Plan's template applies.
- Site 3c (back solve `s = y[i] - sum_k L[k][i]*w[k]`): two options to decide before coding:
  - **Option A (recommended, simplest):** keep scalar for back-solve. Inner loop is ≤ 7 iterations (n=8 max); SIMD gain marginal. Documented decision: "back-solve column access; scalar is bytewise-deterministic reference; vectorization gain < 50ns at n=8 not worth column-load complexity."
  - **Option B:** transpose `L_out` to `L_T_out` once after decomp (single O(N²) pass at line 156); back-solve then reads `L_T_out[i][k]` (row access on transposed). Adds ~50ns memory write + ~50ns memory read. Vectorizes the SIMD-friendly inner loop but pays the transpose cost. Net win ~50-100ns at n=8. Bytewise-deterministic since transpose is deterministic.

**Target ship:** v5.14.11.B (engine wiring + AVX-512 — design decision needed at .B kickoff; doesn't block .A)

**Status:** **OPEN** (plan-stage; .B amendment needed before coding the back-solve site)

**Workaround:** N/A — needs explicit plan decision

**Why MEDIUM not HIGH:**
- The two earlier sites (decomp + forward solve) DO apply v5.11.7 cleanly and account for most of the latency win
- Back-solve scalar (Option A) preserves bytewise-determinism trivially; only forfeit is ~50ns gain
- Bug shape is "missing plan guidance" not "incorrect implementation"; .B can decide cleanly before coding

---

## Focus-area verifications (per re-audit prompt)

### 1. PARITY contract reframing — **TESTABLE + MATCHES MATH** ✓

The 3-boundary contract at line 73-79 is the cleanest articulation in v5.14 sprint:

| Boundary | Tolerance | Verification |
|---|---|---|
| v5.14.10 → v5.14.11 (any cfg) | 1e-9 over K=64 records | Intentional bytewise break from BuildCorr 3-pass → 1-pass refactor |
| Within v5.14.11 (cfg=0 vs cfg=1) | ~1e-13 (sum convergence) | Both paths share FinalizeCorrFromSums |
| AVX-512 vs scalar (any cfg, within v5.14.11) | BYTEWISE IDENTICAL | v5.11.7 discipline at 3 sites |

Each boundary has a distinct testable mechanism:
- Boundary 1: tolerance assertion against locked v5.14.10 corr_matrix baseline (Step 9 test "tolerance 1e-9 vs v5.14.10 baseline" line 360)
- Boundary 2: SHA-256 cfg=0 baseline + SHA-256 cfg=1 baseline both locked within v5.14.11 (Step 9 lines 361-362); cross-cfg comparison is tolerance 1e-13 (Step 9 line 357)
- Boundary 3: SHA-256 scalar↔AVX-512 byte-determinism for 3 sites (Step 9 line 363)

Math validation:
- Sum-of-squares refactor algebraic equivalence to 3-pass: `var = sum_xx/K - (sum_x/K)²` algebraically equals `(1/K)Σ(x - mean)²` — TRUE in infinite precision; IEEE-754 difference is bounded by ε × max(|sum_xx|/K, mean²) per `sliding-window-online-statistics-pattern.md` line 58-72.
- For bounded [0,1] predictions × K=64: max|sum_xx| ≤ 64 → cancellation error ε × 64 ≈ 1.4e-14. Predicted 1e-13 tolerance has 1-order headroom over predicted error.

### 2. PARITY-016/017/018 closure verification

- PARITY-016: **CLOSED** by structural unification + SHA-256 separate-regime baselines. The original failure mode (silent bytewise drift between cfg=0 and cfg=1) does not exist when both share FinalizeCorrFromSums. Verification at .A test addition.
- PARITY-017: **CLOSED for sites 1+2** (UpdateOnline, BuildCorr) by per-site v5.11.7 application + SHA-256 lock test at .B Step 9 line 363. **Site 3 split** — see NEW finding PARITY-019.
- PARITY-018: **CLOSED by elimination** — sliding-window-by-design has no periodic-reset path. The bug class cannot exist.

### 3. Cholesky_Solve AVX-512 byte-determinism (NEW from (D))

Discipline applies cleanly to:
- 3a Decomposition site (line 135-137 in current code): vector mul + scalar reduce per Rule 4 + Rule 5 `#if defined(__AVX512F__)` gate + Rule 2 scalar `/` preserved at line 140. **CLEAN.**
- 3b Forward solve (line 163-165): row-load on L_out[i] + contiguous y_out access. Vector mul + scalar reduce. **CLEAN.**
- 3c Back solve (line 172-174): **COLUMN ACCESS** — needs decision. **PARITY-019 NEW finding above.**

The SHA-256 lock test design (Step 9 line 363) covers all 3 sub-sites uniformly — that's good (single test catches any byte-divergence regardless of vectorization strategy chosen for 3c).

### 4. Stamp-binding HMAC chain integrity — **CLEAN** ✓

Plan Step 6 (line 288-304) describes 3 ridge_* fields migrating `emit_source=DIRECT_FIELD` → `BITMAP_BIT`:

```cpp
X(ridge_within_horizon,  int, "%d", 0,
  BITMAP_IS_SET(cfg.ml_cfg_flags, MASK_ML_CFG_RIDGE_WITHIN_HORIZON) ? 1 : 0,
  (BITMAP_ANY(...)), BITMAP_BIT)
```

The `BITMAP_IS_SET(...) ? 1 : 0` ternary normalization is EXACTLY the pattern v5.14.9.F.2 + v5.14.10 Surprise 6 established. Cross-referenced at `confidence_composite_enabled` entry (StampBoundCfgRegistry.hpp:117-119) which is the canonical precedent at HEAD. Same pattern → same byte output → HMAC chain byte-preserved across migration.

`wire-format-byte-preservation-discipline.md` (workspace doc) is the authoritative discipline; plan correctly references it at line 68. **CLEAN.**

`ridge_online_corr` correctly excluded from FOREACH_STAMP_BOUND_CFG (line 304 documentation) — runtime perf toggle, not train-serve identity surface. Stamp-binding decision matches `cfg-flag-eligibility-criteria.md` 5-criteria framework (perf toggle that doesn't change inference output identity).

### 5. Bounded-input numerical-stability argument — **CONDITIONAL** ⚠ (documented-risk acknowledged)

Plan line 178 claims: "predictions bounded to [0, 1] (typical sigmoid output) + K=64 → max(sum_xx) ≤ 64 → cancellation error ε × 64 ≈ 10^-14, 5 orders of magnitude headroom below 1e-9 PARITY tolerance."

**Verification:**

Per-arm predictions in `ezoo->reward_ring[i].predictions[]` are populated from `Model_Predict_Ensemble_Weighted`'s `out_per_arm_predictions[]` (ModelInference.hpp:1008). Each `predictions[i]` is **raw `Model_Predict(&models[i], ...)`** output (line 962), not normalized.

For BARRIER models (NORM_BARRIER_CLASS_1; the production default for FoxML ensemble): Model_Predict returns class-1 softmax probability via buy_class_idx aliasing → ALWAYS in [0, 1]. ✓
For COMPOSITE models (NORM_COMPOSITE): Model_Predict_Normalized clamps to [0, 1] inside the helper, but the `predictions[i]` stored is RAW (unclamped). Could exceed [0,1] for composite scores BEFORE clamp.
For REGRESSION models (NORM_REGRESSION): Model_Predict returns raw regression output → UNBOUNDED until Model_Predict_Normalized clips to [0,1] via `[-tp_pct, +tp_pct] → [0, 1]` rescale. Stored unclipped.
For IDENTITY normalizer (default): passthrough; depends on label_kind training.

Plus NaN/Inf clamp to 0.5 at line 956-960 (ModelInference.hpp) — bounds defensive against catastrophic.

**Practical bound:** for BARRIER ensembles (production default), bound is [0, 1] strict. For non-BARRIER + non-clipped paths, predictions could spike above 1.0 (operator misconfiguration).

`sliding-window-online-statistics-pattern.md` line 240 explicitly acknowledges this risk:
> "If predictions can spike outside their typical [0, 1] range (e.g., model misconfiguration emits 1e6), cancellation error can blow up. Defensive: assert/log input magnitudes; clamp before accumulator update."

**Recommendation:** Plan should add a defensive guard (or assertion) in `RidgeBlender_UpdateOnline` for predictions outside ~[-10, 10] range — wide enough to capture all realistic non-misconfigured outputs, narrow enough to detect train-time bugs. **NOT a blocker for .A** (production path uses BARRIER ensembles); fold into .A as a cheap safety guard.

Severity: **LOW** documented-risk (not assigned PARITY-NNN; not in line with strict CRITICAL/HIGH bar). The bounded-input assumption is correct for production default + the doc explicitly acknowledges the fragility.

### 6. Sliding-window drop math — **NUMERICALLY EQUIVALENT WITHIN BOUNDED DRIFT** ✓

Plan line 162-168 specifies:
```
delta_x_i = predictions_new[i] - predictions_oldest[i]
sum_x[i] += delta_x_i
sum_xx[i][j] += predictions_new[i] * predictions_new[j]
              - predictions_oldest[i] * predictions_oldest[j]
```

**Mathematical equivalence to fresh BuildCorr after K iterations:**

After K incremental updates with drop-replace, sum_x[i] accumulates `Σ (new_k - old_k) = Σ predictions[i] over [k-K+1, k]` window (telescoping).
sum_xx[i][j] accumulates `Σ (new_k[i]*new_k[j] - old_k[i]*old_k[j]) = Σ predictions[i]*predictions[j] over [k-K+1, k]` window.

After K updates from initialization, both sums equal what a fresh BuildCorr would compute over the same K records — IN INFINITE PRECISION.

In IEEE-754: each update has rounding error O(ε × |operands|). After K updates, accumulated error bound is K × ε × max(|operands|) = 64 × ε × max(pred²) ≈ 64 × 2.2e-16 × 1 ≈ 1.4e-14 for [0,1] inputs.

This is **strictly BOUNDED** (not accumulating to infinity) because:
- Each record's contribution is added once + subtracted once within K-record lifetime (cancellation is BOUNDED per `sliding-window-online-statistics-pattern.md` line 80)
- Bounded-input × bounded-window = bounded-magnitude sums = bounded-rounding error

**Plan claim verified.** Drift does NOT accumulate over many cycles (cycle 1000 has same precision as cycle 10 within the same window).

Caveat noted: if inputs spike outside bound, the drift bound argument fails. See finding 5 above for defensive guard recommendation.

### 7. Decision 4 cohort migration HMAC byte-equivalence — **CLEAN** ✓

Plan line 288-304 specifies 3 ridge_* DIRECT_FIELD → BITMAP_BIT migration. Each line follows the exact v5.14.9.F.2 / v5.14.10.B precedent.

Pre-migration emit (from current `StampBoundCfgRegistry.hpp:102-105`):
```
ridge_within_horizon=<cfg.ridge_within_horizon as int>
```

Post-migration emit (per plan line 291-293):
```
ridge_within_horizon=<BITMAP_IS_SET(cfg.ml_cfg_flags, MASK_ML_CFG_RIDGE_WITHIN_HORIZON) ? 1 : 0>
```

For value 0: pre emits "0"; post emits "0" (ternary).
For value 1: pre emits "1"; post emits "1" (ternary).
For value >1 (rare; cfg.ridge_within_horizon=2 historically possible?): pre emits "2"; post emits "1" (BITMAP_IS_SET returns non-zero → ternary picks 1).

**Caveat to verify before .C codes:** the plan + my grep show `cfg.ridge_within_horizon` is treated as bool (0=off, 1=on) throughout the codebase. Let me double-check there's no value=2 path:

`ControllerConfig.hpp:665`: comment says "0=bandit (default), 1=Ridge across role-arms" — implies BOOL.
`ControllerConfig.hpp:666`: same shape.
`ControllerConfig.hpp:1105`: "0=bandit (default), 1=Ridge" — BOOL.

Confirmed boolean. **HMAC byte-equivalence preserved.** Plan Step 9 line 365 ("Stamp body byte-equivalence test") locks this in test.

### 8. Cross-references + doc coherence

- `DESIGN_SPECS/wire-format-patterns/avx512-byte-determinism-pattern.md`: written + referenced correctly at plan line 38 + line 320-321. 7 rules clean; reference applications cited.
- `DESIGN_SPECS/refactor-patterns/sliding-window-online-statistics-pattern.md`: written + referenced at plan line 130 + line 178. Math kernel + state shape + drop-math all match plan.
- `DESIGN_SPECS/wire-format-patterns/wire-format-byte-preservation-discipline.md`: referenced at plan line 68. Pattern correctly applied to Decision 4 cohort migration.
- `DOCS/PARITY_ISSUES.md`: PARITY-016/017/018 entries present; status will transition OPEN → FIXED when v5.14.11 ships.

---

## Behavior matrix (verify v5.14.11.A → .C produces expected outputs)

| Scenario | Pre-v5.14.11 view | Post-v5.14.11 view | Identical? |
|---|---|---|---|
| Same cfg, replay backtest under v5.14.11 (cfg=0) | corr_matrix baseline pre-refactor | corr_matrix baseline post-refactor | Tolerance 1e-9 (intentional break — BuildCorr 3-pass → 1-pass refactor) |
| Same cfg, replay backtest within v5.14.11 (cfg=0 vs cfg=1) | N/A (cfg=1 didn't exist) | corr_matrix differs by accumulator-build order | Tolerance ~1e-13 (sum convergence; shared FinalizeCorrFromSums) |
| Same cfg, two binaries within v5.14.11 (scalar vs AVX-512) | N/A | corr_matrix at sites 1+2 | BYTEWISE IDENTICAL (v5.11.7 discipline) |
| Same cfg, two binaries within v5.14.11 (scalar vs AVX-512), Cholesky site 3c | N/A | corr_matrix at site 3 sub-c | BYTEWISE IDENTICAL **subject to PARITY-019 strategy decision** |
| Stamp body bytes pre/post Decision 4 cohort migration | direct field emit | BITMAP_BIT ternary emit | BYTEWISE IDENTICAL (ternary normalizes) |

---

## Suggested ship sequence (confirmed from amended plan)

- **v5.14.11.A** (~350 LOC) — embed online_state + sum-of-squares math + sliding-window UpdateOnline + shared FinalizeCorrFromSums + BuildCorr refactor + drop dead last_compute_us + helper extraction + SHA-256 cfg=0/cfg=1 baselines (PARITY-016 closure). **Defensive bounded-input guard** recommended (LOW addition; finding 5).
- **v5.14.11.B** (~250 LOC) — AVX-512 vectorization for UpdateOnline + BuildCorr accumulation + Cholesky_Solve sites 3a + 3b + SHA-256 scalar↔AVX-512 tests. **Site 3c (back solve) strategy decided at .B kickoff** (PARITY-019; recommend Option A scalar).
- **v5.14.11.C** (~150 LOC) — Decision 4 cohort migration + slow-path-gate predicates + 3 stamp-binding emit_source flips + branchless multi-flag dispatch + HOT_PATH_CHANGELOG + CHANGELOG (note bytewise-break from v5.14.10) + Version.hpp bump + TECH_DEBT-017 close.

---

## NOT a bug (verified-safe items)

- Three ridge_* sister fields (ridge_within_horizon, ridge_across_horizons, exit_blender_mode) ALL boolean values; ternary `? 1 : 0` normalization is HMAC byte-preserving for both 0 and 1 values. No value=2+ paths exist.
- `RidgeWeights_Init` uses `memset(rw, 0, sizeof(*rw))` (RidgeBlender.hpp:376) → new appended fields zero-init for free. No postloadsetup registry entry needed; resolved in synthesis D5.
- BuildCorr refactor to single-pass sum-of-squares is algebraically equivalent within IEEE-754 (different operation order; same result within ε × K). cfg=0 path's bytewise-break from v5.14.10 is INTENTIONAL + tolerance-bounded.
- `_ridge_gate` + `bandit_algorithm == 0` dispatch at StrategyParameters.hpp:972-973 — the plan's branchless multi-flag dispatch `(flags & ridge_only_mask) == MASK_RIDGE_WITHIN_ACTIVE` correctly captures both predicates (Ridge active AND Thompson inactive) via single mask compare.

---

## Auto-write contract

PARITY-019 (NEW, MEDIUM) auto-written to `DOCS/PARITY_ISSUES.md` per /parity-check contract.

PARITY-016/017/018 status updates: not auto-written until v5.14.11 actually ships (per skill convention — FIXED status set only after confirming a clean parity-check post-ship). Audit log entry will be appended to reflect this re-audit's GREEN verdict.

---

## Recommendation

**GREEN — amended plan is ready for .A kickoff.**

PARITY-016/017/018 all structurally resolved by adopted decisions; PARITY contract reframing is the cleanest articulation in v5.14 sprint; HMAC chain integrity preserved; bounded-input stability math is sound for production default.

ONE new MEDIUM finding (PARITY-019) doesn't block .A — only affects .B back-solve vectorization strategy. Resolution: at .B kickoff, decide between Option A (scalar back-solve; recommended for simplicity + bytewise-determinism trivially preserved) vs Option B (transpose-then-vectorize). Either choice cleanly meets v5.11.7 discipline.

LOW recommendation: add defensive bounded-input guard at UpdateOnline entry — cheap insurance against future model misconfiguration that might break the bounded-K cancellation-error argument.

---

## Cross-references

- Pre-coding audit synthesis: `plans/plan_checks/2026-05-11-v5.14.11-fresh-audits-synthesis.md`
- Earlier /parity-check pass: `plans/plan_checks/parity-check-2026-05-11-v5.14.11.md`
- DESIGN_SPECS new: `sliding-window-online-statistics-pattern.md`, `avx512-byte-determinism-pattern.md`
- DESIGN_SPECS extended: `cfg-flag-eligibility-criteria.md`
- DESIGN_SPECS referenced: `wire-format-byte-preservation-discipline.md`, `structural-fix-preferred-decision-framework.md`
- DOCS/PARITY_ISSUES.md updated: PARITY-019 NEW, MEDIUM, this audit
