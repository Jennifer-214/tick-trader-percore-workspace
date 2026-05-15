# /dod-audit RE-AUDIT — v5.15.5.F.4c.3 (global vs per-core registry split) — 2026-05-15

**Plan:** `plans/v5.15-live-readiness/subplans/2026-05-15-v5.15.5.F.4c.3-global-vs-per-core-registry-split.md`
**Engine HEAD:** `88043ea` (post `v5.15.5.F.4c.1`)
**Prior audit:** `plans/plan_checks/dod-audit-2026-05-15-v5.15.5.F.4c.3-split.md` (GREEN with 3 pre-coding refinements + 4 post-ship items)
**Amendments section:** plan body "## Post-audit-gate amendments — 2026-05-15" (151 lines appended)
**Re-audit scope:** verify amendments resolve prior 7 findings (F1–F7) + assess 2 NEW DESIGN_SPECs DRAFT quality + re-confirm Class prevention verdicts for 5 classes (18/19/21/23/24)

---

## Per-prior-finding resolution verdicts

### F1 — `alignas(64)` + paired alignof static_assert: GREEN

**Prior:** plan stipulated `sizeof%64==0` only; alignof discipline missing per `per-snapshot-cluster-layout-pattern.md` Rule 3 / cross-thread-snapshot-publish-cluster-isolation.md Step 5.

**Resolution check** (plan amendment § DOD-discipline locked → DOD-F1):
```cpp
template <unsigned F>
struct alignas(64) PerCoreCfg {
    FOREACH_PER_CORE_CFG_FIELD(EMIT_CFG_STRUCT_FIELD)
};
static_assert(sizeof(PerCoreCfg<64>) % 64 == 0, "PerCoreCfg<F> size cache-aligned");
static_assert(alignof(PerCoreCfg<64>) == 64, "PerCoreCfg<F> alignment cache-aligned");
```

Both asserts present + rationale cites `per-snapshot-cluster-layout-pattern.md` Rule 3 + `cross-thread-snapshot-publish-cluster-isolation.md`. The `alignas(64)` decorator on the type is explicit; `alignof==64` and `sizeof%64==0` are the closure pair. F1 RESOLVED. (`per-instance-registry-pattern.md` should also extend its § "Cache discipline" to mandate BOTH asserts at Stage 3 promotion; minor DRAFT polish, no blocker.)

### F2 — A2 bitmap-bool migration discipline: GREEN

**Prior:** plan stipulated A2 but lacked: (1) bit-position determinism anchoring; (2) bitmap-overflow static_assert; (3) SET-discipline rebuild walker statement.

**Resolution check** (plan amendment § CRITICAL-2 + § DOD-F2):
- Bit-count corrected: **13 bits** (audit-verified via `ML_Headers/MlCfgFlagRegistry.hpp:52-64`; plan originally said 12)
- Bit position: **anchored via FOREACH_ML_CFG_FLAG enum ordinal at compile time** — each KIND_BOOL row carries its `MASK_ML_CFG_*` enum value as compile-time row metadata. Precedent named (`FOREACH_PER_ARM_FLAG` mask discipline at v5.15.5.A.2.b). Iteration order is NOT the source of bit positions.
- Stamp-emit-via-BITMAP_BIT carve-out: 4 bits emitted through `HANDLE_STAMP_EMIT_BITMAP_BIT` at `ML_Headers/StampBoundCfgRegistry.hpp:106-146` **DEFER to `.F.4d`** (wire-format framework two-source variant). `.F.4c.3` migrates the 9 non-stamp-emit bits.
- Bitmap-overflow assert: `static_assert(FOREACH_ML_CFG_FLAG_COUNT <= sizeof(ml_cfg_flags_runtime_bitmap) * 8)` co-located per `bitmap-overflow-protection-discipline.md`.
- SET-discipline at rebuild walker per `registry-bitmap-set-discipline.md` Shapes A/B explicitly named in DOD-F2.

F2 RESOLVED + STRENGTHENED. The corrected bit count (12→13) + stamp-emit carve-out + enum-ordinal anchor + co-located overflow assert all cleanly close the discipline.

### F3 — Per-core stamp Layer 5b array Surface G forward-compat: YELLOW-PARTIAL

**Prior:** plan didn't state forward-compat strategy for post-`.F.4c.3` ships extending STAMP_BOUND per-core fields (Layer 6 Surface G `has_*` flags vs re-emit-at-boot).

**Resolution check** (plan amendment § MED-1):
- New per-core stamp body field: `cfg_scope_split_version="5.15.5.F.4c.3"`
- v5.14 stamps without this field OR with older version = explicit ERROR (NOT silent has_*=0 default load). This is the v5.14-cross-version refusal mechanism.
- Forces operator retrain post-`.F.4c.3` (per Caramel's hard-break directive).

**Partial gap:** the amendment handles BACKWARD-incompat (v5.14 stamps explicitly refused). It does NOT explicitly state the FORWARD-compat path for future `.F.4d/.F.4e` ships adding NEW STAMP_BOUND per-core fields. The original F3 raised this — when `.F.4d` adds new STAMP_BOUND rows per-core, will the new `.F.4d` LOCKED_PER_CORE_STAMP_HASH change require a fresh re-stamp, or will Surface G `has_*` flag discipline tolerate legacy `.F.4c.3` stamps?

Likely outcome (consistent with `wire-format-byte-preservation-discipline.md` Layer 5b/6 at `.F.4d` planning): future ships re-stamp via boot-time emit; the `has_*=0` discipline is reserved for runtime data fields not stamped. But this should be explicitly stated in plan body § "If something goes wrong" — Layer 5b array reasoning for `.F.4c.3` → `.F.4d` transition.

**Verdict:** YELLOW — minor polish needed before coding (one-line clarification in plan § "If something goes wrong" or § E). Not blocking; can be folded into `.F.4d` plan body or addressed at Step 5 implementation.

### F4 — `.F.4d` composition pre-author: NOTED (deferred to `.F.4d` agenda)

**Prior:** plan should pre-author the dual-registry composition section in `metadata-bit-driven-derived-filter-framework.md` + `framework-composition-overview.md` so `.F.4d`'s audit gate isn't surprised.

**Resolution check:** the amendments do NOT explicitly add this to `.F.4c.3` scope. It IS implicit in DESIGN_SPECs § J updates-to-existing-specs (which mentions universal-cfg-field-registry-pattern.md + universal-registry-bitmap-dispatcher-pattern.md as "append-section updates"). But `metadata-bit-driven-derived-filter-framework.md` and `framework-composition-overview.md` are NOT in that update list.

**Per the task instructions:** F4 is "to be pre-authored at `.F.4d` planning" — explicitly deferred to `.F.4d` agenda. Acceptable; the gap is now a known item rather than an unknown.

**Verdict:** GREEN — F4 deferred to `.F.4d` agenda as documented in re-audit task scope. Recommend adding one bullet to `.F.4d` plan agenda when authored: "Update metadata-bit-driven-derived-filter-framework.md + framework-composition-overview.md to document dual-registry derived-filter composition."

### F5 — GUI cfg-mirror Option α: GREEN

**Prior:** plan didn't state GUI ↔ engine cfg cross-thread access model. Two options: α (GUI owns separate mirror; file is channel) or β (GUI shares engine's ControllerConfig; cache-line discipline load-bearing).

**Resolution check** (plan amendment § MED-4):
> "MED-4 — GUI cfg-mirror Option α: GUI owns separate `gui_engine_cfg` populated from file at boot; engine owns its own `ControllerConfig`. Communicate via file + reload-signal channel; NEVER pointer-share state across threads. Aligns with H3 (no mutex/condvar/sleep_for/rwlock) + thread-isolation going-forward rule (set 2026-05-14)."

F5 RESOLVED. Option α locked. Cross-references CLAUDE.local.md going-forward rule "GUI ↔ HP/SP thread isolation: NEVER share state directly" (set 2026-05-14). Aligns with H3 hard invariant. The false-sharing concern of F1 is no longer load-bearing for cross-thread access (each thread reads its own mirror); the alignas/sizeof asserts remain hygienic for sizeof determinism + `cores[c]` array element layout.

### F6 — `per-instance-registry-pattern.md` Audit detection section: YELLOW

**Resolution check:** grep'd the DRAFT for `## Audit detection` — section is NOT present. The DRAFT does have an explicit "Anti-patterns to avoid" section listing 5 forbidden shapes (global-default-plus-override / override-set-bitmaps / cross-instance-bleeding / parser-scope-confusion / hidden-inheritance) — those provide grep-detectable signatures BUT are not codified as a per-`/dod-audit`-consumption section per `pattern-codification-lifecycle.md` Stage 2 guidance.

**Verdict:** YELLOW — DRAFT v1.0 lacks explicit `## Audit detection` section; recommended fix is ~10-15 LOC addition before Stage 3 promotion at ship close. Per task instructions, this is acceptable as "ship-close polish" — fold into Step 8 (DESIGN_SPECs ship). Not blocking pre-coding.

### F7 — `cfg-scope-discipline.md` Audit detection grep signatures: YELLOW

**Resolution check:** grep'd the DRAFT — no `## Audit detection` section. The "Anti-patterns — FORBIDDEN at this discipline" section lists 4 anti-patterns with structural shapes but no explicit grep signatures.

Recommended signatures (from prior audit, for documentation):
- Sibling-family-name prefix appearing in BOTH `FOREACH_GLOBAL_CFG_FIELD` AND `FOREACH_PER_CORE_CFG_FIELD` (Anti-pattern 3)
- Cfg parser line key not in either registry → ERROR with `expected_scope_for_key(...)` migration hint (Anti-pattern 4 / parser-state-machine misroute)

**Verdict:** YELLOW — same as F6; fold into Step 8 ship-close polish. Not blocking.

---

## 2 NEW DESIGN_SPECs DRAFT-quality assessment

### `multi-action-registry-walker-family.md` — DRAFT-quality GREEN

- **Pattern shape concrete?** YES. `FOREACH_REGISTRY_ACTION(X)` declaration; `walk_registry_action<TargetStruct, Descriptor, N, ActionFn>` template; `GlobalActionTable<F, Action>` + `PerCoreActionTable<F, Action>` X-macro instantiations; call site shape shown for parse + render.
- **Composition documented?** YES. Cross-refs to per-instance-registry-pattern.md (axis), universal-cfg-field-registry-pattern.md (registry shape), universal-registry-bitmap-dispatcher-pattern.md (bitmap-dispatch primitive), type-trait-dispatch-via-tt-namespace.md (action body's typed dispatch), x-macro-registry-with-presence-dispatch.md (parent presence-dispatch pattern).
- **Future-axes catalog present?** YES. 5 axes named (per-symbol / per-strategy / per-horizon / per-regime / per-bandit-arm) with trigger + new-instantiation count formula.
- **Anti-patterns named?** YES. 4 anti-patterns explicit (walker-body duplication, per-action special-case in template, cross-registry name collision, action-enum value-vs-name confusion).
- **Reference-implementations placeholders?** YES. 4 pending entries marked for Stage 3 back-fill: CfgFieldRegistry.hpp / CfgFieldDispatch.hpp / GlobalActionTable / PerCoreActionTable / SettingsPanel.hpp.

**Verdict:** DRAFT v1.0 is GREEN-quality. Stage 3 ACTIVE promotion path clear at ship close.

### `cfg-section-parser-state-machine.md` — DRAFT-quality GREEN

- **State machine concrete?** YES. `ParseScope` enum + `ParseState` struct + main loop pseudocode + `parse_section_header()` recognizer + `emit_error_with_migration_hint()` + `expected_scope_for_key()` walker. Code-level concrete.
- **Error-handling discipline (migration hints) specified?** YES. Anti-pattern "Migration hints that don't reference the migration guide" + concrete `expected_scope_for_key` walker that returns the correct scope name. 5 error scenarios enumerated in § "First canonical application" (legacy at global / global-key inside section / `[core N]` out of bounds / duplicate section / unknown axis).
- **Anti-patterns named?** YES. 5 explicit (silent fallback / cross-registry try-both / lenient section header / state reset without bounds check / migration hint without doc ref).
- **Composition with other specs?** YES. Cross-refs to per-instance-registry-pattern.md (axis dispatch), multi-action-registry-walker-family.md (drives PARSE action), type-trait-dispatch-via-tt-namespace.md (per-row parse primitive), cfg-scope-discipline.md (prevents cross-registry collisions).
- **Future axes anticipated?** YES. 5 future section syntaxes catalogued ([symbol BTCUSDT] / [strategy MOMENTUM] / [horizon 1000] / [regime TRENDING] / [arm 0]).

**Verdict:** DRAFT v1.0 is GREEN-quality. Stage 3 ACTIVE promotion path clear at ship close.

---

## F6 cohort extension DOD-correctness (NEW; A2 to all 5 cfg-domain bitmaps)

**Plan amendment scope** (§ F6 extension ADOPTED): apply A2 pattern to ALL 5 cfg-domain bitmaps:
- `lifecycle_cfg_flags` (uint8_t; FOREACH_LIFECYCLE_CFG_FLAG)
- `gate_cfg_flags` (uint8_t; FOREACH_GATE_CFG_FLAG)
- `ml_cfg_flags` (uint16_t; FOREACH_ML_CFG_FLAG; 9 bits at .F.4c.3 + 4 at .F.4d)
- `risk_cfg_flags` (uint8_t; FOREACH_RISK_CFG_FLAG)
- `ops_cfg_flags` (uint8_t; FOREACH_OPS_CFG_FLAG)

Total: ~33 new KIND_BOOL rows in per-core registry (was 12; now 33 across 5 domains).

**DOD-correctness checks:**

1. **Each domain's bitmap-rebuild walker X-macro-generated?** YES per F2 / DOD-F2 statement. Plan says "rebuild walker writes `bitmap |= ((uint16_t)row_value) << enum_ordinal`" — that's the SAME structural shape applied per-domain. No per-domain manual walker code; the walker template instantiates per (registry, bitmap-domain) pair.

2. **SET-discipline applies uniformly across 5 domains?** YES. DOD-F2 explicitly invokes `registry-bitmap-set-discipline.md` Shapes A/B — single chokepoint at the rebuild walker; no manual-bit-set bypass paths. Same discipline for all 5 domains.

3. **Cache cost analysis:** 5 cfg-domain bitmaps × per-core × cores = 5 × ~2B × 16 = ~160B per cfg instance. Per `cache-layout-discipline-for-hot-side-structs.md` Rule 7 (size analysis): this fits within a single cache line per bitmap-domain cluster (5 × ~2B = ~10B per core; 16 cores = 160B = 3 cache lines). Cost negligible.

4. **Bitmap-overflow protection per-domain?** YES per DOD-F2. Co-located `static_assert(FOREACH_<DOMAIN>_CFG_FLAG_COUNT <= sizeof(<bitmap_storage>) * 8)` per registry domain. Replicates `.F.4c` overflow-discipline pattern for each new per-core bitmap.

**Verdict:** F6 cohort extension is DOD-correct. The uniform shape across 5 domains validates the universal-registry-bitmap-dispatcher-pattern.md composition + means future cfg-bitmap-domain additions become mechanical (1 X-macro registry + N KIND_BOOL rows + 1 overflow assert + 1 rebuild walker instantiation — all framework-driven).

---

## Class prevention verdicts (re-confirmed after amendments)

### Class 18 (Mirror-incomplete) — GREEN

The F1 reuse harvest (dual-registry walker template `RenderRegistryWalker<Target, Table, WORDS>`) prevents Class 18 by construction. ONE template consumed at Global + per-core tab call sites. No walker-body duplication. Same shape extends to all 5 actions (parse/save/render/stamp/drift) via multi-action-registry-walker-family.md DRAFT.

**Class 18 risk reduction:** N actions × M registries = N + M source items vs N × M with manual mirroring. At `.F.4c.3`: 5 actions × 2 registries = 7 source items vs 10 with manual; saves 3 walker bodies + closes the mirror class by-construction at this surface.

### Class 19 (Hardcoded enum names) — GREEN

Plan body § "Anti-patterns to avoid" explicitly states: *"INT_ENUM labels via X_GEN_LABEL extern from per-instance registry."* No hardcoded strategy/op-mode/regime enum names in gating logic. Categorical applicability axes (`applies_to_strategy_cat` / `applies_to_op_mode_cat` / `applies_to_regime_cat` / `applies_to_risk_cat`) carry over from `.F.4b` to both new registries unchanged.

### Class 21 (Parallel descriptors) — GREEN

The TWO registries (`FOREACH_GLOBAL_CFG_FIELD` + `FOREACH_PER_CORE_CFG_FIELD`) are **scope-DISJOINT by design** — they're NOT parallel descriptors of the same surface (which is Class 21's anti-shape). Each registry owns a distinct set of fields; cfg-scope-discipline.md Anti-pattern 3 ("Mixing scopes in the same field family") forbids cross-registry field-family bleeding.

Plan body § "Anti-patterns to avoid": *"Cross-registry name collision allowed only with explicit per-axis rationale."* Plus test fn 10 (`test_v5_15_5_F4c3_scope_discipline_no_field_in_both_registries`) provides the runtime check.

### Class 23 (Type-erased dispatch) — GREEN

`tt::cfg_<verb>_field<T>` primitives unchanged across the registry split — they take `T&` destination by reference; registry-agnostic. NEW consumers (per-core stamp emit, per-core drift check, dual-registry walker template) all use destination-by-reference. No `void* + offset` reintroduction.

Plan body § "Anti-patterns to avoid": *"Class 23 (Type-erased dispatch): 3-barrier prevention intact at every NEW tt:: consumer."* The 3-barrier discipline (static_assert + if constexpr + tt:: namespace boundary) is preserved at every new consumer site.

### Class 24 (Capability-cfg surface mismatch) — GREEN (STRUCTURAL CLOSURE)

This is THE class this ship closes structurally. The `cfg-scope-discipline.md` discipline forces the question "what scope does this field live at?" at field-add time; per-core is the default for trading-adjacent fields; the override-pattern that's been the recurring failure mode is eliminated.

**Combined closure mechanism:**
1. **cfg-scope-discipline.md** — every new trading field MUST live in per-core registry by discipline (not optional).
2. **per-instance-registry-pattern.md** — the framework that mechanically materializes the discipline (N authoritative instances; no override mechanism; no inheritance confusion).
3. **CLAUDE.local.md surface-alignment rule (set 2026-05-14)** — fires `/ml-audit` at sub-ship close for any ship touching ML capability (second line of defense for cfg-surface gaps).
4. **Plan amendment scope** — kill switches + max-drawdown moved to per-core (operator-refined 2026-05-15); even SAFETY-CRITICAL gating fields now flow through the same discipline.

Class 24 verdict: STRUCTURAL CLOSURE confirmed at multiple disciplines (cfg-scope-discipline + per-instance-registry + auto-flow framework + ml-audit second-line). Post-`.F.4c.3`, the recurring shape "added ML feature but forgot cfg surface" dies mechanically — there's literally no global-cfg-surface-without-per-core-tab path remaining for trading-adjacent code.

---

## Final DOD verdict: DOD-GREEN (ready to code)

**All 7 prior findings (F1–F7) addressed:**
- F1 → GREEN (resolution explicit; both asserts locked)
- F2 → GREEN-STRENGTHENED (13-bit count correction + enum-ordinal anchor + overflow assert + SET-discipline + stamp-emit carve-out all named)
- F3 → YELLOW (one-line forward-compat clarification recommended; non-blocking)
- F4 → GREEN (explicitly deferred to `.F.4d` agenda per task scope)
- F5 → GREEN (Option α locked + cross-refs to H3 + going-forward rule)
- F6 → YELLOW (Audit detection section deferred to ship-close polish; non-blocking)
- F7 → YELLOW (Audit detection section deferred to ship-close polish; non-blocking)

**2 NEW DESIGN_SPECs DRAFT-quality:**
- `multi-action-registry-walker-family.md` — DRAFT GREEN; pattern shape + composition + future-axes + anti-patterns + reference-impl placeholders all present
- `cfg-section-parser-state-machine.md` — DRAFT GREEN; state machine code-level concrete + error-handling discipline + 5 anti-patterns + composition with sister specs

**Class prevention (5 classes):** all GREEN. Class 24 STRUCTURAL CLOSURE at multi-discipline level (cfg-scope-discipline + per-instance-registry + multi-action-walker-family + cfg-section-parser-state-machine + auto-flow framework + ml-audit second-line).

**F6 cohort extension (A2 to 5 cfg-domain bitmaps):** DOD-correct. ~33 new KIND_BOOL rows; ~160B cache cost negligible; framework primitives compose unchanged across 5 domains.

**Pre-coding refinements:** NONE BLOCKING. The 3 YELLOW items (F3 forward-compat note + F6/F7 Audit detection sections) are all ship-close polish — fold into Step 5 (per-core stamp implementation) or Step 8 (DESIGN_SPECs ship) without blocking coding start at Step 0.

**Recommendation:** DOD-GREEN. Ready to code starting from Step 0.A (rollback anchor + baseline). The 3 YELLOW items are documented for in-ship polish; no substantial DOD redesign required.

The architectural shape is sound + composes correctly with framework library + structurally closes Class 24 + advances framework-discipline meta-principle (CLAUDE.md item 31). The amendments resolved every architectural-level concern from the prior audit; remaining items are documentation polish that doesn't change implementation shape.

---

**End of dod-audit RE-AUDIT report.**
