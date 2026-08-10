# foxtag — the central tag-toolchain core (D-337)

The ONE parser + fact-producer + query engine over the locked `[SCHEMA]_[v1.0]` in-code tag
grammar. Every consumer — CI checks, the fox-symdeps plugin, your shell — is a thin client of
this core, so the grammar and the facts exist in exactly one implementation (the anti-Class-18
point of D-337: "one producer, N consumers" as ONE codebase, not N reimplementations).

Grammar SSoT: `DESIGN_SPECS/doc-disciplines/in-code-documentation-schema.md` (the frozen v1.0
contract). foxtag NEVER hardcodes the grammar — the category set and reference-subcats are
derived at runtime from the schema's fences, the `[TAG]` vocab from `doc-tag-vocabulary.md`,
exactly as the Python tools do. Folding a fence/vocab row = every tool tracks it, zero edits.

## Status (increments)

| Increment | What | Verified by |
|---|---|---|
| 1 — parser/scanner/query core + CLI | `validate` / `units` / `unit` / `tags` / `grammar` | `parity_check.sh` §1-3: BYTE-IDENTICAL to `check_code_tag_blocks.py` (violations + inventory + grammar counts), D-349 |
| 2a — LAYOUT producer | `layout` (clang record-layout → size/align/straddlers) | §4: straddler-exact vs `emit_record_layout.lua` on the 204-record census, D-350 |
| 2b — CODEGEN producer | `codegen` (g++ probe → instr / 3-class branches / floats / SIMD width-class) | §5: exact match vs the conformance analyzer's ratchet baseline (Regime_Classify 489/8; floats=18 = the schema example's value), D-351 |
| 2c — NEXT | `update` (the D-327 STRUCT `[DERIVED]` writer) + RC-B compile-DB regen + the generalized drift-gate | — |

**Migration contract (load-bearing):** the Python tools (`check_code_tag_blocks.py`,
`check_cache_layout.py`, `rebuild_doc_indexes.py`) stay CI-AUTHORITATIVE. No consumer cuts
over to foxtag until `parity_check.sh` PASSES — and each cutover is per-consumer, behind the
gate, with a soak. PASS today ≠ cutover done; it means cutover is *allowed*.

## Build

```bash
bash tools/foxtag/build.sh          # g++ -std=c++20 -O2 -Werror → tools/foxtag/foxtag (gitignored)
```

Dev-plane tooling — never linked into the engine (the H1–H3 engine invariants govern the
engine's hot/slow paths, not this apparatus).

## Commands

```bash
foxtag validate [paths...]      # mirror of check_code_tag_blocks.py — byte-identical violations
                                # exit 0 clean / 1 violations / 2 grammar-or-vacuity error

foxtag units [--json] [--type STRUCT] [--tag SLOW_PATH] [--name Foo] [paths...]
                                # unit inventory over the scan set

foxtag unit <file> <line>       # innermost enclosing unit at a line, as JSON — the plugin
                                # keystone (tagadapter.parse via subprocess):
                                #   foxtag unit Strategies/RegimeDetector.hpp 100
                                #   → {"type":"STRUCT","name":"RegimeSignals","open_line":72,
                                #      "close_line":147,"tags":["ENGINE","ML","SLOW_PATH","BINARY_FP"]}

foxtag tags [paths...]          # per-file [TAG] inventory
foxtag grammar                  # loaded grammar counts (SSoT-derived — sanity)
foxtag parity-dump              # sorted U|/T| rows for the parity gate

foxtag layout <tu.cpp> [Struct ...]
                                # LAYOUT facts via clang -fdump-record-layouts (D-321: layout
                                # is clang, ABI-identical to g++). Same JSON shape as
                                # emit_record_layout.lua:
                                #   foxtag layout main.cpp ExecutionCore
                                #   → {"tt::ExecutionCore<64>":{"size":68352,"align":64,"straddlers":[]}}

foxtag codegen --header <h> [--header <h2>...] --params 'SIG' --call 'EXPR' \
               [--flags 'F1 F2 ...'] [--prelude 'CODE']
                                # CODEGEN facts via a g++ NOINLINE PROBE + objdump (D-321:
                                # codegen is g++-only — the shipped compiler). The probe IS the
                                # RC-A fix: '--call' instantiates templates concretely, so
                                # header/template units produce real bodies:
                                #   foxtag codegen --header CoreFrameworks/ControllerEventLoop.hpp \
                                #     --params 'RegimeState<64>* a, const RegimeSignals<64>* b, const ControllerConfig<64>* c' \
                                #     --call 'Regime_Classify<64>(a, b, c)'
                                #   → {"instructions":489,"branches":{"loop":0,"rare_cold":14,
                                #      "data_dependent":8,...},"floats":18,
                                #      "simd":{"class":"scalar-xmm",...},"build":"..."}

foxtag selftest                 # structural grammar teeth (12 cases; RED cases must red)
foxtag codegen-selftest         # known-shape probe teeth (branchless / loop / scalar-float /
                                # packed-AVX2 / RC-E vacuous)
```

## The parity gate

```bash
bash tools/foxtag/parity_check.sh
```

Five sections, all must pass (§4/§5 skip-advisory when nvim/clang/g++ are absent, mirroring
the cache-gate's dependency policy):
1. `validate` output byte-identical to the Python (header / sorted violations / exit code)
2. unit/tag inventory identical (sorted `U|`/`T|` dumps)
3. grammar counts identical (both SSoT-derived)
4. `layout` straddler-exact vs `emit_record_layout.lua` on `main.cpp`
5. `codegen` exact instruction + data-dependent counts vs the conformance analyzer's
   `tools/lib/latency_path_budgets.json` baseline on manifest kernels

## Fact semantics (what a consumer must know)

- **LAYOUT facts** (`layout`) are stable per-ABI → the WRITTEN `[DERIVED]` class (D-327);
  refreshed by the cache-gate `--fix` / the coming `foxtag update`.
- **CODEGEN facts** (`codegen`) are compiler-flag-VOLATILE → LIVE-PREVIEW class (D-327);
  NEVER written without a `[BUILD]` pin. Default flags are the schema's canonical pin
  (`-O3 -march=x86-64-v3` — a concrete microarch, never `-march=native`, D-313); the JSON's
  `"build"` field carries the effective flags for exactly this reason.
- **RC-C width-class:** `simd.class` reports what is really there — `scalar-xmm` (the engine's
  actual float form), `sse-packed`, `avx2`, `avx512`, or `none`. The pre-fix detector matched
  AVX-only and false-cleaned everything scalar.
- **RC-E:** a probe body below the non-vacuity floor (8) is a LOUD `VACUOUS` exit 2 — never a
  green zero-branch verdict (the old branchtag painted "✓ branchless" on empty parses).

## Environment

| Var | Meaning |
|---|---|
| `FOXML_ENGINE` | engine root override (else cwd / sibling, shape-verified by `Version.hpp`) |
| `FOXML_WORKSPACE` | workspace root override (else sibling convention) |
| `FOXML_MEMORY_DIR` | memory dir override (else the Claude-Code projects derivation) |
| `CXX` | codegen compiler (default `g++` — D-321: codegen facts are g++-only) |

## Landmines learned here (do not re-arm)

- **Never `2>&1` into a machine parser of compiler output** — stdout/stderr merge at the PIPE
  and diagnostics interleave MID-LINE with the dump (`[sizeof=14748In file included…` corrupted
  147480→14748 on exactly one record; the parity gate caught it). Capture separately +
  concatenate (`run_capture_split`), mirroring `vim.system`.
- **Probe temp dirs live IN-REPO** — `/tmp` may be noexec (workspace LANDMINE 7).
- **Probe helpers must INLINE into `probe_fn`** — a `noinline` helper leaves the probe as a
  bare `call` and you measure nothing (the codegen teeth caught this on their first run).
- **`ENGINE.rglob`-style scans do NOT descend directory symlinks** — the schema_golden fixture
  dir is added to the scan file-list EXPLICITLY (P3 catch; `engine_source_files`).

## Python consumers (the binding — D-352)

`tools/foxtag_client.py` is the ONE Python↔core seam: binary discovery, subprocess+JSON
transport, decode, and error semantics in one module. Every Python tool imports it (never
spawns the binary directly) and gates on `core_available()` with its Python path as fallback —
a foxtag-less checkout keeps every gate alive. **pybind11 slots in BEHIND this same API** if
in-process speed is ever needed; no consumer would change.

Cut over (each parity-gated + soaked) — **⚠ PARKED 2026-08-10 (D-415): both cutovers REVERSED
for the churn phase — script-side is authoritative again (layout `auto` = Lua; inventory =
the Python collector; foxtag = explicit opt-in via `--backend foxtag` / `FOXTAG_INVENTORY=1`).
The frozen core is KEPT (never deleted — H21 spirit); parity re-arms at v1 as the per-surface
acceptance gate. Historical record of the original cutovers below:**
- `check_cache_layout.py --backend auto` — layout facts from `foxtag layout` when built
  (verified backend-identical vs the Lua emitter; drops the headless-nvim dependency).
- `rebuild_doc_indexes.py` code-tag inventory — from `foxtag parity-dump` via
  `foxtag_client.inventory()` (parity §2 proved it identical; `--check` stays green).

Still Python-authoritative (deliberately): `check_code_tag_blocks.py` — the standing-CI
validator itself; its cutover is the LAST one, after the others soak.

## Roadmap

- **`foxtag update` as a core-native writer:** deliberately NOT built yet — the DERIVED
  refresh-writer already exists, pure + self-tested, as `check_cache_layout.py --fix`
  (`refresh_derived`), which now runs over the core's facts via the backend cutover. A second
  writer implementation while the Python is authoritative would be the exact Class-18 drift
  this system kills; the core-native `update` lands when the Python gate retires.
- **RC-B residual:** the compile-DB itself (regen: `cmake -B build_clangd
  -DCMAKE_EXPORT_COMPILE_COMMANDS=ON .` at the engine root) is main-TU-grained; the core's
  header→TU pick prefers the `main.cpp` entry for header lookups. Full per-header entries =
  a plugin-session concern.
- **Drift-gate generalization:** sequenced, not skipped — it generalizes when the
  corresponding axes start being WRITTEN (the P6 conversion writes layout; call-graph +
  [BUILD]-pinned codegen come with the plugin/P6). Today only layout is written → the
  cache-gate covers it.
- **Phase-5 seam (operator's session):** the plugin's `tagadapter.parse` via `foxtag unit`,
  `facts.lua` via `foxtag layout`/`codegen` — all subprocess+JSON, ready now.

Decisions: D-337 (the core), D-349 (increment 1 + migration contract), D-350 (layout + the
stream-interleave catch), D-351 (codegen + the analyzer-baseline cross-check).
