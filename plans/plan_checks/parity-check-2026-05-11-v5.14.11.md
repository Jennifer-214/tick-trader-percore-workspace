# /parity-check report — 2026-05-11 — v5.14.11 online correlation matrix updates

## Plan summary

- **Plan:** `plans/v5.14-foxml-port-and-maker/subplans/2026-05-08-v5.14.11-online-corr-update.md`
- **HEAD:** e0cc877 (v5.14.10 close)
- **Pre-tag:** `pre-v5.14.11` (exists)
- **Audit scope:** narrow — parity surfaces touched by the plan
  - Welford-incremental ↔ batch BuildCorr identity (numeric tolerance)
  - AVX-512 ↔ scalar bytewise identity (cross-binary determinism)
  - New cfg field stamp-binding eligibility
  - Default-off bytewise-identity to v5.14.10
  - Periodic-reset path identity to standalone full BuildCorr
- **Cross-check baseline:** post-v5.14.10 protections inventory
  (PARITY-001…PARITY-015, FOREACH_STAMP_BOUND_CFG with 23 entries, AVX-512
  determinism discipline at `ML_Headers/BanditLearning.hpp:120-194`)

## TL;DR

**Verdict: YELLOW.** Two HIGH replay-determinism findings (one for the
Welford↔batch tolerance contract, one for the AVX-512↔scalar bytewise
contract), one MEDIUM observability finding (Cholesky-fallback ordering
divergence). All three are plan-stage tightenable in v5.14.11.A / .B
without enlarging scope. Proceed with plan amendment, then code.

The plan itself is well-scoped, default-off, no train↔serve handoff
surface, no stamp body / scaler / feature-registry / label changes. The
risk surface is bounded to **replay-determinism** (CLAUDE.md item 14
parity contract + v5.9.2 backtest test at `tests/controller_test.cpp:19506`
+ Bandit_GetProbabilities AVX-512 precedent v5.11.7).

---

## Findings by severity

### HIGH

#### PARITY-016 — Welford↔batch tolerance contract not bytewise-deterministic; replay-determinism test (v5.9.2) shape mismatch

**Site(s):**
- Plan Step 5 line 168: "result equivalent to full BuildCorr within tight
  tolerance (1e-9) over K=64 records"
- Plan Step 5 line 175-176: "Default cfg (ridge_online_corr=0):
  bytewise-identical to v5.14.0 full recompute"
- Existing replay-determinism contract: `tests/controller_test.cpp:19506-19526`
  ("same input → same output bytewise … FPN<64> wraps a 4096-bit int
   internally — bytewise equality is exact (no float rounding)")
- Existing v5.14.1.B.2.C composite-replay determinism at line 3495-3504
- `RidgeBlender_BuildCorr` computes correlation via doubles (FPN sqrt
  only at boundary), so the existing contract for THIS function is "same
  input → same double output bit-for-bit"; not Welford-tolerance-shaped

**Symptom:** With `cfg.ridge_online_corr=1`, two backtest replays over
the identical tick stream produce `ezoo->ridge_state.corr_matrix[][]`
values that AGREE to 1e-9 tolerance but DIFFER at the bit level (low-order
mantissa bits drift differently due to incremental Welford accumulation
order vs batch two-pass mean-then-variance computation). Downstream:
Cholesky_Solve on bit-different `corr_matrix` produces bit-different
`L`, `y`, `w_internal`, `w[]`. FPN_FromDouble at the boundary rounds the
double to FPN<64> — same FPN bytes within tolerance but bit-different
doubles can round to ADJACENT FPN values at any rounding boundary. Net:
backtest replay produces "same trades but different snapshot bytes" with
nonzero probability, breaking the v5.9.2 replay-determinism contract
that v5.14.1.B / v5.14.10.A both relied on for parity testing.

**Root cause:** Welford one-pass incremental update and the existing
two-pass batch formula at `ML_Headers/RidgeBlender.hpp:308-358` produce
mathematically-equivalent results in infinite precision but NOT in IEEE-754
finite precision. The plan currently treats them as "tolerance-equivalent"
which is correct for the ML-quality contract but FALSE for the
replay-determinism contract. cfg=0 (default) preserves bytewise; cfg=1
(online) silently does not — the contract drift is hidden behind a runtime
toggle that defaults off.

**Recommended fix (v5.14.11.A scope):** Tighten the plan's
replay-determinism claim before coding. Two paths, pick one:

1. **Reframe the contract.** Document that `ridge_online_corr=1` is a
   distinct backtest replay-determinism regime. Same-binary same-cfg
   replays are still bytewise (Welford accumulation is deterministic
   given fixed order); cross-cfg (cfg=0 ↔ cfg=1) replays diverge within
   tolerance. Add a replay-determinism test at v5.14.11.A that runs the
   same backtest twice under cfg=1 and asserts bytewise identity (same
   shape as `tests/controller_test.cpp:19506-19526`). Snapshot the
   corr_matrix SHA-256 lock for both cfg=0 and cfg=1 runs over a fixed
   1000-record prediction trace; cfg=0 hash and cfg=1 hash differ but
   each is stable across runs.

2. **Drop the "bytewise-identical to v5.14.0" claim for cfg=1.** The
   plan currently implies cfg=0 stays byte-identical AND cfg=1 matches
   cfg=0 within tolerance. The tolerance-only relationship between
   cfg=0 and cfg=1 needs to be stated explicitly. Periodic-reset every
   1000 cycles (plan Step 3 line 144-148) does NOT recover bytewise
   identity to cfg=0 — it recovers tolerance identity at the reset
   boundary but bit-drifts again over the next 1000 cycles.

**Cross-ref:** ALREADY-PROTECTED for cfg=0 (default-off; bytewise-identity
to v5.14.10 holds because BuildCorr path is unchanged). GAP for cfg=1
runtime regime + the operator-facing "tolerance" framing.

**Effort estimate:** 30 min (contract reframe + 2 snapshot-locked SHA-256
tests in v5.14.11.A; mirror shape of `tests/controller_test.cpp:22479-22533`
Thompson sample-trace test).

---

#### PARITY-017 — AVX-512 vectorization bytewise-determinism: plan cites discipline; needs explicit pre-coding checklist + snapshot test

**Site(s):**
- Plan Step 2 line 107-131 (AVX-512 vectorization design)
- Plan Step 2 line 127-130 cites the v5.11.7 discipline (mul-by-reciprocal
  avoided, fmadd order matches gcc -O3, scalar reductions stay scalar)
- v5.11.7 Bandit_GetProbabilities reference at
  `ML_Headers/BanditLearning.hpp:138-194`
- Build flags: `-O3 -march=native -funroll-loops -flto` (CMakeLists.txt:11,
  128, 177, 214). `-ffp-contract=fast` is gcc default at -O3 → fmadd
  fusion is on
- Plan Step 5 line 172: "AVX-512 path: byte-identical to scalar path on
  test harness"

**Symptom:** AVX-512 vectorization of the outer-product
`outer_xy[i][j] += (p[i] - mean[i]) × (p[j] - mean[j])` is bytewise-fragile
in 4 places the plan currently leaves unchecked:

1. **Outer-product reduction order.** Welford's running update is
   `outer_xy_new = outer_xy_old + delta`. AVX-512 stores 8 lanes per
   iteration — sum order across rows is irrelevant (only intra-row
   matters). Plan's vectorization sketch (line 119-126) doesn't show how
   the row sweep loop preserves left-to-right scalar order.

2. **Welford mean update divider** (`mean_new = mean_old + delta / n`).
   `delta/n` must use `_mm512_div_pd`, NOT `_mm512_mul_pd(delta, 1/n)` —
   identical pattern to v5.11.7 line 184. Plan only cites this for the
   outer product; mean update is unmentioned.

3. **FinalizeCorr divider** (`corr[i][j] = outer_xy[i][j] /
   sqrt(M2[i] × M2[j])`). Same _mm512_div_pd discipline. Plus
   `_mm512_sqrt_pd` must match scalar `std::sqrt` per IEEE-754 (which it
   does — both are correctly-rounded).

4. **Constant-prediction guard** (`if (std[i] < 1e-9) corr_out[i][j] = 0`).
   Plan doesn't show how the AVX-512 path implements this branchless
   mask — a different blend-mask pattern than the scalar early-out gives
   bit-different zeros (e.g., `0.0 / 0.0` = NaN vs explicit `0.0`).

**Root cause:** Plan cites v5.11.7 discipline but doesn't enumerate the
sites where it must apply. v5.11.7 had ONE division site
(`_mm512_div_pd(w, sum_w_vec)`) and ONE fmadd site
(`_mm512_fmadd_pd(one_min_g, normd, g_over_K)`); plan introduces 3
division sites + 1 fmadd site + 1 mask-branch site. Easy to miss one.

**Recommended fix (v5.14.11.B scope):**

1. Add explicit per-site discipline annotation in plan Step 2 (mirror the
   v5.11.7 commentary at `ML_Headers/BanditLearning.hpp:146-152`):
   - UpdateOnline outer product: fmadd order, no reduce
   - UpdateOnline mean update: div_pd not mul-by-reciprocal
   - FinalizeCorr division: div_pd not mul-by-reciprocal
   - FinalizeCorr constant-prediction guard: mask-blend pattern
     (explicit `0.0` from `_mm512_setzero_pd`, NOT NaN-from-0/0)

2. Add SHA-256-locked snapshot test in v5.14.11.B (mirror shape of
   `tests/controller_test.cpp:22498-22533` Thompson sample-trace test):
   feed a fixed 1000-record prediction trace through both scalar and
   AVX-512 paths; SHA-256 both `corr_matrix` byte-streams; assert hashes
   match between scalar and AVX-512. Future compiler/flag drift trips
   the test immediately.

**Cross-ref:** GAP. v5.11.7 discipline exists in code but is NOT
mechanically enforced — the burden is on each new AVX-512 contributor to
re-read the precedent. PARITY-014 close added a Thompson sample-trace
SHA-256 lock; same pattern wants to land here.

**Effort estimate:** 45 min (4 explicit annotations in plan Step 2 + 1
snapshot test in v5.14.11.B; pattern proven).

---

### MEDIUM

#### PARITY-018 — Periodic recompute path uses BuildCorr but doesn't reset RidgeOnlineState — drift bound is conditional on reset semantics

**Site(s):**
- Plan Step 3 line 144-153 (engine wiring; periodic recompute branch)
- Plan Step 3 line 146-148: "Recompute from scratch via existing
  BuildCorr; reset cycles" — but plan does NOT reset `mean[]`, `M2[]`,
  `outer_xy[]`, or `n` after the BuildCorr call
- Sliding-window vs reset semantics not specified: plan line 70-72
  mentions "Sliding-window variant (drop oldest record)" but Step 3
  doesn't show drop-oldest arithmetic

**Symptom:** After `cycles_since_recompute > 1000`, plan calls full
`RidgeBlender_BuildCorr` to refresh `corr_matrix` from the ring (this is
correct). But it ONLY resets `cycles_since_recompute = 0` — the running
`mean[]`, `M2[]`, `outer_xy[]`, `n` accumulators are NOT reset. Next
cycle's `UpdateOnline` resumes from STALE Welford state, immediately
diverging from the freshly-rebuilt `corr_matrix`. Two interpretations:

A. **Plan intends "BuildCorr writes corr_matrix; Welford state keeps
   drifting".** Then drift bound argument (plan line 71-73) is wrong —
   periodic reset doesn't refresh the Welford accumulators, only the
   downstream output. The next 1000 cycles' UpdateOnline writes drift
   into corr_matrix from the next FinalizeCorr call.

B. **Plan intends "BuildCorr + reset Welford accumulators from the ring
   too".** Then there's a missing Step 3 sub-step: rebuild
   `RidgeOnlineState` from `predictions_history`. Cost equivalent to
   ~2-3× BuildCorr's O(N²K) (one pass for mean, one for M2, one for
   outer_xy). Not specified in plan.

**Recommended fix (v5.14.11.C scope):** Decide A vs B before coding;
add the chosen branch to plan Step 3 with explicit arithmetic. If B,
add a `RidgeBlender_RebuildOnlineState(state, history, n_history,
n_models)` helper (called inside the same `if` branch as BuildCorr) that
runs the two-pass mean/M2 + outer_xy accumulation over the ring's last
K records. Cost: O(N²K) — same as BuildCorr, called once per 1000
cycles, ~1µs amortized over 1000 cycles = 1ns/cycle.

Additionally clarify the sliding-window claim (line 70-72): if the plan
intends to support drop-oldest, Step 3 needs `UpdateOnline_DropOldest`
arithmetic, also bytewise-deterministic (one subtract + one outer-product
update; same div/fmadd discipline). Currently the plan implies sliding-window
exists but Step 3 only shows append-only.

**Cross-ref:** GAP. Same shape as PARITY-009/010/011/012 Class 18 mirror
drift — the periodic-reset gate is "logically the same as BuildCorr at
boot" but the path-walk is missing one of three accumulator rebuilds.

**Effort estimate:** 30 min (1 helper + plan amendment + 1 test).

---

#### NEW-FINDING-1 (LOW) — Cfg field `ridge_online_corr` is NOT stamp-binding-eligible — verify nothing in plan implies otherwise

**Site(s):**
- Plan Step 4 line 161-164: `int ridge_online_corr;`
- Plan does NOT propose adding to FOREACH_STAMP_BOUND_CFG at
  `ML_Headers/StampBoundCfgRegistry.hpp:99-162`

**Analysis:** Apply the stamp-binding eligibility test:

1. Does the cfg field change the MODEL FILE bytes? No. (XGBoost models
   are unchanged; no training-time interaction.)
2. Does it change the SCALER bytes? No.
3. Does it change FEATURE values? No. (Feature compute is untouched.)
4. Does it change LABELS? No.
5. Does it change the inference OUTPUT bytes given the same model +
   scaler + features? **Conditionally — see PARITY-016.** The plan
   intends cfg=0 ↔ cfg=1 to be tolerance-equivalent for the corr_matrix,
   which propagates to ridge weights → ensemble blended weights → trade
   sizing. So cfg=1 IS inference-affecting under strict bytewise
   definition (tolerance only under loose definition).

**Verdict:** Cfg=0 (default) is the train-time + serve-time assumption;
flipping to cfg=1 in production after training with cfg=0 produces
TOLERANCE-EQUIVALENT but BIT-DIFFERENT corr matrices → tolerance-equivalent
blended weights → tolerance-equivalent fills. The threshold for
"stamp-binding required" in this codebase is "would the operator
notice if they trained under one cfg and served under the other?".
For Thompson (PARITY-013), the answer was yes (one-hot vs blended
weights = qualitatively different). For ridge_online_corr, the answer
is NO under tolerance (just bit-drift; trade decisions are equivalent
in P&L statistics) and yes under bytewise.

**Recommendation:** Document the decision explicitly in v5.14.11.C:
- **Option 1 (recommended):** Skip stamp binding. Document in
  `engine.cfg.example` that `ridge_online_corr=1` is a perf toggle
  with tolerance-equivalent output to cfg=0; replay-determinism is
  per-cfg.
- **Option 2 (conservative):** Add to FOREACH_STAMP_BOUND_CFG with
  `emit_when: (cfg.ridge_online_corr != 0)` (so legacy cfg=0 stamps
  load with has_*=0 — Surface G forward-compat). Treats cfg=1 as a
  distinct "inference regime" requiring stamp-binding even though
  outputs are tolerance-equivalent. ~10 min additional work; matches
  the conservative posture of PARITY-013 close for cfg.bandit_algorithm.

**Cross-ref:** ALREADY-PROTECTED partially. cfg=0 default + bytewise
to v5.14.10 means existing stamps are safe. Plan's silence on
stamp-binding is OK if the decision is documented; flag because the
silence could be read as "I forgot to consider this."

**Effort estimate:** Option 1: 5 min docs. Option 2: 15 min (1 X-row +
1 default init + 1 .cfg.example line).

---

### NOT-A-BUG (verified-safe items)

- **Default-off discipline.** Plan Step 4 line 162-163 specifies
  `ridge_online_corr=0` as the default; the engine wiring at plan Step
  3 line 154-157 takes the `RidgeBlender_BuildCorr<F>(...)` branch when
  cfg=0, which is the v5.14.10 path unchanged. Bytewise-identical to
  v5.14.10 for default operators confirmed by Strategies/StrategyParameters.hpp:996+1195
  unchanged in cfg=0 branch.

- **No train↔serve handoff surface.** Plan does NOT touch:
  - Features (FOREACH_FEATURE unchanged; scaler unchanged;
    feature_registry_hash unchanged)
  - Labels (FOREACH_TARGET unchanged)
  - Stamp body schema (no new fields added; cfg ridge_online_corr
    deliberately NOT bound per NEW-FINDING-1)
  - Model file format (MODEL_FORMAT_VERSION unchanged)
  - Scaler sidecar format
  - Cross-binary handshake

- **Hot path untouched.** Plan Step 3 line 184: "Hot path UNTOUCHED."
  Verified by grep — Strategies/StrategyParameters.hpp:996 is the
  ML_BuildParameters dispatch site which is slow-path (per-cycle Ridge
  build, not per-tick).

- **TWO BuildCorr call sites flagged in plan.** Plan REUSE claims line
  16-20 correctly identifies both sites (StrategyParameters.hpp:996
  buy-side; :1195 exit-side). Both must be parity-protected together
  or the exit-side path silently runs the v5.14.10 BuildCorr while the
  buy-side runs the online path → asymmetric replay-determinism between
  fills and exits. Plan acknowledges this but doesn't show the exit-side
  wiring code; flag as work item for .C, not a parity gap.

- **`predict_call_count` vs `exit_predict_call_count` ring-state mirror.**
  Existing buy-side uses `ezoo->predict_call_count`; exit-side uses
  `ezoo_ex->exit_predict_call_count`. Online accumulator state needs
  both `ezoo->ridge_online_state` and `ezoo_ex->exit_ridge_online_state`
  fields (or a single shared one with role discriminator). Plan Step 1
  shows one struct; .C wiring needs to add the second. Class 18 mirror
  risk → flag as `/dod-audit` territory, not a parity gap.

---

## Cross-cutting concerns

- **Replay-determinism IS the bottleneck.** Both HIGH findings collapse
  to one structural fix: define + lock SHA-256-snapshot the corr_matrix
  byte-stream for fixed input traces, separately for cfg=0 and cfg=1
  and (within cfg=1) separately for scalar and AVX-512. v5.14.11.A adds
  the scalar lock; v5.14.11.B adds the AVX-512 lock. Same pattern as
  PARITY-014 Thompson sample-trace SHA-256 close.

- **`/parity-check` re-run gate.** Per CLAUDE.local.md going-forward
  rule (2026-05-09 auto-write), each HIGH finding above is also added
  as PARITY-016 / PARITY-017 / PARITY-018 to `DOCS/PARITY_ISSUES.md`
  with status OPEN (plan-stage). Verify in post-coding re-audit.

- **TWO call sites mean TWO online-state fields.** Plan amendment for
  v5.14.11.C should explicitly add both `ezoo->ridge_online_state` and
  `ezoo_ex->exit_ridge_online_state` fields to EnsembleModelZoo struct
  (or a per-side variant) — Class 18 mirror risk if only one side gets
  the field.

---

## Behavior matrix (verify train and serve agree for default cfg)

| Scenario | Trainer view | Engine view | Identical? |
|---|---|---|---|
| cfg.ridge_online_corr=0 (default) | N/A (no training-time interaction) | v5.14.10 BuildCorr path unchanged | **YES, BYTEWISE** |
| cfg.ridge_online_corr=1, same binary | N/A | Welford accumulator | YES, BYTEWISE (deterministic given fixed order) |
| cfg.ridge_online_corr=1, different binary (libgomp / -O level change) | N/A | Welford accumulator | **UNVERIFIED** (PARITY-017 — needs SHA-256 snapshot lock) |
| cfg=0 ↔ cfg=1 cross-cfg replay | N/A | One path tolerance-equivalent to other | **NO, TOLERANCE ONLY** (PARITY-016 — needs contract reframe) |
| AVX-512 build vs scalar build, cfg=1 | N/A | AVX-512 path | **UNVERIFIED** (PARITY-017 — needs SHA-256 snapshot lock) |

---

## Suggested ship sequence

- **v5.14.11 plan amendment (pre-coding, ~30-60 min):**
  - Reframe replay-determinism contract per PARITY-016 (Option 1 or 2)
  - Enumerate 4 AVX-512 discipline sites per PARITY-017 (in plan Step 2)
  - Decide periodic-reset semantics per PARITY-018 (option A or B; add
    helper if B)
  - Document stamp-binding decision per NEW-FINDING-1 (Option 1 or 2)
  - Confirm TWO online-state field locations in plan Step 1
- **v5.14.11.A (scalar online kernel + tests):** add SHA-256-locked
  snapshot test for cfg=1 scalar path (closes PARITY-016 stamping)
- **v5.14.11.B (AVX-512 vectorization):** add SHA-256-locked snapshot
  test for AVX-512 path matching scalar (closes PARITY-017)
- **v5.14.11.C (engine wiring + cfg propagation + .cfg.example doc):**
  add stamp-binding row if Option 2 (closes NEW-FINDING-1); resolve
  TWO-call-site mirror in same commit
- **v5.14.11 umbrella tag** after .C green

---

## Notes for the operator

This is a parity audit only — no `/merge-scan`, `/dod-audit`,
`/readiness`, or `/trace-deps` ran in parallel here. Recommend running
those alongside this audit if not already done (the typical .E-D
amendment cycle from v5.14.10 used 5 parallel pre-coding audits).

The plan as written is structurally sound; findings are all
"tighten the contract" not "redesign the approach." Per CLAUDE.local.md
"address audit findings now > defer to issues later" rule, the ~60 min
plan amendment is recommended before v5.14.11.A code starts.

`DOCS/PARITY_ISSUES.md` auto-write contract per CLAUDE.local.md
2026-05-09: PARITY-016, PARITY-017, PARITY-018 will be appended to the
ledger as part of this audit.
