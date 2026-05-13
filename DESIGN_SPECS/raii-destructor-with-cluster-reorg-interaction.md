# RAII destructor with cluster reorg interaction (when can you reorganize the fields of a struct that has a destructor?)

**Established:** 2026-05-13 (codification triggered by v5.15.5.C.1 audit of OrderManagerState — first cluster-reorg of a struct in this codebase that has a non-trivial RAII destructor)
**Status:** ACTIVE
**Cross-references:**
- Parent rule: `cache-layout-discipline-for-hot-side-structs.md` (Rule 4 HOT/WARM/COLD reorg)
- Sister: `decision-first-cluster-layout-pattern.md` (ND3 — intra-cluster ordering)
- FoxML_Trader_v2 CLAUDE.md item 11 (RAII destructor exception note)
- FoxML_Trader_v2 `CoreFrameworks/OrderManager.hpp:415-417` (canonical first reference application)

---

## Problem statement

CLAUDE.md (`Code Conventions`) says "C-style with templates, no classes" with one explicit exception: **RAII destructors on resource-owning structs that own threads or mmap'd memory** (since v5.11.26 for `OrderManagerState`). The destructor body calls cleanup functions (e.g., `OrderEventLog_Free`, `fclose`, thread join) on its member fields.

When you reorganize the struct's fields into HOT/WARM/COLD clusters per `cache-layout-discipline-for-hot-side-structs.md` Rule 4, you face a worry: **will the destructor still work if the fields move?** This doc addresses that concern with a clear yes/no + the actual safety conditions.

---

## The pattern (short version)

**Reorg is SAFE as long as:**
1. The destructor body references fields BY NAME (e.g., `OrderEventLog_Free(&this->event_log)`, NOT `*((OrderEventLog*)((char*)this + 0x1234))`)
2. No external code uses raw offsets into the struct (no `offsetof`-based byte access, no `memcpy` of struct bytes that depend on field order)
3. No persistence path writes struct bytes via raw `fwrite(this, sizeof(*this), 1, f)` (field-by-field `fwrite(&this->field, ...)` IS safe — same write order regardless of struct layout)

If all three conditions hold, the struct can be reorganized into any cluster layout without touching the destructor's source code.

**Why it works:** C++ destructors compile to "call cleanup functions on the named members in the reverse order of declaration." The destructor's source code refers to members by name; the compiler resolves names to offsets at compile time. Reordering members changes the offsets but NOT the names. The destructor body sees the same field names; the resolved offsets just differ. Same cleanup semantics.

**Member destruction order:** the implicit (compiler-generated) part of the destructor destroys members in REVERSE order of their declaration in the struct. Reordering fields therefore reorders destruction. This matters ONLY if one member's destructor depends on another member being still alive. In this codebase, members are POD types (no destructors of their own) or simple structs without inter-member dependencies — reordering destruction order is a no-op.

---

## Worked example — v5.15.5.C.1 OrderManagerState reorganization

**Before** (`CoreFrameworks/OrderManager.hpp:151-418` pre-.C.1; fields scattered across tiers):

```cpp
template <unsigned F>
struct OrderManagerState {
    // ... ~270 fields scattered HOT/WARM/COLD/CROSS-THREAD ...
    Order<F> orders[16];                  // line 152 — HOT
    ExchangeAdapter<F> adapter;           // line 163 — COLD
    SPSCRing<...> result_queue;           // line 171 — HOT
    // ... more interleaved tiers ...
    Portfolio<F> portfolio;               // line 199 — WARM
    FPN<F> balance;                       // line 205 — WARM
    // ...
    OrderEventLog<F> event_log;           // line 365 — HOT writer + cross-thread atomics inside
    // ...
    char event_log_path[256];             // COLD boot-set
    FILE* event_log_disk_file;            // COLD
    FILE* calibration_log_file;           // COLD
    ShardedTradeLog* trade_log;           // COLD pointer

    ~OrderManagerState() {
        OrderManager_Shutdown(this);      // <-- destructor body
    }
};

// OrderManager_Shutdown body (CoreFrameworks/OrderManager.hpp:1248-1265):
inline void OrderManager_Shutdown(OrderManagerState<F>* oms) {
    OrderEventLog_Free(&oms->event_log);              // refs by name
    if (oms->calibration_log_file) {                  // refs by name
        fclose(oms->calibration_log_file);
        oms->calibration_log_file = nullptr;
    }
}
```

**After** (`.C.1` proposed cluster reorg):

```cpp
template <unsigned F>
struct OrderManagerState {
    // ────────── HOT cluster ──────────
    Order<F> orders[16];
    alignas(64) SPSCRing<...> result_queue;
    SPSCRing<...> ws_result_queue;
    SPSCRing<...> reconcile_queue;
    SPSCRing<...> submit_queues[16];
    int event_log_mode;
    OrderEventLog<F> event_log;           // HOT writer-side; cross-thread atomics extracted (see ND1)

    // ────────── WARM cluster ──────────
    alignas(64) Portfolio<F> portfolio;
    FPN<F> balance;
    FPN<F> realized_pnl;
    FillRecord last_fill[16];
    // ... etc ...

    // ────────── COLD cluster ──────────
    alignas(64) ExchangeAdapter<F> adapter;
    int live_trading;
    char event_log_path[256];
    FILE* event_log_disk_file;
    FILE* calibration_log_file;
    ShardedTradeLog* trade_log;
    uint64_t last_seen_trade_id;
    FPN<F> ks_min_balance;
    FPN<F> ks_max_drawdown_pct;

    // ────────── Cross-thread atomic clusters ──────────
    alignas(64) struct OmsObservabilityCounters {
        std::atomic<uint64_t> total_submitted;
        std::atomic<uint64_t> total_filled;
        std::atomic<uint64_t> total_rejected;
    } obs;
    alignas(64) struct OmsSafetyCAS {
        std::atomic<uint64_t> flatten_pending;
        std::atomic<uint64_t> recovery_until_us;
    } safety;

    ~OrderManagerState() {
        OrderManager_Shutdown(this);      // <-- destructor body UNCHANGED
    }
};
```

**The destructor body is BYTEWISE UNCHANGED.** `OrderManager_Shutdown(this)` calls `OrderEventLog_Free(&oms->event_log)` — `event_log` is still resolved by name (just at a new offset). `oms->calibration_log_file` still resolves; `fclose` works. **Zero source-line changes to the destructor.**

---

## Trade-offs + when to apply

### Apply when:
- Struct has a non-trivial destructor (per CLAUDE.md item 11 exception)
- HOT/WARM/COLD tier mixing is observable (Rule 4 candidate)
- Destructor body refs fields by name (always true in this codebase per "no classes" convention)
- No external code uses `offsetof`/raw-byte access to the struct
- Persistence (if any) is field-by-field `fwrite(&field, ...)`, not struct-byte `fwrite(this, sizeof(*this), ...)`

### Skip / extra care when:
- Destructor's MEMBER ORDER matters (e.g., one member's destructor uses pointers into another member). In this codebase, no current struct has such dependencies — POD-ish member types throughout. If a new struct ever has order-sensitive member destruction, document it explicitly in the struct's comment block.
- Struct is in a byte-equivalence path (HMAC chain, SHA-256, persistence-via-memcpy). None of the current candidates have this constraint (verified via safety greps in pre-`.C.1` audit).

### Cost:
- Zero source-line changes to the destructor body
- Reorg is a pure data-layout decision; the destructor "just works"

### Win:
- Apply cache-layout-discipline rules to ANY struct with a RAII destructor without fearing destructor-break
- Removes a mental block ("can I reorg this struct? it has a destructor — let me check") that would otherwise discourage cluster discipline on resource-owning structs

---

## Lessons / gotchas

### Static_assert(offsetof) checks survive reorg

When a struct gets cluster anchors via `static_assert(offsetof(Type, field) % 64 == 0)`, the asserts reference fields BY NAME. Reorg + the asserts re-evaluate at compile time against the new offsets. If the reorg breaks alignment, the assert fires at compile time — instant safety net.

### `memcpy(dst, src, sizeof(Type))` is also safe IFF both src + dst are the same Type

The bytewise copy operates on whatever the struct's current byte layout IS. If both copy ends are the same Type, the copy works regardless of field order. UNSAFE: copying between two different versions of the Type (e.g., a v1 binary writing a struct + a v2 binary reading it) — but that's a version-skew concern, not a destructor concern.

### Member-initialization-list order vs declaration order

For constructors (NOT destructors): member init list runs in DECLARATION ORDER regardless of the init list's order. If the init list does `: b(1), a(b+1)` but `a` is declared before `b`, then `a(b+1)` runs FIRST with `b` uninitialized — undefined behavior. Cluster reorg changes declaration order → may expose latent UB if the init list assumed a specific order.

**Mitigation:** in this codebase, struct constructors are mostly default + explicit `OrderManager_Init(...)` field-by-field assignment. The reorg-induced declaration-order change doesn't affect the explicit init path. Verify no constructor uses an order-sensitive init list before reorganizing.

### The destructor's IMPLICIT cleanup (member destruction)

Beyond the explicit destructor body, the compiler runs `~MemberType()` on each member in reverse declaration order. For POD members (e.g., `int`, `FPN<F>`, `Order<F>` without its own destructor), this is a no-op. For non-POD members (e.g., embedded `std::atomic<uint64_t>` if it had a non-trivial destructor — it doesn't in modern libstdc++, but check), this matters.

**This codebase:** verified no embedded non-trivial-destructor members in `OrderManagerState`. SPSCRing has no destructor (lock-free; no resources to release). Order has no destructor. FillRecord has no destructor. Portfolio has no destructor. Atomic types are trivially destructible.

### When a struct OWNS heap-allocated memory via raw pointers

The destructor's job is to free those. If you ADD a new pointer member during reorg work and forget to update the destructor's cleanup list, you leak the resource. Pre-reorg, audit which members are heap-pointers + which are stack-embedded. The audit must list every cleanup the destructor does + every heap-allocation the corresponding `Init` does — pairing must be symmetric.

For OrderManagerState v5.15.5.C.1:
- `OrderEventLog` (heap-allocated mmap region; OrderManager_Init's arena setup; freed in OrderManager_Shutdown)
- `FILE* calibration_log_file` (fopen'd in `OpenCalibrationLog`; fclose'd in Shutdown)
- `FILE* event_log_disk_file` (similar)
- `ShardedTradeLog* trade_log` (set externally; OMS doesn't own; do NOT free in destructor)

The reorg DOES NOT add or remove members; it only reorders. So the symmetric pairing is preserved automatically.

---

## Audit detection (`/dod-audit` integration)

`/dod-audit` should flag MISSED cluster-reorg opportunities on structs with RAII destructors by:

- **Symptom 1:** Struct has `~Type()` defined AND has HOT/WARM/COLD tier mixing (Rule 4 violation per parent doc).
- **Symptom 2:** Destructor's source body uses ONLY named member access (no offsetof, no raw byte arithmetic) — meaning the reorg is SAFE.
- **Symptom 3:** No persistence path writes struct via raw `fwrite(this, ...)` — verified via safety grep for `fwrite.*<Type>` patterns.

When all 3 symptoms hold → flag as `RECOMMENDED — cluster-reorg-with-destructor-preservation`.

---

## Cross-references

- `cache-layout-discipline-for-hot-side-structs.md` (parent rule for HOT/WARM/COLD reorg)
- `decision-first-cluster-layout-pattern.md` (intra-cluster ordering ND3)
- `cross-thread-snapshot-publish-cluster-isolation.md` (ND1; complements: cross-thread atomic clusters within the reorganized struct)
- `struct-padding-determinism-pattern.md` (different concern: byte-equivalence contexts; NOT applicable to OMS per safety grep)
- FoxML_Trader_v2 CLAUDE.md item 11 ("C-style with templates, no classes" + RAII destructor exception)
- FoxML_Trader_v2 `CoreFrameworks/OrderManager.hpp:415-417` (canonical first reference application — RAII destructor preservation through v5.15.5.C.1 tier reorg)

## Promotion criteria (this doc was promoted)

Pattern triggered by `.C.1` pre-coding audit (2026-05-13). `OrderManagerState` is the first struct in this codebase with a non-trivial RAII destructor that also has HOT/WARM/COLD tier mixing requiring reorg. The pattern is generalizable to any future struct that fits both criteria.

Future candidates: any new long-lived resource-owning struct (e.g., a future `MakerOrderbookState` for v6.0 maker work; future `MmapSharedRegion` wrapper for v6.0 colo decoupling).

Re-evaluate when a 2nd application surfaces.
