---
type: framework-pattern
stage: 3-first-canonical
established: 2026-07-17
tags: [framework-discipline, ssot, doc-discipline, structural-fix]
surface: [ci-tooling, doc-pipeline]
sister_specs: [doc-disciplines/in-code-documentation-schema.md, framework-patterns/registry-tuple-as-single-source-of-truth.md, meta-disciplines/calibration-corpus-non-vacuity-discipline.md, meta-disciplines/mechanical-verification-of-derived-code-facts.md]
sister_docs:
  - tools/CLAUDE.md                  # the dev-plane toolchain orientation (always-loaded when editing tools/)
  - DOCS/RECURRING_BUG_PATTERNS.md   # Class 18 (parallel-mirror) — the anti-pattern this architecture kills at the doc layer
applications:
  - 'foxtag core (tools/foxtag/) — single tag-parser + fact-producer (units/unit/validate/layout/codegen) + query engine; CI checks + the fox-symdeps plugin + the shell are thin clients (D-337)'
  - 'grammar DERIVED at runtime from the schema category-set fence + doc-tag-vocabulary.md — fold a fence/vocab row -> every tool tracks it, zero code edits (D-322/D-346)'
  - 'Python->foxtag migration contract (D-349) — Python CI-authoritative until a per-consumer parity_check.sh-gated cutover (layout/codegen/validate/units cutovers parity 8/8, D-349..D-352)'
---

# Doc-intelligence toolchain architecture — one parser, N consumers over a locked grammar

**Established:** 2026-07-17 (retroactive codification of the E.1.2.A toolchain arc, D-306..D-363). The dev-plane doc-intelligence layer — the C++ `foxtag` core + the Python checker family + the Neovim `fox-symdeps` plugin — is a self-hosted code-intelligence + living-documentation system over the LOCKED `[SCHEMA]_[v1.0]` in-code tag grammar (the bespoke version of what Kythe/Glean or Sourcegraph+Swimm+Semgrep sell in pieces). This is its architectural thesis. **The engine Hard Invariants (H1-H22) do NOT govern this plane** — it's `-std=c++20 -O2`, gitignored, never linked into the engine; this pattern IS the dev-plane's discipline.

## The thesis — one core, N thin clients (D-337; Class-18 at the doc layer)

Code = hub, `[TAG]`/`[REFERENCE]` = edges, workspace docs (decisions/specs/invariants/memories) = nodes. **`foxtag` is the SINGLE tag-parser + fact-producer + query engine.** Every consumer — each CI check, the plugin, your shell — is a THIN CLIENT of that one core, so the grammar + the facts exist in exactly one implementation. A checker/plugin/skill that RE-implements block-parsing is a **Class-18 parallel mirror**; a new capability is a foxtag producer/command consumed by all, NOT a private re-parse. (The engine's `registry-tuple-as-single-source-of-truth` — one registry, N expansion sites — is the exact sibling one plane up; this is its doc-layer twin.)

## Grammar DERIVED, never hardcoded

The closed category set + the `[REFERENCE]` sub-cats are read at RUNTIME from the schema's ` ```category-set ` / ` ```reference-subcats ` fences; the `[TAG]` vocab from `doc-tag-vocabulary.md`. Fold a fence/vocab row -> **every** tool tracks it with zero code edits. NEVER hardcode the grammar into a tool (that forks the SSoT — the drift this whole system exists to kill). `foxtag.hpp` states it verbatim: *"GRAMMAR IS NEVER HARDCODED (anti-Class-18)."*

## Vocab/grammar propagation stays 1:1 — `foxtag grammar` is the SSoT-emitter seam (the plugin is the watch-point)

Adding vocab (a `[TAG]` value / a category / a `[REFERENCE]` subcat / a `[DERIVED]` axis) MUST be a ONE-site fold — one row in the schema fence or `doc-tag-vocabulary.md` — that every consumer inherits, NOT an N-site manual sync (the anti-Class-18 thesis applied to the grammar ITSELF, not just the facts). Mechanism:

- **Producers READ the fence at runtime.** The Python checkers (`load_categories` / `load_vocabulary` / `load_ref_subcats`) and the `foxtag` core both derive the grammar from the schema fences → a folded row tracks for free, zero code edits. **`foxtag grammar` emits the fence-derived grammar as data** — the SSoT-emitter a downstream consumer reads instead of hardcoding.
- **Every consumer is fence-derived OR parity-gated.** `parity_check.sh` §3 gates Python↔foxtag `grammar`. A consumer that hardcodes any grammar slice AND sits outside the parity loop is a **Class-18 drift site** — it silently lags the next fold.
- **The plugin (`fox-symdeps.nvim`) is the current watch-point.** It makes ZERO `foxtag` calls and is a native-Lua mirror: `tag_grammar_adapter.lua` self-describes as mirroring the Python parse rule (`:1-6`), and hardcodes the unit-type set (`UNIT`, `:27`) + the `[DERIVED]`-axis rendering + drift-checks (`format_derived` / `verify`, `:63-92`). The parse RULE is grammar-agnostic (a new *category* needs no plugin edit), but a new *unit type* or *DERIVED axis* does, and the parse-rule mirror must track the Python one. **The 1:1 fix (D-349 direction):** the plugin consumes `foxtag grammar` (category/unit/axis sets) + `foxtag unit <file> <line>` (parse) as a thin subprocess client, retiring the mirror → a fence fold reaches the plugin for free. Interim guard until then: a **plugin↔foxtag grammar parity section in `parity_check.sh`** (a hardcoded plugin set that diverges from `foxtag grammar` REDs).

**Standing rule:** a new consumer of the tag grammar reads `foxtag grammar` / `foxtag unit`, or earns a `parity_check.sh` section. No consumer holds grammar the fence doesn't feed it. (Decision log D-365; the vocab-side twin of the D-349 fact-side migration contract below.)

## The migration contract — Python CI-authoritative until a parity-gated cutover (D-349)

The system carries TWO implementations of the parse/producer layer during its build-out: the Python checkers (authoritative) and the C++ `foxtag` core (the destination). The contract that keeps this from being a two-implementations-drift hazard:

- The **Python** tools (`check_code_tag_blocks` / `check_cache_layout` / `check_conversion_completeness` / `rebuild_doc_indexes`) are **CI-AUTHORITATIVE**.
- No consumer cuts over to `foxtag` until `tools/foxtag/parity_check.sh` PASSES for it — **per-consumer, behind the gate, with a soak**.
- **PASS != cutover done; it means cutover is ALLOWED.** The gate proves byte-identical output; the human still flips the switch.

This is the general shape for migrating ANY consumer from an old implementation to a new core: keep the old one authoritative, gate the new one on byte-parity, cut over per-consumer behind the gate. First canonical: the layout + codegen + validate/units cutovers (parity 8/8; D-349..D-352). The still-pending `code-units` producer (the completeness gate's cutover, D-361/D-363) is the next application.

## The load-bearing invariants (the dev-plane's own H-rules)

- **Comments-only + lossless.** A conversion/cleanup changes ZERO code bytes (`lossless.py`-gated: comment-stripped diff == git HEAD). The tags document the code; they never rewrite it.
- **MARK, never delete.** A rotted/legacy/deletion-candidate UNIT gets a `[DEPRECATED]` / `[MARKED_FOR_DELETION]` marker (sister to `[OUTDATED_INFO]` for stale COMMENTS + the H21 tombstone discipline for wire identifiers) — never a code deletion (D-360).
- **The schema is LOCKED (`[SCHEMA]_[v1.0]`, D-346).** A grammar change = a `[SCHEMA]_[vN]` bump coordinated across foxtag + validator + plugin (the stable contract = {closed vocab · section ladder · one-category-per-line · the `====` block structure}).
- **Every consumer asserts its own non-vacuity** -> `calibration-corpus-non-vacuity-discipline.md`.
- **Coverage is a correctness property.** For tool-consumed tags, PARTIAL is unreliable (a half-tagged code-map/DAG can't be trusted); the CONVERSION completeness gate (C1/C2/C3) + the DERIVED coverage (C4) make "every unit blocked + every fact materialized" a CI-gated property, not a hope (E.1.2.A, D-359/D-363).

## Where it lives

`tools/CLAUDE.md` is the always-loaded-when-editing orientation (the piece map + the how-to); this spec is the pattern body (the WHY + the reusable thesis). The grammar SSoT is `in-code-documentation-schema.md`; the target end-state (the custom IDE) is `in-code-doc-system-north-star.md`.

## Sister disciplines

- `in-code-documentation-schema.md` — the LOCKED grammar this toolchain is built over.
- `registry-tuple-as-single-source-of-truth.md` — the engine-plane sibling (one registry, N sites); this is the doc-plane analogue (one parser, N consumers).
- `calibration-corpus-non-vacuity-discipline.md` — how every consumer proves it can fail.
- `mechanical-verification-of-derived-code-facts.md` — the DERIVED-fact half (facts are tool-written + CI-checked, never hand-commented; the emitter's coverage-boundedness, D-363).
- Class 18 (RECURRING_BUG_PATTERNS) — the parallel-mirror anti-pattern this architecture kills at the doc layer.
