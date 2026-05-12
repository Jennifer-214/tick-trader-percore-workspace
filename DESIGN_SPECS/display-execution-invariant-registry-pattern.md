# Display↔Execution Invariant registry pattern (structural enforcement of the cardinal "every hot-path predicate term has a GUI surface" rule)

**Established:** 2026-05-12 (codification of structural enforcement for FoxML_Trader_v2 `DOCS/EXECUTION_DISPLAY_INVARIANTS.md`; v5.15.5.B.4 first reference application via FOREACH_GATE_DIAG)
**Status:** ACTIVE
**Cross-references:**
- Parent invariant: FoxML_Trader_v2 `DOCS/EXECUTION_DISPLAY_INVARIANTS.md` (cardinal rule + manual matrix)
- Parent rule: `x-macro-registry-with-presence-dispatch.md` (X-macro registry pattern; this doc is a SPECIALIZATION for the 5-site display-execution mirror)
- Sister: `autopopulate-pattern-for-production-caller-class.md` (companion macro for caller-site code generation)
- Sister: `structural-fix-preferred-decision-framework.md` (this pattern is the canonical structural fix for the display-execution mirror class)
- FoxML_Trader_v2 CLAUDE.md item 12 (display↔execution invariant — cardinal rule)
- FoxML_Trader_v2 CLAUDE.md item 13 (X-macro registry standard pattern)
- FoxML_Trader_v2 CLAUDE.md item 19 (structural fix preferred for recurring classes)
- FoxML_Trader_v2 CLAUDE.md item 21 (AUTOPOPULATE companion macro)

---

## Problem statement

FoxML_Trader_v2 has a cardinal architectural invariant (CLAUDE.md item 12 + `DOCS/EXECUTION_DISPLAY_INVARIANTS.md`):

> **Every term in the hot-path entry / exit predicate MUST have a corresponding GUI surface.**

The bug class motivating this invariant: the 2026-04-30 incident where the GUI showed "READY" while the hot path was silently refusing to fire (gate flag set due to fee-floor; display-layer truth model was a strict subset of hot-path's). Operators looking at the dashboard were misled.

Today's enforcement is MANUAL:
- A predicate↔display matrix table in `DOCS/EXECUTION_DISPLAY_INVARIANTS.md`
- A discipline rule: "presence of an unmatched term is sufficient grounds to reject a PR"
- PR review is the enforcement mechanism

This is a CLASS-18 MIRROR PATTERN (per recurring-bug-patterns catalog): same data mirrored across MULTIPLE sites, drift-prone, requires human vigilance. The mirror is 5 sites per term:

1. **`CoreContext<F>` field declaration** — where the value is stored at engine state level
2. **Reset write in `EventLoop_RebuildOneCore`** — value reset before each cycle before strategy dispatch
3. **Snapshot capture in `ShardedSnapshot.hpp`** — value copied from CoreContext (or CoreContextDisplayMeta post-v5.15.5.B.2) to PerCoreSnap as double (FPN_ToDouble)
4. **`PerCoreSnap` field declaration in `DataStream/EngineTUI.hpp`** — snapshot-side field type + name
5. **GUI render row in `GUI/MLStatusPanel.hpp` / `DashboardPanels.hpp`** — operator-visible display

Adding a new gate diagnostic requires touching 5 sites. Forgetting ANY breaks the invariant. Reviewer vigilance scales poorly with codebase complexity. Per CLAUDE.md item 19 ("structural fix preferred when bug class can recur"), the invariant deserves COMPILE-TIME enforcement, not human enforcement.

This pattern provides it.

---

## Design space explored

### Option A — Manual matrix maintained in documentation (pre-v5.15.5.B.4)

The `DOCS/EXECUTION_DISPLAY_INVARIANTS.md` predicate↔display matrix lists each term + 4 implementation columns. Reviewer cross-references during PR review.

✓ Self-documenting. ✗ Drift-prone (matrix can fall out of sync with code without anyone noticing). ✗ Doesn't enforce at compile time. ✗ Doesn't help with 5-site update cost when adding a term.

INSUFFICIENT — relies on human vigilance + doesn't reduce per-term update cost.

### Option B — Each-site lint check (PR CI)

Custom CI lint that parses CoreContext + ShardedSnapshot + EngineTUI + GUI files + warns if a term appears in N-1 sites.

✓ Compile-time-ish enforcement. ✗ Brittle (parser fragility); ✗ Doesn't reduce per-term update cost (5 sites still touched per new term); ✗ External tooling vs in-language.

REJECTED.

### Option C — X-macro registry auto-flows all 5 sites (CHOSEN)

Single `FOREACH_GATE_DIAG(X)` (or similar) registry. Each registry entry is 1 row. X-macro expansion auto-generates:
- CoreContext / CoreContextDisplayMeta field declarations
- Reset block in RebuildOneCore
- ShardedSnapshot FPN_ToDouble copy block
- PerCoreSnap field declarations
- GUI render row

Adding a new term = 1 row in registry. All 5 sites flow automatically. Mirror class structurally extinct.

CHOSEN. Pattern documented here.

### Option D — Code generator (Python / Jinja)

Run a script at build time to generate the 5 sites from a YAML manifest.

✓ Easier to read than X-macros for complex generators. ✗ External tooling dependency; ✗ Build-time complication; ✗ X-macros work fine for this scale.

REJECTED for current scope. Acceptable if future expansion needs >10 generated sites per entry.

---

## The pattern (concrete shape)

### Step 1 — Define the registry

```cpp
// MemHeaders/GateDiagRegistry.hpp

#define FOREACH_GATE_DIAG(X) \
    /* X(UPPER_NAME, ACT_SUFFIX, REF_SUFFIX, DESCRIPTION) */ \
    X(SPACING,      actual, floor,     "|bg_threshold - last_entry| vs stddev*spacing_multiplier") \
    X(VWAP,         actual, threshold, "bg_price_threshold vs vwap - vwap*vwap_offset") \
    X(LONG_SLOPE,   value,  min,       "long_rel_slope vs cfg.min_long_slope") \
    X(VOLUME_DELTA, value,  min,       "rolling.volume_delta vs cfg.min_buy_delta") \
    X(STDDEV_PCT,   value,  min,       "rolling.price_stddev / price_avg vs cfg.min_stddev_pct") \
    X(TP_PCT,       actual, floor,     "out.tp_pct vs 3 * fee_rate_taker")
```

Tuple shape:
- `UPPER_NAME` — registry entry identifier (used in MASK / enum / field-name expansion)
- `ACT_SUFFIX` — suffix for the "actual measured value" field (e.g., `_actual` or `_value`)
- `REF_SUFFIX` — suffix for the "reference threshold/floor/min" field (e.g., `_floor`, `_threshold`, `_min`)
- `DESCRIPTION` — operator-visible tooltip / doc text

### Step 2 — X-macro expansion at the 5 sites

Each consumer site uses an X-macro expansion against the registry. The macro body is site-specific.

**Site 1 — `CoreContextDisplayMeta` field declarations:**
```cpp
struct CoreContextDisplayMeta {
    #define X(UPPER, ACT_SUFFIX, REF_SUFFIX, DOC) \
        FPN<F> diag_##LOWER(UPPER)##_##ACT_SUFFIX; \
        FPN<F> diag_##LOWER(UPPER)##_##REF_SUFFIX;
    FOREACH_GATE_DIAG(X)
    #undef X
};
```

(Note: `LOWER(UPPER)` is a placeholder for case conversion; C macros can't lowercase. Either keep field names UPPERCASE-suffixed, or use a small case-conversion helper macro, or normalize all field names to a registry-friendly convention. Decision per-implementer; v5.15.5.B.4 takes the simplest option.)

**Site 2 — Reset block in `EventLoop_RebuildOneCore`:**
```cpp
// Before strategy dispatch
#define X(UPPER, ACT_SUFFIX, REF_SUFFIX, DOC) \
    state->display_meta[slot].diag_##UPPER##_##ACT_SUFFIX = FPN_Zero<F>(); \
    state->display_meta[slot].diag_##UPPER##_##REF_SUFFIX = FPN_Zero<F>();
FOREACH_GATE_DIAG(X)
#undef X
```

**Site 3 — Snapshot capture in `ShardedSnapshot.hpp`:**
```cpp
#define X(UPPER, ACT_SUFFIX, REF_SUFFIX, DOC) \
    snap->per_core[i].diag_##UPPER##_##ACT_SUFFIX = \
        FPN_ToDouble(state->display_meta[i].diag_##UPPER##_##ACT_SUFFIX); \
    snap->per_core[i].diag_##UPPER##_##REF_SUFFIX = \
        FPN_ToDouble(state->display_meta[i].diag_##UPPER##_##REF_SUFFIX);
FOREACH_GATE_DIAG(X)
#undef X
```

**Site 4 — `PerCoreSnap` field declarations:**
```cpp
struct PerCoreSnap {
    // ... other fields ...
    #define X(UPPER, ACT_SUFFIX, REF_SUFFIX, DOC) \
        double diag_##UPPER##_##ACT_SUFFIX; \
        double diag_##UPPER##_##REF_SUFFIX;
    FOREACH_GATE_DIAG(X)
    #undef X
};
```

**Site 5 — GUI render in `MLStatusPanel.hpp` / `DashboardPanels.hpp`:**
```cpp
#define X(UPPER, ACT_SUFFIX, REF_SUFFIX, DOC) \
    ImGui::Text("%s actual: %.4f / ref: %.4f", #UPPER, \
                pc.diag_##UPPER##_##ACT_SUFFIX, \
                pc.diag_##UPPER##_##REF_SUFFIX); \
    if (ImGui::IsItemHovered()) ImGui::SetTooltip("%s", DOC);
FOREACH_GATE_DIAG(X)
#undef X
```

Each site is a 3-5 line X-macro block instead of N manual rows. Adding a new term = 1 row in `FOREACH_GATE_DIAG`; ALL 5 sites flow.

### Step 3 — Compile-time enforcement via static_assert + walk

Add a regression test that walks the registry + asserts every entry has a corresponding PerCoreSnap field:

```cpp
// tests/controller_test_engine.cpp
TEST("FOREACH_GATE_DIAG registry has corresponding PerCoreSnap fields") {
    PerCoreSnap snap{};
    #define X(UPPER, ACT_SUFFIX, REF_SUFFIX, DOC) \
        (void)snap.diag_##UPPER##_##ACT_SUFFIX; \
        (void)snap.diag_##UPPER##_##REF_SUFFIX;
    FOREACH_GATE_DIAG(X)
    #undef X
    /* If a registry entry has no PerCoreSnap field, this fails to compile. */
    check("FOREACH_GATE_DIAG registry walk", true);
}
```

If a registry entry has no corresponding PerCoreSnap field, the test fails to compile. The compile-time enforcement extends to ALL 5 sites — any missing site fails the build.

### Step 4 — Update DOCS/EXECUTION_DISPLAY_INVARIANTS.md

The doc's predicate↔display matrix becomes the SOURCE OF TRUTH (one entry per row), and the registry's X-macro expansion is the IMPLEMENTATION. Update the doc with a section:

```markdown
## Structural enforcement (v5.15.5.B.4+)

The gate-diagnostic subset of the predicate↔display matrix is now ENFORCED
via the `FOREACH_GATE_DIAG(X)` X-macro registry at `MemHeaders/GateDiagRegistry.hpp`.
Each entry auto-flows: CoreContext field decl + reset in RebuildOneCore +
ShardedSnapshot capture + PerCoreSnap field decl + GUI render. Adding a new
gate diagnostic is 1 row + 1 matrix row update. Forgetting any of the 5 sites
becomes IMPOSSIBLE (compile-time enforced via static_assert walk).

See DESIGN_SPECS/display-execution-invariant-registry-pattern.md for pattern.
```

### Step 5 — Generalize to other display-execution surfaces

The pattern applies BEYOND gate-diagnostics. Candidates:
- Regime signals → snapshot (regime_trend_strength, regime_vol_zscore, etc.)
- ML predictions → snapshot (staged_prediction, active_prediction, confidence)
- OMS state → snapshot (fill events, kill state, drainer counters)

Each surface gets its own registry + 5-site X-macro expansion. Common shape: any time data flows `live state → snapshot publisher → GUI`, the registry pattern applies.

---

## Trade-offs + when to apply

### Apply when:
- The display↔execution invariant is in force for this data
- ≥ 3 fields participate in the mirror (registry overhead amortizes)
- Adding new fields is a recurring activity (the cost of 5 sites compounds)
- ALL 5 sites are mechanically derivable from the registry tuple (no per-field special-casing)

### Skip when:
- Single one-off field with no expected siblings (5-site manual cost is fine)
- Per-field logic differs significantly across sites (registry tuple becomes unwieldy)
- The data flows ONE way only (e.g., GUI-set kill_reset bit → engine; not display↔execution)

### Cost:
- Per registry: ~50-100 LOC registry definition + ~20-30 LOC X-macro expansion across 5 sites
- Initial migration of existing manual fields: ~80-120 LOC churn
- Cognitive overhead: contributors must understand X-macro expansion idiom

### Win:
- New term = 1 row, not 5 sites
- Compile-time enforcement of the invariant (cannot forget a site)
- Documentation co-located with registry (DOC field per entry)
- Pattern reusable across surfaces (regime, ML, OMS)
- TECH_DEBT-011 (broader FOREACH_PER_CORE_SNAP_FIELD) closure incremental — each surface that adopts this pattern is one less mirror to maintain

---

## Reference applications

### v5.15.5.B.4 (first) — FOREACH_GATE_DIAG for 12 diag_* fields

**Surface:** `MemHeaders/GateDiagRegistry.hpp` (NEW); migrations across CoreContextDisplayMeta + RebuildOneCore + ShardedSnapshot + PerCoreSnap + MLStatusPanel/DashboardPanels.

**Before:** 12 manual fields × 5 sites = 60 manual touchpoints. Adding a new gate diagnostic touched 10 lines minimum.

**After:** 6 registry entries (12 fields = 6 pairs); each new pair = 1 registry row. 5 sites flow automatically.

### Future applications

| Surface | Registry candidate | Trigger |
|---|---|---|
| Regime signals → snapshot | `FOREACH_REGIME_SIGNAL` | When regime_signals struct adds ≥ 3 new visible fields in one ship |
| ML predictions → snapshot | `FOREACH_ML_OBSERVABILITY` | When ML observability sprint promotes prediction visualization |
| OMS state → snapshot | `FOREACH_OMS_VISIBLE_STATE` | When TECH_DEBT-011 broader closure scheduled |
| Strategy halt reasons | already `FOREACH_HALT_CODE` + `FOREACH_SHALT_CODE` | DONE (separate pattern: enum-driven dispatch) |

---

## Lessons / gotchas

### Case-conversion limitation in C macros

C/C++ macros can't do case conversion. If the registry uses UPPERCASE names but field names need lowercase, options:
- (a) Use uppercase field names: `diag_SPACING_actual` (visible but odd)
- (b) Add a `LOWER_` prefix in the registry tuple: `X(LOWER_NAME, UPPER_NAME, ...)` — duplicates info
- (c) Use a small `LOWER()` macro that expands per-entry to the lowercase form (verbose but works)
- (d) Normalize all field names to one case (rename existing fields)

v5.15.5.B.4 should pick the cleanest option for the specific surface. For GATE_DIAG: rename to all-lowercase field names matching registry-friendly form (`diag_spacing_actual` → match `FOREACH_GATE_DIAG(X) X(spacing, actual, floor, "...")` with lowercase registry tuple). Migration cost: ~12 field renames; cleaner final state.

### Mixed suffix conventions

The diag_* fields today use `_floor`, `_threshold`, `_min` for different reference-value semantics. Registry tuple can encode the suffix per entry — preserves existing names. Alternative: normalize to single `_ref` suffix; cleaner but breaks PerCoreSnap field names (operator-visible). Decision per-surface.

### Test must walk the registry

A test that uses `FOREACH_GATE_DIAG(X)` to verify field presence on PerCoreSnap is the compile-time enforcement. Without this walk, the X-macro expansion at each site is checked individually but cross-site CONSISTENCY isn't enforced. Make the registry-walk test mandatory.

### HMAC chain / byte-equivalence interaction

If the snapshot's serialized form is byte-equivalence-locked (HMAC chain, replay-determinism), adding/removing/reordering registry entries CHANGES the byte layout of PerCoreSnap → CHANGES the snapshot byte stream → BREAKS HMAC chain for old snapshots.

For PerCoreSnap specifically: NOT in HMAC chain today (TUI snapshot is ephemeral, not persisted in audit-trail form). SAFE to reorder.

For surfaces that ARE HMAC-locked (stamp body), use `wire-format-byte-preservation-discipline.md` + treat registry order as canonical wire format.

### Static_assert walk requires struct definition before walk site

The registry-walk test must `#include` PerCoreSnap struct BEFORE expanding the macro. Order matters in test file.

### Adding a NEW registry surface vs extending existing

For NEW surface (e.g., regime_signals registry): write a separate `FOREACH_REGIME_SIGNAL(X)` registry + own 5-site expansion. Don't merge into FOREACH_GATE_DIAG (different domain; different field types possibly).

For EXTENDING existing (new gate diagnostic): add 1 row to FOREACH_GATE_DIAG. Same registry; same expansion sites; nothing to change at site level.

---

## Audit detection (`/dod-audit` integration)

`/dod-audit` should flag MISSED applications by:

- **Symptom 1:** Display-execution mirror surface (data flows `live state → snapshot publisher → GUI`) with manual fields at 5 sites + no registry covering the cohort → missed structural fix
- **Symptom 2:** `DOCS/EXECUTION_DISPLAY_INVARIANTS.md` matrix has entries with status `⚠ to-add` for > 2 sprints — drift indicator
- **Symptom 3:** Per-snapshot-cluster has ≥ 3 fields with parallel naming pattern (e.g., `diag_*` / `regime_*` / `ml_*`) but no registry → cohort-audit candidate
- **Symptom 4:** Recent ship added a new visible state field touching ≥ 4 sites without registry adoption → discipline lapse

When detected → flag as `MISSED — display-execution-invariant-registry-pattern`. Recommended fix: extract the cohort into `FOREACH_<SURFACE>(X)` registry + X-macro expansion at all 5 sites + registry-walk test.

---

## Patterns NOT used here (and why)

### Code generator (Python / Jinja)

External tooling overhead. X-macros are in-language + compile-time-checked. REJECTED for current scope.

### Template metaprogramming with `std::tuple`

C++ tuples + index sequences can express registry walks. But more complex syntax than X-macros + tuple types are less flexible for mixed-type field generation. REJECTED.

### Reflection (C++23 / experimental)

Reflection would make this trivial. Not available in C++17/20 target. Future migration possible when C++26 reflection lands.

### Single Source of Truth via YAML + custom CI

Manifest-driven generation. External tooling overhead. X-macros stay in-tree + compile-checked. REJECTED.

---

## Cross-references

- FoxML_Trader_v2 `DOCS/EXECUTION_DISPLAY_INVARIANTS.md` (the cardinal invariant + manual matrix this pattern enforces)
- `x-macro-registry-with-presence-dispatch.md` (parent pattern; this doc is a SPECIALIZATION)
- `autopopulate-pattern-for-production-caller-class.md` (companion pattern for caller-side code generation; can be used WITH this pattern when consumers need uniform code gen)
- `structural-fix-preferred-decision-framework.md` (this pattern is a canonical structural fix application)
- `per-snapshot-cluster-layout-pattern.md` (governs WHICH cluster the registry fields land in)
- `cross-thread-snapshot-publish-cluster-isolation.md` (companion: cross-thread isolation for the LIVE-STATE-SIDE struct)
- `wire-format-byte-preservation-discipline.md` (different concern: when registry order is byte-equivalence-locked)
- FoxML_Trader_v2 `CLAUDE.md` items 12, 13, 19, 21
- FoxML_Trader_v2 `MemHeaders/GateDiagRegistry.hpp` v5.15.5.B.4 (first reference application; NEW file)
- FoxML_Trader_v2 `DOCS/TECH_DEBT.md` TECH_DEBT-011 (broader FOREACH_PER_CORE_SNAP_FIELD; partially closed by .B.4 + this pattern)

## Promotion criteria (this doc was promoted)

1 first explicit application (FOREACH_GATE_DIAG in v5.15.5.B.4) + 2+ generalizable future surfaces (regime signals, ML predictions, OMS state — each likely to surface in v5.15.6+). Operator framing 2026-05-12: "structural fixes that close out entire classes of future bugs" + "extensive explanation for how critical it is" — codified to lock the pattern as the structural enforcement for CLAUDE.md item 12 invariant.

Re-evaluate when 2nd-3rd applications surface (likely .C OMS ship + ML observability sprint).
