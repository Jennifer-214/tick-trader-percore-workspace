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

---

## Category set (closed vocabulary)

| Category | Grammar | Value source | Tier |
|---|---|---|---|
| `[FILE]`/`[STRUCT]`/`[FUNCTION]`/`[REGISTRY]` | `_[name]` | the identifier | curated |
| `[TAG]` | `_[[a] [b] …]` | doc-tag-vocab SURFACE + CONCERN axes (UPPER_SNAKE render) | curated |
| `[WHY]` | `_ prose` | judgment | curated |
| `[DIAGRAM]` | `_[kind]` + ASCII body | judgment (ASCII byte/data-flow map) | curated intent / DERIVED-checkable |
| `[DERIVED]` family (size/deps/consumers/instr-budget/blast-radius) | `_[SUBCAT]_[val]` | **tool-refreshed in-comment** — generated from clangd / `gen_code_map`, CI-checked vs ground truth, NEVER hand-edited (D-307 fork b) | machine-derived |
| `[ITERATIONS]` | `_[n]` | **DERIVED** — git-churn count (commits touching the unit) → hot-spot detector; tool-refreshed + CI-checked (D-306) | machine-derived |
| `[DETAIL]` | `_ rich prose (block)` | judgment (`deep_dives` LR-narrative style; author's voice) | curated |
| `[EDIT]` / `[VERSION]` | `_[[date-or-version]]` + prose below | judgment (`deep_dives` `[EDIT [14-03-26]]` style) | curated |
| `[REFERENCE]` → `[DESIGN_SPEC]` `[MEMORY]` `[DECISION]` `[TECH_DEBT]` `[CLASS]` `[INVARIANT]` `[PLAN]` `[AUDIT]` | `_[SUBCAT]_[id-or-path]` | workspace artifact id (pointer must RESOLVE — CI). `[DOC]`-sync DROPPED (D-307): rich prose lives in-comment as `[DETAIL]`, not a drift-prone external pointer | curated |
| `[DIRECTIVE]` → `[LAT_EXEMPT]` (+ future `[H12_PAD]`/`[TODO]`) | `_[reason]` on the governed line | machine-read | curated |
| `[FUTURE_WORK]` → `[TECH_DEBT]` `[PLAN]` | `_[SUBCAT]_[id]` | a tracked FORWARD pointer (code twin of a doc's future-expansion; must RESOLVE — CI) — distinct from `[REFERENCE]` which governs/explains (D-306) | curated |
| `[SCHEMA]` | `_[vN]` | the convention version | meta |
| `[END_*]` | `_[name]` | close delimiter | structural |

Vocab is **1-line extensible** (per `doc-tag-vocabulary.md`); add tags at real use-sites, don't pre-enumerate. `[LATENCY_CRITICAL]` etc. are synonyms of existing SURFACE tags — fold, don't add.

---

## Two tiers — the CURATED layer (human-written) vs the DERIVED layer (tool-written, CI-checked)

**Reframed 2026-07-05 (D-307), after reading `fox-symdeps.nvim`.** The plugin already derives the ENTIRE machine layer LIVE from ground truth (clangd + treesitter + `gen_code_map`): size, alignment, cache-line packing, vector-register fit, per-field layout, upstream `Uses`, role-classified `Consumers`, call directions, hot-path instruction budget, doc-mentions, byte-layout blast-radius. The open question was whether to ALSO materialize those facts in-comment or leave them plugin-live-only — a *hand-written* DERIVED tier would MIRROR what the plugin shows = the **Class-18 anti-pattern this whole system exists to kill.** **Resolution (D-307, forks-resolved): DERIVED lives in-comment, but TOOL-REFRESHED** — generator-written from ground truth, CI-checked, never hand-edited. Class-18 only bites *hand* mirrors; a generated + build-gated snapshot cannot silently drift (the moment it does, CI goes red). So the fact is materialized where grep / GitHub / any editor sees it **without** the plugin, and the plugin fuses its live overlay on top.

- **CURATED — the human layer** (humans write; the compiler can't know it): `[WHY]`, `[DETAIL]`, `[TAG]`, `[EDIT]`/`[VERSION]`, `[REFERENCE]`, `[DIAGRAM]` (the author's mental model). Rationale, history, pointers — none mechanically derivable, so none drifts.
- **DERIVED — the tool layer** (the generator writes; CI verifies; NEVER hand-edited): size/deps/consumers/instr-budget/blast-radius, from clangd / `gen_code_map`, materialized in the block so it reads *without* the plugin. The plugin's HUD **fuses** its live overlay on top — your curated block PLUS the derived facts, always current. That fusion IS the polished GUI.

**What this buys:** the drift surface is **contained**, not wished away — the mirror exists, but it is tool-owned + build-gated, so it cannot silently rot: a `[DERIVED]` line that diverges from ground truth is a red build, not a lie. The stale-comment class (TECH_DEBT-226/228) is solved not by *removing* the fact from the comment but by making it **generator-written + CI-verified** — `mechanical-verification-of-derived-code-facts` applied to comments. (Reversible per D-307: if the plugin's live overlay ever makes the in-comment copy redundant, drop back to plugin-live-only — the grammar is unchanged either way.)

### Division of labor (schema ↔ plugin) — the parallel-work contract

The comment block is the **interface** between this schema (the format) and `fox-symdeps` (the consumer). Stable contract = **{closed category vocab · section ladder · one-category-per-line · the `====` bracket structure}**. Hold those stable and the two develop INDEPENDENTLY: changes *within* the contract (richer `[WHY]`, more examples) are free; changes *to* the contract (a new category, a new ladder slot) are the only coordination point — gated by a `[SCHEMA]_[vN]` bump. The plugin parses the block (one-rule grammar → group→tag→value) and overlays the live facts; the schema stays a minimal, co-evolving format. (H22-style clean seam: each side a pure function of the interface.)

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
//   <hand-ASCII data-flow — -> <- | _ ^ v>
//======================================================================
<signature> { <clean body — comments moved OUT> }
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
// [SIZE]_[<n instr>]
// [SIMD]_[<none|avx512>]
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
// [SCHEMA]_[v1]
// [OVERVIEW]_[<layout-by-access-pattern gist>]
// [DIAGRAM]
//   line0: [<field:bytes>] .. = 64B    (byte-map; tool-verified vs offsetof)
//======================================================================
<struct> { … };
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
// [ALIGNED_CONSUMERS]_[[<types>]]
// [THREAD]_[[<HOT_WRITER> <SLOW_READER>]]
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
#define FOREACH_<NAME>(X)  X(...)  …
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

### File — `[FILE]_[<path>]` identity + an `[OVERVIEW]` role + a data-flow `[DIAGRAM]`; serves as the file's TOC anchor. (Orient-block only — no code body.)

### Variants for other unit types (anatomy-REUSE — tweak the `[DERIVED]`/`[REFERENCE]` set, NOT a new system; build each the first time a real unit needs it during conversion, do NOT pre-enumerate)
- **Strategy** — `[STRATEGY]_[<name>]`; `[TAG]` its regime-fit + op-mode, `[REFERENCE]` its params/spec. A strategy is just another tagged unit (fits the hybrid block exactly); a strategy-dev plugin lens renders a strategy-shaped view of the same facts (operator's domain).
- **Enum (persisted / wire CODES)** — `[ENUM]_[<name>]`; add `[REFERENCE]_[INVARIANT]_[H21]` + a tombstone note (Knight-Capital: append-only, never renumber/reuse a slot). The SHALT / halt-reason / regime / snapshot-version code enums live here.
- **Foundational typedef** (`Money`, `FPN_Binary<F>`, `EngineMoneyT`) — `[TYPE]_[<name>]`; `[SIZE]_[<sizeof>]` + `[REFERENCE]` to the encoding epoch / H4. The money-type SSoT warrants a block; a throwaway alias does not.
- **Macro** (`BITMAP_*` / `MBS_*` accessors) — LIGHT `[MACRO]_[<name>]` (no `[END]`; `[DERIVED]` = branchless?/expansion); most accessor macros stay terse-inline.
- **Test group** (`controller_test` Phase blocks) — `[TEST]_[<name>]`; `[REFERENCE]` to the invariant/decision each verifies → navigation across the 3697-test suite.

**Boundary (same as the tag rule):** the 4 first-class blocks (function / struct / registry / file) cover ~90%; the variants fill in organically. Build a variant when a real unit needs it — pre-designing all of them is *template* sprawl, the very thing this kills at the comment level.

---

## Worked examples

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
3. **DERIVED vs ground truth** — each `[DERIVED]` line diffed against its generator (`sizeof`/`offsetof`/`gen_code_map`/`calls_graph`/conformance/git); mismatch = build error.
4. **Closers** — every `[STRUCT]`/`[FUNCTION]`/`[REGISTRY]` has a matching `[END_*]`.

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
