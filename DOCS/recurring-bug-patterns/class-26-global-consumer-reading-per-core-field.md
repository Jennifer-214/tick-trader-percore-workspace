---
type: ledger-template
class_id: 26
title: Global consumer reading per-core field (silently flattens to one core's value at read time)
parent_index: DOCS/RECURRING_BUG_PATTERNS.md
established: 2026-05-19
surface_tags: [cfg-flow, slow-path, hot-path, oms-drainer, ml-inference]
severity: high
recurrence_count: 11
first_instance: v5.15.5.F.4c.3 (Class 27 codification surfaced sister)
closure_mechanism: decision-time-data-binding-pattern (read from in-flight Order/Position/Event at decision time, not from cfg) + cfg-scope-discipline (per-core fields read via core_id index, never as a scalar) + tools/check_per_core_registry_integrity.py CI check
sister_classes: [18, 24, 25, 27]
---

# Class 26 — Global consumer reading per-core field (silently flattens to one core's value at read time)

**Detected:** 2026-05-15 (surfaced as sister to Class 27 during v5.15.5.F.4c.3 OMS fee_rate per-core analysis).
**Severity:** HIGH — silent accounting / inference / risk divergence; the consumer SEES a per-core field but ACTS as if it were global; per-instance distinction lost at read time.

## Recurring symptom

A consumer reads a per-core cfg field WITHOUT a core_id index, treating it as a scalar. Common shapes:

```cpp
// WRONG: reads core 0's fee_rate; cores 1-N's fee_rate ignored
FPN<F> fee = cfg.cores[0].fee_rate_maker;       // implicit "use core 0 value"
// OR
FPN<F> fee = cfg.cores[c].fee_rate_maker;        // c hardcoded somewhere upstream

// WRONG: reads the FIRST cfg entry that matches a name; flattens
for (auto& entry : cfg_entries) {
    if (entry.name == "fee_rate") return entry.value;  // returns core 0's value
}
```

Distinguishing from Class 27 (single-value cache flattens per-instance):
- **Class 27** is at CACHE STRUCTURE — subsystem state has a SCALAR field that mirrors cfg; the cache itself has no per-instance dimension. Pre-resolution required.
- **Class 26** is at READ TIME — cfg HAS per-core dimension, but the consumer reads it AS IF it were scalar. The structural data is right; the access pattern is wrong.

Same root family ("subsystem-state mirror of per-instance cfg") but Class 27 is the structural pre-condition that makes Class 26 silent. Eliminating Class 27 sources (per `DESIGN_SPECS/refactor-patterns/decision-time-data-binding-pattern.md`) eliminates many Class 26 sites by construction.

## Why this is a class (not a one-off bug)

Per-core cfg access without core_id index recurs at every consumer that wasn't authored with per-core consciousness:
- Hot path consumers (BG_Evaluate / SG_Evaluate) reading "the" fee_rate or risk_pct
- ML inference reading "the" confidence_threshold_scale
- OMS drainer reading "the" slippage_pct at fill time
- GUI panels rendering "the" cfg field

Each consumer's access pattern is small + correct-looking. The drift is INVISIBLE in the consumer's own code review (looks like normal cfg access). Surfaces only when:
- Per-core cores are configured DIFFERENTLY
- One instance shows divergent behavior from another
- Accounting + ML invariants drift cross-core

## False-positive surface (per M3 discipline)

Not all scalar cfg access is Class 26:
- Boot-time reads (cores haven't been initialized yet; cfg is the canonical scalar source) — NOT Class 26
- Pre-resolved decision-time reads (Order has fee_rate captured at submit; reading order.fee_rate is correct) — NOT Class 26
- Genuinely-global cfg fields (engine_arch, log_level, paper_test_mode) — NOT Class 26
- Read inside per-core thread context where core_id is implicit (per-core slow-path body) — NOT Class 26 (the core_id IS implicit-but-correct)

## Closure mechanism

**Structural fix** per `DESIGN_SPECS/refactor-patterns/decision-time-data-binding-pattern.md` + `DESIGN_SPECS/refactor-patterns/cfg-scope-discipline.md`:

1. **Decision-time binding (preferred):** capture the per-core cfg value onto the in-flight Order / Position / Event / TradeEvent at decision time. Downstream consumers read from the object directly; no cfg access needed at fill/evaluation time. This eliminates Class 26 at all downstream sites by construction.

2. **Explicit core_id at read site:** when read isn't bound to an in-flight object (e.g., slow-path strategy adapt), thread core_id through the call chain + read `cfg.cores[core_id].field`. The core_id is a function parameter, not implicit/hardcoded.

3. **CI verification:** `tools/check_per_core_registry_integrity.py` Check 7 verifies per-core cfg fields are accessed via core_id index, not as scalars. Same CI as Class 27 (paired discipline).

4. **Audit support:** `/accounting-audit` + `/registry-fit-audit` scan for the access pattern.

## Worked instances

- **v5.15.5.F.4c.3 (2026-05-15):** Class 26 surfaced as sister to Class 27 during OMS fee_rate per-core analysis. OMS drainer's `FillEvent.fee_rate` access pattern was reading via core 0 because the per-core fee_rate cohort hadn't been threaded through the OMS event path. Closure landed v5.15.5.F.4d.1.A.7 via decision-time binding on `Order::pre_resolved.fee_rate_maker / fee_rate_taker` (captured at submit; OMS reads from Order at fill).

- **v5.15.5.F.4d.1.B.4 v1.7.6 (2026-05-27) — MANDATORY structural fix threshold met (10 NEW worked instances at single cycle):** Phase Cx-cfg-cohort closure of categorization-error cohort. 9 fields with per-core registry membership but GLOBAL_ONLY production readers (consumers reading `config->X` global form despite per-core registry); per-core auto-gen was dead code; categorization-error per audit verification.

  Closed via Phase Cx-D extension + Cx-T/U H14 migration at WIP-16 atomic commit `b8bba2b`:

  1. **enable_mtm_kill_switch** — was per-core registry uint32_t scalar; H14 violation (BOOL semantic). Migrated to MASK_RISK_CFG_MTM_KILL_SWITCH_ENABLED bit in risk_cfg_flags bitmap. Cx-T.
  2. **sl_cooldown_adaptive** — was per-core registry BOOL int scalar; H14 violation. Migrated to MASK_RISK_CFG_SL_COOLDOWN_ADAPTIVE_ENABLED bit in risk_cfg_flags bitmap. Cx-U.
  3. **kill_recovery_warmup** — was per-core registry uint32_t. Migrated to FOREACH_GLOBAL_CFG_FIELD with INT(50) operational default; consumer at PortfolioController.hpp:549 + EngineTUI.hpp:615 already reads global pointer. Cx-D extension.
  4. **sl_cooldown_base** — same shape. Migrated to FOREACH_GLOBAL_CFG_FIELD with INT(2). Cx-D extension.
  5. **sl_cooldown_extra** — same. INT(8). Cx-D extension.
  6. **sl_cooldown_cycles** — was per-core registry; CORRECTLY identified as drainer-uniform (EventLoop_DrainPostFill scalar dispatch architectural limit). Migrated to FOREACH_GLOBAL_CFG_FIELD with INT(5). Cx-D extension.
  7. **idle_reset_cycles** — same shape as kill_recovery_warmup. Migrated to FOREACH_GLOBAL_CFG_FIELD with INT(30). Cx-D extension.
  8. **model_max_age_hours** — same shape. Migrated to FOREACH_GLOBAL_CFG_FIELD with INT(0). Cx-D extension.
  9. **lazy_rebuild_price_threshold_pct** — was per-core registry FPN<F>. Migrated to FOREACH_GLOBAL_CFG_FIELD with DBL(0.0005) (tt::cfg_assign_field<FPN<F>> dispatch handles conversion). Cx-D extension.
  10. **regime_hysteresis** — partial Class 26 closure (cosmetic): legacy single_core PortfolioController.hpp:358/:2023 readers migrated from global `config.regime_hysteresis` to `config.cores[0].regime_hysteresis` for sister-convention consistency with SHARDED canonical at EngineCommon.hpp:199. Value-equivalent via walker propagation. Cx-A.

**Discipline-installation transition:** recurrence_count 1→11 hits MANDATORY structural fix threshold per `pattern-codification-lifecycle.md` Stage 3→4 promotion criteria. Closure mechanism: 4-category cfg field categorization decision tree at NEW `framework-patterns/cfg-field-categorization-discipline.md` Stage 2 DRAFT (PER_CORE_MODE_NO_FLAT_FIELD vs PER_CORE_FLAT_SYNC_PARAMETER vs GLOBAL_ONLY vs CFG-FLAG BITMAP BIT); 5-step re-categorization migration procedure; CI Check 8 + 5-question /consumer-pattern-verify mechanical check (M7 4th canonical structural enforcement). Sister to `feedback_cfg_field_categorization_at_registry_add_time` + `feedback_categorize_by_consumer_pattern_not_field_name` operator-collaboration memories codified at v1.7.6 cycle.

## Sister classes

- **Class 27** (Single-value cache flattens per-instance) — structural pre-condition; cache has no per-instance dimension. Eliminating Class 27 sources eliminates many Class 26 sites by construction.
- **Class 24** (Capability cfg surface mismatch) — sister at the cfg-flow layer; capability cfg added but consumer doesn't see per-core dimension.
- **Class 25** (Scope erosion / per-core consumer) — sister at consumer-discipline layer.
- **Class 18** (Mirror-incomplete) — parent family; Class 26 is one instance shape of "mirror missing per-instance dimension."

## Cross-references

- `DESIGN_SPECS/refactor-patterns/decision-time-data-binding-pattern.md` (closure mechanism)
- `DESIGN_SPECS/refactor-patterns/cfg-scope-discipline.md` (per-core access discipline)
- `tools/check_per_core_registry_integrity.py` Check 7 (CI enforcement; paired with Class 27)
- Class 27 sub-file (sister class with detailed structural-cache discussion)
- `/accounting-audit` skill (scans for Class 26 + Class 27 instances in accounting paths)
- `/registry-fit-audit` skill (scans for Class 26 + Class 27 instances at registry boundaries)
