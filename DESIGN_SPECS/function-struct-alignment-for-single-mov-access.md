---
type: data-discipline
stage: 3-first-canonical
version: 1.0
established: 2026-05-13
tags: [data-oriented-design, latency-discipline]
surface: [hot-path, slow-path]
sister_specs: [cache-layout-discipline-for-hot-side-structs.md, decision-first-cluster-layout-pattern.md, cache-line-discipline.md, hot-side-array-element-alignment-for-sparse-access.md]
applies_at_skills: []
---

# Function-struct alignment for single-mov field access

**Established:** 2026-05-13 (v5.15.5.C.4 pre-coding consult)
**Status:** ACTIVE (NEW spec; first canonical application = v5.15.5.C.4 DrainerConstants + extended FillRecord layout discipline)
**Cross-references:**
- CLAUDE.md item 5 (lock-free / no-virtual discipline; sister rule for hot path)
- CLAUDE.md item 11 (RAII destructor exception; orthogonal — destructor vs field access)
- CLAUDE.md item 27 (struct-padding-determinism; sister — padding correctness for byte-equivalence)
- CLAUDE.md item 28 (latency-vs-cache framework; cache-miss cost amplifies broken-discipline)
- `cache-layout-discipline-for-hot-side-structs.md` (sister; about HOT/WARM/COLD cluster placement)
- `struct-padding-determinism-pattern.md` (sister; padding correctness)
- `latency-vs-cache-decision-framework.md` (sister; cost framework)

---

## Problem statement

There's an implicit assumption pervading the codebase that `state->field` compiles to a single `mov` instruction. Most of the time it does — but ONLY when 5 prerequisites hold simultaneously. When ANY of them silently breaks, accesses turn into multi-instruction sequences (unaligned-split loads, indirect indirections, ABI-required shuffles, virtual-table lookups) — adding 1-10 cycles per access AND defeating branchless / cache-discipline work.

This spec captures the 5 prerequisites + provides a verification recipe + flags common pitfalls so the discipline can be enforced at design time, not discovered at profile time.

---

## The 5 prerequisites for single-`mov` field access

A field access compiles to a single `mov` (or equivalent — `movsd` for double, `movzx` for narrow → wide, etc.) when **ALL FIVE** of these hold:

### 1. Struct passed by reference (or by value if small + same TU)

```cpp
// GOOD — single mov via base-register + constant-offset addressing
void consumer(const DrainerConstants& dc) {
    double r = dc.fee_rate_taker_d;  // → movsd xmm0, [rdi + 0]
}

// BAD — pointer-to-pointer adds an extra indirect load
void consumer(const DrainerConstants** dc) {
    double r = (*dc)->fee_rate_taker_d;  // → mov rax, [rdi]; movsd xmm0, [rax + 0]
}

// MIXED — by value works only if struct fits in 1-2 registers (≤16B on x86_64 SysV)
//   For larger structs, the ABI requires stack copy → multi-instruction prologue
void consumer(DrainerConstants dc) {  // 24B → forced to memory via stack copy
    double r = dc.fee_rate_taker_d;
}
```

**Rule:** Pass structs ≥ 16B by `const T&`. Structs ≤ 16B by value are fine (ABI passes in registers).

### 2. Field at natural alignment within the struct

A field is **naturally aligned** when its offset is divisible by its size requirement (8B for double / uint64_t; 4B for int / uint32_t; 2B for uint16_t; 1B for uint8_t). When it isn't, the compiler emits **unaligned load** instructions (`movsd` becomes `movsd` with potential split-load penalty; some architectures emit two-instruction sequences).

```cpp
// BAD — bool at offset 0 forces 7B middle pad before double
struct BadLayout {
    bool   flag;       // 1B @ offset 0
    char   _pad[7];    // 7B WASTED in middle
    double value;      // 8B @ offset 8
};

// GOOD — size-descending order; trailing pad becomes growth slack
struct GoodLayout {
    double value;      // 8B @ offset 0 (naturally aligned)
    bool   flag;       // 1B @ offset 8
    char   _pad[7];    // 7B trailing slack
};
```

**Rule:** Order fields by alignment requirement descending (largest first). Trailing pad becomes reusable for future fields without growing struct size.

### 3. Struct itself naturally aligned in memory

A struct living on the stack, in an `alignas` array, or in a heap allocation from `aligned_alloc(64, ...)` is at a known address modulo 64 (or 8, or 16). Fields then live at known absolute addresses. If the struct's BASE is misaligned (e.g., randomly placed in a `malloc()` slab, or straddles a cache line), even naturally-aligned-within-struct fields may straddle cache lines.

```cpp
// GOOD — alignas(64) guarantees struct base on cache-line boundary
struct alignas(64) HotState { ... };

// GOOD — implicit alignment from largest field (8B for double); sufficient for non-SIMD
struct WarmState { double a; double b; int c; };  // gets 8B alignment

// GOOD — heap allocation via aligned_alloc
auto* state = (HotState*)aligned_alloc(64, sizeof(HotState));

// BAD — heap allocation via malloc; alignment = malloc's default (typically 16B on x86_64)
//   Fine for non-SIMD scalars; BAD for cache-line-aware structs
auto* state = (HotState*)malloc(sizeof(HotState));  // base may not be 64B-aligned

// BAD — struct embedded in a packed parent struct (rare but possible)
struct __attribute__((packed)) Parent {
    int header;       // 4B
    HotState body;    // alignment forcibly reduced to 1B!
};
```

**Rule:** Use `alignas(N)` explicitly when discipline matters (HOT-side structs; cache-line-aware structs). For SIMD-friendly layouts, use `alignas(64)` (full cache line) or `alignas(32)` (AVX2-register).

### 4. Compile-time-resolved offset (struct visible to consumer)

For the compiler to fold `dc.fee_rate_taker_d` into a constant offset, the struct definition MUST be visible to the consumer at compile time. This means:
- Struct defined in a header
- Consumer is a `inline` function in the same header (or otherwise has the definition)
- OR aggressive LTO (compiler can resolve via cross-TU info)

```cpp
// GOOD — struct + consumer both in header (canonical pattern for this codebase)
// MemHeaders/DrainerConstants.hpp
struct DrainerConstants { double fee_rate_taker_d; ... };
inline double get_fee(const DrainerConstants& dc) { return dc.fee_rate_taker_d; }

// BAD — struct in .cpp; consumer in .hpp; offset NOT folded until LTO
//   At -O2 without LTO: consumer goes through generic accessor → indirect call
```

**Rule:** Headers-only (`.hpp`) for any struct + consumer pair where single-mov access matters. Aligned with this codebase's existing C-style-with-templates convention.

### 5. No virtual dispatch / function-pointer dispatch

Virtual table lookups + function-pointer indirections defeat offset folding (the consumer may not be the inlined-version; field offset computation goes through generic dispatch).

```cpp
// BAD — virtual function: consumer offset depends on runtime vtable
struct IConsumer {
    virtual double get_value(const DrainerConstants& dc) const = 0;
};
struct ConcreteConsumer : IConsumer {
    double get_value(const DrainerConstants& dc) const override { return dc.fee_rate_taker_d; }
    // VTBL lookup: mov rax, [vtable_ptr]; call [rax + idx*8]; access offset folded only inside concrete
};

// BAD — function-pointer in registry dispatcher (common in X-macro setups)
struct Handler { void (*fn)(const DrainerConstants&); };
void dispatch(Handler h, const DrainerConstants& dc) { h.fn(dc); }
// indirect call defeats inlining of dc.fee_rate_taker_d access

// GOOD — pure function or templated dispatch
template <typename Consumer>
inline void dispatch(const DrainerConstants& dc, Consumer c) { c(dc); }
// Templated consumer = compile-time-resolved; access folded to mov
```

**Rule:** No virtual / function-pointer dispatch in hot or slow path. Use templated dispatch (CRTP, lambda inline, X-macro expansion) when polymorphism is needed. Aligns with CLAUDE.md item 5.

---

## Verification recipe

After implementing a struct + consumer pair, verify the access compiles to single mov:

```bash
# 1. Compile with optimization + debug symbols (for symbol resolution)
g++ -O2 -g -c -fno-omit-frame-pointer my_consumer.cpp -o my_consumer.o

# 2. Disassemble the relevant function
objdump -d -M intel --disassembler-options=intel-mnemonic my_consumer.o \
  | awk '/<Consumer_get_value/,/^[[:space:]]*$/'

# 3. Look for the field access — should be a single mov with constant offset
#    PASS:  movsd xmm0, QWORD PTR [rdi+0x0]
#    FAIL:  mov rax, QWORD PTR [rdi]; movsd xmm0, QWORD PTR [rax+0x0]  (double indirection)
#    FAIL:  call <_Znwm>                                                  (heap allocation in path)
#    FAIL:  mov rax, QWORD PTR [rdi+0x0]; lea rcx, [rax+0x0]; ...        (offset NOT constant-folded)
```

For struct-size verification (catches accidental size growth):
```cpp
static_assert(sizeof(DrainerConstants) == 24, "DrainerConstants size changed");
static_assert(alignof(DrainerConstants) == 8, "DrainerConstants alignment changed");
static_assert(offsetof(DrainerConstants, fee_rate_taker_d) == 0, "fee_rate_taker_d moved");
```

---

## Common pitfalls + counter-examples

### Pitfall 1: bool / small fields first

```cpp
// BAD — 7B middle pad waste; sub-optimal for both space AND access (bool load + 7B gap before next aligned field)
struct Wasteful {
    bool   flag;
    double value;
    int    count;
};

// FIX — reorder descending
struct Optimal {
    double value;
    int    count;
    bool   flag;
    uint8_t _pad[7];  // explicit trailing pad (per struct-padding-determinism-pattern)
};
```

### Pitfall 2: Inheriting from non-empty base

```cpp
// BAD — inheritance forces base layout first; field offsets shift
struct Base { int header; };
struct Derived : Base { double value; };  // value at offset 8 (after Base's 4B + 4B pad)

// FIX — composition over inheritance for layout-discipline structs
struct Composed {
    int    header;       // 4B
    int    _pad;         // 4B alignment for next 8B field
    double value;        // 8B
};
```

### Pitfall 3: Cache-line straddle in array

```cpp
// BAD — 24B record not cache-line-aligned; record N+2 straddles cache line N→N+1
struct Record { double a, b, c; };  // 24B
Record arr[16];  // 384B; record 2 starts at offset 48 → cache line 0 (24B) + line 1 (24B+8B)

// FIX 1 — alignas(64) per record (explicit padding to cache line)
struct alignas(64) Record { double a, b, c; uint8_t _pad[40]; };  // 64B per record

// FIX 2 — accept straddle if records are read densely (prefetcher handles)
// + add static_assert to catch accidental size changes
struct Record { double a, b, c; };
static_assert(sizeof(Record) == 24, "Record size changed; cache analysis may be stale");
```

### Pitfall 4: Function-pointer dispatch in registry walk

```cpp
// BAD — registry of handlers via function ptrs; indirect call per row
struct CfgHandler { const char* key; void (*parse)(Cfg&, const char*); };
CfgHandler handlers[] = { {"foo", parse_foo}, {"bar", parse_bar}, ... };
for (auto& h : handlers) if (strcmp(h.key, k) == 0) h.parse(cfg, val);
// indirect call (h.parse) defeats inlining

// FIX — X-macro registry expanded at compile time (canonical pattern in this codebase)
#define FOREACH_CFG_HANDLER(X) \
    X("foo", parse_foo)        \
    X("bar", parse_bar)
#define DISPATCH(key, fn) if (strcmp(k, key) == 0) fn(cfg, val);
FOREACH_CFG_HANDLER(DISPATCH)
// each X-expansion is direct inlined call; per-row offset folded
```

### Pitfall 5: Forgetting `inline` on header consumer

```cpp
// BAD — consumer defined in header but not inline; ODR violation OR multi-TU duplicates
// my_consumer.hpp
double get_fee(const DrainerConstants& dc) {  // missing 'inline'
    return dc.fee_rate_taker_d;
}

// FIX — explicit inline
inline double get_fee(const DrainerConstants& dc) {
    return dc.fee_rate_taker_d;
}
// OR static (for free functions; ODR-safe by name mangling)
static inline double get_fee(const DrainerConstants& dc) { ... }
```

---

## Application checklist

Before declaring a struct + consumer pair "single-mov-disciplined", verify:

- [ ] Struct passed by `const T&` (or by value if ≤ 16B)
- [ ] Fields ordered size-descending; alignment requirements met for each field
- [ ] `alignas(N)` set explicitly for HOT-side structs (cache-line discipline)
- [ ] Trailing pad fields explicit (per `struct-padding-determinism-pattern.md`)
- [ ] `static_assert(sizeof(T) == expected)` + `static_assert(alignof(T) == expected)` + `static_assert(offsetof(T, field) == expected)` for key invariants
- [ ] Consumer is `inline` in a header that includes the struct definition
- [ ] No virtual / function-pointer dispatch in the access path
- [ ] Spot-check ASM via `objdump -d` — single mov per field access (or movsd / movzx / etc. equivalent)

---

## Trade-offs + when to relax

**Apply the full discipline when:**
- Struct is on hot path or in slow-path inner loops (drainer body, EventLoop_OnEvent, ExecutionCore_Tick)
- Struct is cross-thread-accessed (cache-line discipline + alignment matters for false-sharing)
- Struct participates in byte-equivalence tests (HMAC, SHA-256, memcmp)
- Struct is in a registry-driven X-macro expansion (offset folding cascades through all fields)

**Relax when:**
- One-off configuration struct read at boot only (parser sits at boot; perf irrelevant)
- Struct used only in tests / non-production code
- Struct under active refactor (verify discipline after refactor settles)

For one-off boot/test structs, size-descending is still a free habit. Skip the `alignas(N)` + `static_assert` discipline; pickup later if struct gets promoted to hot path.

---

## Related spec for the array case

The 5 prerequisites above cover SINGLE-ELEMENT struct access. When the struct lives in an ARRAY and hot path iterates sparsely (bitmap-driven, subset-of-fields per element), additional alignment discipline applies. See `hot-side-array-element-alignment-for-sparse-access.md` (v5.15.5.C.5) — the sister spec extending prerequisite 3 (struct itself naturally aligned in memory) to the array-element-level guarantee via `alignas(64)` so that each `arr[N]` starts on a cache-line boundary.

## Cross-references to CLAUDE.md

This pattern complements + reinforces:

- **Item 5 (no-virtual / lock-free):** virtual dispatch defeats prerequisite 5; same rule different framing
- **Item 11 (RAII destructor exception):** destructor field access still requires prerequisites 1-5 to compile to single mov; destructor presence doesn't itself break the discipline (only the field access pattern matters)
- **Item 27 (struct padding determinism):** sister rule for padding correctness; sizes need to match for both byte-equivalence + ASM-predictability
- **Item 28 (latency-vs-cache framework):** prerequisite 3 (struct alignment) gates whether accesses cost 1 or 3 cycles per cache-line straddle

Promotion candidate to CLAUDE.md as item 29 after 2+ canonical applications shipped (v5.15.5.C.4 DrainerConstants + extended FillRecord layout = first application).

---

**End of spec.**
