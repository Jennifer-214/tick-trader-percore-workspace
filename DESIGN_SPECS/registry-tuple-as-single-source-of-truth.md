# Registry tuple as single source of truth (5-col tuple expansion — Option D)

**Established:** 2026-05-10 (v5.14.9.F.5 — "Option D" decision)
**Status:** ACTIVE
**Cross-references:**
- Parent pattern: `x-macro-registry-with-presence-dispatch.md` (base X-macro registry)
- Sister pattern: `heterogeneous-registry-pattern.md` (DOMAIN SPLIT registries that use this)
- Sister pattern: `autopopulate-from-arity-macro-family.md` (one consumer of the tuple)
- First application: `CoreFrameworks/LifecycleCfgFlagRegistry.hpp` (5-col tuple post-.F.5)
- First GUI consumer: `GUI/SettingsPanel.hpp` (auto-extends field_defs[] from 5 registries)
- CLAUDE.md item 13 (X-macro registry as the standard pattern)

---

## Problem statement

A registry was first conceived for ONE consumer (e.g., cfg parsing). As the codebase matures, MORE consumers want to ingest the same registry: GUI rendering, per-core override declaration, stamp-binding metadata, engine.cfg.example documentation, audit trails, drift checks, tests.

**Recurring trajectory:**

1. Registry shipped with 3-col tuple `X(name, type, default)` — only the parser consumes it.
2. GUI panel needs to render checkboxes for cfg flags → maintainer hardcodes a parallel `field_defs[]` array listing 14 manual entries.
3. Operator-facing docs need entries → maintainer copy-pastes into `engine.cfg.example`.
4. Audit / drift tool needs the doc string → another parallel list.
5. A new flag added 6 months later: maintainer updates registry + parser, FORGETS the GUI + docs + audit.

This is the **partial-mirror tech-debt** shape — registry exists but doesn't COVER all consumers; parallel sources drift over time.

**Option D's claim:** put all consumer-specific metadata in the registry tuple itself. Adding a column for each consumer's needs makes the registry the SINGLE SOURCE OF TRUTH. Adding a new entry = 1 row → ALL consumers auto-flow.

---

## Design space explored

### Option A: Manual per-consumer entries (worst — current state of many registries)

Each consumer maintains its own list. Bug class: drift across N parallel lists.

### Option B: Registry generates ONLY the bitmap/struct (medium)

Registry has minimal tuple (just name + type); consumers like GUI write their OWN `field_defs[]` referencing registry constants but providing labels/sections/docs manually.

**Improvement over A** (registry is consulted) but still partial-mirror — adding an entry touches registry + each consumer's manual table.

### Option C: Hybrid with parallel meta tables (poor compromise)

Registry stays minimal; a separate `MetaTable[]` lists labels/sections/docs indexed by entry name. Consumers JOIN at use site.

**Rejected.** Two tables to maintain side-by-side (registry + meta). Same drift class, just renamed. Worse: the JOIN logic at consumer sites adds boilerplate per consumer.

### Option D (chosen): Tuple expansion — registry IS the source of truth

Registry tuple grows to N columns, one per consumer's needs. Each consumer walks the registry with a tailored X-macro extractor that picks the columns IT needs and ignores the rest.

```cpp
// 5-col tuple: X(NAME, legacy_field, display_label, section, doc)
#define FOREACH_LIFECYCLE_CFG_FLAG(X)                                                                                                                    \
    X(PARTIAL_EXIT_ENABLED, partial_exit_enabled, "Partial Exits##toggle", "Toggles",       "partial-exit dispatcher arm — leg-A and leg-B size split") \
    X(BREAKEVEN_ON_PARTIAL, breakeven_on_partial, "Breakeven SL",          "Partial Exits", "move SL to entry after TP1 hit")                            \
    X(BREAKEVEN_ON_PROFIT,  breakeven_on_profit,  "Breakeven on Profit",   "Partial Exits", "ratchet SL to breakeven when position crosses net profit")
```

Each X-macro consumer macro consumes the args it needs:

```cpp
// Consumer 1: enum + bitmap generation (uses NAME only)
#define X_GEN_BIT(name, legacy_field, display_label, section, doc) LIFECYCLE_CFG_##name,
enum { FOREACH_LIFECYCLE_CFG_FLAG(X_GEN_BIT) };
#undef X_GEN_BIT

// Consumer 2: parser (uses NAME + legacy_field)
#define X_PARSE_BRANCH(name, legacy_field, display_label, section, doc) \
    else if (strcmp(key, #legacy_field) == 0) { /* parse + set bit */ }
FOREACH_LIFECYCLE_CFG_FLAG(X_PARSE_BRANCH)
#undef X_PARSE_BRANCH

// Consumer 3: GUI field_defs[] (uses NAME + legacy_field + display_label + section + doc)
#define X_GUI_FIELD(name, legacy_field, display_label, section, doc) \
    {#legacy_field, display_label, section, CFG_BOOL, NULL, doc},
FOREACH_LIFECYCLE_CFG_FLAG(X_GUI_FIELD)
#undef X_GUI_FIELD

// Consumer 4: engine.cfg.example doc (uses legacy_field + doc)
#define X_CFG_DOC(name, legacy_field, display_label, section, doc) \
    fprintf(f, "# %s\n%s=0\n\n", doc, #legacy_field);
FOREACH_LIFECYCLE_CFG_FLAG(X_CFG_DOC)
#undef X_CFG_DOC
```

Each consumer picks its columns; ignores the rest. Adding a row in the registry → all 4 consumers automatically extend at next compile.

---

## The pattern (concrete shape)

### Step 1: Inventory consumers + identify their needs

Before designing the tuple, list every consumer + what it needs:

| Consumer | Needs |
|---|---|
| Bitmap enum + MASK constants | NAME |
| Cfg parser | NAME, legacy_field (cfg key string) |
| AUTOPOPULATE | NAME (bit position) |
| GUI field_defs[] | NAME, legacy_field, display_label, section, doc |
| engine.cfg.example | legacy_field, doc |
| Per-core override declaration | NAME (bit position) |
| Drift check | NAME, legacy_field, doc |

Union of needs: NAME, legacy_field, display_label, section, doc. → 5-col tuple.

### Step 2: Define the tuple

```cpp
// Tuple: X(NAME, legacy_field, display_label, section, doc)
//   NAME          — UPPERCASE token; used for MASK_<DOMAIN>_CFG_<NAME> + enum bit
//   legacy_field  — cfg key string (snake_case lowercase); used by parser + GUI + docs
//   display_label — operator-facing GUI label (may include "##suffix" for ImGui ID disambiguation)
//   section       — GUI section / collapsing-header name
//   doc           — short description used in cfg.example + GUI tooltip + audit
```

Column types:
- NAME: bare identifier (for token-paste; no quotes)
- legacy_field: bare identifier (for token-paste in parser; consumer adds `#` operator for stringification)
- display_label / section / doc: string literals (consumer uses them directly)

### Step 3: Walk via per-consumer X-macro extractors

Each consumer defines a local X-macro that picks the columns it cares about. Use `#name` for stringification + bare `name` for token-paste.

### Step 4: Co-locate ALL extractors near the FOREACH

Best: put the FOREACH macro at the top of a dedicated registry header. Below it, define ALL consumer extractors that live in this header (enum, MASK constants, AUTOPOPULATE). Other consumers (GUI, parser body) live in their own files but include this header.

```
RegistryHeader.hpp:
  FOREACH_X
  // local consumers
  enum { ... }
  static constexpr MASK_... = ...;
  AUTOPOPULATE macro
  // documentation: list other consumers + their files for cross-ref

ParserBody.hpp (consumer):
  #include "RegistryHeader.hpp"
  // its own X-macro extractor
  FOREACH_X(my_extractor)
```

### Step 5: Document the tuple format ABOVE the FOREACH

The tuple definition is the CONTRACT. Document every column + its purpose so future maintainers can extend without ambiguity:

```cpp
// Tuple: X(NAME, legacy_field, display_label, section, doc)
//   NAME          — UPPERCASE token; used for MASK constants + enum bits
//   legacy_field  — cfg key string (snake_case); used by parser + GUI + docs
//   display_label — operator-facing GUI label; "##suffix" allowed for ImGui IDs
//   section       — GUI section / collapsing-header name
//   doc           — short description; cfg.example + GUI tooltip + audit
//
// Adding a new entry: append 1 row → enum bit, MASK constant, AUTOPOPULATE bit-set,
// parser branch, engine.cfg.example doc, AND GUI checkbox+section+tooltip all
// auto-flow / mechanically extend.
```

---

## Worked example: GUI field_defs[] auto-extension

**Before (Option A — manual entries):**

```cpp
// GUI/SettingsPanel.hpp — 14 manual entries
static const FieldDef field_defs[] = {
    {"partial_exit_enabled", "Partial Exits##toggle", "Toggles", CFG_BOOL, NULL, "..."},
    {"breakeven_on_partial", "Breakeven SL",          "Partial Exits", CFG_BOOL, NULL, "..."},
    {"breakeven_on_profit",  "Breakeven on Profit",   "Partial Exits", CFG_BOOL, NULL, "..."},
    {"depth_enabled",        "Depth Gate",            "Gates",         CFG_BOOL, NULL, "..."},
    {"gate_ema_enabled",     "Gate EMA",              "Gates",         CFG_BOOL, NULL, "..."},
    // ... 9 more entries ...
};
```

**After (Option D — auto-extend from 5 registries):**

```cpp
// GUI/SettingsPanel.hpp
#include "../CoreFrameworks/LifecycleCfgFlagRegistry.hpp"
#include "../CoreFrameworks/GateCfgFlagRegistry.hpp"
#include "../ML_Headers/MlCfgFlagRegistry.hpp"
#include "../CoreFrameworks/RiskCfgFlagRegistry.hpp"
#include "../CoreFrameworks/OpsCfgFlagRegistry.hpp"

#define X_AUTOEXTEND_FIELD_DEFS(name, legacy_field, display_label, section, doc) \
    {#legacy_field, display_label, section, CFG_BOOL, NULL, doc},

static const FieldDef field_defs[] = {
    // ... non-cfg-flag fields stay manual ...
    {"some_other_field", "Other Field", "Misc", CFG_FPN, ...},

    // Auto-extend from 5 domain registries
    FOREACH_LIFECYCLE_CFG_FLAG(X_AUTOEXTEND_FIELD_DEFS)
    FOREACH_GATE_CFG_FLAG(X_AUTOEXTEND_FIELD_DEFS)
    FOREACH_ML_CFG_FLAG(X_AUTOEXTEND_FIELD_DEFS)
    FOREACH_RISK_CFG_FLAG(X_AUTOEXTEND_FIELD_DEFS)
    FOREACH_OPS_CFG_FLAG(X_AUTOEXTEND_FIELD_DEFS)
};
#undef X_AUTOEXTEND_FIELD_DEFS
```

14 manual entries → 5 lines + 1 X-macro extractor. Adding a new flag = 1 row in its registry → GUI auto-renders the checkbox at next compile.

---

## Trade-offs + when to apply

### Apply when:
- Registry has 2+ consumers (cfg parser + GUI + docs + ...)
- Each consumer's per-entry data is mostly derivable (label = display name; section = grouping)
- Maintenance burden of parallel meta tables has shown drift (recurrent bug class)
- Tuple width stays ≤ 8-10 columns (beyond, consumers get unwieldy)

### Skip when:
- Single consumer (no parallel mirror, no drift class)
- Consumers' per-entry data has wildly heterogeneous shape that doesn't fit a uniform tuple
- Registry has very few entries (≤3); manual parallel lists are tractable

### Cost:
- Initial tuple expansion: 1-3h per registry (audit consumers + design tuple + migrate)
- Tuple width grows (2-col → 5-col adds visual weight in the FOREACH definition)
- Each consumer needs an X-macro extractor (~5-10 LOC per consumer)
- Caller-side migration: replace manual tables with FOREACH walks (mechanical; ~1-2h total)

### Win:
- Drift class structurally extinct — registry IS source of truth
- Adding new entry = 1 row → all consumers auto-flow
- Co-located metadata (label/section/doc near the cfg key) improves readability
- Test-by-construction: tests walk the registry to assert every entry has GUI/parser/docs coverage
- Audit / drift tools query ONE place; no parallel-list reconciliation

---

## Reference implementations

### v5.14.9.F.5 — first 5-col tuple expansion

5 registries unified under the 5-col format:

| Registry | Consumers using 5-col |
|---|---|
| FOREACH_LIFECYCLE_CFG_FLAG | enum, MASK, AUTOPOPULATE, parser, GUI, cfg.example, per-core override |
| FOREACH_GATE_CFG_FLAG | (same 7 consumers) |
| FOREACH_ML_CFG_FLAG | (same 7) + stamp-binding (Y3 dispatch) |
| FOREACH_RISK_CFG_FLAG | (same 7) |
| FOREACH_OPS_CFG_FLAG | (same 7) |

Total: 5 registries × 7 consumers = 35 consumer-registry connections, all driven by 1 tuple format.

GUI consumer: `GUI/SettingsPanel.hpp` deleted 14 manual entries; replaced with 5 FOREACH walks.

### Adjacent patterns / future application candidates

- `FOREACH_FEATURE` (v5.14.9.E): currently 7-col tuple (NAME + 6 columns); validates the principle.
- `FOREACH_STAMP_BOUND_CFG` / `FOREACH_STAMP_BOUND_MODEL_CONST` (v5.14.8): 8-col / 9-col tuples; similar principle for stamp-body fields.
- `FOREACH_FAILURE_MODE` (v5.14.8.B): 5-col with per-entry storage_class column.
- Future: any registry with ≥3 consumers should default to Option D from the start.

---

## Lessons / gotchas

### Pick column names carefully — they're permanent

The tuple format is the contract. Renaming a column requires updating every X-macro extractor that consumed it. Pick names that survive scope creep:

- `NAME` (good) vs `enum_value_name` (verbose) vs `key` (ambiguous — key in what sense?)
- `legacy_field` (good — captures provenance even after migration) vs `cfg_key` (less informative)
- `doc` (good — short, clear purpose) vs `description` (longer; same meaning)

### Don't sneak extra columns mid-sprint

When a new consumer emerges that needs a NEW column, evaluate carefully:

- Can the consumer derive it from existing columns? (e.g., GUI tooltip = same as doc — no new column needed)
- Is the new column truly registry-wide, or specific to ONE entry? (specific → put in `doc` as a structured suffix, not a new column)
- If genuinely new + universal: add the column in a deliberate sub-ship; update all existing extractors at the same time.

### Audit detection for partial-mirror tech debt

Once Option D is the canonical pattern, `/dod-audit` can flag:

- Symptom: manual `field_defs[]` / `cfg_doc_lines[]` / similar tables that parallel a FOREACH registry
- Detection: grep for hardcoded field names alongside the registry's NAMEs
- Fix: convert to X-macro extractor walk

### Display label "##suffix" for ImGui ID uniqueness

ImGui uses the label string as both the visible text AND the widget ID. If two checkboxes have the same label "Partial Exits", they collide. Convention: use `##suffix` to disambiguate IDs without changing visible text:

```cpp
X(PARTIAL_EXIT_ENABLED, partial_exit_enabled, "Partial Exits##toggle", "Toggles", "...")
```

Visible: "Partial Exits". ImGui ID: "Partial Exits##toggle". Other consumers (docs, audit) ignore the `##suffix` — they consume the full string; the `##` is harmless in non-GUI contexts.

### Section + display_label can drive auto-grouping

GUI consumer's X-extractor can sort field_defs[] by section, render section headers automatically. Tuple's `section` column becomes the grouping key. No separate "sections" list needed.

### Tuple expansion grows the FOREACH definition visually

A 5-col tuple per row at ~150 chars wide is bulky. Use line continuations + alignment to keep it readable:

```cpp
#define FOREACH_X(X)                                                                                                                  \
    X(SHORT_NAME, short_field,       "Short Label",       "Section", "short doc")                                                     \
    X(LONGER_NAME_HERE, longer_field, "Longer Label",     "Section", "longer doc that explains more")                                 \
    X(MEDIUM_NAME, medium_field,     "Medium Label",      "Section", "medium doc")
```

Column-alignment pressures keep entries visually parseable; many editors auto-align on save.

### Don't break the contract with conditional columns

Tempting to add a column that's "optional" (some entries fill, some don't). **Don't.** Either:
- Every entry fills the column (use a sentinel like `""` or `0` for "no value")
- The column belongs in a SEPARATE registry (different consumer mix)

Conditional columns break the X-macro contract; some extractors would need per-entry branches.

### Don't bury the doc column

The `doc` column is operator-facing — it appears in GUI tooltip + `engine.cfg.example` + audit trails. Operators see it. Write doc strings as if for an operator who's never seen the codebase:

- ✅ "partial-exit dispatcher arm — leg-A and leg-B size split"
- ❌ "enables PE" (acronyms; assumed knowledge)

### Co-locate but don't conflate

The registry header should declare local consumers (enum, MASK, AUTOPOPULATE). Cross-file consumers (parser, GUI) live in their files; the registry header is INCLUDED by them. Don't try to fit GUI rendering logic into the registry header.

---

## Audit detection

`/dod-audit` detects missed applications by:

- Symptom: manual `static const FieldDef field_defs[]` (or similar parallel meta table) listing entries that match a FOREACH registry's NAMEs
- Symptom: `engine.cfg.example`-style doc generator with hardcoded entries paralleling a registry
- Symptom: GUI tooltip table or audit-summary table that mirrors a registry's entries

When detected → flag as `MISSED — registry-tuple-as-single-source-of-truth`. Recommended fix: expand the registry tuple to include the needed columns; replace the parallel table with an X-macro extractor walk.

---

## Patterns NOT used here (and why)

### Reflection (C++26)

Future C++ reflection might let consumers introspect the registry without per-consumer X-macro extractors. Not available yet; revisit at C++26 adoption.

### YAML/JSON registry + code-gen

External registry file + build-time code generator produces C++ headers. Considered for cross-language registries (e.g., Python tools that need the same data). For C++-only registries, in-language X-macros are simpler — no build-tool dependency.

### Boost.PP variadic macros

External preprocessor library. Same single-source-of-truth result; adds dependency. Plain C preprocessor is sufficient for our column counts.

---

## Cross-references

- `x-macro-registry-with-presence-dispatch.md` — base X-macro pattern (this extends with per-consumer extractors)
- `heterogeneous-registry-pattern.md` — DOMAIN SPLIT registries that use Option D
- `autopopulate-from-arity-macro-family.md` — one consumer of the tuple (the AUTOPOPULATE macro)
- `bitmap-flag-api.md` — bitmap consumer (BITMAP_IS_SET reads what the tuple-driven bits define)
- FoxML_Trader_v2 `CLAUDE.md` item 13 — X-macro for multi-site additions
- FoxML_Trader_v2 `CoreFrameworks/LifecycleCfgFlagRegistry.hpp` — first 5-col tuple
- FoxML_Trader_v2 `GUI/SettingsPanel.hpp` — first GUI consumer auto-extending from 5 registries
