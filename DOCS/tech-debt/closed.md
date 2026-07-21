---
type: ledger-template
parent_index: DOCS/TECH_DEBT.md
covers: CLOSED-status TECH_DEBT entries (including NOT-A-BUG rationale-preservation entries)
established: 2026-05-18
---

# TECH_DEBT — CLOSED entries

Archival sub-file containing TECH_DEBT entries with terminal status (CLOSED at a specific ship, APPLIED, or NOT-A-BUG rationale-preservation). Entries here are not actionable; they exist for audit history + cross-reference lookup.

External cross-refs use canonical ID format `TECH_DEBT-NNN`. The ID is preserved across sub-files; `rg "TECH_DEBT-NNN"` finds the canonical entry in the appropriate sub-file automatically.

---

## Drift-class closures (v5.15.5.F.4 — universal cfg field registry sprint)

The v5.15.5.F.4 sprint structurally closes 7 recurring drift classes via the universal cfg field registry + categorical-tag applicability + STAMP_BOUND derived filter + bitmap overflow audit. Class-level closures (individual TECH_DEBT-NNN entries flip CLOSED on their addressing ship):

| Class | Closure mechanism | Closure ship |
|---|---|---|
| `parser_gap` (cfg parser drift across files; 123 missed cfg fields proved recurrence) | registry-driven parser via `tt::cfg_parse_field<KIND_X>` + `lives_in_struct` routing | `.F.4b` (DOUBLE/PCT) + `.F.4c` (INT/INT_ENUM/BOOL) + `.F.4d` (STRING/FILE_PATH) |
| `panel_gap` (SettingsPanel field_defs[] drift) | registry-driven GUI render walk | `.F.4b-d` |
| `persist_gap` (manual Cfg_Save drift; cfg.example documentation drift) | registry-driven save dispatch + cfg.example auto-gen per `lives_in_struct` | `.F.4d` |
| `per_core_gap` (per-core override emission drift; PARITY-002/003/004/005/008 4× recurrence) | `PER_CORE_OK` metadata bit auto-emits override storage + AoS-by-core re-layout consolidates scattered arrays | `.F.4b` (auto-emit) + `.F.4g` (AoS-by-core) |
| `stamp_drift_gap` (TECH_DEBT-006: FOREACH_STAMP_BOUND_CFG vs FOREACH_CFG_FIELD dual registry) | `STAMP_BOUND` derived filter + canonical byte order locked via CI hash test (Layer 5b of `wire-format-byte-preservation-discipline.md`) | `.F.4b` |
| `cfg.example_doc_gap` (cfg.example manual drift; 7th gap class from registry spec future work) | AUTOPOPULATE companion emits per-`lives_in_struct` cfg.example | `.F.4d` |
| `silent_bitmap_truncation` (Class 20: FOREACH_X paired with bitmap field, no overflow guard) | `.F.4h` audit pass adds `static_assert` to all existing bitmap-paired registries | `.F.4h` |

**Hardcoded-instance-gating class (Class 19)** was not previously surfaced as TECH_DEBT but would have recurred on next strategy / regime / op_mode addition. Closed proactively by categorical-tag pattern at `.F.4b/h`.

---

## Issues

### TECH_DEBT-003 — `verify_model_stamp` parser refactor to data-driven dispatch ✅ CLOSED v5.15.0

```yaml
id: TECH_DEBT-003
title: verify_model_stamp parser refactor to data-driven dispatch
severity: low
surface_tags: [parser, wire-format, ml-inference, registry]
trigger: sub-ship-v5.15.0
status: closed
opened: 2026-05-09
closed: 2026-05-12
related_specs: [DESIGN_SPECS/framework-patterns/x-macro-registry-with-presence-dispatch.md]
```

- **Created:** 2026-05-09 by v5.14.2.E.3 (first noted in v5.14.1 post-mortem)
- **Severity:** LOW
- **Surface:** `ML_Headers/ModelInference.hpp` `verify_model_stamp` function
- **What was deferred:** Parser used if-else chain over ~24 PRE_CFG stamp body keys (POST_CFG was already X-macro-driven since v5.14.8.A.merged.4). Adding a new PRE_CFG key required manual `else if (strcmp(key, "...") == 0) { ... }` branch + STAMP_SET dispatch — Class 18 mirror with the registry-driven emit walk.
- **Status:** ✅ **CLOSED v5.15.0 (2026-05-12).** v5.15.0.B refactor migrated the PRE_CFG parser branches to X-macro dispatch walking FOREACH_STAMP_BOUND_MODEL_CONST_PRE_CFG (all 27 entries auto-flow). Uses `tt::stamp_parse_field<T>` templated helper for type dispatch (CLAUDE.md item 23). The 3 hex-encoded uint64 fields (build_flags_hash, label_registry_hash, feature_mask) initially deferred as manual branches were RESOLVED by extending `tt::stamp_parse_field<T>` to take the registry's `fmt` column as an optional parameter and auto-detect base via `strchr(fmt, 'x') || strchr(fmt, 'X')` — DRY: `fmt` is now the single source of truth for emit AND parse format. The originally-proposed `parser_base` tuple column is SUPERSEDED by this approach (no tuple-shape change; future hex fields auto-flow). 1 manual branch remains: `feature_scaler_present` for defensive truthy normalization (any non-zero → 1; production emit always produces 0/1, so the branch is bounded defensive coding against malformed stamps). Closes Class 18 parser/emit mirror at the same surface AUTOPOPULATE closed for emit. ~120 LOC → ~25 LOC X-macro + 1 normalization exception.
- **Cross-ref:** v5.14.1 post-mortem; FOREACH_STAMP_BOUND_CFG (`StampBoundCfgRegistry.hpp`) shows the canonical pattern; v5.15.0 ship; `tt::stamp_parse_field<T>` at `ML_Headers/StampBoundModelConstRegistry.hpp:101+`.

---

### TECH_DEBT-004 — Dual-tau cfg field naming clarity ✅ CLOSED v5.14.9.D

```yaml
id: TECH_DEBT-004
title: Dual-tau cfg field naming clarity
severity: low
surface_tags: [cfg-flow, ml-inference]
trigger: sub-ship-v5.14.9.D
status: closed
opened: 2026-05-09
closed: 2026-05-10
related_specs: []
```

- **Created:** 2026-05-09 by v5.14.2.E.3 (originally PARITY-006; reclassified as TECH_DEBT since not a parity issue)
- **Severity:** LOW
- **Surface:** `ControllerConfig.hpp` cfg fields `confidence_freshness_tau` (legacy IC) + `confidence_freshness_tau_secs` (composite confidence; v5.14.1)
- **What was deferred:** Two distinct cfg fields with overlapping semantics ("freshness tau"). Operator could set one when meaning the other.
- **Status:** ✅ **CLOSED v5.14.9.D (2026-05-10, commit b703e61).** Hard-deletion path: legacy `confidence_freshness_tau` was mathematically inert (`data_age=0` always in production; half-dead via stamp-bound drift check on a value that doesn't affect inference). Deleted entirely from ControllerConfig + 5 ConfidenceScorer_Init callsites adapted (3-arg → 2-arg signature). Legacy stamps with `inference_cfg_freshness_tau` line load successfully (parser ignores unknown key via existing forward-compat semantics; HMAC chain unbroken because HMAC is per-stamp). Operator migration: WARN log if legacy key present in cfg file ("remove from cfg"). Only `confidence_freshness_tau_secs` remains (composite-confidence freshness; not confusable since the legacy field is gone).
- **Cross-ref:** PARITY-006 (originally raised there); v5.14.9.D commit b703e61 (engine repo); v5.14.9 umbrella.

---

### TECH_DEBT-005 — Single-zoo hot-swap strict-mode failure handling unification ✅ CLOSED v5.15.4

```yaml
id: TECH_DEBT-005
title: Single-zoo hot-swap strict-mode failure handling unification
severity: low
surface_tags: [ml-inference, slow-path, concurrency]
trigger: sub-ship-v5.15.4
status: closed
opened: 2026-05-09
closed: 2026-05-12
related_specs: [DESIGN_SPECS/feature-patterns/shadow-load-state-transition-pattern.md]
```

- **Created:** 2026-05-09 by v5.14.2.E.3 (surfaced during v5.14.2.E.1 design)
- **Severity:** LOW
- **Surface:** `CoreFrameworks/EngineSharded.hpp` ~line 2820 (single-zoo hot-swap validate failure handling)
- **What was deferred:** Boot does Free + null + flag on validate failure. Hot-swap did flag-only on validate failure (preserved v5.10.0c "log-and-leave" semantics). Asymmetry was intentional pre-v5.15.4 because pre-swap state wasn't snapshotted; true rollback required infrastructure.
- **Status:** ✅ **CLOSED v5.15.4 (2026-05-12).** Single-zoo + ensemble hot-swap unified via shadow-load pattern (per `shadow-load-state-transition-pattern.md` — promoted DRAFT v0.1 → ACTIVE v1.0). Both surfaces use `tt::HotSwap_ShadowLoad_*<F>` helpers in `CoreFrameworks/HotSwap.hpp`:
  - **`aligned_alloc(64, sizeof(T))` allocates NEW zoo container** — pre-swap state untouched
  - **Init + Load + PostLoadSetup into NEW zoo** — failure modes (alloc OOM / load failed / strict validate failed) all Free new + return nonzero with pre-swap pointer preserved
  - **`__atomic_exchange_n` swap** — lock-free; readers see old OR new, never torn
  - **Free OLD zoo** — single-owner reclamation (per-core slow-path thread is sole owner of `state.cores[c].*_handle`; no RCU grace needed)
  - **PARITY-023 capture-pointer-revert anti-pattern eliminated** — no torn moment exists, so revert is unnecessary
- **Bonus implicit fixes:**
  - Boot path migrated from `static CoreModelZoo<F> ml_zoos[]` to per-core `aligned_alloc(64)` (required for `free(old_ezoo)` validity on first swap)
  - `alignas(64)` retrofit on `CoreModelZoo<F>` + `EnsembleModelZoo<F>` so heap allocations satisfy embedded `ModelHandle<F>` + `RidgeWeights<F>` alignment guarantees
  - Legacy `EnsembleHotSwap.hpp::EngineSharded_HotSwapEnsemble` retained for back-compat but production dispatch now goes through shadow-load
- **Cross-ref:** `CoreFrameworks/HotSwap.hpp` (canonical implementation); `DESIGN_SPECS/feature-patterns/shadow-load-state-transition-pattern.md` (pattern doc); PARITY-023 closure (workspace `PARITY_ISSUES.md`).

---

### TECH_DEBT-006 — `FOREACH_STAMP_BOUND_MODEL_CONST` registry for architectural fields ✅ CLOSED v5.14.8

```yaml
id: TECH_DEBT-006
title: FOREACH_STAMP_BOUND_MODEL_CONST registry for architectural fields
severity: low
surface_tags: [registry, wire-format, ml-inference]
trigger: sub-ship-v5.14.8
status: closed
opened: 2026-05-09
closed: 2026-05-09
related_specs: [DESIGN_SPECS/framework-patterns/x-macro-registry-with-presence-dispatch.md, DESIGN_SPECS/wire-format-patterns/pre-post-cfg-registry-split-for-emit-order-preservation.md, DESIGN_SPECS/framework-patterns/autopopulate-pattern-for-production-caller-class.md, DESIGN_SPECS/framework-patterns/bitmap-flag-api.md]
```

- **Created:** 2026-05-09 by v5.14.2.E.3 (during v5.14.2.E.2.B design)
- **Severity:** LOW
- **Surface:** `ML_Headers/ModelInference.hpp` (architectural fields added manually in v5.14.2.E.2.B)
- **What was deferred:** 4 architectural fields (`expected_num_classes`, `expected_role`, `expected_num_features`, `expected_feature_format_version`) added with manual emit + parse + populator (separate from FOREACH_STAMP_BOUND_CFG which only handles cfg-bound fields). Refactor to parallel X-macro registry `FOREACH_STAMP_BOUND_MODEL_CONST(X)` that handles training-time/build-time-derived fields.
- **Cost estimate:** ~2h to design + extract registry; LOW risk (additive refactor).
- **Status:** ✅ **CLOSED v5.14.8 (2026-05-09).** Substantially exceeded original scope:
  - **32 architectural fields** auto-flow from registry (originally 4 named; expanded to cover all v5.14.2 + earlier architectural fields)
  - **Option 1 unification** across ModelStampResult / StampInferenceCfgInputs / ModelHandle to canonical wire-key names
  - **Bit-packed has_flags uint64_t** (TECH_DEBT-013 BIT_FLAG storage class win for stamp body)
  - **PRE_CFG/POST_CFG split** preserves canonical wire format byte-for-byte (HMAC chain unbroken)
  - **STAMP_MODEL_CONST_AUTOPOPULATE** companion macro extinguishes v5.9.5b production-caller class for stamp body
  - **Reusable BITMAP_* API** (`MemHeaders/BitmapMacros.hpp`) used by sister registries
  - **Round-trip HMAC verification test** (v5.14.8.A.7; 32 fields populated; emit→parse→verify)
  - **5 NEW v5.14.8 fields** added via POST_CFG registry (training_timestamp_us, run_name, scaler_fit_data_hash, removal_reasons_csv, environment_meta group of 5)
  - **Stale-model gate** (v5.14.8.E) consumes training_timestamp_us
- **Future field addition:** 1 row in `FOREACH_STAMP_BOUND_MODEL_CONST_PRE_CFG` or `_POST_CFG` → struct fields + parser + emitter + AUTOPOPULATE wiring all auto-flow.
- **Cross-ref:** v5.14.8 umbrella ship; `DESIGN_SPECS/framework-patterns/x-macro-registry-with-presence-dispatch.md`, `DESIGN_SPECS/wire-format-patterns/pre-post-cfg-registry-split-for-emit-order-preservation.md`, `DESIGN_SPECS/framework-patterns/autopopulate-pattern-for-production-caller-class.md`, `DESIGN_SPECS/framework-patterns/bitmap-flag-api.md`; CLAUDE.md items 13, 20, 21, 22, 23.

---

### TECH_DEBT-010 — FOREACH_CALIB_LOG_COL registry for calibration log CSV columns ✅ CLOSED v5.14.10.D

```yaml
id: TECH_DEBT-010
title: FOREACH_CALIB_LOG_COL registry for calibration log CSV columns
severity: low
surface_tags: [registry, wire-format, oms-drainer]
trigger: sub-ship-v5.14.10.D
status: closed
opened: 2026-05-09
closed: 2026-05-10
related_specs: [DESIGN_SPECS/framework-patterns/calibration-log-column-registry.md]
```

- **Created:** 2026-05-09 by v5.14.8 scope decision (Interpretation B; deferred N-site pattern audit)
- **Severity:** LOW (small N currently; CSV columns relatively stable; pattern still recurring)
- **Surface:** Calibration log CSV writer (`CoreFrameworks/CalibrationLog.hpp` or similar), reader/parser (post-process tooling), header definition
- **What's deferred:** Convert calibration log CSV column additions from manual 3-site updates (header constant + writer column + reader/parser column) to a `FOREACH_CALIB_LOG_COL` registry. Each registry entry would auto-generate header position, writer printf format, reader scanf format.
- **Why deferred (not effort-avoidance):** v5.14.8 work doesn't touch calibration log path; small N (currently ~20 columns) means manual pattern is tractable. Worth converting only when the next ship tries to add ≥3 columns and would otherwise compound the pattern.
- **Cost estimate:** ~3-4h structural ship; ~20 columns to migrate; trivial per-column
- **Trigger:** Next ship that adds 3+ calibration log columns in one umbrella (e.g., maker-side fill metrics when v6.0 maker ships, or new ML observability columns), OR ship that touches the CSV writer/reader for any reason.
- **Status:** **CLOSED v5.14.10.D** — `DataStream/CalibLogColRegistry.hpp` (NEW) defines FOREACH_CALIB_LOG_COL with the existing 9 columns; `OrderManager_HandleFill` row emit + `OpenCalibrationLog` header emit refactored to walk the registry; byte-format preservation (operator-parser compat) maintained. DESIGN_SPECS doc `calibration-log-column-registry.md` (NEW) captures the methodology + lists future candidate logs (MetricsLog + ShardedTradeLog scheduled for v5.14.10.F per /merge-scan N2 finding).
- **Cross-ref:** v5.13.0.B calibration log infrastructure; v5.14.7 deferred plan (would have added 4 maker-related columns); v5.14.10.D commit (TBD); `DESIGN_SPECS/framework-patterns/calibration-log-column-registry.md`.

---

### TECH_DEBT-013 — Bit-packed boolean flags (BIT_FLAG storage class) for byte-per-flag patterns across codebase ✅ CLOSED v5.14.9

```yaml
id: TECH_DEBT-013
title: Bit-packed boolean flags (BIT_FLAG storage class) for byte-per-flag patterns across codebase
severity: medium
surface_tags: [bitmap-packed, registry, cfg-flow]
trigger: sub-ship-v5.14.9
status: closed
opened: 2026-05-09
closed: 2026-05-10
related_specs: [DESIGN_SPECS/framework-patterns/heterogeneous-registry-pattern.md, DESIGN_SPECS/framework-patterns/bitmap-flag-api.md]
```

- **Created:** 2026-05-09 by v5.14.8.B FOREACH_FAILURE_MODE design discussion (operator question: "couldnt we track each one using a single bit since theyre basically 1 or 0?")
- **Severity:** MEDIUM (recurring inefficiency; data-oriented design alignment opportunity; aligns with CLAUDE.md item 1 Portfolio uint16_t bitmap pattern)
- **Surface:** Multiple — see candidate inventory below
- **Pattern definition:** Replace `uint8_t` boolean flag fields with bit-packed `uint16_t` / `uint32_t` / `uint64_t` bitmap. X-macro entries declare `BIT_FLAG` storage class; X-macro auto-allocates bit positions + generates `MASK_##name` constants + ergonomic `IS_SET` / `SET` / `CLR` accessor macros. Wins: memory compactness (16-64 flags in 2-8 bytes), branchless multi-flag check via mask (`flags & (MASK_X | MASK_Y)`), branchless "any flag set?" check (`flags != 0`), atomic multi-flag updates via `__atomic_fetch_or`.
- **Pattern precedent:** `Portfolio<uint16_t>` bitmap (CLAUDE.md item 1); `OrderManagerState.order_bitmap` (uint16_t); v5.14.8.B `FailureModeRegistry.hpp` (newly established X-macro pattern with BIT_FLAG / COUNTER_U32 / PERCENT_U8 storage classes).
- **What's deferred:** Apply BIT_FLAG storage class to byte-per-flag patterns NOT in v5.14.8's active touch surface. Each target gets its own focused ship (or folds into the next ship that touches that surface).

**Candidate inventory (sweep 2026-05-09):**

| Surface | Current flags | Bit-pack target | Effort | Trigger |
|---|---|---|---|---|
| `failure_flags` (FOREACH_FAILURE_MODE) | 2 | uint16_t | ✅ DONE v5.14.8.B | — |
| Stamp body `has_*` (FOREACH_STAMP_BOUND_MODEL_CONST) | 24+ | uint64_t (`has_flags`) | ✅ DONE v5.14.8.A | — |
| `PerCoreSnap` non-failure state flags (permission, bitmap_consistency, gate_direction, is_ml, ml_model_loaded, strategy_was_explicit_set, ladder_bottom_hit) | 6→7 | uint16_t `state_flags` + MASK_* registry | ✅ DONE v5.14.9.B.2 | — |
| `FOREACH_FEATURE` `enabled` flag | 40 features | uint64_t `FEATURE_ENABLED_BITMAP` + `IS_FEATURE_ENABLED(i)` macro | ✅ DONE v5.14.9.E | — |
| Engine-wide cfg bool flags (21 across 5 domains) | 21 | 5 domain bitmaps via `FOREACH_<DOMAIN>_CFG_FLAG` registries | ✅ DONE v5.14.9.F-.F.6 | — |
| `ControllerEventLoop.partner_pending_active` (per-core) | 1 | uint16_t `partner_pending_bitmap` on EventLoopState (1 bit per core) | ✅ DONE v5.14.9.G | — |
| `ShardedSnapshot.any_scaler_present` + `any_scaler_failed` | 2 | uint8_t `scaler_summary_flags` transient local with 6-bit headroom | ✅ DONE v5.14.9.H | — |
| `CoreContext` boot/decision booleans (dirty, core_kill_tripped, model_load_failed, cfg_drift_strict_refused, warmup_log_emitted) | 5 | uint8_t `core_state_flags` + `FOREACH_CORE_STATE_FLAG` registry + `CORE_STATE_FLAG_{IS_SET,SET,CLR}` accessors | ✅ DONE v5.15.5.B.3 (post-closure 8th application; pattern continues to land new sites) | — |

- **Status:** ✅ **CLOSED v5.14.9 (2026-05-10).** All 7 candidates migrated. **+ v5.15.5.B.3 (post-closure)** added an 8th application (`core_state_flags` on CoreContext via `FOREACH_CORE_STATE_FLAG`) — confirms the BIT_FLAG pattern continues to attract new sites organically; no need to reopen the ticket. Cumulative wins:
  - Memory saved: 15B per ControllerConfig (21 scattered ints → 5 bitmap fields) + 126B per EventLoopState (per-core bool → 2-byte bitmap) + scaler aggregation tightened
  - Single-source-of-truth registries: registry = enum + MASK + parser + AUTOPOPULATE + GUI label + section + tooltip + per-core override (Option D 5-col tuple expansion v5.14.9.F.5)
  - HMAC chain byte-equivalence proven for stamp-bound bit-extract entries (v5.14.9.F.2 Y3 dispatch)
  - Per-bit per-core override capability via PER_CORE_OVERRIDE_BITMAP_DOMAINS (v5.14.9.F.6)
  - Cache-layout discipline applied (HOT-CLUSTER alignas(8) at start of 5 domain bitmaps; cold-cluster split deferred to TECH_DEBT-021 post-paper-test profiling)
  - Pattern documented in `DESIGN_SPECS/framework-patterns/heterogeneous-registry-pattern.md` (DRAFT v0.1 → ACTIVE v1.0 after .F-.F.6 field tests validated all 4 pre-field-test concerns)
- **Why valuable:** every future bool cfg flag = 1 row in registry → ALL downstream consumers auto-flow. Recurring "add bool flag = N-site update" class extinguished structurally for booleans (FOREACH_CFG_FIELD broader closure for non-boolean fields tracked under TECH_DEBT-009 partial).
- **Cross-ref:** v5.14.9.F-.F.6 + .G + .H ships; `DESIGN_SPECS/framework-patterns/heterogeneous-registry-pattern.md` (canonical pattern doc); CLAUDE.md item 1 (Portfolio bitmap precedent); item 18 (data-oriented design + branchless mask compute philosophy); `DOCS/EASY_ADDITIONS_INVARIANTS.md` (pattern documentation).

---

### TECH_DEBT-014 — ModelHandle migration to FOREACH_STAMP_BOUND_MODEL_CONST X-macro generation ✅ CLOSED v5.15.0

```yaml
id: TECH_DEBT-014
title: ModelHandle migration to FOREACH_STAMP_BOUND_MODEL_CONST X-macro generation
severity: low
surface_tags: [registry, ml-inference, wire-format, bitmap-packed]
trigger: sub-ship-v5.15.0
status: closed
opened: 2026-05-09
closed: 2026-05-12
related_specs: [DESIGN_SPECS/framework-patterns/x-macro-registry-with-presence-dispatch.md]
```

- **Created:** 2026-05-09 by v5.14.8.A.merged.2 (deferred during Option 1 unification scope)
- **Severity:** LOW
- **Surface:** `ML_Headers/ModelInference.hpp` ModelHandle struct
- **What was deferred:** ModelHandle used MANUAL field declarations for stamp-derived runtime fields (inconsistent `stamp_inf_*`, `stamp_xgb_*`, `stamp_label_*`, `stamp_*` prefix policy across groups). v5.14.8.A.merged migrated ModelStampResult + StampInferenceCfgInputs to X-macro generation but ModelHandle stayed manual.
- **Status:** ✅ **CLOSED v5.15.0 (2026-05-12).** ModelHandle migrated to X-macro generation walking FOREACH_STAMP_BOUND_MODEL_CONST with STAMP_HANDLE_GEN_INCLUDE/SKIP_HANDLE presence dispatch. 14 uint8_t has_* direct fields → uint64_t has_flags bit-packed (CLAUDE.md item 20; shared MASK_* constants with ModelStampResult / StampInferenceCfgInputs so a single parser dispatch table row writes both bits). Value fields renamed to canonical wire-key names (stamp_xgb_max_depth → xgb_max_depth, stamp_inf_confidence_threshold_scale → inference_cfg_confidence_threshold_scale, etc.). alignas(64) + 64B HOT cluster (handle, backend, num_*, has_flags) + HOT-2 cluster (target_classes / class_weights at cache line 2) + WARM cluster (scaler) + COLD cluster (X-macro stamp fields + paths). Explicit padding (`_hot_pad0`, `_hot_pad1[4]`) per CLAUDE.md item 27. ~80 caller sites migrated across CoreModelZoo, EngineSharded, ModelValidation, FeatureRegistryOverlay, tests. ~250 LOC delta.
- **Cross-ref:** v5.14.8.A.merged.2 commit (deferral point); v5.15.0 ship; +23 anchor tests at `tests/controller_test.cpp` (v5.15.0.A + v5.15.0.C sections).

---

### TECH_DEBT-015 — FOREACH_FEATURE 7-col extension (max_staleness_minutes) + Features_PackAll stale-feature wiring ✅ CLOSED v5.14.9.E

```yaml
id: TECH_DEBT-015
title: FOREACH_FEATURE 7-col extension (max_staleness_minutes) + Features_PackAll stale-feature wiring
severity: low
surface_tags: [registry, ml-inference, bitmap-packed]
trigger: sub-ship-v5.14.9.E
status: closed
opened: 2026-05-09
closed: 2026-05-10
related_specs: []
```

- **Created:** 2026-05-09 by v5.14.8.E (stale-feature gating scope split)
- **Severity:** LOW
- **Surface:** `ML_Headers/FeatureRegistry.hpp` (FOREACH_FEATURE registry), `ML_Headers/FeatureRegistry.hpp` Features_PackAll, `ML_Headers/FeatureRegistry.hpp` FeatureComputeCtx
- **What's deferred:** v5.14.8.E added the stale_feature_events COUNTER_U32 entry to FOREACH_FAILURE_MODE (registry + counter slot + panel constants ready) but did NOT wire Features_PackAll to actually consume per-feature staleness thresholds. Full wiring requires:
  - FOREACH_FEATURE 7-column extension: append `max_staleness_minutes` column (per-feature threshold; 0 = disabled). All 7+ X-macro caller sites in FeatureRegistry.hpp update to 7-param signature; hash-compute caller body still reads only (name, version) so FEATURE_REGISTRY_HASH stays stable.
  - `feature_last_update_us[NUM_REGISTERED_FEATURES]` array storage on FeatureComputeCtx (or via per-feature compute fn capturing `now_us`).
  - Features_PackAll stale check: `if (max_staleness_minutes[i] > 0 && (now_us - last_update_us[i]) / 60000000ULL > max_staleness_minutes[i]) { features[i] = 0.0f; stale_feature_events_total++; continue; }`
  - Slow-path latency: ~40ns when configured; HOT_PATH_CHANGELOG entry needed.
- **Why deferred (not effort-avoidance):** v5.14.8.E delivered the high-value stale-MODEL gate (boot-time refuse on operator-deploying-expired-models). Stale-FEATURE gate is value-add but not blocking; bounded follow-up. Feature pipeline wiring spans 7+ X-macro caller sites + FeatureComputeCtx + per-feature compute fns + retest.
- **Cost estimate:** ~2-3h (FOREACH_FEATURE column add + 7 caller-site updates + Features_PackAll wiring + HOT_PATH_CHANGELOG entry + tests).
- **Status:** ✅ **CLOSED v5.14.9.E (2026-05-10).** FOREACH_FEATURE extended 6→7 columns with `max_staleness_minutes`; `FEATURE_ENABLED_BITMAP` uint64_t replaces 40 uint8_t bool fields (312 bytes saved per FeatureComputeCtx); `IS_FEATURE_ENABLED(i)` macro; Features_PackAll do-while wrapper for staleness check skip; `feature_last_update_us[NUM_REGISTERED_FEATURES]` array storage on FeatureComputeCtx; stale_feature_events_total counter (was infrastructure-only since v5.14.8.E; now functional).
- **Cross-ref:** v5.14.8.E commit (infrastructure); v5.14.9.E commit (wiring closed); FOREACH_FAILURE_MODE entry `stale_feature_events` in `MemHeaders/FailureModeRegistry.hpp`; CHANGELOG v5.14.9 row.

---

### TECH_DEBT-017 — Direct-int cfg-flag cohort migration to FOREACH_ML_CFG_FLAG (ridge_within_horizon / ridge_across_horizons / exit_blender_mode / ridge_online_corr) ✅ CLOSED v5.14.11.C

```yaml
id: TECH_DEBT-017
title: Direct-int cfg-flag cohort migration to FOREACH_ML_CFG_FLAG (ridge cohort)
severity: low
surface_tags: [cfg-flow, registry, ml-inference, bitmap-packed]
trigger: sub-ship-v5.14.11.C
status: closed
opened: 2026-05-11
closed: 2026-05-11
related_specs: [DESIGN_SPECS/refactor-patterns/cfg-flag-eligibility-criteria.md, DESIGN_SPECS/framework-patterns/heterogeneous-registry-pattern.md]
```

- **Created:** 2026-05-11 by /readiness Check 16 + /dod-audit HIGH-1 finding during v5.14.11 pre-coding gate
- **Severity:** LOW (cosmetic / discipline; no behavior or perf impact)
- **Surface:** `ControllerConfig.hpp` (3 direct `int` cfg fields prior to .C: `ridge_within_horizon`, `ridge_across_horizons`, `exit_blender_mode`); `ML_Headers/MlCfgFlagRegistry.hpp` (already housing 7 ML/confidence flags pre-.C); `CoreFrameworks/SlowPathGateRegistry.hpp` (cached gate predicates); `ML_Headers/StampBoundCfgRegistry.hpp` (stamp-binding entries for ridge_within + ridge_across + exit_blender + ridge_lambda + ridge_cost_penalty + ridge_min_ic_floor); `Strategies/StrategyParameters.hpp` (buy + exit Ridge dispatch sites + their fallback paths)
- **Class:** Same shape as `confidence_composite_enabled` migration (v5.14.9.F.2) — direct `int` cfg field that's load-bearingly toggled at slow-path gate + stamp-bound at the wire boundary; cohort-eligibility per `DESIGN_SPECS/refactor-patterns/cfg-flag-eligibility-criteria.md` (passes all 5 criteria: boolean semantics, slow-path predicate, parser-friendly key=value form, no analog-knob ambiguity, hot-path cache-line participation). Per CLAUDE.md item 19 (structural fix preferred when bug class can recur), single-row registry addition >> N-site duplication risk.
- **What's deferred → done:** Migrate 3 direct fields off `ControllerConfig` into `FOREACH_ML_CFG_FLAG` bitmap entries (RIDGE_WITHIN_HORIZON, RIDGE_ACROSS_HORIZONS, EXIT_BLENDER_MODE); add new RIDGE_ONLINE_CORR entry for the v5.14.11 online-correlation toggle landing in same ship; flip 3 stamp-binding `emit_source=DIRECT_FIELD` entries to `BITMAP_BIT` with ternary normalization `? 1 : 0` for byte-equivalence on the HMAC chain; update 2 SlowPath gate predicates + add new RIDGE_ONLINE_CORR_ACTIVE gate; refactor 2 Ridge dispatch sites for branchless multi-flag mask check (CLAUDE.md item 18) — single AND+compare when gate_state present; wire `use_online` from gate_state via MASK_RIDGE_ONLINE_CORR_ACTIVE; migrate 4 cfg parser tests + 4 stamp-body autopopulate tests + 4 slow-path gate state tests in `tests/controller_test.cpp`.
- **Why valuable:** Every future ML/confidence boolean cfg flag = 1 row in FOREACH_ML_CFG_FLAG + AUTOPOPULATE handles fan-out across stamp-binding + slow-path gate + dispatch sites + parser + tests. Recurring "add bool flag = N-site update" class extinguished structurally for the Ridge cohort. Slow-path branch density reduced via multi-flag mask check at buy-side Ridge dispatch (2 separate scalar branches → 1 mask AND+compare when gate_state wired).
- **Status:** ✅ **CLOSED v5.14.11.C (2026-05-11).** 4 entries added to FOREACH_ML_CFG_FLAG (Ridge cohort + ridge_online_corr); 3 ControllerConfig direct field declarations + defaults + CFG_PARSE_INT removed (parser auto-routes via FOREACH_ML_CFG_FLAG legacy_field column); 3 stamp-binding entries flipped to BITMAP_BIT with byte-equivalence ternary; 2 SlowPath gate predicates migrated + 1 new RIDGE_ONLINE_CORR_ACTIVE gate added (10 total gates; 6 bits headroom); branchless multi-flag dispatch refactor at buy-side; exit-side migrated; all 2904 tests pass (zero regression).
- **Cross-ref:** v5.14.11.C commit; v5.14.9.F.2 commit (canonical confidence_composite_enabled migration precedent); `DESIGN_SPECS/refactor-patterns/cfg-flag-eligibility-criteria.md` (decision criteria); `DESIGN_SPECS/framework-patterns/heterogeneous-registry-pattern.md` (Y3 dispatch for stamp-binding integration); CLAUDE.md items 18 (branchless mask compute), 19 (structural fix preferred), 20 (BITMAP_* API), 22 (Y3 dispatch); /readiness 2026-05-11 Check 16 + /dod-audit 2026-05-11 HIGH-1 finding (both flagged the cohort migration eligibility pre-coding).

---

### TECH_DEBT-019 — Rejected monolithic FOREACH_ENGINE_CFG_FLAG registry (design rationale preservation)

```yaml
id: TECH_DEBT-019
title: Rejected monolithic FOREACH_ENGINE_CFG_FLAG registry (design rationale preservation)
severity: low
surface_tags: [registry, cfg-flow]
trigger: explicit-operator
status: closed
opened: 2026-05-10
closed: 2026-05-10
related_specs: [DESIGN_SPECS/framework-patterns/heterogeneous-registry-pattern.md]
```

- **Created:** 2026-05-10 by v5.14.9.F Option C decomposition (post-/dod-audit auto-write per CLAUDE.local.md contract)
- **Severity:** N/A (NOT-A-BUG; rationale-preservation entry)
- **Surface:** Conceptual / design-record only; no code surface
- **What was considered:** Monolithic FOREACH_ENGINE_CFG_FLAG registry covering ~18 boolean cfg fields (partial_exit_enabled, depth_enabled, kill_switch_enabled, confidence_enabled, etc.) → single uint32_t engine_cfg_flags bitmap on ControllerConfig.
- **Why rejected (post-2026-05-10 audits):** /dod-audit + /merge-scan independently identified 4 fatal heterogeneity factors that made the COLUMN form (single registry, single bitmap) wrong fit:
  1. **Read cadences differ:** drainer reads partial_exit_enabled every cycle (hot-path-adjacent); kill_switch_enabled mutated by slow-path; depth_enabled boot-frozen; bandit_enabled slow-path-only. Single bitmap = mixed cache-line semantics.
  2. **Mutation patterns differ:** read-only cfg booleans (depth_enabled) vs runtime-mutated state-like booleans (kill_switch_tripped) vs cfg-loadable-but-immutable-runtime (partial_exit_enabled). Single struct field = false-sharing risk.
  3. **Coupling unrelated features:** bandit_enabled, barrier_gate_enabled, cost_gate_enabled, foxml_vol_scaling_enabled have no semantic overlap; grouping them in one registry is convenience-over-architecture.
  4. **Future-flexibility:** ML domain growing fast (bandit warmup, ridge weights, calibration enables); RISK domain stable. Want to split independently in v5.X+ without restructuring; monolithic doesn't permit.
- **Decision:** DOMAIN SPLIT chosen instead. 5 separate FOREACH_<DOMAIN>_CFG_FLAG registries (OMS / GATE / RISK / ML / OPS). Each domain has homogeneous read cadence + mutation pattern + cache-line concerns. Pattern documented in `DESIGN_SPECS/framework-patterns/heterogeneous-registry-pattern.md`.
- **Why this entry exists (NOT-A-BUG):** future sessions reading the codebase may notice "5 small registries; could combine into 1 big one" + propose monolithic refactor. This entry preserves the rejection rationale so that proposal is recognized as design-considered + correctly rejected. Also serves as canonical reference for "when domain-split wins over monolithic" on future heterogeneous-registry decisions.
- **Cost:** 0h (no work to do; this entry is documentation)
- **Trigger to re-litigate:** if, after v5.14.10+ paper-test profiling, the 5 small registries' overhead becomes measurable (e.g., 5 separate AUTOPOPULATE walks at slow-path entry costs >100ns) AND consolidation would actually save cycles AND the heterogeneity factors above no longer apply (e.g., all flags become uniformly slow-path-only with same cache concerns), then revisit. Until then: status NOT-A-BUG.
- **Status:** NOT-A-BUG (preserved as rationale)
- **Cross-ref:** v5.14.9.F-.F.3 (DOMAIN SPLIT implementation); `DESIGN_SPECS/framework-patterns/heterogeneous-registry-pattern.md` (decision framework codified); `plans/plan_checks/dod-audit-2026-05-10-v5.14.9-postE.md` + `merge-scan-2026-05-10-v5.14.9-postE.md` (audit findings that drove the rejection)

---

### TECH_DEBT-023 — `lat_enabled` is NOT cfg-flag-eligible (rationale preservation)

```yaml
id: TECH_DEBT-023
title: lat_enabled is NOT cfg-flag-eligible (rationale preservation)
severity: low
surface_tags: [hot-path, cfg-flow]
trigger: explicit-operator
status: closed
opened: 2026-05-10
closed: 2026-05-10
related_specs: [DESIGN_SPECS/framework-patterns/heterogeneous-registry-pattern.md]
```

- **Created:** 2026-05-10 by v5.14.9.F step 0 verification (caught audit subagent misread; cfg-flag eligibility criteria need explicit doc to prevent recurrence)
- **Severity:** N/A (NOT-A-BUG; rationale-preservation entry to prevent future re-litigation)
- **Surface:** `CoreFrameworks/ExecutionCore.hpp:295` (`lat_enabled` local var inside `ExecutionCore_Tick_Impl`)
- **Class:** Same shape as TECH_DEBT-019 (rationale preservation for rejected design choice)
- **What was considered (and rejected):** Migrating `lat_enabled` into the new `oms_cfg_flags` / `lifecycle_cfg_flags` bitmap as part of v5.14.9.F. The /readiness audit subagent flagged it as "NOT FOUND in ControllerConfig — must add" because the original plan claimed both partial_exit_enabled + lat_enabled would migrate.
- **Why rejected (verified during step 0 inventory):** `lat_enabled` is NOT a cfg field. It's a per-Tick local variable inside `ExecutionCore_Tick_Impl<F, LAT_ENABLED, PAIR_BRANCHLESS>` template function. Three structural reasons it can't migrate:

  1. **Compile-time elision:** When `LAT_ENABLED=false` (production builds without `-DLATENCY_PROFILING`), `if constexpr (LAT_ENABLED)` block compiles out entirely. **Zero runtime cost** — no atomic load, no branch, no instructions. Migrating to a runtime cfg-flag bitmap REGRESSES this to ~1-2ns per tick perpetually paid in production. At 10M ticks/sec hot-path, that's ~10-20ms/sec of pure waste. Compounds against the 40-400ns hot-path budget that's been carefully tuned.

  2. **Per-core runtime mutability:** When `LAT_ENABLED=true`, the actual gate is `core->latency_stats.enabled.load(std::memory_order_relaxed)` — a per-core atomic. Operator can flip latency sampling on/off per-core via GUI live within a profiled binary. Migrating to engine-wide boot-frozen cfg LOSES this capability.

  3. **CLAUDE.md item 18(a) violation:** "DEFAULT-OFF safety gates use compile-time elision via `template <bool ENABLED>` + `if constexpr` so disabled state has zero cost (no branch, no instruction)". `lat_enabled` is the canonical example of this discipline. Cfg-flag migration is an active violation.

- **Decision:** v5.14.9.F migrates only OMS-DOMAIN-PROPER cfg booleans. `lat_enabled` stays as-is (template-bool + per-core atomic). Domain reframed: `FOREACH_OMS_CFG_FLAG` → `FOREACH_LIFECYCLE_CFG_FLAG` covering 3 position-exit-mechanic flags (partial_exit_enabled + breakeven_on_partial + breakeven_on_profit).

- **Cfg-flag eligibility criteria (codified by this entry):** for a boolean to be cfg-flag-bitmap-eligible, ALL of the following must hold:
  1. **Boot-frozen:** value loaded at startup; not mutated at runtime
  2. **Engine-wide OR per-core-via-override:** not per-core via runtime atomic (those use ParameterSlot pattern)
  3. **Hot-path-tolerant:** runtime read of bitmap bit (~1-2ns) is acceptable cost
  4. **No compile-time elision benefit:** the flag isn't a candidate for `template <bool>` + `if constexpr` removal
  5. **Cfg-domain-coherent:** semantically belongs to one of the 5 domains (LIFECYCLE / GATE / RISK / ML / OPS) or warrants a new domain

  If ANY of (1)-(4) fails, the boolean is NOT cfg-flag-eligible. Use ParameterSlot atomic, template-bool elision, or local computation instead.

- **Why this entry exists (NOT-A-BUG):** future audit subagents may make the same mistake (assuming "boolean used in code = cfg-flag-eligible"). This entry codifies the eligibility criteria as a queryable check. Future /dod-audit Pattern 3e (bit-packing candidates) should reference this entry; future /readiness Check 19 (file:line claims) should validate cfg-flag eligibility against these criteria.

- **Cost:** 0h (no work to do; documentation only)

- **Trigger to revisit:** if the latency-profiling subsystem itself is rewritten (e.g., replaced with hardware perf counters that don't need per-core atomic flip), revisit whether the compile-time-elision pattern is still load-bearing. Until then: status NOT-A-BUG.

- **Status:** NOT-A-BUG (preserved as rationale)

- **Cross-ref:** v5.14.9.F step 0 finding (2026-05-10); `CoreFrameworks/ExecutionCore.hpp:288` (template signature); CLAUDE.md item 18 (slow-path latency reduction priority — sub-clause (a)); `DESIGN_SPECS/framework-patterns/heterogeneous-registry-pattern.md` "What's NOT cfg-flag-eligible" section (codifies criteria above).

---

### TECH_DEBT-024 — `breakeven_on_profit` dormant cfg field ✅ CLOSED v5.15.2

```yaml
id: TECH_DEBT-024
title: breakeven_on_profit dormant cfg field
severity: low
surface_tags: [cfg-flow, slow-path]
trigger: sub-ship-v5.15.2
status: closed
opened: 2026-05-10
closed: 2026-05-12
related_specs: []
```

- **Created:** 2026-05-10 by v5.14.9.F step 0 inventory
- **Severity:** LOW (operator-facing dormant feature; no functional impact)
- **Surface:** `CoreFrameworks/ControllerConfig.hpp` declaration + parser; FOREACH_LIFECYCLE_CFG_FLAG bitmap entry
- **What was deferred:** `breakeven_on_profit` cfg bit was declared + parsed + bitmap-allocated (FOREACH_LIFECYCLE_CFG_FLAG via v5.14.9.F migration) but had ZERO read sites. Operators could set it in engine.cfg; engine accepted the value without applying it.
- **Closure (v5.15.2.C):** Wired up via new slow-path helper `EventLoop_BreakevenOnProfit` + `EventLoop_BreakevenOnProfitOneCore` (`CoreFrameworks/ControllerEventLoop.hpp`). Mirrors the existing trailing-SL OneCore/Wrapper precedent. When the bit is set and an open position's gain_pct exceeds round-trip taker fees (2 × fee_rate_taker), ratchets `pending_params.ratchet_sl` to fee-floored breakeven (entry × (1 − 3 × fee_rate_taker)). Max-write semantics compose cleanly with trailing-SL ratchet (trailing wins via max once gain exceeds tp_hold_score; breakeven holds the floor below). Called from both live slow-path (`EngineSharded.hpp` near TrailingSLRatchet call site at ~line 2044) AND backtest driver (`ShardedBacktestDriver.hpp` near TrailingSLRatchet call site at ~line 376). DORMANT marker removed from registry doc string. Cost: ~80-150ns per active position per slow-path cycle when bit set; bit unset → wrapper early-exits in ~1ns. Below 100µs slow-path budget.
- **Status:** ✅ **CLOSED v5.15.2 (2026-05-12).**
- **Cross-ref:** v5.14.9.F (FOREACH_LIFECYCLE_CFG_FLAG bitmap migration); v5.15.2 ship; `CoreFrameworks/ControllerEventLoop.hpp` EventLoop_BreakevenOnProfit; `CoreFrameworks/LifecycleCfgFlagRegistry.hpp:58` (DORMANT marker removed).

---

### TECH_DEBT-027 — Locale pinning gap in `Bandit_SaveJSON` (LC_NUMERIC drift risk)

```yaml
id: TECH_DEBT-027
title: Locale pinning gap in Bandit_SaveJSON (LC_NUMERIC drift risk)
severity: medium
surface_tags: [wire-format, ml-inference]
trigger: sub-ship-v5.14.10.C
status: closed
opened: 2026-05-10
closed: 2026-05-10
related_specs: [DESIGN_SPECS/wire-format-patterns/wire-format-byte-preservation-discipline.md]
```

- **Created:** 2026-05-10 by /dod-audit run on v5.14.10-bayesian-thompson-bandit plan
- **Severity:** MEDIUM
- **Surface:** `ML_Headers/BanditLearning.hpp:369-435` (Bandit_SaveJSON); also `ML_Headers/BanditLearning.hpp:503-...` (Bandit_LoadJSON parser side)
- **What's deferred:** Bandit_SaveJSON does NOT pin `LC_NUMERIC=C` via `uselocale(newlocale(LC_NUMERIC_MASK, "C", 0))` before its `fprintf(..., "%.17g", ...)` calls for `weights[]` + `cum_reward[]`. Engine running under non-C locale (e.g., `LC_NUMERIC=de_DE`) would write `0,55` instead of `0.55`; load round-trip via `tt::parse_double_fast_advance` (locale-immune via `from_chars`) would parse `0` (truncated at comma) → silent state corruption. Same gap exists in any other JSON writer using `%g` family without pinning.
- **Why deferred (not effort-avoidance):** v5.14.10's MEDIUM-2 finding (Thompson_SaveJSON locale pinning) addresses the Thompson side; opportunistic to fold Bandit_SaveJSON fix in same ship. But Bandit_SaveJSON gap pre-dates v5.14.10 and isn't strictly v5.14.10's scope. Current production deployments operate under default `LC_NUMERIC=C` so the bug is dormant. Real-world trigger requires operator to set non-C locale environment before launching engine — uncommon but possible (e.g., systemd unit inheriting user locale; Docker container with locale config).
- **Cost estimate:** ~15-20 LOC across save + load (add `uselocale` save-restore around fprintf body; verify `tt::parse_double_fast_advance` is locale-immune already — it is per v5.11.4.C migration). NEGLIGIBLE risk (additive defensive code; preserves existing format bytes when LC_NUMERIC=C — the common case).
- **Trigger:** Address (a) opportunistically when v5.14.10's MEDIUM-2 Thompson_SaveJSON locale pinning is implemented (same file family; same pattern; ~5 extra LOC), OR (b) when an operator reports non-C locale corruption, OR (c) at next /parity-check that walks wire-format byte-preservation surfaces.
- **Status:** CLOSED 2026-05-10 by v5.14.10.C (ca4259f) — locale pinning added to Bandit_SaveJSON via uselocale(newlocale(LC_NUMERIC_MASK, "C", 0)) around fprintf body + uselocale(prev) + freelocale before fclose. Same pattern as ModelInference.hpp:1830-1940 stamp_write_for_model precedent. Applied opportunistically with v5.14.10.C's Thompson_SaveJSON locale pinning.
- **Cross-ref:** /dod-audit 2026-05-10 v5.14.10 thompson report MEDIUM-2 finding; `DESIGN_SPECS/wire-format-patterns/wire-format-byte-preservation-discipline.md` Layer 2 (locale pinning at emit construction); `ML_Headers/ModelInference.hpp` stamp_write_for_model v5.14.8.A.merged precedent for the canonical 3-line pattern; v5.14.10.C commit ca4259f.

---

### TECH_DEBT-028 — Bool-as-uint8_t PerCoreSnap fields migrated to state_flags bitmap ✅ CLOSED v5.15.1

```yaml
id: TECH_DEBT-028
title: Bool-as-uint8_t PerCoreSnap fields migrated to state_flags bitmap
severity: low
surface_tags: [gui-thread, bitmap-packed, registry]
trigger: sub-ship-v5.15.1
status: closed
opened: 2026-05-10
closed: 2026-05-12
related_specs: [DESIGN_SPECS/framework-patterns/bitmap-flag-api.md]
```

- **Created:** 2026-05-10 by /merge-scan re-audit on v5.14.10 amended plan (finding N4)
- **Severity:** LOW (cosmetic; no functional impact; no parity risk)
- **Surface:** PerCoreSnap struct fields in `DataStream/EngineTUI.hpp`
- **Status:** ✅ **CLOSED v5.15.1 (2026-05-12).** 4 bool-as-uint8_t PerCoreSnap fields (`ml_scaler_present`, `drift_breached`, `drift_kill_tripped`, `core_kill_tripped`) migrated to the existing `state_flags` uint16_t bitmap (4 new entries on `FOREACH_PER_CORE_STATE_FLAG`: ML_SCALER_PRESENT, DRIFT_BREACHED, DRIFT_KILL_TRIPPED, CORE_KILL_TRIPPED). Registry post-migration: 7 + 4 = 11 of 16; 5 bits headroom. Reuses the existing `state_flags` bitmap from v5.14.9.B.2 (no new bitmap surface; cohort homogeneity preserved per CLAUDE.local.md cohort-audit rule). All read sites (MLStatusPanel.hpp, DashboardPanels.hpp ×8) + write sites (ShardedSnapshot.hpp ×2) + tests migrated to STATE_FLAG_IS_SET / SET / CLR. Saves 4 bytes per PerCoreSnap. Engine-side fields (ExecutionCore.core_kill_tripped + drift_history.breached + drift_history.kill_tripped on ControllerEventLoop) intentionally STAY as-is — only the snapshot publication side moves to bitmap.
- **Cross-ref:** v5.14.9.B.2 (`PerCoreSnap state_flags uint16_t` migration; canonical precedent); v5.14.9.H (`ShardedSnapshot.any_scaler_present + any_scaler_failed` bitmap; same pattern); CLAUDE.md item 20 (bit-packed flag storage via BITMAP_* API); `DESIGN_SPECS/framework-patterns/bitmap-flag-api.md`; v5.15.1 ship.

---

### TECH_DEBT-033 — `/readiness` skill wider-build verification check ✅ CLOSED v5.15.2

```yaml
id: TECH_DEBT-033
title: /readiness skill wider-build verification check
severity: medium
surface_tags: [ci-tooling, test-infrastructure]
trigger: sub-ship-v5.15.2.D
status: closed
opened: 2026-05-12
closed: 2026-05-12
related_specs: []
```

- **Created:** 2026-05-12 by v5.14.post1 patch (train_model_worker_fn migration gap)
- **Severity:** MEDIUM (discipline gap; missed sites in mechanical migration sweeps)
- **Surface:** `tick-trader-percore-workspace/claude-skills/readiness/SKILL.md`
- **What was deferred:** /readiness audited ~24 items pre-coding; none verified
  that the previous sprint's close ran `./build.sh gui suite tsan asan all`
  (not just `test`). v5.14.post1 was the warning shot — the wider build
  catches BacktestPanels.hpp + GUI panel consumers that test target skips.
- **Closure (v5.15.2.D):** /readiness Check 26 added — verify last sprint's
  postmortem documents `./build.sh gui suite tsan asan all` GREEN result;
  flag if only `./build.sh test` was run.
- **Closure (v5.15.2.D):** /readiness Check 31 added (Check 26 placeholder reserved for v5.14.E.1 symmetry-test rule; Check 31 is the next free slot). Runs ALWAYS at audit start. Verifies predecessor postmortem documents `./build.sh gui suite tsan asan all` GREEN result (grep + commit-log scan). Non-blocking but flags risk that GUI/sanitizer-only compile errors lurk in the predecessor's surface area.
- **Status:** ✅ **CLOSED v5.15.2.D (2026-05-12).**
- **Cross-ref:** v5.14.post1 patch + postmortem; `tick-trader-percore-workspace/claude-skills/readiness/SKILL.md` Check 31 (added v5.15.2); v5.15.2 ship.

---

### TECH_DEBT-037 — Cfg-derived inference_cfg_* fields live in FOREACH_STAMP_BOUND_MODEL_CONST, not FOREACH_STAMP_BOUND_CFG (taxonomy drift)

```yaml
id: TECH_DEBT-037
title: Cfg-derived inference_cfg_* fields live in FOREACH_STAMP_BOUND_MODEL_CONST, not FOREACH_STAMP_BOUND_CFG (taxonomy drift)
severity: low
surface_tags: [registry, wire-format, ml-inference, cfg-flow]
trigger: sub-ship-v5.15.5.A.7
status: closed
opened: 2026-05-12
closed: 2026-05-12
related_specs: [DESIGN_SPECS/framework-patterns/autopopulate-pattern-for-production-caller-class.md]
```

- **Created:** 2026-05-12 by v5.15.3.A.1 helper extraction
- **Severity:** LOW (manual population works; just taxonomic asymmetry)
- **Surface:** `ML_Headers/StampHelper.hpp:158-187` (helper section 2a
  with cfg-derived model-const manual population); registry-tuple
  taxonomy split between FOREACH_STAMP_BOUND_CFG and
  FOREACH_STAMP_BOUND_MODEL_CONST
- **What's deferred:** `inference_cfg_confidence_threshold_scale`,
  `inference_cfg_barrier_gate_enabled`,
  `inference_cfg_confidence_hard_block_threshold`,
  `inference_cfg_held_out_fraction`,
  `inference_cfg_bandit_blend_ratio`,
  `inference_cfg_fee_rate_maker`, `inference_cfg_fee_rate_taker`,
  `training_poll_interval` are cfg-DERIVED but classified as
  model-const in the registry split (v5.14.8.A.merged historical
  taxonomy). STAMP_CFG_AUTOPOPULATE doesn't reach them; helper
  must manually `inf.X = cfg.X` for each. Adding a new cfg-derived
  inference_cfg_* field today needs both a registry entry AND a
  manual line in the helper section 2a.
- **Why deferred:** The proper fix has 2 options: (a) migrate these
  entries from FOREACH_STAMP_BOUND_MODEL_CONST to
  FOREACH_STAMP_BOUND_CFG so STAMP_CFG_AUTOPOPULATE auto-flows
  them (requires byte-equivalence verification + per-entry
  emit_when predicate restructure since registry-row shape
  differs between the two macros); or (b) extend
  STAMP_CFG_AUTOPOPULATE to optionally take cfg→stamp_field
  mappings (requires registry tuple extension; affects all 22
  current FOREACH_STAMP_BOUND_CFG entries). Either option is
  larger than v5.15.3 scope; manual section 2a works correctly
  today.
- **Cost estimate:** ~2-3h (option a; per-entry migration with
  byte-equivalence check) OR ~3-4h (option b; AUTOPOPULATE extension)
- **Trigger:** Address when (a) operator adds 3+ new cfg-derived
  inference_cfg_* fields in one sprint making manual section 2a
  painful, OR (b) v5.X+ AUTOPOPULATE consolidation sprint takes
  this on alongside TECH_DEBT-036 architectural-field redesign.
- **Status:** ✅ **CLOSED v5.15.5.A.7 (2026-05-12).** New
  `MemHeaders/CfgDerivedInferenceCfgRegistry.hpp` introduces single-source-of-truth
  registry for cfg-derived inference_cfg_* fields (3-col tuple:
  `name, cfg_extraction_expr, gate_when`). Companion macro
  `INFERENCE_CFG_AUTOPOPULATE(inf, cfg)` walks the registry + populates
  `inf.inference_cfg_<name>` via prefix-aware token-paste. Replaces the
  ~20-line manual section 2a at `ML_Headers/StampHelper.hpp:168-187`
  with ONE expansion. 11 entries today (7 existing migrated + 4 v5.15.5.A.7
  per-horizon barrier cohort). Future cfg-derived inference_cfg_* fields
  become 2 X-macro registry rows (MODEL_CONST entry for ModelHandle field +
  CFG_DERIVED entry for population); NO manual code; cannot drift.
  3rd application of `autopopulate-pattern-for-production-caller-class.md`
  pattern (after STAMP_CFG_AUTOPOPULATE v5.14.1.E.E.B + STAMP_MODEL_CONST_AUTOPOPULATE
  v5.14.8.A.merged quarantined at v5.15.3.A.1). Closes Class 18 mirror class
  at the cfg-derived MODEL_CONST surface permanently. New audit test asserts
  `FOREACH_CFG_DERIVED_INFERENCE_CFG_COUNT == 11`.
- **Cross-ref:** v5.15.5.A.7 ship; `MemHeaders/CfgDerivedInferenceCfgRegistry.hpp`;
  `ML_Headers/StampHelper.hpp:~165` (refactored to INFERENCE_CFG_AUTOPOPULATE call);
  `tick-trader-percore-workspace/DESIGN_SPECS/framework-patterns/autopopulate-pattern-for-production-caller-class.md`
  (3rd application referenced); TECH_DEBT-036 (sister AUTOPOPULATE-MODEL_CONST
  redesign still OPEN; quarantined macro separate concern); CLAUDE.md item 21.

---

### TECH_DEBT-040 — FOREACH_SESSION_PHASE cfg-side registry for 4 session_*_mult cfg fields

```yaml
id: TECH_DEBT-040
title: FOREACH_SESSION_PHASE cfg-side registry for 4 session_*_mult cfg fields
severity: low
surface_tags: [registry, cfg-flow, slow-path]
trigger: sub-ship-v5.15.5.B.5
status: closed
opened: 2026-05-12
closed: 2026-05-13
related_specs: [DESIGN_SPECS/refactor-patterns/cfg-flag-eligibility-criteria.md]
```

- **Created:** 2026-05-12 by v5.15.5.B audit (.B.5 surfaced consumer-side branchless conversion; cfg-side cohort registry deferred)
- **Severity:** LOW (4-instance cohort; semantically bounded; cfg-side refactor independent of consumer-side branchless dispatch)
- **Surface:**
  - `CoreFrameworks/ControllerConfig.hpp` — 4 `session_asian_mult / session_european_mult / session_us_mult / session_overnight_mult` cfg fields (cfg-side cohort)
  - `CoreFrameworks/ControllerEventLoop.hpp:2101-2106` — consumer-side 4-way if/else dispatch (CLOSED in v5.15.5.B.5 via branchless `SESSION_BY_HOUR[24]` lookup table + `session_mult_lookup[4]` indexed by `SESSION_*` enum)
- **Context:** v5.15.5.B.5 converts the CONSUMER-SIDE 4-way if/else to branchless table-lookup, but the CFG-SIDE remains 4 separate cfg fields with parallel cfg declarations / tooltips / parser entries / GUI inputs / use sites. That's the canonical X-macro registry candidate per CLAUDE.md item 13 (FOREACH_SESSION_PHASE(X) with `X(ASIAN, "asian", 0, 7) X(EUROPEAN, "european", 7, 13) ...` 4 rows; auto-flow cfg field decl + parser + GUI input + the consumer-side SESSION_BY_HOUR lookup table + session_mult_lookup array).
- **What's deferred:** `FOREACH_SESSION_PHASE(X)` registry on the cfg side. Adding a 5th session phase (e.g., extra granularity for Asia open / close) becomes 1 row + auto-flow vs today's 5-site touch.
- **Why deferred (not effort-avoidance):** v5.15.5.B is already a 9-sub-ship + umbrella ~1030-LOC ship; the cfg-side refactor is a separate concern (cfg declarations + parser + GUI). Bundling further bloats blast radius. Consumer-side branchless conversion (.B.5) captures the immediate latency-discipline win; cfg-side registry is a focused future cleanup that doesn't block.
- **Cost estimate:** ~80-120 LOC (registry definition + cfg field auto-gen + parser auto-gen + GUI input auto-gen + tooltip auto-gen + .B.5 lookup table refactor to use registry). MEDIUM-LOW.
- **Trigger:** Address (a) when adding a 5th session phase is required (currently no plans); (b) cfg-system cleanup sprint focused on cfg-field cohort discipline; (c) when FOREACH_<DOMAIN>_CFG_FLAG registry pattern (already established v5.14.9.F for bool cohorts) extends to enum/float cohorts via a new variant.
- **Status:** ✅ **CLOSED v5.15.5.B.5** — `FOREACH_SESSION_PHASE(X)` registry shipped (`CoreFrameworks/SessionPhaseRegistry.hpp`). 6-column tuple `X(NAME_U, name_l, START, END, DEFAULT_MULT, DOC)` drives: cfg field decl + default-init + parser entry (`ControllerConfig.hpp`); branchless `SESSION_BY_HOUR[24]` constexpr lookup table; per-consumer `session_mult_lookup[]` array (3 consumer sites all migrated: ControllerEventLoop.hpp:2305+, ShardedSnapshot.hpp:175+, PortfolioController.hpp:1503+). First explicit FLOAT-cohort cfg-registry variant; pattern documented for promotion in `DESIGN_SPECS/refactor-patterns/cfg-flag-eligibility-criteria.md` (subsection to add at .B umbrella).
- **Cross-ref:** `CoreFrameworks/SessionPhaseRegistry.hpp` (registry); `CoreFrameworks/ControllerConfig.hpp` (cfg field decl + default + parser auto-flowed via X-macro); `CoreFrameworks/ControllerEventLoop.hpp` + `CoreFrameworks/ShardedSnapshot.hpp` + `CoreFrameworks/PortfolioController.hpp` (3 consumer sites branchless-converted); CLAUDE.md item 13 + item 28.

---

### TECH_DEBT-082 — `.F.5` 3 unmigrated fields per-core eligibility audit (`confidence_ic_floor`, `lazy_rebuild_price_threshold_pct`, `exit_threshold`)

```yaml
id: TECH_DEBT-082
title: .F.5 3 unmigrated fields per-core eligibility audit (confidence_ic_floor, lazy_rebuild_price_threshold_pct, exit_threshold)
severity: medium
surface_tags: [cfg-flow, registry, parser]
trigger: sub-ship-v5.15.5.F.4d
status: closed
opened: 2026-05-16
closed: 2026-05-16
related_specs: [DESIGN_SPECS/refactor-patterns/cfg-flag-eligibility-criteria.md]
```

- **Created:** 2026-05-16 (backfill per `.F.4d` pre-coding subplan verification audit; `.F.5` SKETCH plan listed 13 fields for per-core override; 2 bandit/thompson absorbed by `.F.4d` Thread B; 9 of remaining 11 found in `FOREACH_PER_CORE_CFG_FIELD` at HEAD; **3 still in legacy flat-struct form** at `CoreFrameworks/ControllerConfig.hpp` with manual parser cases)
- **Severity:** LOW-MED (eligibility decision; audit + categorize before migration; one outcome may legitimately be "stay GLOBAL")
- **Surface:** `CoreFrameworks/ControllerConfig.hpp` lines 770 (`lazy_rebuild_price_threshold_pct`), 788 (`exit_threshold`), 970 (`confidence_ic_floor`) — struct fields declared flat. Parser cases at :2360, :2368, :2720 (manual `strcmp` + `atof` blocks). Not enrolled in `FOREACH_PER_CORE_CFG_FIELD` or `FOREACH_GLOBAL_CFG_FIELD` at HEAD.
- **What's deferred:** (1) audit per `DESIGN_SPECS/refactor-patterns/cfg-flag-eligibility-criteria.md` whether each field should be per-core (`.F.5` SKETCH said yes; sketch may have been wrong) OR stays GLOBAL; (2) for fields eligible for per-core: migrate from flat struct + manual parser to `FOREACH_PER_CORE_CFG_FIELD` row + `tt::cfg_*_field<T>` auto-flow; (3) for fields staying GLOBAL: migrate from flat struct + manual parser to `FOREACH_GLOBAL_CFG_FIELD` row (closes Class 23 manual-parser anti-pattern for these 3 sites regardless of per-core outcome).
- **Why deferred (not effort-avoidance):** `.F.5` SKETCH was SUPERSEDED by `.F.4d` MERGED + the bandit/thompson sub-cohort was absorbed by `.F.4d` Thread B. The remaining 3 fields' migration status was not visibly tracked. The fields are functional at HEAD (manual parser works); discipline is canonical-shape cohort harmonization rather than functionality.
- **Cost estimate:** ~1-2h focused (audit + 3-row registry migration per outcome; mechanical).
- **Trigger:** Bundle with `.F.4f` cleanup ship (TECH_DEBT-076 to -080 plus this for cohort-harmonization completeness) OR include in `.F.4d` Thread B as additional 3-field cohort migration if scope permits (decision: see `.F.4d` merged plan body Thread B Section 5.G-J — operator/coder decision at coding time).
- **Status:** **CLOSED at v5.15.5.F.4d 2026-05-16.** All 3 fields migrated to FOREACH_PER_CORE_CFG_FIELD as KIND_DOUBLE_PCT (lazy_rebuild_price_threshold_pct) + KIND_DOUBLE (exit_threshold + confidence_ic_floor; the latter stays `double` storage per H4 non-accounting threshold). Manual parser cases at ControllerConfig.hpp:2362-2365, 2370-2373, 2722-2725 DELETED. Class 23 manual-parser anti-pattern closed at 3 sites. Legacy flat field decls + ControllerConfig_Default init lines KEPT for legacy compat per .F.4d dual-track pattern (full removal at .F.4f cleanup ship per CLAUDE.local.md sprint state). `.F.5` charter residual closed completely — `.F.4f` Phase 7 conditional fold-in no longer needed.
- **Cross-ref:** `subplans/2026-05-13-v5.15.5.F.5-per-core-thompson-bandit-overrides.md` (SUPERSEDED SKETCH; 13-field cohort enumeration); `DESIGN_SPECS/refactor-patterns/cfg-flag-eligibility-criteria.md` (per-core eligibility framework); `CoreFrameworks/CfgFieldRegistry.hpp:412+` (`FOREACH_PER_CORE_CFG_FIELD` canonical registry); CLAUDE.md item 23 (Class 23 anti-pattern — manual parser); CLAUDE.md item 19 (structural fix preferred when bug class can recur); commit `fd9ad8e v5.15.5.F.4d MERGED WIP-checkpoint: TECH_DEBT-082 close — 3 .F.5 residual fields migrate to FOREACH_PER_CORE_CFG_FIELD`.

---

### TECH_DEBT-083 — IWYU hygiene sweep: 8 headers use `uintN_t` without direct `<cstdint>` / `<stdint.h>` include

```yaml
id: TECH_DEBT-083
title: IWYU hygiene sweep — 8 headers use uintN_t without direct <cstdint> / <stdint.h> include
severity: low
surface_tags: [ml-inference]
trigger: sub-ship-v5.15.5.F.4d
status: closed
opened: 2026-05-16
closed: 2026-05-16
related_specs: []
```

- **Created:** 2026-05-16 (surfaced during `.F.4d` Step 1.C coding when removing an unused `<cstdint>` include from `ML_Headers/bandit_dispatch_table.hpp` exposed a transitive-include chain dependency; 2 chain-breakers — `CoreFrameworks/ParseFast.hpp` + `ML_Headers/BanditLearning.hpp` — fixed inline; 8 others remain latent)
- **Severity:** LOW (latent IWYU gap; not breaking current build because of transitive include chains in canonical use; would break if include order changes OR if a new header is added before the transitive cstdint-pull lands)
- **Surface:** 8 headers that use `uint64_t` (or `uint32_t`) without directly including `<cstdint>` or `<stdint.h>`:
  - `ML_Headers/CoreModelZoo.hpp`
  - `ML_Headers/ModelInference.hpp`
  - `ML_Headers/RewardTracker.hpp`
  - `ML_Headers/StampBoundModelConstRegistry.hpp`
  - `ML_Headers/WelfordStats.hpp`
  - `Strategies/MeanReversion.hpp`
  - `Strategies/Momentum.hpp`
  - `Strategies/RegimeDetector.hpp`
- **What's deferred:** add `#include <cstdint>` to each of the 8 headers; ~1-line mechanical addition per file; total ~8 lines + brief IWYU-discipline comment. Closes the latent class (any future include-order change won't expose new chain-breakers).
- **Why deferred (not effort-avoidance):** scope guard on `.F.4d` — pre-coding gate set scope at bandit/thompson 5-state + framework consolidation; IWYU hygiene is unrelated to that scope. Mechanical sweep belongs in a cleanup window. Per CLAUDE.local.md `feedback_consult_on_audit_findings` + scope-creep discipline: surface for operator triage, don't auto-sweep.
- **Cost estimate:** ~30 min focused (8 mechanical edits + verify clean build).
- **Trigger:** Bundle with `.F.4f` cleanup ship Phase 2 (TECH_DEBT-077 bitmap-bool migration also touches these surfaces) OR standalone micro-cleanup post-`.F.4d`. Operator decision on timing.
- **Status:** **CLOSED at v5.15.5.F.4d 2026-05-16.** All 7 remaining headers (CoreModelZoo + ModelInference + RewardTracker + WelfordStats + MeanReversion + Momentum + RegimeDetector) gained explicit `#include <cstdint>`. 8th header (StampBoundModelConstRegistry.hpp) was already fixed inline during prior-session WIP. Latent IWYU class closed structurally — any future include-order change can't expose new chain-breakers.
- **Cross-ref:** discovered during `.F.4d` Step 1.C coding (this session 2026-05-16); fixed inline: `CoreFrameworks/ParseFast.hpp:37` + `ML_Headers/BanditLearning.hpp:47` (both got explicit `#include <cstdint>`); CLAUDE.md item 19 (structural fix preferred when bug class can recur — closing the class via codebase-wide sweep is the right structural answer); commit `cf906a7 v5.15.5.F.4d MERGED WIP-checkpoint: TECH_DEBT-083 close — IWYU sweep (7 headers add explicit <cstdint>)`.

---

### TECH_DEBT-084 — Full symmetric rename of `thompson_bandits` → `buy_thompson_bandits` + FOREACH_BANDIT_SIDE auto-gen across all 6 per-side symbol families

```yaml
id: TECH_DEBT-084
title: Full symmetric rename of thompson_bandits → buy_thompson_bandits + FOREACH_BANDIT_SIDE auto-gen across all 6 per-side symbol families
severity: low
surface_tags: [registry, ml-inference, wire-format]
trigger: sub-ship-v5.15.5.F.4d
status: closed
opened: 2026-05-16
closed: 2026-05-16
related_specs: [DESIGN_SPECS/framework-patterns/sink-fn-pointer-for-optional-side-effect-pattern.md]
```

- **Created:** 2026-05-16 during `.F.4d` Step 1.D Pattern 5 sink-fn-pointer design (this session) — explicit design decision to HAND-MIRROR exit-side rather than full FOREACH_BANDIT_SIDE auto-gen now, to avoid a cascade rename of existing `thompson_bandits` field across ~50 call sites. Captured as future cleanup so the design intent isn't lost.
- **Severity:** LOW (design-quality hygiene; current hand-mirror works correctly; future addition of a 3rd side — per-symbol? per-strategy? — would need 4× hand-writing per fn family without this cleanup)
- **Surface:** rename `EnsembleModelZoo<F>::thompson_bandits` → `buy_thompson_bandits` + `thompson_update_fn` → `buy_thompson_update_fn` + `last_predicted_thompson_arm` → `last_predicted_buy_thompson_arm` + `MASK_EZOO_THOMPSON_READY` → `MASK_EZOO_BUY_THOMPSON_READY` + `EnsembleModelZoo_InitThompsonBandits` → `EnsembleModelZoo_InitBuyThompsonBandits` (+ symmetric for `_Save`/`_Load`/`_State` JSON paths). All ~50 call sites + persistence file paths + test fixtures + GUI display references migrate.
- **What's deferred:** full FOREACH_BANDIT_SIDE auto-gen across all 6 per-side symbol families per § G.1 of `.F.4d` merged plan body. Replaces hand-mirror at `.F.4d` (which produces `thompson_bandits` + `thompson_exit_bandits` asymmetric naming + duplicate `_InitThompsonBandits`/`_InitExitThompsonBandits` fn bodies) with single X-macro expansion per consumer site:
  ```cpp
  #define _DEFINE_INIT_FN(side) \
      template <unsigned F> \
      inline void EnsembleModelZoo_Init##side##ThompsonBandits(EnsembleModelZoo<F>* ezoo, ...) { \
          /* body parameterized; field accessed as ezoo->side##_thompson_bandits[r] via token-paste */ \
      }
  FOREACH_BANDIT_SIDE(_DEFINE_INIT_FN)
  ```
  Adding a 3rd side (e.g., per-symbol Thompson) becomes 1 row in `FOREACH_BANDIT_SIDE(X) X(buy) X(exit) X(per_symbol)` → 6 mirror sites auto-generate (init fn / load fn / save fn / dispatch table entry / sink-fn field / init flag).
- **Why deferred (not effort-avoidance):** cascade rename of `thompson_bandits` field affects ~50 call sites across ML_Headers/ + GUI/ + tests/ + persistence file paths. Scope-creep risk for `.F.4d` which is already MED-HIGH risk. Per `feedback_overengineering_boundary_when_future_easier` — at the borderline of "harder now / easier future" the rule is "pick harder when future MUCH easier". Here the future-easier multiplier is modest (2 sides today, 3-4 projected; ~30-50 lines saved per future side). Defer is legitimate cost/benefit call.
- **Cost estimate:** ~6-10h focused (cascade rename via careful Edit replace_all + per-site verification + test fixture sweep + persistence file path migration + GUI display refresh + back-compat alias for old `thompson_state.json` filename → new `buy_thompson_state.json`).
- **Trigger:** when a 3rd per-side axis (per-symbol Thompson? per-strategy Thompson?) is proposed — at that point the rename cost is amortized by the auto-gen value. OR bundled into `.F.4f` cleanup ship if scope permits. OR standalone hygiene ship post-`.F.4e`.
- **Status:** **CLOSED at v5.15.5.F.4d 2026-05-16 (cascade rename portion — Phase 1 + Phase 2 per postmortem).** Cascade rename of 6 patterns across 14 files (200+ refs; word-boundary sed in collision-safe order): thompson_exit_bandits → exit_thompson_bandits + last_predicted_thompson_arm → last_predicted_buy_thompson_arm + MASK_EZOO_THOMPSON_READY → MASK_EZOO_BUY_THOMPSON_READY + EnsembleModelZoo_InitThompsonBandits → EnsembleModelZoo_InitBuyThompsonBandits + thompson_bandits → buy_thompson_bandits + thompson_update_fn → buy_thompson_update_fn. Persistence file path migration: thompson_state.json → buy_thompson_state.json + thompson_exit_state.json → exit_thompson_state.json with Load-side back-compat alias for existing on-disk model bundles. **Naming asymmetry closed.** Full FOREACH_BANDIT_SIDE auto-gen (X-macro expansion across 6 per-side symbol families replacing hand-mirror init/load/save fn bodies) DEFERRED to TECH_DEBT-085 as supplementary work — naming is symmetric so adding a 3rd side is mechanical even with hand-mirror.
- **Cross-ref:** `.F.4d` merged plan body § G (FOREACH_BANDIT_SIDE auto-mirror full design); `ML_Headers/CoreModelZoo.hpp` `EnsembleModelZoo<F>` struct (now symmetric naming); `ML_Headers/ThompsonBandit.hpp` `ThompsonUpdateFn` typedef + noop/real wrappers (sink-fn infrastructure ready for auto-gen consumer); CLAUDE.md item 19 (structural fix preferred when bug class can recur); CLAUDE.md item 31 (framework-driven extensibility); `DESIGN_SPECS/framework-patterns/sink-fn-pointer-for-optional-side-effect-pattern.md` Pattern 5 — full auto-gen would generalize this; commit `f9e1882 v5.15.5.F.4d MERGED WIP-checkpoint: TECH_DEBT-084 close — FOREACH_BANDIT_SIDE cascade rename`.

---

### TECH_DEBT-086 — `.F.4d` doc residual: RECURRING_BUG_PATTERNS amendments + DESIGN_PHILOSOPHY § 2 H15-H20 narrative + DESIGN_SPECS README catalog verification

```yaml
id: TECH_DEBT-086
title: .F.4d doc residual — RECURRING_BUG_PATTERNS amendments + DESIGN_PHILOSOPHY § 2 H15-H20 narrative + DESIGN_SPECS README catalog verification
severity: low
surface_tags: []
trigger: sub-ship-v5.15.5.F.4d.1
status: closed
opened: 2026-05-16
closed: 2026-05-16
related_specs: []
```

- **Created:** 2026-05-16 (at v5.15.5.F.4d.1 planning consult — Decision 2 lock: bundle as TECH_DEBT-086 + fold into `.F.4d.1.D` ship close auto-writes; Option B separate doc-only mini-ship rejected as MVP-shaped per `feedback_no_mvp_for_plumbing_only_for_unknown_unknowns`)
- **Severity:** LOW (doc-residual; no code-functional impact). **Cost-to-defer IS real** though: `/bug-check` accuracy degrades without Class 30 in RECURRING_BUG_PATTERNS registry (next OMS sibling-array enrollment drift goes uncaught); cold-pickup orientation drifts without H15-H20 narrative in DESIGN_PHILOSOPHY § 2; `/handoff` skill load coverage misses 4 Thread A specs without catalog verification.
- **Surface:**
  - `DOCS/RECURRING_BUG_PATTERNS.md` (engine repo) — Class 30 codification + Class 24/25/28 amendments
  - `tick-trader-percore-workspace/DOCS/DESIGN_PHILOSOPHY.md` § 2 — H15-H20 narrative addition (currently codified in CLAUDE.md table; family-grouped philosophy doc narrative still pending)
  - `tick-trader-percore-workspace/DESIGN_SPECS/README.md` — catalog count update + Stage 3 ACTIVE marker verification (4 NEW Thread A specs from `.F.4d`: metadata-bit-driven-derived-filter-framework + sidecar-override-pattern-for-registry-auto-flows + meta-registry-pattern-for-codebase-registry-discipline + framework-composition-overview)
- **What's deferred:**
  1. **Class 30 codification** in RECURRING_BUG_PATTERNS.md — OMS sibling-array enrollment drift (codified `.F.4c.3` WIP2d-1.B.0 + structurally closed at `.F.4d` via FOREACH_OMS_PER_SLOT_FIELD 3→5 row enrollment; sister to Check 8 cohort eligibility CI)
  2. **Class 24 amendments** — bandit/thompson attribution surface sister application + Thompson_Update wired via dispatch tables canonical example at `.F.4d`
  3. **Class 25 amendments** — OMS consumer sweep precedent at `.F.4d` (`PerCoreCfg<F>*` single-param sig threaded through TickRewardsFromLookback + TradeCloseReward + ControllerEventLoop exit-side)
  4. **Class 28 amendments** — 6 cmov sites closed at `.F.4d` (Bandit_Update / Thompson_Sample / ModelInference Predict + WeightedBlend / RollingTurnover / __builtin_expect bounds guard); Pattern 5 sink-fn-pointer canonical added; `/hft-audit` skill extended with branchless dispatch opportunity scan
  5. **DESIGN_PHILOSOPHY § 2 H15-H20 narrative** — family-grouped discussion paralleling CLAUDE.md hard-invariants table (H15 X-macro registry enrollment + H16 metadata-bit derived-filter completeness + H17 cfg struct auto-generated + H18 sidecar override discipline + H19 meta-registry topology + H20 branchless preferred for SP/HP)
  6. **DESIGN_SPECS/README.md catalog verification** — confirm all 4 Thread A specs carry Stage 3 ACTIVE marker; bump total count (currently shows "57+ patterns" + "~71 patterns total" at end; verify against actual file count); confirm Stage 3 ACTIVE rows are present in catalog table; cross-link from `.F.4d` ship-close commit
- **Why deferred (not effort-avoidance):**
  - **Ship-close scope guard at `.F.4d` MERGED** — coder time at `.F.4d` spent on Thread B FULL + Thread A foundation + 3 substantial TECH_DEBT fold-ins (-082/-083/-084 ~9-13h combined). Doc residual is mechanical writes that don't drive functional ship deliverable; bundling into next ship's auto-write boundary preserves single-ship coherence.
  - **Auto-write contract** (CLAUDE.local.md) is mandatory at sub-ship close → `.F.4d.1.D` ship close is the natural ledger boundary
  - **Separate doc-only mini-ship rejected** — MVP-shaped (small bounded ship for one concern) per `feedback_no_mvp_for_plumbing_only_for_unknown_unknowns` rule; doc-only mini-ship adds Version bump + tag + postmortem overhead for ~2-3h of doc work
  - **Per Decision 2 at `.F.4d.1` planning consult 2026-05-16** — Option A (TECH_DEBT-086 + fold into `.D`) selected per philosophy alignment (auto-write contract + no-MVP-for-plumbing + `.D`'s LOW-risk boundary fits doc work + saves ship cycle vs Option B separate mini-ship)
- **Cost estimate:** ~2-3h focused. Breakdown: RECURRING_BUG_PATTERNS amendments (Class 30 codification + 3 class amendments) ~1h + DESIGN_PHILOSOPHY § 2 H15-H20 narrative ~1h + DESIGN_SPECS README catalog verification + Stage 3 ACTIVE marker confirmation + count update ~30 min. LOW risk (doc-only; no code-functional impact).
- **Trigger:** **`.F.4d.1.D` ship close.** Per Decision 2 at `.F.4d.1` planning consult 2026-05-16 + CLAUDE.local.md auto-write contract (mandatory at sub-ship close). `.D` is the natural boundary — CI + fixture is the smallest sub-ship; doc residual is the same flavor (verification + cleanup); ship-close cadence matches. **Revision 2026-05-16:** Caramel directed "we should go ahead and deal with this" → execution moved up from `.F.4d.1.D` ship close to `.F.4d.1` planning session (this session). Doc-only work doesn't need a ship-cycle deferral when it can land in the current planning context; aging it well + closing before plan-body drafts so they reference up-to-date docs.
- **Status:** **CLOSED at v5.15.5.F.4d.1 planning 2026-05-16** (per Caramel revision: executed in planning session vs deferred to `.D`). All 6 deliverables landed:
  1. **Class 30 landing ship note appended** (`RECURRING_BUG_PATTERNS.md` after Severity line; clarifies `.F.4c.4`→`.F.4d` merge per Option G ratification)
  2. **Class 24 .F.4d closure update appended** (Thompson_Update wire gap structurally closed at `.F.4d` via `FOREACH_BANDIT_ALGORITHM` 3→5 + dispatch tables; cross-link to `multi-state-dispatch-with-per-state-update-metadata.md`)
  3. **Class 25 .F.4d sweep extension appended** (OMS consumer surface migration: TickRewardsFromLookback + TradeCloseReward + ControllerEventLoop exit-side; `PerCoreCfg<F>*` single-param sig threaded)
  4. **Class 28 .F.4d canonical additions appended** (6 new cmov sites — Bandit_Update + Thompson_Sample + ModelInference_Predict + WeightedBlend + RollingTurnover + __builtin_expect rare bounds guard; Pattern 5 sink-fn extension for Thompson_Update; H20 ratification cross-ref)
  5. **DESIGN_PHILOSOPHY § 2 H15-H20 promoted** from "Pending codification" sub-table to main hard-invariants table (codified `.F.4d` 2026-05-16); family grouping notes added explaining H1-H6 / H7-H8 / H9-H12 / H13-H14 / H15-H20 partitioning
  6. **DESIGN_SPECS/README.md catalog verified + count bumped 71→72** (4 Thread A specs confirmed Stage 3 ACTIVE; new Stage 2 DRAFT `type-erased-per-core-resource-handle-pattern.md` row added with 3 canonical applications cited)
- **Cross-ref:** `plans/v5.15-live-readiness/postmortems/2026-05-16-v5.15.5.F.4d-merged-postmortem.md` (predecessor; items deferred from `.F.4d` ship close listed in postmortem "Decisions captured" + Version.hpp comment block); `plans/v5.15-live-readiness/handoffs/2026-05-16-v5.15.5.F.4d.1-planning-handoff.md` Decision 3 ("Auto-writes residual from `.F.4d`"); `DOCS/RECURRING_BUG_PATTERNS.md` (target for Class 30 + amendments); `tick-trader-percore-workspace/DOCS/DESIGN_PHILOSOPHY.md` § 2 (target for H15-H20 narrative); `tick-trader-percore-workspace/DESIGN_SPECS/README.md` (catalog verification target); CLAUDE.local.md "Auto-write contracts" rule; `feedback_no_mvp_for_plumbing_only_for_unknown_unknowns` memory; CLAUDE.md item 19 (structural fix preferred — applies here at meta-level: codifying Class 30 in registry is structural fix against future drift recurrence).

---

### TECH_DEBT-108 — `double` STORAGE_T in FOREACH_PER_CORE_CFG_FIELD (H4 violation candidate) — CLOSED (verified compliant)

```yaml
id: TECH_DEBT-108
title: double STORAGE_T in FOREACH_PER_CORE_CFG_FIELD (H4 violation candidate) — verified compliant
severity: medium
surface_tags: [cfg-flow, registry, ml-inference, ci-tooling]
trigger: sub-ship-v5.15.5.F.4d.1.B.3
status: closed
opened: 2026-05-18
closed: 2026-05-18
related_specs: [DESIGN_SPECS/meta-disciplines/implementation-layer-blindspot-taxonomy.md]
```

- **Created:** 2026-05-18 (surfaced by NEW CI tool `tools/check_storage_t_coverage.py` at `.B.3` mid-coding META program landing)
- **Closed:** 2026-05-18 (same-day investigation; both rows verified compliant with H4 "display-only OK" exemption)
- **Severity:** MED (downgraded to N-A after investigation)
- **Surface:** 2 rows in `CoreFrameworks/CfgFieldRegistry.hpp` declare `double` STORAGE_T:
  - `:653` — `ensemble_min_agreement_pct` (DBL(0.0, 0.0, 1.0); voting threshold for ML horizon-agreement gate)
  - `:664` — `confidence_ic_floor` (DBL(0.02, -1.0, 1.0); rolling IC threshold for ML drift detection)
- **Investigation findings:**
  - **ensemble_min_agreement_pct read sites:** `Strategies/StrategyParameters.hpp:1084` (voting threshold comparison; NOT accounting); `ControllerConfig.hpp:1787` (default init); `ControllerConfig.hpp:2606` (parser). NO accounting-path read sites.
  - **confidence_ic_floor read sites:** `EngineSharded.hpp:2490` (drift gate comparison; NOT accounting); `ConfidenceScore.hpp:835` (comment); `MLStatusPanel.hpp:323` (GUI display). NO accounting-path read sites.
  - **Pre-existing explicit exemption documentation:** `ControllerConfig.hpp:316` comment explicitly states "double: ML voting threshold exemption (ensemble_min_agreement_pct only)" — confirms intentional design.
  - **H4 compliance:** Both rows are STATISTICAL THRESHOLDS / VOTING METRICS used for gate-decision comparison only. Neither flows into FPN-based accounting calculations. Per H4 "display-only OK" + extension to "threshold-only comparison" — compliant.
- **Resolution:** No migration needed. Both rows are intentional `double` exemptions for statistical/voting threshold use. CI tool finding is a false-positive at the `double` variant level — the tool can't distinguish "accounting double" (H4 violation) from "threshold double" (H4 compliant). Future CI tool extension could add metadata column to `H4_COMPLIANT_EXEMPTION` annotation per row.
- **Status:** **CLOSED 2026-05-18** (investigated + verified compliant + documented rationale)
- **Future improvement (LOW priority):** Extend `check_storage_t_coverage.py` to recognize H4-compliant exemption metadata (e.g., new `H4_THRESHOLD_EXEMPT` bit on metadata_flags column) — would auto-suppress false-positive `double` warnings on documented exemption rows. Not urgent — only 2 known exemptions; manual rationale suffices.
- **Cross-ref:** `tools/check_storage_t_coverage.py`; `DESIGN_SPECS/meta-disciplines/implementation-layer-blindspot-taxonomy.md` § B6; `CLAUDE.md` H4 invariant; `CoreFrameworks/ControllerConfig.hpp:316` (pre-existing exemption documentation).

---

### TECH_DEBT-109 — Skill SKILL.md drift audit (pragmatic triage executed; CLOSED)

```yaml
id: TECH_DEBT-109
title: Skill SKILL.md drift audit (pragmatic triage executed)
severity: low
surface_tags: [ci-tooling]
trigger: sub-ship-v5.15.5.F.4d.1.B.3
status: closed
opened: 2026-05-18
closed: 2026-05-18
related_specs: []
```

- **Created:** 2026-05-18 (deferred from META program at `.B.3` mid-coding per scope-bounded landing)
- **Refined scope 2026-05-18:** initial estimate "24 skills × hardcoded refs each" was based on raw grep count (250+ refs across 17 skills). Sampling 3 skills (/readiness 75 refs, /bug-check 6 refs, /dust 5 refs) revealed **majority of refs are LEGITIMATE WORKED EXAMPLES** (postmortem context, "added after vX.Y" annotations, "first canonical at vN" markers). These set discipline context for future readers — REMOVING them loses information.
- **Severity:** LOW (drift items are estimated 10-30 across 17 skills; bulk replace_all WRONG — needs per-ref classification)
- **Surface:** `claude-skills/<skill>/SKILL.md` for 24 skills. **Genuine drift patterns** (need fixing):
  - Skill description text citing sprint-specific phasing as if canonical (e.g., "for v5.15.5.F.4d.1.B.3 work")
  - Trigger conditions citing TECH_DEBT-N as the ONLY trigger (vs categorical trigger family)
  - Examples that use sprint-specific filenames in `<placeholder>` positions
  - "(NEW post-v5.15.5.F.4b)" descriptors that became "(LEGACY)" without update
- **Legitimate worked-example patterns** (KEEP — discipline context for future readers):
  - "First systematic application: v5.14.8.A pre-A.merged" (canonical reference)
  - "v5.4.0 postmortem F7-F10 motivation" (why-this-Check-exists context)
  - "Codified at v5.15.5.F.4d after Class N recurrence" (anti-pattern history)
- **What's deferred:** per-skill classification scan (~30-60 min per skill × 17 = ~10-15h FULL) OR pragmatic triage (~5 min per skill × 17 = ~1.5h scope-bounded; fix only obvious-drift instances + leave worked-example sections alone).
- **Why deferred (refined; NOT effort-avoidance):** Bulk-edit approach (initial idea) would LOSE legitimate worked-example context. Per-ref classification is genuine scope. Out of `.B.3` Step 1.6.3 critical path. Not blocking; cleanup polish.
- **Cost estimate:** ~1.5-2h pragmatic triage (recommended); ~10-15h full per-ref classification.
- **Trigger:** future maintenance ship dedicated to skill cleanup; OR ad-hoc when sprint-specific drift is noticed in a skill spec during routine work.
- **Status:** **CLOSED 2026-05-18** (pragmatic triage executed; 16 skills scanned with drift refs + 14 skills CLEAN baseline; per-ref classification preserved worked-example sections verbatim per discipline)
- **Resolution summary (2026-05-18 pragmatic triage):**
  - **Total skills scanned:** 30 SKILL.md files
  - **Skills CLEAN (0 drift refs to begin with):** 9 — `accounting-audit`, `dead-code-trace`, `dependency-chain-trace`, `finding-analyzer`, `foxlib-promotion`, `handoff` (zero refs to versions; later had stale-NEW markers fixed too), `patch-planner`, `precoding-audit-gate`, `sync-models`
  - **Skills WITH drift refs but ALL worked-example LEGITIMATE (KEPT verbatim):** 13 — `anti-spaghetti` (Stage 3 lifecycle), `ml-audit` (v5.9 canonical history), `parity-check` (v5.9 canonical history, ~64 refs all worked-example), `merge-scan` (v5.12 / v5.14 canonical refs), `trace-deps` (v5.14 canonical refs), `latency-track` (v5.12.1.B.3 motivating example), `dust` (v5.4.0 postmortem context), `plan-check` (v5.9 illustrative), `post-ship-audit` (concrete tag examples), `plan-draft` (Stage 2 lifecycle), `strategy-template` (v5.10/v5.11/v5.12 canonical refs), `sync-workspace` (v5.11.43 migration history), `test-strength-audit` (v5.14.9.D motivating example)
  - **Skills WITH genuine drift FIXED:** 11 — `bug-check` (5 sites), `dod-audit` (3 sites), `registry-fit-audit` (3 sites), `hft-audit` (1 site), `blindspot-scan` (1 sprint-specific example path), `plan-context-sweep` (1 stale "NEW" marker), `ship` (2 stale "NEW" markers including auto-write contract block), `handoff` (5 stale "NEW (post-2026-05-14)" markers + 1 stale sprint-specific dynamic-load row), `test-strength-audit` (1 "Post-2026-05-14 enhancement" preload-contract header), `trace-deps`/`bug-check`/`parity-check`/`merge-scan`/`ml-audit`/`hft-audit`/`latency-track`/`dust`/`dod-audit`/`readiness` (each had identical "Post-2026-05-14 enhancement — uniform parameter + preload contract" header that became standard skill structure — generalized to "Uniform parameter + preload contract")
  - **Total drift sites fixed:** ~22 fixes across 16 SKILL.md files
  - **Worked-example sections preserved:** ~225+ refs preserved verbatim (high preservation ratio = discipline working correctly per entry's criteria)
- **Accountability mechanism (retrospective):** Could still codify as M5 meta-discipline (`check_skill_md_sprint_refs.py`) if drift recurrence pattern emerges across future ships. Not urgent — manual per-ref classification cost was bounded (~45 min); CI tool ROI marginal at current cadence.
- **Cross-ref:** `claude-skills/precoding-audit-gate/SKILL.md` (canonical generalized precedent); META program at `.B.3` for context; `DESIGN_PHILOSOPHY.md` § 11.5 (where M5 codification would live if recurrence emerges); workspace commit `4c7aed6` (TECH_DEBT-109 CLOSED 2026-05-18).

---

### TECH_DEBT-112 — Skill structural audit closure (categorical-triggers-over-hardcoded-refs application)

```yaml
id: TECH_DEBT-112
title: Skill structural audit closure (categorical-triggers-over-hardcoded-refs application)
severity: medium
surface_tags: [ci-tooling, registry]
trigger: sub-ship-v5.15.5.F.4d.1.B.3
status: closed
opened: 2026-05-18
closed: 2026-05-18
related_specs: [DESIGN_SPECS/doc-disciplines/categorical-triggers-in-always-loaded-docs.md]
```

- **Created:** 2026-05-18 (concurrent with codification of `DESIGN_SPECS/doc-disciplines/categorical-triggers-in-always-loaded-docs.md` v1.0 DRAFT + memory rule `feedback_categorical_triggers_over_hardcoded_refs.md` at v5.15.5.F.4d.1.B.3 doc-layer refresh)
- **Severity:** MEDIUM (always-loaded SKILL.md content drift; categorical-list duplication invisibly accumulated)
- **Surface:** 22 of 30 SKILL.md files at `claude-skills/<skill>/SKILL.md` carry ~50 C-bucket hardcoded refs (canonical-list duplication, line-range refs, sprint version markers in trigger bodies)
- **Sister:** TECH_DEBT-109 (skill SKILL.md drift triage; sprint-phrasing-level closure — addressed worked-example drift). This entry addresses the STRUCTURAL layer below.
- **What's being closed at this entry's ship:** Apply C-bucket conversions per structural skill audit findings — defer-to-registry pattern (`FOREACH_STAMP_BOUND_CFG_DERIVED` / `DOCS/HOT_PATH_CHANGELOG.md` cadence tier / `DOCS/CLAUDE_ML_INVARIANTS.md` / `CoreFrameworks/MetaRegistry.hpp` FOREACH_REGISTRY) replacing inline canonical-list duplication. Inline application during `.B.3` doc-layer refresh ship close.
- **Audit findings reference:** Background-Agent structural audit fired 2026-05-18 against 30 SKILL.md files. Findings: A KEEP ~200+ catalog refs; B KEEP-WITH-FRAMING ~80+ worked examples; C CONVERT ~50 actionable hardcoded refs.
- **Top conversion clusters:**
  1. Stamp-bound cfg field enumeration → defer to `FOREACH_STAMP_BOUND_CFG_DERIVED` (skills: `/parity-check`, `/readiness` Check 16, `/handoff` Stage 1.5)
  2. Hot-path file enumeration → defer to `DOCS/HOT_PATH_CHANGELOG.md` cadence tier (skills: `/ship`, `/latency-track`, `/readiness` Check 23)
  3. Architectural-sprint guards → defer to `DOCS/CLAUDE_ML_INVARIANTS.md` / `INVARIANTS_MAP.md` (skills: `/ml-audit`, `/parity-check` Section L)
  4. Line-range refs → remove parentheticals (skill: `/strategy-template`)
  5. Specific sprint markers in trigger bodies → CLAUDE.md item ref / H invariant ref (skills: `/dod-audit` section headers, `/plan-check` example)
- **Status:** APPLIED at `.B.3` doc-layer refresh ship close (Background-Agent applies conversions; this entry CLOSED at ship-close commit)
- **Follow-up entry:** TECH_DEBT-112-followup-A — periodic skill audit cadence (quarterly + post-codification sweep) per `DESIGN_SPECS/doc-disciplines/categorical-triggers-in-always-loaded-docs.md` § Audit cadence
- **Cross-ref:** `DESIGN_SPECS/doc-disciplines/categorical-triggers-in-always-loaded-docs.md` v1.0 DRAFT (canonical discipline body); `feedback_categorical_triggers_over_hardcoded_refs.md` (going-forward rule); `feedback_claude_md_guidelines_not_stuff_to_do.md` (companion doc-layer separation); TECH_DEBT-109 (predecessor sprint-phrasing-level closure); `feedback_iteration_spiral_signals_audit_meta_gap.md` (Caramel's recognition signal — "instead of generalized stuff we made hardcoded references, which is why we're having so many issues finding stuff").

---

### TECH_DEBT-132 — 2 dead helpers post centralized SHARDED deletion (CLOSED at .B.7)

```yaml
id: TECH_DEBT-132
title: 2 dead helpers EventLoop_UpdateRollingStateAllCores + EventLoop_RebuildAllParameters_PerCore (post centralized SHARDED full surface deletion at .B.4)
severity: low
surface_tags: [dead-code, slow-path, post-deletion-cleanup]
trigger: sub-ship-v5.15.5.F.4d.1.B.7
status: closed
opened: 2026-05-27
closed: 2026-05-27
related_specs: []
```

- **Created:** 2026-05-27 (surfaced at post-`.B.6` codebase-wide `/dust` sweep; opened + closed same ship `.B.7`)
- **Closed:** 2026-05-27 at `v5.15.5.F.4d.1.B.7`
- **Severity:** LOW
- **Surface:** `CoreFrameworks/ControllerEventLoop.hpp:2225` (`EventLoop_UpdateRollingStateAllCores`) + `:2259` (`EventLoop_RebuildAllParameters_PerCore`) — orphaned helpers post centralized SHARDED full surface deletion at `.B.4` WIP-14b 51-site cohort
- **Resolution:** Both helpers DELETED at `.B.7` via clean removal; no remaining callers post centralized deletion cohort. Build clean; tests pass.
- **Status:** **CLOSED 2026-05-27** at `v5.15.5.F.4d.1.B.7`
- **Retroactive ledger write:** This entry was claimed NEW+CLOSED in `.B.7` CHANGELOG + postmortem but missed ledger write at ship close. Retroactively written at 2026-05-27 PM during `/accept-handoff` Stage 4.5 forward-promise verification dogfood (TECH_DEBT-139 mechanical Check 11 will catch this class going forward).
- **Cross-ref:** `plans/v5.15-live-readiness/postmortems/2026-05-27-v5.15.5.F.4d.1.B.7-postmortem.md`; `.B.7` CHANGELOG row in `DOCS/CHANGELOG.md`; `.B.4` WIP-14b 51-site `engine_arch=centralized` SHARDED full surface deletion (parent context); TECH_DEBT-139 (the Check 11 Python impl that would have caught this drift mechanically).

---

### TECH_DEBT-134 — 5 stale "centralized arch" comments cleanup (CLOSED at .B.7)

```yaml
id: TECH_DEBT-134
title: 5 stale "centralized arch" comments post centralized SHARDED deletion (sister to Class 31 stale-comment drift)
severity: low
surface_tags: [stale-comments, post-deletion-cleanup, doc-discipline]
trigger: sub-ship-v5.15.5.F.4d.1.B.7
status: closed
opened: 2026-05-27
closed: 2026-05-27
related_specs: []
```

- **Created:** 2026-05-27 (surfaced at post-`.B.6` codebase-wide `/dust` sweep; opened + closed same ship `.B.7`)
- **Closed:** 2026-05-27 at `v5.15.5.F.4d.1.B.7`
- **Severity:** LOW
- **Surface:** 5 inline-comment sites referencing centralized engine architecture post `.B.4` WIP-14b surface deletion:
  - `CoreFrameworks/EngineCommon.hpp:12` + `:814`
  - `CoreFrameworks/ControllerEventLoop.hpp:88` + `:95` + `:2169`
- **Class:** Sister to Class 31 (hardcoded refs in always-loaded docs); same root cause (stale-comment drift post structural deletion), different surface (inline source comments vs always-loaded doc files)
- **Resolution:** Comments updated/removed at `.B.7` ship per `feedback_archived_changelog_preservation_discipline` + `feedback_operator_facing_doc_cohort_at_cfg_deletion`.
- **Status:** **CLOSED 2026-05-27** at `v5.15.5.F.4d.1.B.7`
- **Retroactive ledger write:** This entry was claimed NEW+CLOSED in `.B.7` CHANGELOG + postmortem but missed ledger write at ship close. Retroactively written at 2026-05-27 PM during `/accept-handoff` Stage 4.5 forward-promise verification dogfood.
- **Cross-ref:** `plans/v5.15-live-readiness/postmortems/2026-05-27-v5.15.5.F.4d.1.B.7-postmortem.md`; `.B.7` CHANGELOG row in `DOCS/CHANGELOG.md`; TECH_DEBT-131 PARTIAL_CLOSURE (sister doc-layer at operator-facing surfaces); TECH_DEBT-139 (Check 11 Python impl that would have caught this drift mechanically); Class 31 catalog (stale-comment drift class).

---

### TECH_DEBT-138 — Vestigial DrainerConstants.fee_rate_taker_d field deletion (CLOSED at .B.8)

```yaml
id: TECH_DEBT-138
title: Vestigial DrainerConstants.fee_rate_taker_d field (Class 27 sub-instance post-.F.4c.3 WIP2d-1.B.1 cache deletion)
severity: low
surface_tags: [dead-state, class-27, post-cache-deletion, accounting, drainer]
trigger: sub-ship-v5.15.5.F.4d.1.B.8
status: closed
opened: 2026-05-27
closed: 2026-05-27
related_specs: [DESIGN_SPECS/refactor-patterns/decision-time-data-binding-pattern.md]
```

- **Created:** 2026-05-27 (surfaced at `.B.8` Phase A comprehensive cohort enumeration — classified LOW-1)
- **Closed:** 2026-05-27 (same-ship deletion at `.B.8` Phase B LOW-1)
- **Severity:** LOW
- **Surface:** `MemHeaders/DrainerConstants.hpp` `fee_rate_taker_d` field — unread post `.F.4c.3` WIP2d-1.B.1 cache deletion (per-core decision-time data binding migrated fee_rate_taker onto Order via `o->pre_resolved.fee_rate`; cache state in DrainerConstants became vestigial)
- **Class:** Class 27 sub-instance — single-value cache flattens per-instance; vestigial cache state post structural fix landed earlier
- **Resolution:** Field DELETED at `.B.8` Phase B LOW-1 via B14 leaves-first ordering swap (deletion at leaf-of-dependency-graph: no remaining consumers post `.F.4c.3` migration). `sizeof(DrainerConstants)` 24→16; `alignof` 8→4; comment block updated at lines 18/67/77 documenting the cleanup. 5 binaries clean; tests pass.
- **Status:** **CLOSED 2026-05-27** at `v5.15.5.F.4d.1.B.8`
- **Retroactive ledger write:** This entry was claimed NEW+CLOSED in `.B.8` handoff + postmortem + CHANGELOG but missed ledger write at ship close. Retroactively written at 2026-05-27 PM during `/accept-handoff` Stage 4.5 forward-promise verification dogfood (sister to `.B.7` -132/-134 retroactive writes same session; same M7 surface).
- **Cross-ref:** `plans/v5.15-live-readiness/postmortems/2026-05-27-v5.15.5.F.4d.1.B.8-postmortem.md` Phase B; `.B.8` CHANGELOG row; `.B.7` Class 26 ×2 closure (parent context — drainer surface accounting cohort); `decision-time-data-binding-pattern.md` (canonical pattern for per-core cfg consumer); TECH_DEBT-139 (Check 11 Python impl that would have caught this drift mechanically); `plans/v5.15-live-readiness/capture-audit-reports/2026-05-27-accept-handoff.md` HIGH-1.

---

### TECH_DEBT-001 — Replace `tools/stamp_model.sh` bash CLI with thin C++ wrapper binary (CLOSED via surface deletion)

```yaml
id: TECH_DEBT-001
title: Replace tools/stamp_model.sh bash CLI with thin C++ wrapper binary (CLOSED via surface deletion at .B.3 Phase L revert)
severity: medium
surface_tags: [cross-tool, wire-format, ml-inference, framework-driven-cli-binary-pattern]
trigger: recurrence-count-2
status: closed
opened: 2026-05-09
closed: 2026-05-24
related_specs: [DESIGN_SPECS/refactor-patterns/framework-driven-cli-binary-pattern.md]
```

- **Created:** 2026-05-09 by v5.14.2.E.3 (initial population; debt accrued since v5.10.0a.G.2)
- **Severity:** MEDIUM
- **Surface:** `tools/stamp_model.sh` (operator-side bash CLI; ~382 LOC of shell) — DELETED at `.B.3` Phase L revert
- **Class:** Same shape as v5.9.5b production-caller class — parallel implementation that drifts. Bash CLI duplicated the LOGIC of `stamp_write_for_model` (canonical body construction + HMAC computation + `.stamp` write) in shell, instead of CALLING the C++ function directly.
- **Closure mechanism:** **Surface deletion (no replacement needed)** at `.B.3` Phase L revert (2026-05-24). Both `tools/stamp_model.sh` AND draft replacement `tools/stamp_model_cli.cpp` were DELETED per YAGNI rationale documented at `DESIGN_SPECS/refactor-patterns/framework-driven-cli-binary-pattern.md` v1.1 § "Pattern status update (2026-05-24)":
  - foxml_suite already stamps models in-process via `Backtest_RunFullValidation → Stamp_AssembleAndEmit` (cfg.auto_stamp_on_held_out_completion)
  - Operator workflow doesn't require CLI binary for common case
  - Bash CLI was edge-case-only infrastructure
  - Per `feedback_overengineering_boundary_when_future_easier` + YAGNI
- **Status:** **CLOSED 2026-05-24** via surface deletion at `.B.3` Phase L revert. Bash CLI no longer exists; parallel implementation eliminated; no drift surface remains. framework-driven-cli-binary-pattern Stage 2 DRAFT retained as pattern body; Stage 3 first canonical deferred to v5.16+ cmdline-invocable training when decoupling endgoal needs a true headless CLI per `plans/_future/2026-05-12-decoupling-endgoal-roadmap.md` "Training entry points" axis.
- **Sister context (added 2026-05-27 PM):** `.C` per-core override emission CLI also SKIPPED at post-`.B.8` pickup re-scope per same YAGNI rationale + operator confirmation; framework-driven-cli-binary-pattern Stage 4 cohort migration deferred to v5.16+ FOREACH_CLI_MODE (TECH_DEBT-034). Pipeline collapsed `.C` slot; `.D` becomes immediate next-up.
- **Retroactive ledger write:** This entry sat OPEN in ledger even though surface was DELETED at `.B.3` (2026-05-24). Retroactively closed at 2026-05-27 PM during `/accept-handoff` Stage 4.5 forward-promise verification dogfood cleanup + `.C` skip decision (sister cohort to TECH_DEBT-132/-133/-134/-135/-136/-138/-139 retroactive ledger writes same session per same M7 surface — ship-close ritual incompletely propagates to all expected destinations).
- **Cross-ref:** `DESIGN_SPECS/refactor-patterns/framework-driven-cli-binary-pattern.md` v1.1 status update (canonical revert rationale); `plans/_future/2026-05-12-decoupling-endgoal-roadmap.md` "Training entry points" axis (v5.16+ FOREACH_CLI_MODE successor surface); TECH_DEBT-034 (FOREACH_CLI_MODE registry; future Stage 3 first canonical surface); CLAUDE.local.md going-forward rule "Framework-driven CLI binary pattern Stage 4 cohort migration deferred to v5.16+ FOREACH_CLI_MODE" (2026-05-27); CLAUDE.md item 19 (structural fix preferred when bug class can recur — applies here: YAGNI deletion eliminates the drift class by removing both implementations).

---

## .D Phase D retroactive ledger writes (cohort: forward-promise drift caught by Check 11 dogfood)

The 8 entries below were retroactively written at v5.15.5.F.4d.1.D ship close after Check 11 Python detection (NEW at this ship) fired against `.B.3` → `.B.8` ship-close artifacts and surfaced accumulated forward-promise drift across 6+ ships. Each entry's closure narrative was already documented in CHANGELOG.md + postmortem narrative + handoff doc at the original ship close, but the `id: TECH_DEBT-NNN` ledger entry was missed at write-time. Check 11 mechanical detection at every subsequent ship close prevents this class going forward.

Sister cohort to the 7 retroactive ledger writes at v5.15.5.F.4d.1.B.8 close-out (commit 237c970 — TECH_DEBT-132/-133/-134/-135/-136/-138 + TECH_DEBT-001 close-out at 858b385). Same M7 surface — ship-close ritual incompletely propagates to ledger.

---

### TECH_DEBT-029 — Source file length reduction (CLOSED at .B.7 C1 via AI-workflow reframe)

```yaml
id: TECH_DEBT-029
title: Source file length reduction (wontfix-per-ai-workflow at .B.7 C1 close-out)
severity: medium
surface_tags: [code-organization, file-size, ai-driven-workflow-scoped]
trigger: n/a (closed; wontfix-per-ai-workflow)
status: wontfix-per-ai-workflow
opened: 2026-05-09
closed_at: v5.15.5.F.4d.1.B.7
closure_rationale: AI-driven solo workflow (per operator C1 directive 2026-05-27); Claude 1M context handles 6K-line files trivially; no human code-review cognitive load concern; compile time unchanged for header-only template code
related_specs: [DESIGN_SPECS/doc-disciplines/file-size-split-discipline.md]
```

- **Created:** 2026-05-09 (initial population at v5.14 cycle; long-standing concern about per-file LOC growth)
- **Severity:** MEDIUM (originally; downgraded to N/A post C1 close-out)
- **Surface:** All source files exceeding typical-human-readable thresholds (multiple .hpp/.cpp files in 5K-10K LOC range)
- **Closure rationale:** Per operator C1 directive 2026-05-27 (AI-driven solo workflow rethink): file-length discipline applies SELECTIVELY in AI-driven workflow. AI 1M context handles 6K-line files trivially; no human code-review cognitive load concern; compile time unchanged for header-only template code. Test 5K rule retained for test-reliability concern but source/header thresholds become guidelines not mandates. See `DESIGN_SPECS/doc-disciplines/file-size-split-discipline.md` v1.4 § "AI-driven workflow scoping" for full rationale.
- **Sister cohort closures at .B.7 C1**: TECH_DEBT-114 (controller_test.cpp split) + TECH_DEBT-116 (TECH_DEBT.md split) + TECH_DEBT-117 (RBP.md split — done-incidentally) + TECH_DEBT-118 (/readiness SKILL.md split) all closed as wontfix-per-ai-workflow same ship.
- **Status:** **CLOSED 2026-05-27** at `v5.15.5.F.4d.1.B.7` via C1 close-out
- **Retroactive ledger write:** This entry was claimed CLOSED in `.B.7` CHANGELOG row + postmortem + handoff doc but missed `id: TECH_DEBT-029` yaml entry write at ship close. Retroactively written at `.D` Phase D after Check 11 dogfood detection.
- **Cross-ref:** `plans/v5.15-live-readiness/postmortems/2026-05-27-v5.15.5.F.4d.1.B.7-postmortem.md` C1 close-out section; `.B.7` CHANGELOG row in `DOCS/CHANGELOG.md`; `feedback_count_code_loc_not_total_lines`; `file-size-split-discipline.md` v1.4 AI-driven workflow scoping; sister TECH_DEBT-133 (EngineSharded_Run mega-fn; DEFERRED-INDEFINITE per same workflow reframe); Check 11 mechanical drift detection at `.D` Phase B is the closure mechanism for THIS class of forward-promise drift.

---

### TECH_DEBT-105 — CI tool tools/check_sister_registry_sig_parity.py (M1 sister-registry parity verification)

```yaml
id: TECH_DEBT-105
title: CI tool tools/check_sister_registry_sig_parity.py (M1 sister-registry parity verification)
severity: low
surface_tags: [ci-tooling, m1-sister-registry-parity]
trigger: n/a (wontfix-per-ai-workflow)
status: wontfix-per-ai-workflow
opened: 2026-05-19 (retroactive write 2026-05-28)
closed_at: v5.15.5.F.4d.1.D
closure_rationale: AI-driven solo workflow (per operator C1 directive 2026-05-27); M1 sister-registry parity verification discipline already codified at DESIGN_SPECS level; manual application via /readiness Check 29 + audit-driven planning sufficient at current cohort scale; CI tool ROI marginal; re-evaluate at v5.16+ if cohort grows OR regression slips through manual application
related_specs: [DESIGN_SPECS/meta-disciplines/sister-cohort-amendment-completeness-discipline.md, DESIGN_SPECS/meta-disciplines/canonical-sister-extension-discipline.md]
```

- **Created:** 2026-05-19 by `.B.3` v1.16 plan body close-out (claimed NEW at ship close but never written to ledger; retroactive open + close at `.D` Phase D.1)
- **Severity:** LOW (defense-in-depth CI; manual discipline application is sufficient at current cohort scale)
- **Surface:** Future Python CI script `tools/check_sister_registry_sig_parity.py` (would verify FOREACH_*_CFG_FIELD sister-registry signature parity)
- **What was deferred (per .B.3 v1.16 original framing):** Build CI tool that enforces M1 sister-registry parity discipline mechanically. Trigger: "warranted when 3+ family members exist with shared consumer pattern".
- **Closure rationale (.D Phase D.1):** Per operator C1 directive 2026-05-27 + AI-driven workflow reframe (sister to TECH_DEBT-029/-114/-116/-117/-118 file-length closures at `.B.7`). M1 discipline codified at `DESIGN_SPECS/meta-disciplines/sister-cohort-amendment-completeness-discipline.md` (Stage 3 first canonical at `.B.8`); manual application via `/readiness` Check 29 ("Plans introducing new registries cite existing sister registry inspection") + audit-driven planning at HIGH-RISK ship tier covers the verification surface. CI tool ROI marginal at current cohort scale (5 FOREACH_*_CFG_FIELD families); re-evaluate at v5.16+ if cohort grows OR regression slips through manual audit.
- **Sister cohort:** TECH_DEBT-106 (M2 cross-tool emit-site enumeration CI; same wontfix rationale); TECH_DEBT-111 (CLI flag drift CI; trigger updated to v5.16+ FOREACH_CLI_MODE alignment); TECH_DEBT-139 (Check 11 forward-promise verification; ACTUALLY IMPLEMENTED at .D because dogfood evidence proved manual discipline insufficient at THIS surface specifically — sister CI tools at -105/-106/-111 surface DON'T have dogfood evidence yet).
- **Status:** **CLOSED 2026-05-28** at `v5.15.5.F.4d.1.D` via AI-workflow reframe (sister to .B.7 C1 close-out pattern)
- **Retroactive ledger write:** Entry was claimed NEW at `.B.3` v1.16 plan body close-out but missed ledger write. Retroactively written at `.D` Phase D.1 after Check 11 dogfood detection.
- **Cross-ref:** `plans/v5.15-live-readiness/subplans/2026-05-17-v5.15.5.F.4d.1.B.3-legacy-empty-out.md` v1.16 close-out section line 418; `.B.3` ship CHANGELOG; sister wontfix entries -106/-111 (this same Phase D cohort); `feedback_framework_layer_payoff_diminishing_returns` (rationale for CI-tool-when-cohort-grows discipline); `DESIGN_SPECS/meta-disciplines/sister-cohort-amendment-completeness-discipline.md` (canonical M1 discipline doc).

---

### TECH_DEBT-106 — CI tool tools/check_cross_tool_emit_parity.py (M2 cross-tool emit-site enumeration)

```yaml
id: TECH_DEBT-106
title: CI tool tools/check_cross_tool_emit_parity.py (M2 cross-tool emit-site enumeration)
severity: low
surface_tags: [ci-tooling, m2-cross-tool-emit, wire-format]
trigger: n/a (wontfix-per-ai-workflow)
status: wontfix-per-ai-workflow
opened: 2026-05-19 (retroactive write 2026-05-28)
closed_at: v5.15.5.F.4d.1.D
closure_rationale: AI-driven solo workflow reframe; M2 cross-tool emit-site enumeration discipline codified at wire-format-byte-preservation-discipline.md Layer 7; cross-tool surfaces limited at v5.15 post .B.3 Phase L revert; manual /merge-scan + Layer 7 application sufficient; re-evaluate at v5.16+ FOREACH_CLI_MODE alignment
related_specs: [DESIGN_SPECS/wire-format-patterns/wire-format-byte-preservation-discipline.md, DESIGN_SPECS/refactor-patterns/framework-driven-cli-binary-pattern.md]
```

- **Created:** 2026-05-19 by `.B.3` v1.16 plan body close-out (claimed NEW at ship close but never written to ledger; retroactive open + close at `.D` Phase D.2)
- **Severity:** LOW (defense-in-depth CI; manual discipline application is sufficient at current cross-tool surface scale)
- **Surface:** Future Python CI script `tools/check_cross_tool_emit_parity.py` (would verify cross-tool wire-emit surfaces don't drift from engine emit)
- **What was deferred (per .B.3 v1.16 original framing):** Build CI tool that enforces M2 cross-tool emit-site enumeration discipline mechanically. Trigger: "warranted when 3+ cross-tool emit sites exist".
- **Closure rationale (.D Phase D.2):** Same as TECH_DEBT-105 (AI-workflow reframe). M2 discipline codified at `wire-format-byte-preservation-discipline.md` Layer 7; manual application via `/merge-scan` audit + audit-driven planning at HIGH-RISK ship tier covers the verification surface. Cross-tool surfaces at v5.15 reduced post `.B.3` Phase L revert (`tools/stamp_model.sh` + `tools/stamp_model_cli.cpp` both DELETED); CI tool ROI marginal at current scale; re-evaluate at v5.16+ FOREACH_CLI_MODE alignment when cross-tool registry-driven approach lands.
- **Status:** **CLOSED 2026-05-28** at `v5.15.5.F.4d.1.D` via AI-workflow reframe
- **Retroactive ledger write:** Entry was claimed NEW at `.B.3` v1.16 plan body close-out but missed ledger write. Retroactively written at `.D` Phase D.2 after Check 11 dogfood detection.
- **Cross-ref:** `plans/v5.15-live-readiness/subplans/2026-05-17-v5.15.5.F.4d.1.B.3-legacy-empty-out.md` v1.16 close-out section line 433; `.B.3` ship CHANGELOG; sister wontfix entries -105/-111 (this same Phase D cohort); `DESIGN_SPECS/wire-format-patterns/wire-format-byte-preservation-discipline.md` Layer 7 (canonical M2 discipline doc).

---

### TECH_DEBT-107 — CLOSURE RETRACTED → `DOCS/tech-debt/open.md`

*(This entry claimed "opened+closed same ship" at `.B.3`. That framing was CORRECTED by the open.md entry's own Status bullet to PARTIAL CLOSED — 12 of 28 audit-targeted rows closed, DIFFER cases pending per-row operator decision — so the closure recorded here was premature and this copy was its superseded original. A full duplicate lived in BOTH sub-files with divergent content (47-globals/LOW here vs 49-globals/MED there), so a bare cite resolved open-or-closed by coin flip. Retracted at `E.1.2.B` `0.2` (f); the live entry is in `open.md`. The generalized anti-pattern is homed at TECH_DEBT-264.)*

---

### TECH_DEBT-114 — controller_test.cpp split (CLOSED at .B.7 C1 via AI-workflow reframe)

```yaml
id: TECH_DEBT-114
title: controller_test.cpp split (wontfix-per-ai-workflow at .B.7 C1 close-out)
severity: medium
surface_tags: [test-organization, file-size, ai-driven-workflow-scoped]
trigger: n/a (closed; wontfix-per-ai-workflow)
status: wontfix-per-ai-workflow
opened: 2026-05-13
closed_at: v5.15.5.F.4d.1.B.7
closure_rationale: AI-driven solo workflow reframe (sister to TECH_DEBT-029); controller_test.cpp at 26K lines navigable via grep + section markers; test-reliability NOT compromised at AI-workflow scale; TECH_DEBT-127 stays open as the actual test-reliability concern
related_specs: [DESIGN_SPECS/doc-disciplines/file-size-split-discipline.md]
```

- **Created:** 2026-05-13 at v5.15.5.F.4d.1.B.5 plan-body file-size umbrella scaffold
- **Severity:** MEDIUM (originally; downgraded to N/A post C1 close-out)
- **Surface:** `tests/controller_test.cpp` (currently ~26K lines; ~3239 test sections)
- **Closure rationale:** Per operator C1 directive 2026-05-27 (AI-driven solo workflow rethink): test-file 5K rule retained as guideline but per-file split deferred indefinitely while AI workflow handles large file navigation reliably. Test reliability concern surface migrated to TECH_DEBT-127 (separate entry) which stays OPEN as the actual test-reliability surface. Sister cohort closures at .B.7 C1: -029/-116/-117/-118 + this entry.
- **Status:** **CLOSED 2026-05-27** at `v5.15.5.F.4d.1.B.7` via C1 close-out
- **Retroactive ledger write:** Entry was claimed CLOSED in `.B.7` CHANGELOG row + postmortem + handoff but missed `id: TECH_DEBT-114` yaml entry write at ship close. Retroactively written at `.D` Phase D.4 after Check 11 dogfood detection.
- **Cross-ref:** `plans/v5.15-live-readiness/postmortems/2026-05-27-v5.15.5.F.4d.1.B.7-postmortem.md` C1 close-out section; `.B.7` CHANGELOG row; TECH_DEBT-127 (sister; test-reliability surface STAYS OPEN); `feedback_file_size_split_discipline` (AI-workflow scoping note).

---

### TECH_DEBT-116 — TECH_DEBT.md split (CLOSED at .B.7 C1 — done-incidentally)

```yaml
id: TECH_DEBT-116
title: TECH_DEBT.md split (file-size discipline application — done-incidentally at .B.7)
severity: medium
surface_tags: [doc-organization, file-size, ai-driven-workflow-scoped]
trigger: n/a (closed; wontfix-per-ai-workflow)
status: wontfix-per-ai-workflow
opened: 2026-05-18
closed_at: v5.15.5.F.4d.1.B.7
closure_rationale: AI-driven solo workflow reframe; TECH_DEBT.md split into open.md / in-flight.md / closed.md already happened at .B.3 prep (see DOCS/TECH_DEBT.md INDEX `splits_into:` frontmatter); intent already realized
related_specs: [DESIGN_SPECS/doc-disciplines/file-size-split-discipline.md]
```

- **Created:** 2026-05-18 at `.B.3` ship close (codified post-`feedback_file_size_split_discipline.md` codification)
- **Severity:** MEDIUM (originally; downgraded — work already done incidentally)
- **Surface:** `DOCS/TECH_DEBT.md` (now INDEX file; sub-files at `DOCS/tech-debt/{open,in-flight,closed}.md`)
- **Closure rationale:** Split work already happened at `.B.3` prep (TECH_DEBT.md became INDEX with `splits_into:` frontmatter; sub-files contain entries by status). Original deferral was about future split work that already landed incidentally. Per .B.7 C1 close-out, formally marked wontfix-per-ai-workflow alongside sister cohort -029/-114/-117/-118.
- **Status:** **CLOSED 2026-05-27** at `v5.15.5.F.4d.1.B.7` via C1 close-out (incidentally completed pre-`.B.7`)
- **Retroactive ledger write:** Entry was claimed CLOSED in `.B.7` CHANGELOG + postmortem but missed `id: TECH_DEBT-116` yaml entry write. Retroactively written at `.D` Phase D.5 after Check 11 dogfood detection.
- **Cross-ref:** `DOCS/TECH_DEBT.md` INDEX file (proof split happened); `.B.7` CHANGELOG row; sister TECH_DEBT-117 (RBP.md split done-incidentally; same shape; moved from open.md to closed.md at this `.D` ship); `feedback_file_size_split_discipline`.

---

### TECH_DEBT-118 — /readiness SKILL.md split (CLOSED at .B.7 C1 via AI-workflow reframe)

```yaml
id: TECH_DEBT-118
title: /readiness SKILL.md split (wontfix-per-ai-workflow at .B.7 C1 close-out)
severity: medium
surface_tags: [skill-organization, file-size, ai-driven-workflow-scoped]
trigger: n/a (closed; wontfix-per-ai-workflow)
status: wontfix-per-ai-workflow
opened: 2026-05-18
closed_at: v5.15.5.F.4d.1.B.7
closure_rationale: AI-driven solo workflow reframe; /readiness SKILL.md at 1674 lines navigable via section markers + skill body is reference doc not heavy compute; AI 1M context handles trivially
related_specs: [DESIGN_SPECS/doc-disciplines/file-size-split-discipline.md]
```

- **Created:** 2026-05-18 at `.B.3` ship close (codified post-`feedback_file_size_split_discipline.md` codification)
- **Severity:** MEDIUM (originally; downgraded to N/A post C1 close-out)
- **Surface:** `claude-skills/readiness/SKILL.md` (currently ~1674 lines; 30+ checks)
- **Closure rationale:** Per operator C1 directive (AI-driven solo workflow rethink): SKILL.md 1500-line threshold reframed as guideline not mandate; AI workflow handles large skill files trivially. Sister cohort closures at .B.7 C1: -029/-114/-116/-117 + this entry.
- **Status:** **CLOSED 2026-05-27** at `v5.15.5.F.4d.1.B.7` via C1 close-out
- **Retroactive ledger write:** Entry was claimed CLOSED in `.B.7` CHANGELOG + postmortem but missed `id: TECH_DEBT-118` yaml entry write. Retroactively written at `.D` Phase D.6 after Check 11 dogfood detection.
- **Cross-ref:** `.B.7` CHANGELOG row; sister entries -029/-114/-116/-117 (same Phase D retroactive cohort); `feedback_file_size_split_discipline` AI-workflow scoping note.

---

### TECH_DEBT-117 — RECURRING_BUG_PATTERNS.md split (CLOSED at .B.7 — done-incidentally; moved from open.md)

```yaml
id: TECH_DEBT-117
title: RECURRING_BUG_PATTERNS.md split (file-size discipline application — done-incidentally at .B.7)
severity: medium
surface_tags: [doc-organization, file-size, ai-driven-workflow-scoped]
trigger: n/a (closed; done-incidentally)
status: done-incidentally
opened: 2026-05-18
closed_at: v5.15.5.F.4d.1.B.7
closure_rationale: Done incidentally — RECURRING_BUG_PATTERNS.md was split into per-class sub-files at 2026-05-18 (see INDEX `splits_into:` frontmatter). Original intent already realized; closure is bookkeeping
related_specs: [DESIGN_SPECS/doc-disciplines/file-size-split-discipline.md, DESIGN_SPECS/ledger-templates/ledger-entry-templates.md]
```

- **Created:** 2026-05-18 (codified at `.B.3` ship close)
- **Severity:** MEDIUM (2198 lines, 32 classes — exceeded 2000-line hard threshold; now done)
- **Surface:** `DOCS/RECURRING_BUG_PATTERNS.md` (now INDEX file)
- **Closure rationale:** Done incidentally — RECURRING_BUG_PATTERNS.md was split into per-class sub-files at 2026-05-18 (see INDEX `splits_into:` frontmatter). Per .B.7 C1 close-out, formally marked done-incidentally (distinct from sister -029/-114/-116/-118 wontfix-per-ai-workflow because the split actually happened, vs the wontfix entries which won't split per workflow reframe).
- **Status:** **CLOSED 2026-05-27** at `v5.15.5.F.4d.1.B.7` (status: done-incidentally; moved from open.md to closed.md at `.D` Phase D.7)
- **Retroactive ledger move:** Entry was in open.md per .B.7 C1 close-out claim but ledger move to closed.md was missed. Moved at `.D` Phase D.7 after Check 11 dogfood detection. Sister to -029/-114/-116/-118 wontfix-per-ai-workflow cohort (this is the 5th of 5 .B.7 C1 closures; -117 had different status — done-incidentally — but still needed ledger move).
- **Cross-ref:** `DESIGN_SPECS/doc-disciplines/file-size-split-discipline.md`; sister cohort entries -029/-114/-116/-118 (this same Phase D retroactive batch); `feedback_file_size_split_discipline`; `DOCS/RECURRING_BUG_PATTERNS.md` INDEX file (proof split happened).

---

### TECH_DEBT-139 — /capture-audit Check 11 Python detection logic implementation (CLOSED at .D — IMPLEMENTED)

```yaml
id: TECH_DEBT-139
title: /capture-audit Check 11 Python detection logic implementation (forward-promise auto-write verification mechanical enforcement) — IMPLEMENTED at .D
severity: medium
surface_tags: [ci-tooling, capture-audit, forward-promise-verification, m7-stage-6, m7-7th-canonical]
trigger: n/a (closed; implemented)
status: closed
opened: 2026-05-27
closed_at: v5.15.5.F.4d.1.D
closure_rationale: Implemented at .D Phase B — NEW tools/check_forward_promise_audit.py (~800 LOC; 24 sentinel patterns; 24 verifier functions; ScanSpec dataclass; section parser; exemption mechanism; --since/--strict/--json/--include-archived modes). M7 7th canonical structural enforcement application. Dogfood at Phase G ship close verified Check 11 catches mechanical drift.
related_specs: [DESIGN_SPECS/meta-disciplines/structural-enforcement-when-memory-insufficient.md, DESIGN_SPECS/meta-disciplines/canonical-sister-extension-discipline.md]
```

- **Created:** 2026-05-27 (surfaced at `/accept-handoff` Stage 5 dogfood verification post-`.B.8` ship pickup; SKILL.md amendment landed at `.B.8` Phase H.2.c; mechanical Python impl deferred per token-budget pragmatism)
- **Severity:** MED (load-bearing: without Python impl, Check 11 must be run manually via Bash greps; mechanical at-commit-time enforcement requires the impl)
- **Surface:** NEW `tools/check_forward_promise_audit.py` (the `.D` primary deliverable)
- **Closure rationale:** Implemented at `.D` Phase B (~800 LOC tool with comprehensive sentinel + verifier coverage). M7 7th canonical structural enforcement application (sister to Check 9 + Check 10 in `check_per_core_registry_integrity.py` + B-Plus pre-commit hook + 3 other canonicals). Dogfood at Phase G ship close verified Check 11 catches mechanical drift across `.B.3` → `.B.8` ship-close artifacts (surfaced 8+ retroactive ledger writes in THIS same `.D` ship close — proving the discipline works as designed).
- **Implementation details:** `tools/check_forward_promise_audit.py` lands at `.D` ship commit. Sister tools verified at HEAD: `check_per_core_registry_integrity.py` (Check 9 + Check 10), `check_plan_body_symbol_existence.py` (B-Plus). Sister discipline at `claude-skills/capture-audit/SKILL.md` Check 11 section (amended at `.B.8` Phase H.2.c; Python tool finally lands at `.D`).
- **Dogfood result:** First Check 11 run at `.D` Phase B.5 smoke test surfaced 19 HIGH findings + 12 distinct claim+id forward-promise drift instances across 6+ prior ships. All 8 substantive retroactive writes landed at `.D` Phase D cohort closure. Sister to .B.8 commit 237c970 (7 retroactive ledger writes detected manually via /accept-handoff Stage 4.5 Bash-grep methodology — Check 11 Python now mechanizes that detection).
- **Status:** **CLOSED 2026-05-28** at `v5.15.5.F.4d.1.D` via IMPLEMENTED (not deferred; structural enforcement landed)
- **Cross-ref:** `plans/v5.15-live-readiness/postmortems/2026-05-27-v5.15.5.F.4d.1.B.8-postmortem.md` § What went poorly #2 (deferral rationale at .B.8); `plans/v5.15-live-readiness/subplans/2026-05-27-v5.15.5.F.4d.1.D-forward-promise-verification-ci.md` v1.1 (the .D plan body); `feedback_forward_promise_auto_write_verification` (Stage 3 first canonical at this ship); `feedback_structural_enforcement_when_memory_insufficient` (M7 parent; worked_examples extended); `claude-skills/capture-audit/SKILL.md` Check 11 spec; `tools/check_forward_promise_audit.py` (the deliverable); sister M7 7th canonical applications at Stage 6 escalation surface.

### TECH_DEBT-150 — [FALSE POSITIVE] `check_meta_registry.py` Check-2 missed `(BASE_X)`-param meta-walkers (CLOSED at `.E` Session-4 — checker regex fix; relocated from open.md)

```yaml
id: TECH_DEBT-150
title: check_meta_registry.py regex matched only (X)-param macros -> false orphan for FOREACH_STAMP_BOUND_DERIVED_COHORT
severity: low
surface_tags: [registry, meta-registry, ci-check, h15]
status: closed
opened: 2026-05-30
closed: 2026-05-30
resolution: checker regex broadened; NOT real debt
related_specs: [framework-patterns/meta-registry-pattern-for-codebase-registry-discipline.md]
```

- **Created + CLOSED:** 2026-05-30 (`.E` Session-4). **NOT real tech debt — a checker false-positive I mis-filed, then corrected (verify-don't-assume; `feedback_run_doc_ci_tools_first_never_hand_verify`).** Relocated open.md → closed.md same session (no maintenance-pass deferral).
- **What actually happened:** `check_meta_registry.py` Check 2 reported `FOREACH_STAMP_BOUND_DERIVED_COHORT` as "in FOREACH_REGISTRY but no #define." Investigation: the macro IS defined (`MemHeaders/CfgGateRegistry.hpp:227`) + used at 8 sites — but with param `(BASE_X)`, while the macro-finder regex (`tools/check_meta_registry.py:70`) matched only literal `(X)`. So a real, registered, used macro was a phantom orphan.
- **Fix (landed this session):** broadened the regex `\(\s*X\s*\)` → `\(\s*\w+\s*\)` (any single-identifier param) so action-parameterized meta-walkers (`FOREACH_<COHORT>_COHORT(BASE_X)`) are seen. `check_meta_registry.py` now **EXIT 0** (Check 2 PASS: all 64 rows match a real #define; found 66 macros). Kept as a CLOSED record (not deleted) so the false-positive class is on file.
- **Residual (genuinely pre-existing, NON-FATAL):** 2 Check-1 WARNs (`FOREACH_LEGACY_PREFIXED_KEY`, `FOREACH_STAMP_RESULT_FIELD_EXCLUSION` unregistered) — explicitly "NON-FATAL during transition" per the tool; not debt, transition state.
- **Cross-ref:** `tools/check_meta_registry.py:70` (the fixed regex); `MemHeaders/CfgGateRegistry.hpp:227`; CLAUDE.md H15; decision-log D-114.

---

## v5.15.5.F.4d.1.E.0.7 closures (Ship A — the 16B storage flip; 2026-06-08)

### TECH_DEBT-157 — struct-alignment guard tool (alloc-site + alignof CI check) — CLOSED

- **id:** TECH_DEBT-157 · **severity:** medium · **opened:** 2026-06-08 · **closed:** 2026-06-08 (v5.15.5.F.4d.1.E.0.7) · **surface_tags:** [ci-tooling, capital-safety, data-oriented-design, alignment, structural-enforcement]
- **Resolution:** BUILT this session — `tools/check_struct_alignment.py` collects every `alignas(>16)` struct (struct- + member-level via a state machine; strips `//` comments) and flags any over-aligned type allocated via bare `malloc`/`calloc`/`realloc` (exit 1 = the Knight/H21 over-aligned-bare-malloc class). Wired pre-commit **Check K** (blocking) + teeth-proofed by `test_check_struct_alignment.py` (VIOLATION → RED+named; CLEAN → GREEN). Enrolled in `DOCS/TOOLS.md`. The (a) malloc-honors-alignment guard IS the structural close; an optional (b) advisory lists 12 over-aligned types that could add a locked `static_assert(alignof==N)` — surfaced on every relevant commit (tracked-by-tooling), NOT pursued per D-84 (close-the-class-via-the-guard ≠ lock-every-site; the per-type namespace/template-arg friction was disproportionate + a `using namespace tt` wrap leaked globally).
- **Cross-ref:** pre-commit Check K; M7 (`structural-enforcement-when-memory-insufficient.md`); `feedback_guards_compound_enforcement_is_leverage`; postmortem `2026-06-08-v5.15.5.F.4d.1.E.0.7-postmortem.md`.

### TECH_DEBT-158 — pre-existing sanitizer findings (asan AVX-512 SEGV + ubsan timing-test) — CLOSED

- **id:** TECH_DEBT-158 · **severity:** low · **opened:** 2026-06-08 · **closed:** 2026-06-08 (v5.15.5.F.4d.1.E.0.7) · **surface_tags:** [ci-tooling, sanitizers, avx512, ml-bandit, testing]
- **Resolution:** FIXED this session (not deferred — operator close-out-now steer, D-159). (1) asan AVX-512 SEGV → `__attribute__((no_sanitize("address")))` on the 3 verified-correct AVX-512 masked kernels (`Bandit_GetProbabilities` + `RidgeBlender_BuildCorr`/`_UpdateOnline`; asan can't model `_mm512_mask_*`; buffers correctly 8-wide; scalar-reference byte-determinism tests prove correctness) → asan 3246/0. (2) ubsan timing-test flakiness → NEW `FOXML_SANITIZER_BUILD` flag (build.sh tsan/asan/ubsan lanes) lets the seqlock timing test relax its snapshot-count floor under instrumentation → ubsan UB-clean. The flip itself is value-correct (3246/0) + own-UB-clean.
- **Cross-ref:** TECH_DEBT-157; `avx512-byte-determinism-pattern.md`; postmortem `2026-06-08-v5.15.5.F.4d.1.E.0.7-postmortem.md`.

### TECH_DEBT-161 — pin the sanitizer-suite run conditions + audit harness exit-leaks — CLOSED

- **id:** TECH_DEBT-161 · **severity:** medium · **opened:** 2026-06-09 (A.5 acceptance) · **closed:** 2026-06-09 (post-v5.15.5.F.4d.1.E.0.8 close-out, same day) · **surface_tags:** [ci-tooling, sanitizers, testing, structural-enforcement]
- **(a) Runner:** NEW `tools/run_sanitizer_suite.sh` (TOOLS.md-enrolled STANDING-CI) pins `ulimit -s unlimited` + `ASAN_OPTIONS=detect_leaks=0` with the WHY documented inline; v2 preserves `[FAIL]` lines to a kept log (a bare `tail` ate the failing test's name on first dogfood — evidence-destroying-instrumentation lesson). Dogfooded: asan **3246/0** via the runner; ubsan **3246/0** on rerun (the single chain-run failure reproduced the KNOWN D-155(c) load-sensitive timing-floor flake shape and vanished on a quiet rerun — runner logs now capture the name if it recurs).
- **(b) Leak audit:** `detect_leaks=1` run captured + classified — ALL 765 reported allocations (~115MB) are INIT-TIME fixtures (`PortfolioController_Init:475-506` rolling allocs ×~180, `EventLoopState_Init`/`_alloc_and_init_slow_state` ×~70, test-local fixtures); **zero runtime/tick/trade-path leaks in the observed window**. Caveat recorded: leak-mode aborts between the suite's two RESULTS blocks (~test 900), consistent with memory pressure from accumulated no-teardown fixtures under ASan overhead — the harness exits without teardown BY DESIGN (process exit reclaims), so the gate stays `detect_leaks=0`, documented in the runner.
- **Cross-ref:** A.5 postmortem; D-155; `feedback_guards_compound_enforcement_is_leverage`; TECH_DEBT-160 (sister, same acceptance batch).

### TECH_DEBT-160 — gui-lane `-Wstringop-overflow` audit (3 sites: 2 FIXED provable, 1 verified-FP documented) — CLOSED

- **id:** TECH_DEBT-160 · **severity:** low · **opened:** 2026-06-09 (A.5 gui build) · **closed:** 2026-06-09 (post-v5.15.5.F.4d.1.E.0.8 close-out, same day) · **surface_tags:** [build-warnings, slow-path, oms-drainer, testing]
- The original 2-site scoping was a TRUNCATED-CAPTURE artifact (a 30-line tail); proper tee-capture enumerated 3 sites:
  1. **FIXED** `CoreFrameworks/ControllerEventLoop.hpp` `EventLoopState_SetCoreStrategy` — added the compile-provable `slot >= MAX_EXECUTION_CORES` clause (zero behavior change: `registered_count <= MAX_EXECUTION_CORES` invariant means it never fires alone; boot/setup cadence). Warning verified GONE.
  2. **FIXED** `DataStream/DepthRecorder.hpp` + **`TickRecorder.hpp` (sister-cohort, same emit shape)** — `to_chars(o, rend-1, ...)` reserves the separator byte so `*o++` is PROVABLY in-bounds even on the value-too-large path (`ptr==last`); the unchecked-ptr shape was a latent 1-byte overflow under the type contract, only arithmetically unreachable (142/160B, ~73/96B worst cases). Warnings verified GONE; suite 3246/0; replay emit byte-identical for all real values.
  3. **VERIFIED-FP, documented** `CoreFrameworks/SPSCRing.hpp` `SPSCRing_TryPush` masked write — 8 instances via IPA/.isra clones of the submit chain (`BinanceAdapter_Submit*` -> `OrderManager_Submit` -> `OMS_DrainSubmit`). In-bounds BY CONSTRUCTION (`MASK = N-1`, power-of-2 static_assert). "Region of size 0" = degenerate clone-side base-pointer PROVENANCE — index-side facts can't fix it; BOTH remedies tried + verified ineffective (GCC pragma ignored by late IPA passes; `__builtin_unreachable()` range hint no effect). Disposition comment AT the write site; the 8 lines are known-classified — **any stringop warning at any OTHER site is real signal**.
- **Cross-ref:** A.5 postmortem addendum; TECH_DEBT-161 (same acceptance batch); D-155 (don't-conflate discipline that opened these as rows instead of folding into the zero-semantic ship).

### TECH_DEBT-146 — Symbol `lot_step_size`/`qty_decimals` stored as `double`

```yaml
id: TECH_DEBT-146
severity: LOW
status: OPEN
trigger: .E.0.3 review OR PRE-PAPER-TEST
surface_tags: [accounting, symbol-precision, fpn, order-validation]
```

- **Created:** 2026-05-29 by v5.15.5.F.4d.1.E.0.1 hardened-gate audit (symbol-precision question).
- **What's deferred:** `BinanceOrderAPI.hpp:76/80` stores `lot_step_size` as `double` + derives `qty_decimals`. For order-validation precision + consistency with the `.E.0.3` `string→FPN` direction, review whether it should be FPN/decimal-exact. Low-stakes (order validation, not core accounting).
- **Cross-ref:** decision-log D-85.

> **CLOSED 2026-06-10 (SUBSUMED by Ship B v5.15.5.F.4d.1.E.0.9):** `SymbolFilters` fields retyped to decimal `Money` (D-106 source-exact mirrors) + `Money_QuantizeToStep` (#6) is the exact LOT_SIZE quantizer; `qty_decimals` derives from the Money step. The double SHELL on the REST plumbing rides .E.3.

---

### TECH_DEBT-164 — D-190 process-codification residue (AP4 extension + characterization-test DESIGN_SPEC + adversarial-default into skills)

- **id:** TECH_DEBT-164 · **severity:** low · **opened:** 2026-06-10 · **status:** CLOSED 2026-06-12 (all 3 parts done) · **surface_tags:** [audit-methodology, anti-pattern-catalog, design-spec, skill-default, M7, doc-system]
- **What it was:** the `.E.0.10` D-190 saga codified the immediate lessons (3 memories + D-190 + PARITY-038 + Landmine 8 + the structural guard) but left 3 DEEPER process codifications: (1) the "AP4 extension" (single-source the COMPUTATION, not just the mode, for any money value derived ≥2 ways); (2) a NEW `characterization-test-discipline` DESIGN_SPEC (the complete / non-vacuous / not-frozen-bug 3-lens pass); (3) M7 — wire the adversarial-default + 3-lens pass INTO the audit/review skills so they fire by default, not from memory.
- **CLOSED across 3 passes:**
  - **Part 3 (2026-06-11):** adversarial-default made BINDING DEFAULT — shared consult discipline Stage-0 + `tools/check_capital_adversarial_audit.py` failsafe (+ D-137 self-test) + AR-8/AR-9 catalogued + `feedback_adversarial_framing_default_for_checks` BINDING.
  - **Part 2 (2026-06-12):** authored `DESIGN_SPECS/audit-methodologies/characterization-test-discipline.md` (first-canonical = `oms-ts-1`/`oms-ts-1b`; README audit-methodology 5→6; sister-symmetric with adversarial-multi-agent + audit-driven-pre-coding-gate; `applies_at_skills` = /readiness /test-strength-audit /blindspot-scan /precoding-audit-gate /plan-dive /accounting-audit).
  - **Part 1 (2026-06-12):** the "AP4 extension" — a grep PROVED **AP4 was never authored as a catalog class** (D-121 left AP1–AP4 Stage-2 DRAFT; only memory + ledger refs ever existed — a cited-but-nonexistent / WH-5 catch surfaced by grounding-in-real-code at write time) → authored fresh as **Class 43** (money value derived ≥2 ways without single-sourcing the computation — Sub-shape A divergent/implicit rounding-mode [D-105] + Sub-shape B open-coded formula duplication [D-190]; recurrence_count 2), added to the RBP index table (the 41/42 rows that were numbering-note-only were backfilled in the same edit), cross-reffed from `feedback_single_source_the_computation_not_just_the_mode`.
- **Cross-ref:** D-190; D-198 (the codification-pass decision); Class 43; `DESIGN_SPECS/audit-methodologies/characterization-test-discipline.md`; `feedback_single_source_the_computation_not_just_the_mode`; `feedback_adversarial_framing_default_for_checks`. Index consistency gated by `tools/check_session_docs.sh`.

### TECH_DEBT-178 — Combined investigate→adversarially-refute DECISION-check skill (`/decision-check`)

- **id:** TECH_DEBT-178 · **severity:** medium · **opened:** 2026-06-12 · **status:** CLOSED 2026-06-12 (built same session — operator "knock 178 out, i dont wanna keep this list growing") · **surface_tags:** [skill, audit-methodology, adversarial-default, decision-gate, m7]
- **What it was:** the gap that `/precoding-audit-gate` (heavyweight plan-gate) + `/second-opinion` (adversarial-only, no investigative-first) + `/finding-analyzer` (investigative-only, no refute) each leave — NONE fuses investigate→adversarially-refute for a single DECISION. A25 (D-204) proved both the value and the cost of not having it: the proposer recommended a `DESIGN_PHILOSOPHY:726`-forbidden 24-TU wide cascade, an investigative agent independently endorsed it, and ONLY the adversarial pass caught it — momentum-SKIPPED until operator pushback.
- **CLOSED (2026-06-12):** built `.claude/skills/decision-check/SKILL.md` — Layer-1 orchestrator: Stage 1 investigative agent (surface/options/blast-radius, AR-3 re-ground) → Stage 2 independent adversarial refute (FIND/REFUTE; mandatory per the binding adversarial-default) → Stage 3 cross-check (flag DISAGREEMENT for operator code-read, never rubber-stamp) → Stage 4 synthesize (GREEN/YELLOW/RED, consult-before-coding, never auto-proceeds). COMPOSES `/finding-analyzer` + `/second-opinion` (canonical-sister; not reimplemented). Wired into the CLAUDE.md skill suite ("Pre-coding plan verification"); registered + invokable. The M7 structural close for the DECISION surface (sister to TECH_DEBT-164's audit-skill adversarial wiring).
- **Cross-ref:** `/second-opinion` + `/finding-analyzer` (the halves it fuses); `/precoding-audit-gate` (heavyweight plan-gate sibling); `feedback_adversarial_framing_default_for_checks` (the policy + the A25 sharpening it enforces); TECH_DEBT-164 (sister M7 audit-skill wiring); D-204 (A25, the motivating + first-dogfood instance).

### TECH_DEBT-182 — `Portfolio_Init`/`ClearPositions`/`AddPositionWithExits` zero a SUBSET of Position fields (A19 bug class)

- **id:** TECH_DEBT-182 · **severity:** medium · **opened:** 2026-06-12 · **status:** CLOSED-by-`.E.0.10`-A28 (engine `0e1f6d2`, 2026-06-12) · **surface_tags:** [portfolio, position-reset, stale-state, class-44, a19-sister, capital]
- **What it was (register A28):** `Portfolio_Init`/`ClearPositions`/`AddPositionWithExits` zeroed only a 5-field subset → `original_tp`/`original_sl`/`pair_index`/`entry_timestamp_us` survived a slot reuse (stale trail anchor + mis-paired legs; the A19 class one field over).
- **CLOSED (A28):** `Position_Reset(Position<F>*)` SSoT — full-struct reset, called by `Portfolio_Init` + `ClearPositions`; `Portfolio_AddPositionWithExits` now sets `original_*` (mirror `Portfolio_OpenSlot`). Closes the subset-zeroing class structurally (one site to maintain; `pair_index` defaults -1). Suite 3378/0; the A25-bundle char-test exercises the path.
- **Cross-ref:** register A28 + A19 (sister `ratchet_tp` clear); D-205/A25 (the co-fix touch); `Portfolio.hpp` `Position_Reset`.

### TECH_DEBT-186 — NEW anti-pattern Class + DESIGN_SPEC: "reconstruct-path-reads-a-DIFFERENT-source-field"

- **id:** TECH_DEBT-186 · **severity:** medium · **opened:** 2026-06-12 · **status:** CLOSED-by-`.E.0.10` (2026-06-12; A25-close harvest) · **surface_tags:** [anti-pattern-codification, single-source, restore-replay, class-candidate, design-spec, harvest-obligation]
- **What it was:** a restore/reconstruct/replay path re-derives a value the FORWARD path computes but reads a DIFFERENT source field → silent divergence. A1 + A25 canonical. Promised in register meta-lesson #1 but authored nowhere (prose-only).
- **CLOSED (harvest):** per D-208 (canonical-sister discipline — EXTEND, don't author parallel infra): (1) `decision-time-data-binding-pattern.md` **v1.3 amendment** (the reconstruct-path corollary, A1+A25 worked); (2) **RECURRING_BUG_PATTERNS Class 45** (index row + numbering note + per-class file `class-45-reconstruct-path-reads-different-source-field.md` with a detection signature → auto-picked by `/bug-check`). The originally-proposed standalone `forward-vs-reconstruct-single-source.md` was SUPERSEDED by extending the active sister (the adversarial-verify recommendation).
- **Cross-ref:** D-208 (the extend-vs-new-spec call); `decision-time-data-binding-pattern.md` v1.3; Class 45; A1 (closed) + A25; Class 43 / Class 18 (distinct); AR-7 (sibling).

### TECH_DEBT-168 — A1: warm-restart recomputed live_tp/live_sl from GLOBAL take_profit_pct, ignoring the per-strategy override (restore ≠ live exit price)

- **id:** TECH_DEBT-168 · **severity:** high · **opened:** 2026-06-11 · **status:** CLOSED 2026-06-11 in `.E.0.10` (single-source `ResolvePerFillTpPct/SlPct` for BOTH entry + restore; SimpleDip+MR char-tests GREEN, suite 3368/0; 3-agent independent refute SOUND) · **moved:** open→closed.md 2026-07-01 · **surface_tags:** [accounting, snapshot-restore, tp-sl, parity, reconstruct-vs-forward, .E.0.10]
- **What it was:** `ShardedSnapshotPersist.hpp:653` recomputed restored `live_tp/live_sl` from GLOBAL `resolved.take_profit_pct` while the live entry path used the per-strategy override (`simpledip_tp_pct ?: take_profit_pct`) → a warm-restarted SimpleDip/MR/EmaCross position exited at a DIFFERENT TP/SL than while live. Fixed by single-sourcing the resolver for BOTH paths (the reconstruct=forward close, RBP Class 45).
- **Sibling (distinct root, NOT this — do not conflate):** **Fight #4 / D-288** (2026-07-01) — the FRESH-ENTRY hot `live_tp`/`live_sl` anchor to the DECISION tick vs the FILL (no post-fill re-sync); *same fields*, different bug, homed to **E.1.3** (mirror↔book coherence).
- **Cross-ref:** register bug-hunt § A1; PARITY-039; RBP Class 45 + `decision-time-data-binding-pattern.md` v1.3 (the reconstruct-path corollary this closed).


### TECH_DEBT-226 — `Order<F>`/`OrderPreResolved<F>` stale size/layout comments (comment-drift; the live static_asserts are correct)

- **id:** TECH_DEBT-226 · **severity:** LOW-MED · **opened:** 2026-06-30 · **status:** CLOSED 2026-07-16 by E.1.2.A-P6.20/P6.20b (the [SCHEMA]_[v1.0] conversion — exactly the entry's "any next Order.hpp-touching ship" trigger) · **moved:** open→closed.md 2026-07-16 · **surface_tags:** [oms, comment-drift, layout, order, subagent-arming-2.5]
- **What it was:** descriptive size/layout comments in `CoreFrameworks/Order.hpp` drifted from the code: `:137` "Sized at 32 B" (real: 48B per assert, A25 tp_pct growth); `:193` "32 B @ 160 (Ship-A 16B: 48→32)"; "HOT subtotal: 192 B / exactly 3 cache lines" + "exchange_id @ 192" (invalidated by the 48B pre_resolved; sizeof(Order<64>)==272). The static_asserts were all CORRECT; only the human comments drifted.
- **CLOSED (subsumed by the conversion, per the entry's own §2.5 prescription — reference the assert, don't restate the digit):** the stale "Sized at 32 B" sentence DROPPED (Refinement A); the F.4c.3 "320 B / 4-cache-line" lead story re-scoped historical; the in-struct digits de-digited to assert-references ("size = the OrderPreResolved assert above" / "sizeof assert-locked below" / "offset moved with pre_resolved growth"); both size asserts gained [ASSERT]_[LAYOUT_LOCK] annotations; the tool-owned [DERIVED] now carries the live 272B. Verified: lossless code diff = 0; validator + cache gate green; suite 3697/0 (engine a2534d3 + the P6.20b follow-up).
- **Cross-ref:** SUBAGENT_ARMING §2.5 · `mechanical-verification-of-derived-code-facts.md` · the E.1.2.A in-code tag system (whose DERIVED/assert discipline is the structural close of this whole comment-drift class).

### TECH_DEBT-237 — pre-epoch stamp FLOOR never implemented (comment claims "unconditional floor below"; parser actually accepts [0,3]) — Class-38 phantom-invariant on the stamp ingest path [pre-live must-close]
- **id:** TECH_DEBT-237 · **severity:** HIGH · **opened:** 2026-07-16 · **status:** closed · **surface_tags:** [ml-inference, wire-format, capital-safety, live-readiness, stamp, class-38]
- **What:** the Ship-B P2b flip (`838bf09`) bumped `STAMP_FORMAT_VERSION_CURRENT`/`MAX_SUPPORTED` to 3 and wrote the constant comment "Ship-B: pre-epoch stamps [1,2] are HARD-INVALID (unconditional floor below — bypasses the strict fork)" (`ML_Headers/ModelInference.hpp` MAX_SUPPORTED line) — but the FLOOR WAS NEVER CODED. The only `stamp_format_version` check in `verify_model_stamp` is the too-NEW rejection (`> MAX`); that check's own comment ("RELAXED accept [1, MAX]") + the code are the actual behavior. No caller (NodeModelZoo/StrategyParameters/HotSwap/BacktestPanels) checks it either (rg-verified at the P6.96 conversion, engine `43d3bd4`; flip-diff-verified: `838bf09` changed only constants + comments). Consequence: a pre-epoch v1/v2 stamp (model_format_version=6, hashes matching, sig valid) LOADS; its ~30 money wire fields (fee_rate_*, ml_tp_pct/ml_sl_pct, …) were emitted under the binary-FPN encoding and parse into the DECIMAL engine — the exact S-4/D-174 scenario the epoch tripwire `static_assert` demanded be closed "in THIS commit". The assert was satisfied by the version bump alone; the refusal half slipped.
- **Why not a live bug today:** no live models exist (all artifacts are dev/test fixtures — `project_no_live_models_dev_test_only`; epoch breaks are free) + the Phase-D blanket live-gate refuses live until `.E` lands. Blast radius today = a dev-fixture mis-parse.
- **Fix (small + mechanical):** in `verify_model_stamp`, an UNCONDITIONAL pre-epoch floor: `stamp_format_version < 3` (including ABSENT = 0, also pre-epoch) → `r.valid = 0` (NOT −1 — so `held_out_gate_strict=0` cannot admit it) with a "pre-epoch stamp carries binary-encoded money fields; decimal engine refuses — retrain" reason; keyed on `MONEY_ENCODING_EPOCH == 1` (trait-matched to the tripwire). Plus a NEGATIVE test (a v2 fixture stamp MUST refuse) + flip the two constant comments to match reality.
- **Disposition / trigger:** DEFER-homed — a capital-path code change is out of scope for the E.1.2.A docs pass that found it (comments-only, lossless-gated). Trigger: the next stamp/ML-surface code ship, or the pre-live hardening pass AT LATEST (live-enable precondition class). The P6.96 conversion annotates the constant comment with the truth + this id (phantom claim killed in prose; design intent preserved).
- **Cross-ref:** S-4/D-174 (the decided design) · `838bf09` (the flip that half-landed it) · Class 38 (phantom invariant) · Class 42 (semantic re-encode at identical layout — the underlying hazard) · H9/H21 · `wire-format-byte-preservation-discipline.md` · TECH_DEBT-238 (the back-compat layer this floor deadens) · `feedback_no_unhomed_debt_code_smell`.
- **CLOSED 2026-07-17** (same-day fix ship, engine commit follows): the 0c floor landed in verify_model_stamp (STAMP_FORMAT_VERSION_EPOCH_FLOOR=3 pinned by a second EPOCH_TRIPWIRE assert; valid=0 hard-invalid incl. absent=0; dev-mode bypass-proof) + 5 negative tests (v2 / absent / v1-legacy-key shapes; suite 3702/0). The FOREACH_LEGACY_PREFIXED_KEY layer was deleted per H21 (macro + parser dispatch + MetaRegistry row + the 5 comment sites; tombstone at ML_Headers/ModelInference.hpp). BONUS FIND fixed in the same ship: MetaRegistry.hpp:60 was missing its line-continuation backslash — the entire 43-row bulk block sat OUTSIDE the FOREACH_REGISTRY macro (latent: the header is included by NOBODY; the H15 guard is text-level, so it never saw it; standalone compile-probe now clean).

### TECH_DEBT-238 — FOREACH_LEGACY_PREFIXED_KEY deletion target lost its ledger home (cited "TECH_DEBT-101" exists in NO ledger file) — re-homed here
- **id:** TECH_DEBT-238 · **severity:** LOW · **opened:** 2026-07-16 · **status:** closed · **surface_tags:** [ml-inference, wire-format, ledger-hygiene, H21]
- **What:** `ML_Headers/ModelInference.hpp`'s `FOREACH_LEGACY_PREFIXED_KEY` (16 v1→v2 wire-key back-compat rows) cites "Deletion target tracked at TECH_DEBT-101" — and `CoreFrameworks/MetaRegistry.hpp` row 65's doc string cites the same id — but TECH_DEBT-101 exists in NO ledger file (open/in-flight/closed/umbrella; rg-verified 2026-07-16). The entry was lost somewhere in the ledger split/renumber history. The DEBT ITSELF (delete the back-compat layer when production v1 stamps are extinct) is real and re-homed HERE.
- **The re-homed debt:** delete the `FOREACH_LEGACY_PREFIXED_KEY` macro body + the parser dispatch walk in `verify_model_stamp` + the v1 LOAD test fixture in controller_test.cpp + un-enroll the MetaRegistry row (H15) — once TECH_DEBT-237's floor lands, this layer is DEAD CODE by construction (a [1,2] stamp can never reach the dispatch; H21: remove, don't leave compiled-in). Fold this deletion INTO the TD-237 fix ship.
- **Site cleanup:** the ModelInference banner cite updated to TECH_DEBT-238 at P6.96 (comment). The MetaRegistry.hpp row-doc cite is a STRING LITERAL (code bytes — untouchable in a docs pass) → update in the fix ship.
- **Disposition / trigger:** fold into the TECH_DEBT-237 fix ship (same surface; 237 deadens this layer).
- **Cross-ref:** TECH_DEBT-237 · H21 (dead-code removal) · `CoreFrameworks/MetaRegistry.hpp:65` · Layer 6b SOFT-bump procedure (`wire-format-byte-preservation-discipline.md`) · `feedback_no_unhomed_debt_code_smell`.
- **CLOSED 2026-07-17** — folded into the TECH_DEBT-237 fix ship as planned: layer deleted (H21), MetaRegistry row retired with tombstone comment, the dangling TD-101 cites replaced at all editable sites (ModelInference banner/tombstone + MetaRegistry row-doc + CfgFieldRegistry + StampBoundModelConstRegistry + the controller_test citing comment). The once-cited 'v1 LOAD fixture test' was rg-proven to have never existed; the TD-237 floor tests are the standing re-introduction guard.



### TECH_DEBT-245 — Conversion/validation gates are BLIND to gitignored engine source (rg's default `.gitignore` filtering) — a latent false-green class

- **id:** TECH_DEBT-245 · **severity:** med · **opened:** 2026-07-19 · **status:** closed · **surface_tags:** [toolchain, doc-tag-system, ci-gate, false-green, privacy-boundary]
- **What:** `check_conversion_completeness.py:158` (`converted_files()`) enumerates source via `subprocess.run(["rg","-l",…,str(ENGINE)])` **without `-u`/`--no-ignore`**, so it inherits ripgrep's default `.gitignore` filtering → **gitignored-but-real engine source is invisible to the gate.** Proven 2026-07-19 (operator-flagged: *"there are still files that dont match the comment schema 1:1 or the templates, so maybe the tools dont work perfectly for detecting things that break that"*): `Strategies/private/EmaCross.hpp` (294 lines, gitignored per the privacy boundary) is skipped — a `Strategies/` scan sees **10** files by rg-default vs **11** with `-u`; corpus-wide `find`=162 vs rg=161. **Current impact NIL** — that file is *correctly* converted (conformant `// [SCHEMA]_[v1.0]` ×5, 9 orient blocks) — so "163 converted · 0 gaps" is not WRONG today, it is simply **unverified** across the gitignored surface. **The latent hole:** any private/gitignored source added later is silently never validated while the gate still reports 0 gaps — a **Class-51-adjacent false-green** (a guard cannot RED on input it never reads). **Adjacent (verify):** other rg-based enumerators in the tool family may share the blind spot (`check_code_tag_blocks.engine_source_files` — the shared collector — `rebuild_doc_indexes`, the code-tag inventory), so the fix belongs at the SHARED enumerator, not per-tool. **Not a gap (checked, for the record):** `EngineSharded/Run.hpp` — the operator's original example — is fine: 5 functions / 0 structs, and `[DERIVED]` is C3-required for `[STRUCT]` only (198 struct-DERIVED vs 3 function-DERIVED corpus-wide); function facts are plugin-LIVE per D-307, not required in-comment.
- **Fix shape:** route ALL source enumeration through ONE shared file-list (canonical sister: `check_code_tag_blocks.engine_source_files`) and make it ignore-correct — `rg -u` / `--no-ignore-vcs` **plus explicit excludes** (`build*/`, `.git/`, vendored trees) so gitignored-but-real source IS scanned while junk stays out; every gate then inherits the correct view. Add the **non-vacuity tooth**: a selftest that plants a *gitignored* un-converted fixture and asserts the gate REDs (today it would pass silently). Also **declare the policy explicitly** — is private/gitignored source IN the conversion contract? (It is compiled code, so presumably yes.) Codify it either way so the exclusion is *declared*, never accidental.
- **Trigger:** next touch of `check_conversion_completeness` or the shared source enumerator — E.1.2.B `0.2` (the update-orchestrator) is the natural home since it already composes the checker family — OR the moment a 2nd private source file lands.
- **Cross-ref:** D-307 (DERIVED = tool-written + CI-checked — the tier this gate defends) · Class-51 (vacuously-green guard; here the guard cannot fail on unread input) · `feedback_verify_by_context_not_count` (the "163 files / 0 gaps" count read as completeness) · `project_public_repo_is_code_only` (why gitignored source exists in-tree) · TECH_DEBT-176 (unified runner — the composition point for the shared enumerator).
- **CLOSED:** 2026-07-20 at E.1.2.B `0.2` (BB-1 corpus-contract wiring), commit `67d901a`. `converted_files()` no longer shells out to `rg -l`; it enumerates through the single-sourced contract (`engine_source_files(profile="validate")`) and applies the contract's anchored `selectors.converted.line_prefix` with `startswith()`. `.gitignore` is structurally no longer an input to corpus membership (D-393 pt 2), so the fix is at the SHARED enumerator exactly as the fix-shape asked — all six consumers now inherit one view.
- **Measured at close:** 172 converted files vs rg's 163. The 9-file delta is precisely C-396 #2's prediction — `Strategies/private/EmaCross.hpp` (the live gitignored instance, hidden by a DIRECTORY rule at `.gitignore:167`), the 3 file-symlinked `DOCS/*TEMPLATE*.hpp`, and the 5 `schema_golden` fixtures (unreachable for rg because engine `tests/` is a directory symlink and rg follows neither symlink kind without `-L`). All 9 scan CLEAN, so the baseline stays at HARD-zero — the entry's "current impact NIL" assessment was correct. What changed is that "clean" is now a MEASUREMENT rather than an assumption.
- **Non-vacuity tooth (the fix-shape REQUIRED one):** `--selftest` now plants a synthetic frozen fixture and asserts a gitignored source file is still enumerated AND judged. ⚠️ The FIRST version of that tooth was itself VACUOUS and the discrimination check caught it: it used a FILE-level ignore, and ripgrep skips a gitignored DIRECTORY while still returning a file-level-ignored file — so the fixture would have passed against the very rg enumerator it exists to catch. Rewritten directory-level (also the real-world shape) and verified discriminating: rg sees 0, the contract walk sees 1. A guard's own tooth needs a positive control too.
- **Policy now DECLARED, not accidental** (the entry's third ask): gitignored-but-real source IS in the conversion contract. Stated once in `corpus_contract.json` (`two_populations.scan_population` + D-393 pt 2) instead of falling out of a tool's default flags.
- **Adjacent, NOT closed:** TECH_DEBT-246 (functions never checked) — the shared enumerator was its PRECONDITION, not its fix; it needs its own check class + planted-function tooth. TECH_DEBT-253 (zero `.py` scanned) stays open and TOMBSTONED in the contract as `deferred.python_sources`; its false docstring claim was removed at this commit so the gate no longer advertises coverage it does not have.


### TECH_DEBT-255 — `check_identifier_retirement.py --update` overwrites its golden ledger with NO diff and NO confirmation (an agent can rubber-stamp it)

- **id:** TECH_DEBT-255 · **severity:** medium (it guards H21 — the Knight-Capital identifier-retirement invariant — and its re-bless path is the one an automated caller can trip silently) · **opened:** 2026-07-19 · **status:** closed · **surface_tags:** [ci-tooling, golden, h21, m10, delegation-safety, class-51]
- **What:** `tools/check_identifier_retirement.py:277-281` implements `--update` as: write the ledger, `return 0`. **No diff is shown and no confirmation is required.** `tools/identifier_ledger.txt` is the golden for H21 (*"NEVER renumber/reuse/drop a row"*) — the Knight-Capital discipline. So the tool that enforces append-only-immutable identifiers can have its own record silently rewritten by any caller, including a delegated agent that "fixed the red by re-baselining."
- **Why it matters:** **D-394** decided the opposite posture for the corpus golden — `--bless` requires a TTY + typed confirmation, non-interactive **hard-refuses rc=2**, no `--yes` escape hatch — on the reasoning that *"per D-385/M10 a delegated agent becomes structurally INCAPABLE of blessing a golden."* That property is exactly as load-bearing here, arguably more so: this golden guards a capital-adjacent invariant. Right now the two goldens in the tree have **opposite** re-bless safety postures. (Same shape in `check_latency_path_conformance.py:569` `--update-budgets`, though a ratchet is lower-stakes than an append-only ledger.)
- **Fix shape:** bring `--update` to the D-394 contract — show the per-row diff, require a TTY + typed confirmation, hard-refuse `rc=2` when non-interactive. **Do NOT silently "fix" it as part of another ship:** it has its own callers (pre-commit Check H, `/readiness` Check 46, `/post-ship-audit`), and any of them invoking it non-interactively would newly RED. Enumerate those callers first — the same enumerate-before-flipping discipline the `0.2` (e) prerequisite needed.
- **Trigger:** the `0.2` gate-wiring pass, alongside the corpus `--bless` implementation — build both against one shared bless helper rather than two, or the postures diverge again.
- **Cross-ref:** **D-394** (the contract this should adopt; the sibling-hole was recorded there but not ledgered until now) · **D-385/M10** (`acceptance-oracle-totality-before-delegation.md`) · **H21** + `dead-code-and-identifier-retirement-discipline.md` (what the ledger guards) · `check_latency_path_conformance.py:569` (the ratchet sibling) · Class-51.
- **CLOSED:** 2026-07-20 at E.1.2.B `0.2` (BB-1/BB-2 gate layer). `--update` no longer does `write_ledger(current); return 0`; it routes through **`tools/bless.py`**, the ONE shared re-bless path — which is what this entry's own trigger demanded (*"build both against one shared bless helper rather than two, or the postures diverge again"*). The corpus golden and the H21 tombstone ledger now share a single implementation of the D-394 contract, so they cannot drift into opposite postures again.
- **What it now enforces:** a TTY is REQUIRED; the per-file diff is SHOWN together with what the ledger currently holds and how many rows would be REMOVED (the expensive direction); a typed confirmation (`bless identifier-ledger`, not y/n) is demanded; a non-interactive caller is HARD-REFUSED `rc=2` without ever blocking on stdin. Per D-385/M10 a delegated agent is now structurally INCAPABLE of re-blessing the H21 golden. Verified by running it non-interactively against a planted version-decrease: REFUSED rc=2, ledger byte-unchanged.
- **Bonus, D-369:** it also inherits no-op ⇒ NO WRITE. `--update` on an unchanged ledger now leaves the file byte-identical instead of rewriting it unconditionally, so a "run the producer, expect 0-diff" currency check finally means something for this artifact.
- **SAFE TO TIGHTEN — callers enumerated FIRST**, per the entry's own warning (the enumerate-before-flipping discipline): `--update` has NO automated caller. `.githooks/pre-commit:360` only PRINTS it as an operator instruction, the ledger header mentions it in a comment, and the negative self-test manipulates the ledger directly with `cp`/`sed` rather than invoking it. Pre-commit Check H, `/readiness` Check 46 and `/post-ship-audit` all call the VERIFY mode, which is untouched. Nothing newly REDs.
- **⚠️ FOUND WHILE CLOSING THIS — a separate, real defect:** the H21 guard's negative self-test had a BROKEN TOOTH. Case (2) hardcoded `version|SHARDED_SNAPSHOT_VERSION|8` while the ledger had moved to `|10`, so the `sed` was a NO-OP, nothing was planted, the guard passed on an unmutated ledger, and the test reported *"version-decrease should be RED"* — which reads as *the guard is broken* when the truth was *the fixture failed to plant*. **The guard itself was fine**; only its proof was. Fixed three ways: values are now DERIVED not hardcoded, every plant is ASSERTED (a stale anchor fails loudly as "planted NOTHING" instead of masquerading as a guard failure), and the self-test now runs against a THROWAWAY COPY via a new `IDENTIFIER_LEDGER` override so it can never corrupt the tracked golden. **It was also wired into `check_session_docs.sh` as HARD** — it previously ran in NO gate, which is precisely how the tooth stayed broken. Same shape as the calibration-corpus rule about fixtures anchored to live values.
- **Still open, adjacent:** `check_latency_path_conformance.py:569` `--update-budgets` has the same unconfirmed-write shape. Lower stakes (a ratchet, not an append-only identity ledger) but it is the next consumer `bless.py` should absorb.

### TECH_DEBT-101 — TOMBSTONE (re-homed to TECH_DEBT-238; slot RESERVED, never reuse)

- **id:** TECH_DEBT-101 · **severity:** LOW · **status:** tombstone · **surface_tags:** [ledger-hygiene, H21]
- **Disposition:** the entry was lost in the ledger split/renumber history. The DEBT ITSELF — delete `FOREACH_LEGACY_PREFIXED_KEY` once production v1 stamps are extinct — is real and was re-homed to **TECH_DEBT-238** (this file) on 2026-07-16. Live citations remain in `ML_Headers/ModelInference.hpp` and `CoreFrameworks/MetaRegistry.hpp` row 65; they resolve HERE and forward to -238.
- **Why a tombstone and not a deletion (H21):** the id is cited from engine source. Dropping the slot would let a future entry reuse `101` and silently re-point those citations at unrelated content — the doc-plane form of the Knight Capital slot-reuse failure. The slot is RESERVED permanently.
- **Cross-ref:** TECH_DEBT-238 (the live home) · TECH_DEBT-249 (the dangling-id sweep that found it).
