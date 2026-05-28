---
type: framework-pattern
stage: 3-first-canonical
version: 1.0
established: 2026-05-28
landing_ship: v5.15.5.F.4d.1.E.X
canonical_applications:
  - v5.15.5.F.4d.1.E.X (.so reload + atomic pointer swap with grace period)
sister_specs:
  - framework-patterns/dynamic-library-strategy-loading-pattern.md (sister; loader)
  - refactor-patterns/branchless-dispatch-discipline.md (H20; cached pointer dispatch)
tags: [framework-discipline, hot-reload, dlopen, atomic-swap, grace-period]
surface: [strategy-dispatch, runtime-mutation]
applies_at_skills: [/precoding-audit-gate, /parity-check]
---

# Strategy hot-reload via dlopen pattern

**Pattern intent:** Strategy code lives in .so (shared library). Engine dlopen's at boot; holds function pointer. SIGUSR2 → load NEW .so; atomic_exchange pointer; grace period; dlclose OLD. Per-node hot-path uses cached pointer (H7 branchless preserved).

## Problem statement

Operator needs to update strategy code without engine restart:
- Restart = 5-30s downtime (graceful shutdown + reconcile + resume)
- Open positions persist on Binance; engine must reconcile on restart
- Production-grade operators avoid restart for trivial strategy tweaks

Without hot-reload: restart-only path; substantial overhead.
With hot-reload: ~5ms swap (atomic exchange + grace period).

## Pattern description

### Per-strategy .so build target

```bash
# build.sh extension
build_strategy_lib() {
    local strategy_name=$1
    g++ -shared -fPIC -O3 -march=native \
        -DENGINE_STRATEGY_ABI_VERSION=${ENGINE_STRATEGY_ABI_VERSION} \
        Strategies/${strategy_name^}.hpp \
        -o build/libstrategy_${strategy_name}.so \
        $CXXFLAGS
}

build_strategy_lib "momentum"
build_strategy_lib "ml"
# ... etc
```

### ABI contract (extern "C"; stable across versions)

```cpp
// REQUIRED exported symbols per strategy .so:

extern "C" {
    void* strategy_init(const StrategyParameters<F>* params);
    TradeDecision strategy_evaluate(void* state, const TickContext<F>* tick);
    void strategy_rebuild(void* state, const RebuildContext<F>* rebuild);
    void strategy_close(void* state);

    const char* strategy_name(void);
    const char* strategy_variant_id(void);
    uint32_t strategy_abi_version(void);
}
```

ABI version check on dlopen; refuse load on mismatch.

### Atomic pointer swap with grace period

```cpp
// In NodeState.hot:
alignas(64) struct {
    std::atomic<strategy_evaluate_fn> strategy_evaluate;
    std::atomic<void*> strategy_state;
    std::atomic<uint64_t> tick_counter;        // for grace-period tracking
    void* strategy_dl_handle;
    strategy_close_fn strategy_close_fn;
    uint32_t strategy_variant_id;
} hot;

// Hot path read pattern (branchless; H7 preserved)
TradeDecision NodeHotPath_Evaluate(NodeState<F>& node, const TickContext<F>& tick) {
    node.hot.tick_counter.fetch_add(1, std::memory_order_relaxed);  // for grace period
    strategy_evaluate_fn evaluate = node.hot.strategy_evaluate.load(std::memory_order_acquire);
    void* state = node.hot.strategy_state.load(std::memory_order_acquire);
    return evaluate(state, &tick);  // function call; branchless
}

// Hot-reload sequence (in slow-path context)
void NodeSlowPath_HandleSIGUSR2_StrategyReload(NodeState<F>& node, const char* new_so_path) {
    // Phase 1: Load NEW .so
    StrategyHandle new_handle;
    if (StrategyLoader_Load(new_so_path, &new_handle) != 0) return;

    // Phase 2: ABI version check
    if (new_handle.abi_version_fn() != ENGINE_STRATEGY_ABI_VERSION) {
        StrategyLoader_Unload(&new_handle);
        return;
    }

    // Phase 3: Initialize new strategy
    new_handle.per_node_state = new_handle.init_fn(&node.hot.params);
    if (!new_handle.per_node_state) {
        StrategyLoader_Unload(&new_handle);
        return;
    }

    // Phase 4: Save OLD for cleanup
    StrategyHandle old_handle = {};
    old_handle.dl_handle = node.hot.strategy_dl_handle;
    old_handle.evaluate_fn = node.hot.strategy_evaluate.load();
    old_handle.close_fn = node.hot.strategy_close_fn;
    old_handle.per_node_state = node.hot.strategy_state.load();

    // Phase 5: ATOMIC SWAP (hot path sees NEW from next tick)
    node.hot.strategy_evaluate.store(new_handle.evaluate_fn, std::memory_order_release);
    node.hot.strategy_state.store(new_handle.per_node_state, std::memory_order_release);
    node.hot.strategy_dl_handle = new_handle.dl_handle;
    node.hot.strategy_close_fn = new_handle.close_fn;
    node.hot.strategy_variant_id = new_handle.variant_id_fn();

    // Phase 6: Grace period (wait 2 ticks; hot path guaranteed to see new pointer)
    WaitForGracePeriod(node, /*tick_count=*/2);

    // Phase 7: Clean up OLD
    old_handle.close_fn(old_handle.per_node_state);
    dlclose(old_handle.dl_handle);

    LOG_INFO("Strategy hot-reload complete: node=%u, variant=%s",
             node.binding.subaccount_id, new_handle.variant_id_fn());
}

void WaitForGracePeriod(NodeState<F>& node, uint32_t tick_count) {
    uint64_t baseline = node.hot.tick_counter.load();
    while (node.hot.tick_counter.load() < baseline + tick_count) {
        usleep(100);
    }
}
```

### State preservation across swap

What's preserved (engine-owned):
- Per-node Position state (NodeState.drainer_state.orders)
- Per-node CoreContext (NodeState.slow_account; P&L; balance)
- Per-cluster shared state
- Aggregator state

What's reset (strategy-owned; in .so):
- Strategy internal state (EMA values; bandit arms; ML caches)
- Variant_id changes

Optional preservation via strategy_state_serialize/deserialize (per `.E.X` plan body); for power-user strategies.

### fox-cli verbs

```bash
fox-cli model-swap binance/node_0 --to build/libstrategy_momentum_v2.so
fox-cli reload-strategy momentum --new-binary build/libstrategy_momentum_v2.so
fox-cli rollback-strategy binance/node_0   # revert to previous variant
```

## Stage progression criteria

- **Stage 3 first canonical** (`.E.X`): hot-reload via dlopen implemented
- **Stage 4 cohort** (when 2nd application: e.g., model-only swap via mmap): pattern proven
- **Stage 5 CLAUDE.md** (3rd application): promoted

## Anti-patterns avoided

- **Restart for every strategy update** — downtime overhead
- **Premature dlclose** (UAF) — grace period required
- **Branchy hot-path strategy dispatch** — H7 violation; cached pointer preserves branchless

## Cross-references

- Sister: `framework-patterns/dynamic-library-strategy-loading-pattern.md` (loader; ABI contract)
- Parent: `refactor-patterns/branchless-dispatch-discipline.md` (H20)
- First application: `plans/v5.15-live-readiness/subplans/2026-05-28-v5.15.5.F.4d.1.E.X-strategy-hot-reload.md`
