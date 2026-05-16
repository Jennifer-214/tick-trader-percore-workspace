# HP_REFACTOR.md — Hot-path refactor scope + triggers (future opportunity)

**Created:** 2026-05-16 (v5.15.5.F.4c.4 audit-gate pre-coding observation)
**Status:** SCOPE-DOCUMENT — not a planned ship; captures the "complete-rework path for HOT-path latency changes" as a future opportunity to track once the broader structural-improvement sprint settles

## Why this doc exists

The v5.15.5.F.4 sprint series (and its surrounding work) ships a steady stream of **structural / framework-discipline / bug-class-closure** improvements that operate on SLOW-PATH / DRAINER / SP-bound surfaces. The hot path (`BG_Evaluate` / `SG_Evaluate` / `ExecutionCore_Tick` / `GateParameters` / `ParameterSlot`) has been deliberately UNTOUCHED through the entire `.F` sprint per H7+H8 invariants.

This is the right discipline for the framework-progression work — hot-path changes carry high risk (latency budget violation; determinism regression; mispredict surface expansion) and should NOT be bundled with structural/correctness ships.

**But:** the hot path itself accumulates latency-relevant opportunities over time. This doc captures the SCOPE + TRIGGERS for a future dedicated hot-path-refactor ship when (a) the framework work reaches a stable plateau, (b) operator profile data identifies a hot-path budget pressure point, OR (c) a new latency-sensitive feature (e.g., maker order MVP) requires hot-path expansion.

## What's IN the hot path today

Per CLAUDE.md architecture + `latency-path-discipline.md`:

### Per-tick path (≤500ns p99 budget — H8)

| Function | File:line | Cadence | Current shape |
|---|---|---|---|
| `BG_Evaluate` | `CoreFrameworks/ControllerEventLoop.hpp` | Per Binance tick | Branchless gate predicate compute; reads cached `GateParameters` via seqlock; mask-select dispatch |
| `SG_Evaluate ×2` (entry + exit) | `CoreFrameworks/ControllerEventLoop.hpp` | Per tick × 2 strategies | Branchless gate decision; cmov dispatch |
| `ExecutionCore_Tick` | `CoreFrameworks/ExecutionCore.hpp` | Per tick | Mask-AND gate check; branchless TradeEvent push (rare branch via `__builtin_expect`) |
| `GateParameters` reads via `ParameterSlot` | `CoreFrameworks/ParameterSlot.hpp` | Per tick | Lock-free seqlock read of cached per-core params |

### Hot-path invariants (per CLAUDE.md H7 + H8)

- **H7: Hot path BRANCHLESS for data-dependent dispatch** (mask compute + cmov per Rule 8 of `latency-path-discipline.md`)
- **H8: Hot path p99 ≤500ns; slow path p99 ≤100µs** (regression = ship blocker)
- **H20: Branchless preferred for SP/HP data-dependent dispatch EVEN WHEN NOMINALLY SLOWER** (added v5.15.5.F.4c.3 WIP2d-1.B.0d)

## What's OUT of the hot path (slow-path / drainer / boot-time)

- `EventLoop_RebuildOneCore` (slow path — per-cycle ≤100µs)
- `OMS_DrainSubmit` / `OrderManager_Tick` (drainer — per-fill/per-cmd, slow-path-bounded)
- `RollingStats_Push` / `Regime_ComputeSignals` (slow-path)
- `Bandit_Update` / `Thompson_Update` / reward attribution (slow-path)
- All ML feature compute (slow-path)
- All calib log emission (drainer-rare; trade-close-bounded)
- All cfg parsing / boot setup (one-time)

## Why HOT path stays untouched through the `.F` sprint series

The `.F` sprint family (.F.4a → .F.4c.4 → .F.4d → .F.4e → .F.5) is framework-discipline progression:
- Universal cfg registry frameworks
- `tt::` typed dispatch
- Derived filter frameworks
- Meta-registry framework
- Sidecar override pattern
- Per-instance registry pattern
- `multi-state-dispatch-with-per-state-update-metadata` (first canonical at .F.4c.4)
- `multi-bit-state-encoding-pattern` (Stage 3 progression)
- `decision-time-data-binding-pattern` (sibling-array family)
- `sink-fn-pointer-for-optional-side-effect-pattern` (Pattern 5)
- `branchless-dispatch-discipline` (Pattern 1/3/4/5 canonicalization)
- `cfg-scope-discipline` (Class 25 closure)

ALL of these operate on slow-path / drainer / boot-time surfaces. The hot path doesn't materially benefit from these framework progressions — it already has its own branchless discipline (H7) + tight cache layout + minimal dispatch.

**Touching hot path during a framework-discipline ship is the wrong frame** — risk-reward asymmetry says: framework discipline ships should preserve hot-path invariants (calls_graph_diff verify; HOT_PATH_CHANGELOG: NONE) and accept that hot-path optimization waits for its own dedicated ship.

## When to consider an HP-refactor ship

### Trigger 1 — Hot-path p99 budget pressure observed in production profile data

If operator profile data surfaces that:
- p99 (hot path) > 500ns for a non-trivial fraction of ticks
- Specific BG/SG/ExecutionCore_Tick callsites exceed budget under high tick rate
- Mispredict variance widens p99/p50 spread past comfort

→ Trigger an `HP_*` ship to investigate + fix the specific budget-violating site.

### Trigger 2 — New latency-sensitive feature requires hot-path expansion

If a new feature (e.g., maker order MVP via TECH_DEBT-008, order book ingest, multi-symbol routing) requires per-tick logic that doesn't fit the current hot-path discipline:

→ Trigger an HP-design ship to lay out the new hot-path surface + expand H8 budget envelope OR find alternative architecture (e.g., move logic to slow-path / drainer).

### Trigger 3 — Framework progression stabilizes; hot-path optimization opens as the natural next direction

When the `.F` sprint series closes its umbrella (post-.F.4e or post-.F.5) and the framework library is at a stable plateau, the natural next direction is:
1. Cross-cutting cache audit (sister to this concern)
2. Hot-path latency profile review
3. Dedicated HP-refactor ships if profiles surface improvement opportunities

→ Trigger HP_REFACTOR_PLANNING ship to enumerate concrete opportunities + scope.

### Trigger 4 — Hardware/OS environment change

If the deployment environment changes (different CPU, kernel, isolation strategy):
- Branch predictor behavior changes
- Cache hierarchy changes
- TLB pressure changes

→ Re-profile + re-evaluate hot-path discipline assumptions.

## Scope candidates for a future HP-refactor ship

NOT planned for any specific sprint; these are CANDIDATES to evaluate when an HP-refactor ship is triggered:

### A. ExecutionCore_Tick branchless dispatch composition

Hot path currently uses mask-compute + cmov per-tick. Could the dispatch be metadata-driven (sister to multi-state-dispatch-with-per-state-update-metadata applied to ExecutionCore states)?

- **Current shape:** mask-AND on gate flags; cmov on TradeEvent push decision
- **Potential:** dispatch table indexed by per-tick state? (Risk: increased L1i pressure for indirect call vs simple cmov)
- **Verdict:** likely NOT worth changing — current cmov shape is already optimal for binary decision; metadata-driven dispatch table adds overhead

### B. ParameterSlot seqlock read optimization

Hot path reads cached `GateParameters` via seqlock every tick. Already lock-free + branchless.

- **Current shape:** atomic load + seqlock retry on torn read
- **Potential:** prefetch hint at slow-path-rebuild time; cache-line co-location of frequently-co-read params
- **Verdict:** profile-driven; low expected impact unless seqlock retries surface in profile

### C. BG_Evaluate gate predicate cache-line layout

Hot path reads multiple gate predicates per tick. Cache discipline matters.

- **Current shape:** predicates co-located via slow-path-gate-registry-pattern; cached at slow-path-rebuild
- **Potential:** AVX-512 SIMD evaluation of multiple gate predicates in one MOV (sister to AVX-512 patterns elsewhere)
- **Verdict:** profile-driven; AVX-512 SIMD has its own discipline cost (scalar fallback requirement per H10)

### D. SG_Evaluate inline composition with BG_Evaluate

Hot path runs BG_Evaluate then SG_Evaluate ×2. Three function calls per tick.

- **Current shape:** three inline function calls (inlined by compiler at -O3)
- **Potential:** single composed fn merging gate-block + sg-decision logic (lossy on modularity)
- **Verdict:** measure if inlining is actually happening at -O3; if yes, no work needed; if no, inline the composition

### E. Per-tick TradeEvent struct layout for branchless push

Hot path constructs TradeEvent + pushes to SPSC ring (rare per H8 budget).

- **Current shape:** TradeEvent fields filled per-tick; push via `__builtin_expect`-rare branch
- **Potential:** pre-allocate TradeEvent slot via prefetch + always-construct + mask-gated push
- **Verdict:** maybe; benchmark before changing

### F. AVX-512 vector dispatch for multi-strategy hot path

If multiple strategies per core become hot-path simultaneous (today: 2 max), AVX-512 lane-parallel evaluation could pack the multi-strategy dispatch.

- **Current shape:** 2 strategies sequentially evaluated
- **Potential:** AVX-512 lane-parallel for up to 8 strategies
- **Verdict:** speculative; only relevant if strategy count grows past 2

## Cross-references

- `tick-trader-percore-workspace/DOCS/DESIGN_PHILOSOPHY.md` § 4 — Latency cost framework
- `DOCS/STRATEGY_AND_CODING_RULES.md` (private) — 11 strict invariants (H1-H14 + H20)
- `DOCS/LATENCY_OPTIMIZATION_AUDIT.md` (private) — 13-part audit of optimization opportunities
- `plans/_cross-cutting/2026-05-06-latency-path-discipline.md` — 7 latency-path rules + anti-pattern history
- `DESIGN_SPECS/branchless-dispatch-discipline.md` — Pattern 1/2/3/4/5 canonical shapes
- `DESIGN_SPECS/latency-vs-cache-decision-framework.md` — Cost model for cache vs branch decisions
- `DESIGN_SPECS/avx512-byte-determinism-pattern.md` — AVX-512 SIMD with scalar fallback discipline
- `tick-trader-percore-workspace/DOCS/DESIGN_PHILOSOPHY.md` § 2 (Hard Invariants — H7 + H8 + H20 governing hot path)

## Companion: cache-audit-related observations + rough scope idea

Codebase-wide CACHE concerns surfaced during `.F.4c.4` audit-gate review 2026-05-16 (sister to hot-path concerns; not strictly HP-refactor but adjacent). Documented here for future cache-audit ship.

### Concrete observations (as of v5.15.5.F.4c.3 + post-`.F.4c.4` close)

#### O1 — Per-slot data scattered across 3 different owners

Per-slot decision-time-bound data lives on different structs:
- `Portfolio<F>::positions[slot].entry_fee` (in Portfolio<F>; Pattern 4 retroactively recognized)
- `OmsState::per_slot_decision.last_exit_fee[pslot]` (in OmsState; canonical at `.F.4c.3` r-4; named-cluster at `.F.4c.4`)
- `OmsState::per_slot_decision.bandit_reward_bps[pslot]` (in OmsState; this ship)
- `Order<F>::flags_packed` bandit context bits (in Order<F>; `.F.4c.4` Option 8 bit-pack)
- `Order<F>::pre_resolved.fee_rate / .slippage_pct` (in Order<F>; `.F.4c.3` r-1 canonical)

Result: drainer at trade-close has to touch 3-4 different cache lines across Position + OmsState + Order to assemble the calib emit row. Cross-owner unification could improve cache locality at trade-close emit time. **Profile-driven decision; not premature today.**

Scope estimate if pursued as standalone ship:
- Consolidate per-slot decision-time-bound data under one owner (likely OmsState; Position survives as Portfolio's view of executed trades)
- Audit + migrate every per-slot field access across ~10-20 file edits
- Effort: 1-2 days focused work
- Risk: MED-HIGH (cross-owner reorganization touches many readers/writers)
- Benefit: ~10-50ns p99 trade-close emit improvement (estimated; profile-driven)

#### O2 — ThompsonBandit SoA layout per-arm field separation

Current shape:
```cpp
struct ThompsonBanditState {
    double mu_post[8];          // 64B (1 cache line)
    double precision_post[8];   // 64B (1 cache line)
    uint32_t total_pulls[8];    // 32B (half cache line)
    // ...
};
```

`Thompson_Sample` reads `mu_post[i]` + `precision_post[i]` + (potentially `total_pulls[i]`) per-arm. SoA → 2-3 cache lines per per-arm access × 8 arms = 16-24 cache line touches per Thompson_Sample.

AoS-pack alternative:
```cpp
struct ThompsonArmState {
    double mu_post;
    double precision_post;
    uint32_t total_pulls;
    uint32_t _padding;
};
struct ThompsonBanditState {
    ThompsonArmState arms[8];  // 24B × 8 = 192B (3 cache lines; 1.6× tighter for per-arm access)
};
```

AoS-pack hot-side benefits: each per-arm access touches ONE cache line instead of 2-3. Cost: when batching same-field across arms (e.g., `for i: sum += mu_post[i]`), AoS is slower than SoA. Mixed pattern; depends on which access pattern dominates in production profile.

Scope estimate if pursued:
- Restructure `ThompsonBanditState` to AoS or HoSoA (hybrid)
- Audit + migrate `Thompson_Sample` / `Thompson_Update` / `Thompson_GetProbabilities` / `Thompson_GetSoftmaxWeights` body access patterns
- Re-run determinism tests (bytewise-identical output required)
- Effort: ~4-6h
- Risk: MED (math kernel restructure; determinism regression surface)
- Benefit: ~50-100ns p99 on Thompson_Sample (estimated; profile-driven)

#### O3 — Bandit_GetProbabilities AVX-512 path alignment verification

AVX-512 SIMD kernels require 64-byte alignment per H10 + `avx512-byte-determinism-pattern.md`. `Bandit_GetProbabilities` body at `BanditLearning.hpp:179-255` has both AVX-512 path + scalar fallback (H10 invariant). Verify per-arm weight array alignment + AVX-512 scalar-fallback bytewise-identical output regression test passes.

Scope estimate:
- Spot-check alignment via `static_assert(alignof(...))` + grep
- Verify scalar-fallback test exists in `tests/controller_test.cpp`
- Run AVX-512 byte-determinism regression
- Effort: ~30-60 min audit
- Risk: LOW (verification only; no restructure unless violation found)
- Benefit: AVX-512 invariant integrity (correctness, not latency)

#### O4 — Cross-cutting struct padding determinism audit

H12 invariant: structs in byte-equivalence contexts get explicit `int<N>_t _padding<N> = 0;` default-init fields. Cache layout changes during `.F.4d/.F.4e/.F.5` framework progression may introduce implicit padding gaps that violate H12 silently. Periodic audit catches them.

Scope estimate:
- Codebase-wide grep for structs with `static_assert(sizeof(...) == N)`
- Visual inspection for padding gaps
- Add explicit `_padding<N>` members where gaps detected
- Effort: ~2-4h
- Risk: LOW (additive; preserves byte layout determinism)
- Benefit: invariant integrity for HMAC byte-preservation discipline

#### O5 — Cluster placement audit on EnsembleModelZoo + ThompsonBanditState post-multi-side expansion

`.F.4c.4` adds `thompson_exit_bandits[NUM_REGIMES]` mirror + new fn-pointer fields. Post-ship, EnsembleModelZoo has ~25% more cluster surface than pre-ship. HOT/WARM/COLD cluster boundaries may need rebalancing.

Scope estimate:
- Profile reads-per-tick on EnsembleModelZoo fields
- Re-cluster per access pattern
- Effort: ~2-3h profile + restructure
- Risk: MED (cluster changes touch reader sites)
- Benefit: slow-path latency improvement; cache footprint reduction

### Aggregate cache-audit-ship rough scope

If all O1-O5 are pursued as ONE dedicated cache-audit ship after framework progression closes:

- **Effort:** ~2-3 days focused work
- **Risk:** MED (multiple cross-cutting changes; cache miss cascade potential)
- **Profile-data requirement:** YES — need production hot-path + slow-path profile data to prioritize O1 vs O2 vs O5
- **Prerequisites:**
  - `.F.4d` / `.F.4e` / `.F.5` framework progression closed (cluster placement stable)
  - Production profile data captured (perf record on representative workload)
  - HP_REFACTOR triggers evaluated (no current Trigger 1-4 active)
- **Benefit estimate (combined):**
  - Hot-path p99: ~50-200ns reduction potential (unverified; profile-driven)
  - Slow-path p99: ~100-500ns reduction at trade-close emit
  - Cache footprint: bounded reduction; ~kilobytes per core
  - Maintenance: cleaner cross-owner story (less "where does this field live" confusion)

### Cache-audit-ship → tech-debt closure value

If pursued, the cache audit ship would close substantial latent tech debt:
- TECH_DEBT-NNN: per-slot data scattered (O1)
- TECH_DEBT-NNN: ThompsonBandit SoA layout sub-optimal (O2)
- TECH_DEBT-NNN: cross-cutting padding determinism (O4)
- TECH_DEBT-NNN: EnsembleModelZoo cluster discipline post-mirror-expansion (O5)
- Plus: makes future per-instance field additions cleaner (no "where do I add this?" decision when canonical homes are clearer)

### Should this be a `/cache-audit` or `/hp-audit` skill?

Yes — likely the right shape for future ship discipline. Workflow:
1. Operator captures production profile (perf record + perf report)
2. Operator runs `/cache-audit module:<target>` skill
3. Skill identifies struct fields involved + cluster layout per access pattern
4. Skill proposes layout changes + size_assert verification
5. Skill estimates latency impact
6. Operator triages findings + decides scope

Could be sister to existing `/hft-audit` skill but with cache-layout-specific scope. **Codify as skill spec when cache-audit ship is triggered.** For now, this section + HP_REFACTOR.md content are the seed material for the eventual skill body.

### Anti-premature-optimization reminder

Pursuing cache audit BEFORE:
- Framework progression closes (`.F.4d`/`.F.4e`/`.F.5`)
- Profile data identifies actual bottleneck
- Production budget pressure surfaces

...is **premature optimization**. Cache restructure done speculatively (without profile-driven need) often regresses unexpectedly (cache miss cascade in different access pattern; cluster boundary breaks across future ship). The right ordering: structural settle FIRST, THEN profile-driven optimization.

This is consistent with the "more work now, less work later" principle applied correctly — the "more work now" is FRAMEWORK PROGRESSION (which IS being done now via `.F.4` sprint family). The cache audit is "less work later" THAT COMES AFTER structural settles. Doing it now would invert the order + cost rework.

## Anti-pattern reminder

**DO NOT attempt opportunistic hot-path optimization during framework-discipline ships.** The risk-reward asymmetry favors discipline preservation:
- Framework ship's value = structural correctness + future-leverage
- Hot-path optimization risk = latency budget violation + invariant break + regression surface expansion
- Combined ship's risk surface = product of both = HIGH; combined ship's marginal value = framework value (hot-path optimization wasn't the ship's goal)

The `.F.4c.4` ship (and predecessors) explicitly preserve hot-path UNTOUCHED via:
- `tools/calls_graph_diff.sh verify` at ship close
- HOT_PATH_CHANGELOG: NONE entries when no hot-path changes
- H7 + H8 invariants enforced at code-review

Hot-path optimization is its OWN ship class. This doc captures that scope for when it triggers.

---

**End of HP_REFACTOR.md.** Operational scope-document; not a planned ship. Triggers (production profile data / new latency-sensitive feature / framework stabilization / hardware change) escalate to specific HP-* ships when warranted.
