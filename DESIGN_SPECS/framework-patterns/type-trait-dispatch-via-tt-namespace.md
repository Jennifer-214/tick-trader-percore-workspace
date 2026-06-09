---
type: framework-pattern
stage: 5-claude-md
version: 1.0
established: 2026-05-14
tags: [framework-discipline, structural-fix, branchless-discipline]
surface: [registry, cfg-flow, wire-format]
sister_specs: [universal-cfg-field-registry-pattern.md, type-erased-per-core-resource-handle-pattern.md, x-macro-registry-with-presence-dispatch.md]
applies_at_skills: []
---

# Type-trait dispatch via tt:: namespace — registry-driven typed-field access without type erasure

**Established:** 2026-05-14 (v5.15.5.F.4b pre-coding audit; pattern formalized from the precedent at `tt::stamp_parse_field<T>` v5.14.8.A.merged)
**Status:** ACTIVE
**Cross-references:**
- Parent: `x-macro-registry-with-presence-dispatch.md` (Y3 dispatch + tt:: precedent)
- Sister: `autopopulate-pattern-for-production-caller-class.md` (AUTOPOPULATE companion macros use tt:: dispatch under the hood)
- Anti-pattern: `DOCS/RECURRING_BUG_PATTERNS.md` Class 23 (Type-erased typed-field write via reinterpret_cast through char* offset)
- Canonical reference implementation: `tt::stamp_parse_field<T>` at `ML_Headers/StampBoundModelConstRegistry.hpp:86-99`
- First codified application: `tt::cfg_parse_field<T>` / `tt::cfg_save_field<T>` / `tt::cfg_render_field<T>` at v5.15.5.F.4b
- CLAUDE.md item 23 (type-trait dispatch via templated helpers; THIS pattern is the canonical doc for that item)
- CLAUDE.md item 19 (structural fix preferred when bug class can recur) — motivates the 3-barrier design
- CLAUDE.md item 13 (X-macro registry as the standard pattern for multi-site additions)

---

## Problem statement

X-macro-driven registries (FOREACH_X) generate parser / save / render / drift-check / snapshot dispatchers across many entries. Each registry entry has a TYPE (the destination field's actual type in the consumer struct). A naïve dispatch implementation uses an opaque type token (Kind enum) + offsetof pun:

```cpp
// ANTI-PATTERN — type-erased dispatch (Class 23):
template <Kind K>
void dispatch_parse(void* dst_base, size_t offset, const char* val);

template <> void dispatch_parse<KIND_DOUBLE>(void* dst_base, size_t offset, const char* val) {
    *reinterpret_cast<double*>((char*)dst_base + offset) = parse_double(val);
}
```

This SILENTLY CORRUPTS when the actual field type at `(dst_base + offset)` differs from the assumed pun type. Concrete failure: punning a `double` write through an `FPN_Binary<F>` field address (16 bytes; a bare two's-complement `__int128 v`) writes 8 bytes of mantissa+exponent into the low half of the FPN_Binary's `__int128 v`, leaving the high 64 bits stale. Subsequent FPN_Binary arithmetic operates on corrupt state → silent precision loss → backtest determinism breaks → train-serve parity breaks. The bug is undetectable by load+compare-back roundtrip tests that only inspect the trivial-type subset.

The recurring class behind this anti-shape: **type erasure at registry dispatch time**. The registry knows the entry NAME but the dispatcher manipulates the destination via opaque address+offset. Type safety is left to the macro-author's discipline ("make sure Kind matches the actual field type"). When discipline slips — and it WILL slip — the failure is silent.

**The structural fix:** dispatch on the destination type T directly. Pass the field BY REFERENCE; let template deduction determine T; use `if constexpr` branches keyed on type traits (`is_fp_binary_v<T>`, `std::is_array_v<T>`, `std::is_floating_point_v<T>`, etc.). The Kind enum stays as METADATA only (drives GUI presentation: slider range, format string, percentage suffix) — never used to choose how the value is stored.

This pattern makes the bug class structurally unreachable in well-formed code, fails-the-build on type extension that's unhandled, and is grep-detectable on intentional bypass.

---

## Design space explored

### Option A — Kind enum + offsetof + reinterpret_cast (the anti-pattern)

```cpp
template <Kind K> void dispatch(void* base, size_t offset, ...);
```

**Rejected.** Type-erases the destination; requires manual discipline to keep Kind in sync with field type; silent corruption on drift. This IS Class 23.

### Option B — Member pointer table

```cpp
struct Descriptor {
    Kind kind;
    union {
        double Cfg::* dbl_ptr;
        int Cfg::* int_ptr;
        FPN<64> Cfg::* fpn64_ptr;
        // ...
    };
};
```

**Rejected.** Per-Kind union increases descriptor size; doesn't compose with template-instantiated FPN_Binary<F> (would need per-F member pointers); type safety enforced at member-pointer-init time but dispatch still reads Kind to know which union arm to use → drift class persists.

### Option C — Templated dispatch via tt:: namespace, T deduced from field reference (chosen)

```cpp
namespace tt {
    template <typename T>
    void dispatch_parse(T& dst, const Descriptor& desc, const char* val) {
        if constexpr (is_FPN_v<T>)        { /* FPN_FromDouble + clamp */ }
        else if constexpr (std::is_floating_point_v<T>) { /* parse_double_fast */ }
        else if constexpr (std::is_array_v<T>)          { /* strncpy + null-term */ }
        // ...
    }
}
```

X-macro extractor passes the field by reference: `tt::dispatch_parse(cfg->name, desc, val)`. T is deduced from the actual field type. Wrong type at extension time = compile error (via `static_assert` type-family guard), not silent corruption.

**Wins over A:**
- Type safety enforced by C++ template system, not by macro-author discipline
- Adding a new field type = extend `tt::` with a new `if constexpr` branch (forced visibility)
- Kind enum freed up to be metadata-only (decoupled from storage)
- Composes cleanly with X-macro extractors (canonical chokepoint per CLAUDE.md item 13)

**Wins over B:**
- No per-T template specialization explosion (one templated function; type-trait branches inside)
- Composes with template-instantiated types (FPN_Binary<F>) without per-F machinery
- No descriptor size growth from member-pointer union

**Cost vs A:**
- Slightly more verbose at the X-macro extractor (passes `cfg->name` instead of `offsetof(Cfg, name)`)
- Requires type traits for codebase-specific types (e.g., `is_fp_binary_v<T>`)
- All consumer types must be in a "recognized family" or static_assert fails — surfaces extension cost at build time (deliberate; this IS the safety mechanism)

### Y3 dispatch caveat (where tt:: differs)

Per `x-macro-registry-with-presence-dispatch.md` § "Y3 dispatch canon", in non-template macro context, `if constexpr` branches must be SYNTACTICALLY VALID for ALL types — `(char[16])(scalar_value)` in a non-taken `if constexpr` branch is still a hard cast error. **Solution:** put the `if constexpr` chain inside a TEMPLATED helper (the `tt::` function); template instantiation per T discards branches correctly. The X-macro extractor calls the templated helper, not raw `if constexpr`. This pattern's `tt::` namespace IS that solution.

---

## The pattern (concrete shape)

### 3-barrier structural design

This pattern alone closes Class 23 only if all THREE barriers are in place. Each barrier alone is insufficient.

**Barrier 1 — API surface: only T-deduced overloads exist.**

```cpp
namespace tt {
    template <typename T>
    inline void <verb>_field(T& dst, const Descriptor& desc, /* args */);
}
```

NO `<verb>_field<KIND>(void* base, size_t offset, ...)` overload exists. A new contributor cannot accidentally write the anti-shape because the unsafe symbol doesn't exist. Bypassing requires inventing new infrastructure → grep-detectable.

**Barrier 2 — X-macro extractor is the chokepoint.** The only registered way to walk the registry is through extractor macros that pass field by reference:

```cpp
#define EMIT_PARSE_CASE(kind_token, name, ...) \
    else if (strcmp(key, #name) == 0) { \
        tt::cfg_parse_field(cfg->name, g_descriptors[FIELD_IDX_##name], val); \
    }
FOREACH_CFG_FIELD(EMIT_PARSE_CASE)
```

`cfg->name` is a real field access; T is deduced from the field declaration. The extractor template has no `(char*)cfg + offset` form; new contributors copy the canonical extractor; the safe form is the only template available.

**Barrier 3 — compile-time type-family guard inside the dispatcher.**

```cpp
namespace tt {
    template <typename T>
    inline void cfg_parse_field(T& dst, const Descriptor& desc, const char* val) {
        static_assert(is_FPN_v<T>
                   || std::is_floating_point_v<T>
                   || std::is_integral_v<T>
                   || std::is_array_v<T>,
                      "cfg field type not in recognized family — "
                      "extend tt::cfg_parse_field<T> with a new branch before using this T as a cfg field");
        if constexpr (is_FPN_v<T>) { /* ... */ }
        else if constexpr (std::is_floating_point_v<T>) { /* ... */ }
        else if constexpr (std::is_array_v<T>)          { /* ... */ }
        else if constexpr (std::is_unsigned_v<T>)       { /* ... */ }
        else                                             { /* signed integral */ }
    }
}
```

Adding a cfg field of an unrecognized type **fails the build** at the static_assert. Forces a deliberate decision (extend the dispatcher) rather than silent truncation.

### Required type traits (codebase-specific)

```cpp
// FixedPoint/FixedPointN.hpp — colocated with FPN<F> primary template
template <typename T> struct is_FPN : std::false_type {};
template <unsigned F> struct is_FPN<FPN<F>> : std::true_type {};
template <typename T> inline constexpr bool is_FPN_v = is_FPN<T>::value;
```

Same shape for any other template-instantiated POD type the codebase needs to dispatch on (e.g., if a `BitmapField<N>` template gets added, define `is_BitmapField_v`).

### Per-verb dispatch (parse / save / render / drift-check)

The pattern repeats per verb:

```cpp
namespace tt {
    // Parse text → field
    template <typename T>
    inline void cfg_parse_field(T& dst, const Descriptor& desc, const char* val);

    // Save field → text buffer
    template <typename T>
    inline void cfg_save_field(const T& src, const Descriptor& desc, char* buf, size_t cap);

    // Render field via Dear ImGui (returns true if user changed it)
    template <typename T>
    inline bool cfg_render_field(T& field, const Descriptor& desc);

    // Drift-check at boot vs stamp body
    template <typename T>
    inline bool cfg_drift_check(const T& live_value, const T& stamp_value, const Descriptor& desc);
}
```

Each verb has its own type-family guard + `if constexpr` branches. Adding a new verb (e.g., `cfg_diff_for_log`) means writing one new `tt::` function with the same shape; X-macro extractors compose by walking the same registry.

### How Kind enum stays metadata-only

The descriptor's `Kind` enum drives **presentation**, NOT storage:

```cpp
struct Descriptor {
    Kind kind;                  // GUI presentation hint (slider vs textbox; % suffix; clamp coercion)
    uint16_t metadata_flags;
    const char* label;
    const char* tooltip;
    union { /* per-Kind GUI metadata: clamp range, enum labels, etc. */ } payload;
};
```

`KIND_DOUBLE` vs `KIND_DOUBLE_PCT` differ ONLY in GUI presentation (×100 + "%" suffix in render) — both store as `double` (or `FPN_Binary<F>` if the actual field is FPN_Binary). The dispatch's type behavior is identical; only the renderer reads Kind.

This separation is what makes the 3-barrier design sustainable: a future maintainer can add `KIND_DOUBLE_BPS` (basis points; ×10000 + " bps" suffix) without touching the dispatch — just one new render branch keyed on Kind.

---

## Trade-offs + when to apply

### Apply when:
- Building a registry-driven dispatcher (parser, save, render, drift-check) over typed fields
- Field types include any of: template-instantiated types (`FPN_Binary<F>`, custom POD templates), char arrays, mixed scalar + container types
- Multiple verbs dispatch over the same registry (parse + save + render + ...)
- The cost of silent corruption is high (HMAC-signed wire format, byte-equivalent test harness, deterministic backtest)

### Skip when:
- Single dispatcher over single trivial type (e.g., parse 5 boolean cfg flags) — registry overhead exceeds win
- All field types are trivially scalar (double, int) AND will never grow to template-instantiated types — Option A's silent-corruption risk is lower (still ill-advised)
- Field count below registry threshold (CLAUDE.md item 13: ≥3 entries + ≥2 caller sites)

### Cost:
- ~40-80 LOC of `tt::` namespace per verb (one templated function + type-family guard + 4-6 if-constexpr branches)
- ~5 LOC per codebase-specific type trait (`is_fp_binary_v` etc.)
- ~10-20 LOC per X-macro extractor (one per consumer site)
- Caller migration from offsetof to field-by-reference: mechanical find/replace

### Win:
- **Class 23 (type-erased typed-field write) structurally extinct** in well-formed code
- Compile-time type extension forced via static_assert (deliberate decision, not silent slip)
- Decoupling Kind enum from storage type = future GUI variants (KIND_DOUBLE_BPS, KIND_DOUBLE_LOG_SCALE) cost only a render branch
- Composable with all X-macro registry consumer patterns (autopopulate, presence dispatch, pre/post split)
- Reuses standard C++ type traits + codebase-specific traits in a uniform pattern

---

## Reference implementations

### First applied: v5.14.8.A.merged — `tt::stamp_parse_field<T>`

- File: `ML_Headers/StampBoundModelConstRegistry.hpp:86-99`
- Registry: `FOREACH_STAMP_BOUND_MODEL_CONST` (32 entries; 6 groups + standalone)
- Verbs dispatched: parse + emit + AUTOPOPULATE
- Type families covered: `std::is_array_v` (char[16] / char[65]), `std::is_floating_point_v`, `std::is_unsigned_v`, signed integral fallback
- Pattern existed implicitly; codified at v5.15.5.F.4b after Class 23 surfaced

### Codified application: v5.15.5.F.4b — `tt::cfg_parse_field<T>` + `tt::cfg_save_field<T>` + `tt::cfg_render_field<T>`

- File: `CoreFrameworks/CfgFieldDispatch.hpp` (NEW)
- Registry: `FOREACH_CFG_FIELD` (~40 KIND_DOUBLE/_PCT entries at .F.4b; expands through .F.4i to 213+ entries across all kinds)
- Verbs dispatched: parse + save + render + drift-check (the latter via STAMP_BOUND derived filter)
- Type families covered: `is_fp_binary_v` (NEW trait; ~38 of the 40 .F.4b entries are FPN_Binary<F>) + `std::is_floating_point_v` + `std::is_array_v` + `std::is_integral_v`
- Drives the 3-barrier structural fix that closes Class 23

### Future application candidates

- **`tt::feature_compute_field<T>`** (FOREACH_FEATURE) — when feature compute fns gain heterogeneous output types
- **`tt::snapshot_field<T>`** (FOREACH_PER_CORE_SNAP_FIELD; TECH_DEBT-011) — when PerCoreSnap migrates to registry-driven snapshot publish
- **`tt::log_field<T>`** (FOREACH_<LOGNAME>_COL; calibration-log-column-registry.md) — when CSV column writers gain typed-field dispatch
- **`tt::oms_field<T>`** (FOREACH_OMS_FIELD; v5.15.5.C.3 Phase 3b) — already partially structured this way; full migration brings consistency

Pattern composes with: `x-macro-registry-with-presence-dispatch.md` (Y3 dispatch on Kind for metadata; T dispatch via tt:: for storage), `autopopulate-pattern-for-production-caller-class.md` (AUTOPOPULATE companions invoke tt:: helpers under the hood), `wire-format-byte-preservation-discipline.md` (Layer 5b hash test verifies tt:: dispatch produces byte-identical output to manual emit).

---

## Lessons / gotchas

### `if constexpr` branches must be syntactically valid per type — that's why we wrap in templated function

In a non-template context, `if constexpr (false) { strncpy(scalar_var, ...); }` is a HARD compile error (strncpy on non-array). Inside a TEMPLATED function, the per-T instantiation discards the false branches before the syntactic check runs.

This is THE reason `tt::` is a namespace of TEMPLATED functions, not a set of free function specializations. A free `void cfg_parse_field(double&, ...)` + `void cfg_parse_field(int&, ...)` set of overloads would work for SAFE dispatch but loses the type-family guard + composability with new types added later.

### Type-family guard catches the FIRST extension

Adding a new cfg field whose type isn't in the recognized family fails compile at the `static_assert`. The error message names the offending T + tells the contributor exactly what to do (extend `tt::` with a new branch). This is forcing function — the new type can't be silently used; a deliberate dispatch decision is required.

If the static_assert fires and the contributor's reaction is "let me bypass this with reinterpret_cast" — that bypass triggers the audit detection (Class 23). Defense in depth.

### Codebase-specific traits live with the type they describe

`is_fp_binary_v` lives in `FixedPoint/FixedPointN.hpp` next to the `FPN_Binary<F>` primary template. Don't put codebase-specific traits in a central "traits.hpp" — locality with the type makes them discoverable + survives template-class refactors.

If a future template POD type emerges (e.g., `Volume<N>`), define `is_Volume_v` in `Volume.hpp` next to it. Then extend each `tt::cfg_*_field` function with an `else if constexpr (is_Volume_v<T>)` branch. The static_assert reminds contributors at first-use that the family must include the new type.

### Composability with runtime metadata via Kind enum

The dispatch FUNCTION reads T (compile time); the dispatch can ALSO consume runtime metadata from `desc` (the descriptor passed by reference). E.g., `desc.payload.as_double.clamp_min/max` for clamping. This combines compile-time type dispatch with runtime metadata cleanly:

```cpp
if constexpr (is_FPN_v<T>) {
    double v = parse_double_fast(val);
    v = std::clamp(v, desc.payload.as_double.clamp_min, desc.payload.as_double.clamp_max);
    dst = FPN_FromDouble<T::F>(v);
}
```

Both compile-time (type) and runtime (clamp range) information available; no type erasure.

### When the pattern doesn't apply: HOT-path per-tick dispatch

`tt::` dispatch is for SLOW path (parser, save, GUI render, boot drift-check). NOT for hot-path per-tick dispatch where every cycle counts. Hot path uses compile-time elision via `template <bool ENABLED>` + `if constexpr` directly in the function body (per CLAUDE.md item 18(a)) — no template helper indirection.

The patterns are sister: both leverage if-constexpr + template instantiation; one for slow-path type safety, one for hot-path zero-cost elision. Same C++ machinery, different deployment context.

### Migration from existing offsetof-based dispatchers is mechanical

If a codebase has Option A dispatchers today (e.g., v5.14 had stamp body parsing via per-Kind specialization), migration is mechanical:

1. Define type traits for codebase-specific types (`is_fp_binary_v` etc.)
2. Rewrite the dispatcher as `tt::<verb>_field<T>(T& dst, ...)` with type-family guard + if-constexpr branches per T
3. Update X-macro extractors to pass field by reference (`cfg->name`) instead of `offsetof(Cfg, name)`
4. Delete the per-Kind specialization templates
5. Audit grep for any remaining `reinterpret_cast<X*>((char*)Y + Z)` patterns — these need migration too

The migration BUILD-FAILS at the static_assert if any field type isn't covered — forcing exhaustive coverage in one ship rather than incremental drift.

---

## Patterns NOT used here (and why)

### `std::variant` over field types

C++17 variant could store the field reference + dispatch via `std::visit`. Rejected because:
- Adds runtime overhead (variant tag + visit dispatch ~5-10ns per access vs zero-overhead template)
- Opaque to compilers' inlining + optimization
- Harder to extend (each new type adds a variant arm + visit branch)
- Doesn't compose with template-instantiated types (FPN_Binary<F>) cleanly

### `boost::hana` or `boost::mp11` type-list metaprogramming

External metaprogramming libraries can express the dispatch elegantly. Rejected because:
- FoxLIB has zero core dependencies; macros + standard type traits stay in-tree
- The if-constexpr chain is direct + readable; no template-metaprogramming opacity
- Plain C++17 is sufficient for the use case

### Reflection (C++26+)

Future reflection might let dispatchers introspect struct fields automatically without per-T extension. Not yet available; revisit at C++26 adoption.

---

## Cross-references

- `DOCS/RECURRING_BUG_PATTERNS.md` Class 23 — anti-pattern catalog entry; cites this doc as the antidote
- `x-macro-registry-with-presence-dispatch.md` — Y3 dispatch + tt:: caveat (parent doc)
- `autopopulate-pattern-for-production-caller-class.md` — companion macro shape (AUTOPOPULATE invokes tt:: under the hood)
- `wire-format-byte-preservation-discipline.md` — Layer 5b hash test verifies tt:: dispatch byte-equivalence
- `structural-fix-preferred-decision-framework.md` — meta-decision for the 3-barrier shape
- CLAUDE.md item 23 — public statement of "type-trait dispatch via templated helpers"
- CLAUDE.md item 19 — public statement of "structural fix preferred"
- CLAUDE.md item 13 — public statement of "X-macro registry as standard pattern"
- FoxML_Trader_v2 `ML_Headers/StampBoundModelConstRegistry.hpp:86-99` — first reference implementation
- FoxML_Trader_v2 `CoreFrameworks/CfgFieldDispatch.hpp` (v5.15.5.F.4b NEW) — first codified application + 3-barrier integration
