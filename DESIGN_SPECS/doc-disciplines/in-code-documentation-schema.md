---
type: doc-discipline
stage: 2-draft
version: 1.0
established: 2026-07-05
tags: [doc-discipline, meta-discipline, ssot, structural-fix]
surface: [ci-tooling, doc-pipeline, test-infrastructure]
sister_specs: [doc-tag-vocabulary.md, categorical-tag-applicability-pattern.md, mechanical-verification-of-derived-code-facts.md, file-size-split-discipline.md]
applies_at_skills: []
---

# In-code documentation schema (the tag-block convention — SSoT)

**Established:** 2026-07-05 (design captured in decision-log D-306; formalizes the `====`-block sketches Caramel began in the `deep_dives` folder). **Origin:** a one-line latency-tool `[LAT_EXEMPT]` marker generalized into a full navigable in-code documentation system for the in-house fox-symdeps dev environment.

**Status:** Stage 2 DRAFT v1.0. First canonical of the `[DIRECTIVE]` axis = the `check_latency_path_conformance.py` `[LAT_EXEMPT]` marker. Full-convention first-canonical = the codebase conversion pass (deferred; see § Conversion + Rollout).

---

## Purpose

A single, standardized, tool-parseable convention for in-code documentation that:
- **kills comment SPRAWL** — the WHY/history/diagrams move to a structured block ABOVE the unit; the body stays readable (`ExecutionCore` was ~100 lines of interleaved comments smothering ~30 lines of fields);
- **kills comment DRIFT** — the facts that rot (sizes, dep lists, instruction budgets) are TOOL-generated + CI-checked, never hand-written;
- **is a navigable INDEX** into institutional memory — code is the hub, tags are edges, the workspace docs (decisions / specs / memories / invariants) are the nodes; grep + the plugin traverse the graph.

### Novel alternative considered — why not Doxygen?

Doxygen (and clang-doc / standardese) generate API-reference HTML from `///` comments. Rejected as the primary: (a) it targets *published API docs*, not in-buffer *navigation*; (b) no institutional-memory linking (decisions / invariants / audits) and no DERIVED-fact CI-checking — the two things that make this drift-proof + navigable; (c) heavyweight generation step vs plain `rg` + a light index. This convention is grep-native and tool-agnostic; a Doxygen pass can still run *alongside* it (the `[WHY]`/`[DIAGRAM]` prose is Doxygen-compatible) if API HTML is ever wanted.

---

## The three invariants (the whole standard)

**1. One PARSE rule.** Every structured comment line is `// [CATEGORY]…`. The ENTIRE parser is one innermost-bracket regex — `\[([^\[\]]+)\]`. Token[0] = CATEGORY (a closed ALL-CAPS set); the rest are values. The outer list-grouping `[[a] [b]]` is non-innermost → skipped, so `[TAG]_[[SLOW_PATH] [ML]]` → `[TAG, SLOW_PATH, ML]` for free. No per-category regex, no naming-convention parsing.

**2. One SECTION ORDER** (the "access ladder" — CI-enforced, so it's guaranteed not hoped-for):
```
[FILE] / [STRUCT] / [FUNCTION] / [REGISTRY]   →  WHAT it is
[TAG]                                          →  CLASSIFY (surface/concern)
[WHY]  /  [DIAGRAM]                            →  UNDERSTAND
[DERIVED]                                      →  the FACTS (auto, CI-checked)
[VERSION]                                      →  WHEN it changed
[REFERENCE]                                    →  DRILL-OUT (specs/decisions/invariants)
[END_*]                                        →  fold-range / jump-nav close
```
Reading top-down IS the comprehension path.

**3. One COMPOSE recipe** — orthogonal axes (unit / classify / when / where) intersect in any order, identical to `doc-tag-vocabulary.md § Retrieval recipes`, now over code:
```
rg -l '\[TAG\]_\[\[SLOW_PATH'  |  xargs rg -l '\[VERSION\]_\[v5.15'  |  xargs rg -l '\[REFERENCE\]_\[DESIGN_SPEC\]_\[cache'
```

---

## Line & wrapping rules (keep the parse trivial)

- **ONE category per line.** Each structured line carries exactly one `[CATEGORY]` (token[0]) — NEVER two. This is what makes "token[0]=category, rest=values" hold; a second category on the line would force a vocab-aware segmenting parser (the complexity we're avoiding). So `[REFERENCE]_[AUDIT]_[…]` and `[REFERENCE]_[INVARIANT]_[[H4] [H8]]` are SEPARATE lines; `[TAG]` and `[SCHEMA]` are separate lines. One fact per line → one grep hit per fact.
- **All metadata is BRACKETED — no loose text.** Every tag value is wrapped: `[OVERVIEW]_[ring-buffer ingest …]`, NEVER `[OVERVIEW]_ ring-buffer …`. Freeform prose lives ONLY in the two delimited content-regions below.
- **Value lists: inline when short, BLOCK (YAML-style) when long.** Short list inline: `[CONSUMERS]_[[A] [B]]`. A list that would wrap uses the block form — the category alone as a header, each value on a following `- `-prefixed line (YAML list marker):
  ```
  // [SUPPORTING_DOCS]
  //   - [INVARIANT]_[H7]
  //   - [DECISION]_[D-188]
  ```
  **Parse:** a category line WITH value-brackets = inline; a category line with NO values = a block header whose values are the following `//   - [X]` lines (until the next `[CATEGORY]` or `====`/`——`/`----` bar). Grep finds the header AND each value either way. Block form ONLY when it would wrap.
- **The TWO freeform content-regions** — a `[COMMENT]` partition body + a `[DIAGRAM]` body — span from their header to the next `[CATEGORY]` or bar (continuation lines need no prefix). These are the ONLY places prose sits un-bracketed; they are delimited *content*, not loose metadata. (The templates + worked examples below are in the final hybrid form.)

## Coverage — what gets a block

| Unit | Block? | Notes |
|---|---|---|
| Struct / class (esp. layout-critical: `alignas`, bit-packed, wire-serialized) | **YES — full** | the `[DIAGRAM]` byte-map is the payoff |
| Function (esp. hot/slow-path kernels, delegates, gates) | **YES — full** | |
| `FOREACH_*` X-macro registry | **YES — `[REGISTRY]` shape** | row-count = DERIVED; MetaRegistry enrollment = `[REFERENCE]`; the wire/section it drives = `[TAG]` |
| File (a `.hpp`/`.cpp` header) | **YES — `[FILE]` shape** | a data-flow `[DIAGRAM]` + the file's role; the "sub-file" TOC anchor |
| Trivial struct (≤3 POD fields) / one-liner / obvious getter | **NO** — terse inline only | proportionality: ceremony on the trivial is its own sprawl |

**Granularity:** one block per unit (struct / function / registry / file). Individual struct fields get OPTIONAL terse inline tags (`// hot read`, `// [H12_PAD]`), never prose. Nested types get their own block if non-trivial.

**Inline field comments + sub-group headers STAY in `[CODE]` — verbatim (D-326).** Converting a unit relocates ONLY the *unit-level* WHY prose (what the whole unit is + why) to `[COMMENT]`. The existing per-field inline comments (`FPN_Binary<F> short_slope; // relative price slope`) and the sub-group section headers that organize the body (`// short window (128-tick)`, `// derived signals`) are **field-LOCAL documentation** — they stay inside `[CODE]`, unchanged. They are read *at the field*, where the reader needs them; stripping them out into `[COMMENT]` would destroy the field↔doc locality that makes a densely field-documented struct (e.g. `RegimeSignals` — 40+ signal fields, each annotated) readable at all. Rule of thumb: **does the comment explain the WHOLE unit (→ `[COMMENT]`) or a single field/sub-group (→ stays inline in `[CODE]`)?** Preserve-voice applies to both — verbatim on relocation, verbatim in place.

---

## Category set (closed vocabulary)

| Category | Grammar | Value source | Tier |
|---|---|---|---|
| `[FILE]`/`[STRUCT]`/`[FUNCTION]`/`[REGISTRY]` | `_[name]` | the identifier | curated |
| `[TAG]` | `_[[a] [b] …]` | doc-tag-vocab SURFACE + CONCERN axes (UPPER_SNAKE render) | curated |
| `[SCOPE]` | `_[DEPLOYMENT\|CLUSTER\|NODE\|CORE]` | the shard SCALE-LEVEL the unit's state/logic lives at (glossary §15 · H22 scale-invariance; `ExecutionCore`/CPU-core = CORE) — plugin can flag an H22 violation (a per-NODE unit reading a `core_N_*`-overridden global) | curated |
| `[WHY]` | `_ prose` | judgment | curated |
| `[DIAGRAM]` | `_[kind]` + ASCII body | judgment (ASCII byte-map / bit-map for packed fields / data-flow map) | curated intent / DERIVED-checkable |
| `[DERIVED]` family (build-flags/size/align/cache-lines/straddle/branches/float/deps/consumers/tested-by/instr-budget/blast-radius) | `_[SUBCAT]_[val]` | **tool-refreshed in-comment** — generated from clangd / `gen_code_map`, CI-checked vs ground truth, NEVER hand-edited (D-307 fork b) | machine-derived |
| `[ITERATIONS]` | `_[n]` | **DERIVED** — git-churn count (commits touching the unit) → hot-spot detector; tool-refreshed + CI-checked (D-306) | machine-derived |
| `[DETAIL]` | `_ rich prose (block)` | judgment (`deep_dives` LR-narrative style; author's voice) | curated |
| `[EDIT]` / `[VERSION]` | `_[[date-or-version]]` + prose below | judgment (`deep_dives` `[EDIT [14-03-26]]` style) | curated |
| `[REFERENCE]` → `[DESIGN_SPEC]` `[MEMORY]` `[DECISION]` `[TECH_DEBT]` `[CLASS]` `[INVARIANT]` `[PLAN]` `[AUDIT]` | `_[SUBCAT]_[id-or-path]` | workspace artifact id (pointer must RESOLVE — CI). `[DOC]`-sync DROPPED (D-307): rich prose lives in-comment as `[DETAIL]`, not a drift-prone external pointer | curated |
| `[DIRECTIVE]` → `[LAT_EXEMPT]` (+ future `[H12_PAD]`/`[TODO]`) | `_[reason]` on the governed line | machine-read | curated |
| `[FUTURE_WORK]` → `[TECH_DEBT]` `[PLAN]` | `_[SUBCAT]_[id]` | a tracked FORWARD pointer (code twin of a doc's future-expansion; must RESOLVE — CI) — distinct from `[REFERENCE]` which governs/explains (D-306) | curated |
| `[SCHEMA]` | `_[vN]` | the convention version | meta |
| `[CODE]` / `[END_CODE]` | (none) | **body-range delimiter** — explicitly brackets the code body so the DERIVED size-tool + the plugin's cursor-position tracking read an exact PARSED range (the `====` bars are render-only, can't serve this) (D-306) | structural |
| `[END_*]` | `_[name]` | close delimiter (`[END_FUNCTION]`/`[END_STRUCT]`/`[END_REGISTRY]`/`[END_CODE]`) | structural |

Vocab is **1-line extensible** (per `doc-tag-vocabulary.md`); add tags at real use-sites, don't pre-enumerate. `[LATENCY_CRITICAL]` etc. are synonyms of existing SURFACE tags — fold, don't add. **⚠ The validator is LIVE (CI-wired):** a `[TAG]` value not in `doc-tag-vocabulary.md` throws `not in doc-tag-vocabulary` immediately. **✅ RECONCILED — D-322 (2026-07-05):** the component/plane family (`[ENGINE]`/`[ML]`/`[GUI]`/`[DATA_PLANE]`/`[MONITORING_PLANE]`/`[DEV_PLANE]`) + the classify family (`[CAPITAL_BEARING]`/`[NON_CAPITAL]`/`[DECIMAL]`/`[BINARY_FP]`/`[INT]`/`[FLOAT_DISPLAY_ONLY]`/`[FROZEN]`/`[GOLDEN]`/`[CRITICAL]`/`[SUPPORTIVE]`/`[HELPER]`/`[ENTRY_POINT]`) are now IN the vocab (18 new rows — operator's new-rows-for-granularity call) → they validate. **⚠ 4 REUSE-BY-RENAME (SSoT — NOT new rows):** write `[OMS_DRAINER]` / `[DETERMINISM]` / `[PERSISTENCE]` / `[BITMAP_PACKED]` (they map to existing `oms-drainer`/`determinism`/`persistence`/`bitmap-packed`), NOT `[DRAINER]`/`[DETERMINISTIC]`/`[PERSISTED]`/`[BIT_PACKED]` — those RED. The authoritative full classify+component set is `plans/v5.15-live-readiness/subplans/2026-07-05-E.1.2.A-readout-axes-and-classify-vocab.md` § classify + the landed rows in `doc-tag-vocabulary.md`.

### Closed category set — machine-readable SSoT (the validator DERIVES from this, never mirrors it)

`check_code_tag_blocks.py` parses THIS block for the closed set (single-source: folding a disposition category = adding one token here → the validator tracks it automatically, no code edit). Whitespace-separated tokens; `#`-comments ignored; `[END_*]` is validated by prefix, not listed. These are every token that appears as `token[0]` on a structured line (top-level categories + the DERIVED subcats that head their own lines + the curated structural annotations).

```category-set
FILE STRUCT FUNCTION REGISTRY STRATEGY ENUM TYPE MACRO TEST
TAG SCOPE SCHEMA OVERVIEW WHY DETAIL DIAGRAM COMMENT SUPPORTING_DOCS EDIT VERSION REFERENCE DIRECTIVE FUTURE_WORK CODE
DERIVED SIZE SIMD FLOAT BRANCHES BUILD INSTANTIATION ALIGN CACHE_LINES STRADDLE UPSTREAM CONSUMERS ROW_COUNT ENROLLED ALIGNED_CONSUMERS ITERATIONS BLAST_RADIUS
CONTAINS TOC INCLUDES INCLUDED_BY BINARIES
THREAD SYNC BIT_PACKED PADDING WIRE_FORMAT PERSISTED LAT_EXEMPT
```
**Disposition categories NOT YET in the fence above** — `REGION` `COMPLEXITY` `APPLY_AFTER` `MUTATES` `SPILLS` `DOMAIN` `ROUNDING` `OVERFLOW` `FAULT_SIGNAL` `SEAM` `GATED_BY` `WIRE_VERSION` … These are PROPOSED for the variant surfaces (enum / wire / type / …). **The validator throws `UNKNOWN category` on each until it is folded into the ` ```category-set ` block above** — so **fold each WHEN its variant is first piloted**, not before (`WIRE_VERSION` in particular is an OPEN decision: full variant vs DERIVED-under-`[REFERENCE]` — pre-pilot decision #1). ⇒ the proven-surface pilot (function / struct / registry) stays clear of them by construction; a variant pilot folds the ones it needs first.

**`[INSTANTIATION]` FOLDED (D-318, standalone set-valued):** `[INSTANTIATION]_[[<args>] …]` — the concrete template-arg tuples a template unit is instantiated at (e.g. `FixedPoint` → `[[2,64] [10,8]]`, `RollingStats` → `[[128] [256] [512] [1024]]`). The DERIVED size/layout facts become PER-instantiation, and the plugin's size-probe reads it as its substitution list (fixes the injected-class-name probe failure — a bare `Foo<PARAM>` isn't sizeof-able). Chosen over folding into `[BUILD]`: `[BUILD]` pins compiler FLAGS (one set per file), `[INSTANTIATION]` pins template ARGS (a SET) — different axis + cardinality.

### `[REFERENCE]` subcats — machine-readable SSoT + resolution table (the resolver DERIVES from this)

`[REFERENCE]_[SUBCAT]_[id]` (and the `[SUPPORTING_DOCS]` block-form `- [SUBCAT]_[id]`) point at workspace artifacts; the resolver (`check_code_tag_blocks.py` `[REFERENCE]`-resolution increment) checks each id RESOLVES (dangling = CI red). ⚠ **Only the subcat MEMBERSHIP (col 1) is data-driven** (fold a subcat the resolver already handles = one row here). Unlike the ` ```category-set ` block, the SOURCE (col 2) is a per-subcat resolution CODE PATH (glob `DESIGN_SPECS`, grep CLAUDE.md H-numbers, union-grep decision-logs) — a NEW subcat with a new source SHAPE needs a resolver code edit, not just a row.

```reference-subcats
# SUBCAT       SOURCE (where the id resolves)                                   ID-FORM               NOTES
DESIGN_SPEC    DESIGN_SPECS/**/<id>.md                                          kebab-basename (no .md)
MEMORY         <memory-dir>/<id>.md                                             snake_basename (no .md)
DECISION       UNION of plans/**/decision-logs/*.md ("D/C/F: D-<n>")            D-<n>                 D-numbers RESTART per log → resolve against the union; membership only
INVARIANT      CLAUDE.md Hard-Invariants table                                  H<n>                  H1..H22
TECH_DEBT      DOCS/TECH_DEBT.md + DOCS/tech-debt/{open,in-flight,closed}.md    TECH_DEBT-<n>
CLASS          DOCS/RECURRING_BUG_PATTERNS.md ("Class <n>")                     <n> bare int          match zero-padded "Class 0*<n>"
PLAN           plans/**/*.md                                                    path-or-basename
AUDIT          EXISTENCE-UNCHECKED — audits are scattered (no single ledger)    free                  advisory-only until an audit index exists; resolver does NOT red on AUDIT
```

### Structural + concurrency annotations (register the vocab; apply as-encountered)

Design classifications a tool can't infer — the author declares them. Register the known set so it's consistent + not forgotten (`doc-tag-vocabulary` is 1-line extensible); APPLY each at its first real unit during conversion, never pre-stamp. The byte/bit **breakdown** is the `[DIAGRAM]`'s job (byte-map + bit-map), NOT a per-field tag explosion.

- **Packing (layout)** — `[BIT_PACKED]` (H14: manual `MASK_`/`SHIFT_`/`BITMAP_`/`MBS_` over `uint{8..64}_t`, never C++ bitfields) → the `[DIAGRAM]` carries the **bit-map** (what each bit / bit-group encodes). `[PADDING]` (H12 byte-equivalence).
- **Cross-thread mechanism** — a curated `[SYNC]` line (mirrors `[THREAD]`): `[SYNC]_[SEQ_LOCK]` (slow→hot config cache) · `[SYNC]_[SPSC]` (producer→consumer ring) · `[SYNC]_[ATOMIC]` (cross-core flag/counter) · `[SYNC]_[LOCK_FREE]`.
- **Wire / persistence** — `[TAG]` concern-values `[WIRE_FORMAT]` (H9 HMAC body) · `[PERSISTED]` (snapshot-serialized).

A new sync primitive / packing scheme adds ONE vocab line at the first struct that needs it — the conversion surfaces it, so a forgotten annotation self-corrects (never a silent gap).

---

## Two tiers — the CURATED layer (human-written) vs the DERIVED layer (tool-written, CI-checked)

**Reframed 2026-07-05 (D-307), after reading `fox-symdeps.nvim`.** The plugin already derives the ENTIRE machine layer LIVE from ground truth (clangd + treesitter + `gen_code_map`): size, alignment, cache-line packing, vector-register fit, per-field layout, upstream `Uses`, role-classified `Consumers`, call directions, hot-path instruction budget, doc-mentions, byte-layout blast-radius. The open question was whether to ALSO materialize those facts in-comment or leave them plugin-live-only — a *hand-written* DERIVED tier would MIRROR what the plugin shows = the **Class-18 anti-pattern this whole system exists to kill.** **Resolution (D-307, forks-resolved): DERIVED lives in-comment, but TOOL-REFRESHED** — generator-written from ground truth, CI-checked, never hand-edited. Class-18 only bites *hand* mirrors; a generated + build-gated snapshot cannot silently drift (the moment it does, CI goes red). So the fact is materialized where grep / GitHub / any editor sees it **without** the plugin, and the plugin fuses its live overlay on top.

- **CURATED — the human layer** (humans write; the compiler can't know it): `[WHY]`, `[DETAIL]`, `[TAG]`, `[EDIT]`/`[VERSION]`, `[REFERENCE]`, `[DIAGRAM]` (the author's mental model). Rationale, history, pointers — none mechanically derivable, so none drifts.
- **DERIVED — the tool layer** (the generator writes; CI verifies; NEVER hand-edited): size/deps/consumers/instr-budget/blast-radius, from clangd / `gen_code_map`, materialized in the block so it reads *without* the plugin. The plugin's HUD **fuses** its live overlay on top — your curated block PLUS the derived facts, always current. That fusion IS the polished GUI.

**What this buys:** the drift surface is **contained**, not wished away — the mirror exists, but it is tool-owned + build-gated, so it cannot silently rot: a `[DERIVED]` line that diverges from ground truth is a red build, not a lie. The stale-comment class (TECH_DEBT-226/228) is solved not by *removing* the fact from the comment but by making it **generator-written + CI-verified** — `mechanical-verification-of-derived-code-facts` applied to comments. (Reversible per D-307: if the plugin's live overlay ever makes the in-comment copy redundant, drop back to plugin-live-only — the grammar is unchanged either way.)

### Division of labor (schema ↔ plugin) — the parallel-work contract

The comment block is the **interface** between this schema (the format) and `fox-symdeps` (the consumer). Stable contract = **{closed category vocab · section ladder · one-category-per-line · the `====` bracket structure}**. Hold those stable and the two develop INDEPENDENTLY: changes *within* the contract (richer `[WHY]`, more examples) are free; changes *to* the contract (a new category, a new ladder slot) are the only coordination point — gated by a `[SCHEMA]_[vN]` bump. The plugin parses the block (one-rule grammar → group→tag→value) and overlays the live facts; the schema stays a minimal, co-evolving format. (H22-style clean seam: each side a pure function of the interface.)

**Plugin WRITE-role (D-319, bounded).** The plugin may WRITE, but only within the two tiers: **CURATED** (`[TAG]` / `[REFERENCE]` / `[WHY]` / `[OVERVIEW]` / `[DIAGRAM]`) = edit-assist (vocab-completion for `[TAG]`, live resolve-check for `[REFERENCE]`, `[SUPPORTING_DOCS]` insert); a whole block = **scaffold-generate** (DERIVED pre-filled from the fact-producers); **DERIVED** = **REGENERATE-only** from ground truth, NEVER hand-edited (a hand-edit that drifts is the Class-18 mirror this system exists to kill — DERIVED is effectively read-only in the buffer). Writers go through the SAME grammar + SAME fact-producers as the CI validator → a plugin-written block is CI-green by construction, and plugin-written DERIVED cannot disagree with CI-expected DERIVED (single-source the COMPUTATION, not two implementations). **Plugin writes, CI verifies — same grammar both sides.**

**DERIVED — WRITTEN vs LIVE-PREVIEW (D-327).** Not every derived fact is *written* into the block; split by STABILITY. **WRITTEN** = facts stable under a pinned build: struct **layout** (`[SIZE]`-bytes / `[ALIGN]` / `[STRADDLE]` / `[CACHE_LINES]` — Itanium-ABI-fixed → refreshed by `check_cache_layout.py --fix`) + the **call-graph** (`[UPSTREAM]` / `[CONSUMERS]` — source-fixed → written by the plugin's `:FoxSymdepsDerived!`). **LIVE-PREVIEW-only, NEVER written** = facts that flip with compiler flags/version or are meaningless without a concrete instantiation: instruction-count, `[SIMD]` usage, `[BRANCHES]` count. Writing a volatile fact makes the committed source a *lie* on the next `-O`/`-march` change — or reads `0 instr` for an un-instantiated template (the observed `CumDelta_Init<F>` case) — churning CI for zero signal. The plugin SHOWS them live (`:FoxSymdepsDerived` preview + the HUD asm view, which is *why* it asks you to instantiate); the source carries only the stable subset. **Per-unit-type writer:** STRUCT → `--fix` (layout); FUNCTION → `:FoxSymdepsDerived!` (call-graph). The generator **MERGES** (keeps the other writer's facts — a struct's `--fix` `[SIZE]` survives a plugin `[UPSTREAM]` write, and vice-versa), never clobbers. Materially: I hand-add the CURATED structure (orient / `[CODE]` with inline comments preserved / `[COMMENT]` / an empty `[DERIVED]` skeleton); the TOOLS fill `[DERIVED]` — **zero hand-written derived facts** (the anti-Class-18 whole point).

**Explicitly NOT done:** (a) HAND-writing or hand-editing a derived fact — the generator owns the `[DERIVED]` block and a hand-edit that drifts from ground truth fails CI (the tool/plugin refreshes it); (b) commented-out old/new code as diffs (git owns the diff; `[EDIT]` + `[REFERENCE]_[DECISION]` own the what/why).

---

## Templates (copy-paste skeletons — HYBRID layout: orient-above / code / detail-below)

### Function
```cpp
//======================================================================
// [FUNCTION]_[<Name>]
//----------------------------------------------------------------------
// [TAG]_[[<SURFACE>] [<CONCERN>]]
// [SCHEMA]_[v1]
// [OVERVIEW]_[<one-line gist>]
// [DIAGRAM]
//   <hand-ASCII — ASCII boxes (+--+ | +) + arrows (-> <- ^ v); NO Unicode glyphs>
//======================================================================
// [CODE]
//======================================================================
<signature> { <clean body — comments moved OUT> }
//======================================================================
// [END_CODE]
//======================================================================
// [COMMENT]
//——————————————————————————————————————————————————————————
// [[<YYYY-MM-DD>] [<version>]]
//----------------------------------------------------------------------
// <what this version does + why — prose; the freeform region>
// [SUPPORTING_DOCS]
//   - [<SUBCAT>]_[<id>]
//======================================================================
// [DERIVED]   (tool-refreshed by fox-symdeps; do NOT hand-edit)
//----------------------------------------------------------------------
// [BUILD]_[<canonical build.sh flags — e.g. -O3 -march=native; pins the asm-derived facts below>]
// [SIZE]_[<n instr>]
// [SIMD]_[<none|avx512>]
// [FLOAT]_[<n · H4-exempt if feature-math>]
// [BRANCHES]_[<data-dependent: n · H7/H20 branchless meter>]
// [UPSTREAM]_[[<types>]]
// [CONSUMERS]_[[<callers>]]
//======================================================================
// [END_FUNCTION]_[<Name>]
//======================================================================
```

### Struct (layout-critical)
```cpp
//======================================================================
// [STRUCT]_[<Name>]
//----------------------------------------------------------------------
// [TAG]_[[<SURFACE>] [DATA_ORIENTED_DESIGN]]
// [THREAD]_[[<HOT_WRITER> <SLOW_READER>]]   (CURATED — author-declared thread ownership; not clang-derivable)
// [SCHEMA]_[v1]
// [OVERVIEW]_[<layout-by-access-pattern gist>]
// [DIAGRAM]
//   line0: [<field:bytes>] .. = 64B    (byte-map; tool-verified vs offsetof)
//======================================================================
// [CODE]
//======================================================================
<struct> { … };
//======================================================================
// [END_CODE]
//======================================================================
// [COMMENT]
//——————————————————————————————————————————————————————————
// [[<date>] [<version>]]
//----------------------------------------------------------------------
// <the layout decision + why>
// [SUPPORTING_DOCS]
//   - [DESIGN_SPEC]_[<spec>]
//   - [INVARIANT]_[<H#>]
//======================================================================
// [DERIVED]   (tool-refreshed)
//----------------------------------------------------------------------
// [SIZE]_[<N>B]
// [ALIGN]_[<alignas — 64 for cross-thread, H6>]
// [CACHE_LINES]_[<n 64B lines spanned>]
// [STRADDLE]_[<none | field@off crosses a line → false-sharing risk>]
// [ALIGNED_CONSUMERS]_[[<types>]]
//======================================================================
// [END_STRUCT]_[<Name>]
//======================================================================
```

### Registry (`FOREACH_*` X-macro) — the "registry map"
```cpp
//======================================================================
// [REGISTRY]_[<FOREACH_NAME>]
//----------------------------------------------------------------------
// [TAG]_[[<SURFACE>] [FRAMEWORK_DISCIPLINE]]
// [SCHEMA]_[v1]
// [OVERVIEW]_[<what it single-sources; add/drop = 1 row + a version bump>]
//======================================================================
// [CODE]
//======================================================================
#define FOREACH_<NAME>(X)  X(...)  …
//======================================================================
// [END_CODE]
//======================================================================
// [COMMENT]
//——————————————————————————————————————————————————————————
// [[<date>] [<version>]]
//----------------------------------------------------------------------
// <why the registry exists / what it drives>
// [SUPPORTING_DOCS]
//   - [DESIGN_SPEC]_[registry-tuple-as-single-source-of-truth]
//   - [INVARIANT]_[H15]
//   - [INVARIANT]_[H21]
//======================================================================
// [DERIVED]   (tool-refreshed)
//----------------------------------------------------------------------
// [ROW_COUNT]_[<n>]
// [ENROLLED]_[MetaRegistry.hpp]
// [CONSUMERS]_[[<the walkers that expand it>]]
//======================================================================
// [END_REGISTRY]_[<FOREACH_NAME>]
//======================================================================
```
The registry DERIVED — `[ROW_COUNT]` · `[ENROLLED]` (its MetaRegistry row, H15) · `[CONSUMERS]` (the walkers, grep-derived) — IS the "registry map." Registries are the codebase's load-bearing pattern, so this is a first-class block (not a variant).

### File — the top-of-file MAJOR OVERVIEW (the 7-axis readout at FILE granularity)
`[FILE]_[<path>]` identity + `[TAG]_[[<component/domain>]]` (`[ENGINE]`/`[ML]`/`[GUI]`/`[XGBOOST]`/`[CORE]`… — vocab values, added as real files need them) + `[SCOPE]` (if the file is scale-bound) + `[SCHEMA]_[v1]` + `[OVERVIEW]` (what it's for) + a data-flow `[DIAGRAM]` + the **file-level graph**: `[CONTAINS]`/`[TOC]` (child units — the file's table-of-contents) · `[CONSUMERS]`/`[INCLUDED_BY]` (who uses it) · `[UPSTREAM]`/`[INCLUDES]` (what it pulls in) · `[BLAST_RADIUS]` (change-impact) · `[BINARIES]` (which build targets link it). Orient-block only (no code body). **Dual role:** the file's TOC anchor AND — via its `[SCHEMA]_[v1]` — the per-file conversion/whitelist marker (the CI validator polices a file only once it carries a `[FILE]` block; un-converted files are skipped, `[SCHEMA]_[exempt]_[reason]` opts one out). Same block anatomy as a function/struct → the tool + plugin parse per-FILE and per-UNIT uniformly.

### Variants for other unit types (anatomy-REUSE — tweak the `[DERIVED]`/`[REFERENCE]` set, NOT a new system; build each the first time a real unit needs it during conversion, do NOT pre-enumerate)
- **Strategy** — `[STRATEGY]_[<name>]`; `[TAG]` its regime-fit + op-mode, `[REFERENCE]` its params/spec. A strategy is just another tagged unit (fits the hybrid block exactly); a strategy-dev plugin lens renders a strategy-shaped view of the same facts (operator's domain).
- **Enum (persisted / wire CODES)** — `[ENUM]_[<name>]`; add `[REFERENCE]_[INVARIANT]_[H21]` + a tombstone note (Knight-Capital: append-only, never renumber/reuse a slot). The SHALT / halt-reason / regime / snapshot-version code enums live here.
- **Foundational typedef** (`Money`, `FPN_Binary<F>`, `EngineMoneyT`) — `[TYPE]_[<name>]`; `[SIZE]_[<sizeof>]` + `[REFERENCE]` to the encoding epoch / H4. The money-type SSoT warrants a block; a throwaway alias does not.
- **Macro** (`BITMAP_*` / `MBS_*` accessors) — LIGHT `[MACRO]_[<name>]` (no `[END]`; `[DERIVED]` = branchless?/expansion); most accessor macros stay terse-inline.
- **Test group** (`controller_test` Phase blocks) — `[TEST]_[<name>]`; `[REFERENCE]` to the invariant/decision each verifies → navigation across the 3697-test suite.

**Boundary (same as the tag rule):** the 4 first-class blocks (function / struct / registry / file) cover ~90%; the variants fill in organically. Build a variant when a real unit needs it — pre-designing all of them is *template* sprawl, the very thing this kills at the comment level.

---

## Worked examples

> **Illustrative — NOT the golden fixture.** These show block SHAPE. The `[DERIVED]` numbers are hand-written placeholders (some stale — sizes predating the 16B core) and MUST NOT be frozen as the self-test golden: the committed golden is TOOL-GENERATED from the P2 pilots (`sizeof`/`offsetof`/analyzer), never hand-authored — hand-writing DERIVED is the Class-18 drift the schema bans. They also predate `[CODE]`/`[END_CODE]` framing + the cache/branch DERIVED tags (added at lock); the pilots render the current form.

### Function — `Regime_Classify` (Strategies/RegimeDetector.hpp)
```cpp
//======================================================================
// [FUNCTION]_[Regime_Classify]
//----------------------------------------------------------------------
// [TAG]_[[SLOW_PATH] [ML_INFERENCE]]
// [SCHEMA]_[v1]
// [OVERVIEW]_[score-based regime classify — each signal +1, highest wins]
// [DIAGRAM]
//   RegimeSignals {slope, R2, ROR, vol, var}
//          |
//          v
//     trend / vol score  --highest-->  hysteresis  -->  regime
//======================================================================
template <unsigned F>
inline int Regime_Classify(RegimeState<F>* state, const RegimeSignals<F>* sig,
                           const ControllerConfig<F>* cfg) {
    if (sig->short_count < 64) return state->current_regime;   // cold start
    // signal scoring -> hysteresis -> regime
}
//======================================================================
// [COMMENT]
//——————————————————————————————————————————————————————————
// [[2026-04-01] [v5.7.1]]
//----------------------------------------------------------------------
// each signal +1 to a trending/volatile score, highest wins; hysteresis
// (hold N cycles) stops it flapping, RANGING is the default. extend by
// adding a RegimeSignals field + one compare here — the whole surface.
// exposed last_trending/volatile_score so the entry-quality log reads the
// real margin, not just the winning regime.
// [SUPPORTING_DOCS]
//   - [AUDIT]_[latency-conformance-kernel]
//   - [INVARIANT]_[H4]
//   - [INVARIANT]_[H8]
//======================================================================
// [DERIVED]   (tool-refreshed)
//----------------------------------------------------------------------
// [SIZE]_[~480 instr]
// [SIMD]_[none]
// [FLOAT]_[18 · H4-exempt]
// [UPSTREAM]_[[RegimeSignals] [ControllerConfig]]
// [CONSUMERS]_[[EventLoop_RebuildOneCore] [StrategyParameters_Dispatch]]
//   body: 1x [LAT_EXEMPT] env-gated cold-debug fprintf
//======================================================================
// [END_FUNCTION]_[Regime_Classify]
//======================================================================
```

### Struct — `ExecutionCore` (the sprawl exhibit: ~100 comment lines → this)
```cpp
//======================================================================
// [STRUCT]_[ExecutionCore]
//----------------------------------------------------------------------
// [TAG]_[[HOT_PATH] [DATA_ORIENTED_DESIGN] [CONCURRENCY]]
// [SCHEMA]_[v1]
// [OVERVIEW]_[per-node hot execution state — layout-by-access-pattern (H6)]
// [DIAGRAM]
//   line0: [active:1][active_b:1][pad:6][live_tp:24][live_sl:24][pad:8] = 64B
//   line2: [permission:1][pad:63]   <- false-sharing isolated
//======================================================================
template <unsigned F> struct alignas(64) ExecutionCore { … };
//======================================================================
// [COMMENT]
//——————————————————————————————————————————————————————————
// [[2026-05-11] [v5.11.1.5]]
//----------------------------------------------------------------------
// moved live_tp/live_sl into line 0 so the steady CMOV reads both in one
// cache line — cut a tick from 2 loads to 1. permission sits cross-CPU so
// it gets its own line (false-sharing isolation).
// [SUPPORTING_DOCS]
//   - [DESIGN_SPEC]_[cache-line-discipline]
//   - [INVARIANT]_[H6]
//======================================================================
// [DERIVED]   (tool-refreshed; byte-map verified vs offsetof)
//----------------------------------------------------------------------
// [SIZE]_[192B]
// [ALIGNED_CONSUMERS]_[[ControllerEventLoop] [OrderManager]]
// [THREAD]_[[HOT_WRITER] [SLOW_READER]]
//======================================================================
// [END_STRUCT]_[ExecutionCore]
//======================================================================
```

---

## CI enforcement (extend `check_doc_metadata.py` → also validates code)

1. **Vocab** — every `[CATEGORY]` in the closed set; every `[TAG]`/`[REFERENCE]` value resolves (tag ∈ doc-tag-vocab; `[DECISION]_[D-306]`/`[DESIGN_SPEC]_[x]` EXISTS — `check_capture_audit`-shape → no dangling refs).
2. **Section order** — blocks follow the ladder; out-of-order = fail.
3. **DERIVED vs ground truth** — each `[DERIVED]` line diffed against its generator (`sizeof`/`offsetof`/`gen_code_map`/`calls_graph`/conformance/git); mismatch = build error. **DERIVED facts MUST be REPRODUCIBLE** (deterministic per binary — instruction count / cache spans / offsets / SIMD / branch class, the asm-derived ones pinned by a `[BUILD]` line naming the canonical `build.sh` flags — the count is meaningless without them): a machine-variable metric (measured **ns** — clock/turbo/voltage/core-interrupt dependent) is NEVER a drift-checked comment fact (it would false-RED in CI). **Instruction count (`[SIZE]_[instr]`) is the transferable latency proxy**; the H8 ns budget is a design constraint (`[REFERENCE]_[INVARIANT]_[H8]`); actual ns measurement lives on the separate measurement surfaces (dev-time `fox-bench` fingerprints / the runtime data+monitoring planes), never in this dev-plane comment. **Toolchain split (D-321) — the two fact-families use DIFFERENT compilers:** LAYOUT facts (`[SIZE]_[bytes]` / `[ALIGN]` / `[CACHE_LINES]` / `[STRADDLE]` / offsets) are computed with clang `-Xclang -fdump-record-layouts` (a clang-only flag, but Itanium-ABI-identical to the shipped g++ for these POD / H12 / H14-no-bitfield structs). CODEGEN facts (`[SIZE]_[instr]` / `[BRANCHES]` / `[SIMD]` / spills) MUST use **g++** (the shipped compiler) with the `[BUILD]` flags — clang's instruction selection + branch codegen diverge from g++, so a clang instr-count / branch-class would be WRONG for the binary we actually run. (The clang layout probe uses only the portable flag subset `-I` / `-isystem` / `-D` / `-std` — the g++ `compile_commands.json` carries `-flto` / `-funroll-loops` that clang rejects; reuse `sizeprobe._filter_flags`, don't fork it.)
4. **Closers** — every `[STRUCT]`/`[FUNCTION]`/`[REGISTRY]` has a matching `[END_*]`.
5. **Prose asserts no DERIVABLE fact** — curated `[WHY]`/`[DETAIL]` states the WHY (rationale/intent/history) but NEVER restates a machine-derivable WHAT. Codegen-keywords in prose (branchless / CMOV / no-spill / SIMD / inlined / a size or instr claim) are cross-checked against the corresponding DERIVED tag (`[BRANCHES]`/`[SIMD]`/`[SIZE]`…) — a contradiction FAILS the build. **Rationale (SSoT):** a derivable fact restated in prose is a second, UNCHECKED copy = a drift surface; the fact lives ONCE, in its DERIVED tag, and prose *references* it (`[BRANCHES]_[0]`) rather than *asserting* it ("branchless"). This structurally closes the **prose-lies-about-codegen** class (a stale "CMOV/branchless" comment relocating verbatim as a false claim CI never inspected — RBP-class candidate).

---

## Schema evolution (`[SCHEMA]_[vN]`)

The convention self-versions. When it evolves v1→v2, a migrator greps `[SCHEMA]_[v1]` blocks and upgrades them in place — no big-bang re-convert. A block without `[SCHEMA]` = un-migrated legacy (reported by the metadata audit). This is how the format changes safely over the codebase's life.

---

## Extending the schema (three flavors, each bounded — the SCHEMA never changes)

New things SLOT IN; the parse rule + ladder + vocab are untouched:
- **New CATEGORY** (e.g. an `[OWNER]` axis) → one row in the category set + one line in the CI validator + document its grammar. The parser already handles it (it's just another `[X]`).
- **New TEMPLATE VARIANT** (a new unit type — a lock, a coroutine, a GUI panel) → reuse the ONE anatomy; pick which `[DERIVED]`/`[REFERENCE]` tags it emphasizes. No new parser, no new schema. Built as-encountered during conversion.
- **New DERIVED tag** (e.g. `[BRANCH_MISPREDICT_RISK]`) → add its GENERATOR (the tool that computes it) + its CI check (validate vs ground truth) + the category row. Heaviest (needs tooling), most valuable (auto-maintained).

When the SCHEMA ITSELF must change (v1→v2 — a new ladder slot, a renamed category), `[SCHEMA]_[vN]` + the migrator handle it (§ Schema evolution). Everything else is additive + backward-compatible.

## Tooling — the scaffold generator (the adoption keystone)

The convention adopts at scale ONLY with a **scaffold generator**: an editor command / `make doc-block <unit>` that emits the skeleton block with the **DERIVED tier PRE-FILLED** from the tools (size/deps/consumers/instr-budget/simd). Documenting a unit then = run it, fill only the curated `[WHY]`/`[TAG]`/`[REFERENCE]`, done. Without it, every block is hand-assembled → friction → skipped → the convention rots. With it, friction is near-zero AND the DERIVED tier is correct-by-construction (fits fox-symdeps as an editor command). **This is the single highest-leverage tool to build after the CI validator.**

- **Schema self-test (golden):** a committed fixture of example blocks + their expected parse/validate output → the parser + CI carry a characterization test (golden-master discipline applied to the tooling itself; regen only behind a reviewed `[SCHEMA]` bump).
- **Exemption (deliberate opt-out):** generated / third-party / trivial code that legitimately has no block carries a file-level `// [SCHEMA]_[exempt]_[reason]` → CI skips it (distinct from a *malformed* block, which WARNS). No false-flags on a bare/half-converted file.
- **Backlinks (doc→code):** the tool inverts the `[REFERENCE]` tags → each workspace doc gains a computed "referenced-by these code units" index, completing the bidirectional graph.

## Conversion + Rollout (the deferred codebase pass)

**Sequence (per D-306):** v1.0 spec (this doc) → the DERIVED/CI tooling → **tool-assisted, INCREMENTAL** conversion (pilot a few representative files → validate the format in real use → roll out) → workspace DESIGN_SPECS + tools → *then* resume deferred code (E.1.2 2d+). NOT a monolithic hand-freeze — the tool fills the DERIVED tier + scaffolds the block; humans write only `[WHY]`/`[TAG]`/`[REFERENCE]`.

**Preserve-voice contract (reconciles the codebase's "preserve the user's voice" rule):** conversion RELOCATES existing WHY-prose into the `[WHY]`/`[DIAGRAM]` sections **verbatim in the author's voice** — it does not rewrite it. Tags + the DERIVED tier are ADDED *around* the preserved prose. A conversion that flattens/reworded the author's explanation is a defect, not a conversion.

**Robustness:** an unknown `[CATEGORY]` or malformed bracket → the parser WARNS + skips the line (never crashes); the CI check surfaces it. Graceful degradation so a half-converted codebase still parses.

---

## Cross-references

- Sister: `doc-tag-vocabulary.md` (the SSoT vocab reused by `[TAG]`; extend with `[DIRECTIVE]`/`[REFERENCE]` axes + the UPPER_SNAKE↔lower-hyphen render note)
- Sister: `categorical-tag-applicability-pattern.md` (the code-level tag-applicability analog this realizes)
- Sister: `mechanical-verification-of-derived-code-facts.md` (the DERIVED-tier discipline)
- Sister: `file-size-split-discipline.md` (`[END_*]` jump-nav is what lets files grow past the old caps — consistent with the AI-workflow relaxation)
- Decision: D-306 (`decision-logs/v5.15.5.F.4d.1.E-architecture-v2.md`) — the full design capture + the rollout/defer sequencing
- First `[DIRECTIVE]` canonical: `tools/check_latency_path_conformance.py` `[LAT_EXEMPT]` marker

---

**End of in-code-documentation-schema v1.0 DRAFT.** Formalizes D-306 + the deep_dives sketches. First-canonical full-convention application = the incremental codebase conversion (next session).
