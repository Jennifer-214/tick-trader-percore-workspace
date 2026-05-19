---
type: ledger-template
class_id: 23
title: Type-erased typed-field write via reinterpret_cast through char* offset
parent_index: DOCS/RECURRING_BUG_PATTERNS.md
established: 2026-05-18
surface_tags: [cfg-flow, registry, parser, fixed-point-math]
severity: blocker
recurrence_count: 1
first_instance: v5.15.5.F.4b
closure_mechanism: 3-barrier structural fix (Barrier 1 API surface no void*+offset entry point; Barrier 2 X-macro extractor chokepoint with cfg->name real-field access; Barrier 3 compile-time type-family static_assert in tt::cfg_*_field dispatcher) + H13 hard invariant + /dod-audit + /bug-check registry-driven scan
sister_classes: [11, 14, 16, 18, 21, 25, 27]
---

## Class 23 — Type-erased typed-field write via reinterpret_cast through char* offset

**Surface:** any registry-driven typed-field access (parser, save, render, drift-check, snapshot publish). High-risk when destination field types are template-instantiated (`FPN<F>`, custom POD types) vs trivial scalars (`double`, `int`).

**Symptom:** silent data corruption when writing to typed fields via opaque byte offsets. Parser/save appears to work for cfg roundtrip tests that exercise scalar fields (double, int) but produces garbage when the same code path runs against `FPN<F>`-typed fields. Bug latent in production for any field whose actual type differs from the assumed pun type. Tests that compare struct-field-after-load to struct-field-before-save miss it if they only exercise the trivial-type subset. Catastrophic for backtest determinism + train-serve parity because FPN mantissa words get clobbered while the load+compare-back roundtrip silently agrees within the corrupted 8-byte view.

**Root cause:** the code pattern `*reinterpret_cast<T*>((char*)dst + offset) = value` PUNS the destination address as type T regardless of the actual field type stored there. For 8-byte `double` punned through a 24-byte `FPN<F>` address: writes 8 bytes (double mantissa+exponent) into the first 8 bytes of the FPN's `uint64_t w[2]` storage. The FPN's remaining 16 bytes (second word + sign + padding) keep stale data. Subsequent FPN arithmetic operates on corrupt state → silent precision loss + non-deterministic outputs.

The shape is "type erasure at registry dispatch time": the registry knows the cfg field NAME but not its TYPE; the dispatcher uses Kind enum (DOUBLE/INT/etc.) to drive the type, decoupling it from the actual struct field declaration. When Kind ≠ actual field type, the dispatch silently corrupts.

**Detection:**

```bash
# Find reinterpret_cast through char* offset arithmetic (the anti-shape):
rg "reinterpret_cast<\s*\w+\s*\*>\(.*\(char\s*\*\)|reinterpret_cast<\s*\w+\s*\*>\(\s*reinterpret_cast<\s*char\s*\*>" --type cpp .

# Tighten: cfg/registry dispatch context specifically:
rg "reinterpret_cast<.*>.*\+\s*\w*offset" CoreFrameworks/ ML_Headers/ Strategies/ Backtest/

# Find offsetof + reinterpret_cast pairs (most common anti-form):
rg -B2 "reinterpret_cast<.*\*>" CoreFrameworks/ ML_Headers/ | rg -A2 "offsetof"
```

Audit hooks: `/dod-audit` Stage 6 detection signature; `/bug-check` registry-driven scan picks this up automatically once Class 23 is in the registry.

**Known instances:**

- **2026-05-14 — v5.15.5.F.4b pre-coding audit (CAUGHT BEFORE SHIP).** Plan Step 2 specified `tt::cfg_parse_field<KIND_DOUBLE>` using `*reinterpret_cast<double*>((char*)cfg + cfg_field_offset(name)) = v;` for ~40 KIND_DOUBLE/_PCT cfg fields. ~38 of those 40 fields are actually `FPN<F>` (24 bytes) in `ControllerConfig<F>`. Caught by `/trace-deps` BL-1 (independent finding) and `/merge-scan` #3 (related pattern alignment); reported in `plans/plan_checks/2026-05-14-v5.15.5.F.4b-fresh-audits-synthesis.md`. **Anti-pattern caught at pre-coding gate — zero production occurrences.** Plan amended to use type-dispatch-on-T pattern per Prevention below.

**Prevention — 3-barrier structural fix (extinguishes the class):**

The bug is structurally unreachable when ALL three barriers are in place. Each barrier alone is insufficient; together they make the anti-shape impossible to write accidentally + grep-detectable on intentional bypass.

**Barrier 1 — API surface: no void*+offset entry point exists.** The only `tt::cfg_*_field` overloads take destination by reference; T is deduced. There is NO `tt::cfg_parse_field<KIND>(void* base, size_t offset, ...)` form to invoke.

```cpp
namespace tt {
    template <typename T>
    inline void cfg_parse_field(T& dst, const CfgFieldDescriptor& desc, const char* val);

    template <typename T>
    inline void cfg_save_field(const T& src, const CfgFieldDescriptor& desc, char* buf, size_t cap);

    template <typename T>
    inline bool cfg_render_field(T& field, const CfgFieldDescriptor& desc);
}
```

A new contributor cannot accidentally write the anti-shape because the unsafe symbol doesn't exist. Bypassing requires inventing new infrastructure — grep-detectable.

**Barrier 2 — X-macro extractor is the chokepoint.** The only way to walk a cfg field registry is through extractor macros that follow the canonical shape:

```cpp
#define EMIT_CFG_PARSER_CASE(kind_token, name, label, section, meta, payload, tooltip, \
                              applies_to_strategy, applies_to_op_mode, lives_in) \
    else if (strcmp(key, #name) == 0) { \
        tt::cfg_parse_field(cfg->name, g_cfg_field_descriptors[FIELD_IDX_##name], val); \
    }
FOREACH_CFG_FIELD(EMIT_CFG_PARSER_CASE)
```

`cfg->name` is a real field access; T is deduced from the field declaration. There's no `&((char*)cfg)[offset]` form in the extractor template. New contributors copy the existing shape; the safe form is the only template available.

**Barrier 3 — compile-time type-family guard inside the dispatcher.** The dispatch helper `static_assert`s that T is in a recognized family before any if-constexpr branch:

```cpp
namespace tt {
    template <typename T>
    inline void cfg_parse_field(T& dst, const CfgFieldDescriptor& desc, const char* val) {
        static_assert(is_FPN_v<T>
                   || std::is_floating_point_v<T>
                   || std::is_integral_v<T>
                   || std::is_array_v<T>,
                      "cfg field type not in recognized family — "
                      "extend tt::cfg_parse_field<T> with a new branch before using this T as a cfg field");
        if constexpr (is_FPN_v<T>) {
            double v = parse_double_fast(val);
            v = std::clamp(v, desc.payload.as_double.clamp_min, desc.payload.as_double.clamp_max);
            dst = FPN_FromDouble<T::F>(v);
        } else if constexpr (std::is_floating_point_v<T>) {
            dst = (T)parse_double_fast(val);
        } else if constexpr (std::is_array_v<T>) {
            strncpy(dst, val, std::extent_v<T> - 1);
            dst[std::extent_v<T> - 1] = '\0';
        } else if constexpr (std::is_unsigned_v<T>) {
            dst = (T)strtoull(val, nullptr, 10);
        } else { // signed integral
            dst = (T)atoi(val);
        }
    }
}
```

Adding a cfg field of an unrecognized type **fails the build**. Forces a deliberate decision (extend the dispatcher) rather than silent truncation.

**Required type traits:**
```cpp
// FixedPoint/FixedPointN.hpp
template <typename T> struct is_FPN : std::false_type {};
template <unsigned F> struct is_FPN<FPN<F>> : std::true_type {};
template <typename T> inline constexpr bool is_FPN_v = is_FPN<T>::value;
```

**Plus audit detection** (defense in depth): `/dod-audit` + `/bug-check` scan for any historical or future `reinterpret_cast<X*>((char*)Y + Z)` pattern. Even if a contributor invents a bypass, the audit catches it at the next sub-ship gate.

**Architectural principle:** the Kind enum in the descriptor is **metadata-only** — drives GUI presentation (slider vs textbox, format string, percentage scaling, clamp coercion) but NOT type dispatch. Decouples GUI metadata from storage type. KIND_DOUBLE_PCT vs KIND_DOUBLE differs only in GUI rendering (×100 + "%" suffix), not in how the value is stored. This separation is what makes the 3-barrier design sustainable.

**Related classes:**

- **Class 11** (Extensibility friction causing silent drift) — same "manual integration site drifts from registered list" shape at a different layer
- **Class 14** (Plan calls a function or struct field that doesn't exist) — sibling process class for type-vs-API misalignment at plan-draft time. The CRITICAL-1 (Class 23 origin) + CRITICAL-2 (Class 14 recurrence) findings on v5.15.5.F.4b were detected together — the plan that proposed the anti-shape was the same plan that referenced the wrong API surface. Both stem from "drafted under imperfect API knowledge."
- **Class 16** (Naming convention drift breaks X-macro dispatcher) — both are "dispatcher behaves wrong when assumed mapping fails" at different points. Class 16 is name → bit-position; Class 23 is name → type.
- **Class 18** (Mirror-incomplete) — both are "looks correct at compile time; corrupts at runtime" failure shape.
- **Class 21** (Multiple parallel descriptors) — sibling cfg-surface class; the CfgFieldDescriptor unification (single descriptor + lives_in_struct discriminator) eliminated Class 21 at the same architectural ship as Class 23's structural fix.

**Cross-references:**

- CLAUDE.md item 23 (type-trait dispatch via templated helpers) — base pattern
- CLAUDE.md item 19 (structural fix preferred when bug class can recur) — meta-pattern motivating the 3-barrier design
- `DESIGN_SPECS/framework-patterns/x-macro-registry-with-presence-dispatch.md` § "Y3 dispatch caveat re: if-constexpr in non-template context" — sister concern at the macro-dispatch layer
- `DESIGN_SPECS/framework-patterns/type-trait-dispatch-via-tt-namespace.md` (NEW 2026-05-14) — dedicated antidote pattern doc; canonical reference implementation at `tt::stamp_parse_field<T>` in `ML_Headers/StampBoundModelConstRegistry.hpp:86-99`
- `DESIGN_SPECS/meta-disciplines/structural-fix-preferred-decision-framework.md` — meta-decision to apply 3-barrier structural fix vs direct patch
- `plans/plan_checks/2026-05-14-v5.15.5.F.4b-fresh-audits-synthesis.md` — full audit synthesis that surfaced the class
