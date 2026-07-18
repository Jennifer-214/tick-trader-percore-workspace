---
type: framework-pattern
stage: 3-first-canonical
established: 2026-07-18
tags: [framework-discipline, doc-discipline, ci-tooling, structural-fix]
surface: [ci-tooling, doc-pipeline]
sister_specs: [meta-disciplines/mechanical-verification-of-derived-code-facts.md, framework-patterns/doc-intelligence-toolchain-architecture.md, meta-disciplines/calibration-corpus-non-vacuity-discipline.md, data-disciplines/function-struct-alignment-for-single-mov-access.md]
sister_docs:
  - tools/check_cache_layout.py   # the first-canonical --isolate implementation
applications:
  - 'check_cache_layout.py --isolate (E.1.2.A C4 step-2, D-363/D-368) — per-header sizeof-forcing probes materialize every converted [STRUCT] main.cpp under-instantiates; proven across global / tt:: / template / multi-instantiation'
---

# Isolated per-struct layout probe — materialize ANY struct's layout in isolation, 1:1 with the binary

**Established:** 2026-07-18 (E.1.2.A C4 DERIVED-write step-2, D-363/D-368; operator-improved — Caramel's per-struct-isolation insight beat the monolithic all-headers probe). The technique the LAYOUT fact-producer uses to get a struct's real byte layout WITHOUT compiling the whole engine.

## The problem

`clang -fdump-record-layouts` only dumps the layout of a record it actually LAYS OUT — one that is USED (a variable, a member, a `sizeof`, a base) or, for a template, INSTANTIATED at concrete args. A struct merely `#include`d but unused is never laid out → never dumped. So a monolithic "include every header" probe TU covers only the structs the TU happens to USE (`main.cpp` covers ~81 of 324 converted `[STRUCT]`s), is SLOW (~2min — it pulls the whole engine), and is FRAGILE (the RC-B include-order class: ~11% of headers fail standalone; e.g. `TUISnapshot`-unknown before its defining header is included).

## The technique — per-header isolation + sizeof-forcing

For the converted `[STRUCT]`s in a header, force each layout in an ISOLATED, minimal TU:

```cpp
#include <cmath>            // prelude — RC-B transitive-std-dep hygiene (a header leaning on a transitive <cmath> etc.)
#include <cstdint>
#include <cstddef>
#include "<the header>"
using namespace tt;         // resolves BOTH global and tt:: struct names by bare reference — NO per-struct namespace parsing
char _probe_0[sizeof(StructName)];         // sizeof forces the layout; NO ctor needed
char _probe_1[sizeof(TemplateName<64>)];   // templates instantiate at real F (extra params ride defaults)
```

Group the converted `[STRUCT]`s by header, emit one such TU per header, compile each (`-fsyntax-only -Xclang -fdump-record-layouts` with the real build's flags), and merge the dumps.

## Why it works — layout is USE-INDEPENDENT + 1:1 by ABI determinism

A struct's layout is a PURE FUNCTION of `(its definition · the layout-relevant compile flags · the template args)` — TOTALLY INDEPENDENT of how, or whether, it is USED. So you do NOT need "example consumers" mirroring the real code; you need only the DEFINITION + the real build's flag/`#ifdef` context + a materialization trigger (`sizeof`). Given those match, the isolated layout is BYTE-IDENTICAL to the compiled binary's — the D-321 guarantee (clang `-fdump-record-layouts` is Itanium-ABI-identical to the shipped g++). Same technique `pahole` / ABI-diff tools use.

**The 1:1 correctness catch:** a field behind `#ifdef X` lays out the same ONLY if the probe sets `X` the same as the real build. So the isolated TU must reproduce the real build's layout-relevant flags (`-std`, `-m`, packing pragmas) + active `-D` defines (reuse `main.cpp`'s flags via the compile-DB `db[1]` fallback in `sizeprobe._flags_for`) + template args. Match those → 1:1 guaranteed; mismatch a define → the layouts CAN diverge. **"Match the real code" means match the DEFINE/FLAG/ARG context, not the usage.**

## Why isolation beats the monolithic probe

| | monolithic all-headers probe | per-header isolation |
|---|---|---|
| Coverage | only the structs the TU USES | EVERY struct (sizeof-forced) |
| Speed | one ~2min+ compile (whole engine) | seconds per header, parallelizable |
| Fragility | RC-B include-order dominoes (`TUISnapshot`-unknown; 11% fail standalone) | each header + its own deps; no cross-contamination |
| Correctness | 1:1 (same ABI) | 1:1 (same ABI), per-struct-clean |

## Edge-cases

- **Templates** — detect via the `template<…>` decl; instantiate at real `F=64` (extra params on defaults). Multi-instantiation (`RollingStats<64>`/`<64,256>`/…) — the layout matcher strips `<…>` to the bare name; pick the primary instantiation (or `[INSTANTIATION]`-key each).
- **RC-B header-hygiene** — a header leaning on a transitive std include fails standalone; the common `<cmath>/<cstdint>/<cstddef>` prelude covers most; extend per-header as they surface.
- **Non-instantiable-via-ctor structs** — `sizeof` needs no ctor, so private-ctor / required-arg / abstract structs still materialize (a *variable* would not — this is why `sizeof`-forcing, not a variable).

## Sister disciplines

- `mechanical-verification-of-derived-code-facts.md` — this is the PRODUCER technique whose facts the DERIVED-fact guards consume (size / straddle).
- `doc-intelligence-toolchain-architecture.md` — the one-producer-N-consumers toolchain this producer feeds.
- `function-struct-alignment-for-single-mov-access.md` — the register-fit / single-mov discipline the per-field layout facts (RC-F, D-366) surface.
- `calibration-corpus-non-vacuity-discipline.md` — the writer's `--selftest` asserts this producer's non-vacuity + idempotency + round-trip.
