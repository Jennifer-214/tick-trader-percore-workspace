---
type: meta-discipline
stage: 2-draft
version: 1.0
established: 2026-06-12
tags: [data-oriented-design, ci-tooling, static-analysis, capital-safety, migration-discipline, cache-line, structural-fix]
surface: [hot-path, slow-path, oms-drainer, persistence, wire-format]
sister_specs: [representation-migration-completeness.md, dead-code-and-identifier-retirement-discipline.md]
realizes_tech_debt: [TECH_DEBT-175, TECH_DEBT-177, TECH_DEBT-159]
related_skills: [/dependency-chain-trace, /dod-audit, /latency-track]
related_tools: [gen_code_map.sh, check_struct_alignment.py, check_identifier_retirement.py]
canonical_decision: D-202 (plans/v5.15-live-readiness/decision-logs/v5.15.5.F.4d.1.E-architecture-v2.md)
---

# Struct-change cascade-impact tooling (Tool A + Tool B — the struct-rework support loop)

> **Status: DESIGN DRAFT (stage 2).** Captures the agreed shape (D-202 + its REFINEMENT). The tool is NOT built — this doc is the reference the build follows. Tool A is `TECH_DEBT-175`; Tool B is `TECH_DEBT-177`; both feed the `TECH_DEBT-159` DOD re-pack.
>
> **⚠️ ADVERSARIAL REVIEW 2026-06-12 — RED (do NOT build as-is).** A 3-agent independent panel (FIND/REFUTE, grounded in empirical libclang runs + file:lines) found the bespoke-libclang-engine framing over-built and partly blocked. **Killers:** (1) `gen_code_map` ALREADY does TRANSITIVE composition (`--composition`, fixpoint loop `:108-142`; ran live = "20 direct + 13 transitive" for `Money`) + byte-sensitive sites (`--byte-context`) + X-macro fields (`--macros`) — the "v1 novelty" is largely SHIPPED; this spec mischaracterized gen_code_map as "grep + one level" (a `feedback_audit_canonical_sister_before_new_infra` miss — `--composition`/`--byte-context` are even cited in `/dependency-chain-trace` SKILL step 7, which I'd read). (2) The CI "layout-sensitivity golden" is INFERIOR to + DUPLICATES the codebase's existing compile-time `offsetof`/`sizeof` `static_assert` idiom (43 present incl. `ExecutionCore.hpp:176` cache-span guard + `OrderManager.hpp:736` %64 guard; `check_struct_alignment.py` advisory(b) already recommends extending them) — a `static_assert` fails at-site, can't drift, needs no ledger. (3) libclang returns ZERO field cursors for the X-macro structs `PerCoreCfg`/`ControllerConfig<F>` (empirically: children=1, 0 FIELD_DECLs) — the PRIMARY targets — so the AST engine is blocked on its own headline target; per-field layout needs `get_offset("name")` driven off a registry-text parse (which `gen_code_map --macros` + `check_per_core_registry_integrity.py` already do). (4) `function→thread` is ILL-POSED, not just hard: the same OMS/portfolio fns run drainer-threaded live AND single-threaded in the backtest driver → cross-thread-ness is a call-context property, so v1's cache filter needs reachability → the v1/v2 split is dishonest. (5) Tool B's `llvm-mca` is NOT installed + is ill-suited to inlined header-only hot paths; `pahole -R` on the existing `-g` builds (`build_tsan/asan/ubsan`) + `/latency-track`/`bench_hot_path.cpp` carry the real signal. **RE-CUT direction (in-thread 2026-06-12, pending operator):** compose existing `gen_code_map --composition`/`--byte-context`/`--macros` + `pahole -R` into a thin `cascade <T>` view; a static_assert-COVERAGE meta-guard for the CI half (NOT a golden); `/latency-track` for codegen (drop `llvm-mca`); scope the orphan-detection (A9/A11/A12/A24) honestly as the one genuinely-new (hard: liveness + call-graph + registry-parse) piece — not "v1 composition." Everything below is the PRE-review draft, retained for the re-cut.

## Why this exists (the human-fallibility gap it closes)

Operator, 2026-06-12: *"this tool is to make things like that easier because I forgot about downstream impacts."*

When a **core struct central to operational functioning** changes — a field resized, a type swapped (the 24B→16B `Money` flip), a field re-packed — the change **cascades**: structs that contain it resize/reorder, structs that contain *those* shift, and every consumption site sees moved offsets. You cannot hold that transitive cascade in your head while editing one struct, so a downstream impact gets **forgotten — silently, because it still compiles**. Most of the cascade is harmless (the compiler recomputes offsets); a few sites need real rework. This tooling makes the cascade **VISIBLE on demand** (a cascade check you run while changing a struct) and **ENFORCED in CI** (a gate that won't let a core-struct change silently leave a downstream byte/cache hazard unaddressed).

This is the permanent structural close (M7) for the [[representation-migration-completeness]] meta-pattern — but its *headline* purpose is broader than orphan-detection: it is **struct-change → downstream-impact analysis**. Orphan-detection (the 4 representation-migration sub-shapes) is one *query* over the same field-dependency graph, not the point.

## Two tools, one loop

| | **Tool A — cascade-impact analyzer** (TD-175) | **Tool B — codegen verifier** (TD-177) |
|---|---|---|
| Question | *If I change this core struct, what downstream resizes/realigns, and which consumption sites need real WORK?* | *After I did the rework, did it actually hit minimum cycles / introduce no new cache-line splits?* |
| Kind | STATIC structural impact — **scopes** the rework + the sites | codegen/cycle verification — **verifies** the result |
| Input | source AST (libclang) + record layouts | compiled asm + DWARF |
| Mechanism | transitive composition graph + per-site classification | `llvm-mca` (cycle estimate) + `pahole` (layout) + before/after diff |
| Output | the cascade-impact map + the work-site filter (+ orphan flags) | per-function cycle/span delta vs a frozen golden |

They are the two halves of struct-rework support: **plan the rework (A) / verify the rework (B)**, sharing the same underlying data (the field set + the hot set). Build order (D-202): Tool A → Tool B (machinery) → the `.E.0.10` fix-ship dogfoods both → `.E.1`.

## Tool A — what it computes

### The two data-flows (the v1/v2 line)

A core-struct change has **two** kinds of downstream flow; do not conflate them:

1. **Composition / layout data-flow — v1 CORE (the headline).** *Tractable.* Given a changed struct/type T:
   - **Transitive composition cascade:** every struct that embeds T as a field, then every struct embedding *those*, recursively (libclang field-type graph). The deep, transitive, layout-precise successor to `gen_code_map --structs T` (which is grep + one level only).
   - **Per-site layout delta:** for each affected struct, the new size + the new **field offsets and cache-line spans** (libclang record layout, or `pahole` on the binary). Track **offset/span deltas, not just size** — a pure H6 field-reorder shifts cache-line spans at *constant* size, and that still matters.
   - Worked instance already in-code: the Ship-A 16B flip shrank `OrderPreResolved<64>` 48B→32B (`CoreFrameworks/Order.hpp` `static_assert(sizeof(OrderPreResolved<64>) == 32, ... "Ship-A 16B: 48→32")`) → cascades to `Order` / `Position` / the ExecutionCore params + their consumption sites. That cascade IS `TECH_DEBT-159`'s sharpened scope ("verify the shrink didn't mis-align / introduce cache-line splits").

2. **Value / liveness data-flow — v2 (the hard part).** *Needs escape/reachability analysis.* Does a write reach a *live* read; is a read *reachable*; is a write to a *discarded copy*? This is the only genuinely-hard piece. It is what A9's subtle shape needs (the OnEvent slip block writes a discarded local `event` copy; the `effective_cores[].slippage_pct` read sits after a mode-1 early-return → statically present, dynamically dead). v1 *flags* such sites "suspicious — human verify"; v2 resolves them mechanically.

### The work-site filter (the signal, not the noise)

The cascade is large; the **WORK is small**. Most consumption sites are **compiler-handled** — offsets just recompute, zero source change. Listing all 200 sites that touch a struct is noise. The tool's value is **filtering the cascade down to the sites that need actual human rework:**

- **Byte-layout-sensitive sites (H9 / H12):** `memcmp` / `SHA-256` / `fwrite` / HMAC-input / wire-emit / snapshot-persist over the struct — a layout change breaks byte-equivalence here. (Reuses `gen_code_map --byte-context` logic.)
- **Cache-sensitive sites (H6):** a hot-path field pair that now **straddles** a 64B cache line, or an `alignas(64)` cross-thread field knocked off its line (false-sharing re-introduced) by the offset shift.

Everything else in the cascade is reported as *informational* (affected-but-compiler-handled). The headline output is **"here are the N sites that actually need rework,"** not the full touch set.

### Orphan-detection (the secondary query)

Over the same field-dependency graph, Tool A also answers the [[representation-migration-completeness]] sub-shapes (Class 44 / 26 / 27 / torn-read):
- `write-with-no-live-read` (A9/A16) · `read-with-no-live-write` (A11/A12 — the producer-orphan) · `>8B cross-thread-written field read outside a seqlock` (A22/A23) · `flat-field-mutation-then-cores[slot]-read` (A24).

These are a *query*, not the headline. The first three are v1 (discrete, accessor + call-graph resolvable); the discarded-copy/dead-path refinement of the first is v2 (value-liveness).

### How we select which structs

Not all structs (noise + cost). A deterministic high-risk seed, **reusing existing tooling**:
- `gen_code_map --structs Money` + `--structs FPN_Binary<64>` + `--structs Position` → every struct embedding a migration-prone money/feature type (= where the sub-shapes live = the byte-layout blast set the 159 re-pack needs).
- ∪ cross-thread `alignas(64)` structs (the threading surface — A22/A23).
- ∪ X-macro-registry target structs (the framework-managed structs where migrations happen; enumerable from `FOREACH_REGISTRY`).
- \+ a `--struct <Name>` override for a targeted single-struct run (mirrors `/dependency-chain-trace`'s symbol arg).

## Tool A — the two modes

1. **On-demand cascade check (`cascade:<struct-or-type>`).** Run while changing a core struct: prints the transitive composition cascade + the filtered work-sites (byte-sensitive + cache-sensitive) + any orphan flags. This is the "make it visible" mode — the thing the operator reaches for *before* touching a central struct so the downstream impact isn't forgotten.

2. **Standing CI gate (the "catch what I forget" mode).** A **layout-sensitivity golden** — the same pattern as `check_identifier_retirement.py`'s golden ledger, applied to struct layout:
   - The golden is a checked-in ledger of the **work-sensitive facts** for each selected core struct: its size, its byte-layout-sensitive consumption sites, its hot-field cache-line spans, its `alignas(64)` cross-thread field placements.
   - On commit: recompute those facts from current code; **diff vs the golden**. If a struct's *work-sensitive* fact changed AND the golden was not re-blessed in the same commit → **FAIL**, naming the specific cascade ("`Money` layout changed → `OrderPreResolved` 48→32 → these 3 wire/memcmp sites + 1 hot cache-span affected; review + update the golden").
   - **Low-noise by construction:** the gate keys on the *work-sensitive* surface (byte + cache), NOT on every offset shift — a plain compiler-handled offset move does not trip it. (A noisy gate gets ignored; this one fires only when a genuinely-rework-needing fact moves.)
   - **Negative self-test (D-137):** inject a layout change to a sensitive struct without a golden update → assert the gate goes RED. Enroll in `DOCS/TOOLS.md` + compose into `run_all_tests.sh` (TD-176) + the pre-commit hooks.

## Edge cases (scouted)

**v1 must handle (and why grep can't):**
- **Accessor-mediated access** — fields touched via getter/setter (`MBS_OrderSetBanditContext`, `Order_GetIsMaker`, `BITMAP_*`), not `.field`. A setter call = a write; a getter = a read. A11 IS this (setter defined, *never called*) — grep sees it defined; only a **call-graph** sees it's dead.
- **Init/reset-write vs value-write** — A12 IS this: `bandit_reward_bps[]` is written *by the FOREACH zero-init* but never with a real value. "Written" must distinguish init/reset from value-bearing, or A12 hides.
- **Seqlock-published read** — slow writes, hot reads a *published copy* (not the same field). Model the publish/consume contract or it false-flags every seqlock'd field as "written-not-read."
- **Persistence / wire read** — a field written every cycle, "read" only by the cross-process snapshot save. Counts as a live read, else every persisted field false-flags.
- **Template instantiation** — `Order<F>` / `Position<F>` / `OrderPreResolved<F>`: analyze at a canonical instantiation (F=64); uninstantiated members otherwise invisible.

**v2 (value-liveness — the hard part):**
- **Write-to-discarded-copy** (A9): a write to a stack-local whose value is never propagated — needs escape analysis.
- **Dead-path read** (A9): a read after an early-return / in an unreachable branch — needs control-flow reachability.

**Infra dependency (both versions):** a **function→thread map** (which functions run producer / drainer / slow / hot / boot). `/dependency-chain-trace` infers it by LLM; the deterministic tool needs it **curated** (seeded from the thread entry points + transitive call-graph). This map is itself reusable (it's the thread-attribution layer for any cross-thread analysis).

## Relationship to existing tooling (extend + compose, do not duplicate)

Per [[feedback_audit_canonical_sister_before_new_infra]] + [[feedback_independence_for_judgment_not_mechanical]], grounded by reading the artifacts:

- **`gen_code_map.sh` (CODE_MAP)** — grep-based, function/type-LOCATION + a one-level `--structs T` blast set. Tool A is the **deep, transitive, layout-precise AST successor** to its `--structs`/`--byte-context` modes. Tool A may emit a field-access section back into CODE_MAP.
- **`/dependency-chain-trace` (skill)** — the JUDGMENT sister: it already does per-symbol write-sites / read-sites / flow-graph / lifecycle / blast-radius (its steps 2–7), but by LLM, for ONE symbol, on-demand. Tool A is its **mechanized, exhaustive, deterministic** core. **Refactor the skill to CONSUME Tool A's map** for the mechanical enumeration (drop the LLM grep-and-classify) and keep only the judgment layer (blast-radius assessment, recommendations). Mechanical → the tool; judgment → the skill.
- **`check_identifier_retirement.py`** — the golden-ledger pattern Tool A's CI gate mirrors (force-acknowledge on a wire-visible change; here, on a layout-sensitive change).

So Tool A is **one new AST engine** that unifies, at field granularity with byte/cache deltas, the composition/layout half (`gen_code_map --structs`) + the consumption-flow half (`/dependency-chain-trace`) — not a parallel island.

## Tool B — codegen verification (the sister)

Where Tool A says *what resizes and where realignment is needed*, Tool B confirms *the rework actually minimized cycles*. **Machinery-now / goldens-later (D-202):**
- **Machinery (build early — reusable, validatable on current code):** compile the Tool-A-flagged hot functions to asm under the **real `build.sh` -O3 flags** (pinned target — else the numbers are fiction) → `llvm-mca` per-block cycle / port-pressure estimate → `pahole` cache-line spans → **before/after diff** on a rework. The characterization-test discipline applied to codegen (freeze the mca profile, assert no-regression on layout change).
- **Goldens (freeze later):** the production cycle/layout baselines freeze **post-`.E.1`** — the Core→Node rename churns any baseline frozen now. Pre-`.E.1`, Tool B runs **advisory relative-delta** only.
- **Caveat:** `llvm-mca` is a pipeline *estimate* (no real cache-miss/mispredict model) → frame as a *relative regression-delta* gate, not an absolute cycle oracle. The absolute truth is the existing `build_lat/` LATENCY_BENCH + `perf` harness (`/latency-track`) — Tool B's static delta is the cheap MIDDLE tier that **composes** that harness, never duplicates it (Class-21).

## Output artifacts (the reusable SSoT)

Tool A emits a machine-readable **field-access / cascade map (JSON)** — the reusable artifact the whole family shares:
- `/dependency-chain-trace` consumes it (enumeration).
- Tool B consumes it (which fields are hot → which functions to codegen-verify).
- The TD-159 DOD re-pack consumes it (cluster-by-access-pattern layout decisions, H6).
- The `subsystem-designs/` catalogue consumes it (as-built field maps).
- Every future migration consumes it (run before + after = the prevention discipline).

It is therefore not an A9-hunter — it is the permanent **field-level code-intelligence layer**.

## Build scope + sequencing

- **v1 = the struct-change impact analyzer:** composition/layout cascade + the work-site filter (byte + cache) + offset/span deltas + the discrete orphans (write-no-read / read-no-write via accessor + call-graph) + the two modes (cascade check + CI golden). Covers A11/A12/A16/A24 mechanically; flags A9's shape for human review.
- **v2 = value-liveness:** escape/reachability for the discarded-copy/dead-path cases (A9). Resolves the flagged-for-review set mechanically.
- **Tool B = machinery-now / goldens-post-`.E.1`.**
- **Order (D-202):** Tool A → Tool B (machinery) → the `.E.0.10` fix-ship dogfoods both → `.E.1` (guarded by Tool A) → … → TD-159 re-pack (Tool B's goldens serve it).

## Cross-references

[[representation-migration-completeness]] (the meta-pattern this tool is the permanent guard for); Class 44 (bound/computed value with a dead/overwriting consumer); Class 26/27 (per-core scope); the torn-read class; `dead-code-and-identifier-retirement-discipline.md` (the golden-ledger CI pattern Tool A's gate mirrors); `cache-line-discipline.md` (the H6 spans Tool A measures); `gen_code_map.sh` + `/dependency-chain-trace` (the tools Tool A consolidates at AST depth); `/latency-track` + `build_lat/` LATENCY_BENCH (Tool B's measured tier); D-202 (the canonical decision); `TECH_DEBT-175` (Tool A) + `TECH_DEBT-177` (Tool B) + `TECH_DEBT-159` (the DOD re-pack consumer).
