---
type: ledger-template
class_id: 26
title: Global consumer reading per-core field (silently flattens to one core's value at read time)
parent_index: DOCS/RECURRING_BUG_PATTERNS.md
established: 2026-05-19
surface_tags: [cfg-flow, slow-path, hot-path, oms-drainer, ml-inference]
severity: high
recurrence_count: 17
first_instance: v5.15.5.F.4c.3 (Class 27 codification surfaced sister)
sub_shapes:
  - A (WRONG-INDEX paired-access; `cfg.core_overrides[X]` + `cfg.cores[Y]` with X != Y; Check 9 catches mechanically at .B.7)
  - B (UNINDEXED-GLOBAL at per-core consumer site; `cfg.X` / `cfg->X` / `resolved_cfg.X` UNINDEXED on per-core-with-global-sister fields; Check 10 catches mechanically at .B.8)
closure_mechanism: decision-time-data-binding-pattern (read from in-flight Order/Position/Event at decision time, not from cfg) + cfg-scope-discipline (per-core fields read via core_id index, never as a scalar) + tools/check_per_core_registry_integrity.py CI Check 9 (sub-shape A paired-access mismatch) + CI Check 10 (sub-shape B UNINDEXED-GLOBAL detection)
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

- **v5.15.5.F.4d.1.B.7 (2026-05-27) — 2 NEW worked instances at drainer body (sub-shape A paired-access surface; Check 9 codification):** Pre-fix `CoreFrameworks/EngineSharded/Async.hpp:814` + `:853` (drainer-cycle `EngineSharded_Async_DrainWithSubmit` body). Both used `cfg.cores[i]` where `i` was the inner ring-pop counter (`for (int i = 0; i < MAX_EVENTS_PER_DRAIN_PER_CORE; ++i)` at Async.hpp:768), NOT the outer per-core slot variable (`for (int slot = 0; slot < state.registered_count; ++slot)` at Async.hpp:765). Silent miscalibration for per-core `partial_exit_pct` + `tp2_mult` when `core_overrides[slot]` not set; introduced at mechanical migration commit `ea08210` (.F.4c.3 WIP2d-1 Phase 2; `cfg.X` → `cfg.cores[i].X` substitution applied with wrong `i` symbol inside nested loop). Fix: `i` → `slot` at both sites. **Sister mechanical detection landed:** NEW Check 9 in `tools/check_per_core_registry_integrity.py` — paired-access mismatch detector flags `cfg.core_overrides[X]` + `cfg.cores[Y]` co-located within 5 lines where X != Y. Stage 6 escalation per M7 (memory codification alone proved insufficient — recurrence at drainer body despite codified discipline; structural CI catches future instances at commit-time). Regression test at `tests/controller_test.cpp` "v5.15.5.F.4d.1.B.7 Class 26: drainer per-core cfg slot integrity" section (8 new assertions; 4 slots × 2 fields). Recurrence_count 11→13.

  **Forward advisory closed at .B.8** (PARITY ledger DOCUMENTED-RISK entry at .B.8 retroactively closes this forward-promise — see .B.8 worked example below): prior `partial_exit_pct` / `tp2_mult` calibration sweeps may have produced tainted results (operators tuned against silently-miscalibrated behavior). Forward-looking work fine post-fix; historical calibration values may warrant re-validation at next sweep cycle.

- **v5.15.5.F.4d.1.B.8 (2026-05-27) — 4 NEW worked instances at accounting fee-floor compute paths (sub-shape B UNINDEXED-GLOBAL surface; Check 10 codification):** `/accounting-audit` sister-bug surface check surfaced UNINDEXED-GLOBAL sub-shape — same `ea08210` mechanical migration cohort as sub-shape A at .B.7 but DIFFERENT shape: reads `cfg.X` / `cfg->X` / `resolved_cfg.X` UNINDEXED (no array indexing at all) on per-core-with-global-sister fields at per-core consumer sites. Check 9 catches PAIRED-ACCESS-MISMATCH (sub-shape A); Check 9 CANNOT catch UNINDEXED-GLOBAL (no array indexing present to mismatch). Pre-fix sites:
  - `CoreFrameworks/ControllerEventLoop.hpp:3605-3606` — `EventLoop_TrailingSLRatchetOneCore` reads `cfg.fee_rate_taker` + `cfg.fee_rate` fallback UNINDEXED with `core_id` parameter in scope; slow-path SL ratchet fee-floor cap silently flattens to global → ratchet pushes SL too close to entry on high-fee cores → SG-fired exits become NET-NEGATIVE → silent realized-P&L drift per core
  - `CoreFrameworks/ControllerEventLoop.hpp:3670-3671` — `EventLoop_BreakevenOnProfitOneCore` sister-block same shape; net-profit threshold (2× fee_rate_taker) + fee-floor cap (3× fee_rate_taker) silently flatten
  - `Strategies/StrategyLifecycle.hpp:272-273` — `Strategy_WriteRatchetSL` shared helper reads `cfg->fee_rate_taker` + `cfg->fee_rate` fallback UNINDEXED with `slot` parameter; affects 5 callers (MeanReversion.hpp:613 + MLStrategy.hpp:314 + EmaCross.hpp:216 + Momentum.hpp:393 + ControllerEventLoop.hpp:2530)
  - `CoreFrameworks/ControllerEventLoop.hpp:3042-3043` — `EventLoop_RebuildOneCore` GUI diag capture reads `resolved_cfg.fee_rate_taker` UNINDEXED (resolved_cfg is stack-local copy from ControllerConfig_ResolveForCore; fee_rate_taker NOT in PER_CORE_OVERRIDE_FIELDS at ControllerConfig.hpp:119 so resolved_cfg.X stays GLOBAL); display↔execution divergence at fee-floor diag panel (sister at line 3061 correctly uses `&resolved_cfg.cores[slot]`)

  **Fix:** consumer-side substitution at each site: `cfg.X` → `cfg.cores[core_id].X` (or `resolved_cfg.cores[slot].X` for aliased case). Per H20 branchless: pre-resolve `const auto& core_cfg = cfg.cores[core_id]` + ternary `?:` select (cmov-lowerable). Sister-canonical pattern: `Strategies/StrategyParameters.hpp:1762` (correctly uses `core_cfg->fee_rate_taker`).

  **Sister mechanical detection landed:** NEW Check 10 in `tools/check_per_core_registry_integrity.py` — UNINDEXED-GLOBAL detector flags `cfg.X` / `cfg->X` / `resolved_cfg.X` reads on per-core-with-global-sister fields (fee_rate / fee_rate_taker / fee_rate_maker / slippage_pct) at per-core consumer sites. Stage 6 escalation per M7 6th canonical (Check 9 catches sub-shape A; Check 10 catches sub-shape B; same tool sister-extension per `canonical-sister-extension-discipline.md` v1.1 CI-tooling-surface axis). 5 Section D exemptions on file at .B.8 close (LEGACY single_core + DISPLAY KEEP-AS-GLOBAL).

  **Phase A cohort enumeration** at .B.8 confirmed audit scope: 4 REAL Class 26 sub-shape B + 1 MED-1 display fix (ShardedSnapshot.hpp:249) + 5 LEGACY-EXEMPT (EmaCross.hpp:143-144 + RegimeDetector.hpp:760/789/808 — legacy single_core paths per Cat 8 LEGACY-KEEP verdict) + 3 DISPLAY KEEP-AS-GLOBAL (ShardedSnapshot.hpp:142/343/344 — Settings panel operator-facing semantic). NEW Phase A discovery: `ControllerConfig.hpp:1337-1340 Fee_Compute()` canonical fee math helper has UNINDEXED-GLOBAL pattern but is NOT dead (tests use it; comments cite as Phase 8 maker/taker fee accuracy invariant); global-only by design (takes ControllerConfig<F>* not PerCoreCfg<F>*); annotated with global-only semantics doc.

  **Regression test:** `tests/controller_test.cpp` "v5.15.5.F.4d.1.B.8 Class 26: UNINDEXED-GLOBAL accounting cohort closure" section (~16-32 assertions; 4 slots × 2 fields × 4 consumer sites). Recurrence_count 13→17.

  **DOCUMENTED-RISK PARITY entry at .B.8 close** retroactively closes `.B.7` forward-promise (which was never actually written as entry): operators using per-core `fee_rate_taker` / `partial_exit_pct` / `tp2_mult` calibration sweeps PRIOR to `.B.7/.B.8` fixes may have produced tainted results; historical calibration values may warrant re-validation at next sweep cycle. Closure trigger: operator re-validation at next paper-test cycle OR operator decision that historical calibrations are acceptable.

## Sister classes

- **Class 27** (Single-value cache flattens per-instance) — structural pre-condition; cache has no per-instance dimension. Eliminating Class 27 sources eliminates many Class 26 sites by construction.
- **Class 24** (Capability cfg surface mismatch) — sister at the cfg-flow layer; capability cfg added but consumer doesn't see per-core dimension.
- **Class 25** (Scope erosion / per-core consumer) — sister at consumer-discipline layer.
- **Class 18** (Mirror-incomplete) — parent family; Class 26 is one instance shape of "mirror missing per-instance dimension."

## Cross-references

- `DESIGN_SPECS/refactor-patterns/decision-time-data-binding-pattern.md` (closure mechanism)
- `DESIGN_SPECS/refactor-patterns/cfg-scope-discipline.md` (per-core access discipline)
- `tools/check_per_core_registry_integrity.py` Check 7 + Check 9 (CI enforcement; Check 7 for Class 27 subsystem-state cfg-mirror scan + NEW Check 9 for Class 26 paired-access mismatch detection — `cfg.core_overrides[X]` + `cfg.cores[Y]` paired access with X != Y; added at v5.15.5.F.4d.1.B.7 per M7 4th canonical structural enforcement)
- Class 27 sub-file (sister class with detailed structural-cache discussion)
- `/accounting-audit` skill (scans for Class 26 + Class 27 instances in accounting paths)
- `/registry-fit-audit` skill (scans for Class 26 + Class 27 instances at registry boundaries)
