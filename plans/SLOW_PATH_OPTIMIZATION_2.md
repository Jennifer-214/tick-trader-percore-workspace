# SLOW PATH OPTIMIZATION 2 — analysis + decision framework

**Private** (gitignored via plans/ — workspace-backed).
**Date:** 2026-05-08
**Predecessor:** v5.11 sprint (closed at v5.11.7) hit 92µs p50, 220µs p99
slow path. This doc analyzes paths to sub-8µs (12x further reduction).

---

## TL;DR

Sub-8µs slow path is achievable but requires architectural change.
Two tiers:

1. **Without rearchitecture: ~30-50µs p50 ceiling (2x improvement).**
   AVX-512 + Treelite + FPN reduction + lazy rebuild. ~1-2 week ship.

2. **Sub-8µs requires "streaming features" architecture.**
   Hot path absorbs incremental feature updates; slow path becomes
   "publish-only." ~2-3 weeks. Canonical HFT pattern.

**Whether you SHOULD do either matters more than whether you CAN.**
At current poll_interval=100 ticks + Binance WS tick rate, slow path
cadence is ~1-10 seconds wall time. Reducing slow-path duration
from 92µs to 8µs doesn't change decision frequency — it's bounded
by poll_interval, not slow-path latency. You're using <1% of
available slow-path budget.

Premature optimization. Document the path, ship paper-trade, gather
data, decide based on real bottlenecks.

---

## Current state (post-v5.11)

```
PER-ENGINE SLOW-PATH LATENCY (per-cycle work in engine_arch=per_core_slow)
Engine  Strat   Samples   Min      Avg      p50      p95      p99       Max
0       ML      103       43.7µs   96.0µs   92.6µs   104.7µs  112.9µs   1147.9µs
1       DIP     103       36.7µs   96.5µs   91.9µs   114.9µs  220.5µs   1189.1µs
2       AUTO    104       55.9µs   104.2µs  99.1µs   113.4µs  120.6µs   1153.6µs
3       EMA     103       40.9µs   103.7µs  89.5µs   105.3µs  115.4µs   1189.1µs

PER-ENGINE SLOW-PATH WORK BREAKDOWN (slow-path components)
Engine  Rolling p50  Rolling p99   Rebuild p50   Rebuild p99   Push p50   Push p99   TimeExit  TrailSL  Σ p50
0 (ML)  68.2µs       1119.2µs      15.9µs        36.2µs        194ns      898ns      175ns     229ns    84.7µs
1 (DIP) 55.3µs       1201.8µs      39.5µs        171.0µs       155ns      393ns      202ns     188ns    95.4µs
2 (AUTO)68.2µs       1119.2µs      37.1µs        50.5µs        34ns       181ns      167ns     181ns    105.6µs
3 (EMA) 62.0µs       1201.8µs      39.5µs        54.6µs        35ns       385ns      162ns     194ns    101.9µs
```

**Cost distribution (per-cycle p50):**
- Rolling stats updates: 55-68µs (dominant — RollingStats_Push × 4
  windows × FPN<F=64> arithmetic, plus regime feature compute for
  AUTO/ML cores)
- Parameter rebuild: 16-40µs (ML cores hit 16µs, AUTO/static 37-40µs
  due to adaptive gating regen)
- Push to hot-path seqlock: 34ns-194ns (negligible)
- TimeExit + TrailSL evaluation: 162-229ns each

**Pre-v5.11 baseline:** Slow path was creeping to ~3000µs p99.
Current p99 ~115-220µs = **14-30x improvement** across the v5.11
sprint. Source attribution:
- v5.11.2 (slow-path O(1) regression): big rolling-stats win
- v5.11.6 (allocator eradication): tail latency reduction
- v5.11.7 (Bandit AVX-512): part of the rebuild reduction
- ReciprocalLUT, FPN_BlendOnMask, FPN_FromInt: cumulative micro-wins

---

## Tier 1: ~30-50µs p50 without rearchitecture (~1-2 week ship)

### 1.1 AVX-512 vectorize RollingStats_Push (~4-8x reduction on rolling)

**Current:** 4 rolling windows (long/short/med/ROR), each calls
RollingStats_Push with scalar FPN<F=64> add/subtract/multiply for
mean / variance / slope updates. Each call ~10-20µs in tight loop.

**Optimization:** Vectorize across 4 windows using AVX-512 _mm512
intrinsics. Each window's running-sum + running-sum-of-squares
update is ~6 ops; 4 windows × 6 ops = 24 scalar ops; AVX-512 gather +
fused-multiply-add brings it to ~3-4 vector ops total. ~5-8x speedup.

**Engineering cost:** ~3-4 days. Touches RollingStats_Push hot
loop. Replay-determinism baseline test must pass post-conversion
(bytewise identical to scalar). Pattern: cache-line-align the 4
windows, gather pointers, vectorize ops, scatter-store results.

**Estimated win:** 55-68µs → ~10-15µs on RollingStats. Total
slow-path drops to ~40-50µs p50.

### 1.2 Treelite AOT compile for ML predict (saves ~3µs)

Already documented as deferred v5.11.8. XGBoost C-API call drops
from 1-5µs to 50-200ns. Saves ~3µs of the rebuild cost on ML cores.

**Engineering cost:** ~2-3 days. Treelite integration + stamp body
extension + load path with fallback + parity test.

### 1.3 FPN<F=64> → FPN<F=32> on slow-path-only math (~2x on math ops)

Current FPN<F=64> = 4096 bits; F=32 = 2048 bits. Half the limbs,
~2x faster arithmetic on most ops. Slow-path math (regression
slopes, regime scores, threshold computations) doesn't need full
F=64 precision — F=32 is plenty. Hot path stays at F=64 for
accounting (TP/SL exit prices, position sizes).

**Engineering cost:** ~half-day. Add `using SlowFPN = FPN<32>;` alias.
Convert RollingStats internal state to SlowFPN. Boundary conversions
at the FPN<F=64> → SlowFPN edge are cheap (truncation).

**Catch:** Train-serve parity. SlowFPN math is bytewise-different
from FPN<F=64>. Must update parity tests + retrain models if
features depend on the converted math. Probably hits FEATURE_REGISTRY_HASH.

### 1.4 Lazy parameter rebuild (~70% of cycles skipped)

**Current:** Every slow-path cycle does full parameter regen
(EventLoop_RebuildOneCore). This includes regime classification,
ML predict, gate threshold computation.

**Optimization:** Gate on "have inputs changed enough to potentially
flip parameters?" If RollingStats moments + regime classifier
inputs are within ε of last cycle's, skip rebuild entirely.
Parameters stay at last cycle's values; published seqlock unchanged.

**Engineering cost:** ~1 day. Add "input fingerprint" (cheap hash
of regime classifier inputs) + per-cycle comparison. Threshold
tuning requires paper-test.

**Estimated win:** 70% of cycles skip rebuild → effective rebuild
cost drops from 16-40µs to 5-12µs. Big win for AUTO/static cores.

**Catch:** Risk of staleness if threshold is too lax. Conservative:
ε such that ~10% of "skipped" cycles would have produced
identical-bytewise output anyway = pure win, no behavioral change.

### Combined Tier-1 ceiling: ~30-50µs p50

| Component | Current p50 | Tier 1 p50 | Source |
|---|---|---|---|
| Rolling stats | 55-68µs | 10-15µs | AVX-512 |
| Rebuild | 16-40µs | 5-12µs (lazy + Treelite) | Lazy + Treelite |
| Other | ~5-10µs | ~5-10µs | unchanged |
| **Σ p50** | **84.7-105.6µs** | **~25-40µs** | |

Realistic Tier-1 ceiling: **~30-50µs p50, ~60-80µs p99.**
~2x improvement. Big ship: ~1-2 weeks.

---

## Tier 2: Sub-8µs requires "streaming features" architecture

### The architectural shift

**Current model:** "Every poll_interval ticks, do batch work."
Slow path is a periodic event that does big O(N) work over the
window. N = window size × number of windows × per-feature compute.

**Streaming model:** "Every tick, increment incrementally."
- Hot path adds ~50-100ns per tick for one rolling-stat increment
  (O(1) update formula, not full recompute)
- Slow path becomes "publish current parameters" — pure seqlock
  write, sub-microsecond
- ML predict still runs at slower cadence (every 100-1000 ticks)
  because XGBoost C-API cost is unavoidable; but it runs OFF the
  per-tick streaming path

### Why this works

Every rolling statistic has an O(1) incremental update formula:

| Stat | O(N) batch | O(1) incremental |
|---|---|---|
| Mean | `sum/N` over window | `mean += (new - old) / N` (Welford) |
| Variance | `Σ(x-μ)²/N` over window | Welford online algorithm |
| Slope | linear regression over window | Sherman-Morrison rank-1 update |
| EMA | weighted sum recompute | `ema = α×new + (1-α)×ema_prev` |
| Z-score | (current - mean) / stddev | `(current - rolling_mean) / rolling_stddev` (uses incremental mean+var) |

ROR_regressor, FlowFeatures EWMA, all of these are
streaming-friendly. The current batch implementation throws away
the locality advantage.

### Hot-path budget impact

Hot path currently 30-35ns p50 (after rdtsc subtract). Adding ~50-100ns
per tick for streaming feature increments brings hot path to
~80-130ns p50. Still sub-microsecond, still per-spec ≤500ns p99 with
margin.

**Trade:** Hot path widens 2-4x. Slow path drops 12x. Net: hot path
budget consumed (was wasted), slow path budget freed (was wasted).
Same total compute, redistributed.

### Why per-tick freshness matters (or doesn't)

For your current deployment:
- Tick rate ~10-100 ticks/sec sustained, bursty to 1000
- poll_interval=100 → slow path runs every ~1-10 sec wall time
- Decisions update every ~1-10 sec → not actually per-tick

Streaming gives you per-tick parameter freshness. Whether that
buys alpha depends on:
- Are there market events that resolve in <1 second AND your
  strategy could react to them? At Binance crypto tick rate, yes —
  microbursts on news, MM flicker, large taker prints. But your
  current strategy gates on multi-second windows, so per-tick
  freshness wouldn't change behavior.
- Would per-tick ML inference resolve sub-second signals? Yes,
  but ML predict cost (XGBoost C-API ~1-5µs per row) would
  saturate per-tick. Treelite (50-200ns) makes per-tick ML viable.

### Engineering cost: ~2-3 weeks

**Phase 1 (~1 week):** RollingStats refactor to incremental.
Each window gets a per-tick update fn that returns current
moments without recomputing from scratch. Parity tests must pass
bytewise — tricky because incremental floating-point is order-
dependent. Solve via fixed integer arithmetic in FPN domain.

**Phase 2 (~3-4 days):** Features_PackAll refactor to O(1) per-tick.
Each FOREACH_FEATURE compute fn becomes streaming-update + read.
FEATURE_REGISTRY_HASH semantics preserved; fingerprint stays stable.

**Phase 3 (~3-4 days):** Slow path becomes publish-only. Remove
batch rolling-stat computation. Add cache invalidation for ML
predict + parameter regen only when input fingerprint changes.

**Phase 4 (~3 days):** Train-serve parity verification. Replay-
determinism baseline must pass. Snapshot tests for incremental
formulas. Backtest the streaming engine against the baseline
batch engine on identical input — bytewise-equivalent feature
output required.

**Phase 5 (~2 days):** Hot path benchmarks + AVX-512 streaming
math where it pays off. Confirm hot path stays under 500ns p99.

### Combined Tier-2 ceiling: ~5-8µs p50 slow path

| Component | Tier 1 p50 | Tier 2 p50 | Source |
|---|---|---|---|
| Rolling stats | 10-15µs | <100ns (per-tick increments live in hot path) | Streaming |
| Rebuild | 5-12µs | ~3-5µs (Treelite + lazy gating) | Lazy + Treelite + ML cadence |
| Push | <1µs | <1µs | unchanged |
| **Σ p50** | **~25-40µs** | **~5-8µs** | |

Realistic Tier-2 ceiling: **~5-8µs p50, ~15-25µs p99.**
~12-18x improvement total. Big ship: ~2-3 weeks plus full parity
re-verification.

---

## Decision framework — when to invest in each tier

### Tier 0 (do nothing — current state)
- Slow path 92µs p50, 220µs p99
- Wall time per slow-path cycle ~1-10 sec at current tick rate
- Slow-path budget utilization: <1% of available
- **You are here. This is fine for paper trading + small-cap live.**

### Tier 1 (~2x improvement)
**Invest when:**
- Profiling shows slow path is THE bottleneck on parameter freshness
- You drop poll_interval below 50 (more frequent slow-path cycles)
- ML core slow-path P99 starts exceeding 1ms regularly under burst
- You want to free CPU budget for adding features (more rolling
  windows, deeper regime classification)

**Don't invest when:**
- Paper trading shows current cadence is already the bottleneck
  on RESPONSE TIME, not parameter freshness (= different problem)
- Profiling shows rolling stats aren't the dominant cost (might
  not be after Tier 1 lands; check before Tier 2)

### Tier 2 (~12-18x improvement, streaming refactor)
**Invest when:**
- You're going colo. Sub-millisecond decision windows make slow-
  path latency itself load-bearing.
- You want per-tick decisions (poll_interval=1) — only feasible
  with streaming features.
- You're trading instruments where microsecond-scale market
  microstructure matters (HFT desks, sub-second arbitrage).
- Trading thesis genuinely requires microbursts response (you've
  paper-tested showing alpha you can't capture without it).

**Don't invest when:**
- Current strategy gates on multi-second windows. Per-tick
  freshness doesn't enable the strategy to do anything different.
- You haven't ruled out simpler explanations for "slow path
  feels slow" (Tier 1 first).
- You don't have paper-trading data showing the strategy actually
  needs sub-second response.

### Cross-cutting: never do without paper data

Both tiers are AT LEAST 1 week of focused engineering with parity
re-verification. Doing them without empirical justification (paper
trading shows the bottleneck) is premature optimization on a path
that's already fast.

The current state is a finishing line, not a starting line.
Don't optimize past where it matters.

---

## What's NOT addressed by either tier

**XGBoost predict cost itself.** Treelite (50-200ns) is the
software ceiling. FPGA gets to 5-20ns but requires hardware. For
your deployment, Treelite is the right next step on inference;
neither tier moves it further.

**OS jitter (the p99-Max gap).** Current p99 ~115µs, max ~1147µs
= 10x ratio. That's OS scheduling preemption + CPU frequency
transitions + cache cold misses, not slow-path code. Mitigations:
isolcpus + SCHED_FIFO + cpufreq performance governor + huge
pages. None of these are code changes — they're deployment
config (covered in `DOCS/OPERATOR_DEPLOYMENT.md`).

**Hot path budget consumed by streaming.** Tier 2 trades slow
path for hot path. If you ALSO want hot path < 100ns p99 at
that point, you'd need to push more work to "fast slow path"
(an in-between tier between hot and slow). That's a 4-week+
research project; no clear path that doesn't reintroduce batch
work somewhere.

---

## Cross-references

- v5.11 sprint master plan: `plans/2026-05-07-MASTER-v5.11-optimization-sprint.md`
- v5.11.8 Treelite deferred: `plans/2026-05-07-deferred-items.md` "v5.11.8 — ML AOT compile"
- AVX-512 background: `DOCS/v5.11-OPTIMIZATION-REFERENCE.md`
- Audit's Part 2+5 (slow path): `DOCS/LATENCY_OPTIMIZATION_AUDIT.md`
- Hot path discipline rules: `plans/2026-05-06-latency-path-discipline.md`
- Per-tick refresh strategies: `DOCS/v5.11-hft-suggestions.md` (if
  exists in workspace)

---

## Maintenance

When Tier 1 starts: copy this analysis into a dated plan
(`plans/<date>-tier1-slow-path.md`) with concrete tasks. Mark this
doc's Tier 1 section `**ACTIVE: see <plan>**`. Update post-ship
with actual measured results vs predicted.

When Tier 2 trigger fires: same pattern. Probably preceded by a
focused profiling pass to confirm Tier 1's gains were absorbed
and slow path is again the bottleneck.

When deciding to permanently kill a tier: append `KILLED` section
with reason. Don't delete.
