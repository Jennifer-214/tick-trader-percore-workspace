---
type: data-discipline
stage: 2-draft
version: 1.0
established: 2026-06-24
tags: [data-oriented-design, latency-discipline, codegen]
surface: [hot-path, slow-path]
sister_specs: [cache-line-discipline.md, concurrency-model-summary.md]
applies_at_skills: [/hft-audit, /dod-audit, /latency-track, /blindspot-scan]
---

# Register-spill discipline (the register-level rung of the working-set gradient)

**Established:** 2026-06-24 (v5.15.5.F.4d.1.E.1.1 — codified from the operator's register-spill capture).
**Status:** Stage 2 DRAFT v1.0 — matures when a hot-path register-pressure finding is fixed against it.

The sibling of `cache-line-discipline.md`, one rung UP the working-set gradient. Cache-line discipline keeps the hot working set **L1-resident**; register-spill discipline keeps the INNERMOST working set **register-resident**. Same goal (data in the fastest tier), different tier.

---

## The gradient

```
register  >  L1 cache  >  L2/L3  >  spill-to-stack (memory)
^^^^^^^^                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
this spec                cache-line-discipline.md
```

x86-64 has ~16 general-purpose registers. When a function's SIMULTANEOUSLY-LIVE values exceed that, the compiler **spills** the excess to the stack — a store now (`mov %reg, -N(%rbp)`), a reload later. Each spill = extra µops + memory traffic (even when L1-resident) + a lengthened dependency chain.

## Why it's a hot-path concern (latency AND determinism)

On a sub-µs branchless hot path, a spill in the inner loop:
- **ADDS LATENCY** — the store/reload µops + the dependency stall on the reload.
- **ADDS VARIANCE** — the determinism enemy (H8). A spilled value's reload can land in a different cache/store-buffer state run-to-run.

**Our specific trigger — 16B types.** `Money` (`FixedPoint<10,8>`) and `FPN_Binary<64>` are `__int128`-backed = 16B = **TWO general-purpose registers EACH**. Holding several live at once (e.g. a gate materializing entry / exit / SL / TP `Money` values simultaneously) exhausts the register file fast. Deep inlining (the whole `BG_Evaluate`→`SG_Evaluate` chain inlined) + over-unrolling compound it.

## Detection — ADVISORY, not a hard gate

`tools/check_latency_path_conformance.py` counts spills on the named hot/slow fns: the `mov %reg, -0xNN(%rbp)`-beyond-preamble heuristic, reported as `spills=N`.

**It is deliberately NOT strict-teeth'd** (unlike the no-malloc / no-float / no-div gates). A frame-relative store isn't always a spill — a struct field written to a stack-local looks byte-identical in the asm. So:
- A non-zero `spills=N` is a **SIGNAL to inspect, NOT an auto-fail**.
- Confirm by hand: `g++ … -S` (or `objdump -d`) the inner loop; a real spill is a store-then-later-reload of the SAME value with no intervening semantic store.
- Track the count as a **RATCHET** (did this change RAISE it vs the pre-change build?), not an absolute gate.

## Mitigation (when a real spill is confirmed in a hot loop)

- **Shorten live ranges** — reorder so a value's last use comes before the next value is born; the compiler reuses the freed register.
- **Hold fewer 16B values live** — recompute-cheap can beat hold-live; don't materialize all of entry/exit/SL/TP `Money` at once if they're consumed sequentially.
- **Split the function** — an over-pressured hot fn split into two (each with a smaller live set) can drop below the spill threshold.
- **`__restrict`** — frees registers the compiler otherwise pins for aliasing safety.
- **Don't over-unroll** — each unrolled iteration's live values add to the pressure.

## What this is NOT

- NOT a blanket "minimize locals" rule — readability matters; this applies to the NAMED hot/slow inner loops only (the conformance tool's scope).
- NOT a hard CI gate — the heuristic's false-positive surface (struct-field-to-stack-local) makes a strict gate noisy. The discipline is **inspect-on-signal + ratchet**, not refuse. (Sister posture to the cache-line spec: a layout audit, not a compile error.)

## Cross-references

- `cache-line-discipline.md` — the sister rung (L1 residency / false-sharing / `alignas(64)`).
- `plans/_cross-cutting/2026-05-06-latency-path-discipline.md` § Register spills — the operational verification home + the `-S` inspection steps.
- `tools/check_latency_path_conformance.py` — the `spills=N` detector (advisory).
- `DOCS/DESIGN_PHILOSOPHY.md` § 4 (latency cost framework) — cycles vs cache vs branch costs.
- Invariants: H4 (`Money`/`FPN` 16B = the 2-registers-each pressure source) · H8 (variance/determinism) · H7/H20 (branchless hot path).
