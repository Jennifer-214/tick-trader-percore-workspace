# DESIGN_PHILOSOPHY.md

**Workspace-private.** The narrative + WHY companion to `CLAUDE.md`'s
operational orientation. Read this when:
- Cold-pickup of an unfamiliar surface (which family of principles applies?)
- Designing a non-trivial change (which discipline tier am I choosing into?)
- New contributor onboarding (where does the codebase's mental model live?)
- Making a design trade-off (which family's rules dominate?)

`CLAUDE.md` (always-loaded) gives the orientation + hard invariants;
`DESIGN_SPECS/README.md` (catalog) gives the pattern reference;
`DOCS/RECURRING_BUG_PATTERNS.md` gives the failure-mode catalog.
**This doc gives the WHY** — the mental model that makes the patterns
make sense.

---

## How to read this doc

Every principle is tagged with a discipline tier:

| Tier | Meaning | Override path |
|---|---|---|
| **HARD** | NEVER break. Architectural invariant that defines what this codebase IS. | None — if you'd break it, you're building a different codebase |
| **STRONG** | Apply unless specifically justified. Default for the surface. | Justify in code comments + commit message; document the override in TECH_DEBT.md or CLAUDE.local.md |
| **SOFT** | Do when reasonable. Improves quality but doesn't redefine the architecture. | Drop when a specific reason makes it costly; no formal justification needed |
| **PROCESS** | Gate or decision framework. Tells you when to apply other principles. | The framework IS the override mechanism |

Each section ends with **Cross-references** linking to canonical sources
(CLAUDE.md item N, DESIGN_SPECS path, RECURRING_BUG_PATTERNS class).
Those are the source-of-truth; this doc is the synthesis.

---

## 1. What this codebase optimizes for (the foundational frame)

A single-symbol HFT trading engine that:
- Hits sub-microsecond p99 on the hot path (40-400ns for `ExecutionCore_Tick`)
- Gives DETERMINISTIC outputs across runs, binaries, and locales
- Surfaces operational visibility (failure modes, drift, observability)
- Stays MAINTAINABLE under feature pressure (drift classes structurally extinct)
- Trades operator-edit ergonomics off branchlessly (settings tab + tooltips matter)

Everything in this doc is in service of those four. When two principles
conflict, the priority order is:

1. **Latency** (hot path budget — never give it up)
2. **Determinism** (cross-run, cross-binary, cross-locale; load-bearing for replay + train/serve parity)
3. **Maintainability** (structural fix preferred when a bug class can recur)
4. **Operator UX** (comment-preserving cfg writes, tooltip preservation, no surprising behavior changes)

If you're trading off principles, name which one wins + why.

### The cost framework (CLAUDE.md item 28; the lens for all decisions)

At ~3 GHz x86 with AVX-512:

| Operation | Cost | Multiplier vs cycle |
|---|---|---|
| 1 CPU cycle | ~0.3 ns | 1× |
| L1 hit | ~1 ns | ~3× |
| L2 hit | ~4 ns | ~13× |
| L3 hit | ~13 ns | ~43× |
| **DRAM (L1 miss; cold cache)** | **~100 ns** | **~300×** |
| Branch mispredict | ~3-5 ns | ~10-15× |
| Locked atomic / mutex acquire | ~20-50 ns + scheduling | ~100×+ |
| Syscall | ~200-500 ns | ~700×+ |
| Page fault | ~10-100 μs | ~30,000×+ |
| Mutex contention (kernel wait) | up to ms | ~3,000,000×+ |

Decision rules that fall out of this:
- **Approach A (+N cycles, -M cache misses) beats Approach B (-N cycles, +M misses) when M > N/300.** For N=10 cycles, 1 saved miss = ~30× net win.
- **Branchless A (+N cycles) beats branchy B (1 branch, M% mispredict) when M > N/16.** For data-dependent branches commonly mispredicting 30-50%, branchless usually wins.
- **NEVER syscall on hot path.** A single syscall costs more than the full per-tick budget.
- **NEVER allow page faults on critical pages.** Lock memory at boot via `mlockall(MCL_CURRENT | MCL_FUTURE)`.
- **NEVER acquire mutexes on hot/slow path.** The unbounded tail under contention nukes any latency budget.

**Cross-references:** CLAUDE.md item 28 (cycles vs cache), `DESIGN_SPECS/latency-vs-cache-decision-framework.md`.

---

## 1.5 Framework discipline (the meta-principle behind structural fixes)

This codebase deliberately invests upfront complexity in FRAMEWORKS — X-macro
registries, AUTOPOPULATE companions, type-trait dispatch (`tt::` namespace),
derived-filter macros, sidecar override tables, meta-registries — when the
trade-off math favors framework over ad-hoc:

1. **Pattern recurrence is foreseeable** (≥2 future applications projected)
2. **Bug class can recur** (sites can drift apart over time)
3. **Framework cost ≤ projected savings across N applications** (upfront LOC + maintenance < per-instance ad-hoc cost × N)

The trade-off: framework code is HARDER TO READ at first encounter than
ad-hoc per-instance code. The PAYOFF is that future additions become
1-row mechanical changes; the framework's API encodes the discipline so
contributors can't drift from it.

### Why this matters in this codebase specifically

Recurring drift classes have cost 1-3h per occurrence on average, and we've
seen 3-4× recurrence on classes that "weren't going to come back" — Class 14
plan-API-drift (5× recurrence), Class 18 mirror-incomplete (4× recurrence
before `EnsembleModelZoo_PostLoadSetup` structurally closed it), Class 21
parallel descriptors (closed structurally at v5.15.5.F.4 via single
`CfgFieldDescriptor` + `lives_in_struct` discriminator). Each framework that
closes a bug class structurally saves multiples of its upfront cost.

### Complexity budget calculation

Before investing in a framework, compute the breakeven:
- **Upfront cost:** framework code LOC + DESIGN_SPEC drafting + audit/test infrastructure
- **Per-application savings:** avoided per-instance LOC × projected N applications
- **Breakeven N ≈ upfront cost / per-app savings**

For the v5.15.5.F.4 cfg-registry work: upfront ~1500 LOC; per-app savings
50-200 LOC × ~20 known future applications (cfg fields + derived filters +
drift overrides + new registries) = breakeven within the v5.15.6 sprint;
lifetime payoff 4-10×.

### When NOT to invest in a framework

- Single known application + no clear recurrence signal (one-shot bug fix)
- Pattern variance too high (no shared shape to extract)
- Framework cost ≥ projected savings × N (negative ROI)
- Premature: less than 3 codebase applications + no DESIGN_SPEC yet
  (per `pattern-codification-lifecycle.md` Stage 2 requirement)

### Composition reduces total complexity

Multiple frameworks often COMPOSE — e.g., the v5.15.5.F.4d ship composes:
- Universal cfg registry (`FOREACH_CFG_FIELD`)
- `tt::` type-trait dispatch (parse / save / render trio)
- Derived-filter framework (`FOREACH_DERIVED_FILTER` over CFG_FIELD)
- Sidecar override pattern (over CFG_FIELD)
- Meta-registry (`FOREACH_REGISTRY` managing all the above)
- X-macro struct generation (Cfg struct fields from `FOREACH_CFG_FIELD`)

The composition is intentional. Each framework handles ONE concern;
together they extinguish 5 bug classes (Class 14, 18, 19, 21, 23). Without
the framework discipline, each concern would be solved independently with
parallel infrastructure — more total complexity, less coverage.

### Cross-references

- § 7 Structural-fix family — the bug-class-recurrence motivation
- § 11 Process discipline — "don't measure structural work by LOC"
- `DESIGN_SPECS/pattern-codification-lifecycle.md` — the 7-stage codification process
- `DESIGN_SPECS/structural-fix-preferred-decision-framework.md` — direct-patch vs structural-fix decision
- CLAUDE.md item 19 — structural fix preferred (codified principle)
- CLAUDE.md item 31 — framework-driven extensibility (codifies THIS section)

---

## 2. Hard invariants (NEVER break)

These define what this codebase IS. Breaking any of them = building a
different codebase.

| # | Rule | Tier | Source |
|---|---|---|---|
| H1 | No `malloc` / `new` / `std::vector` / `std::string` on hot/slow/drainer/parser paths | HARD | STRATEGY_AND_CODING_RULES Rule 1 |
| H2 | No `virtual` functions / `std::function` / `std::shared_ptr` anywhere | HARD | STRATEGY_AND_CODING_RULES Rule 2 |
| H3 | No `std::mutex` / `condition_variable` / `sleep_for` / `pthread_rwlock` anywhere | HARD | STRATEGY_AND_CODING_RULES Rule 3 |
| H4 | `FPN<F=64>` for accounting math; NEVER `float`/`double` on accounting paths (display-only OK) | HARD | CLAUDE.md item 4 (per-core data plane); STRATEGY_AND_CODING_RULES |
| H5 | No `atof` / `strstr` / scalar JSON in parser inner loops; use `simdjson` / `fast_float` / `parse_double_fast` | HARD | STRATEGY_AND_CODING_RULES Rule 6 |
| H6 | Cross-thread fields get `alignas(64)` to isolate cache lines; no false sharing | HARD | STRATEGY_AND_CODING_RULES Rule 7; CLAUDE.md item 12 |
| H7 | Hot path is BRANCHLESS for data-dependent dispatch (mask compute, cmov; per Rule 8 of latency-path-discipline) | HARD | latency-path-discipline.md Rule 8 |
| H8 | Hot path p99 ≤500ns; slow path p99 ≤100μs (regression = ship blocker) | HARD | CLAUDE.md item 17 |
| H9 | Wire-format byte preservation for HMAC-signed bodies (stamps, snapshots, RunHistory); locale pinning at emit | HARD | DESIGN_SPECS/wire-format-byte-preservation-discipline.md |
| H10 | AVX-512 SIMD kernels MUST have a scalar fallback producing BYTEWISE IDENTICAL output | HARD | CLAUDE.md item 25; DESIGN_SPECS/avx512-byte-determinism-pattern.md |
| H11 | Math kernels on slow/hot path are CONSTANT-ITER + branchless within the inner reduction | HARD | CLAUDE.md item 26; DESIGN_SPECS/branchless-math-kernel-pattern.md |
| H12 | Structs used in byte-equivalence contexts (memcmp / SHA-256 / wire format) have EXPLICIT zero-init padding fields | HARD | CLAUDE.md item 27; DESIGN_SPECS/struct-padding-determinism-pattern.md |
| H13 | Type-erased `*reinterpret_cast<T*>((char*)cfg + offset) = v` style dispatch is FORBIDDEN — use `tt::<verb>_field<T>` with T deduced (Class 23 3-barrier fix) | HARD | CLAUDE.md item 23; DESIGN_SPECS/type-trait-dispatch-via-tt-namespace.md; RECURRING_BUG_PATTERNS Class 23 |

**Pending codification at v5.15.5.F.4d ship** (DRAFT slots reserved here; concrete wording locks when shipped):

| # | Rule | Tier | Source |
|---|---|---|---|
| H14 | Every X-macro registry in the codebase MUST have a row in `FOREACH_REGISTRY` (CI-checked). Adding a new registry without registering it FAILS the build. | HARD (pending .F.4d) | DESIGN_SPECS/meta-registry-pattern-for-codebase-registry-discipline.md; CLAUDE.md item 31 |
| H15 | Every metadata bit on `FOREACH_CFG_FIELD` MUST have either (a) a corresponding derived filter declared in `FOREACH_DERIVED_FILTER` OR (b) documented "no-derived-filter" exemption with rationale (CI cross-check enforces). | HARD (pending .F.4d) | DESIGN_SPECS/metadata-bit-driven-derived-filter-framework.md |
| H16 | Cfg struct field declarations MUST come from `FOREACH_CFG_FIELD` via X-macro generation; manual cfg field declarations FORBIDDEN. Runtime/derived state stays manual but is documented in `MANUAL_FIELDS_INVENTORY.md` with rationale. | HARD (pending .F.4d) | DESIGN_SPECS/universal-cfg-field-registry-pattern.md § Reverse-drift |
| H17 | Custom-semantics overrides on auto-flowed registries MUST use the sidecar override pattern; parallel wide-variant registries FORBIDDEN over the same parent registry. (Promoted from STRONG to HARD at second cohort application.) | STRONG → HARD (pending .F.4d) | DESIGN_SPECS/sidecar-override-pattern-for-registry-auto-flows.md |
| H18 | Registries with LEVEL > 0 MUST declare PARENT in `FOREACH_REGISTRY` tuple; PARENT must exist in `FOREACH_REGISTRY` or equal ROOT (CI-checked). | HARD (pending .F.4d) | DESIGN_SPECS/meta-registry-pattern-for-codebase-registry-discipline.md |

These are the floor. Everything below builds on them.

---

## 3. Data-oriented design family

**WHY this family exists.** The hot path's per-tick budget (≤500ns) is a
tiny fraction of a single DRAM round-trip (~100ns). The hot path can
afford a handful of cache hits + some L2 fetches; it CANNOT afford any
DRAM misses. So everything the hot path touches per tick must already
be in L1/L2. This drives every memory layout decision.

The slow path budget (≤100μs) is looser but compounds tightly under
load. Same discipline, slightly relaxed (predictable branches OK,
larger working sets OK, but no syscalls / no allocations / no mutex).

### Principles in this family

**STRONG: Bitmap-pack flags when ≥3 booleans coexist in a struct.**
- Memory: 16 flags in 2 bytes vs 16 bytes byte-per-flag
- Atomic multi-flag updates: 1 instruction (`__atomic_fetch_or`) vs N stores
- Branchless multi-flag check: 1 cycle (mask AND) vs N branches
- Cache: flag-set for entire core fits one word
- Use `BITMAP_*` macros from `MemHeaders/BitmapMacros.hpp` (CLAUDE.md item 20)
- Per-record bit-packing (one bit per record across many records) is the EXCEPTION — usually loses to per-record cache locality

**STRONG: Bit-pack small-state fields (1-3 bits each) into a single byte/word — NOT adjacent `uint8_t` fields.**
- Anti-pattern: `struct { uint8_t severity; uint8_t category; uint8_t mode; uint8_t _pad; }` — wastes 3 bytes; loses cache-line packing efficiency; later widening (uint8 → uint16) is schema bend
- Pattern: pack states as bits in a single `uint8_t` / `uint16_t` with named bit positions + branchless accessor helpers (per `bitmap-flag-api.md`)
- Apply DURING struct design — retrofitting later is schema bend (consumer macros need updates)
- For ≥4 distinct values per field: use multi-bit slots per `multi-bit-state-encoding-pattern.md` (CLAUDE.md item 30)
- Detection: any new struct with ≥2 adjacent `uint8_t state_<N>` fields where each represents an enum of ≤4 values → consolidation candidate. `/dod-audit` Stage 6 detection signature.
- Canonical applications: `DriftOverride` flags + `RegistryRosterEntry.flags` + `ManualFieldInventoryEntry.kind` (all v5.15.5.F.4d ship)

**STRONG: Cluster fields by access pattern, not declaration convention.**
- Hot READS go in line 0 (first cache line of struct)
- Hot WRITES go in their own cluster (avoid invalidating reads)
- Cross-thread fields (atomic flags, snapshot pointers) get `alignas(64)` on their OWN line
- Cold init-time fields go in the cold cluster (last lines of struct)
- See `DESIGN_SPECS/cache-layout-discipline-for-hot-side-structs.md` + `decision-first-cluster-layout-pattern.md`

**STRONG: Branchless mask compute for data-dependent dispatch on hot path.**
- Pattern: `result = (cond_mask & if_true_value) | (~cond_mask & if_false_value)`
- See latency-path-discipline.md Rule 8 + CLAUDE.md item 18
- Predictable branches (cfg flags set at boot) can stay branchy — branch predictor handles them at ~0ns

**STRONG: Use `__builtin_expect` for predicted-rare branches; `__attribute__((cold))` for cold helpers.**
- Pattern: `if (__builtin_expect(can_enter | can_exit, 0)) { /* event push */ }` — predictor learns "not taken" within ~1k ticks; steady-state cost ~0ns
- See latency-path-discipline.md Rule 4

**SOFT: Use compile-time elision (`template <bool> + if constexpr`) for default-off features.**
- Disabled state compiles to ZERO instructions
- Used for `LAT_ENABLED`, debug instrumentation, etc.
- See CLAUDE.md item 18(a) + cfg-flag-eligibility-criteria.md (when to use template-elision vs cfg-flag bitmap)

**SOFT: AVX-512-friendly layouts** — if a state array is 8×64-bit (e.g., bandit weights), it fits one __m512d register. Plan accordingly. See CLAUDE.md item 25 + STRATEGY_AND_CODING_RULES Rule 5.

### What NOT to do

- ❌ Per-record bit-packing across millions of records (cache locality + indirection cost > memory savings)
- ❌ Mutex protection of bitmap reads (bitmap reads are inherently lock-free)
- ❌ Bitmap field without overflow guard — `static_assert(FOREACH_X_COUNT_VALUE <= sizeof(type) * 8)` is mandatory (Class 20; bitmap-overflow-protection-discipline.md)

**Cross-references:** CLAUDE.md items 1, 12, 20, 28; DESIGN_SPECS/bitmap-flag-api.md, cache-layout-discipline-for-hot-side-structs.md, decision-first-cluster-layout-pattern.md, per-snapshot-cluster-layout-pattern.md, multi-bit-state-encoding-pattern.md, latency-vs-cache-decision-framework.md; RECURRING_BUG_PATTERNS Class 20 (bitmap overflow).

---

## 4. Latency cost framework family

**WHY.** Hot path is per-tick (~1μs intervals); slow path is per-cycle
(~100 ticks × 1μs ≈ 100μs intervals). Drainer is per-fill. Each path
has a budget that's a few orders of magnitude tighter than naive code
would produce. Decisions about WHAT TO ADD to a path must be reasoned
against the path's budget.

### Principles in this family

**HARD: Hot path lat budget ≤500ns p99; slow path ≤100μs p99.**
- `tools/calls_graph_diff.sh` + bench gate verify before merge
- Replay-determinism test at `tests/controller_test.cpp:10251` is bytewise lock

**STRONG: Latency-additions to hot/slow/drainer paths get tracked.**
- Document in `DOCS/HOT_PATH_CHANGELOG.md` with cost estimate (ns) + branchless analysis + cache impact + FUTURE optimization note
- Run `/latency-track` skill after sprints touching audited surfaces
- See CLAUDE.md item 17

**STRONG: Slow-path additions follow specific reduction patterns.**
- Default-OFF safety gates → compile-time elision via `template <bool ENABLED> + if constexpr` (zero cost when disabled)
- ALWAYS-ON gates → branchless mask compute on cached state
- Runtime-toggleable + load-bearing → cache an "any_gate_enabled" mask at slow-path entry; later checks are AND-mask compares
- Avoid sprinkling cfg-flag checks through deep functions — hoist to slow-path top + pass a small struct of resolved predicates
- Mask compute > switch on enum: for "any of these states?" queries, single mask AND beats switch (branchless, predictable, single uop)
- See CLAUDE.md item 18

**STRONG: Reuse-audit before adding new code.**
- Before writing a new function or duplicating state access, scan the codebase + adjacent in-flight plans for: existing functions with overlapping responsibility, atomic loads / `clock_gettime` / cfg accesses that could be SHARED across consumers in the same slow-path cycle, state fields that could be reused, conversion paths (FPN ↔ double, system_clock ↔ rdtsc) that already exist
- Hot-path/producer paths get branchless mask compute on shared data; slow-path can use predictable branches with shared reads
- Run `/merge-scan` periodically; ship-time check in `/readiness` (item 18) catches per-plan misses
- See CLAUDE.md item 16

**SOFT: AOT-compile ML inference when latency tightens.** XGBoost C API is ~1-5μs per inference; Treelite-style transpilation can drop this to <100ns with AVX-512 parallel tree evaluation. Path documented in LATENCY_OPTIMIZATION_AUDIT.md Part 4.3.

### What NOT to do

- ❌ Adding latency-impacting code without a HOT_PATH_CHANGELOG entry
- ❌ Sleeping on hot/slow path (any `sleep_for` is a syscall + scheduler dependency)
- ❌ Synchronous I/O on drainer thread (cascading stalls; OrderEventLog uses async logger thread)

**Cross-references:** CLAUDE.md items 16, 17, 18, 28; STRATEGY_AND_CODING_RULES Rules 1-9; LATENCY_OPTIMIZATION_AUDIT.md (13 parts; private); plans/_cross-cutting/2026-05-06-latency-path-discipline.md (8 rules + anti-pattern history).

---

## 5. Determinism family

**WHY.** This codebase has THREE determinism contracts:
1. **Replay-determinism** — same input ticks → same output trades (operator-side audit + bug investigation)
2. **Train-serve parity** — features computed at training time = features at inference time (model accuracy depends on it)
3. **Cross-binary determinism** — paper-trade run + live-trade run with same cfg + same ticks → bytewise-identical decisions (HMAC chains for stamp verification)

Breaking ANY of these fails silently and accumulates over time. The
discipline that prevents this is COMPREHENSIVE — every byte that
participates in a deterministic computation must come from a
deterministic source.

### Principles in this family

**HARD: FPN<F=64> for accounting math.** Floating-point arithmetic is non-associative + locale-dependent + has subnormals. Fixed-point is integer math + bytewise-deterministic across compilers + binaries.

**HARD: Wire-format byte preservation for HMAC-signed bodies.**
- Locale pinning at emit (`uselocale(newlocale(LC_NUMERIC_MASK, "C", 0))`) — per-thread, lock-free
- Per-entry format strings locked in registry's `fmt` column (registry-driven emit ALWAYS uses this format)
- Layer 5b canonical body snapshot hash test prevents accidental row reorder
- Surface G `has_*` forward-compat flags preserve legacy stamps without `MODEL_FORMAT_VERSION` bumps
- Round-trip HMAC test against committed v(N-1) stamp fixture
- See `wire-format-byte-preservation-discipline.md`

**HARD: Parity-tested-by-construction.** Every train→serve handoff surface (features, labels, scaler, cfg, stamp body, threading, build flags) gains protection by adding a registry/binding/snapshot, NOT ad-hoc tests.
- Pattern: `FEATURE_REGISTRY_HASH` + scaler `feature_registry_hash` + stamp body `has_*` forward-compat flags + snapshot tests for compute-fn bodies
- Prefer Surface G stamp body extension (`has_<field>` flag with `model_format_version` UNCHANGED) over `MODEL_FORMAT_VERSION` bumps
- Run `/parity-check` before declaring an ML-side sprint complete
- See CLAUDE.md item 15; DOCS/PARITY_LIFECYCLE.md, PARITY_VERIFICATION_CHECKLIST.md

**HARD: NaN-free feature pack.** `Features_PackAll` is the SINGLE chokepoint where every feature value is validated. Two-layer guard: `FPN_IsValidFinite` (catches FPN saturation past 1e15) + IEEE-754 `isnan/isinf` post float-cast. Returns `-1` sentinel on failure; caller skips prediction cycle + increments `nan_feature_events_total`. Adding a new feature does NOT add a separate validation site — pack-time is the load-bearing surface; downstream code trusts the pack output.

**HARD: AVX-512 SIMD kernels have scalar fallback producing BYTEWISE IDENTICAL output.**
- Every AVX-512 kernel has `#if defined(__AVX512F__)` else baseline
- 7-8 rules per `avx512-byte-determinism-pattern.md` + SHA-256 lock test template
- Cross-binary replay determinism is load-bearing — paper-trade audits + HMAC chains + cache-warm replay tests all break under 1-ULP divergence
- See CLAUDE.md item 25

**HARD: Math kernels on slow/hot path are CONSTANT-ITER + branchless within reductions.**
- Inner reductions iterate a compile-time-constant count (e.g., `MAX_RIDGE_MODELS=8`, NOT runtime `n`)
- NO `if` guards inside reduction loops
- Zero-contribution iterations are bytewise no-ops via IEEE-754 invariants (`x*0=0`, `x-0=x` exact)
- Algorithmic state pre-zero (per-row, per-solve, per-cycle) establishes the zero-invariant
- See CLAUDE.md item 26; `branchless-math-kernel-pattern.md`

**HARD: Structs used in byte-equivalence contexts have EXPLICIT zero-init padding.**
- Any struct compared via `memcmp` / SHA-256 / wire format / HMAC input declares ALL padding bytes via `int<N>_t _padding<N> = 0;` default-init fields
- Implicit C/C++ struct padding is UB unless explicitly initialized
- Pattern documented in `struct-padding-determinism-pattern.md`
- See CLAUDE.md item 27

**STRONG: PRNG choice for replay-determinism + persistence.**
- When replay-determinism + persistence are both load-bearing, prefer SIMPLE algorithm with small state (splitmix64; 1 uint64) over HIGH-QUALITY algorithm with large state (mt19937_64; 312 words)
- `std::normal_distribution` is UNSAFE for cross-binary replay (libstdc++-implementation-defined output)
- Pattern: simple algorithm + small state + Box-Muller helper + seed-scrambling helper + SHA-256-locked sample-trace test
- See `prng-choice-for-replay-determinism.md` (CLAUDE.md item 24's first reference application)

**STRONG: Sliding-window incremental statistics over a fixed window.**
- For statistics (mean, variance, covariance, correlation) over the K most recent records, maintain running sums via subtract-then-add at sample eviction: `sum += x_new - x_oldest`
- Eliminates periodic-reset code smell common in vanilla-Welford-with-drift-mitigation
- Bounds drift by window contents (each record's contribution added once + subtracted once across its K-record lifetime)
- See CLAUDE.md item 29; `sliding-window-online-statistics-pattern.md`

### What NOT to do

- ❌ `std::normal_distribution` anywhere replay-determinism matters (libstdc++ implementation-defined)
- ❌ `atof` in parsers (locale-dependent; produces "0,55" → 0.0 under de_DE)
- ❌ Variable-iteration math kernels on slow path (drift class; replace with constant-iter + pre-zero)
- ❌ Wide refactors that change struct field offsets in HMAC-signed bodies (Layer 5b hash test fires; investigate before resetting hash)

**Cross-references:** CLAUDE.md items 14, 15, 24, 25, 26, 27, 29; DESIGN_SPECS/wire-format-byte-preservation-discipline.md, avx512-byte-determinism-pattern.md, branchless-math-kernel-pattern.md, struct-padding-determinism-pattern.md, prng-choice-for-replay-determinism.md, sliding-window-online-statistics-pattern.md; PARITY_LIFECYCLE.md, PARITY_VERIFICATION_CHECKLIST.md.

---

## 6. Concurrency family

**WHY.** No mutexes anywhere — period. Every cross-thread interaction
must be lock-free, wait-free, or designed for eventual consistency
with explicit staleness tolerance. The reason: a single mutex acquisition
under contention can stall the hot path for milliseconds (kernel wait
+ scheduler), which is 10,000× the per-tick budget.

### Principles in this family

**HARD: All thread sync via lock-free primitives only.**
- **SPSC/MPSC rings** (`MemHeaders/SPSCRing.hpp`) for producer/consumer messaging
- **ParameterSlot seqlock** (`CoreFrameworks/ExecutionCore.hpp`) for slow→hot push of GateParameters (1 reader, 1 writer; ~6ns full read; ~1ns cached-seq check)
- **`alignas(64) atomic<T>`** for single-byte cross-thread flags (e.g., `permission`, `kill_tripped`)
- See STRATEGY_AND_CODING_RULES Rule 3 + latency-path-discipline.md Rule 7

**HARD: Per-core data plane.** Each engine owns its rolling/regime/flow state. No shared state between cores on the slow path. Producer thread fans Binance ticks across SPSC rings to per-core consumers. See CLAUDE.md item 4.

**HARD: OMS submit funneling.** The drainer thread is the SOLE caller of `OrderManager_Submit`. Any other code path that would submit goes through the drainer's MPSC submit queue. Single-writer = lock-free; multiple-writer = MPSC ring. See CLAUDE.md item 5.

**STRONG: SPSC ring failure → counter, not retry.**
- `SPSCRing_TryPush` returns false when full
- Increment a failure counter; preserve state so next tick retries naturally
- NEVER busy-wait or block on push
- See latency-path-discipline.md Rule 3

**STRONG: Cross-thread fields get `alignas(64)` to avoid false sharing.**
- Hot READS go in own cache line cluster
- Cross-thread atomic writes go in own `alignas(64)` block
- Verify with grep: any `__atomic_load_n` / `std::atomic<T>` field should have `alignas(64)` or be in a struct that does
- Periodically run `perf c2c` to verify no false sharing under load
- See latency-path-discipline.md Rule 1

**STRONG: Smart CPU pinning** — slow-paths avoid SMT siblings of busy threads via `/sys` topology read at boot. Reduces tail variance from cross-SMT cache eviction. See CLAUDE.md item 11.

**SOFT: Memory ordering** — default `__ATOMIC_RELAXED` for observability flags (no happens-before constraint with other data). Upgrade to `release-acquire` when the bitmap synchronizes OTHER data (e.g., result-ready flag releasing a result struct).

**PROCESS: Failure-path observability via counter increment + slow-path scrape.**
- When a hot-path operation can fail (ring full, NaN feature, etc.), increment a counter; do NOT log
- Slow path scrapes counter periodically + logs delta if non-zero, OR surfaces via TUISnapshot
- Counters are lock-free single-writer (the failing thread's own); read by slow path with `__atomic_load_n(..., ATOMIC_RELAXED)`
- See latency-path-discipline.md Rule 2

### What NOT to do

- ❌ `std::mutex` / `condition_variable` / `pthread_rwlock` anywhere
- ❌ `std::shared_mutex` (atomics + potential blocking)
- ❌ Busy-wait on push (couples hot-path latency to drainer responsiveness)
- ❌ `fprintf` / `printf` / `write()` from hot/slow path (libc stdio mutex; cascading stall under degraded conditions)
- ❌ Synchronous I/O on drainer thread (use async logger thread per OrderEventLog pattern)

**Cross-references:** CLAUDE.md items 4, 5, 11; STRATEGY_AND_CODING_RULES Rule 3; latency-path-discipline.md Rules 2, 3, 7; LATENCY_OPTIMIZATION_AUDIT.md Part 6 (system & OS jitter).

---

## 7. Structural-fix family (the most load-bearing meta-pattern)

**WHY this family exists.** The codebase has a long history of bug
classes that recur when the same pattern at multiple sites drifts
apart — e.g., parser site forgets to add the new cfg field that the
struct site added; mirror code paths drift apart over time; production-
caller forgets the populator step. Direct-patching each instance is
recurring debt; structural fix (compile-time enforcement, X-macro
registry, single chokepoint) eliminates the bug CLASS — not just the
instance. The decision framework: if a bug class has recurred 3+
times, structural fix is the correct path even at higher upfront cost.

### Principles in this family

**STRONG: X-macro registry is the standard pattern for multi-site additions.**
- Any category where "adding the next instance" requires touching ≥2 code sites must use a `FOREACH_<CATEGORY>(X)` registry
- Audited categories: strategies, ML features, SHALT codes, halt_reason codes, regimes, stateful GUI panels, backtest metrics, stamp-bound cfg fields, architectural stamp-body model-const fields, failure-mode observability fields
- See CLAUDE.md item 13; `EASY_ADDITIONS_INVARIANTS.md`; `x-macro-registry-with-presence-dispatch.md`

**STRONG: Structural fix preferred when bug class can recur.**
- When facing a bug whose ROOT CAUSE is "same pattern at multiple sites drifted apart" (Class 18 mirror, parallel paths), prefer compile-time enforcement (X-macro registry, helper extraction with all callers unified) over direct patch
- Reason: 4× recurrence of v5.9.5b production-caller class before STAMP_CFG_AUTOPOPULATE extinguished it. Each occurrence cost 1-3h debug. Structural fix would have cost ~3h once.
- See CLAUDE.md item 19; `structural-fix-preferred-decision-framework.md`

**STRONG: AUTOPOPULATE companion macro for X-macro registries with production-caller side effects.**
- When a registry has multiple production callers that ASSEMBLE the registry-driven struct, define an AUTOPOPULATE companion macro that auto-generates per-field populator code via X-macro expansion
- Production callers replace ~50-100 LOC of manual `inf.X = src.X; inf.has_X = 1;` blocks with one `STAMP_X_AUTOPOPULATE(target, source)` call
- Closes production-caller field-population class structurally — adding a new registry field becomes 1 row; AUTOPOPULATE picks it up at next compile; forgetting becomes impossible
- See CLAUDE.md item 21; `autopopulate-pattern-for-production-caller-class.md`

**STRONG: PRE/POST registry split for canonical-emit-order preservation.**
- When a registry's entries must emit at positions INTERLEAVED with a SISTER registry's entries (HMAC-locked wire format), split FOREACH into `_PRE_CFG` and `_POST_CFG` halves
- Same tuple shape across halves; struct generation + AUTOPOPULATE walk the union; emit walks halves separately
- See CLAUDE.md item 22; `pre-post-cfg-registry-split-for-emit-order-preservation.md`

**STRONG: Type-trait dispatch via templated helpers (`tt::` namespace).**
- C++17 `if constexpr` discards branches at TEMPLATE INSTANTIATION
- In **non-template macro context** (X-macro expansion in regular function body), all branches must be SYNTACTICALLY VALID for ALL types
- Fix: extract type dispatch into a templated helper function that's instantiated per-T
- Required ANY TIME a non-template context uses if-constexpr with branches that have different syntax requirements per type (typical: `char[N]` strncpy vs scalar cast)
- This pattern is the foundation of the **3-barrier structural fix for Class 23** (type-erased reinterpret_cast dispatch): API surface has no void*+offset entry + X-macro extractor passes field by reference + type-family static_assert at each tt:: function
- See CLAUDE.md item 23; `type-trait-dispatch-via-tt-namespace.md`; RECURRING_BUG_PATTERNS Class 23

**STRONG: Registry-bitmap SET discipline.**
- When a registry of flag bits (FOREACH_*) is paired with a bitmap field + downstream consumers (BITMAP_IS_SET, branchless mask compute, `/readiness` checks), the SET sites are SEPARATE actions from the data writes — easy to forget
- Two anti-pattern shapes: (A) data write without companion BITMAP_SET, (B) SET chokepoint bypassed by alternate loader path
- Structural fix templates (preference order): AUTOPOPULATE companion → single chokepoint function → accessor wrapper
- See CLAUDE.md item 30; `registry-bitmap-set-discipline.md`

**PROCESS: Codify design principles in CLAUDE.md as patterns mature.**
- Promote to CLAUDE.md once: ≥2 codebase applications OR DESIGN_SPECS doc exists, AND pattern is broad
- Items 19-30 are the codified history of this lifecycle
- See `pattern-codification-lifecycle.md` (7-stage lifecycle: audit → DESIGN_SPEC → first reference → cohort migration → CLAUDE.md item → tooling enforcement → wider audit)

### What NOT to do

- ❌ Premature abstraction (registry overhead requires ≥3 entries + ≥2 caller sites; CLAUDE.md item 13 threshold)
- ❌ Structural fix for one-off bugs (use direct patch; this framework is for RECURRING classes)
- ❌ Adding to a registry without updating its AUTOPOPULATE companion (silently breaks production callers)
- ❌ Bypassing the X-macro extractor with hand-written if-chains (defeats the structural fix; reintroduces the drift class)

**Cross-references:** CLAUDE.md items 13, 19, 21, 22, 23, 30; DESIGN_SPECS/x-macro-registry-with-presence-dispatch.md, autopopulate-pattern-for-production-caller-class.md, autopopulate-from-arity-macro-family.md, pre-post-cfg-registry-split-for-emit-order-preservation.md, structural-fix-preferred-decision-framework.md, type-trait-dispatch-via-tt-namespace.md, registry-bitmap-set-discipline.md, pattern-codification-lifecycle.md; RECURRING_BUG_PATTERNS Class 11 (extensibility friction), Class 13 (snapshot mirror), Class 18 (mirror-incomplete), Class 23 (type-erased dispatch).

---

## 8. Failure observability family

**WHY.** Production HFT systems fail in ways that aren't obvious from
exit codes — silent drift, partial corruption, degraded model accuracy,
subtle timing regressions. The discipline is to make failures VISIBLE
the moment they happen, with enough metadata to diagnose without
re-deriving context.

### Principles in this family

**HARD: NaN-free feature pack with single-chokepoint validation.** See Determinism family above.

**STRONG: Failure modes registry with bit-flag storage.**
- `FOREACH_FAILURE_MODE` registry tracks all observable failure conditions
- BIT_FLAG entries auto-pack into a uint16_t / uint32_t / uint64_t bitmap
- COUNTER_U32 entries track recurring failure rates
- PERCENT_U8 entries track degraded states with severity gradient
- Storage class declared per-entry; AUTOPOPULATE handles dispatch
- See `MemHeaders/FailureModeRegistry.hpp`; CLAUDE.md item 13 (storage class discipline)

**STRONG: Drift detection registries (boot + runtime).**
- `feature_registry_hash` / `label_registry_hash` / `build_flags_hash` compared at model load vs current
- `scaler.feature_registry_hash` vs `handle.feature_registry_hash` cross-check
- `cfg.binding_drift` checks stamp-bound cfg field count + values
- `STAMP_HMAC_NOT_VERIFIED` set when held_out_stamp_secret was empty at load
- `MODEL_AGE_WARN` triggered when training_timestamp_us > model_max_age_hours
- All consolidated into `failure_flags` bitmap on PerCoreSnap → GUI Model Health panel

**STRONG: Per-arm reward observability invariant.**
- Each ensemble arm's prediction is graded INDEPENDENTLY against actual price movement
- Per-arm rewards observable regardless of which arm was selected
- Enables shadow-training (parallel bandit logging without acting), counterfactual evaluation, multi-algorithm A/B testing
- See CLAUDE.md item 24

**SOFT: Audit-driven detection of failure modes.**
- `/dod-audit` Stage 6 detection signatures for each pattern
- `/bug-check` registry-driven scan of `DOCS/RECURRING_BUG_PATTERNS.md`
- Adding a new bug class to RECURRING_BUG_PATTERNS auto-includes it in next /bug-check run

### What NOT to do

- ❌ Silent failure handling (any error returned from a hot-path operation must increment a counter; slow path observes)
- ❌ Mixing failure-flag storage classes in the same word without per-entry storage class declaration
- ❌ Adding a failure mode without paired GUI surface (display ↔ execution invariant; CLAUDE.md item 12)

**Cross-references:** CLAUDE.md items 12, 14, 24; `MemHeaders/FailureModeRegistry.hpp`; DOCS/CLAUDE_INTEGRATION.md (display↔execution invariant adoption pattern); /dod-audit + /bug-check skills.

---

## 9. Architectural primitives family

**WHY.** Beyond the cross-cutting principles above, certain
architectural decisions define the codebase's specific shape. These
aren't general principles; they're CHOICES that, once made, constrain
everything else. Understanding them is required to design new features
that fit the codebase.

### Principles in this family

**HARD: Per-position TP/SL exits on hot path; portfolio management on slow path.** TP/SL evaluation lives in `SG_Evaluate` (hot, branchless). Portfolio sizing, exposure tracking, drawdown checks live in slow path. See CLAUDE.md item 2.

**HARD: Fill consumption every tick.** No unprotected exposure. Even if no events arrive, the drainer drains; even if no fills arrive, the consumer consumes. See CLAUDE.md item 3.

**HARD: OMS submit funneling.** Drainer is sole `OrderManager_Submit` caller. See Concurrency family.

**STRONG: OneCore helpers shared by 3 callers.** Centralized live, per_core_slow live, backtest. Structural train-serve parity by construction — same helper function called from all three contexts means same behavior. See CLAUDE.md item 6.

**STRONG: TUI independent of engine.** Engine runs headless (no rendering on hot path). TUI reads state via double-buffered `TUISnapshot` (with seqlock since v5.11.3). GUI thread / TUI thread runs at ~60 Hz; engine is unaffected. See CLAUDE.md item 8.

**STRONG: Warmup observes market before trading.** Gates on slow-path sample count, not just tick count. Prevents trading during cold-cache cold-state startup. See CLAUDE.md item 7.

**STRONG: Partial exits dispatcher post-cap.** Strategies stay leg-A-only (single-position evaluators); the dispatcher decides if a second leg (partial exit) gets an entry. Hot path branch-gates leg B. See CLAUDE.md item 10.

**SOFT: No API key for market data WS.** Public Binance trade stream + depth WS endpoint. Avoids latency cost of authentication round-trips on data path. Order WS uses authenticated REST endpoint. See CLAUDE.md item 9.

### What NOT to do

- ❌ Adding an exit mode to slow path (exits are HOT-path; slow path only sets parameters)
- ❌ Bypassing OMS submit funnel (drainer must be the only caller)
- ❌ Coupling TUI to engine state directly (always go through TUISnapshot)
- ❌ Trading during warmup (warmup gates are NEVER short-circuited)

**Cross-references:** CLAUDE.md items 2, 3, 6, 7, 8, 9, 10, 11; /strategy-template skill (canonical strategy lifecycle); CoreFrameworks/EngineSharded.hpp (architectural anchor); plans/v5.15-live-readiness/MASTER.md (current sprint context).

---

## 10. Operator UX family

**WHY.** This codebase has ONE operator (currently Caramel; future
contributors will inherit). The operator-side surfaces — cfg files,
GUI tooltips, logs, paper-test workflow — are LOAD-BEARING for
correct operation. Breaking operator UX silently (e.g., dropping a
tooltip, changing default behavior, removing comment-preservation in
cfg writes) is a real bug, even if no test catches it.

### Principles in this family

**STRONG: Comment-preserving cfg writes.** `cfg_write_field(path, key, value)` at `GUI/SettingsPanel.hpp:472` does per-field text-splice that PRESERVES operator comments + line ordering in the cfg file. NEVER replace this with a wholesale `Cfg_Save(FILE*)` that rewrites the file from scratch.

**STRONG: Tooltip preservation byte-identical during migrations.**
- Hand-tuned operator prose (multi-line tooltips with examples, fee structure explanations, Discord/Telegram setup notes) MUST be preserved when migrating GUI fields between sources of truth
- Use C++ raw string literals `R"(...)"` or escaped `\n` to keep the bytes identical
- Tooltip changes are an operator-visible behavior change; they require explicit decision, not silent drift

**STRONG: Categorical applicability for cfg field gating in GUI.**
- NEVER hardcode strategy/regime/op-mode names in gating conditions
- Use category bitmaps (`STRAT_CAT_USES_BANDIT`, `OP_MODE_CAT_LIVE`, etc.) so adding a new strategy auto-applies relevant cfg fields
- See `categorical-tag-applicability-pattern.md`; CLAUDE.local.md going-forward rule "Categorical applicability for new cfg fields"

**STRONG: Cross-file cfg surfaces use `lives_in_struct` discriminator.**
- ONE `CfgFieldDescriptor` + `lives_in_struct` enum value; never parallel descriptors per cfg file
- Closes Class 21 (multiple parallel descriptors) drift class
- See `CoreFrameworks/CfgFieldRegistry.hpp`; CLAUDE.md item 21 (closes Class 21 + 23)

**SOFT: Default behavior preservation on version upgrades.**
- New cfg field defaults should match pre-existing behavior when operator hasn't set them
- Surface G `has_*` flags in stamp body preserve forward-compat without `MODEL_FORMAT_VERSION` bumps
- Live mode strict defaults via post-parse normalize pass (changes effective behavior of `model_verify_strict` etc. only when `trading_mode == LIVE` AND operator hasn't explicitly set the override)

**PROCESS: FEATURE_LOOKUP.md auto-write on new operator-visible features.**
- Per CLAUDE.local.md auto-write contract: agent MUST add an entry to `FEATURE_LOOKUP.md` when a new operator-visible feature ships
- Entry includes: what / cfg flags / fallback / where to verify / paper-test sanity / gotchas / related references
- Skip auto-write for: pure refactors, internal helper extraction, bug fixes restoring expected behavior, bytewise-identical perf optimizations

### What NOT to do

- ❌ Wholesale-rewrite of cfg files (loses operator comments + ordering)
- ❌ Tooltip drift during migrations (the operator notices)
- ❌ Hardcoded strategy enum names in gating (breaks when next strategy added)
- ❌ Parallel descriptors per cfg file (Class 21 mirror drift)

**Cross-references:** `categorical-tag-applicability-pattern.md`; `universal-cfg-field-registry-pattern.md` § "Cross-file cfg unification"; CLAUDE.local.md auto-write contracts; `tick-trader-percore-workspace/FEATURE_LOOKUP.md`; RECURRING_BUG_PATTERNS Class 19, 21.

---

## 11. Process discipline family

**WHY.** Multi-day architectural work + sprint-cadence shipping require
process discipline that prevents drift between plan + reality, catches
recurring bug classes pre-coding, and keeps the audit infrastructure
(skills + DESIGN_SPECS + RECURRING_BUG_PATTERNS) in sync with the code.

### Principles in this family

**HARD: Cold-pickup plan completeness — 10 fields.**
- Every plan must specify: branch state, exec-order matches deps, Step-0 first concrete move, function-names cited (verified via grep), file:line refs, stale-claim audit, effort-vs-LOC reconciliation, source-audit references, predecessor + dependent plans, tag + rollback anchors
- Fresh-context coder shouldn't lose hours re-deriving context
- See `/readiness` skill Cold-pickup section + DOCS/CLAUDE_REVIEW.md

**HARD: Verify handoffs against current code.**
- Compaction degrades — handoff prompts may have stale function names, line refs, struct shapes
- ALWAYS re-verify handoff claims via grep before acting
- See memory `feedback_compaction_degrades_treat_handoffs_or_hints.md`

**STRONG: Audit-driven pre-coding gate.**
- HIGH-RISK ships, first pattern applications, or cross-cutting changes get `/parity-check + /trace-deps + /readiness + /merge-scan + /dod-audit` fired in parallel BEFORE coding
- Operator decides whether to fire (NOT auto-triggered)
- Synthesize convergent findings to `plans/plan_checks/<sprint>-<sub-ship>-fresh-audits-synthesis.md`
- THEN consult operator before coding (do NOT auto-proceed even if findings look clear)
- See `audit-driven-pre-coding-gate.md`

**STRONG: After pre-coding audit, ALWAYS consult before coding.**
- Present findings + list potential fixes + iterate with operator
- Do NOT auto-proceed even if findings look clearly addressable
- See memory `feedback_consult_on_audit_findings.md`

**STRONG: Boundary-stable refactors over wide cascades.**
- Default to keeping public types unchanged + isolating new behavior INSIDE
- Reserve cascade for when the boundary type ITSELF is the bug
- Refactor that crosses ≥4 files: stop, propose stable boundary first
- See memory `feedback_reduce_touch_sites.md`

**STRONG: Cohort-audit when new cfg field has 2+ siblings.**
- New boolean cfg field with 2+ semantic siblings (`ridge_*`, `bandit_*`) → audit cohort
- All-eligible: migrate together; mixed eligibility: TECH_DEBT per-sibling
- See `cfg-flag-eligibility-criteria.md` § "Cohort audit"; CLAUDE.local.md going-forward rule

**STRONG: New docs default to private.**
- Docs capturing unshipped direction / optimization findings / operator-edge / private cfgs → `plans/` (workspace, gitignored, date-prefixed)
- Public architectural-only → `DOCS/`
- Auto-private gitignore patterns: `*_AUDIT.md`, `FUTURE_*.md`, `*-design-notes.md`, `*-suggestions.md`, etc.
- See CLAUDE.local.md going-forward rule

**STRONG: Workspace mirror for edge content.**
- `/sync-workspace` skill mirrors plans/ + .claude/skills/ (auto via symlinks); cfg files + .env + *.local.md (explicit copy)
- Run on-demand at end of session / after plan finalized / after skill updated

**SOFT: Suggest mid-sprint audits when work impacts downstream.**
- HIGH-RISK ship just shipped / first pattern application / cross-cutting changes → suggest `/test-strength-audit + /dod-audit + /parity-check` in parallel
- Wait for greenlight; don't auto-trigger
- Skip for routine pattern-application or pure additive work

**PROCESS: Auto-write contracts.**
- When an audit / skill / sub-ship surfaces an item, the agent MUST write the entry to the named ledger
- Surface → Ledger map: parity findings → PARITY_ISSUES.md; deferred items → TECH_DEBT.md; operator-visible features → FEATURE_LOOKUP.md; decoupling positioning → decoupling-roadmap; cohort findings → TECH_DEBT.md; operational landmines → LANDMINES.md
- See CLAUDE.local.md "Auto-write contracts" section

**PROCESS: No defer for effort-avoidance.**
- "Smaller scope" recommendations have been wrong 3/3 times in past sessions vs operator's "do it right now" instinct
- Defer is last-ditch, never an effort-avoidance escape hatch
- See memory `feedback_no_defer_for_effort.md`

**PROCESS: No MVP for plumbing/refactor work.**
- MVP is for genuinely-new features with external dependencies (maker orders w/ orderbook)
- Plumbing/pattern-application work ships the FULL DOCUMENTED DESIGN
- See memory `feedback_no_mvp_for_plumbing_only_for_unknown_unknowns.md`

**PROCESS: Don't measure structural work by LOC.**
- For pattern-building / refactor / class-closure work, lead with classes-closed + patterns-codified + future-work-becomes-mechanical
- LOC is incidental (can even be negative)
- See memory `feedback_dont_measure_structural_work_by_loc.md`

### What NOT to do

- ❌ Coding directly off a plan without /readiness verification
- ❌ Auto-proceeding past audit findings without operator consult
- ❌ Wide cascades when boundary-stable refactor would work
- ❌ Premature deferral as effort-avoidance
- ❌ MVP-style ship for refactor work where the design is documented

**Cross-references:** CLAUDE.local.md going-forward rules; memories at `~/.claude/projects/-home-caramel-code-FoxML-Trader-v2/memory/`; /readiness, /parity-check, /trace-deps, /merge-scan, /dod-audit, /bug-check, /handoff skills; DESIGN_SPECS/audit-driven-pre-coding-gate.md, structural-fix-preferred-decision-framework.md, pattern-codification-lifecycle.md.

---

## 12. What this codebase EXPLICITLY does NOT optimize for

Every codebase has design choices it says NO to. Naming them keeps focus.

- **Multi-symbol portfolio management.** Single-symbol design. Adding multi-symbol would require fundamental rework of the per-core sharded model + portfolio bitmap + risk allocation. Defer indefinitely.
- **Maker order execution.** No consistent order-book data source today; TECH_DEBT-008 indefinite defer. Engine is taker-side only.
- **Sub-millisecond fill confirmation.** Binance REST round-trip is ~50-200ms; we don't try to beat the network.
- **Multi-tenant operator support.** Single-operator tooling (one paper-test session at a time; one cfg file).
- **GPU-accelerated ML inference.** XGBoost C API + future Treelite AOT path is sufficient; GPU dependency adds deployment friction without proportionate latency win for our model sizes.
- **Cross-platform (Windows, macOS).** Linux-only (`isolcpus`, `nohz_full`, `rcu_nocbs`, `mlockall`, `MAP_HUGETLB`, AVX-512). Windows/macOS deployments would need rework of OS-level tuning.
- **Web frontend / browser GUI.** Native ImGui via SDL2; no HTTP server, no JS frontend. Operator runs locally.
- **Distributed deployment.** Single-process, single-machine. No cross-machine orchestration.
- **Backtest performance optimization (subsecond per-day).** Backtest engine prioritizes train-serve parity over throughput; running multi-day backtests is acceptable.
- **Exotic strategies requiring heavy state (deep RL, full order-book modeling).** Lightweight strategies (regression-driven, ML inference, fixed rules) only. Heavy state breaks the per-core sharding contract.

When operator priorities shift — e.g., a new revenue path requires
multi-symbol — these explicit-NOs become explicit decision points,
not silent assumptions.

---

## 13. Cross-reference index

Every claim in this doc traces to a canonical source. Use this table
for quick lookups when implementing or reviewing.

| Topic | CLAUDE.md item | DESIGN_SPECS path | RECURRING_BUG_PATTERNS class |
|---|---|---|---|
| Portfolio bitmap | 1 | bitmap-flag-api.md | — |
| Per-position TP/SL hot, portfolio slow | 2 | — | — |
| Fill consumption every tick | 3 | — | — |
| Per-core data plane | 4 | — | — |
| OMS submit funneling | 5 | — | — |
| OneCore helpers | 6 | — | — |
| Warmup observes before trading | 7 | — | — |
| TUI decoupling | 8 | — | — |
| No API key for market data WS | 9 | — | — |
| Partial exits dispatcher post-cap | 10 | — | — |
| Smart CPU pinning | 11 | — | — |
| Display ↔ execution invariant | 12 | display-execution-invariant-registry-pattern.md | — |
| X-macro registry | 13 | x-macro-registry-with-presence-dispatch.md | Class 11 |
| NaN-free feature pack | 14 | — | — |
| Parity-tested-by-construction | 15 | wire-format-byte-preservation-discipline.md | — |
| Reuse-audit | 16 | — | — |
| Latency-additions tracked | 17 | — | — |
| Slow-path latency reduction | 18 | latency-vs-cache-decision-framework.md | — |
| Structural fix preferred | 19 | structural-fix-preferred-decision-framework.md | Class 18 |
| Bit-packed flag storage (BITMAP_*) | 20 | bitmap-flag-api.md, bitmap-overflow-protection-discipline.md | Class 20 |
| AUTOPOPULATE companion | 21 | autopopulate-pattern-for-production-caller-class.md | Class 14 |
| PRE/POST registry split | 22 | pre-post-cfg-registry-split-for-emit-order-preservation.md | — |
| Type-trait dispatch via tt:: | 23 | type-trait-dispatch-via-tt-namespace.md | Class 23 |
| Per-arm reward observability | 24 | prng-choice-for-replay-determinism.md | — |
| AVX-512 byte determinism | 25 | avx512-byte-determinism-pattern.md | — |
| Math kernels constant-iter + branchless | 26 | branchless-math-kernel-pattern.md | — |
| Struct padding determinism | 27 | struct-padding-determinism-pattern.md | — |
| Cycles vs cache cost framework | 28 | latency-vs-cache-decision-framework.md | — |
| Sliding-window incremental stats | 29 | sliding-window-online-statistics-pattern.md | — |
| Registry-bitmap SET discipline | 30 | registry-bitmap-set-discipline.md | — |
| Categorical-tag applicability | (CLAUDE.local.md rule) | categorical-tag-applicability-pattern.md | Class 19 |
| Cross-file cfg unification | (CLAUDE.local.md rule) | universal-cfg-field-registry-pattern.md § "Cross-file" | Class 21 |
| Cohort audit when new cfg sibling | (CLAUDE.local.md rule) | cfg-flag-eligibility-criteria.md § "Cohort audit" | — |
| Boundary-stable refactors | (memory rule) | — | — |
| Audit-driven pre-coding gate | (CLAUDE.local.md rule) | audit-driven-pre-coding-gate.md | — |
| Pattern codification lifecycle | (CLAUDE.local.md rule) | pattern-codification-lifecycle.md | — |
| Framework-driven extensibility (meta-principle) | 31 | (§ 1.5 — this doc) | — |
| Metadata-bit-driven derived filter framework | (item 31 sub-pattern) | metadata-bit-driven-derived-filter-framework.md | — |
| Meta-registry of registries (codebase-wide) | (item 31 sub-pattern) | meta-registry-pattern-for-codebase-registry-discipline.md | — |
| Sidecar override pattern for auto-flows | (item 31 sub-pattern) | sidecar-override-pattern-for-registry-auto-flows.md | — |
| Framework composition (cfg infra at .F.4d) | (item 31 sub-pattern) | framework-composition-overview.md | — |
| Plan API drift (fictional functions) | — | — | Class 14 |
| Function signature drift | — | — | Class 15 |
| Naming convention drift | — | — | Class 16 |
| Architectural deferral without grep | — | — | Class 17 |
| Mirror-incomplete plans | — | — | Class 18 |
| Hardcoded instance names | — | — | Class 19 |
| Bitmap overflow without static_assert | — | — | Class 20 |
| Multiple parallel descriptors | — | — | Class 21 |
| Runtime cfg gating scattered | — | — | Class 22 |
| Type-erased reinterpret_cast dispatch | — | type-trait-dispatch-via-tt-namespace.md | Class 23 |

---

## 14. How to extend this doc

When a new architectural pattern matures (per `pattern-codification-lifecycle.md`):

1. The pattern gets a DESIGN_SPEC body
2. After 2+ codebase applications, the pattern becomes a CLAUDE.md item
3. **Add it to this doc** under the appropriate family section (or create a new family)
4. Update the cross-reference index in section 13

When a new bug class gets a 3rd recurrence:

1. Add Class N entry to `DOCS/RECURRING_BUG_PATTERNS.md`
2. If a positive antidote pattern is established → add DESIGN_SPEC
3. **Cross-link from the relevant family section in this doc**
4. Update the cross-reference index

When operator priorities shift:

1. Update section 12 (explicit NOs) to remove the item or add a new explicit-YES
2. Update CLAUDE.md if the change affects always-on context
3. Add a CLAUDE.local.md going-forward rule if the change has process implications

---

**End of DESIGN_PHILOSOPHY.md.** This doc is the WHY behind the codebase's
mental model. The patterns + items + bug classes referenced are the source-
of-truth — this doc synthesizes. Read it cold-pickup; refer to it when
designing; cross-link from it when extending.
