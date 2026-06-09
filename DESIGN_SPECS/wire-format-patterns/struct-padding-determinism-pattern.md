---
type: wire-format-pattern
stage: 5-claude-md
version: 1.0
established: 2026-05-11
tags: [wire-format, data-oriented-design, fixed-point-math]
surface: [wire-format]
sister_specs: [wire-format-byte-preservation-discipline.md, struct-padding-determinism-pattern.md, branchless-math-kernel-pattern.md]
applies_at_skills: [/parity-check]
---

# Struct padding determinism pattern (explicit zero-init padding fields)

**Established:** 2026-05-11 (v5.14.11.B — FPN<F=64> canonical first reference)
**Status:** ACTIVE
**Cross-references:**
- First reference application: `FixedPoint/FixedPointN.hpp::FPN<F>` (v5.14.11.B.2)
- Sister patterns: `wire-format-byte-preservation-discipline.md` (HMAC byte preservation; related byte-equivalence concern); `avx512-byte-determinism-pattern.md` (deterministic-bytes-across-binaries philosophy)
- CLAUDE.md item 12 (Display ↔ execution invariant — relies on snapshot byte determinism)
- CLAUDE.md item 15 (Parity-tested-by-construction)
- CLAUDE.md item 27 (Structs used in byte-equivalence contexts have explicit zero-init padding)
- CLAUDE.md item 19 (Structural fix preferred when bug class can recur)

---

## Problem statement

C/C++ structs frequently contain implicit padding bytes to satisfy alignment requirements.

> [!NOTE]
> **The FPN worked example below is HISTORICAL.** It documents the original sign-magnitude `FPN<F=64>` layout (24B: `uint64_t w[2]` + `int32_t sign` + `int32_t _padding`) that motivated this pattern. **Ship-A (tag `v5.15.5.F.4d.1.E.0.7`) SUPERSEDED that layout** — `FPN<F=64>` is now a bare two's-complement `__int128 v` (16 bytes, sign in the top bit, NO sign field, NO padding). FPN therefore no longer needs the `_padding` trick: it has **no padding at all**, so the determinism comes for free. The example is preserved because the **general H12 padding-determinism pattern still applies to any OTHER struct with implicit padding** (see § "The pattern (concrete shape)"). Read the FPN specifics as the origin story; read the pattern as the durable lesson.

Example (historical, pre-Ship-A FPN layout): `FPN<F=64>` was:

```cpp
// HISTORICAL — pre-Ship-A sign-magnitude layout, sizeof 24 (superseded by the 16B __int128).
template <unsigned FRAC_BITS> struct FPN {
    uint64_t w[N];        // the magnitude array: 16 bytes (N=2 at FRAC_BITS=64); 8-byte aligned
    int32_t  sign;        // 4 bytes
    // 4 bytes IMPLICIT PADDING to round struct size to 8-byte multiple
};
// sizeof(FPN<64>) = 24 (16B w[2] + 4B sign + 4B padding); NOT the 16B of the current __int128 core
```

The 4 padding bytes after `sign` were **UB unless explicitly initialized**. Two FPN<64> values with identical `w[]` + `sign` could have DIFFERENT padding bytes (whatever was on the stack at construction time).

**Consequences:**

1. **`memcmp` comparison fails** for two structs with same VALUES (e.g., `memcmp(&fpn_a, &fpn_b, sizeof(fpn_a))` returns non-zero even when fpn_a and fpn_b represent the same number)
2. **SHA-256 / hash byte input non-deterministic** — same input produces different hash bytes
3. **Wire format / serialization non-deterministic** — same logical struct serializes to different bytes across runs
4. **Test failures are EXTREMELY HARD to diagnose** — same code, same input, different result; varies with stack layout changes (compiler version, optimization flags, surrounding function changes)

**Recurring case (v5.14.11.B trigger):** During v5.14.11.B implementation, adding ~600 bytes to `RidgeWeights<F=64>` shifted stack layout in functions calling FPN operations. The `tests/controller_test.cpp:19524 "v5.14.5.C: same input → bytewise identical FracDiff"` test (which had been passing) suddenly FAILED. Root cause: FPN<F=64> uninit-padding bytes were now leaking through stack with different values in two FPN locals being compared via `memcmp`. The bug was LATENT for months; only surfaced when stack layout changed.

This bug class (uninit struct padding exposed by stack-layout shifts) is highly recurrent — any struct with implicit padding can manifest the bug under the right conditions. Structural fix needed.

---

## Design space explored

### Option A: Explicit `_padding = 0` field (CHOSEN)

```cpp
template <unsigned FRAC_BITS> struct FPN {
    uint64_t w[N];
    int32_t  sign;
    int32_t  _padding = 0;  // explicit; deterministic
};
```

✓ 1-line struct change. ✓ Same struct size (24B; padding was already there implicitly). ✓ All FPN operations work unchanged (no API change). ✓ Default member initializer guarantees `_padding = 0` for every new FPN<F> instance. ✓ Standard C++ copy-construction preserves `_padding` correctly (memcpy semantics). ✓ Future operations + future copies automatically get correct padding.

**Trade-off:** struct becomes non-trivially-default-constructible (has user-provided default init). Other members (w[]/sign) are unaffected — they remain uninit by default; only `_padding` gets the explicit 0. For most uses this is irrelevant; matters only for `is_trivially_default_constructible_v<FPN<F>>` type traits checks.

### Option B: Change `int32_t sign` to `int64_t sign`

```cpp
struct FPN {
    uint64_t w[N];        // 16 bytes
    int64_t  sign;        // 8 bytes — eliminates padding entirely
};
// sizeof(FPN<64>) = 24 (unchanged); no padding
```

✓ Eliminates padding entirely. ✗ Implicit narrowing warnings on `int32_t x = fpn.sign;` consumer sites under `-Werror=conversion`. ✗ Requires ~67 consumer-site reviews for narrowing safety. **Heavier blast radius.**

### Option C: Pack sign into w[N-1] high bit (deeper representation refactor)

✓ Eliminates the sign field entirely. ✗ Multi-week refactor; touches every FPN math operation; rebaselines every PARITY contract. **Out of bug-fix scope; tracked as TECH_DEBT-034b.**

### Option D: Fix the FAILING TEST to compare field-by-field

✓ Smallest scope. ✗ Bug class persists; any future test relying on byte-comparison will hit the same issue. **Defers debt; rejected.**

### Option E: Use `memset(&fpn, 0, sizeof(fpn))` before every FPN_Add / FPN_Mul return

✓ Per-op zero-init. ✗ Requires touching every FPN operation; easy to forget; recurring discipline. **REJECTED per CLAUDE.md item 19 (structural fix preferred).**

**Option A wins** on the structural-fix + minimal-blast axis. The pattern then GENERALIZES to other structs with implicit padding.

---

## The pattern (concrete shape)

### Generic template

For any struct used in a byte-equivalence context (memcmp / SHA-256 / wire format / hash):

```cpp
struct DataBearing {
    TYPE_A field_a;       // N_a bytes
    TYPE_B field_b;       // N_b bytes
    // ...
    
    // Explicit padding to round to alignof(struct). One field per padding gap.
    int_<N>_t _padding_N = 0;
};
```

Padding fields are named `_padding<N>` (or `_padding` if only one). Type chosen to fill the gap: `int8_t` for 1B, `int16_t` for 2B, `int32_t` for 4B, etc. Default value `= 0` ensures determinism.

### Identifying implicit padding

For any struct, compute:

```
sizeof(struct) - sum(sizeof(member))
```

If non-zero, there's implicit padding. Common pattern: `int32_t sign` after `uint64_t w[N]` adds 4 bytes of padding to satisfy 8-byte alignment.

Tools: `__builtin_offsetof(struct, field)` + `sizeof(struct)` reveal layout. `clang -Xclang -fdump-record-layouts` produces explicit layout dumps.

### When NOT to add explicit padding

- Struct is private to one translation unit + never compared bytewise → padding irrelevant
- Struct is intentionally non-trivial (already has user constructors that zero everything)
- Struct's byte layout is hardware-defined (e.g., DMA buffer; padding is meaningful) — different concern; handle via `#pragma pack` or `__attribute__((packed))` separately

### Coexistence with `#pragma pack` / `__attribute__((aligned))`

Explicit padding fields integrate fine with packing pragmas + alignment attributes. The padding field has its own size + alignment; the struct's total alignment respects all members.

For `alignas(N) struct X { ... };`, padding fields still work — they fill gaps inside the struct; the `alignas` only affects the struct's external alignment.

---

## Trade-offs + when to apply

### Apply when:

- Struct will be compared via `memcmp`, hashed via SHA-256, serialized to wire format, used as HMAC input, or otherwise byte-equivalence-sensitive
- Struct has fields of mixed sizes/alignments creating implicit padding
- The struct is touched by code with stack-layout sensitivity (function returns, struct copies through generic templates)
- Future struct evolution should preserve byte-determinism

### Skip when:

- Struct is a one-off internal type with no byte-comparison usage
- Struct is intentionally byte-packed (already no padding)
- Struct has a non-trivial constructor that already zero-initializes everything (verify; many "trivial" constructors don't)

### Cost:

- Per affected struct: 1 line per padding gap (typically 1-2 lines total)
- Code review burden: minimal — explicit padding is self-documenting
- Compile time: trivially small
- Runtime: zero — padding is data, not code

### Win:

- **Bug class structurally extinct** — uninit padding cannot leak through `memcmp` / hash / serialize
- **Diagnostic clarity** — struct shape is self-documenting; future contributors see padding explicitly
- **Stable under stack-layout shifts** — adding fields elsewhere can't expose the bug
- **Test reliability** — `memcmp(&a, &b, sizeof(a))` is a valid value comparison after this fix
- **Reusable pattern** — applies to ALL byte-equivalence-sensitive structs in the codebase

---

## Reference implementations

### v5.14.11.B.2 — FPN<F> (canonical first reference) — SUPERSEDED by Ship-A

> [!NOTE]
> **This FPN application was later SUPERSEDED.** Ship-A (tag `v5.15.5.F.4d.1.E.0.7`) flipped `FPN<F=64>` to a bare two's-complement `__int128 v` (16 bytes, no `sign` field, no `_padding` field). The `_padding = 0` trick recorded below no longer exists in `FPN<F>` — the 16B `__int128` has **no padding at all**, so determinism is structural. The entry is preserved as the historical first canonical reference; the general pattern remains valid for other padded structs.

`FixedPoint/FixedPointN.hpp::FPN<F>` (historical). Added `int32_t _padding = 0;` after `int32_t sign`. Same struct size (24B at F=64; was 24B with implicit padding). FracDiff `same input → bytewise identical` test now passed reliably regardless of stack-layout shifts.

Verified at the time: all 92 FPN core operation tests pass; all 67 consumer-site usages of `.sign` unaffected.

### Future application candidates (audit findings)

Audit pending in v5.14.11.B.0 for other structs in the codebase:

- `BanditState` (BanditLearning.hpp) — verify no implicit padding (or add)
- `ThompsonBanditState` (ThompsonBandit.hpp) — verify
- `PredictionRecord` (CoreModelZoo.hpp) — verify
- `PerCoreSnap` fields used in snapshot byte comparison — verify
- `RollingStats` instances — verify
- Any struct returned by value through a function (return-value optimization can preserve padding bytes from constructor's stack frame)

`/dod-audit` skill enforcement (added in v5.14.11.B.5) catches new struct additions that violate the pattern.

---

## Lessons / gotchas

### Default member initialization makes struct non-trivially-default-constructible

`int32_t _padding = 0;` is a **user-provided default initializer**. This changes the struct's trait classification:

- Before: `is_trivially_default_constructible_v<FPN<F>> == true` → `FPN<F> x;` leaves entire struct uninit (including padding)
- After: `is_trivially_default_constructible_v<FPN<F>> == false` → `FPN<F> x;` calls implicit constructor → initializes `_padding = 0`; other members STILL uninit (only the field with explicit init is initialized)

For most uses this is irrelevant. Matters only for:
- `std::aligned_storage` / `placement new` patterns that assume trivial default
- Type-trait dispatching on `is_trivially_default_constructible`
- `static_assert(std::is_trivially_default_constructible_v<...>)` checks

The struct remains:
- `is_trivially_copyable_v<...> == true`  ✓ (memcpy semantics preserved)
- `is_standard_layout_v<...> == true`     ✓ (offset arithmetic still valid)
- Naturally aligned                       ✓ (no change)

For FPN specifically: no codebase usage triggers trivial-default-constructible checks. Safe migration.

### Copy semantics preserve padding correctly

C++ `struct X x = some_x;` (copy-construction) and `struct X x; x = some_x;` (assignment) use member-wise copy that **DOES include `_padding`**. The destination gets `_padding = some_x._padding` (i.e., `= 0` if the source's `_padding` was correctly initialized).

This works because `_padding` is a real field (no special exemption from copy semantics).

### Default member init runs only at FIRST construction

```cpp
FPN<F> a;           // a._padding = 0 (default member init runs)
a.w[0] = 42;        // a._padding still 0
FPN<F> b = a;       // b._padding = 0 (copy from a's _padding which is 0)
FPN<F> c;           // c._padding = 0 (default member init runs again for c)
```

No need to manually re-initialize `_padding` after each operation. Default member init runs at every fresh construction.

### Padding field must be initialized to zero (not just declared)

```cpp
int32_t _padding;       // ✗ NO. Implicit constructor doesn't init; still UB.
int32_t _padding = 0;   // ✓ YES. Default member init makes it 0.
int32_t _padding{};     // ✓ YES (C++11 brace-init; equivalent to = 0 for primitives).
```

The `= 0` is load-bearing. Without it, the field exists but is uninit; same UB as before.

### Verify struct size unchanged after migration

Guard the post-migration struct size with a `static_assert` so a future field addition can't silently reintroduce (or shift) padding:

```cpp
// General technique — pin the size of ANY padded struct after migration:
static_assert(sizeof(SomePaddedStruct) == EXPECTED_BYTES, "size must stay fixed");
```

Add to test suite. Catches accidental size changes (e.g., from a future field addition).

> [!NOTE]
> **The original FPN-specific worked example is OBSOLETE.** It read:
> ```cpp
> static_assert(sizeof(FPN<F=64>) == 24, "FPN<F=64> struct size must remain 24 bytes");  // pre-Ship-A
> ```
> Ship-A (tag `v5.15.5.F.4d.1.E.0.7`) flipped `FPN<F=64>` to a bare `__int128 v` — it is now **16 bytes with no `_padding` field**, so this 24-byte / `_padding`-determinism assertion no longer applies to FPN (the live guard is `sizeof(FPN<F=64>) == 16`). The **general technique above is still valid** for any other struct that uses the explicit-`_padding` pattern.

### Wire format / serialization compatibility

If the struct is serialized to disk / network as raw bytes (uncommon but possible), the byte layout MUST match across producers + consumers. Adding `_padding = 0` doesn't change the BYTE LAYOUT (padding was already there); it just makes the padding bytes DETERMINISTICALLY 0 instead of UB.

Producers and consumers that previously worked despite UB padding (e.g., both happened to read the same bytes) now have a stable contract: padding bytes are 0. This is an improvement, not a regression.

### Field reordering doesn't help

Reordering fields to put smaller types first could ELIMINATE the padding gap (e.g., `int32_t sign` before `uint64_t w[N]` makes `sign` the first field with 4 bytes followed by 4 bytes of padding BEFORE w[]; but this just moves the padding, doesn't eliminate it; struct size stays 24B).

Adding the explicit `_padding = 0` after the existing layout is the safer fix (preserves field order; doesn't shift offsets that other code might depend on).

---

## Audit detection

`/dod-audit` should flag STRUCTS that:

- **Symptom 1:** `sizeof(T) > sum_of_member_sizes(T)` AND `T` is used in `memcmp` / `sha256_bytes` / `hmac_*` / wire format → flag as missing explicit padding field
- **Symptom 2:** struct has mixed-alignment members (e.g., `uint64_t` followed by `int32_t` followed by nothing) → flag as having likely-implicit-padding gap
- **Symptom 3:** struct is returned by value through a function AND consumer compares via `memcmp` → flag as latent regression risk

When detected → recommend Option A migration per this pattern. Cross-reference to first-reference application in FPN<F>.

---

## Patterns NOT used here (and why)

### `__attribute__((packed))` to eliminate padding

Forces alignment-1 packing. ✗ Slower memory access (unaligned loads). ✗ Some platforms reject misaligned access entirely. ✗ Most cases want correct alignment + deterministic padding, not no padding. **REJECTED for general use.** Acceptable for hardware-defined byte layouts (DMA buffers, network packets).

### `#pragma pack` (MSVC-style)

Same as `__attribute__((packed))` problems. **REJECTED for the same reasons.**

### `memset(this, 0, sizeof(*this))` in constructor

✓ Zero-inits ALL bytes including padding. ✗ Requires user-defined constructor (struct no longer aggregate). ✗ Penalty even when caller will overwrite all fields immediately. ✗ Doesn't generalize cleanly across templated structs (FPN<F> has variable size depending on F). **Heavier than Option A.**

### `std::bit_cast` to convert struct ↔ byte array

✓ Validates trivially-copyable + same-size requirements. ✗ Doesn't solve uninit padding problem (still uninit). **Not applicable.**

### Wrap structs in `std::aligned_storage<sizeof(T), alignof(T)>` + placement new

✓ Some control over construction. ✗ Wildly heavier than `_padding = 0`. ✗ Type traits change in ways callers must accommodate. **REJECTED.**

---

## Cross-references

- `wire-format-byte-preservation-discipline.md` — sister concern (HMAC chain byte preservation)
- `avx512-byte-determinism-pattern.md` — adjacent philosophy (cross-binary byte determinism)
- `structural-fix-preferred-decision-framework.md` — decision framework (this pattern is the structural fix for uninit-padding bug class)
- FoxML_Trader_v2 `CLAUDE.md` item 12 — Display ↔ execution invariant (relies on snapshot byte determinism)
- FoxML_Trader_v2 `CLAUDE.md` item 15 — Parity-tested-by-construction
- FoxML_Trader_v2 `CLAUDE.md` item 27 — explicit zero-init padding (this pattern codified)
- FoxML_Trader_v2 `FixedPoint/FixedPointN.hpp::FPN<F>` v5.14.11.B.2 (canonical first reference)
- C++ standard [class.mem] — struct layout + padding semantics
- C++ standard [dcl.init] — default member initializer semantics
- FracDiff regression test `tests/controller_test.cpp:19524` (the test that exposed the latent bug; preserved as canonical regression detector)
- v5.14.11.B subplan: `plans/v5.14-foxml-port-and-maker/subplans/2026-05-11-v5.14.11.B-branchless-math-mega-bundle.md`
- Caramel framing 2026-05-11: *"for the FPN, what is your reccomended solution? what fits with the design philosophy i have? like we deviated and now we introcued issues"* — provided the impetus for codifying this structural fix as a reusable pattern
