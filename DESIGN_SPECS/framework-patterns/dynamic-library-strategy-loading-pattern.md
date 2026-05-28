---
type: framework-pattern
stage: 3-first-canonical
version: 1.0
established: 2026-05-28
landing_ship: v5.15.5.F.4d.1.E.X
canonical_applications:
  - v5.15.5.F.4d.1.E.X (StrategyLoader; dlopen/dlsym/dlclose; ABI version)
sister_specs:
  - framework-patterns/strategy-hot-reload-via-dlopen-pattern.md (sister; atomic swap discipline)
tags: [framework-discipline, dlopen, abi-versioning, strategy-loader]
surface: [strategy-loading]
---

# Dynamic library strategy loading pattern

**Pattern intent:** Codify dlopen + dlsym + ABI version check for strategy .so loading. Sister to `strategy-hot-reload-via-dlopen-pattern.md` (this spec covers LOADING; sister covers atomic swap with grace period).

## Pattern description

```cpp
struct StrategyHandle {
    void* dl_handle;
    strategy_init_fn init_fn;
    strategy_evaluate_fn evaluate_fn;
    strategy_rebuild_fn rebuild_fn;
    strategy_close_fn close_fn;
    strategy_name_fn name_fn;
    strategy_variant_id_fn variant_id_fn;
    strategy_abi_version_fn abi_version_fn;

    // Optional exports
    strategy_serialize_fn serialize_fn;          // NULL if not implemented
    strategy_deserialize_fn deserialize_fn;

    void* per_node_state;
    char source_path[256];
    uint64_t loaded_at_us;
};

int StrategyLoader_Load(const char* so_path, StrategyHandle* handle) {
    handle->dl_handle = dlopen(so_path, RTLD_NOW | RTLD_LOCAL);
    if (!handle->dl_handle) {
        LOG_ERROR("dlopen %s failed: %s", so_path, dlerror());
        return -1;
    }

    // Resolve required symbols
    handle->init_fn = (strategy_init_fn)dlsym(handle->dl_handle, "strategy_init");
    handle->evaluate_fn = (strategy_evaluate_fn)dlsym(handle->dl_handle, "strategy_evaluate");
    handle->rebuild_fn = (strategy_rebuild_fn)dlsym(handle->dl_handle, "strategy_rebuild");
    handle->close_fn = (strategy_close_fn)dlsym(handle->dl_handle, "strategy_close");
    handle->name_fn = (strategy_name_fn)dlsym(handle->dl_handle, "strategy_name");
    handle->variant_id_fn = (strategy_variant_id_fn)dlsym(handle->dl_handle, "strategy_variant_id");
    handle->abi_version_fn = (strategy_abi_version_fn)dlsym(handle->dl_handle, "strategy_abi_version");

    // Verify required symbols
    if (!handle->init_fn || !handle->evaluate_fn || !handle->rebuild_fn ||
        !handle->close_fn || !handle->abi_version_fn) {
        LOG_ERROR("strategy .so missing required symbols");
        dlclose(handle->dl_handle);
        return -2;
    }

    // Resolve OPTIONAL symbols
    handle->serialize_fn = (strategy_serialize_fn)dlsym(handle->dl_handle, "strategy_state_serialize");
    handle->deserialize_fn = (strategy_deserialize_fn)dlsym(handle->dl_handle, "strategy_state_deserialize");

    // ABI version check
    uint32_t so_abi = handle->abi_version_fn();
    if (so_abi != ENGINE_STRATEGY_ABI_VERSION) {
        LOG_ERROR("ABI mismatch: engine=%u, so=%u", ENGINE_STRATEGY_ABI_VERSION, so_abi);
        dlclose(handle->dl_handle);
        return -3;
    }

    strncpy(handle->source_path, so_path, sizeof(handle->source_path) - 1);
    handle->loaded_at_us = NowUs();
    return 0;
}

void StrategyLoader_Unload(StrategyHandle* handle) {
    if (handle->per_node_state) {
        handle->close_fn(handle->per_node_state);
    }
    if (handle->dl_handle) {
        dlclose(handle->dl_handle);
    }
    memset(handle, 0, sizeof(StrategyHandle));
}
```

## ABI version discipline

```cpp
// In Limits.hpp:
#define ENGINE_STRATEGY_ABI_VERSION 1

// Bumped on:
// - NEW required symbol added
// - Existing symbol signature changed
// - Semantic change in contract (NOT signature change)
```

When bumping: existing .so files refuse to load until rebuilt. Operator workflow: rebuild strategy .so via `build.sh strategies`.

## Cross-references

- Sister: `framework-patterns/strategy-hot-reload-via-dlopen-pattern.md`
- First application: `plans/v5.15-live-readiness/subplans/2026-05-28-v5.15.5.F.4d.1.E.X-strategy-hot-reload.md`
