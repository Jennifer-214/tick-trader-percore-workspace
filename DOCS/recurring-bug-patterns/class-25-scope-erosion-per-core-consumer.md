---
type: ledger-template
class_id: 25
title: Scope-erosion in per-core consumer function (registry says per-core; consumer reads from wrong scope)
parent_index: DOCS/RECURRING_BUG_PATTERNS.md
established: 2026-05-18
---

## Class 25 — Scope-erosion in per-core consumer function (registry says per-core; consumer reads from wrong scope)

**Detected:** 2026-05-15 (during v5.15.5.F.4c.3 Step 2 `_BuildParameters` migration scoping; caught BEFORE the bug shipped).
**Severity:** HIGH — per-core configuration set by operator silently ignored; behavior diverges from cfg surface invisibly.

### Recurring symptom

Per-core capability is correctly classified in `FOREACH_PER_CORE_CFG_FIELD` and present on `PerCoreCfg<F>` cores[c]. Operator sets `cfg.cores[2].take_profit_pct = 5.0` via Settings panel — value persists, reload reflects it correctly in the Settings UI for core 2.

But the CONSUMER function (e.g., `SimpleDip_BuildParameters`) takes `const ControllerConfig<F>* config` and reads `config->take_profit_pct` — which is the FLAT/GLOBAL field, or core 0's value, or a stale pre-`.F.4c.3` value depending on what the shadow-migration window is doing. Cores 1-15 silently use the wrong value.

The cfg surface CORRECTLY exposes the capability; the EXECUTION code doesn't honor scope. This is distinct from Class 24 (capability not surfaced) — here capability IS surfaced but consumer reads from wrong scope.

### Root cause

A consumer function that takes the FULL `const ControllerConfig<F>*` (or `const ControllerConfig<F>&`) when it's called per-core has access to BOTH:
- The flat / "global" field path: `config->take_profit_pct` (legacy or stale)
- The per-core path: `config->cores[c].take_profit_pct` (correct)

Author writes `config->take_profit_pct` because it's shorter, the field name is in scope, the compiler accepts it. The per-core slice is bypassed entirely. The compile succeeds; the test on core 0 passes (since `cores[0].take_profit_pct == config->take_profit_pct` under the shadow-sync window); only multi-core runtime divergence reveals the bug.

The full-cfg pointer is the discipline boundary failure. Once a per-core consumer can see the global cfg, it can lazily reach for the wrong field.

### Structural fix

**Per-core consumer functions take `const PerCoreCfg<F>*` (single-param), NEVER `const ControllerConfig<F>*`.** Globals (when genuinely needed by a per-core consumer, e.g., `poll_interval` for tick→time conversion) are caller-resolved as scalar args.

```cpp
// CORRECT
SimpleDip_BuildParameters(const RollingStats<F>* rolling,
                            const PerCoreCfg<F>* core_cfg,    // <-- per-core slice ONLY
                            FPN<F> allocated_balance,
                            GateParameters<F>* out, ...);

ML_BuildParameters(..., const PerCoreCfg<F>* core_cfg, ..., int poll_interval_arg);
                                                          // ^ scalar global, caller-resolved

// FORBIDDEN
SimpleDip_BuildParameters(const RollingStats<F>* rolling,
                            const ControllerConfig<F>* config,   // <-- WRONG; full cfg
                            ...);

// FORBIDDEN — two-param "convenience" sig silently re-introduces the anti-pattern
SimpleDip_BuildParameters(..., const ControllerConfig<F>* config,
                                const PerCoreCfg<F>* core_cfg, ...);
                       // ^ never do this; `config->X` lazy reads return for whoever ships next
```

The discipline: there is NO PATH for a per-core consumer to read the global cfg pointer. Per-core reads MUST go through `core_cfg->X`. Genuinely-global reads happen at the CALLER (which has the full cfg), are pre-resolved to scalar values, passed as explicit args. The consumer signature itself is the structural enforcement — the type system makes the wrong access non-expressible.

Closed at `v5.15.5.F.4c.3` WIP2c.2 — first canonical application; 5 strategy fns + 1 dispatcher migrated to single-param sigs; `poll_interval` extracted as scalar arg in `ML_BuildParameters`.

### Prevention (going-forward rule + audit)

Codified at `DESIGN_SPECS/refactor-patterns/cfg-scope-discipline.md` § "Consumer function signatures over per-core slices" (NEW at `.F.4c.3`).

> **Per-core consumer functions take `const PerCoreCfg<F>*` (single-param), NEVER `const ControllerConfig<F>*`.** Genuinely-global reads are caller-resolved as scalar args. Two-param sigs `(const ControllerConfig<F>* config, const PerCoreCfg<F>* core_cfg)` are FORBIDDEN — they silently re-introduce the anti-pattern.

Anti-pattern grep signatures (for `/dod-audit` + `/bug-check` integration):

```bash
# A1: Consumer fn (per-core sig family) taking ControllerConfig<F>*
rg -n "(BuildParameters|_Tick|_Adapt|_Rebuild|_Step)\(.*const ControllerConfig<F>\*" --type cpp

# A2: Per-core fn with `core_cfg` param ALSO reading `config->` (mixed-scope erosion)
rg -nP "(?s)PerCoreCfg<F>\*.*?config->[a-z_]+" --multiline --type cpp
```

Documented exemptions (false-positives):
- `ControllerConfig_ResolveForCore` — the resolver itself; producing per-core view from full cfg by design. (Deleted at `.F.4c.3` Step 2 end anyway.)
- `ControllerConfig_NormalizeForMode` — operates on whole cfg by design (mode-flip normalize pass).
- Boot-time engine init paths — full cfg needed for multi-core setup.

### .F.4d sweep extension (2026-05-16)

Sweep extended to OMS consumer surface at `v5.15.5.F.4d` MERGED. `PerCoreCfg<F>*` single-param sig threaded through reward-attribution path: `TickRewardsFromLookback` + `TradeCloseReward` + `ControllerEventLoop` exit-side. Same discipline as `.F.4c.3` WIP2c.2 first canonical — per-core consumer functions take `const PerCoreCfg<F>*` only; full `ControllerConfig` pointer never reaches per-core execution code. Two-param convenience sigs (`const ControllerConfig<F>*, const PerCoreCfg<F>*`) remain FORBIDDEN.

### Related classes

- **Class 24** (Capability-cfg surface mismatch) — sister at SURFACE layer (capability not exposed in cfg). Class 25 is at EXECUTION layer (capability exposed but execution doesn't honor scope). Both close structurally at `.F.4c.3` via the cfg-scope-discipline + single-param consumer convention.
- **Class 18** (Mirror-incomplete) — same family of "all surfaces must update together"; Class 25 is the specific consumer-side variant.
- **Class 23** (Type-erased dispatch) — same `.F.4c` ship's anti-pattern; both are "scope or type erosion through a pointer that's too broad"; structural fix is narrowing the pointer's type (tt:: namespace for type; PerCoreCfg<F>* for scope).

### Cross-references

- `DESIGN_SPECS/refactor-patterns/cfg-scope-discipline.md` § "Consumer function signatures over per-core slices" — full discipline definition
- `DESIGN_SPECS/framework-patterns/per-instance-registry-pattern.md` — per-core registry (Class 25 applies to all per-instance axes)
- `Strategies/StrategyParameters.hpp` (post-v5.15.5.F.4c.3) — canonical 5-fn application
- CLAUDE.md item 31 — framework discipline meta-principle
