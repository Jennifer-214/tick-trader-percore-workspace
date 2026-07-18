# Working in `tools/` — the doc-system toolchain (foxtag + checkers + plugin)

> **On-demand nested orientation.** Loads when you edit a file under `tools/`. This is the **DEV-PLANE
> doc-intelligence toolchain** — a SEPARATE project from the engine. The engine's Hard Invariants
> (H1–H3 no-heap/no-mutex, hot/slow latency) govern the ENGINE's paths, **NOT this apparatus**: foxtag
> is `-std=c++20 -O2`, gitignored, and **never linked into the engine**. As the operator put it, this
> is "basically 2-3 codebases" in one workspace — the C++ `foxtag` core + the Python checker family +
> the Neovim plugin — all over the LOCKED `[SCHEMA]_[v1.0]` in-code tag grammar.

## What this toolchain IS

A **self-hosted code-intelligence + living-documentation layer** over the `[SCHEMA]_[v1.0]` tag grammar
— the bespoke version of what Kythe/Glean (internal) or Sourcegraph + Swimm + Semgrep (commercial)
sell in pieces. Code = hub, `[TAG]`/`[REFERENCE]` = edges, workspace docs (decisions/specs/invariants/
memories) = nodes. Every consumer (CI checks · the fox-symdeps plugin · your shell) is a **thin client
of ONE core**, so the grammar + facts exist in exactly one implementation.

## Load-bearing disciplines (the toolchain's own invariants — do NOT break)

- **ONE parser, N consumers (D-337).** `foxtag` is the single tag-parser + fact-producer + query
  engine. A checker/plugin/skill that RE-implements block-parsing is a **Class-18 mirror**. A new
  capability = a foxtag producer/command consumed by all — not a private re-parse.
- **Grammar DERIVED, never hardcoded.** The category set + reference-subcats are read from the schema's
  ```-fences at runtime; the `[TAG]` vocab from `doc-tag-vocabulary.md`. Fold a fence/vocab row → every
  tool tracks it, **zero code edits**. NEVER hardcode the grammar into a tool. `foxtag grammar` emits the
  fence-derived grammar as data — the seam a consumer reads instead of hardcoding. **Watch-point:** the
  nvim plugin is NOT yet fence-derived — `tag_grammar_adapter.lua` is a native-Lua mirror (hardcoded `UNIT`
  set `:27` + `[DERIVED]`-axis render `:63-92`, zero `foxtag` calls), so a new unit-type / DERIVED axis
  needs a manual plugin edit until it consumes `foxtag grammar`/`foxtag unit` (D-349) or a `parity_check.sh`
  plugin section guards it. → `doc-intelligence-toolchain-architecture.md` § grammar-propagation (D-365).
- **Migration contract (D-349) — Python is CI-AUTHORITATIVE until a gated cutover.** The Python tools
  (`check_code_tag_blocks` / `check_cache_layout` / `check_conversion_completeness` / `rebuild_doc_indexes`)
  are authoritative. No consumer cuts over to foxtag until `tools/foxtag/parity_check.sh` PASSES for it —
  per-consumer, behind the gate, with a soak. **PASS ≠ cutover done; it means cutover is ALLOWED.**
- **Every guard asserts its own non-vacuity (anti-Class-51).** Each checker carries a `--selftest` that
  PROVES it flags a planted known-bad AND passes a known-good. Canonical references: **ExecutionCore.hpp**
  = a COMPLETE conversion (must scan clean) · a **SYNTHETIC golden-broken fixture** (the completeness gate's
  in-code `DemoLumped6` — a 6-field struct lumped in a `[FUNCTION]` block) = must be flagged; it is
  corpus-independent BY DESIGN, so it survived the Phase-C cleanup that CONVERTED the original
  `GateControlNetwork.hpp` exemplar (now the clean worked-template) · **CODE_TAG_TEMPLATES.hpp** = the
  validator-green template corpus. A guard that can't fail on a planted defect is vacuously-green. Standing
  calibration fixtures are SYNTHETIC/frozen — a live broken file gets fixed and stops being broken (D-362).
- **Comments-only + lossless; MARK, never delete.** Conversions/cleanups change ZERO code bytes
  (`lossless.py`-gated — comment-stripped diff == git HEAD). A rotted/legacy/deletion-candidate UNIT gets
  a `[DEPRECATED]` / `[MARKED_FOR_DELETION]` marker (sister to `[OUTDATED_INFO]` for stale COMMENTS + the
  H21 tombstone discipline) — **never a code deletion.**
- **The schema is LOCKED (`[SCHEMA]_[v1.0]`, D-346).** A grammar change = a `[SCHEMA]_[vN]` bump,
  coordinated across foxtag + the validator + the plugin (the stable contract = {closed vocab · section
  ladder · one-category-per-line · the `====` block structure}). Don't drift a tool off the locked grammar.

## Where things live

| Piece | Path |
|---|---|
| foxtag C++ core (parser · `units`/`unit`/`validate` · `layout` · `codegen`) | `tools/foxtag/` (`foxtag.hpp` + `foxtag_main.cpp`; `build.sh` → gitignored `foxtag`) |
| Parity gate (Python ↔ foxtag byte-identical) | `tools/foxtag/parity_check.sh` |
| Validator — grammar + `[TAG]` vocab + `[REFERENCE]` resolution | `tools/check_code_tag_blocks.py` (`--selftest`) |
| Layout DERIVED gate (size/align/straddle vs ABI) | `tools/check_cache_layout.py` (`--fix`) |
| **Completeness / coverage gate** (C1 lumped · C2 missing · C3 no-DERIVED) | `tools/check_conversion_completeness.py` (`--selftest`) |
| Conversion checkers (dev-staging: det1/det4/gap/lossless/ladder) | `plans/v5.15-live-readiness/tools-staging/e12a-conversion-checkers/` |
| The Neovim plugin (RENDERS foxtag output; operator's session, D-353) | `tools/plugins/fox-symdeps.nvim` |
| Grammar SSoT · Vocab SSoT · Template corpus · North-star | `DESIGN_SPECS/doc-disciplines/in-code-documentation-schema.md` · `DESIGN_SPECS/meta-disciplines/doc-tag-vocabulary.md` · `DOCS/CODE_TAG_TEMPLATES.hpp` · `DESIGN_SPECS/doc-disciplines/in-code-doc-system-north-star.md` |
| The living sprint plan | `plans/v5.15-live-readiness/subplans/2026-07-05-E.1.2.A-comment-system-and-doc-consolidation.md` |

## How to …

- **Add a CI check over the tags** → a Python checker (the authoritative layer) with a `--selftest`
  (planted-bad fails + known-good passes) → wire into `check_session_docs.sh`. Cut over to a foxtag
  command later, behind `parity_check.sh`.
- **Add a foxtag command / producer** → `foxtag_main.cpp` + `foxtag.hpp`; extend `parity_check.sh` with
  a byte-identical section vs the Python authority. (Pending: a `code-units` producer — the raw
  struct/registry inventory the completeness check needs, so it can cut over from Python.)
- **Query the corpus** → `foxtag units --tag SLOW_PATH --type STRUCT [--name X] [--json]` (the faceted
  query = the plugin's tag-browser data layer) · `foxtag unit <file> <line>` (innermost enclosing unit) ·
  `foxtag validate [paths]`.
- **Add a tag/vocab row** → `doc-tag-vocabulary.md` (1-line); the grammar-derived tools track it
  automatically (a `[TAG]` not in the vocab REDS the validator). `[REFERENCE]` ids must RESOLVE (CI).
- **Verify a tag conversion** → `lossless.py` (code byte-identical) → validator → `check_cache_layout --fix`
  (structs) → `check_conversion_completeness` (coverage). Build + suite stays baseline (comments-only).

## Memory

Toolchain-specific disciplines live HERE (this doc is the toolchain's always-loaded-when-editing memory).
Cross-cutting operator-collaboration rules still go to `memory/` (auto-loaded everywhere). When a
toolchain-only collaboration rule emerges (e.g. a foxtag-cutover gotcha), capture it as a `memory/`
file AND cross-link it here.

## Reach for more

- The engine invariants (H1–H22) do NOT govern here (dev-plane) — but the tools **enforce** them in the
  engine. Root `CLAUDE.md` § "How to find anything" indexes the doc system; the schema SSoT + the sprint
  plan carry the full grammar + roadmap.
- The toolchain's architectural thesis (one-parser-N-consumers · grammar-derived · the D-349 migration
  contract) is codified at `DESIGN_SPECS/framework-patterns/doc-intelligence-toolchain-architecture.md`;
  the every-guard-asserts-non-vacuity discipline at
  `DESIGN_SPECS/meta-disciplines/calibration-corpus-non-vacuity-discipline.md`.
