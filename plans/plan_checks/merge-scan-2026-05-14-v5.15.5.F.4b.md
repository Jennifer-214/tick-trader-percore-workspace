# /merge-scan report — v5.15.5.F.4b CfgFieldRegistry — 2026-05-14

**Plan:** `plans/v5.15-live-readiness/subplans/2026-05-13-v5.15.5.F.4b-foreach-cfg-field-registry-implementation.md`
**Sprint umbrella:** `2026-05-13-v5.15.5.F.4-universal-cfg-registry-sprint.md`
**Engine HEAD:** `f72caef` (v5.15.5.F.3 — registry-bitmap SET discipline)
**Scope:** reuse-merge + redundancy detection across ~50 existing FOREACH_ registries; bitmap API compliance; categorical enum reuse; mirror-incomplete; AUTOPOPULATE alignment.

---

## TL;DR — verdict

**Verdict:** YELLOW — design is well-aligned with existing patterns (heterogeneous-registry / AUTOPOPULATE / bitmap-flag-api / SCOPE COLUMN by Kind) but has **TWO HIGH-priority structural reuse issues** that should be absorbed into .F.4b before locking the descriptor schema, plus several MED-priority items where decisions should be made now to avoid drift.

**Top-3 highest-impact items to act on (within .F.4b scope):**

1. **HIGH — Pre-existing `CfgFieldDef` struct at SettingsPanel.hpp:35-42 + `field_defs[]` (109+ entries)** is the de facto v0 of the proposed registry, AND it already consumes the 5 domain CFG_FLAG registries via auto-extension (lines 297-303). New `CfgFieldDescriptor` must **subsume** this, not parallel it. **Cutover, don't coexist.**

2. **HIGH — `INFERENCE_CFG_AUTOPOPULATE` (FOREACH_CFG_DERIVED_INFERENCE_CFG, v5.15.5.A.7) is a third autopopulate consumer of cfg-side reads.** The proposed `CfgFieldRegistry` overlaps it on ~7 fields (`confidence_threshold_scale`, `confidence_hard_block_threshold`, `held_out_fraction`, `bandit_blend_ratio`, `fee_rate_maker`, `fee_rate_taker`, `ml_tp_pct`, `ml_sl_pct`, `barrier_blend_mode`). They serve different consumers (stamp emit vs runtime cfg I/O) but read the SAME cfg fields. Don't merge them — but declare orthogonality explicitly in the plan + .F.4d reverse-drift CI.

3. **MED — `tt::stamp_parse_field<T>` pattern (CLAUDE.md item 23, established in StampBoundModelConstRegistry.hpp:86-99) already exists and is canonical.** The plan's `tt::cfg_parse_field<Kind>` should mirror its shape EXACTLY (template by trait, dispatch via `if constexpr (std::is_array_v<T>) / is_floating_point_v / is_unsigned_v`), not introduce a parallel Kind-token dispatch. Lean on the existing pattern; don't reinvent.

---

## 1. Existing FOREACH_ registry inventory (50 total — `.F.4b` must not duplicate)

Categorized scan:

### A. Cfg-flag domain registries (5 — DOMAIN SPLIT per heterogeneous-registry-pattern.md)
- `FOREACH_LIFECYCLE_CFG_FLAG` (3 entries, uint8_t bitmap, partial_exit_enabled / breakeven_*)
- `FOREACH_GATE_CFG_FLAG` (6 entries, uint8_t, depth_enabled / gate_ema_enabled / no_trade_band / cost_gate / barrier_gate / param_staleness_gate)
- `FOREACH_ML_CFG_FLAG` (12 entries, uint16_t, confidence_* / bandit_* / ridge_* / vol_scaling / lazy_rebuild / exit_blender_mode / per_horizon_barrier_blend)
- `FOREACH_RISK_CFG_FLAG` (3 entries, uint8_t, kill_switch_enabled / vol_sizing / ws_dead_time_flatten)
- `FOREACH_OPS_CFG_FLAG` (4 entries, uint8_t, session_filter / notify / acknowledge_*_drift)

**Plan position (deferred to .F.4c):** these stay in their domain registries; cfg.X reads via `BITMAP_IS_SET(cfg.<domain>_cfg_flags, MASK_<DOMAIN>_<NAME>)`. **Confirmed correct.** Do NOT absorb 28 booleans into FOREACH_CFG_FIELD as KIND_BOOL — that would re-fragment the cache-coherent uint8/uint16 bitmap layout established v5.14.9.F. Plan correctly leaves them on the domain side; KIND_BOOL slot in registry should be used only for legacy non-bitmap booleans + future singletons that don't fit a domain.

**`emit_when` predicates already use BITMAP_IS_SET** for these flags (StampBoundCfgRegistry.hpp:107-111, 125-133, 145; CfgDerivedInferenceCfgRegistry.hpp:108-116). The "cfg-flag-on-bitmap" → "stamp-bound bit derivation" pipeline is established.

### B. Stamp / model body registries (8 — wire-format-locked)
- `FOREACH_STAMP_BOUND_CFG` (24 entries, 7-col tuple — `name, type, fmt, default_val, get_cfg, emit_when, emit_source`); has STAMP_CFG_AUTOPOPULATE companion. **THIS IS THE TARGET of the `STAMP_BOUND` derived-filter (Deliverable A).**
- `FOREACH_STAMP_BOUND_MODEL_CONST` + `_GROUPS` + `_STANDALONE` + `_PRE_CFG` + `_POST_CFG` (split per pre-post-cfg-registry-split-for-emit-order-preservation.md, item 22)
- `FOREACH_CFG_DERIVED_INFERENCE_CFG` (11 entries, 3-col `name, cfg_extraction_expr, gate_when` — at MemHeaders/CfgDerivedInferenceCfgRegistry.hpp; new v5.15.5.A.7). Has `INFERENCE_CFG_AUTOPOPULATE`. **Sister to FOREACH_STAMP_BOUND_CFG** — reads cfg side, writes ModelHandle.inference_cfg_* fields.

### C. ML pipeline registries (8 — orthogonal to cfg)
- `FOREACH_FEATURE` (~40 entries, 7-col `id, name, version, enabled, fn, note, staleness`); uint64_t FEATURE_ENABLED_BITMAP. **Truly orthogonal — features are computation, not cfg.**
- `FOREACH_BANDIT_ALGORITHM`, `FOREACH_BARRIER_BLEND_MODE`, `FOREACH_DEGRADATION_CURVE`, `FOREACH_IC_VARIANT`, `FOREACH_ROLLING_WINDOW`, `FOREACH_PER_ARM_FLAG`, `FOREACH_EZOO_INIT_FLAG`, `FOREACH_CFG_DRIFT_CHECK`, `FOREACH_CONFIDENCE_PERSIST_FIELD` — enum/state catalogs. **Orthogonal to cfg-field shape; no merge.**
- `FOREACH_ENSEMBLE_POST_LOAD` / `FOREACH_SINGLE_ZOO_POST_LOAD` (PostLoadSetup pattern per postloadsetup-registry-pattern.md). **Orthogonal.**

### D. Observability + state registries (12 — orthogonal)
- `FOREACH_FAILURE_MODE` (heterogeneous storage classes: BIT_FLAG / COUNTER_U32 / PERCENT_U8); uint64_t failure_flags bitmap
- `FOREACH_CORE_STATE_FLAG`, `FOREACH_OMS_STATE_FLAG`, `FOREACH_PER_CORE_STATE_FLAG`, `FOREACH_OMS_STATE_MULTI_BIT`, `FOREACH_ARCH_FIELD_DRIFT`, `FOREACH_DISPLAY_META_FIELD`, `FOREACH_GATE_DIAG_PAIR`, `FOREACH_OMS_META_SLOT`, `FOREACH_CORE_CTX_INIT_FIELD`, `FOREACH_CORE_CTX_RESET_FIELD`, `FOREACH_CORE_CTX_SUMMARY_FIELD`, `FOREACH_POSITION_FIELD`, `FOREACH_OMS_FIELD`, `FOREACH_OMS_PER_SLOT_FIELD`, `FOREACH_SLOW_PATH_GATE`, `FOREACH_SP_SECTION`, `FOREACH_TRADE_LOG_COL`, `FOREACH_CALIB_LOG_COL`, `FOREACH_RECONCILE_MODE`, `FOREACH_LIVE_READINESS_CHECK`, `FOREACH_SESSION_PHASE`, `FOREACH_PANEL`, `FOREACH_BACKTEST_METRIC`, `FOREACH_TARGET`, `FOREACH_HALT_REASON`, `FOREACH_SHALT`, `FOREACH_REGIME`, `FOREACH_STRATEGY` — **all orthogonal to cfg-field shape**.

### E. Strategy + regime registries (4 — orthogonal but extend in .F.4h)
- `FOREACH_STRATEGY`, `FOREACH_REGIME`, `FOREACH_HALT_REASON`, `FOREACH_SHALT`

**Plan position for .F.4h:** FOREACH_STRATEGY adds category-mask column. **No overlap with proposed FOREACH_CFG_FIELD** — different shape (instance tuple vs cfg-field-descriptor tuple). **Plan correct.**

---

## 2. HIGH priority — pre-existing CfgFieldDef + field_defs[] is the v0

**Location:** `GUI/SettingsPanel.hpp:35-306` — 6-column struct `CfgFieldDef { key, label, section, type, fmt, tooltip }` + 109+ static field_defs entries. **AND** lines 297-303 auto-extend via the 5 domain CFG_FLAG registries (already consuming FOREACH_LIFECYCLE/GATE/ML/RISK/OPS_CFG_FLAG with `X(name, legacy_field, display_label, section, doc)` X-macro). This is what 26+ "site adds" already pivot around.

**Why this matters for `.F.4b`:**

1. The plan describes the new `CfgFieldDescriptor` (128 bytes; 12+ fields including categorical bitmap columns + tt:: payload union + lives_in_struct + metadata_flags) as if greenfield. It's not — there's a 6-col 32-byte `CfgFieldDef` already, with 90+ rows of curated tooltip/section data.

2. The new design must **migrate** existing field_defs[] entries to FOREACH_CFG_FIELD rows. The proposed Step 3 mentions this ("Locate existing `field_defs[]` array... For each KIND_DOUBLE + KIND_DOUBLE_PCT field... Remove from `field_defs[]`"), but doesn't account for:
   - **The 5 domain registries' auto-extension** at lines 297-303 already feeding field_defs[] for ~28 boolean rows. Removing those would re-fragment; KEEP them or migrate the 5 domain registries into FOREACH_CFG_FIELD with KIND_BOOL + STRUCT_CFG (the plan's .F.4c). The plan's "leave 5 domain registries alone" decision conflicts with absorbing the 28 booleans into FOREACH_CFG_FIELD via lines 297-303's auto-extension path.
   - **Tooltip text quality.** 109 existing rows have hand-tuned operator-facing prose (multi-line, Discord/Telegram webhook examples, version-bound notes). The new registry's `tooltip` column must preserve these BYTEWISE. Don't lose work.
   - **Section names map to cfg.example documentation grouping**, not just GUI. Migration must preserve them.

**Recommended action — absorb into .F.4b:**
- Step 3 explicitly says "Locate existing field_defs[]" — extend to **migrate** the 40 KIND_DOUBLE/_PCT entries' tooltip+section text into FOREACH_CFG_FIELD rows (don't lose), AND verify the registry-extension blocks at lines 297-303 (FOREACH_*_CFG_FLAG) **continue to work** during .F.4b's transition (since they emit CFG_BOOL entries that aren't migrated until .F.4c). Concretely: the macro `EMIT_PANEL_RENDER` walk should COEXIST with the existing field_defs[] walk for the un-migrated kinds.
- Add an explicit step: **"Audit field_defs[] for KIND_DOUBLE+KIND_DOUBLE_PCT rows; preserve their tooltip/section text in FOREACH_CFG_FIELD rows; verify NUM_FIELDS doesn't decrement when those rows are removed from field_defs[]"** OR keep field_defs[] static + just SUPPLEMENT with the new registry-driven walk (no removal at .F.4b — defer cleanup to .F.4d).
- **Decision needed:** does the registry SUBSUME field_defs[] (cleaner, more migration risk) or COEXIST (safer, defers cleanup to .F.4d)? Plan says subsume (Step 3 "Remove from field_defs[]"). Adopt explicit migration table in .F.4b documenting which 40 rows move + their preserved tooltip text.

---

## 3. HIGH priority — INFERENCE_CFG_AUTOPOPULATE orthogonality

**Location:** `MemHeaders/CfgDerivedInferenceCfgRegistry.hpp:101-116` — 11 entries with 3-col tuple `(name, cfg_extraction_expr, gate_when)`. AUTOPOPULATE companion writes to `inf.inference_cfg_<name>` (prefix-aware token paste). Currently called from `StampHelper.hpp` to populate training-time stamp body.

**Overlap with FOREACH_CFG_FIELD:** ~7 of the 11 fields are ALSO in FOREACH_CFG_FIELD's proposed row set:
- `confidence_hard_block_threshold`, `held_out_fraction`, `bandit_blend_ratio` — explicitly listed in the plan's initial DOUBLE rows
- `fee_rate_maker`, `fee_rate_taker`, `ml_tp_pct`, `ml_sl_pct`, `barrier_blend_mode` — implied by "remaining ~80 entries" comment

**The relationship is read-vs-emit:**
- `FOREACH_CFG_FIELD` describes the cfg field (parser, GUI, save, per-core override, drift check)
- `FOREACH_CFG_DERIVED_INFERENCE_CFG` describes how cfg field VALUE is captured into model stamp body at training time

These are NOT duplicates; they're two CONSUMERS of the same underlying cfg fields. **But:**

**Risk:** if FOREACH_CFG_FIELD adds a new STAMP_BOUND row that's ALSO an inference_cfg_* derivation, and INFERENCE_CFG_AUTOPOPULATE doesn't pick it up, the cfg→stamp emit drifts. The plan's `STAMP_BOUND` metadata bit handles the FOREACH_STAMP_BOUND_CFG derivation (deliverable A) but doesn't address FOREACH_CFG_DERIVED_INFERENCE_CFG.

**Recommended action — clarify in .F.4b:**
- Document in `CfgFieldRegistry.hpp` header comment: "**Orthogonal registries:**
  - `FOREACH_STAMP_BOUND_CFG` — derived from FOREACH_CFG_FIELD via STAMP_BOUND bit (closes dual-registry stamp drift)
  - `FOREACH_CFG_DERIVED_INFERENCE_CFG` — sister registry: cfg → inf.inference_cfg_* population. STAYS SEPARATE. New cfg fields that also need inference_cfg_* derivation require BOTH a FOREACH_CFG_FIELD row AND a FOREACH_CFG_DERIVED_INFERENCE_CFG row + matching FOREACH_STAMP_BOUND_MODEL_CONST_POST_CFG row."
- Add a CI parity check (deferred to .F.4d alongside reverse-drift CI): every FOREACH_CFG_DERIVED_INFERENCE_CFG `name` MUST correspond to a FOREACH_CFG_FIELD row (or explicit allow-list entry). Closes the drift class for new cfg-derived inference_cfg_* additions.
- **Optional — defer to .F.4i / v5.15.6:** consider whether `applies_to_op_mode_cat: OP_MODE_CAT_TRAINING` could absorb FOREACH_CFG_DERIVED_INFERENCE_CFG entirely. Probably not in scope; the cfg→inf prefix-paste shape is non-trivial.

---

## 4. MED priority — tt:: dispatch pattern alignment

**Pre-existing:** `tt::stamp_parse_field<T>(T& dst, const char* val)` at `ML_Headers/StampBoundModelConstRegistry.hpp:86-99` — template-by-type, dispatches via `if constexpr (std::is_array_v<T>) / is_floating_point_v / is_unsigned_v / else`. Established v5.14.8.A.merged.4. **Item 23 of CLAUDE.md is built around this exact shape.**

**Proposed:** `tt::cfg_parse_field<Kind>(Cfg* dst, const Descriptor&, const char* val)` — template-by-Kind-enum, requires 5+ explicit specializations.

**Tension:** the existing pattern is *template-by-type* (one template, one body, type-dispatch via traits — robust to new types automatically). The proposed pattern is *template-by-enum-token* (specialize per Kind — adding a new Kind requires another specialization).

**Recommendation — adopt template-by-type as primary, Kind-enum as auxiliary metadata:**
- The Kind enum on the descriptor stays (for GUI render dispatch — `cfg_render_field<Kind>` legitimately needs Kind-dispatch because rendering DOES differ structurally per Kind: DragFloat vs Combo vs Checkbox vs InputText).
- For parse + save: extract the **field offset + type from the descriptor**, call `tt::cfg_parse_field<T>` (existing shape; passes `*reinterpret_cast<T*>(cfg_byte_ptr + offset)`). One body; type-dispatched via existing traits. **Re-uses** the validated v5.14.8 shape; aligns CLAUDE.md item 23 reference application count.
- Caveat: `KIND_DOUBLE_PCT` vs `KIND_DOUBLE` differ in DISPLAY but not STORAGE; both are `double`. Parser is identical; rendering differs. Clean.
- Caveat: `KIND_INT_ENUM` is `int` storage but adds clamp-to-`[0, count)` semantics — that's a payload-driven validate-after-parse, not a different parser. Same shape applies.

**Effort impact:** ~50 LOC simpler than the plan's Kind-specialization-per-Kind. Reduces parser test surface to one tt::cfg_parse_field<T> body.

---

## 5. MED priority — descriptor cache layout vs latency-vs-cache decision framework

**Plan's stated decision:** "Accept 128-byte descriptor; cfg metadata not latency-critical per latency-vs-cache-decision-framework.md."

**Cross-check:** descriptor array indexed by FIELD_IDX_<name>; ~250 entries × 128 bytes = 32 KB total. L1 d-cache is typically 32-48 KB per core. Walk in parser + render is per-pass linear → cache-warm on second access; **fits L1 comfortably** as a working set OR streams from L2 (4ns/line) without measurable cost.

**No action needed** — plan's analysis is correct. Note: if FOREACH_CFG_FIELD grows past ~400 rows the descriptor table starts to spill L1; a sidecar lookup table (`cfg_field_offset_table[256]`) keyed by FIELD_IDX would be cheaper for the hot accessor paths. Defer to v5.15.6+ if needed.

---

## 6. MED priority — BITMAP_* API compliance check on metadata_flags

**Plan's design:** `uint16_t metadata_flags` on descriptor; 10 bits used (`PER_CORE_OK / RESTART_REQUIRED / SAFETY_CRITICAL / DEPRECATED / STAMP_BOUND / HIDDEN_BY_DEFAULT / IS_SECRET / IS_BOOT_ONLY / AFFECTS_STAMP_PARITY / LOG_VALUE_FORBIDDEN`).

**Plan's macros (deliverable B):**
```cpp
#define EMIT_PER_CORE_DECL(kind_token, name, ..., meta, ...) \
    EMIT_PER_CORE_DECL_IF_##meta(kind_token, name)
```

**Issue:** the dispatch shape `EMIT_X_IF_##meta` assumes `meta` is a single TOKEN. But the descriptor's `metadata_flags` is a **uint16_t bitmap** — `PER_CORE_OK | STAMP_BOUND | SAFETY_CRITICAL`. Token-paste on a bitmap expression `PER_CORE_OK | STAMP_BOUND` doesn't produce a valid macro name; it produces `EMIT_PER_CORE_DECL_IF_PER_CORE_OK | STAMP_BOUND` which won't compile.

**Two valid alternatives:**
- **Option A (preferred):** dispatch on a **separate per-row "presence bit" token** that the macro explicitly grafts (e.g., `X(KIND, name, ..., HAS_PER_CORE_OK, HAS_STAMP_BOUND, HAS_RESTART_REQUIRED, ...)` — explicit YES/NO columns). 10 extra macro args. Cleaner if there are < 5 metadata bits to dispatch on.
- **Option B:** runtime branch — `if (descriptor.metadata_flags & MASK_PER_CORE_OK) { emit_per_core_storage(); }`. No compile-time dispatch; runtime cost ~1ns per entry × 250 entries × boot-time = trivial. Simpler.

**Recommendation:** Use Option B for runtime emission. Use Option A only for compile-time-required dispatch (struct field declarations that need per-row gating). The plan's deliverable B example "X-macro generates Cfg struct fields" works fine with Option A.

**Effort:** clarify in CfgFieldRegistry.hpp's AUTOPOPULATE design before locking the descriptor.

---

## 7. MED priority — AUTOPOPULATE companion shape consistency

**Existing AUTOPOPULATE applications (per autopopulate-pattern-for-production-caller-class.md):**

| Companion | Registry | Target | Notes |
|---|---|---|---|
| `STAMP_CFG_AUTOPOPULATE(inf, cfg)` | FOREACH_STAMP_BOUND_CFG | `StampInferenceCfgInputs inf` | Y3 dispatch by emit_source |
| `STAMP_MODEL_CONST_AUTOPOPULATE` | FOREACH_STAMP_BOUND_MODEL_CONST | (QUARANTINED v5.15.3.A.1 — self-referential expansion broken) | TECH_DEBT-036 |
| `INFERENCE_CFG_AUTOPOPULATE(inf, cfg)` | FOREACH_CFG_DERIVED_INFERENCE_CFG | `inf.inference_cfg_<name>` (prefix-paste) | v5.15.5.A.7 |
| `LIFECYCLE_CFG_FLAG_AUTOPOPULATE_FROM_TRIPLE` | FOREACH_LIFECYCLE_CFG_FLAG | `uint8_t lifecycle_cfg_flags` | scattered-locals variant |
| `GATE_CFG_FLAG_AUTOPOPULATE_FROM_HEX` | FOREACH_GATE_CFG_FLAG | `uint8_t gate_cfg_flags` | scattered-locals variant |
| `RISK_CFG_FLAG_AUTOPOPULATE_FROM_TRIPLE` | FOREACH_RISK_CFG_FLAG | `uint8_t risk_cfg_flags` | scattered-locals variant |
| `ML_CFG_FLAG_AUTOPOPULATE_FROM_SEPTUPLE` | FOREACH_ML_CFG_FLAG | `uint16_t ml_cfg_flags` | scattered-locals variant |

**Proposed .F.4b AUTOPOPULATE companions:**
- `CFG_PARSER_AUTOPOPULATE`? — implied by EMIT_CFG_PARSER_CASE walks
- `CFG_SAVE_AUTOPOPULATE`? — implied by EMIT_CFG_SAVE_LINE walks

**Plan doesn't actually NAME these as AUTOPOPULATE macros.** The Step 4/5 examples define EMIT_CFG_PARSER_CASE + EMIT_CFG_SAVE_LINE as inline X-macro expansions inside the parser/save function bodies, not as AUTOPOPULATE companions used at multiple call sites.

**Question:** is there a multi-caller production-caller class here that AUTOPOPULATE would close? Parser is one site (CfgParser_HandleKV). Save is one site (Cfg_Save). GUI render is one site (Settings panel). **NO multi-caller class** → no AUTOPOPULATE needed for parser/save/render.

**But:** per-core override emission is multi-caller-ish:
- Boot: `ControllerConfig_ResolveForCore(cfg, core_idx)` reads per-core overrides
- Save: `Cfg_Save` emits `core_N_<name>=` per per-core row
- Parser: `core_N_<name>` key parsing
- GUI: per-core tab render
- Snapshot: include per-core override values in PerCoreSnap

That's 4-5 call sites. **AUTOPOPULATE for the emit/parse direction here would be valuable** — `CFG_PER_CORE_OVERRIDE_AUTOPOPULATE(cfg, core_idx)` emits storage declarations + accessor wrappers. **In scope for .F.4g (per-core AoS-by-core re-layout)** per the umbrella, not .F.4b.

**Recommendation:** plan should explicitly say "AUTOPOPULATE companions deferred to .F.4g for per-core override surfaces; parser/save/render are single-site so no AUTOPOPULATE needed."

---

## 8. LOW priority — categorical enum bit space + overflow guards

**Plan's design:**
- `StrategyCategory : uint32_t` (32 bits; ~12-15 used)
- `OpModeCategory : uint16_t` (16 bits; ~5 used)
- `RegimeCategory : uint16_t` (16 bits; ~4 used)
- `RiskCategory : uint16_t` (16 bits; ~4 used)

**Cross-check:** no existing enum/bitmap in the codebase claims `STRAT_CAT_*` / `OP_MODE_CAT_*` / `REGIME_CAT_*` / `RISK_CAT_*` namespace. No overlap with `FailureMode`, `EzooInitFlag`, `OmsStateFlag`, etc. ✓ Clean namespace.

**Overflow guards (per bitmap-overflow-protection-discipline.md):** plan correctly includes them. ✓

**Caveat — distinguish CATEGORY from STATE:**
- `RegimeCategory` bitmap is conceptually parallel to existing `enum Regime { REGIME_RANGING, REGIME_TRENDING, ... }` (5 states; ordinal). One regime is active at a time → fits multi-bit-state-encoding-pattern.md NOT bitmap-flag-api.md. **But the descriptor's `applies_to_regime_cat` IS a bitmap — "this cfg field applies to ANY of these regimes" is the right semantics.** Both views are valid: the active regime is ONE state; the applicability mask is N states.
- Same for `RiskCategory` — `risk_degradation_curve` is one of OFF/LINEAR/EXP/STEP at a time (multi-bit-state).
- **Recommendation:** clarify in design spec that category bitmaps ≠ state enums. Document the dual representation. Already implicit in `categorical-tag-applicability-pattern.md` but worth surfacing in the registry header comment.

---

## 9. LOW priority — atomic / clock / cfg-access reuse per CLAUDE.md item 16

**Plan's runtime touches:** parser (boot-only), save (operator-triggered), render (60 Hz GUI), per-core override emission (boot + per-cycle slow-path resolution).

**No hot-path additions in .F.4b.** Slow-path resolution (`ResolveCoreCfg`) is .F.4e scope, not .F.4b.

**No atomic accesses introduced by registry walking.** All cfg reads are non-atomic POD struct field reads (boot-frozen per cfg-flag-eligibility-criteria.md).

**No clock reads introduced.** GUI render is ImGui-frame-driven; no clock_gettime added.

**No reuse opportunity surfaced** — registry walks are independent of existing slow-path/hot-path atomic/clock surfaces.

**Verdict:** ✓ Clean per CLAUDE.md item 16.

---

## 10. LOW priority — recent v5.15.5.F.3 registry-bitmap SET discipline overlap

**Concern:** does the new `metadata_flags` bitmap on descriptors have the registry-bitmap-set-discipline class risk?

**Analysis:**
- `descriptor.metadata_flags` is **set ONCE at static-init time** via the FOREACH_CFG_FIELD expansion (no runtime SET sites). The bits are compile-time-determined from the registry tuple.
- The two anti-pattern shapes (A: missing SET alongside data write; B: chokepoint bypassed) don't apply because there's no runtime data being written here.
- The only "SET site" concern is the registry row authoring — and that's exactly what FOREACH_CFG_FIELD's single-source-of-truth structure prevents.

**Verdict:** ✓ Not at risk. The registry-bitmap-SET-discipline class applies to runtime-mutated bitmaps; metadata_flags is a static-init bitmap.

**Sanity check on PROPOSED `cfg.metadata_flags` reads** (the field-descriptor accesses by parser/render): plan should use `BITMAP_IS_SET(descriptor.metadata_flags, MASK_PER_CORE_OK)` not `(descriptor.metadata_flags & MASK_PER_CORE_OK)`. The int-truncation bug class (CLAUDE.md item 20) is the reason BITMAP_IS_SET exists. Since `metadata_flags` is uint16_t and MASK_PER_CORE_OK fits low bits, the truncation risk is zero here — but the convention is to use the API uniformly. Recommend lint via `/dod-audit` post-ship.

---

## 11. Items to absorb into .F.4b vs defer

### Absorb into .F.4b (before locking descriptor schema)
1. **Header comment in CfgFieldRegistry.hpp** declaring orthogonality with FOREACH_CFG_DERIVED_INFERENCE_CFG (item 3 above).
2. **tt::cfg_parse_field alignment with stamp_parse_field's template-by-type shape** (item 4 above) — saves ~50 LOC and re-uses validated pattern.
3. **Migration table for the 40 KIND_DOUBLE+KIND_DOUBLE_PCT field_defs[] entries** documenting which 40 rows move + preserve tooltip BYTEWISE (item 2 above) — operator-facing prose is load-bearing.
4. **Disambiguation of metadata_flags dispatch shape** (item 6 above) — choose Option A (per-row token columns for compile-time) or Option B (runtime branch) before locking the FOREACH tuple arity. Currently the plan implies BOTH which can't coexist.
5. **Decision on field_defs[] SUBSUME vs COEXIST** (item 2 above) — plan says subsume but the 5 domain-registry auto-extension blocks at SettingsPanel.hpp:297-303 emit CFG_BOOL entries that aren't migrated until .F.4c. Confirm coexist-during-transition is the .F.4b approach + that NUM_FIELDS macro still works.

### Hold for later sub-ships (not absorbed into .F.4b)
- **AUTOPOPULATE for per-core override surfaces** → .F.4g (per-core override AoS re-layout)
- **CI parity check between FOREACH_CFG_FIELD + FOREACH_CFG_DERIVED_INFERENCE_CFG** → .F.4d (alongside reverse-drift CI)
- **5 domain CFG_FLAG registries → KIND_BOOL absorption decision** → .F.4c (when KIND_BOOL migration ships); plan currently keeps them separate which IS correct per heterogeneous-registry-pattern.md DOMAIN SPLIT discipline (different cadences + cache locality preserved). **Strong recommend: KEEP THEM SEPARATE.** Boolean cfg flags benefit from cache-coherent bitmap layout; dispersing them as KIND_BOOL slots in the 128-byte descriptor array loses that. **Document this decision in .F.4b** so .F.4c doesn't accidentally re-absorb them.
- **Promotion of categorical-tag-applicability-pattern.md to CLAUDE.md** → after 2nd domain ships (strategy + op_mode at .F.4h) per spec's "Stage 5"
- **Per-bit-per-core override pattern composition** → .F.4g
- **PRE/POST cfg registry split for emit order** (per pre-post-cfg-registry-split-for-emit-order-preservation.md) → applies to FOREACH_STAMP_BOUND_MODEL_CONST (already shipped) + future STAMP_BOUND derived filter; not directly to FOREACH_CFG_FIELD. **No action.**

### Defer to v5.15.6+
- **Phase 2 cfg struct unification** (merge ControllerConfig/BacktestCfg/ControllerCfg/SecretsCfg/TrainingCfg) — explicit deferral in umbrella, ✓
- **Cross-domain category rollout** (regime + risk + feature categorical applicability) — explicit deferral in umbrella, ✓
- **Phase 1 controller.cfg + secrets.cfg + training cfg integration** — v5.15.6 (3 sub-ships), ✓

---

## 12. Function-body parallelism scan

**Pre-existing parallel surfaces that .F.4b touches/replaces:**

| Site A | Site B | Body shape | Merge candidate? |
|---|---|---|---|
| `CfgParser_HandleKV` if-else chain (~600 LOC, 115 strcmp branches) | `Cfg_Save` per-field fprintf chain | Both walk cfg fields linearly | YES — registry-driven walks at .F.4b for DOUBLE/_PCT, .F.4c for INT/BOOL/INT_ENUM, .F.4d for STRING/FILE_PATH **(plan correct)** |
| SettingsPanel render walk (field_defs[]) | Cfg.example documentation | Both consume tooltip+section text | YES — auto-gen cfg.example from registry at .F.4d **(plan correct)** |
| `core_N_<X>` parser branches | Per-core override save branches | Both per-field iterate | DEFERRED to .F.4g per umbrella |

**No new parallel surfaces introduced by .F.4b.** ✓

---

## 13. Branch-vs-branchless audit

**.F.4b is boot-only + GUI (60 Hz). No hot-path or producer code touched.**

- Parser: `strcmp` chain → unordered map / perfect hash candidate. Plan correctly notes "A flat array search is fine for ~250 entries; promote to perfect hash only if profiling shows it matters." ✓
- Cfg_Save: linear FOREACH walk. Single boot/operator-trigger cost. ✓
- GUI render: 60 Hz cache-warm. Branchy is fine. ✓

**No branch-vs-branchless concerns.** ✓

---

## 14. Final ranked priorities

| # | Priority | Item | Effort impact |
|---|---|---|---|
| 1 | HIGH | Migrate field_defs[] tooltip+section text into FOREACH_CFG_FIELD rows BYTEWISE; clarify subsume-vs-coexist for .F.4b transition | ~2hr; load-bearing prose |
| 2 | HIGH | Document orthogonality with FOREACH_CFG_DERIVED_INFERENCE_CFG in CfgFieldRegistry.hpp header + add CI parity check (deferred to .F.4d) | ~30min spec + .F.4d hook |
| 3 | MED | Align tt::cfg_parse_field with template-by-type shape (re-use tt::stamp_parse_field validated pattern) | ~1hr; saves 50+ LOC |
| 4 | MED | Disambiguate metadata_flags dispatch shape (Option A explicit columns vs Option B runtime branch); pick before locking tuple arity | ~30min decision |
| 5 | MED | Confirm 5 domain CFG_FLAG registries stay separate from FOREACH_CFG_FIELD; document in CfgFieldRegistry.hpp header | ~15min comment |
| 6 | LOW | Categorical-vs-state-enum dual representation note for regime/risk masks | ~10min comment |
| 7 | LOW | Use BITMAP_IS_SET on metadata_flags consumers per item 20 convention | per /dod-audit follow-up |

---

## 15. Synthesis paragraph (for parent agent return)

The .F.4b plan is well-grounded in the codebase's existing pattern library (X-macro, AUTOPOPULATE, BITMAP_*, heterogeneous-registry, tt:: type-trait dispatch) and correctly identifies the 6-site cfg drift class as the Class-18 mirror at function-composition level. Two HIGH-priority structural reuse issues should be absorbed before locking the descriptor schema: (1) the pre-existing `CfgFieldDef` + `field_defs[]` (109+ rows, 5 auto-extending domain registries) at GUI/SettingsPanel.hpp is the v0 of the proposed registry and contains load-bearing operator-facing tooltip prose that must be preserved BYTEWISE in the migration; the plan's "subsume vs coexist during transition" needs explicit decision before Step 3 lands; (2) `INFERENCE_CFG_AUTOPOPULATE` (FOREACH_CFG_DERIVED_INFERENCE_CFG, v5.15.5.A.7) reads ~7 of the same cfg fields the new registry covers but writes to a different consumer (stamp body inference_cfg_* fields); declare the orthogonality explicitly in CfgFieldRegistry.hpp and queue a CI parity check at .F.4d. Three MED-priority items improve consistency: align tt::cfg_parse_field with the existing tt::stamp_parse_field's template-by-type shape (re-uses CLAUDE.md item 23 validated pattern, saves ~50 LOC); disambiguate metadata_flags dispatch shape (runtime branch wins for the parser/save side; explicit per-row columns only for compile-time struct-gen); confirm the 5 domain CFG_FLAG registries (`FOREACH_<DOMAIN>_CFG_FLAG`) STAY SEPARATE from FOREACH_CFG_FIELD even when KIND_BOOL lands in .F.4c — DOMAIN SPLIT cache-coherence is load-bearing per heterogeneous-registry-pattern.md. No hot-path or atomic merge candidates surface (.F.4b is boot + GUI 60Hz only). No overlap with existing FailureMode / EzooInitFlag / OmsStateFlag namespaces for new category enums. AUTOPOPULATE companions for per-core override surfaces correctly deferred to .F.4g. The plan's descriptor design (128-byte / 2 cache lines / 4 categorical bitmap columns / uint16_t metadata_flags) is sound per latency-vs-cache-decision-framework.md; no cache-layout regressions surface.
