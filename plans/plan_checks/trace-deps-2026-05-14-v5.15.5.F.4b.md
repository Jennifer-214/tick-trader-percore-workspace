# /trace-deps report — v5.15.5.F.4b — 2026-05-14

Plan: `plans/v5.15-live-readiness/subplans/2026-05-13-v5.15.5.F.4b-foreach-cfg-field-registry-implementation.md`
Engine HEAD: `f72caef` (v5.15.5.F.3)
Audit scope: dependency-chain map + downstream-impact for new plan code

## Summary

- NEW callables analyzed: 6 (tt::cfg_parse_field<K> ×N, tt::cfg_save_field<K> ×N, tt::cfg_render_field<K> ×N, cfg_field_offset, EMIT_PER_CORE_DECL, FOREACH_CFG_FIELD)
- NEW structs analyzed: 3 (CfgFieldDescriptor, StrategyCategory enum, OpModeCategory enum)
- Callees PASS: 14
- BLOCKER GAPS: 3 (BL-1, BL-2, BL-3) — plan must update before coding
- DRIFT findings: 3 (DR-1, DR-2, DR-3) — plan needs adapter or scope clarification
- DOCUMENTED-RISK: 2 (DOC-1, DOC-2) — captured for awareness

Verdict: **RED** — three blocking gaps. Plan needs amendment at Step 2 (offset semantics for FPN), Step 5 (save model mismatch), and stretch goal feasibility audit before .F.4b coding begins.

---

## BLOCKER FINDINGS

### BL-1: Offsetof-into-FPN<F> incompatible with the plan's `*reinterpret_cast<double*>` design

**Where:** plan Step 2 "Option A" (recommended); design spec
`universal-cfg-field-registry-pattern.md:196`:

```cpp
*reinterpret_cast<double*>(reinterpret_cast<char*>(dst) + cfg_field_offset(desc.cfg_field_name)) = v;
```

**Problem:** the ~40 KIND_DOUBLE/_PCT fields in scope are NOT `double` in the
struct. They are `FPN<F>` (a 4096-bit fixed-point struct, F=64).

Evidence (`CoreFrameworks/ControllerConfig.hpp:280-348`):

```cpp
template <unsigned F> struct ControllerConfig {
  ...
  FPN<F> r2_threshold;
  FPN<F> take_profit_pct;
  FPN<F> ml_buy_threshold;     // line 729
  FPN<F> bandit_blend_ratio;   // line 768
  ...
};
```

The existing parser explicitly converts:

```cpp
#define CFG_PARSE_FPN(name) \
  if (strcmp(key, #name) == 0) { cfg.name = FPN_FromDouble<F>(atof(val)); continue; }
```

If `tt::cfg_parse_field<KIND_DOUBLE>` writes a raw `double` at the offset, it
will OVERWRITE the first 8 bytes of an FPN<F> object — corrupt the
mantissa words (FPN is a multi-word integer; F=64 → 64 64-bit words).
Bytewise read-back via `FPN_ToDouble<F>(cfg.X)` produces garbage. Silent corruption
because everything compiles + no runtime crash; backtest determinism breaks
(at best) or trades go off random reconstructed FPN values (worst).

Compounding: many of the ~40 fields are KIND_DOUBLE_PCT. Existing parser
does `FPN_FromDouble<F>(atof(val) / 100.0)` (CFG_PARSE_PCT, line 1885). Plan must
preserve the /100.0 divide-on-parse + *100 on save semantics, AND the FPN
conversion. The `_PCT` Kind already handles the divide if dispatched
correctly — but only if the storage-write uses `FPN_FromDouble<F>`,
NOT `reinterpret_cast<double*>`.

**Required plan amendment:**
1. **Storage discriminator per Kind.** `cfg_parse_field<KIND_DOUBLE>` must
   detect that the destination type is `FPN<F>` (which is the case for
   ~38 of ~40 entries). Two options:
   - **Option A1**: introduce `KIND_FPN_FROM_DOUBLE` + `KIND_FPN_FROM_DOUBLE_PCT`
     as separate Kinds; existing KIND_DOUBLE stays for the ~2 truly-double
     fields (e.g., `ensemble_bandit_eta` parsed as raw atof, line 2353-2360).
   - **Option A2**: keep KIND_DOUBLE + KIND_DOUBLE_PCT, but route storage
     via a templated helper that knows the target type at the X-macro
     expansion site (extends CLAUDE.md item 23 pattern; tt::cfg_write_field<T>
     with `if constexpr (is_FPN<T>) FPN_FromDouble<F> else direct`).
     Requires type-token in registry tuple OR per-field offset-table that
     also carries the target-type discriminator.
2. **Option A2 is preferred** for keeping the registry "type-erased at write
   site" while preserving structural fix discipline. Pattern: `tt::stamp_parse_field<T>`
   (`ML_Headers/StampBoundModelConstRegistry.hpp:102-124`) is the precedent —
   already handles array vs scalar vs unsigned via `if constexpr`. Extend
   with `is_FPN_v<T>` branch. The challenge: the registry doesn't
   currently know the destination TYPE (only the Kind). To make this work,
   either:
   (a) the X-macro expansion captures `decltype(cfg.NAME)` via a member-pointer
       table generated at compile time, or
   (b) the registry tuple gains an explicit storage-type-discriminator column.

**Audit verdict:** BL-1 is the single largest design-correctness gap.
Without resolution, the .F.4b parser will silently corrupt ~38 cfg field
values, breaking backtest determinism + live trade calculations. Cannot ship.

**Cross-ref:**
- `DESIGN_SPECS/framework-patterns/universal-cfg-field-registry-pattern.md:196` — design assumes raw double offset
- `CLAUDE.md item 23` — `tt::stamp_parse_field<T>` is the resolvable pattern
- `CoreFrameworks/ControllerConfig.hpp:1877-1913` — existing CFG_PARSE_FPN/_PCT/_FPN_POS that .F.4b removes

### BL-2: Cfg_Save function design does not match actual save model

**Where:** plan Step 5, expected `Cfg_Save(const Cfg* cfg, FILE* fp)` writes
key=value lines.

**Problem:** No such function exists. The actual save model in this codebase
is **in-place text edit per field** via `cfg_write_field(path, key, value)`
in `GUI/SettingsPanel.hpp:472-533`:

```cpp
static inline void cfg_write_field(const char *path, const char *key, const char *value) {
  // 1) read entire file into buf (16KB cap)
  // 2) line-anchored search for "key="
  // 3) splice in replacement OR append at EOF
  // 4) rewrite entire file
}
```

This is called PER FIELD from the SettingsPanel "Apply" / "Save" button.
**There is no whole-cfg-save chokepoint.** Every cfg field write is a
separate fopen/read/splice/fwrite cycle. Plan's `tt::cfg_save_field<K>(FILE*, ...)`
design assumes a streaming-write model that doesn't exist.

The roundtrip parity test in plan Step 6 (lines 207-220) ALSO breaks:

```cpp
Cfg_Save(&cfg1, fp);  // ← function doesn't exist
```

There IS no Cfg_Save. And there's no Cfg_LoadFromString / Cfg_LoadFromFile
either — load is `ControllerConfig_Load(const char *filepath)`
(`CoreFrameworks/ControllerConfig.hpp:1798`) which reads + parses key=value
text lines via fgets + the giant if-strcmp chain.

**Required plan amendment:**

Choose one model for .F.4b:
1. **MODEL A (introduce Cfg_Save):** create a new whole-cfg-save function that
   walks FOREACH_CFG_FIELD and writes key=value lines to FILE*. SettingsPanel's
   "Save All" button (if added) calls this. Existing per-field cfg_write_field
   stays for incremental edits (don't delete; in-place edit semantics is what
   operators need when toggling one flag without disturbing comments).
   Roundtrip test compares output to a baseline file. **NEW SURFACE** —
   requires its own design + Apply-button UX decision.
2. **MODEL B (replace cfg_write_field):** rewrite cfg_write_field to look up
   the field's descriptor via registry, format via tt::cfg_save_field, then
   splice into the existing in-place-edit body. Preserves per-field
   semantics; no new function needed. Migrates the FORMATTING but not the
   FILE I/O.
3. **MODEL C (defer save migration):** .F.4b ships REGISTRY + PARSER + PANEL
   RENDER only. Save stays manual until .F.4c or later. The plan's
   "persist_gap" closure (per universal-cfg-field-registry-pattern.md table)
   moves to .F.4c+.

**Recommendation:** MODEL B is the least disruptive — it preserves the
v4.0 "splice one field, preserve comments" UX while routing the value
FORMATTING through the registry. Add a step to .F.4b:
*"Step 5 (revised): wire tt::cfg_save_field as the value-formatting helper
inside cfg_write_field — call site does
`tt::cfg_save_field<K>(value_buf, sizeof(value_buf), src, desc)` to produce
the value string, then existing splice logic continues."*

Plan also must rewrite test (Step 6 line 207) to avoid Cfg_Save/Cfg_LoadFromString
references — use ControllerConfig_Load via tmpfile + the actual cfg_write_field path.

**Audit verdict:** plan Step 5 + Step 6 specify a non-existent surface.
Must either introduce the surface (MODEL A) — new design work — or migrate
the existing cfg_write_field formatter (MODEL B). MODEL C is the defer
escape hatch but contradicts the "structural fix" intent.

**Cross-ref:**
- `GUI/SettingsPanel.hpp:472-533` — actual save model (`cfg_write_field`)
- `CoreFrameworks/ControllerConfig.hpp:1798` — `ControllerConfig_Load`
- plan Step 5 lines 175-189; Step 6 lines 207-220

### BL-3: Stretch goal "X-macro generates Cfg struct fields" infeasible without further design

**Where:** plan Step 7 "Deliverable B: stretch" lines 340-356.

**Problem:** the stretch proposes:

```cpp
#define EMIT_CFG_STRUCT_FIELD(kind, name, ...) cfg_field_type_##kind name;
// expanded inside `template <unsigned F> struct ControllerConfig { ... }`
```

The C-macro token-paste `cfg_field_type_##KIND_DOUBLE` requires a typedef
`cfg_field_type_KIND_DOUBLE = double;` — but the actual storage type is
`FPN<F>` (BL-1 root cause). Possible escape: `cfg_field_type_KIND_DOUBLE = FPN<F>;`
— but then for the ~2 truly-double fields, you need a different Kind.

Worse, even if we resolve the typedef question, the stretch faces **mass
field-ordering and ABI churn**:

1. `ControllerConfig.hpp` currently declares ~340 lines of struct fields
   organized for readability + historical organic order. The plan's offsetof
   approach requires those offsets to remain STABLE across .F.4b
   (focus item #1 explicitly).
2. If FOREACH_CFG_FIELD ordering doesn't match the existing struct ordering
   EXACTLY (line by line), generating struct fields from the registry will
   REORDER memory layout. Every snapshot byte format, every offset table,
   every memcpy of the cfg struct breaks.
3. The full set of ControllerConfig fields is ~213 cfg-registered fields
   + many non-registry fields (boot-only, monitoring, per-core overrides,
   computed-at-load). The stretch covers only ~40 fields (DOUBLE + DOUBLE_PCT);
   the other ~173 + non-registry fields stay manually declared.

**Implication:** the stretch implies a MIXED struct where the first part is
registry-generated + the latter is manual. This is a sound pattern (X-macro
preamble + manual tail) but requires:
- Strict registry-row ordering matching existing struct line ordering for
  the migrated subset
- Static_assert that offsetof(Cfg, X) for each migrated field matches the
  pre-.F.4b value (you can compute the pre-value at .F.4b ship time +
  embed as a snapshot test, but you can't compute it at compile time
  without the prior binary's offsets)

**Risk assessment:**
- If stretch is attempted in .F.4b: meaningful risk of bytewise-incompatible
  snapshot/backtest determinism break. Mitigations require additional design
  work that's not in scope.
- If stretch is dropped: .F.4d's "reverse drift CI script" is the documented
  fallback (universal-cfg-field-registry-pattern.md line 339-340). Plan
  already names this.

**Required plan amendment:** Explicitly DROP the stretch from .F.4b scope.
Add a TECH_DEBT entry "v5.15.5.F.4 stretch: X-macro generates Cfg struct fields"
that documents the deferral + the prerequisite (resolve BL-1 storage-type
discriminator first). Resume in .F.4d or later AFTER KIND_INT + KIND_BOOL +
KIND_STRING migration validates the storage-discriminator pattern.

**Cross-ref:**
- plan lines 339-356 — stretch deliverable
- `universal-cfg-field-registry-pattern.md:339-340` — backup CI script
- `CLAUDE.md item 19` — structural fix preferred (the stretch IS the structural
  fix here; defer is acceptable when prerequisite design is blocked, per
  `feedback_no_defer_for_effort.md` "defer is last-ditch but here the prerequisite is concretely missing")

---

## DRIFT FINDINGS (review; not blocking)

### DR-1: lives_in_struct enum declared but only STRUCT_CFG populated in .F.4b — what happens if a STRUCT_BACKTEST_CFG row appears prematurely?

**Where:** plan Step 1 lines 39-40; descriptor design `universal-cfg-field-registry-pattern.md:122-129`.

The enum has 5 values (CFG / BACKTEST_CFG / CONTROLLER_CFG / SECRETS_CFG /
TRAINING_CFG). Only STRUCT_CFG is populated at .F.4b. Plan does not specify
the dispatcher's behavior if a STRUCT_BACKTEST_CFG-tagged row is added
prematurely (e.g., by someone working on .F.4i in parallel).

Three options:
1. **Compile-time refuse**: `static_assert(desc.lives_in_struct == STRUCT_CFG, ...)`
   inside the parser X-macro expansion. Any non-STRUCT_CFG entry triggers
   a build error with a clear message. Catches early.
2. **Runtime skip**: parser dispatch on lives_in_struct; non-STRUCT_CFG entries
   silently no-op. Backtest cfg fields parsed from engine.cfg become silent
   ignore. Risky — operator confusion.
3. **Defer to .F.4i**: ban non-STRUCT_CFG rows from the registry until .F.4i
   adds the routing infrastructure. Plan must include this ban as an
   AUTOPOPULATE invariant.

**Recommendation:** Option 1. Add a `static_assert` companion macro
(`FOREACH_CFG_FIELD_ASSERT_STRUCT_CFG`) that walks the registry + emits
`static_assert(KIND_##kind, desc.lives_in_struct == STRUCT_CFG)` for each
entry. .F.4i's first action removes the static_assert.

**Cross-ref:**
- plan Step 1 lines 39-40
- `categorical-tag-applicability-pattern.md` § "Cross-file cfg unification"

### DR-2: tt:: namespace overlap potential — composition with existing tt::stamp_parse_field

**Where:** plan focus item #5 + Step 2 design.

Existing `namespace tt` has ~60 declared sites (verified via grep — see audit
log). The plan introduces tt::cfg_parse_field<K>, tt::cfg_save_field<K>,
tt::cfg_render_field<K>. **No collision today** with any existing tt symbol.

BUT: composition with `tt::stamp_parse_field<T>` (`StampBoundModelConstRegistry.hpp:102`)
is load-bearing for .F.4b's BL-1 resolution. If .F.4b's parser eventually
delegates the type-dispatch INTO tt::stamp_parse_field (or its sibling),
there's a need to thread the FPN<F> type discriminator through both.

Two paths:
1. **Reuse**: tt::cfg_parse_field<KIND_DOUBLE> internally calls
   tt::stamp_parse_field<FPN<F>>(dst, val) for FPN fields and
   tt::stamp_parse_field<double>(dst, val) for raw double. This requires
   the cfg-field-side to know the destination C++ type (BL-1).
2. **Parallel**: tt::cfg_parse_field stays independent. Code duplication
   with tt::stamp_parse_field for the dispatch shape; both diverge over time.

**Recommendation:** Resolution depends on BL-1 fix. If Option A2 (templated
storage helper via decltype), then path 1 is natural composition. If Option
A1 (separate KIND_FPN_*), then path 2 is simpler but duplicates dispatch
logic.

**Audit verdict:** non-blocking; document the composition decision when
resolving BL-1.

### DR-3: FOREACH_STRATEGY tuple-arity already at 8 cols; adding `applies_to_strategy_cat` makes it 9

**Where:** plan Deliverable C lines 360-368; FOREACH_STRATEGY at
`Strategies/StrategyInterface.hpp:107-120`.

Existing tuple shape (8 cols):
```cpp
X(id, short_name, full_name, state_t, init_fn, build_fn, adapt_fn, exit_fn)
```

Adding `category_mask` makes it 9. All consumers (21 grep hits across
`Strategies/`, `tests/`, `Backtest/LabelFunctions.hpp`) currently
expect exactly 8 args. Adding a 9th column requires touching ALL consumer
macros to accept the new arg (even if ignored). Plan does not explicitly
list this as work.

The .F.4h sub-ship plan (umbrella line 44) is when FOREACH_STRATEGY gets
the category-mask column. Per umbrella: ".F.4b creates the CATEGORY ENUMS
(`StrategyCategory : uint32_t`) but does NOT yet populate them on
FOREACH_STRATEGY rows (.F.4h's job)."

This means at .F.4b ship time, `applies_to_strategy_cat` columns on cfg
field rows can reference STRAT_CAT_* values (defined .F.4b in
StrategyCategories.hpp), but the runtime LOOKUP
`strategy_categories_lut[STRATEGY_X]` doesn't exist yet — that's the
FOREACH_STRATEGY column-add job in .F.4h.

**Consequence:** if plan's CI Test 2 (no orphan cfg fields) at .F.4b checks
`applies_to_strategy_cat != 0`, that's fine — it doesn't dereference any
strategy LUT. But if .F.4b tries to GATE rendering on
`(applies_to & active_strategy_cats) != 0`, active_strategy_cats can't be
computed yet (no LUT). GUI filtering by strategy → deferred to .F.4h.

**Plan amendment needed:** clarify that at .F.4b, the
`applies_to_strategy_cat` columns are *declared but unused* for runtime
gating. Render walk shows ALL fields regardless. Categorical filtering
activates at .F.4h. (Or: .F.4b adds 1 column to FOREACH_STRATEGY with all
zeros + .F.4h populates with real values; this defers the consumer-macro
arity change to .F.4b — possibly easier to do once.)

**Cross-ref:**
- plan Deliverable C lines 360-368
- umbrella sub-ship table line 44 (.F.4h)
- `Strategies/StrategyInterface.hpp:107`, `Strategies/StrategyLifecycle.hpp:136`

---

## DOCUMENTED-RISK FINDINGS

### DOC-1: SettingsPanel field_defs[] has TWO source-of-truth surfaces today (manual + 5 FOREACH_*_CFG_FLAG auto-extend)

**Where:** `GUI/SettingsPanel.hpp:46-305`.

The field_defs[] array already has TWO populating mechanisms:
1. **Manual entries** (~90 rows; the "old way")
2. **Auto-extended via 5 FOREACH_*_CFG_FLAG registries** (LIFECYCLE / GATE / ML / RISK / OPS) appended at lines 297-304 — 21 boolean cfg flags

Plan's .F.4b adds a THIRD mechanism: FOREACH_CFG_FIELD walk emitting render
calls. The migration plan says to "Remove from `field_defs[]`" (Step 3 line 122)
for migrated DOUBLE fields — that's fine. But the result is field_defs[]
with two remaining sources (manual + cfg-flag registries) PLUS a parallel
new render walk. During the .F.4b→.F.4d transition, render order
preservation is delicate: cfg.example documentation conventions assume
section grouping (e.g., "Trading" → "Entry Filters" → "Risk Management"); the
NEW registry walk must merge into the SAME section ordering visible in the
existing field_defs[].

**Risk:** if the FOREACH_CFG_FIELD-driven render walk runs at a different
time/place than the field_defs[] walk, rendered sections drift visually
(operator UX confusion — "where did Bandit Blend go?").

**Mitigation:** plan should specify whether (a) the new walk emits BEFORE
field_defs[] iteration, (b) AFTER, or (c) sections are merged by name
matching at render time. Recommend (c) — robust to migration order; matches
the existing "section heading collapsing header" idiom.

**Cross-ref:** `GUI/SettingsPanel.hpp:756-784` (existing Global Tab render walk).

### DOC-2: PerCoreOverrides struct fields use FPN<F> — same BL-1 issue for per-core overrides

**Where:** `CoreFrameworks/ControllerConfig.hpp:252-268`.

Per-core overrides are stored in `PerCoreOverrides<F>` via PER_CORE_OVERRIDE_FIELDS
macro. Every override is `FPN<F> name;` (RAW + PCT both expand to FPN).
The plan's Deliverable D defers per-core override re-layout to .F.4g but does
mention .F.4b emits `core_<name>[16]` storage when PER_CORE_OK metadata is
set (universal-cfg-field-registry-pattern.md:254-258).

If .F.4b auto-emits storage via X-macro at the PerCoreOverrides struct
declaration site, that storage must be FPN<F> for KIND_DOUBLE/_PCT fields
(not double). Same fix as BL-1 applied here too.

If .F.4b does NOT auto-emit per-core storage (deferred to .F.4g), the
plan should say so — plan currently states "verify per-core override
auto-emits if PER_CORE_OK set" (universal-cfg-field-registry-pattern.md:320,
checklist item 5) — implying it does at .F.4b. Status ambiguous.

**Recommendation:** plan should explicitly state ".F.4b: PER_CORE_OK metadata
column declared on registry rows but NOT yet wired to storage emission;
existing PER_CORE_OVERRIDE_FIELDS macro continues to govern per-core
storage until .F.4g re-layouts."

---

## Mirror data-flow audit

Plan does not claim to mirror an existing source surface verbatim — it's
NEW infrastructure layered alongside the existing parser. Mirror audit
(Step 6 of skill procedure) returns: N/A, no mirror to audit.

Mirror call-sequence audit: similarly N/A.

---

## Per-callee verification

| Callee | Verdict | Location | Note |
|---|---|---|---|
| `tt::stamp_parse_field<T>` (precedent only) | PASS | `ML_Headers/StampBoundModelConstRegistry.hpp:102-124` | composition pattern for BL-1 fix |
| `parse_double_fast` | PASS | `CoreFrameworks/ParseFast.hpp:38` (declared in tt::) | available |
| `FPN_FromDouble<F>` | PASS | `FixedPoint/FPN.hpp` | available |
| `FPN_ToDouble<F>` | PASS | `FixedPoint/FPN.hpp` | available |
| `CFG_PARSE_FPN` / `_PCT` / `_INT` / `_U32` / `_FPN_POS` | PASS (to be removed) | `CoreFrameworks/ControllerConfig.hpp:1877-1913` | exist; .F.4b deletes for migrated fields |
| `FOREACH_STAMP_BOUND_CFG` | PASS | `ML_Headers/StampBoundCfgRegistry.hpp:99` | derived filter target |
| `FOREACH_STRATEGY` | PASS | `Strategies/StrategyInterface.hpp:107` | needs column extension at .F.4h (DR-3) |
| `STAMP_CFG_AUTOPOPULATE` | PASS | `ML_Headers/StampBoundCfgRegistry.hpp:227` | precedent pattern |
| `BITMAP_IS_SET` / `BITMAP_ANY` | PASS | `MemHeaders/BitmapMacros.hpp` | available |
| `ControllerConfig<F>` | PASS | `CoreFrameworks/ControllerConfig.hpp:280` | templated POD struct (offsetof works) |
| `ControllerConfig_Load` | PASS | `CoreFrameworks/ControllerConfig.hpp:1798` | exists |
| `Cfg_Save` | GAP | does not exist | BL-2 |
| `Cfg_LoadFromString` | GAP | does not exist | BL-2 |
| `cfg_write_field` | PASS | `GUI/SettingsPanel.hpp:472` | actual save mechanism |
| `cfg_field_offset(name)` | GAP-PLANNED | to be created | requires BL-1 type-dispatch resolution |
| `g_cfg_field_descriptors[FIELD_IDX_X]` | GAP-PLANNED | to be created | descriptor table generation |
| `StrategyCategory` enum | GAP-PLANNED | NEW Strategies/StrategyCategories.hpp | no collision with existing |
| `OpModeCategory` enum | GAP-PLANNED | NEW Strategies/OpModeCategories.hpp | no collision with existing |

---

## Recommendations summary

**Before .F.4b coding starts:**

1. **Resolve BL-1** — pick storage-type-discriminator approach (A1 / A2). Update
   `universal-cfg-field-registry-pattern.md:189-202` + plan Step 2 to specify
   `tt::cfg_parse_field<K>` body using `FPN_FromDouble<F>` for FPN fields,
   raw assign for true-double fields. Document the type-discriminator path
   in the descriptor (extra column or per-Kind specialization).

2. **Resolve BL-2** — pick save model. MODEL B (rewire cfg_write_field's
   formatter through tt::cfg_save_field) recommended. Update plan Step 5 +
   Step 6 (roundtrip test) accordingly. Drop references to Cfg_Save /
   Cfg_LoadFromString.

3. **Resolve BL-3** — drop X-macro Cfg struct-gen stretch from .F.4b scope.
   Document deferral as TECH_DEBT entry with prerequisite ("complete BL-1
   storage discriminator first"). Note `.F.4d`'s reverse-drift CI script
   as the load-bearing fallback for the drift class.

**During .F.4b coding:**

4. **DR-1**: Add static_assert that all .F.4b registry entries have
   `lives_in_struct == STRUCT_CFG`. Document removal in .F.4i.
5. **DR-2**: Document the BL-1 resolution in tt:: namespace compose decision
   inline + cross-link to tt::stamp_parse_field<T>.
6. **DR-3**: Either (a) add `category_mask` column to FOREACH_STRATEGY at
   .F.4b with all zeros (consumer-macro arity bump done once), or (b) plan
   .F.4h adds the column + the populated values together. Recommend (a) —
   bumps arity once, future .F.4h additions are mechanical.
7. **DOC-1**: Plan how registry-driven render walk merges with manual
   field_defs[] section ordering during transition.
8. **DOC-2**: Clarify per-core storage emission timing (.F.4b declares the
   PER_CORE_OK metadata bit but storage emission deferred to .F.4g).

**Effort impact:** these resolutions add ~30-60 min of design clarification
to the .F.4b pre-coding pass. They do NOT change scope materially — they
clarify what already needs to happen. BL-1 in particular is a load-bearing
correctness blocker; ship without it risks bytewise corruption.

---

## Verdict

**RED** — three BLOCKER findings must be resolved in plan before coding.

The plan's design intent is correct + the structural-fix-preferred framework
applies here (Class 18 mirror at function-composition level for cfg field
addition). The execution-level details (FPN storage, save model, struct-gen
stretch) need pre-coding fixes. Plan is otherwise well-scoped; once BL-1 + BL-2
+ BL-3 are addressed, audit re-runs to GREEN/YELLOW.
