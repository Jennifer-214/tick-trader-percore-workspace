# /readiness report — v5.11.2-slow-path-o1-regression — 2026-05-06

## Plan summary

- **3 sub-ships planned** (v5.11.2.A → 2.B → 2.C → final tag v5.11.2)
- **Effort claim:** ~4-5h, ~120-180 LOC delta in `ML_Headers/RollingStats.hpp` + `ML_Headers/LinearRegression3X.hpp` (defer) + new `ML_Headers/ReciprocalLUT.hpp`
- **Branch:** `feat/v5.11-optimization` at HEAD `beacb59` (verified — branch matches current; HEAD has tags `v5.11.1` AND `v5.11.1.2` — plan only mentions `v5.11.1`)
- **Hot path:** UNTOUCHED (verified — RollingStats absent from `ExecutionCore.hpp`, `OrderGates.hpp` / BG_Evaluate / SG_Evaluate)

## Checklist verdicts (10-item review)

| # | Item | Verdict | Notes |
|---|------|---------|-------|
| 1 | Hot path purity | **PASS** | Verified: no `RollingStats` reference in ExecutionCore.hpp, OrderGates.hpp; "slow-path-only ship" claim holds |
| 2 | Train-serve parity | **DRIFT-RISK** | Phase 2.A `FPN_Mul(sum, recip[n])` ≠ `FPN_DivNoAssert(sum, n_fp)` at the ULP level. Replay-determinism test (controller_test.cpp:10258) does **bit-exact float compare** via `memcmp(&a, &b, sizeof(float)) != 0` — ANY ULP drift fails the test. Plan's mitigation (regenerate baseline) is acceptable but model retrain may be required |
| 3 | Surface area | **PASS** | 3 files touched (1 new, 2 edited); LinearRegression3X.hpp may be deferred. ≤8 files |
| 4 | Pointer init / heap | **PASS** | Meyer's singleton in `GetReciprocalLUT<F,W>` is C++11+ thread-safe. RollingStats fields all stack-init via `_Init` |
| 5 | Backward compat | **GAP** | RollingStats struct change in Phase 2.B + 2.C affects `ShardedSnapshotPersist` if it serializes RollingStats. Plan does not mention `SHARDED_SNAPSHOT_VERSION`. **Verify** whether `ShardedSnapshot.hpp` snapshots the RollingStats struct or just outputs (price_avg, etc). If the former, version bump required |
| 6 | Multi-threading | **DRIFT-RISK** | Phase 2.B claims false-sharing reduction with GUI thread. RollingStats is also embedded INLINE in `PortfolioController` (line 247: `RollingStats<F> rolling`). Adding `alignas(64)` to internal field forces alignment of ENCLOSING struct — may push hot-cache fields off their cache lines (see explicit comments at PortfolioController.hpp:245). Plan should validate post-reorder offsets |
| 7 | Test coverage | **GAP** | Plan lists 3 new tests in Phase 2.C ("test_rollingstats_o1_sums_match_ow_recompute", etc) but doesn't specify WHERE they land in `tests/controller_test.cpp` (which EXTENSIBILITY block). Existing RollingStats tests at `controller_test.cpp:1470, 1596, 4041, 4168, 4722, 4890, 4953, 5022, 5434` — propose adding new tests in a v5.11.2-prefixed EXTENSIBILITY block |
| 8 | Docs + invariants | **GAP** | Plan modifies a regression-sums implementation without proposing a `DOCS/CLAUDE_INVARIANTS.md` entry for the periodic-resync discipline (every 100k pushes). New invariant: "RollingStats O(1) running sums must resync every N pushes to bound FPN-saturation drift." Add as enforced by the periodic-resync trigger + the new test that asserts it |
| 9 | Forward maintenance | **DRIFT** | RollingStats template is instantiated at W=128, W=256, W=512, W=1024 (PortfolioController.hpp:248-252). Plan only proposes `static_assert` for `<64, 128>`. Other instantiations (rolling_long, rolling_medium, rolling_baseline) silently bypass the layout invariant. Propose: make the static_assert template-parametric over `<F, W>`, or add it inside the struct definition |
| 10 | Rollback story | **PASS** | `pre-v5.11.2` anchor at `beacb59`; per-phase tags (`v5.11.2.A/B/C`); push commands listed |

## Architectural / extra checks

| # | Check | Verdict | Notes |
|---|-------|---------|-------|
| 11 | Sprint sprint detection | **PASS** | Localized refactor; not architectural; no "extract", "decouple", "shard" keywords |
| 12 | Display ↔ execution invariant | **PASS** | RollingStats fields read by-name in 30+ sites (verified via grep `rolling->price_avg` etc); reorder safe |
| 13 | Strategy lifecycle | **PASS** | No strategy lifecycle touched |
| 14 | X-macro dispatch | **PASS** | No X-macro / function-pointer dispatch added |
| 15 | ML feature change | **PARTIAL — DRIFT-RISK** | RollingStats is upstream of `Features_PackAll` and `Regime_ComputeSignals`. ULP drift in Phase 2.A or O(1) drift in Phase 2.C will cascade through to feature_matrix → break v5.9.2 replay test. Plan acknowledges. **Snapshot test impact:** if FEATURE_REGISTRY_HASH or RegimeSignals snapshot tests exist that pin the exact byte values of `price_avg` / `price_variance`, those will need bumped baselines |
| 16 | Stamp-bearing cfg | **PASS** | No new cfg field |
| 17 | Model-load path | **PASS** | No model-load changes |

## Dependency verification (file:line refs)

| Claim | Verified | Notes |
|---|---|---|
| `RollingStats_Push` at `RollingStats.hpp:115` | `:115-116` | template line is 115; function definition is 116. Close — accept |
| 5-sum O(W) loop at `:174-189` | **VERIFIED** | exact match |
| `FPN_DivNoAssert(price_sum, n_fp)` at `:202-203` | **VERIFIED** | exact match |
| `FPN_DivNoAssert(ss_total, n_sq)` at `:215` | **VERIFIED** | exact match |
| RollingStats struct at `:35-69` | **VERIFIED** | exact match |
| `LinearRegression3X_Fit` at `LinearRegression3X.hpp:100-145` | **VERIFIED** | also uses `FPN_DivNoAssert` (lines 130, 133, 141) — Phase 2.A could apply |
| Replay-determinism at `controller_test.cpp:10147` (block) / `:10258` (assertion) | **VERIFIED** | block at 10147 ("v5.9.2 Phase 3 — train-serve parity"), bytewise assertion at 10258. Plan's other claim of `:10251` is column-index assignment, not assertion — minor doc bug |
| `FPN<64> = 24 bytes` | **VERIFIED via inspection** | `uint64_t w[2]` (16B) + `int32_t sign` (4B), 8-byte aligned = 24B effective. ✅ |
| `FPN_DivNoAssert`, `FPN_Mul`, `FPN_AddSat`, `FPN_SubSat`, `FPN_FromInt`, `FPN_Min`, `FPN_Max`, `FPN_Equal`, `FPN_IsZero`, `FPN_Zero` | **ALL VERIFIED** | grep against `FixedPoint/FixedPointN.hpp` |
| `GetReciprocalLUT<F, W>` and `RollingStats_Resync<F, W>` | **NEW (correctly absent)** | plan creates them in 2.A and 2.C respectively |

## Hidden scope detected

1. **Stale `RollingStats<F, 256>` / `<F, 1024>` size comments** (`PortfolioController.hpp:251-252` claim "~393KB" / "~1.5MB") — pre-existing bug, not plan's problem. Plan unrelated.

2. **Phase 2.B's `static_assert` only validates `<64, 128>`** — plan instantiates RollingStats at W=128, 256, 512, 1024 (verified via grep). Static_assert as written is a single specialization. **Hidden scope (~10 min):** parameterize the static_assert via `static_assert(offsetof(RollingStats<F, W>, head) >= 64)` inside the struct (not at namespace scope), or add 4 specializations.

3. **Phase 2.B's `alignas(64)` may force PortfolioController layout change** — RollingStats is embedded inline at line 247. PortfolioController.hpp:245 ("kept at end to avoid polluting hot cache lines") suggests the operator has consciously placed RollingStats at end. `alignas(64)` propagates: it would force the ENTIRE PortfolioController struct to also be 64-byte aligned, which it likely already is. **Hidden scope (~15 min):** verify via static_assert that adding alignas(64) doesn't introduce internal padding inside PortfolioController that pushes the trade_buf or other hot fields.

4. **Multiple FPN_DivNoAssert sites in RollingStats.hpp NOT in Phase 2.A scope** (lines 142, 143, 155, 210, 224, 231, 236) — these are non-LUT-eligible (divisor is variable, not a positive integer in [2,W]), so correctly excluded. But plan should explicitly call this out: "Phase 2.A does NOT replace the divisions at lines 142/143/155/210/224/231/236 because their divisors are non-integer FPN values (vol_sum, vwap, range, denominator, ss_total, safe_total)."

5. **Phase 2.C Step 0 promotes 5 new sums + counter to struct fields** — plan-claimed Phase 2.B reorder in proposal lists `// v5.11.2.C: O(1) running regression sums (added in Phase 2.C)` as a comment-only placeholder. Sequence works (B does layout reorder, C adds fields). But: when C adds the 5 new FPN<F> + uint64_t fields, they must land in the WRITE-HEAVY cluster, not OUTPUTS. Plan implies this but should make it explicit.

## Cold-pickup completeness check

| # | Field | Status | Notes |
|---|-------|--------|-------|
| C.1 | Branch state | **PASS** | Says "stay on `feat/v5.11-optimization`" with rollback tag `pre-v5.11.2` |
| C.2 | Phase order matches deps | **PASS** | A → B → C, with explicit "B helps verify layout invariants for C" rationale |
| C.3 | First concrete move per phase | **PASS** | Each phase has Step 0 with file:line + code shape |
| C.4 | Function/macro names cited | **PASS** | All cited (FPN_DivNoAssert, FPN_Mul, FPN_AddSat, FPN_SubSat, FPN_FromInt, GetReciprocalLUT (new), RollingStats_Resync (new)) |
| C.5 | File:line refs for tests/baselines | **PASS-WITH-NOTE** | Plan cites `tests/controller_test.cpp:10147` (block) and `:10258` (assertion); note that plan also cites `:10251` elsewhere, but that's a column-index line, not the assertion. Cosmetic |
| C.6 | Stale-claim audit | **PASS** | Plan has dedicated "Stale-claim audit" section, all entries verified against HEAD `beacb59` |
| C.7 | Effort vs LOC reconciliation | **YELLOW** | Plan claims "~120-180 LOC delta". Phase 2.C alone touches ~100 LOC (reorder Push body), plus 5 new fields + Resync helper (~30 LOC) + 3 new tests (~40 LOC). Estimate is reasonable but conservative — could overrun |
| C.8 | Source-audit references with paths | **PASS** | `DOCS/LATENCY_OPTIMIZATION_AUDIT.md` Part 2, `DOCS/STRATEGY_AND_CODING_RULES.md` §5/§7 cited |
| C.9 | Predecessor / dependent plans named | **PASS** | All four cross-ref plans exist on disk: master, predecessor, discipline, successor (pending) |
| C.10 | Tag names locked | **PASS** | `pre-v5.11.2`, `v5.11.2.A/B/C`, `v5.11.2` final — all unique, push commands listed |

**Cold-pickup score: 9.5/10** (one minor C.5 inconsistency, one C.7 conservative estimate). Both flagged as fix-during-coding, not blocking.

## Drift audit (8 sub-categories)

| Category | Verdict | Notes |
|---|---|---|
| 1. Feature drift | **DRIFT-RISK** | RollingStats outputs feed Features_PackAll. Phase 2.A ULP differences cascade to feature_matrix bytewise check |
| 2. Label drift | **PASS** | No label change |
| 3. Metric drift | **PASS** | No metric formula in two places |
| 4. Path drift | **PASS** | No path/symlink changes |
| 5. Format drift | **DRIFT-RISK** | New struct fields in Phase 2.C (price_sum, price_sum_y2, price_sum_xy, volume_sum, vol_sum_xy, total_pushes). If `ShardedSnapshotPersist` serializes RollingStats by struct copy, **needs SHARDED_SNAPSHOT_VERSION bump**. Plan does not mention. **Verify before coding** whether snapshots include rolling state at all |
| 6. Threshold drift | **PASS** | 100k resync threshold is single constant in code; no operator-facing cfg |
| 7. Tick-source drift | **PASS** | No change to tick source |
| 8. Build-flag drift | **PASS** | No new build flag dependency |

### Proposed fix for DRIFT-RISK in cat 1+5

**Cat 1 (feature drift):** if Phase 2.A's ULP-difference bench shows non-zero bytewise divergence, document the new replay-determinism baseline in the v5.11.2.A commit message AND add a comment in `controller_test.cpp:10258`-area noting the regenerate event. Add a one-liner to `DOCS/PARITY_LIFECYCLE.md` documenting "v5.11.2.A regenerated baseline due to FPN reciprocal-mul truncation difference vs FPN_DivNoAssert."

**Cat 5 (format drift):** before Phase 2.C, run `grep -n "RollingStats\|rolling" CoreFrameworks/ShardedSnapshotPersist.hpp` to determine whether RollingStats fields are serialized. If yes: bump `SHARDED_SNAPSHOT_VERSION` in same ship as Phase 2.C. If no: document explicitly in plan that "RollingStats not persisted; new fields are session-local."

## Hardening checks

| Check | Verdict | Notes |
|---|---|---|
| Atomic file writes | N/A | No file writes |
| Locale pinning | N/A | No locale-sensitive parsing |
| GUI render-thread blocking | **PASS** | RollingStats reads from GUI are field copies; no I/O |
| Failure telemetry | **PASS** | No failure mode added |
| Resource cleanup | **PASS** | No new resource alloc |
| Cancellation | N/A | No long-running op |
| Cross-platform | **PASS** | Standard C++ + FPN ops |

## Recommendations

### Must fix before coding (P1)

1. **Pre-coding ULP-drift spike for Phase 2.A** (~30 min). Plan already proposes this. Specifically: write a synthetic test loop comparing `FPN_Mul(sum, recip[n])` vs `FPN_DivNoAssert(sum, n_fp)` for n ∈ {2..128} with 1000 random sums. Decision tree:
   - Zero divergence → ship 2.A as-is.
   - Non-zero divergence ≤1 ULP → ship 2.A WITH regenerated baseline + commit-message documentation + DOCS/PARITY_LIFECYCLE.md note.
   - >1 ULP → reconsider; investigate whether higher-precision recip storage helps.

2. **Snapshot serialization audit before Phase 2.C** (~10 min). Run `grep -n "rolling\|RollingStats" CoreFrameworks/ShardedSnapshot*.hpp Backtest/*.hpp` to verify whether any persistence path serializes RollingStats internal fields. If yes → bump `SHARDED_SNAPSHOT_VERSION` + add forward-compat parser handling. If no → document in plan as "session-local, not persisted."

3. **Parameterize Phase 2.B's static_assert across all W instantiations** (~10 min). Current plan only asserts `<64, 128>`. Solution: place the static_assert INSIDE the struct definition so it fires for every template instance (W=128, 256, 512, 1024). Example:
```cpp
template <unsigned F, unsigned W = 128> struct RollingStats {
    static_assert(W > 0 && (W & (W - 1)) == 0, "W must be power of 2");
    // ... fields ...
    // After fields:
    static_assert(/* via friend struct or sizeof check */);
};
```

### Worth fixing during coding (P2)

4. **Explicitly note non-LUT-eligible divisions** in Phase 2.A spec. Lines 142, 143, 155, 210, 224, 231, 236 are NOT in scope (non-integer divisors). Add to plan to prevent future-self confusion.

5. **Phase 2.B layout note for PortfolioController embedding** (~15 min). Verify `alignas(64)` propagation doesn't push hot fields. Add `static_assert(offsetof(PortfolioController<64>, fills_received) <= ..., "...")` or similar.

6. **Phase 2.C new fields land in write-heavy cluster** — plan should make this explicit (currently a comment placeholder in the 2.B reorder). Add a sentence: "Phase 2.C's 5 new running-sum fields + total_pushes counter must be added AFTER the `alignas(64)` boundary established in Phase 2.B, in the write-heavy cluster."

7. **Test placement** (~5 min). Specify the EXTENSIBILITY block name for the 3 new Phase 2.C tests. Suggest: `printf("\n--- EXTENSIBILITY: v5.11.2.C — RollingStats O(1) regression-sums parity ---\n");`

8. **DOCS/CLAUDE_INVARIANTS.md entry for periodic resync** (~10 min). New invariant: "RollingStats O(1) running sums require periodic resync (every 100k pushes) to bound FPN-saturation drift."

### Acceptable risk (don't block)

- Phase 2.A ULP drift, IF the spike shows ≤1 ULP — accept new baseline as the trade-off for ~50-100ns/Push speedup.
- Conservative effort estimate (C.7) — plan may overrun by 30-60 min on Phase 2.C; not a blocker.

## Map-update suggestions

After v5.11.2 ships:
- **CODE_MAP.md regen** — new functions: `GetReciprocalLUT<F,W>`, `RollingStats_Resync<F,W>`, possibly inlined in headers (verify gen_code_map.sh picks them up).
- **INVARIANTS_MAP.md update** — new invariant for periodic resync; new test rows (3) for Phase 2.C tests.
- **DOCS/CHANGELOG.md** — entry per phase tag (v5.11.2.A reciprocal LUT, v5.11.2.B layout, v5.11.2.C O(1) sums + resync) plus final v5.11.2 summary.
- **DOCS/PARITY_LIFECYCLE.md** — IF Phase 2.A regenerates baseline, add a row noting the regeneration event with rationale.

## Verdict: YELLOW

YELLOW — fix the must-fix items above first (~30-50 min):
1. Pre-coding ULP-drift bench for Phase 2.A (decision input)
2. Snapshot serialization audit (gates Phase 2.C version-bump decision)
3. Parameterize Phase 2.B static_assert across W instantiations

Plan is structurally sound (math verified, surface area tight, hot path untouched, cold-pickup 9.5/10). The two BIG risks the operator flagged in the dispatch are real:
- **(1) ULP drift in Phase 2.A** — confirmed; FPN_Mul + FPN_DivNoAssert both truncate but at different precision points; non-zero divergence is essentially guaranteed for any n where 1/n lacks a finite binary representation in F=64 (n=3,5,6,7,9,10,11,...).
- **(2) O(1) sum correctness in Phase 2.C** — verified mathematically by tracing W=4, 5-sample example. Plan's formula matches the O(W) recompute exactly.

The 30-50 min of P1 work derisks both before any code is written.
