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

**T-index — cite these by ID.** An UNNUMBERED rule cannot be quoted into a review, a spec, or an agent
prompt — which is exactly how T2/T4 got rediscovered the hard way in E.1.2.B `0.3`. The engine has
H1–H22; this is the dev-plane's equivalent. (Bodies are the bullets below; the gotchas that are only
in the source are the section after.)

| ID | Invariant | Anchor |
|---|---|---|
| **T1** | ONE parser, N consumers — a re-implementation is a Class-18 mirror | D-337 |
| **T2** | Grammar DERIVED at runtime, never hardcoded into a tool | D-365 |
| **T3** | PLANE is a first-class gate; this toolchain is `[DEV_PLANE]` and self-hosts | D-367 |
| **T4** | Migration contract — Python stays CI-AUTHORITATIVE until a gated, soaked cutover (**PASS ≠ cutover done**) | D-349 |
| **T5** | Every guard asserts its OWN non-vacuity (planted-bad REDs **and** known-good passes) | Class-51 |
| **T6** | Comments-only + lossless; MARK never delete; tooling writes comments/docs, **NEVER engine logic** | D-380 |
| **T7** | The schema is LOCKED `[SCHEMA]_[v1.0]` — a grammar change is a `[SCHEMA]_[vN]` bump | D-346 |
| **T8** | Toolchain semver `X.Y.Z`, MAJOR tied to the `[SCHEMA]` contract; ONE `TOOLCHAIN_VERSION` SSoT | D-373 |
| **T9** | UPDATE is ONE codified action; GATES stay verify-only (flag-not-auto) | D-374 |
| **T10** | Tool-I/O = ONE envelope + a schema-as-DATA registry — read, never hardcoded | D-376/D-380 |
| **T11** | A toolchain/tag-system change runs the armed I→A sweep BEFORE implementation | D-383 |
| **T12** | Delegate implementation only where the acceptance oracle is TOTAL; PARTIAL ⇒ hand-review before commit | D-385 |

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
- **PLANE is a first-class discipline-gate; this toolchain self-hosts (D-367).** `[ENGINE]`/`[DATA_PLANE]`/
  `[MONITORING_PLANE]`/`[DEV_PLANE]` are a first-class GATING axis (path-derived value, a `FOREACH_PLANE`
  registry of `{constraints · valid [TAG] vocab · [DERIVED] axis-set}`). This toolchain is `[DEV_PLANE]` —
  functionality-over-latency; the engine H1–H22 / straddle-gate / register-fit do NOT apply here, but the
  toolchain still earns ENGINE-grade rigor because it's one-producer-N-consumers (a wrong fact fans out).
  Going-forward: the toolchain SELF-HOSTS — foxtag C++ tagged (same `//`), the Python checkers (`#`) + Lua
  plugin (`--`) after the multi-comment-syntax parser lands. DEV_PLANE `[DERIVED]` is pipeline-reality
  (grammar-fences-read / parity-status / call-graph), never the engine's compiled-reality axes.
  → `doc-intelligence-toolchain-architecture.md` § plane-first-class (D-367).
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
  H21 tombstone discipline) — **never a code deletion.** **Tooling WRITES comments / `[DERIVED]` fact-blocks /
  index-docs ONLY — it NEVER generates or rewrites engine LOGIC (D-380).** `codegen` (instr/branch/SIMD) is
  read-only + LIVE-only (never persisted — flips with `-O`/`-march`); `check_cache_layout --fix` rewrites the
  derived COMMENT, never the struct. Auto-generated engine code is a Knight-adjacent trust hole on a capital
  path (same verification burden as hand-written → buys nothing); operator-skepticism is the calibrated posture.
- **The schema is LOCKED (`[SCHEMA]_[v1.0]`, D-346).** A grammar change = a `[SCHEMA]_[vN]` bump,
  coordinated across foxtag + the validator + the plugin (the stable contract = {closed vocab · section
  ladder · one-category-per-line · the `====` block structure}). Don't drift a tool off the locked grammar.
- **Toolchain VERSIONING — semver `X.Y.Z`, MAJOR tied to the `[SCHEMA]` contract (D-373).** The toolchain is a
  dev-plane PRODUCT: `MAJOR.MINOR.PATCH`, where a `[SCHEMA]_[vN]` grammar bump = the MAJOR (it ripples to every
  consumer); MINOR = a new surface/producer/capability (incl. additive vocab rows — they don't bump the schema);
  PATCH = a fix. One SSoT `tools/TOOLCHAIN_VERSION` every surface reports (foxtag `--version` · plugin
  `:checkhealth` · CI banner). `0.x` until the cohesive V1 → `1.0.0`. NOT the engine's wire-bound `.F.4d` cadence
  (that constraint doesn't apply here). Spec: `doc-disciplines/toolchain-semantic-versioning.md`.
- **UPDATE is ONE codified action; GATES stay verify-only (D-374).** Propagating a change
  (vocab/grammar/derived-facts/indexes/parity) is a single orchestrated skill — regenerate all WRITTEN derived state
  + indexes from ground truth in dependency order, IDEMPOTENTLY (D-369 stamp-on-change), verify-after — NOT a
  remembered N-step ritual (that's what drifts). The CI gates READ (red on drift); the update skill WRITES (how you
  fix drift). Never a hook that silently rewrites files ("flag-not-auto", per `[OUTDATED_INFO]`). Spec:
  `framework-patterns/one-action-toolchain-update-orchestrator.md`.
- **Tool-I/O = ONE envelope + schema-as-DATA registry (D-376/D-380).** Every producer/gate emits the standardized
  `{envelope, payload:{schema, rows}}` (single-doc JSON) via ONE emit helper that READS each `kind`'s schema+version
  from a **language-neutral registry** (a data file BOTH the C++ core + the Python tools read — NEVER a per-language
  hardcode, which would be the Class-18 mirror). `status.findings` unifies producers + gates. Add/evolve a kind = 1
  registry row; every producer+consumer tracks it. `.toolbus/` = the gitignored latest-wins rendezvous. The
  "grammar-DERIVED, never hardcoded" law raised to payload + gate schemas. `foxtag <cmd> --json` emits the
  COMPLETE self-describing envelope (D-382; the frame data-driven off the registry — two readers, one source,
  the `Version.hpp` model), so a direct subprocess consumer gets a full envelope. Spec:
  `framework-patterns/standardized-tool-io-envelope-and-payload.md`.
- **Toolchain / tag-system change → run the armed I→A agent sweep BEFORE implementing (D-383).** The toolchain +
  the in-code tag system are one-producer-N-consumers: a change to the tool-I/O / schema registry / vocab /
  `[SCHEMA]` grammar fans out across foxtag + the `check_*` family + the plugin + every tagged unit — a local-looking
  edit can ripple. Rerun the armed I→A cascade (scaled to the change; arm per `DOCS/SUBAGENT_ARMING.md`) scoped to the
  WIDER toolchain + tag-system blast radius, not just the edited file, before coding. Correctness-critical despite
  dev-plane (a wrong fact fans out). Re-fires on a materially-corrected shape.

## Tool invariants + gotchas (facts that live ONLY in the source — add new ones HERE)

Harvested 2026-07-19 from E.1.2.B `0.1.5`/`0.3`, where **each of these cost a debug cycle or produced
a FALSE finding**. If you discover a tool behaviour that is not derivable from its `--help` or its
docstring, write it here — that is the entire point of this section.

- **`foxtag` is CWD-SENSITIVE — run it from the ENGINE ROOT.** It resolves the corpus relative to
  `cwd`; a consumer inheriting some other cwd (an editor, a hook) fails with *"cannot resolve the
  engine root."* Resolve the root by **MARKER** (`Version.hpp`) + sibling probe, **never** by walking
  up from the binary — `tools/` is a SYMLINK, so a path-walk lands in the WORKSPACE, which has no
  marker (Landmine 5). Worked references: `nodemodel.lua` (Lua), `foxroots.py` (Python).
- **The "is this file converted?" selector is ANCHORED: `^// \[SCHEMA\]_\[v1`.** An UNanchored
  `rg '\[SCHEMA\]_\[v1'` ALSO matches selftest fixture **string literals** (`"// [SCHEMA]_[v1.0]\n…"`
  inside `SELFTEST[]`) and prose — it will report `foxtag_main.cpp` as converted when it is not.
  This produced a false in-session finding; verify by READING what matched, not by counting matches
  (`feedback_verify_by_context_not_count`).
- **`check_conversion_completeness` covers STRUCTS + FOREACH registries ONLY** (C1 lumped · C2
  missing-block · C3 missing-`[DERIVED]`). **FUNCTIONS are never checked for a missing block** — a
  latent hole: function-level tag coverage can drift and stay green indefinitely.
- **That same gate is BLIND to gitignored source** — it enumerates via `rg` WITHOUT `--no-ignore`, so
  a gitignored-but-real file is never scanned; "0 gaps" then means *unverified*, not *clean*
  (TECH_DEBT-245).
- **`tools/lib/*_baseline.txt` are EXCEPTION lists, NOT goldens.** They grandfather known-bad findings
  (shrinking). They do **not** pin a tool's OUTPUT — and **no tool pins its output today**, so a
  change to what a tool EMITS passes every gate provided both implementations change together
  (D-386 adopts output goldens to close exactly this).
- **`[DERIVED]` is required for `[STRUCT]` blocks, not for functions.** Function facts (call-graph,
  branches, SIMD) are shown **LIVE** by the plugin (D-307/D-327), so a struct-less file legitimately
  carries zero `[DERIVED]` — that is not a gap.

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
