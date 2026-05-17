# /trace-deps report — `2026-05-16-v5.15.5.F.4d.1.A-framework-infra.md` (+ sidecar) — 2026-05-16

**Plan body version:** v1.2
**Sidecar version:** v1.1
**HEAD audited:** `545b0879948a0893f806dc6afe7992968acd57e3` = tag `v5.15.5.F.4d`
**Audit scope:** dependency-chain verification per `/trace-deps` SKILL.md (Steps 1-7)
**Skill loaded:** structural-fix-preferred-decision-framework.md + meta-registry-pattern-for-codebase-registry-discipline.md + metadata-bit-driven-derived-filter-framework.md + wire-format-byte-preservation-discipline.md

---

## Summary

| Focus area | Verdict |
|---|---|
| 1. File:line refs verification (HEAD anchors) | **GREEN** (all 11 anchor refs PASS) |
| 2. Function / macro / symbol existence (.A surface) | **YELLOW** (10/12 PASS; 1 GAP `FOREACH_REGISTRY` tuple shape drift; 1 GAP CI Check naming) |
| 3. Predecessor wiring (tag + foundation) | **GREEN** (pre-v5.15.5.F.4d + v5.15.5.F.4d tags PASS; FOREACH_BANDIT_SIDE enrolled at MetaRegistry.hpp:58) |
| 4. Test count baseline | **GREEN** (3174/0 confirmed via `./build/controller_test`) |
| 5. Macro name collision check | **GREEN** (no collisions at HEAD; sole references in forward-looking Version.hpp + MetaRegistry.hpp comments) |

**Overall verdict: YELLOW** — Plan body + sidecar are 90% accurate, but **3 cumulative drifts in one row** (sidecar § Step 4 FOREACH_REGISTRY row) will fail `python3 tools/check_meta_registry.py` at Step 4 build-verify. Mechanical fix; no design change needed. NOT a RED — all referenced symbols exist; just the FOREACH_REGISTRY enrollment row example is structurally wrong against the actual tuple shape.

---

## Top findings (blocking → cosmetic)

### Finding A — RED-on-coding-time: FOREACH_REGISTRY row tuple shape drift (sidecar `examples.md:454-457`)

**Plan claim** (sidecar § Step 4):
```cpp
X(DERIVED_FILTER,
  "CoreFrameworks/DerivedFilterRoster.hpp", 1, ROOT,
  "metadata-bit-driven-derived-filter-framework.md", Class_21, MIXED,
  "...")
```

**Actual** (`MetaRegistry.hpp:35-105` + `tools/check_meta_registry.py:100-103` regex):
- Tuple shape is 4-col: `X(registry_name, LEVEL, PARENT, "description")` — NOT 8-col.
- `registry_name` MUST be the actual `FOREACH_<NAME>(X)` macro name, i.e., `FOREACH_DERIVED_FILTER` not `DERIVED_FILTER`. Otherwise Check 2 fails: "FOREACH_REGISTRY rows have no matching #define in codebase".
- PARENT for Level-1 rows uses `FOREACH_REGISTRY` (the symbol; see all 62 Level-1 rows at MetaRegistry.hpp:39-105), NOT `ROOT`. (`ROOT_NONE` is the sentinel for Level-0 only — defined at MetaRegistry.hpp:33.)
- Plan body line 421 + 533: also says "DERIVED_FILTER PARENT=ROOT" — same naming drift.

**Correct row** (matches existing convention):
```cpp
X(FOREACH_DERIVED_FILTER, 1, FOREACH_REGISTRY, "Manages cfg-derived filters; Stage 3 ACTIVE first canonical at .F.4d.1.A; wire-format byte-preservation via structural invariant tests")
```

**Blast radius:** Step 4 build-verify will fail Check 2 + Check 3 of `python3 tools/check_meta_registry.py` until the row is fixed. Mechanical 1-line correction; no design impact.

### Finding B — YELLOW: CI Check naming aspirational, not actual tooling

Plan body lines 421, 532, 533, 564 + sidecar lines 464, 465 reference `test_meta_registry_coverage` + `test_meta_registry_topology` as "CI Checks". These names appear in CLAUDE.md H15/H19 + DESIGN_PHILOSOPHY but **DO NOT exist as actual test binaries / test names** at HEAD. The actual CI mechanism is the Python script `tools/check_meta_registry.py` (3 checks: "Check 1 PASS / Check 2 PASS / Check 3 PASS").

**Resolution path:**
- Option 1 (recommended): Add the `test_meta_registry_coverage` + `test_meta_registry_topology` C++ test sections inside `controller_test.cpp` at Step 4 — wrap shell-out to `python3 tools/check_meta_registry.py` OR re-implement the 3 checks as C++ assertions over `FOREACH_REGISTRY` X-macro expansion (compile-time discipline preferred per v1.2 Step 5b rationale).
- Option 2: Update plan body language to say "shell out to `python3 tools/check_meta_registry.py` Check 1+2+3 PASS" instead of `test_meta_registry_coverage / _topology`.

**Note:** v1.2 Step 5b added compile-time H16 static_assert directly in `CfgFieldRegistry.hpp` — this is the right pattern for these H15/H19 checks too (compile-time over Python CI script). Consider adding compile-time static_asserts that enforce the H15/H19 invariants alongside H16 in the same Step 5b.

### Finding C — GREEN with note: `tt::cfg_emit_synthetic_field<T>` correctly deferred to `.B`

Plan body line 32-33 + lines 117-118 properly defer the `.B` helper. Sister functions `tt::cfg_parse_field<T>` / `tt::cfg_save_field<T>` / `tt::cfg_render_field<T>` exist at HEAD (`FixedPoint/FixedPointN.hpp:37-58`, `GUI/SettingsPanel.hpp:40-66`, `CoreFrameworks/ControllerConfig.hpp:2119+2137`) — `tt::` namespace exists; pattern is canonical. `.A` correctly emits `<name>=stub\n` placeholder (sidecar lines 167-172).

### Finding D — GREEN: All 11 file:line anchor refs PASS at HEAD

| Anchor | Expected | Actual at HEAD | Verdict |
|---|---|---|---|
| CfgFieldRegistry.hpp:149 STAMP_BOUND_CFG_DERIVED bit 13 | `1u << 13` | Line 149: `STAMP_BOUND_CFG_DERIVED = 1u << 13` | PASS |
| CfgFieldRegistry.hpp:170-174 header layout | kind/lives_in_struct/metadata_flags/_reserved/field_idx | Lines 170-174 match | PASS |
| CfgFieldRegistry.hpp:212 bitmap-overflow static_assert | `WARN_ON_CLAMP < (1u << 16)` | Line 211-212 match | PASS |
| CfgFieldRegistry.hpp:890+895 FIELD_IDX_*_END sentinels | walker bounds | Lines 890, 895 match | PASS |
| CfgFieldRegistry.hpp:947+951 g_*_cfg_field_descriptors[] | walker target arrays | Lines 947, 951 match | PASS |
| CfgFieldRegistry.hpp:959-962 descriptor array size guard | static_assert precedent | Lines 959-962 match | PASS |
| MlCfgFlagRegistry.hpp:52+ FOREACH_ML_CFG_FLAG 12 rows | 5-arg sig | Lines 53-64 = 12 rows; sig `(NAME, legacy_field, display_label, section, doc)` = 5 args | PASS |
| MlCfgFlagRegistry.hpp:70 X_GEN_ML_CFG_BIT | consumer macro | Line 70 match | PASS |
| MlCfgFlagRegistry.hpp:82-83 X_GEN_ML_CFG_MASK | consumer macro | Lines 82-84 (actual span 82-85) | PASS |
| MlCfgFlagRegistry.hpp:92-103 ML_CFG_FLAG_AUTOPOPULATE_FROM_SEPTUPLE | hand-written, not migrated | Lines 92-103 match | PASS |
| ModelInference.hpp:1697 locale-pin precedent | `uselocale(newlocale(LC_NUMERIC_MASK, "C", (locale_t)0))` | Line 1697 match | PASS |

### Finding E — GREEN: MetadataFlag enum bits — all 12 EXEMPT_FROM_DERIVED_FILTER names + STAMP_BOUND_CFG_DERIVED exist at HEAD

Verified at `CfgFieldRegistry.hpp:131-149`. No name drift; H16 static_assert in v1.2 Step 5b will compile cleanly. `CfgFieldDescriptor` is in global namespace; `CfgFieldDescriptor::RESTART_REQUIRED` access pattern works.

### Finding F — GREEN: STAMP_HAS + BITMAP_IS_SET + BITMAP_ANY API exists

- `STAMP_HAS` at `ML_Headers/StampBoundModelConstRegistry.hpp:617`
- `BITMAP_IS_SET` at `MemHeaders/BitmapMacros.hpp:78`
- `BITMAP_ANY` at `MemHeaders/BitmapMacros.hpp:95`

Sidecar invariant runner uses `memchr` for I3 (no decimal `,` check) — standard library, no new API needed.

### Finding G — GREEN: Predecessor wiring + baseline test count

- `git rev-parse HEAD` = `545b0879948a0893f806dc6afe7992968acd57e3` ✓ matches `.F.4d` ship close claim
- `git tag --list`: `v5.15.5.F.4d` + `pre-v5.15.5.F.4d` both exist (GPG-signed)
- `./build/controller_test`: **3174 passed, 0 failed** ✓ matches baseline claim
- `python3 tools/check_meta_registry.py`: Check 1+2+3 PASS, 63 macros / 63 enrolled ✓ matches CLAUDE.local.md
- `FOREACH_BANDIT_SIDE` enrolled at `MetaRegistry.hpp:58` (first H15 canonical) ✓ matches Thread A foundation claim

---

## Mirror data-flow audit (Step 6) — NOT TRIGGERED

Plan body does NOT contain "mirror" / "duplicate this for X" / "parallel to X" keywords. No mirror-style dependency check needed. The framework macros DO compose (Variant 2 reuses Variant 1's GUI walker via macro chaining at sidecar:147) — but that's structural composition, NOT mirror duplication.

---

## Call-sequence audit — minor concern

Sidecar § Step 2's `NAME##_emit_canonical_body` lambda invokes:
1. `newlocale(LC_NUMERIC_MASK, "C", (locale_t)0)` — present at `ModelInference.hpp:1697` precedent
2. `uselocale(pinned)` — same precedent
3. `snprintf(c->buf + *c->pos, c->cap - *c->pos, "%s=stub\n", d.cfg_field_name)` — standard library
4. `NAME##_walk_filtered_rows(g_per_core_cfg_field_descriptors, FIELD_IDX_PER_CORE_END, +emit_row, &ctx)` — macro-generated callee
5. `NAME##_walk_filtered_rows(g_global_cfg_field_descriptors, FIELD_IDX_GLOBAL_END, +emit_row, &ctx)` — macro-generated callee
6. `freelocale(pinned)` — paired with newlocale

All transitive callees PASS. The `freelocale(pinned)` call (sidecar:180) is correctly paired with line 152's `newlocale` — note `ModelInference.hpp:1697` does NOT call `freelocale` (the locale leaks intentionally for the lifetime of the proc); the sidecar's approach (free on every body emit) is structurally cleaner but consider whether repeated `newlocale` + `freelocale` at every invocation has measurable cost. (Tests call emit_canonical_body many times; if hot, cache the locale handle once.) MINOR — not blocking.

---

## Recommendations (in priority order)

1. **Fix sidecar § Step 4 FOREACH_REGISTRY row** to use the correct 4-col tuple + `FOREACH_DERIVED_FILTER` registry name + `FOREACH_REGISTRY` as PARENT. Update plan body lines 421, 532-533, 564 similarly to drop "ROOT" → "FOREACH_REGISTRY" and "DERIVED_FILTER" → "FOREACH_DERIVED_FILTER".
2. **Resolve CI Check naming** — either add compile-time static_asserts alongside H16 (preferred, per v1.2 rationale "compile-time mechanism preferred when source data X-macro-driven") OR update plan body language to "shell out to `python3 tools/check_meta_registry.py` Check 1+2+3 PASS".
3. **Consider locale handle caching** in emit_canonical_body (MINOR; only if test invocation count is high).
4. **No code changes needed** for symbol existence — every claimed function / macro / API surface exists at HEAD per verified findings D-G.

---

## Verdict: YELLOW (proceed with mechanical fixes)

Plan body + sidecar are well-grounded against HEAD. The single drift cluster (FOREACH_REGISTRY row shape in sidecar § Step 4) is a mechanical 1-line correction. CI Check naming is the second non-blocking issue. All file:line refs PASS. All MetadataFlag bit names exist. All sister `tt::` dispatch primitives exist. Test baseline confirmed. Predecessor wiring confirmed. The `.A` ship is ready to start once the FOREACH_REGISTRY row example is corrected (1 line) and the CI Check naming question is resolved (operator choice: compile-time static_assert OR shell-out reword).
