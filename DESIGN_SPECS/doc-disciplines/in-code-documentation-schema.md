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
- **Value lists: inline when short, BLOCK when long.** A short list stays inline: `[CONSUMERS]_[[A] [B]]`. A list that would wrap past ~one line uses the block form — the category alone as a header, values on following indented value-only lines:
  ```
  // [CONSUMERS]
  //   [ControllerEventLoop]
  //   [OrderManager]
  //   [BacktestSharded]
  ```
  **Parse:** a category line WITH value-brackets = inline; a category line with NO values = a block header whose values are the following `//   [X]` lines (until the next `[CATEGORY]` or `====`/`----` bar). Grep finds the header (`[CONSUMERS]`) AND each value (`[OrderManager]`) either way. Use the block form ONLY when it would wrap — zero bloat on short lists.
- **`[WHY]` prose + `[DIAGRAM]` ASCII** are already block-content: they span from their category line to the next `[CATEGORY]` or bar (continuation lines need no prefix). (Worked examples below still show a few combined lines from the pre-refinement draft — swept to one-per-line as the draft matures.)

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
| ~~`[DERIVED]` family~~ (size/deps/consumers/instr-budget/blast-radius) | — | **PLUGIN-owned — live from clangd; NEVER a comment tag** (D-307) | machine-live |
| `[DETAIL]` | `_ rich prose (block)` | judgment (`deep_dives` LR-narrative style; author's voice) | curated |
| `[EDIT]` / `[VERSION]` | `_[[date-or-version]]` + prose below | judgment (`deep_dives` `[EDIT [14-03-26]]` style) | curated |
| `[REFERENCE]` → `[DESIGN_SPEC]` `[MEMORY]` `[DECISION]` `[TECH_DEBT]` `[CLASS]` `[INVARIANT]` `[PLAN]` `[AUDIT]` `[DOC]` | `_[SUBCAT]_[id-or-path]` | workspace artifact id; `[DOC]` = path to a richer external writeup (doc-sync) | curated (pointer must RESOLVE — CI) |
| `[DIRECTIVE]` → `[LAT_EXEMPT]` (+ future `[H12_PAD]`/`[TODO]`) | `_[reason]` on the governed line | machine-read | curated |
| `[SCHEMA]` | `_[vN]` | the convention version | meta |
| `[END_*]` | `_[name]` | close delimiter | structural |

Vocab is **1-line extensible** (per `doc-tag-vocabulary.md`); add tags at real use-sites, don't pre-enumerate. `[LATENCY_CRITICAL]` etc. are synonyms of existing SURFACE tags — fold, don't add.

---

## Two tiers — the human layer (comments) vs the machine layer (the plugin)

**Reframed 2026-07-05 (D-307), after reading `fox-symdeps.nvim`.** The plugin already derives the ENTIRE machine layer LIVE from ground truth (clangd + treesitter + `gen_code_map`): size, alignment, cache-line packing, vector-register fit, per-field layout, upstream `Uses`, role-classified `Consumers`, call directions, hot-path instruction budget, doc-mentions, byte-layout blast-radius. A DERIVED *comment* tier would MIRROR exactly what the plugin already shows = the **Class-18 anti-pattern this whole system exists to kill.** Resolution: **comments never carry derived facts.**

- **CURATED — the comment block** (humans write; the compiler can't know it): `[WHY]`, `[DETAIL]`, `[TAG]`, `[EDIT]`/`[VERSION]`, `[REFERENCE]` (incl. `[DOC]_[path]` sync), `[DIAGRAM]` (the author's mental model). Rationale, history, pointers — none mechanically derivable, so none drifts.
- **DERIVED — the plugin's live overlay** (NOT comments): size/deps/consumers/instr-budget/blast-radius, from clangd. The plugin's HUD **fuses** the two — your curated block PLUS the live facts, side by side. That fusion IS the polished GUI.

**What this buys:** the drift surface DISAPPEARS — nothing tool-generated in comments to go stale → no DERIVED-regenerator, no DERIVED-CI-drift-check. The stale-comment class (TECH_DEBT-226/228) is solved by having **no mirror** — the fact lives once, at ground truth, surfaced live.

### Division of labor (schema ↔ plugin) — the parallel-work contract

The comment block is the **interface** between this schema (the format) and `fox-symdeps` (the consumer). Stable contract = **{closed category vocab · section ladder · one-category-per-line · the `====` bracket structure}**. Hold those stable and the two develop INDEPENDENTLY: changes *within* the contract (richer `[WHY]`, more examples) are free; changes *to* the contract (a new category, a new ladder slot) are the only coordination point — gated by a `[SCHEMA]_[vN]` bump. The plugin parses the block (one-rule grammar → group→tag→value) and overlays the live facts; the schema stays a minimal, co-evolving format. (H22-style clean seam: each side a pure function of the interface.)

**Explicitly NOT done:** (a) mirroring any clangd-derivable fact in a comment (the plugin owns it); (b) commented-out old/new code as diffs (git owns the diff; `[EDIT]` + `[REFERENCE]_[DECISION]` own the what/why).

---

## Templates (copy-paste skeletons)

### Function
```cpp
//======================================================================
// [FUNCTION]_[<Name>]
// [TAG]_[[<SURFACE>] [<CONCERN>]]   [SCHEMA]_[v1]
//======================================================================
// [WHY]_ <one-paragraph rationale; extend-point if any>
//----------------------------------------------------------------------
// [DIAGRAM]_[<kind>]              (optional; data-flow for non-trivial fns)
//   <ASCII>
//----------------------------------------------------------------------
// [DERIVED]   (auto; CI-checked; do NOT hand-edit)
// [DATA_SIZE]_[<n instr>]   [SIMD]_[<none|avx512|…>]   [FLOAT]_[<n · H4-status>]
// [DEP_CHAIN]_in_[[<types>]]  out_[[<types>]]
// [CONSUMERS]_[[<callers>]]   [ITERATIONS]_[auto:git]
//----------------------------------------------------------------------
// [VERSION]_[<id>]_[<semantic what changed>]
// [REFERENCE]_[<SUBCAT>]_[<id>]   [INVARIANT]_[[<H#>]]
//======================================================================
<signature> { <clean body — terse inline comments only> }
//======================================================================
// [END_FUNCTION]_[<Name>]
//======================================================================
```

### Struct (layout-critical)
```cpp
//======================================================================
// [STRUCT]_[<Name>]
// [TAG]_[[<SURFACE>] [DATA_ORIENTED_DESIGN] …]   [SCHEMA]_[v1]
//======================================================================
// [WHY]_ <layout-by-access-pattern rationale>
//----------------------------------------------------------------------
// [DIAGRAM]_[<layout>]
//   line0: [<field:bytes>]…= 64B   line1: …   (byte-map)
//----------------------------------------------------------------------
// [DERIVED]   (auto; CI-checked)
// [DATA_SIZE]_[<N>B]   [ALIGNED_CONSUMERS]_[[<types needing this layout>]]
// [THREAD]_[[<HOT_WRITER> <SLOW_READER> …>]]
//----------------------------------------------------------------------
// [VERSION]_[<id>]_[<what>]
// [REFERENCE]_[DESIGN_SPEC]_[<spec>]   [INVARIANT]_[[<H#>]]
//======================================================================
<struct> { … };
//======================================================================
// [END_STRUCT]_[<Name>]
//======================================================================
```

### Registry (`FOREACH_*` X-macro) — the "registry map"
```cpp
//======================================================================
// [REGISTRY]_[FOREACH_REGIME_PERSIST_FIELD]
// [TAG]_[[SLOW_PATH] [PERSISTENCE] [FRAMEWORK_DISCIPLINE]]   [SCHEMA]_[v1]
//======================================================================
// [WHY]_ single-source the RegimeState snapshot wire order; one row = one
//        persisted field; add/drop = 1 row + a SHARDED version bump (H21).
//----------------------------------------------------------------------
// [DIAGRAM]_[row-shape]   X(field, type, count) x7 -> FieldwiseWrite/Read/Commit
//----------------------------------------------------------------------
// [DERIVED]   (auto; CI-checked)
// [ROW_COUNT]_[7]   [ENROLLED]_[MetaRegistry.hpp]
// [CONSUMERS]_[[RegimeState_FieldwiseWrite] [_FieldwiseRead] [_CommitPersistedFields]]
//----------------------------------------------------------------------
// [VERSION]_[v5.15.5...E.1.2]_[created — registry-ize regime persist (D-305)]
// [REFERENCE]_[DESIGN_SPEC]_[registry-tuple-as-single-source-of-truth]  [INVARIANT]_[[H15] [H21]]
//======================================================================
#define FOREACH_REGIME_PERSIST_FIELD(X)  X(current_regime, int, 1)  …
//======================================================================
// [END_REGISTRY]_[FOREACH_REGIME_PERSIST_FIELD]
//======================================================================
```
The registry-specific DERIVED — `[ROW_COUNT]`, `[ENROLLED]` (its MetaRegistry row, H15), `[CONSUMERS]` (the walkers that expand it, grep-derived) — IS the "registry map": what it defines, who uses it, what it's for. Registries are the codebase's load-bearing pattern, so this is a first-class block (not a variant).

### File — `[FILE]_[<path>]` on the identity line + a role `[WHY]` + a data-flow `[DIAGRAM]` + it serves as the sub-file TOC anchor for the whole file.

### Variants for other unit types (anatomy-REUSE — tweak the `[DERIVED]`/`[REFERENCE]` set, NOT a new system; build each the first time a real unit needs it during conversion, do NOT pre-enumerate)
- **Enum (persisted / wire CODES)** — `[ENUM]_[<name>]`; add `[REFERENCE]_[INVARIANT]_[H21]` + a tombstone note (Knight-Capital: append-only, never renumber/reuse a slot). The SHALT / halt-reason / regime / snapshot-version code enums live here.
- **Foundational typedef** (`Money`, `FPN_Binary<F>`, `EngineMoneyT`) — `[TYPE]_[<name>]`; `[DATA_SIZE]_[<sizeof>]` + `[REFERENCE]` to the encoding epoch / H4. The money-type SSoT warrants a block; a throwaway alias does not.
- **Macro** (`BITMAP_*` / `MBS_*` accessors) — LIGHT `[MACRO]_[<name>]` (no `[END]`; `[DERIVED]` = branchless?/expansion); most accessor macros stay terse-inline.
- **Test group** (`controller_test` Phase blocks) — `[TEST]_[<name>]`; `[REFERENCE]` to the invariant/decision each verifies → navigation across the 3697-test suite.

**Boundary (same as the tag rule):** the 4 first-class blocks (function / struct / registry / file) cover ~90%; the variants fill in organically. Build a variant when a real unit needs it — pre-designing all of them is *template* sprawl, the very thing this kills at the comment level.

---

## Worked examples

### Function — `Regime_Classify` (Strategies/RegimeDetector.hpp)
```cpp
//======================================================================
// [FUNCTION]_[Regime_Classify]
// [TAG]_[[SLOW_PATH] [ML_INFERENCE]]   [SCHEMA]_[v1]
//======================================================================
// [WHY]_ each signal +1 to a trending/volatile score, highest wins;
//        hysteresis (hold N cycles) prevents flapping; RANGING default.
//        Extend = +1 RegimeSignals field & +1 compare here.
//----------------------------------------------------------------------
// [DIAGRAM]_[signal-flow]
//   RegimeSignals{slope x2, R2, ROR, vol, var-ratio} ─┐
//   ControllerConfig{thresholds} ────────────────────┼─► trending_score
//                                                     └─► volatile_score
//                             highest ─► hysteresis ─► return regime
//----------------------------------------------------------------------
// [DERIVED]   (auto; CI-checked; do NOT hand-edit)
// [DATA_SIZE]_[~480 instr]   [SIMD]_[none]   [FLOAT]_[18 · H4-exempt]
// [DEP_CHAIN]_in_[[RegimeSignals] [ControllerConfig]]  out_[[RegimeState]]
// [CONSUMERS]_[[EventLoop_RebuildOneCore] [StrategyParameters_Dispatch]]  [ITERATIONS]_[auto:git]
//----------------------------------------------------------------------
// [VERSION]_[v5.7.1]_[expose last_trending/volatile_score for entry-quality log]
// [REFERENCE]_[AUDIT]_[latency-conformance-kernel]   [INVARIANT]_[[H4] [H8]]
//   body: 1x [LAT_EXEMPT] env-gated cold-debug fprintf
//======================================================================
template <unsigned F>
inline int Regime_Classify(RegimeState<F>* state, const RegimeSignals<F>* sig,
                           const ControllerConfig<F>* cfg) {
    if (sig->short_count < 64) return state->current_regime;   // cold start
    // signal scoring -> hysteresis -> regime   (terse inline comments only)
}
//======================================================================
// [END_FUNCTION]_[Regime_Classify]
//======================================================================
```

### Struct — `ExecutionCore` (the sprawl exhibit: ~100 comment lines → this)
```cpp
//======================================================================
// [STRUCT]_[ExecutionCore]
// [TAG]_[[HOT_PATH] [DATA_ORIENTED_DESIGN] [CONCURRENCY]]   [SCHEMA]_[v1]
//======================================================================
// [WHY]_ layout by access pattern (H6): steady CMOV reads live_tp+live_sl
//        each tick -> both fit line 0; permission cross-CPU -> own line.
//----------------------------------------------------------------------
// [DIAGRAM]_[cache-layout]
//   line0: [active:1][active_b:1][pad:6][live_tp:24][live_sl:24][pad:8]=64B
//   line2: [permission:1][pad:63]   <- false-sharing isolated
//----------------------------------------------------------------------
// [DERIVED]   (auto; CI-checked)
// [DATA_SIZE]_[192B]   [ALIGNED_CONSUMERS]_[[ControllerEventLoop] [OrderManager]]
// [THREAD]_[[HOT_WRITER] [SLOW_READER]]
//----------------------------------------------------------------------
// [VERSION]_[v5.11.1.5]_[live_tp/live_sl -> line 0 (Money 24B fit)]
// [REFERENCE]_[DESIGN_SPEC]_[cache-line-discipline]   [INVARIANT]_[[H6]]
//======================================================================
template <unsigned F> struct alignas(64) ExecutionCore { … };
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
