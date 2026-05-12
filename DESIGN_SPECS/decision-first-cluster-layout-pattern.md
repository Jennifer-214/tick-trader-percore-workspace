# Decision-first cluster layout pattern (intra-cluster field ordering for access-temporal sequence + cache prefetcher friendliness)

**Established:** 2026-05-12 (codification of an implicit pattern field-validated across 3 codebase surfaces; v5.15.5.B.1 first explicit reference application)
**Status:** ACTIVE
**Cross-references:**
- Parent rule: `cache-layout-discipline-for-hot-side-structs.md` Rule 4 (HOT/WARM/COLD tier clustering)
- Sister: `per-snapshot-cluster-layout-pattern.md` (alignas(64) cluster boundaries; established v5.14.10.0)
- Sister: `latency-vs-cache-decision-framework.md` (cost reference for prefetcher trade-offs)
- FoxML_Trader_v2 CLAUDE.md item 7 (memory hierarchy)
- FoxML_Trader_v2 CLAUDE.md item 11 (SMT siblings + cache discipline)
- FoxML_Trader_v2 CLAUDE.md item 17 (latency tracking)
- FoxML_Trader_v2 CLAUDE.md item 18 (slow-path branch + cycle minimization)
- FoxML_Trader_v2 CLAUDE.md item 28 (latency-vs-cache decision framework)

---

## Problem statement

`cache-layout-discipline-for-hot-side-structs.md` Rule 4 (HOT/WARM/COLD tiering) tells you WHICH fields belong in WHICH cluster (by access frequency), but it's silent on **field order WITHIN each cluster**. Field order within a cluster matters at two scales:

1. **Cache prefetcher behavior.** Intel and AMD CPUs deploy multiple cache prefetchers (L1d stream prefetcher / adjacent-line prefetcher / L2 streamer / per-IP stride prefetcher). These prefetchers ALL favor **forward-sequential cache-line touches**. A struct laid out so the slow-path-cycle access pattern is `line 0 → line 1 → line 2 → line 3 ...` enables the prefetcher to issue prefetches AHEAD of the consumer, hiding cache-miss latency. A struct laid out so access JUMPS BACKWARDS (line 3 first, then line 0) defeats the prefetcher — backward strides are detected less reliably + the prefetcher won't prefetch what's already past.

2. **Decision-first bail-out.** Many per-cycle access patterns begin with a DECISION: "should this work happen at all? what kind of work?" If the data needed to make the decision sits at offset 0 of the struct (first cache line), then cycles where the decision is "skip / no work / lazy rebuild" touch ONLY line 0 before bailing. If decision data is scattered later in the struct, every skip-eligible cycle pays the cost of fetching subsequent lines.

The pattern is implicit in 3 codebase surfaces today (ExecutionCore<F> hot-path, PerCoreSnap bandit-telemetry cluster, ParameterSlot<F> seqlock). None document the principle explicitly. This doc codifies it so future cluster-layout work has a documented rule to follow, not "look at 3 precedents and infer."

---

## Design space explored

### Why not "logical grouping by feature"?

Tempting alternative: order fields by feature/concern (e.g., all bandit fields together, all P&L fields together). Caught in v5.15.5 cache audit as anti-pattern:
- Mixes hot + cold within feature group; doesn't help prefetcher
- Doesn't help decision-first bail-out
- Doesn't align with cycle's access-temporal sequence

REJECTED. Rule 4 already establishes frequency grouping as the parent organizational axis; within-cluster ordering should follow access TEMPORAL SEQUENCE not feature grouping.

### Why not "size grouping" (largest first / smallest first)?

Some style guides recommend sorting struct fields by size (largest first) to minimize padding. Real but secondary concern:
- Size-driven ordering optimizes BYTES (size); access-temporal ordering optimizes CYCLES (cache misses); cycles dominate by 75-100× per `latency-vs-cache-decision-framework.md`
- Explicit `alignas(64)` cluster boundaries + intentional padding within clusters > implicit size-driven sort

Size grouping is an acceptable TIE-BREAKER within access-temporal-equivalent fields, not the primary axis.

### Why not "alphabetical or declaration-order"?

Anti-patterns. Both ignore the cycle's actual access pattern. Caught in audit of `CoreContext<F>` pre-v5.15.5.B which had ad-hoc declaration order accumulated over v4.0.3 → v5.15.5 development. Cycle touched 17-22 distinct cache lines per slow-path body.

### Why not "compile-time auto-reorder via attributes"?

GCC has `-fipa-struct-reorg` (interprocedural struct reorganization) but it's experimental + breaks ABI assumptions. Manual reorder with explicit static_assert(offsetof) locks is the safer + more visible approach.

---

## The pattern (concrete shape)

Within a HOT/WARM/COLD cluster (per Rule 4), order fields by **access-temporal sequence** + **decision-first prioritization**:

### Step 1 — Trace the access pattern

For each consumer function that touches the cluster, list its field accesses in temporal order. Example for `EventLoop_RebuildOneCore` (per-cycle slow-path body):

1. Read `gate_state.flags` (bitmap check: "should this cycle do full rebuild or skip?")
2. Read `strategy_id` (dispatch decision)
3. Read `model_handle` / `ensemble_handle` (resolve which model)
4. Read `slow_state` ptr (deref into rolling stats; lazy-rebuild gate fields)
5. Read+write `regime_state` (Regime_Classify)
6. Read `model_handle` again (Strategy_BuildParameters dispatch)
7. Write `pending_params` (Strategy_BuildParameters result; large block)
8. Write `intended_tp` / `intended_sl` / `intended_qty` / `allocated_balance` (entry intent)
9. Write `halt_reason` / `strategy_halt_reason` (gate decisions)
10. Write `staged_prediction` / `last_confidence` (ML cycle output)
11. Read `pending_params` (seqlock push to ExecutionCore)
12. Write `sp_telemetry.last_tick_us` / `cycles_total` (cycle close)

Then order the struct's HOT cluster fields to match this sequence as closely as possible.

### Step 2 — Decision-first at offset 0

Place fields that drive **early bail-out decisions** at offset 0 (line 0 of HOT cluster):

```cpp
template <unsigned F>
struct alignas(64) CoreContext {
    // ============================================================
    // HOT CLUSTER — decision-first at offset 0
    // ============================================================

    // ---- Decision metadata (line 0; first L1 fetch resolves "do work? what kind?") ----
    SlowPathGateState gate_state;        // bitmap of cached gate predicates
    ExecutionCore<F>* core;              // per-core pointer
    CoreSlowState<F>* slow_state;        // rolling/regime/flow state pointer
    void* model_handle;                   // CoreModelZoo<F>*
    void* ensemble_handle;                // EnsembleModelZoo<F>* (multi-horizon)
    void* strategy_state;                 // strategy-specific state
    uint8_t strategy_id;                  // dispatch enum
    uint8_t resolved_strategy_id;
    uint8_t dirty;
    uint8_t strategy_state_kind;

    // ---- Per-cycle work, forward-sequential ----
    RegimeState<F> regime_state;
    ConfidenceScorer confidence;
    GateParameters<F> pending_params;
    FPN<F> intended_tp;
    FPN<F> intended_sl;
    FPN<F> intended_qty;
    FPN<F> allocated_balance;
    uint8_t halt_reason;
    uint8_t strategy_halt_reason;
    double staged_prediction;
    double active_prediction;
    double last_confidence;
    // ... continues forward through cluster ...

    // ---- WARM cluster boundary ----
    alignas(64) /* per-event accounting starts here */
    // ...
};
```

**Skip-eligible cycles** (lazy_rebuild fires, no full rebuild) touch ONLY line 0 (gate_state bitmap check) + the lazy-rebuild fields in CoreSlowState (hoisted to head per .B.1 Step 4). Subsequent lines never fetched.

**Full-rebuild cycles** touch lines 0, 1, 2, ..., N in forward-sequential order. Cache prefetcher detects forward stride after 2-3 line accesses + issues prefetches for upcoming lines.

### Step 3 — Bail-driven branchless check at offset 0

The decision-first field should be readable with **branchless mask compute** for fastest bail-out:

```cpp
// Slow-path cycle entry — line 0 fetch
SlowPathGateState gs = state->cores[c].gate_state;  // 1 cache line

// Branchless bail check via mask AND (per CLAUDE.md item 18 + 20)
bool full_rebuild_needed =
    BITMAP_IS_SET(gs.flags, MASK_SP_GATE_FORCE_REBUILD) ||
    /* time-since-last + price-delta predicates from lazy_rebuild fields */;

if (!full_rebuild_needed) return;  // bail; subsequent lines not fetched
```

The bail branch IS predictable (lazy-rebuild typically fires or doesn't fire stably over windows of cycles). Branch predictor handles it cleanly. Bail saves ~10 cache misses × 100 ns each = ~1 µs/skip-cycle in cold cache.

### Step 4 — Forward-sequential subsequent fields

After line 0, lay out fields in the SAME ORDER the consumer accesses them. Cache prefetcher detects the forward stride + issues line-N+1 prefetch when line N is loaded.

### Step 5 — Static_assert(offsetof) cluster anchor

Lock the cluster boundary at compile time:

```cpp
static_assert(offsetof(CoreContext<64>, entries_processed) % 64 == 0,
              "WARM cluster anchor MUST be 64-byte aligned");
```

Catches future inadvertent field-insertion that breaks the cluster boundary.

---

## Cache prefetcher behavior — Intel + AMD x86

### Intel x86 prefetchers (Sandy Bridge → Sapphire Rapids; relevant for Tiger Lake dev hardware)

1. **L1d streamer prefetcher (DCU prefetcher):** detects forward-sequential cache-line touches; prefetches the next 1-2 lines into L1d. Triggered after 2-3 sequential line accesses on the same memory page.

2. **Adjacent-line prefetcher:** on any L1d miss, fetches the line immediately following (+64 bytes). Essentially "free" — happens whenever the miss handler runs.

3. **L2 streamer prefetcher:** detects forward strides + prefetches into L2 (further ahead than L1 prefetcher). Handles larger forward strides up to several lines.

4. **IP-based stride prefetcher:** per-instruction-pointer pattern detection; can handle non-unit forward strides (e.g., every 3rd cache line). Less effective than streamer for unit strides; useful for irregular but PER-IP-CONSISTENT patterns.

### AMD Zen prefetchers (Zen 2 → Zen 4)

Similar to Intel:
- L1d stream prefetcher (forward-only)
- L2 stream prefetcher
- L2 stride prefetcher (per-IP)

Backwards stride detection: Both Intel and AMD have some backwards-stride detection, but it's LESS RELIABLE than forward. Empirical observation: forward stride is detected within 2-3 accesses; backwards stride may take 4-5 or never trigger depending on adjacent accesses.

### Pattern implication

| Access pattern | Prefetcher help | Implication for cluster layout |
|---|---|---|
| Forward sequential (line N → N+1 → N+2 → ...) | EXCELLENT — all prefetchers engage | Order fields by access-temporal sequence |
| Backward jump (line 3 → line 0 → line 1 → line 2) | POOR — forward prefetcher doesn't engage; backward stride detection unreliable | Avoid — common anti-pattern in feature-grouped layouts |
| Strided forward (line N → N+2 → N+4) | OK — IP-stride prefetcher detects | Acceptable but slower than unit stride |
| Random / data-dependent | NONE — each access is a miss | Avoid in HOT/WARM clusters |

The "decision-first" + "forward-sequential" combo aligns the cluster's layout with the BEST prefetcher case.

---

## Reference implementations (3 codebase precedents + 1 new application)

### Precedent 1 — `ExecutionCore<F>` hot-path layout (v5.11.1.5)

**Surface:** `CoreFrameworks/ExecutionCore.hpp:50+`

**Decision-first fields at offset 0:**
- `permission` (atomic) — checked FIRST in `ExecutionCore_Tick`; bail if permission off
- `active` / `active_b` bitmap — checked SECOND; bail if no positions to exit
- `bg_fires` — gate output bitmap

**Bail behavior:** if `permission == 0`, hot-path bails after reading line 0. Bail rate is HIGH during paused mode → minimal cache pollution.

**Forward-sequential subsequent fields:** `cached_params` (ParameterSlot read-cached), TP/SL FPN values, exit thresholds, ring-push state.

**Reference: latency-path-discipline.md** "Cross-thread fields → own cache line" rule + this precedent share the alignas(64) discipline AND the decision-first ordering.

### Precedent 2 — `PerCoreSnap` bandit-telemetry cluster (v5.14.10.0)

**Surface:** `DataStream/EngineTUI.hpp:1188+` (first reference application of `per-snapshot-cluster-layout-pattern.md`)

**Decision-first field at cluster offset 0:**
- `ensemble_active` (uint8_t boolean) — IS downstream bandit data meaningful for this core's snapshot?

**Bail behavior:** GUI render code in `MLStatusPanel` checks `pc->ensemble_active == 0` first; skips entire bandit-telemetry cluster render if false. Snapshot publisher always populates the fields (write-only); reader's bail saves the GUI's read-cache misses.

**Forward-sequential subsequent fields:** `ensemble_n_horizons`, `ensemble_weights[5][8]`, `ensemble_pulls[5][8]`, `thompson_*` fields.

### Precedent 3 — `ParameterSlot<F>` seqlock (v5.11.3)

**Surface:** `CoreFrameworks/GateParameters.hpp:50+`

**Decision-first field at offset 0:**
- `sequence` (atomic uint64_t) — even/odd seqnum; odd = write in progress; reader bails to retry on odd or mismatched after-read seqnum

**Bail behavior:** hot-path consumer reads seqnum first; if odd, retry; if even, read FPN data; recheck seqnum after read; if changed, retry. Bail saves the consumer from reading torn data.

**Forward-sequential subsequent fields:** `tp_pct`, `sl_pct`, `qty`, `flags`, exit thresholds.

### New application (.B.1; v5.15.5.B.1) — `CoreContext<F>` HOT cluster

**Surface:** `CoreFrameworks/ControllerEventLoop.hpp:173+` (post-v5.15.5.B.1)

**Decision-first fields at offset 0:**
- `gate_state` (SlowPathGateState bitmap) — bitmap of cached gate predicates; bail if lazy-rebuild predicate fires
- `strategy_id` — dispatch decision (which strategy's _BuildParameters to call)
- `model_handle` / `ensemble_handle` — resolve which model(s) to use

**Bail behavior:** lazy-rebuild gate (post-v5.12.2) skips 30-50% of cycles. Bail after line 0 + CoreSlowState lazy_rebuild fields = ~2 cache lines per skip cycle.

**Forward-sequential subsequent fields:** regime_state → confidence → pending_params → intended_tp/sl/qty → halt_reason → ML state.

### Future candidate applications

The pattern generalizes — any per-cycle struct with a bail decision benefits:
- `OrderManagerState` (.C ship) — fill-event dispatch
- `FlowFeatures<F>` (.D ship) — feature computation gate
- `ConfidenceScorer<F>` (.E ship) — composite confidence skip-when-disabled

`/dod-audit` should flag candidates per the detection criteria below.

---

## Trade-offs + when to apply

### Apply when:
- Cluster has 3+ fields AND has a per-cycle access pattern
- A bail decision exists at cycle entry (e.g., "is this work needed?" / "is this state meaningful?")
- Cache miss cost is non-trivial (slow-path cadence; not boot-only)
- Multiple consumers access the cluster in similar order (not arbitrary)

### Skip when:
- Cluster is COLD-only (boot init, persistence-only, display-only with no bail decision)
- Cluster is tiny (≤ 64B = single cache line; ordering doesn't matter within)
- Multiple consumers access fields in CONFLICTING orders (no consistent forward-sequential pattern; can't optimize for all)
- Cluster is read sequentially via `memcpy` / wire format (bytewise dump; ordering matters for ABI, not cache)

### Cost:
- Per cluster: 30-60 LOC reorder + static_assert(offsetof) cluster anchor
- Cognitive overhead: contributors must understand access-temporal sequence + decision-first axis

### Win:
- Skip-eligible cycles touch fewer cache lines (huge cold-cache win)
- Full-rebuild cycles benefit from prefetcher (warm-cache hides miss latency)
- Static_assert locks intent; future field-insertion catches at compile time
- Pattern composable with Rule 4 frequency clustering + Rule 5 bit-packing + Rule 3 alignas isolation

---

## Lessons / gotchas

### "Decision data" must be SMALL enough to fit at offset 0

If the decision-driving fields take more than 1 cache line, the bail-out savings shrink. Ideal: < 32 bytes of decision data so line 0 has room for adjacent cluster fields.

For `CoreContext` HOT cluster: gate_state (~16B) + handles (4 × 8 = 32B) + 4 × uint8_t enums (4B) = ~52B; tight fit for 64B line.

### Decision branch must be PREDICTABLE

The bail check (`if (skip_eligible) return;`) must have a branch predictor pattern that converges. Common cases:
- Lazy-rebuild fires consistently for stable windows → predictor learns; ~0 misprediction
- Bail predicate flips every cycle → predictor fails; consider branchless mask compute (Rule 8)

Per CLAUDE.md item 18 Pattern 8a (compile-time elision via `template <bool>`): if the bail predicate is COMPILE-TIME-KNOWN (cfg flag), use `if constexpr` so non-bail code is fully elided.

### Forward-sequential isn't always achievable

If two consumer functions access the cluster in DIFFERENT orders (e.g., RebuildOneCore reads regime → pending_params; OnEvent reads core_realized → entries_processed), no single layout serves both. Order to match the HOTTEST consumer (per-cycle > per-event > display). Document the consumer priority in the cluster comment.

### Static_assert(offsetof) requires standard-layout type

C++17 `offsetof` requires standard-layout types. Most pure-data structs qualify. If using inheritance or virtual functions (rare in this codebase — `static_assert(!std::is_polymorphic<T>::value)` per ExecutionCore precedent), offsetof may be UB. Use only on standard-layout structs.

### Sub-struct internal layout matters too

If a HOT cluster field is itself a struct (e.g., `RegimeState<F> regime_state;`), the sub-struct's INTERNAL field order also follows the decision-first principle for IT'S consumer. Apply the pattern recursively to sub-structs accessed per cycle.

### Backwards compatibility under refactor

Reordering struct fields changes `offsetof(...)` values. SAFE if:
- No memcpy / fwrite / SHA-256 / HMAC of the struct (no byte-equivalence path)
- No code uses raw offsets (no `*(char*)&s + 17` tricks)
- Tests don't check sizeof beyond multiple-of-64 invariant

UNSAFE if:
- Persistence format encodes raw struct bytes
- DMA descriptors reference specific offsets
- C ABI consumers expect specific field positions

For `CoreContext`: verified SAFE (ShardedSnapshotPersist is field-by-field; safety greps cleared 2026-05-12). For other struts, verify before applying.

---

## Audit detection (`/dod-audit` integration)

`/dod-audit` should flag MISSED applications by:

- **Symptom 1:** HOT/WARM/COLD-clustered struct with NO `static_assert(offsetof(...))` cluster boundary anchors → missed Rule 5 enforcement
- **Symptom 2:** Struct accessed per slow-path cycle with `if (early_bail_predicate) return;` at function entry, but decision-driving field is NOT at offset 0 of the cluster → missed bail optimization
- **Symptom 3:** Per-cycle consumer function accesses fields in temporal order A → B → C, but struct declaration has fields in order C → A → B → ... → missed forward-sequential pattern
- **Symptom 4:** Per-IP stride prefetcher observable in perf samples for a slow-path consumer function but struct layout is feature-grouped not access-grouped → suboptimal prefetcher engagement

When detected → flag as `MISSED — decision-first-cluster-layout-pattern`. Recommended fix: trace consumer access pattern + reorder to forward-sequential with decision-driving fields at offset 0.

---

## Patterns NOT used here (and why)

### Alphabetical field order

Pure declaration convenience; ignores cycle behavior. REJECTED.

### Largest-first size grouping

Reasonable as tie-breaker WITHIN access-temporal-equivalent fields; not the primary axis. Cache miss > padding cost by 75-100× per `latency-vs-cache-decision-framework.md`. REJECTED as primary.

### Random access via direct offset arithmetic

`base + offset` indexing into struct via raw offsets — defeats type safety + invalidates static_assert(offsetof) locks. REJECTED.

### Compile-time auto-reorder via `-fipa-struct-reorg`

GCC experimental feature; breaks ABI; not safe for cross-binary determinism (different gcc versions reorder differently). REJECTED. Manual reorder + static_assert(offsetof) is the explicit, reliable approach.

### `[[gnu::aligned]]` on individual fields

Per-field alignment forces padding between every field; massive memory waste vs cluster-boundary alignment. REJECTED. Use `alignas(64)` on cluster ANCHOR field only.

---

## Cross-references

- `cache-layout-discipline-for-hot-side-structs.md` Rule 4 (parent rule; HOT/WARM/COLD tier clustering)
- `per-snapshot-cluster-layout-pattern.md` (alignas(64) cluster boundaries; PerCoreSnap precedent)
- `latency-vs-cache-decision-framework.md` (cost reference: cache miss = 75-100× cycle cost)
- `bitmap-flag-api.md` (BITMAP_* primitives for decision-driving bitmap fields)
- `struct-padding-determinism-pattern.md` (separate concern: byte-equivalence contexts)
- `avx512-byte-determinism-pattern.md` (different optimization axis: SIMD vectorization)
- `branchless-math-kernel-pattern.md` (Rule 8 branchless mask-compute for decision predicates)
- FoxML_Trader_v2 `CoreFrameworks/ExecutionCore.hpp` (precedent 1: hot-path layout)
- FoxML_Trader_v2 `DataStream/EngineTUI.hpp:1188+` (precedent 2: PerCoreSnap bandit cluster)
- FoxML_Trader_v2 `CoreFrameworks/GateParameters.hpp:50+` (precedent 3: ParameterSlot seqlock)
- FoxML_Trader_v2 `CoreFrameworks/ControllerEventLoop.hpp:173+` (.B.1 first explicit reference; post-v5.15.5.B.1)
- FoxML_Trader_v2 CLAUDE.md items 7, 11, 17, 18, 28

## Promotion criteria (this doc was promoted)

Pattern field-validated 3× implicitly across distinct codebase surfaces (ExecutionCore hot-path, PerCoreSnap bandit cluster, ParameterSlot seqlock) before explicit codification. Operator framing 2026-05-12: "named pattern style... this stuff needs extensive explanation for how critical it is" — codification triggered when audit (.B pre-coding) surfaced the implicit pattern + 4th explicit application proposed.

Re-evaluate when 5th-6th applications surface (likely .C / .D / .E sibling cache-layout sweeps in v5.15.5 sprint continuation). Update reference table with each new application.
