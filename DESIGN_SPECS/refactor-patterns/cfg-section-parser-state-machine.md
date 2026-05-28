---
type: refactor-pattern
stage: 2-draft
version: 1.0
established: 2026-05-15
tags: [framework-discipline, structural-fix]
surface: [cfg-flow, parser]
sister_specs: [universal-cfg-field-registry-pattern.md, cfg-scope-discipline.md]
applies_at_skills: []
---

# Cfg section parser state machine

**Stage:** Stage 2 DRAFT v1.0 (drafted ahead of first canonical application at v5.15.5.F.4c.3)
**Promotes to:** Stage 3 ACTIVE v1.0 at `.F.4c.3` ship close
**Sister specs:** `per-instance-registry-pattern.md` (the per-instance axis this parser dispatches into), `multi-action-registry-walker-family.md` (the PARSE action this state machine drives)

---

## Summary

When a cfg file holds N per-instance registries' worth of rows (per-node trading config + per-symbol cfg + per-strategy cfg + ...) plus a global section, parse via an INI-style `[section name]` state machine. Lines before any section header parse against the global registry; lines inside `[<axis> <instance>]` headers parse against the per-instance registry of that axis. Unknown keys produce explicit ERRORS with migration hints (no silent fallback). The state machine is reusable across all per-instance axes — adding a new axis = 1 new section-header recognizer + parse-state value.

## When to apply

Apply when:
- Cfg file structure has ≥2 scopes (one global + one or more per-instance axes)
- Per-instance instances are bounded + enumerable (e.g., cores 0..15, symbols from a validated list)
- Operator clarity matters more than cfg-file brevity (explicit `[core N]` sections > sparse `core_N_<key>=` prefix scan)
- Hard-break of legacy single-scope syntax is acceptable (no backward-compat shim layer)

Skip when:
- Cfg file is single-scope (no per-instance axes; everything is global)
- Backward-compat with sparse-prefix syntax (`core_0_take_profit_pct=`) is required indefinitely
- Cfg file is machine-generated only (operator never edits; tooling can use any format)

## Pattern shape

### Parse state enum

```cpp
enum class ParseScope {
    GLOBAL,               // lines before any [section] header
    PER_CORE,             // lines inside [core N] section
    // Future axes:
    // PER_SYMBOL,        // [symbol BTCUSDT]
    // PER_STRATEGY,      // [strategy MOMENTUM]
    // PER_HORIZON,       // [horizon 1000]
    // PER_REGIME,        // [regime TRENDING]
};

struct ParseState {
    ParseScope scope;
    int active_instance_idx;       // core idx, symbol idx, etc.
    char active_instance_name[64]; // for error messages ("core 2", "symbol BTCUSDT")
};
```

### State machine

```cpp
ParseState state = { ParseScope::GLOBAL, -1, "" };

while (read_line(file, line)) {
    // Trim whitespace; skip blank/comment lines
    if (is_blank_or_comment(line)) continue;
    
    // Section header detection: line matches `[<axis> <instance>]`
    if (line[0] == '[') {
        ParseScope new_scope;
        int new_instance_idx;
        char new_instance_name[64];
        
        if (parse_section_header(line, &new_scope, &new_instance_idx, new_instance_name)) {
            // Validate: [core N] where N >= num_execution_cores produces WARN + skip-section
            // Validate: duplicate [core 0] produces ERROR
            // Validate: unknown axis ([foo 1]) produces ERROR with migration hint
            state.scope = new_scope;
            state.active_instance_idx = new_instance_idx;
            strncpy(state.active_instance_name, new_instance_name, sizeof(state.active_instance_name) - 1);
            continue;
        }
        emit_error("malformed section header: %s", line);
        continue;
    }
    
    // Key=value line: parse against current scope's registry
    char key[128], value[512];
    if (!parse_kv_line(line, key, value)) {
        emit_error("malformed line: %s", line);
        continue;
    }
    
    // Dispatch to scope's registry parser
    switch (state.scope) {
        case ParseScope::GLOBAL:
            if (!parse_against_registry(cfg, g_global_cfg_field_descriptors,
                                         GLOBAL_FIELD_IDX_END, key, value)) {
                emit_error_with_migration_hint(key, "global", expected_scope_for_key(key));
            }
            break;
        case ParseScope::PER_CORE:
            if (!parse_against_registry(cfg.cores[state.active_instance_idx],
                                         g_per_core_cfg_field_descriptors,
                                         PER_CORE_FIELD_IDX_END, key, value)) {
                emit_error_with_migration_hint(key, "per-core", expected_scope_for_key(key));
            }
            break;
        // Future axes...
    }
}
```

### Migration hint emission

```cpp
void emit_error_with_migration_hint(const char* key, const char* current_scope, const char* expected_scope) {
    fprintf(stderr, "[cfg] ERROR: key '%s' is not valid at scope '%s'. ", key, current_scope);
    if (expected_scope) {
        fprintf(stderr, "It moved to '%s' scope at v5.15.5.F.4c.3. ", expected_scope);
        fprintf(stderr, "Place under the appropriate section header. ");
    }
    fprintf(stderr, "See workspace/DOCS/CFG_SCOPE_MIGRATION_GUIDE.md for migration steps.\n");
}

const char* expected_scope_for_key(const char* key) {
    // Walk both registries; if key is found in one, return that scope's name.
    for (size_t i = 0; i < GLOBAL_FIELD_IDX_END; ++i) {
        if (strcmp(key, g_global_cfg_field_descriptors[i].cfg_field_name) == 0) return "global";
    }
    for (size_t i = 0; i < PER_CORE_FIELD_IDX_END; ++i) {
        if (strcmp(key, g_per_core_cfg_field_descriptors[i].cfg_field_name) == 0) return "per-core";
    }
    return nullptr;  // truly unknown — operator typo or deprecated key
}
```

### Section header recognizer

```cpp
// Matches "[<axis> <instance>]" patterns.
// Examples: "[core 0]", "[symbol BTCUSDT]", "[strategy MOMENTUM]".
bool parse_section_header(const char* line, ParseScope* out_scope,
                          int* out_instance_idx, char* out_instance_name) {
    if (line[0] != '[') return false;
    
    char axis[32], instance[64];
    if (sscanf(line, "[%31s %63[^]]]", axis, instance) != 2) return false;
    
    if (strcasecmp(axis, "core") == 0) {
        *out_scope = ParseScope::PER_CORE;
        *out_instance_idx = atoi(instance);
        snprintf(out_instance_name, 64, "core %d", *out_instance_idx);
        return true;
    }
    
    // Future axes: symbol / strategy / horizon / regime
    
    return false;  // unknown axis
}
```

## Composition with other patterns

- **`per-instance-registry-pattern.md`** — the section parser dispatches into a per-instance registry; each section header advances state to a specific instance of that axis.
- **`multi-action-registry-walker-family.md`** — the PARSE action body is consumed via the walker template; the state machine drives which target struct + which registry the walker uses.
- **`type-trait-dispatch-via-tt-namespace.md`** — `tt::cfg_parse_field<T>` is the per-row parse primitive consumed by `parse_against_registry`.
- **`cfg-scope-discipline.md`** — the migration hint surface relies on scope discipline: every key has ONE correct scope (no field appears in both registries).

## First canonical application — v5.15.5.F.4c.3

`engine.cfg` parses with this state machine:

```
# Global section (no header — defaults at top)
num_execution_cores=4
engine_mode=sharded
trading_mode=paper

[core 0]
strategy=ml
risk_pct=15.0
take_profit_pct=3.0

[core 1]
strategy=ml
risk_pct=10.0
take_profit_pct=2.5
```

Error scenarios:
- `take_profit_pct=3.0` BEFORE any `[core N]` header → ERROR with migration hint "take_profit_pct moved to per-node; place under [core 0] section. See CFG_SCOPE_MIGRATION_GUIDE.md."
- `num_execution_cores=4` INSIDE a `[core 0]` section → ERROR "num_execution_cores is global; place at top of file before any section header."
- `[core 5]` with `num_execution_cores=4` → WARN + skip section ("core 5 cfg present but engine runs 4 cores; ignoring").
- Duplicate `[core 0]` → ERROR ("section [core 0] already defined").
- Unknown axis `[foo 1]` → ERROR ("unknown axis 'foo'; expected: core").

## Anticipated future applications

| Axis | Section syntax | Future ship |
|---|---|---|
| Per-symbol | `[symbol BTCUSDT]` | Multi-symbol DataStream ship |
| Per-strategy | `[strategy MOMENTUM]` | Per-strategy hyperparameter cfg ship |
| Per-horizon | `[horizon 1000]` | Per-horizon ensemble cfg ship |
| Per-regime | `[regime TRENDING]` | Regime-specific tuning ship |
| Per-bandit-arm | `[arm 0]` | Per-arm parameter override ship |

Each new axis adds:
1. ParseScope enum value
2. Section header recognizer entry (1 strcmp in `parse_section_header`)
3. switch case in the parser main loop
4. (Optional) cohort discipline note in `cfg-scope-discipline.md`

## Anti-patterns to avoid

- **Silent fallback on unknown keys.** A typo'd key (`takee_profit_pct=3.0`) must produce an explicit ERROR, NOT silently default to nothing. Operator's intent is observable; rejection forces correction.
- **Cross-registry name collisions handled by "try both registries."** A key existing in BOTH registries indicates scope-discipline violation. The parser must NOT silently route to whichever registry matches first. Use `cfg-scope-discipline.md` to ensure no cross-registry name collision exists at the registry level; the parser then has unambiguous dispatch.
- **Section header parse ambiguity.** Lenient parsing (`[core0]`, `[core_0]`, `[core 0]` all accepted) creates operator confusion. Pick ONE canonical syntax (`[<axis> <instance>]` with single space) + reject all others with clear error messages.
- **State reset on every section header read.** The parser must validate that `active_instance_idx` is within bounds BEFORE writing to `cfg.cores[idx].<field>` — out-of-bounds index = silent memory corruption otherwise.
- **Migration hints that don't reference the migration guide.** Every ERROR message names `CFG_SCOPE_MIGRATION_GUIDE.md` so operator has a recovery path.

## Reference implementations

(Populates at Stage 3 ACTIVE — shipped sites get file:line refs back-linked here.)

- (pending) `CoreFrameworks/ControllerConfig.hpp` — cfg parser state machine implementation (post `.F.4c.3`)
- (pending) `workspace/DOCS/CFG_SCOPE_MIGRATION_GUIDE.md` — migration guide referenced in error messages

## Cross-references

- `DESIGN_SPECS/framework-patterns/per-instance-registry-pattern.md` — per-instance axis this parser dispatches into
- `DESIGN_SPECS/framework-patterns/multi-action-registry-walker-family.md` — PARSE action this state machine drives
- `DESIGN_SPECS/refactor-patterns/cfg-scope-discipline.md` — scope discipline that prevents cross-registry name collisions
- `DESIGN_SPECS/framework-patterns/type-trait-dispatch-via-tt-namespace.md` — `tt::cfg_parse_field<T>` per-row parse primitive
- `DESIGN_SPECS/meta-disciplines/pattern-codification-lifecycle.md` — workflow
- CLAUDE.md item 31 — framework discipline meta-principle

---

**Stage 2 DRAFT v1.0 — committed 2026-05-15 ahead of `.F.4c.3` ship.** Promotes to Stage 3 ACTIVE v1.0 at ship close once the `engine.cfg` parser state machine implementation lands.
