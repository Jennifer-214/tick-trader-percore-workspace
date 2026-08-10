---
type: doc-discipline
stage: 3-first-canonical
version: 1.0
locked: 2026-07-14
established: 2026-07-05
tags: [doc-discipline, meta-discipline, ssot, structural-fix]
surface: [ci-tooling, doc-pipeline, test-infrastructure]
sister_specs: [in-code-doc-system-north-star.md, format-input-space-taxonomy.md, doc-tag-vocabulary.md, categorical-tag-applicability-pattern.md, mechanical-verification-of-derived-code-facts.md, doc-intelligence-toolchain-architecture.md, file-size-split-discipline.md]
applies_at_skills: []
---

# In-code documentation schema (the tag-block convention — SSoT)

**Established:** 2026-07-05 (design captured in decision-log D-306; formalizes the `====`-block sketches Caramel began in the `deep_dives` folder). **Origin:** a one-line latency-tool `[LAT_EXEMPT]` marker generalized into a full navigable in-code documentation system for the in-house fox-symdeps dev environment.

**Status: LOCKED — `[SCHEMA]_[v1.0]`** (2026-07-14, D-346) — the first COMPLETE, rollout-ready release of the format. Frozen contract = the one parse rule + the ladder + the node model (D-339) + the member model (D-340) + the closed 76-token category set + the `[REFERENCE]`/`[ASSERT]`/`[DERIVED]` families. Verified before lock: all 14 taxonomy shapes covered (D-345) + every plugin target fed (D-344). *There was never a "v1 in the wild" — nothing was converted; the internal "v1 draft → v2 additions" iteration collapsed into this first release, so it's `v1.0`, not `v2`.* Codebase conversion = the deferred rollout (§ Conversion + Rollout; phases 2–6). **Reversible** via a `[SCHEMA]` version bump (nothing converted yet).

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

## One skeleton — every unit type is the same block (the anti-adapter invariant · D-339)

A COROLLARY of the three invariants, made explicit: there is exactly ONE unit skeleton, and **every** `[TYPE]` fills the same slots in the same ladder order. A registry is not a special case with its own parser — it is this skeleton with `[TYPE]=REGISTRY`.

```
[<TYPE>]_[name]            TYPE ∈ {FILE STRUCT FUNCTION REGISTRY ENUM TYPE MACRO TEST STRATEGY ASSERT}
[TAG] · [SCOPE]            classify
[OVERVIEW] · [DIAGRAM]     understand
[COLUMN]…                  member-STRUCTURE legend, orient-region (registry tuple; optional)
[CODE]                     the source, VERBATIM (D-326 code-local comments stay in place)
   [SECTION]_[label]         universal IN-BODY grouping — the SAME tag for a struct field-band,
                             a function phase, an enum tier, a registry row-group
[END_CODE]
[ROW]… / [FIELD]…          SPARSE member rationale, `[KIND]_[id]_[why]` — adjacent to the body,
                           kept OUT of any `\`-continued macro (so the continuation is a non-issue)
[COMMENT]                  curated unit-WHY
[DERIVED]                  tool-written facts — the ONE slot that varies by type ↓
[REFERENCE] · [END_<TYPE>]_[name]
```

**The only thing that varies by `[TYPE]` is the `[DERIVED]` axis-set — and that variance is a DECLARATIVE TABLE, never a parser branch.** The parser is type-agnostic (`check_code_tag_blocks.py` has zero `if TYPE ==` special-casing — its rule is *"exactly as the plugin's tagadapter"*); it runs the one innermost-bracket rule over the one skeleton. So there are **no per-type adapters between struct / function / registry**: CI, the plugin, and the CLI parse identically, and a fact-producer emits a type's facts by looking `[TYPE]` up here:

| `[TYPE]` | `[DERIVED]` axis-set (what the fact-producer emits) | members addressed as |
|---|---|---|
| `[STRUCT]` | `SIZE` · `ALIGN` · `CACHE_LINES` · `STRADDLE` · `ALIGNED_CONSUMERS` · `THREAD` | `[FIELD]` inline (D-326); field-bands via `[SECTION]` |
| `[FUNCTION]` | `SIZE`(instr) · `SIMD` · `FLOAT` · `BRANCHES` · `UPSTREAM` · `CONSUMERS` (pinned by `[BUILD]`) | phases via `[SECTION]` |
| `[REGISTRY]` | `ROW_COUNT` · `ENROLLED` · `CONSUMERS` | `[ROW]` · `[COLUMN]`; row-groups via `[SECTION]` |
| `[FILE]` | `CONTAINS`/`TOC` · `INCLUDES`/`UPSTREAM` · `INCLUDED_BY`/`CONSUMERS` · `BLAST_RADIUS` · `BINARIES` | child units via `[CONTAINS]` |
| variants (`ENUM`/`TYPE`/`MACRO`/`TEST`/`STRATEGY`) | REUSE the anatomy; pick the subset when a real unit needs it (§ Variants) — never pre-enumerated | — |

That table is the whole per-type surface. Adding a unit type = one row here (which facts to emit), never a new parser or adapter — the anti-Class-18 discipline (D-331 "one producer, N consumers"; D-337 "one core") realized at the grammar level: **one skeleton, one parser, N renderers.**

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
| **Function-LOCAL struct** (declared inside a function's body braces) | **NO** — EXEMPT (D-364) | a stack impl-detail, NOT a navigable unit — the tag-browser lists real structures + cursor-track resolves to the enclosing fn. DISTINCT from a namespace-scope struct merely SITED under a mega `[FUNCTION]` block (`RegressionFeederX`, the GCN structs — brace-depth 0), which DOES get a block. `check_conversion_completeness.py` enforces (brace-depth test). |

**Granularity:** one block per unit (struct / function / registry / file). Individual struct fields get OPTIONAL terse inline tags (`// hot read`, `// [H12_PAD]`), never prose. Nested types get their own block if non-trivial.

**Code-local comments STAY in `[CODE]` — verbatim (D-326; generalized to function bodies 2026-07-06).** Converting a unit relocates ONLY the *unit-level* WHY prose (what the whole unit is + why) to `[COMMENT]`. Three kinds of comment are **code-LOCAL** and stay inside `[CODE]`, unchanged: (a) per-field inline comments (`FPN_Binary<F> short_slope; // relative price slope`); (b) **function-body step-comments** that explain the line they sit on (`// relative slope: normalize by price`, `// variance ratio…` throughout `Regime_ComputeSignals`); (c) sub-group section headers that organize the body (`// short window (128-tick)`, `// derived signals`). They are read *at the line*, where the reader needs them; stripping them into `[COMMENT]` would destroy the comment↔code locality that makes a densely-annotated unit — a 40-field struct (`RegimeSignals`) OR a step-commented function (`Regime_ComputeSignals`) — readable at all. **Rule of thumb: does the comment explain the WHOLE unit (→ `[COMMENT]`) or a single line / field / sub-group (→ stays inline in `[CODE]`)?** Preserve-voice applies to both — verbatim on relocation, verbatim in place. (The `[CODE]` body is only ever *wrapped*, never rewritten: nothing but the top-of-unit WHY moves.)

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
| `[ORIGIN]` / `[UPDATED]` | `[ORIGIN]_[AUTO\|MANUAL]` · `[UPDATED]_[YYYY-MM-DD]` | **provenance + freshness** (D-369) — a fact-producer stamps `[ORIGIN]_[AUTO]` (owned/regenerable) + `[UPDATED]`-on-value-change; `[MANUAL]` = curated, a writer must NEVER clobber. Structured replacement for the ad-hoc "(tool-refreshed…)" prose. ISO-8601 date; stamp-on-change preserves writer idempotency (Class-56) | machine-derived |
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
# v2 GROWTH (2026-07-06, the D-fmt slate): + registry ROW/COLUMN sub-units · ASSERT unit variant ·
# OUTDATED_INFO · REGION (cross-fn/beyond-function grouping) · SWAR (bit-pack sub-tag) · EXCLUDED (wire
# field-absent) · SEAM (train↔serve) · the numeric-domain row. [FORMULA] is a [DIAGRAM] KIND, not a token[0].
FILE STRUCT FUNCTION REGISTRY STRATEGY ENUM TYPE MACRO TEST ASSERT
TAG SCOPE SCHEMA OVERVIEW WHY DETAIL DIAGRAM COMMENT SUPPORTING_DOCS EDIT VERSION REFERENCE DIRECTIVE FUTURE_WORK OUTDATED_INFO CODE SECTION REGION
DERIVED SIZE SIMD FLOAT BRANCHES BUILD INSTANTIATION ALIGN CACHE_LINES STRADDLE STRADDLE_EXEMPT UPSTREAM CONSUMERS ROW_COUNT ENROLLED ALIGNED_CONSUMERS ITERATIONS BLAST_RADIUS
# PROVENANCE + FRESHNESS (D-369): who auto-wrote a fact + when. Cross-cuts DERIVED + the auto NON-DERIVED
# fields (CONSUMERS/UPSTREAM/CONTAINS/TOC). ORIGIN_[AUTO|MANUAL]; UPDATED_[ISO-date], stamped on value-change.
ORIGIN UPDATED
ROW COLUMN VALUE WIRE_FIELD PARENT CHILDREN SIDECARS OVERRIDES
CONTAINS TOC INCLUDES INCLUDED_BY BINARIES
THREAD SYNC BIT_PACKED SWAR PADDING WIRE_FORMAT PERSISTED EXCLUDED SEAM LAT_EXEMPT
OVERFLOW ROUNDING DOMAIN PRECISION
COMPLEXITY APPLY_AFTER MUTATES WIRE_VERSION
```
**Disposition categories NOT YET in the fence above** — `SPILLS` `FAULT_SIGNAL` `GATED_BY` … (the D-fmt-slate categories + `COMPLEXITY`/`APPLY_AFTER`/`MUTATES`/`WIRE_VERSION` are now **FOLDED** above — the last four at D-342, 2026-07-14). The rest stay PROPOSED for variant surfaces; **the validator throws `UNKNOWN category` until folded** — fold each WHEN its variant is first piloted.

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
PARITY         DOCS/PARITY_ISSUES.md ("id: PARITY-<n>")                         PARITY-<n>            (D-345 widened-[REFERENCE])
SOURCE         EXISTENCE-UNCHECKED — external repo / venue docs / `.py:line`    free                  advisory (like AUDIT); provenance to a source-authority
URL            EXISTENCE-UNCHECKED — external http(s) link                      free                  advisory; not resolved
```

### Structural + concurrency annotations (register the vocab; apply as-encountered)

Design classifications a tool can't infer — the author declares them. Register the known set so it's consistent + not forgotten (`doc-tag-vocabulary` is 1-line extensible); APPLY each at its first real unit during conversion, never pre-stamp. The byte/bit **breakdown** is the `[DIAGRAM]`'s job (byte-map + bit-map), NOT a per-field tag explosion.

- **Packing (layout)** — `[BIT_PACKED]` (H14: manual `MASK_`/`SHIFT_`/`BITMAP_`/`MBS_` over `uint{8..64}_t`, never C++ bitfields) → the `[DIAGRAM]` carries the **bit-map** (what each bit / bit-group encodes). `[PADDING]` (H12 byte-equivalence).
- **Cross-thread mechanism** — a curated `[SYNC]` line (mirrors `[THREAD]`): `[SYNC]_[SEQ_LOCK]` (slow→hot config cache) · `[SYNC]_[SPSC]` (producer→consumer ring) · `[SYNC]_[ATOMIC]` (cross-core flag/counter) · `[SYNC]_[LOCK_FREE]`.
- **Wire / persistence** — `[TAG]` concern-values `[WIRE_FORMAT]` (H9 HMAC body) · `[PERSISTED]` (snapshot-serialized).
- **Within-function sections** — `[SECTION]_[<label>]` (CURATED · code-local · OPTIONAL; D-329): marks a logical section inside a big multi-part function's `[CODE]` body, **bar-wrapped** (`----` above + below, indented to the code — lighter than the `====` unit bars → clear hierarchy: `====` = unit boundary, `----` = section boundary):
  ```cpp
      //------------------------------------------------------------
      // [SECTION]_[short window signals]
      //------------------------------------------------------------
      <phase body — its step-comments stay inline (D-326)>
  ```
  It **stays in `[CODE]`** (it demarcates the code, not unit-WHY) and *replaces the plain prose section-comment* with the same text made machine-navigable (label = the value; spaces OK). **The bars are load-bearing, not decoration:** the plugin reads them to detect where each section BEGINS + ENDS (the next `[SECTION]` bar implicitly ends the previous), driving a within-function TOC / jump-list — the machine-readable form of the "demarcation points" idea. Use when a function has ≥3 distinct computational phases (e.g. `Regime_ComputeSignals` — short/long window · variance · ROR · flow · wave-1/2); a small single-purpose fn needs none. A one-line computation keeps its plain inline comment — `[SECTION]` is for the multi-line *groupings*.

A new sync primitive / packing scheme adds ONE vocab line at the first struct that needs it — the conversion surfaces it, so a forgotten annotation self-corrects (never a silent gap).

---

## The member model — three tiers (the D-339 sibling)

D-339 gave the per-type NODE model (one skeleton + the `[DERIVED]`-axes table). This is its companion — the per-type MEMBER model: how a unit's internal parts bind, reconciled from D-309's `[REGION]` + D-339's `[ROW]`/`[COLUMN]` + D-340's nested units into ONE cross-type scheme (D-340).

Individual fields / statements stay INLINE in `[CODE]` verbatim (D-326). Above that, a *structured* part sits at one of **three tiers** — the same three for every `[TYPE]`; only the tier-2 vocab differs (exactly like the `[DERIVED]`-axes table):

| Tier | What it is | Tag(s) | Per-`[TYPE]` vocab |
|---|---|---|---|
| **1 · grouping** | a TOC divider; organizes, carries NO own facts | `[SECTION]` | fn phases · struct field-bands · registry row-groups · enum tiers |
| **2 · fact-scoping member** | a sub-part that scopes its OWN facts | `[REGION]` · `[ROW]`+`[COLUMN]` · `[VALUE]` · `[WIRE_FIELD]` | struct → `[REGION]_[name]_[byte-range]` (+ bit-slot form) scoping own `[THREAD]`/`[SYNC]`/`[RESIDENCY]`/`[BIT_OCCUPANCY]` (D-309 #1) · registry → `[ROW]`+`[COLUMN]` (D-339) · enum → `[VALUE]` (SPARSE, like `[ROW]`; carries the wire-CODE per H21 — D-341) · wire-parser → `[WIRE_FIELD]_[<key>]_[<meaning>]` (JSON key-map / FIX tag / CSV column; `[EXCLUDED]` for documented-absent fields; D-345) |
| **3 · nested sub-unit** | a rich nested type promoted to its OWN full block | via `[CONTAINS]` | nested `[ENUM]`/`[STRUCT]` (D-340) |

**Promotion between tiers = the § Coverage proportionality bar** — trivial → stays inline · mid → tier 2 · rich → its own block (tier 3). The *same* member-grammar runs at every tier — `[KIND]_[id]_[why]`, sparse, id-addressed (the one D-339 innermost-bracket parse rule) — so there are **no per-type member adapters**, exactly as D-339 promised for nodes.

**Each tier IS a plugin render** (why the model is shaped this way): tier 1 → the within-unit TOC / jump-list · tier-2 `[REGION]` → the byte-map regions overlay (`regions[]` in `facts.lua`, D-309) · `[ROW]`/`[COLUMN]` → the registry-tree / row-browser · tier 3 → cursor-track the innermost-enclosing unit. The three tiers are the render hierarchy the plugin walks — so the format and the plugin are one design, not two.

---

## v2 grammar additions (the D-fmt slate — 2026-07-06; parse rule + ladder UNCHANGED, all additive)

The 8 locked format decisions + the 3-survey taxonomy grow v1→v2. The fence above carries the new categories; these define their grammar. Detailed templates land as the surfaces are grown (see `format-input-space-taxonomy.md` for the exemplar each answers).

- **SUB-TAGS (D-fmt-5) — a tag may carry a refining child:** `[PARENT]_[CHILD]` (`[BIT_PACKED]_[SWAR]` — manual `BITMAP_*`/`MBS_*` packing IS SIMD-within-a-register; auto-detected from the idiom). Parse unchanged (innermost-bracket, token[0]=parent). Generalizes to any category; `[SWAR]` is the first canonical.
- **`[OUTDATED_INFO]` (D-fmt-6) — the stale-comment tombstone:** wraps a block whose content no longer reflects the code → CI **FLAGS** it → a **human deletes** it (NEVER auto — a mis-mark must not silently drop a load-bearing comment on a capital codebase). Sister to `[FUTURE_WORK]` (intentional scaffold kept) + the P4 rot-check gate.
- **`[EDIT]`/`[VERSION]` grammar (D-fmt-1 + D-338) — parseable + sortable:** `[EDIT]_[<version>]_[<descriptor>]`, `<version>` following a canonical sortable grammar so the plugin DERIVES the version-timeline (no hand-tagging). Version-tags stay code-local. ⚠ **H21:** existing identifiers are historical/immutable — the grammar applies GOING FORWARD; history preserved, never renamed. A bare dev/ship "Phase H" is a VERSION identifier (this grammar), NOT a `[SECTION]`. Exact grammar = OPEN sub-decision.
- **`[SECTION]` — tier-1 grouping (§ member model; D-fmt-4 + survey):** a TOC divider carrying NO own facts — demarcate within a STRUCT (field-bands), ENUM (tiers), REGISTRY (row-groups), FUNCTION (phases), or FILE scope (between units); ONE sub-level of nesting (`[SECTION]` ⊃ `[SECTION]`); absorbs the real bar styles (`===` / unbarred ALL-CAPS runs → canonical bars). A cross-file "Phase" is a `[SECTION]_[Phase N]` **label** (grep for all sites); **`[REFERENCE]_[PHASE]` DROPPED** — the dep tools own the code-cascade (CODE_MAP/DAG/dep-trace, surfaced in the plugin per D-334).
- **`[REGION]` — tier-2 fact-scoping sub-unit (§ member model; D-309 #1, RECONCILED at D-340 — was under-framed here as a bare `[SECTION]` grouping):** the level between a block and an inline field-tag — `[REGION]_[<name>]_[<byte-range>]` (+ a per-bit-slot form) scoping its OWN `[THREAD]`/`[SYNC]`/`[RESIDENCY]`/`[BIT_OCCUPANCY]`. UNLIKE `[SECTION]` (which only groups), a `[REGION]` BINDS per-range facts that otherwise collapse to lossy scalars or un-greppable `[DIAGRAM]` prose (ExecutionCore's 10 regions over 0..68352; Order's packed bit-slots). Plugin: a region-grouping overlay on the byte-map (`regions[]` in `facts.lua`).
- **`[ROW]`/`[COLUMN]` registry sub-schema (survey gap #1, the biggest) — GRAMMAR LANDED (D-339):** a `[REGISTRY]` documents its tuple + rows in the ORIENT region, so the `[CODE]` macro body stays byte-verbatim (D-326) and the `\`-continuation is a **non-issue** — nothing new is injected between the backslash-continued `X(...)` rows:
  - **`[COLUMN]_[<name>]_[<meaning>]`** — one line per tuple column, in **tuple order** (listing order = the ordinal; position IS meaning in a positional macro, so no explicit numbering — same as how a struct lists its fields). An enumerated column appends its token/bit-set (`[COLUMN]_[meta]_[CfgFieldDescriptor OR-flags]_[[IS_BOOT_ONLY] [WARN_ON_CLAMP] …]`). The validator asserts `COLUMN-count == tuple-arity` → a dropped or added arg reds the build.
  - **`[ROW]_[<id>]_[<why>]`** — SPARSE; only a row whose rationale exceeds its own payload gets one, addressed by the row's identity column (the `name` arg for a cfg field). `[ROW]_[TOMBSTONE]_[<retired-id>]` records a retired slot (H21 — append-only, never reused).
  - **Group dividers = the universal `[SECTION]`** (NOT a registry-special tag): a band of rows is `[SECTION]_[<label>]`, the same tag a struct field-band or a function phase uses. The in-macro `/* === Group (n) === */` dividers stay VERBATIM in `[CODE]`; the plugin DERIVES the row-group TOC from them — no mirrored `[SECTION]` list (anti-Class-18).
  - `ROW_COUNT` stays a `[DERIVED]` (tool-counted) fact; `[ROW]`/`[COLUMN]` are the CURATED legend + rationale over it. Worked example: § Worked examples → `FOREACH_GLOBAL_CFG_FIELD`.
- **Nested units — a container's block may hold child blocks (D-340; dogfood-grounded on `CfgFieldDescriptor`):** a `[STRUCT]`/`[FILE]` whose body physically contains a non-trivial `[ENUM]`/`[STRUCT]` gets that child its OWN block, sited at the child's real location inside the parent's `[CODE]` (the parser is stack-based — `[END_TYPE]_[name]` matches by name, so nesting parses for free; the plugin resolves the INNERMOST enclosing unit at the cursor). The parent lists its children in `[CONTAINS]` (the `[FILE]` TOC generalized to any container). **Proportionality holds** — a trivial nested enum (a few obvious values) stays terse-inline, no block; only a rich nested unit (e.g. `MetadataFlag` — 15 bits + a tombstone) earns one. Layout DERIVED is unaffected: a nested *type* adds no bytes, only a *field* of it does — the tool computes `[SIZE]` correctly regardless of doc nesting.
- **`[ASSERT]` unit — static_assert-as-doc (survey B gap #8/#13) — GRAMMAR LANDED (D-340):** a compile-time guard is a LIGHT unit (no `[END]`, like `[MACRO]`), sited on the `static_assert` it annotates: `[ASSERT]_[<FAMILY>]_[<expr>]` + `[WHY]_[<rationale — incl. the remediation the assert MESSAGE carries>]`. FAMILY is an extensible vocab; starter set `{LAYOUT_LOCK · BITMAP_OVERFLOW · EPOCH_TRIPWIRE · OVERLAP_EXCLUSION · PADDING_FREE}` + `REGISTRY_COVERAGE` (registry arity/coverage/enrollment locks — first use CfgFieldRegistry + StrategyInterface at the P6 uplift pass, 2026-07-16) (1-line-add a new one at first use). **`[ASSERT]` ↔ `[DERIVED]` coexistence rule:** an `[ASSERT]_[LAYOUT_LOCK]_[sizeof(T) <= 128]` and the struct's `[SIZE]` DERIVED both name the size — **the assert ENFORCES (a bound; build-fails on violation), the DERIVED REPORTS (the actual value; tool-refreshed)** — complementary, not a mirror. (Phase-4 CI candidate: verify each `[ASSERT]_[…]_[expr]` matches a real `static_assert` on the following line so the doc can't drift from the guard.) Exemplar: § Worked examples → `CfgFieldDescriptor` (`LAYOUT_LOCK` size-pin + `BITMAP_OVERFLOW` metadata-flag guard).
- **Bars = ASCII, 3 weights (D-fmt-2 + D-fmt-3):** `====` unit · `~~~~` sub · `----` section (the v1 Unicode `——` `[COMMENT]` separator → ASCII). `[DIAGRAM]` bodies are **ASCII-UML** (`+--+` boxes · `|`/`---` links · `>`/`v` arrows) — NO Unicode glyphs; a **diagram-helper tool** draws them (no hand-aligning `|`).
- **`[DIAGRAM]_[formula]` (D-fmt-7):** a formula sub-kind of `[DIAGRAM]` — math laid out, plugin-displayable, and explicitly **EXEMPT** from the § CI "prose asserts no derivable fact" check (a formula is a *definition*, not a claimed derived value).
- **`[WIRE_FIELD]` — wire/persist field-map (survey C flagship; D-345 — grounded on `BinanceUserData` executionReport):** a venue/persist unit (JSON parser · FIX table · CSV recorder) documents its field-map as tier-2 members — `[WIRE_FIELD]_[<key>]_[<meaning>]` (+ type/example): JSON is **key-addressed**, FIX/CSV are **ordinal-addressed** (position = the id, like `[COLUMN]`). A documented-absent field = `[EXCLUDED]_[<key>]_[<why-not-parsed>]` (Binance `"z"` cumulative-qty — currently unparsed, surfacing the A2 bug / TECH_DEBT-169). Version via `[WIRE_VERSION]` (H21 append-only keys). **Reuses the member model** — `[WIRE_FIELD]` is just the wire-parser's tier-2 vocab. The widened `[REFERENCE]` prefix-zoo (PARITY/SOURCE/URL — reference-subcats table) + the numeric-domain row (`[OVERFLOW]`/`[ROUNDING]`/`[DOMAIN]`/`[PRECISION]`, in-fence) close the rest of survey C.
- **Build-at-pilot status (P3 dogfood corpus, 2026-07-15 — D-348):** labeled `[COMMENT]_[<label>]` sub-sections — **canonical LANDED** at `tests/schema_golden/golden_file_header.hpp` (the EngineCommon rich file-header: 7 real labeled partitions; form = each label is its own `[COMMENT]_[<LABEL>]` header + prose + a closing `====` bar — parse-trivial, greppable). The concurrency block — PARTIAL: `[SYNC]`/`[THREAD]` structured annotations + tier-2 `[REGION]` scoping piloted on the real `ExecutionCore` (`golden_struct_hot.hpp`); the full file-narrative + cluster `Writer=/Reader=` + per-field `producer:/consumer:` form still grows at ITS first real site (the OrderManager conversion). **Ladder note from the pilot:** `[DIAGRAM]` opens a freeform body, so structured `[REGION]`/`[THREAD]`/`[SYNC]` lines sit ABOVE it in the orient block.
- **`[COMPLEXITY]` (D-309 #4, ADOPT · curated · D-342):** amortized / worst-case trip-count a straight-line `[SIZE]_[instr]` + `[BRANCHES]`-class both miss — `[COMPLEXITY]_[O(1) amortized / O(W) worst]` (e.g. `RollingStats` deque pops). Greppable + carries the bound; CURATED (a tool can't infer the amortized bound).
- **`[APPLY_AFTER]` (D-309 #5, ADOPT · curated · CAPITAL-BEARING · D-342):** walker last-wins expansion ORDER that lives only in `[WHY]` prose today (early-apply re-arms the founding bug — `FOREACH_PER_NODE_ARRAY_OVERRIDE`). `[APPLY_AFTER]_[<other-walker>]` makes the sequencing queryable + CI-checkable.
- **`[MUTATES]` (D-309 #6, DERIVED-TAG · D-342):** the WRITE half of the graph (`[UPSTREAM]`/`[CONSUMERS]` are reads-in + callers). A compact `[MUTATES]_[<N> fields]` (+ the key ones) materialized; the full write-set on plugin hover (no bulky drift-prone comment). Tool-derived (`writers.for_struct` already tracks it).
- **`[WIRE_VERSION]` + paired-bump (D-309 #7, DERIVED-TAG · D-342):** "what do I bump if I touch it" — `[WIRE_VERSION]_[[SHARDED=10] [CONTROLLER=14]]` + a paired-bump note (Position is jointly gated; drifted live 6-vs-7). Materialized from a persist-site→version map, CI-checked vs `identifier_ledger.txt`.
- **Registry topology `[PARENT]`/`[CHILDREN]`/`[SIDECARS]`/`[OVERRIDES]` (D-309 #3, DERIVED-TAG · D-344 — MISSED in the D-342 pass, CAUGHT by the plugin-alignment check):** the meta-registry hierarchy (H16 metadata-bit cohort / H18 sidecar-override / H19 parent-level — only H15 `[ENROLLED]` was covered before). Reproducible from `MetaRegistry` LEVEL/PARENT + `FIELD_IDX` + if-constexpr filters — no grammar change, a DERIVED tag + generator + CI. **Feeds the plugin's registry-tree / row-browser** (north-star §6.10 REGISTRY-SPECIAL + §7.5 5th-role) — the target whose data-need surfaced the miss.
- **Clarifications — BLESS (D-309; the structure already holds · D-342):** (a) **multiple `[DIAGRAM]_[kind]` per block** (Order = byte-map + bit-map; MetaRegistry a registry-tree); (b) **`[DIRECTIVE]` on an `X()`-row inside `[CODE]`** (per-row tombstones — SHALT); (c) **`[CODE]`/`[END_CODE]` for NON-CONTIGUOUS units** — consts + struct + accessors across regions → multiple framed `[CODE]` segments per unit (the stack parser handles it), or the consts/accessors become tier-3 sub-blocks.

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

**PROVENANCE + FRESHNESS — every auto-written fact carries `[ORIGIN]_[AUTO]` + `[UPDATED]` (D-369).** A fact-producer stamps two metadata tags on what it writes: **`[ORIGIN]_[AUTO]`** (machine-written — regenerable, never hand-edit; `[ORIGIN]_[MANUAL]` marks curated content a producer must never clobber) + **`[UPDATED]_[YYYY-MM-DD]`** (freshness). This turns the old free-text `(tool-refreshed — do NOT hand-edit)` note (and the drift-prone `(… emitter cannot probe this yet, D-327)` variants) into structured, machine-readable provenance — the same "structured tag > prose" move the whole schema rests on, applied to the tools' OWN output. **`[UPDATED]` is stamped ONLY on a real value-change** — a no-op refresh does not restamp; this preserves each writer's idempotency (the "run the producer, expect 0-diff" currency check + the Class-56 non-idempotent-writer guard), where a naive every-run timestamp would rewrite the whole corpus each run. ISO-8601 date (canonical/sortable — H9 sibling). Both auto-writers honor it — `check_cache_layout --fix` (struct layout) + the plugin's `:FoxSymdepsDerived!` (call-graph) — each MERGE-preserving the other's facts. ADDITIVE grammar: existing blocks stay CI-green un-stamped; the writers populate `[ORIGIN]`/`[UPDATED]` as they refresh, and a later completeness flip can require them.

**DERIVED — the third disposition: `N/A_FOLDED` (D-340; dogfood-grounded on `cfg_compute_mask`).** Beyond WRITTEN vs LIVE-PREVIEW, a codegen axis can be *structurally absent*: a **compile-time-folded** unit has no runtime code to measure (`cfg_compute_mask` folds to a `.rodata` constant), so `[SIZE]_[instr]` / `[BRANCHES]` / `[SIMD]` are written `[<AXIS>]_[N/A_FOLDED]` — a reserved value (like `[SIMD]_[none]`) telling the tool + CI to SKIP measurement, never read `0`/garbage. The call-graph axes (`[UPSTREAM]` / `[CONSUMERS]`) still apply. **Enforcement (phase-4 CI):** a `consteval` unit's codegen axes MUST be `N/A_FOLDED` (guaranteed immediate); a `constexpr` unit's are `N/A_FOLDED` only when the tool confirms no runtime call site (else it has real codegen at the runtime use) — the tool knows constexpr/consteval-ness from the parse, so this is checkable, closing the "hide a real function behind N/A" hole.

**Refinement A — stale DERIVED-class facts are DROPPED, not relocated (D-309 · D-342).** A hand-written DERIVED-class fact (a byte-map, a size, a version, a row-shape) that has gone stale is BOTH a preserve-voice candidate AND a DERIVED fact — resolution: **the conversion DROPS it, never relocates it** (Position's stale 24B/192B byte-map that contradicts its own `static_assert(==128)` is deleted, not carried forward). Only rationale / history / author-voice is preserved verbatim; byte-maps / sizes / versions / row-shapes are TOOL-REGENERATED.

**Refinement B — unit-level `[LAT_EXEMPT]` (D-309 · D-342) UNIFIES with `N/A_FOLDED`.** A non-hot / non-capital unit (a 60Hz GUI render fn) carries a unit-level `[LAT_EXEMPT]` → suppress the DERIVED latency quartet (`[SIZE]_[instr]` / `[SIMD]` / `[BRANCHES]` + the conformance generator); CI does not flag the omission (proportionality — no forced hot-path ceremony on support code). This is the SAME suppression as the constexpr `N/A_FOLDED` marker (D-340) — different reason (non-latency vs compile-time-folded), one mechanism: **the codegen quartet is written only where it is meaningful.**

**Explicitly NOT done:** (a) HAND-writing or hand-editing a derived fact — the generator owns the `[DERIVED]` block and a hand-edit that drifts from ground truth fails CI (the tool/plugin refreshes it); (b) commented-out old/new code as diffs (git owns the diff; `[EDIT]` + `[REFERENCE]_[DECISION]` own the what/why).

---

## Templates (copy-paste skeletons — HYBRID layout: orient-above / code / detail-below)

> **Validator-green copy-source: `DOCS/CODE_TAG_TEMPLATES.hpp`** — one conforming block per
> unit type (all 10), `[SCHEMA]`-opted-in so standing CI polices the corpus forever;
> `/doc-create code-block <TYPE> <name>` scaffolds from it. The skeletons below are the
> normative SHAPES; the corpus is the proven rendering. (P2 propagation, D-347.)

### Function
```cpp
//======================================================================
// [FUNCTION]_[<Name>]
//----------------------------------------------------------------------
// [TAG]_[[<SURFACE>] [<CONCERN>]]
// [SCHEMA]_[v1.0]
// [OVERVIEW]_[<one-line gist>]
// [DIAGRAM]
//   <hand-ASCII — ASCII boxes (+--+ | +) + arrows (-> <- ^ v); NO Unicode glyphs>
//======================================================================
// [CODE]
//======================================================================
<signature> {
    // code-local comments STAY here, VERBATIM — a step-comment explains the line it sits on + helps
    // you read the code (D-326). ONLY the unit-level WHY (what the whole fn is + why) was lifted to [COMMENT].
    //------------------------------------------------------------
    // [SECTION]_[<first phase>]        // OPTIONAL (D-329): bar-wrapped phase of a big multi-part fn.
    //------------------------------------------------------------  // the plugin reads the `----` bars as
    <phase-1 body — its step-comments stay>                         // begin/end → a within-fn TOC / jump-list.
    //------------------------------------------------------------
    // [SECTION]_[<next phase>]
    //------------------------------------------------------------
    <phase-2 body>
}
//======================================================================
// [END_CODE]
//======================================================================
// [COMMENT]
//~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
// [[<YYYY-MM-DD>] [<version>]]
//----------------------------------------------------------------------
// <what this version does + why — prose; the freeform region>
// [SUPPORTING_DOCS]
//   - [<SUBCAT>]_[<id>]
//======================================================================
// [DERIVED]
//----------------------------------------------------------------------
// [ORIGIN]_[AUTO]                 (fact-producer-owned — regenerated, never hand-edit; D-369)
// [UPDATED]_[<YYYY-MM-DD>]        (stamped only on a value-change — keeps the writer idempotent)
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
// [SCHEMA]_[v1.0]
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
//~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
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
// [STRADDLE]_[<none (FULLY verified — never written for a partial record) | field@off … (real sub-64B straddlers) | … · unverified: f g (fields with UNRESOLVED size whose extent BOUND crosses a line — tri-state, D-413)>]
// [STRADDLE_EXEMPT]_[<field>]_[<reason + decision-ref — CURATED, field-level ONLY (never blanket-struct); silences the H6 gate VERDICT for that field; the FACT still gets written>]
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
// [SCHEMA]_[v1.0]
// [OVERVIEW]_[<what it single-sources; add/drop = 1 row + a version bump>]
// [COLUMN]_[<col1-name>]_[<meaning>]                     // tuple legend — listing order = ordinal (D-339)
// [COLUMN]_[<col2-name>]_[<meaning>]_[<enum token/bit-set, if any>]
// …one [COLUMN] per positional arg; validator checks count == tuple-arity…
//======================================================================
// [CODE]
//======================================================================
#define FOREACH_<NAME>(X)                        \
    /* === <Group label> (n) === */              \   // stays VERBATIM; plugin derives the row-group TOC
    X(...)                                        \
    X(...)                                        \
//======================================================================
// [END_CODE]
//======================================================================
// [ROW]_[<row-id>]_[<why — SPARSE; only rows needing rationale beyond their payload>]   (D-339)
// [ROW]_[TOMBSTONE]_[<retired-id>]                       // retired slot, never reused (H21)
//======================================================================
// [COMMENT]
//~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
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
`[FILE]_[<path>]` identity + `[TAG]_[[<component/domain>]]` (`[ENGINE]`/`[ML]`/`[GUI]`/`[XGBOOST]`/`[CORE]`… — vocab values, added as real files need them) + `[SCOPE]` (if the file is scale-bound) + `[SCHEMA]_[v1.0]` + `[OVERVIEW]` (what it's for) + a data-flow `[DIAGRAM]` + the **file-level graph**: `[CONTAINS]`/`[TOC]` (child units — the file's table-of-contents) · `[CONSUMERS]`/`[INCLUDED_BY]` (who uses it) · `[UPSTREAM]`/`[INCLUDES]` (what it pulls in) · `[BLAST_RADIUS]` (change-impact) · `[BINARIES]` (which build targets link it). Orient-block only (no code body). **Dual role:** the file's TOC anchor AND — via its `[SCHEMA]_[v1.0]` — the per-file conversion/whitelist marker (the CI validator polices a file only once it carries a `[FILE]` block; un-converted files are skipped, `[SCHEMA]_[exempt]_[reason]` opts one out). Same block anatomy as a function/struct → the tool + plugin parse per-FILE and per-UNIT uniformly.

### Variants for other unit types (anatomy-REUSE — tweak the `[DERIVED]`/`[REFERENCE]` set, NOT a new system; build each the first time a real unit needs it during conversion, do NOT pre-enumerate)
- **Strategy** — `[STRATEGY]_[<name>]`; `[TAG]` its regime-fit + op-mode, `[REFERENCE]` its params/spec. A strategy is just another tagged unit (fits the hybrid block exactly); a strategy-dev plugin lens renders a strategy-shaped view of the same facts (operator's domain).
- **Enum (persisted / wire CODES)** — `[ENUM]_[<name>]`; add `[REFERENCE]_[INVARIANT]_[H21]` + a tombstone note (Knight-Capital: append-only, never renumber/reuse a slot). The SHALT / halt-reason / regime / snapshot-version code enums live here.
- **Foundational typedef** (`Money`, `FPN_Binary<F>`, `EngineMoneyT`) — `[TYPE]_[<name>]`; `[SIZE]_[<sizeof>]` + `[REFERENCE]` to the encoding epoch / H4. The money-type SSoT warrants a block; a throwaway alias does not.
- **Macro** (`BITMAP_*` / `MBS_*` accessors) — LIGHT `[MACRO]_[<name>]` (no `[END]`; `[DERIVED]` = branchless?/expansion); most accessor macros stay terse-inline.
- **Test group** (`controller_test` Phase blocks) — `[TEST]_[<name>]`; `[REFERENCE]` to the invariant/decision each verifies → navigation across the 3697-test suite.
- **Compile-time guard** (`static_assert`) — LIGHT `[ASSERT]_[<FAMILY>]_[<expr>]` + `[WHY]` (no `[END]`), sited on the assert; FAMILY ∈ `{LAYOUT_LOCK · BITMAP_OVERFLOW · EPOCH_TRIPWIRE · OVERLAP_EXCLUSION · PADDING_FREE}` (extensible). Coexists with a struct's `[SIZE]` DERIVED — the assert ENFORCES the bound, the DERIVED REPORTS the value (D-340). Size-pin / bitmap-overflow / encoding-epoch guards live here.

**Boundary (same as the tag rule):** the 4 first-class blocks (function / struct / registry / file) cover ~90%; the variants fill in organically. Build a variant when a real unit needs it — pre-designing all of them is *template* sprawl, the very thing this kills at the comment level.

---

## Worked examples

> **Illustrative — NOT the golden fixture.** These show block SHAPE. The `[DERIVED]` numbers are hand-written placeholders (some stale — sizes predating the 16B core) and MUST NOT be frozen as the self-test golden: the committed golden is TOOL-GENERATED from the P2 pilots (`sizeof`/`offsetof`/analyzer), never hand-authored — hand-writing DERIVED is the Class-18 drift the schema bans. They also predate `[CODE]`/`[END_CODE]` framing + the cache/branch DERIVED tags (added at lock); the pilots render the current form.
>
> **Known validator NON-CONFORMANCES below, kept as-written** (the validator-green rendering of every type is `DOCS/CODE_TAG_TEMPLATES.hpp`, standing-CI-policed — copy from THERE, not from here; P2 propagation, D-347): pre-vocab `[TAG]` values (`[BIT_PACKED]`/`[PERSISTED]` → write `[BITMAP_PACKED]`/`[PERSISTENCE]`; `[WIRE_FORMAT]` as a TAG value collides with the fence CATEGORY of the same name — v1.1 vocab-alias candidate) · multi-category single lines (`[DERIVED]  [SIZE]_[…]`, `[ASSERT]_[…]  [WHY]_[…]` — the one-category-per-line rule wants them split) · inline `[CONTAINS]` carrying unit-type values (use the block form) · `[REFERENCE]_[REGISTRY]` (REGISTRY is not a reference-subcat; point at the governing invariant/spec instead) · doubled `[WIRE_FIELD]` per line.

### Function — `Regime_Classify` (Strategies/RegimeDetector.hpp)
```cpp
//======================================================================
// [FUNCTION]_[Regime_Classify]
//----------------------------------------------------------------------
// [TAG]_[[SLOW_PATH] [ML_INFERENCE]]
// [SCHEMA]_[v1.0]
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
// [SCHEMA]_[v1.0]
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

### Struct with nested units + `[ASSERT]` — `CfgFieldDescriptor` (CoreFrameworks/CfgFieldRegistry.hpp · the nesting + guard exemplar, D-340)
```cpp
//======================================================================
// [STRUCT]_[CfgFieldDescriptor]
//----------------------------------------------------------------------
// [TAG]_[[ENGINE] [DATA_ORIENTED_DESIGN]]
// [SCHEMA]_[v1.0]
// [OVERVIEW]_[per-field metadata record the 13-col X-macro materializes into; GUI+parser+validation; boot/60Hz cache-warm]
// [CONTAINS]_[[ENUM]_[Kind] [ENUM]_[MetadataFlag] [ENUM]_[LivesInStruct]]   // nested units → own blocks, sited below
//======================================================================
// [CODE]
//======================================================================
struct CfgFieldDescriptor {
    // [ENUM]_[MetadataFlag]        ← rich nested unit gets its OWN block, sited HERE (15 bits + a tombstone)
    enum MetadataFlag : uint16_t { /* … its own block … */ };
    enum Kind : uint8_t { … };      // trivial-ish → terse-inline unless it earns a block (proportionality)
    //---- [SECTION]_[Header (8 bytes)] ----
    Kind kind; uint16_t metadata_flags; uint16_t _reserved = 0;   // [DIRECTIVE]_[H12_PAD]
    //---- [SECTION]_[Payload union (32 bytes)] ----
    union { … } payload;
};
//======================================================================
// [END_CODE]
//======================================================================
// [DERIVED]   [SIZE]_[<=128B]  [ALIGN]_[8]  [CACHE_LINES]_[2]  [STRADDLE]_[none]
//======================================================================
// [END_STRUCT]_[CfgFieldDescriptor]
//======================================================================

// [ASSERT]_[LAYOUT_LOCK]_[sizeof(CfgFieldDescriptor) <= 128]
// [WHY]_[2 cache lines; GUI 60Hz cache-warm — assert ENFORCES the bound, [SIZE] DERIVED REPORTS the value]
static_assert(sizeof(CfgFieldDescriptor) <= 128, "...");
// [ASSERT]_[BITMAP_OVERFLOW]_[CAPITAL_BOUND_GAIN < (1u<<16)]
// [WHY]_[MetadataFlag must fit uint16; the message carries the remediation: widen->uint32 at the highest bit]
static_assert(CfgFieldDescriptor::CAPITAL_BOUND_GAIN < (1u << 16), "...");
```

### Registry — `FOREACH_GLOBAL_CFG_FIELD` (CoreFrameworks/CfgFieldRegistry.hpp · the `[ROW]`/`[COLUMN]` exemplar)
```cpp
//======================================================================
// [REGISTRY]_[FOREACH_GLOBAL_CFG_FIELD]
//----------------------------------------------------------------------
// [TAG]_[[ENGINE] [FRAMEWORK_DISCIPLINE]]
// [SCHEMA]_[v1.0]
// [OVERVIEW]_[47 global cfg fields — operator sets once engine-wide (not per-node); add a field = 1 row]
// [COLUMN]_[STORAGE_T]_[C storage type]                        // listing order = tuple ordinal (D-339)
// [COLUMN]_[KIND_TOKEN]_[GUI-metadata kind]_[[KIND_INT] [KIND_BOOL] [KIND_DOUBLE] [KIND_STRING] [KIND_FILE] [KIND_HEX] [KIND_RANGE]]
// [COLUMN]_[name]_[cfg identifier → ControllerConfig<F> member (H17)]
// [COLUMN]_[label]_[GUI display string]
// [COLUMN]_[section]_[GUI bucket]_[[Operational] [Engine Timing] [Risk Management] […]]
// [COLUMN]_[meta]_[CfgFieldDescriptor OR-flags]_[[IS_BOOT_ONLY] [WARN_ON_CLAMP] [DEPRECATED] [STAMP_BOUND_CFG_DERIVED]]
// [COLUMN]_[payload]_[ctor matching KIND_TOKEN]_[[INT(def,min,max)] [BOOL(def)] [DOUBLE(def,min,max)] [RANGE(…)]]
// [COLUMN]_[tooltip]_[operator help · nullptr = inherit GUI field_defs[]]
// [COLUMN]_[STRAT/OP_MODE/REGIME/RISK_CAT]_[applicability filters · category tokens]
// [COLUMN]_[storage_class]_[cfg storage tier]_[[STRUCT_CFG] […]]
//======================================================================
// [CODE]
//======================================================================
#define FOREACH_GLOBAL_CFG_FIELD(X)                                                \
    /* === System / Operational (5) === */                                        \
    X(uint16_t, KIND_INT, num_execution_nodes, "Execution Nodes", "Operational",  \
      IS_BOOT_ONLY | WARN_ON_CLAMP, INT(1, 1, 16), "Number of shards. [1,16].", …) \
    /* === Engine timing (5) === */                                               \
    X(uint32_t, KIND_INT, poll_interval, "Poll Interval", "Engine Timing",        \
      WARN_ON_CLAMP, INT(100, 1, 1000000), "Ticks between slow-path runs.", …)     \
    /* … 45 more rows … */
//======================================================================
// [END_CODE]
//======================================================================
// [ROW]_[num_execution_nodes]_[cap 16 = the shard ceiling (H22 / Limits.hpp), not arbitrary]
// [ROW]_[min_warmup_samples]_[caps at 128 = rolling-window size; >128 clamped at load]
//   (SPARSE — most rows carry their per-row help in the tooltip column, not a [ROW])
//======================================================================
// [COMMENT]
//——————————————————————————————————————————————————————————
// [[2026-06-11] [v5.15.5.F.4d.1.E.1.1]]
//----------------------------------------------------------------------
// the engine-wide half of the cfg-field split; the per-node half is
// FOREACH_PER_NODE_CFG_FIELD. one X-macro row → parser + GUI render +
// tooltip + validation all auto-flow (H17). group dividers stay verbatim;
// the plugin derives the section TOC from them.
// [SUPPORTING_DOCS]
//   - [DESIGN_SPEC]_[universal-cfg-field-registry-pattern]
//   - [INVARIANT]_[H17]
//   - [INVARIANT]_[H15]
//======================================================================
// [DERIVED]   (tool-refreshed)
//----------------------------------------------------------------------
// [ROW_COUNT]_[47]
// [ENROLLED]_[MetaRegistry.hpp]
// [CONSUMERS]_[[ControllerConfig_Load] [PerCoreCfg] [SettingsPanel] [CfgFieldDispatch]]
//======================================================================
// [END_REGISTRY]_[FOREACH_GLOBAL_CFG_FIELD]
//======================================================================
```
The `[COLUMN]` tuple-legend (10 lines; the four `*_CAT` filters collapse to one) + `[SECTION]`-derived row-groups (the `/* === … === */` dividers, kept verbatim) + SPARSE `[ROW]` rationale all live in the orient/detail region — the `[CODE]` macro stays byte-verbatim, so a schema tag never meets the `\`-continuation.

### Enum — `OrderState` (CoreFrameworks/Order.hpp · persisted/wire CODE enum · D-341)
```cpp
//======================================================================
// [ENUM]_[OrderState]
//----------------------------------------------------------------------
// [TAG]_[[ENGINE] [OMS_DRAINER] [PERSISTED]]
// [SCHEMA]_[v1.0]
// [OVERVIEW]_[order lifecycle state — packed into Order.flags_packed bits 2-5; codes are wire/persist-visible]
// [REFERENCE]_[INVARIANT]_[H21]        ← codes 0..8 append-only + immutable
//======================================================================
// [CODE]
//======================================================================
enum OrderState : uint8_t {
    //---- [SECTION]_[working] ----
    ORDER_PENDING = 0,  // submitted to OMS, not yet on exchange      ← inline name=code//meaning STAYS (D-326)
    ORDER_SUBMITTED = 1, ORDER_ACKNOWLEDGED = 2, ORDER_PARTIAL = 3,
    //---- [SECTION]_[terminal] ----
    ORDER_FILLED = 4, ORDER_REJECTED = 5, ORDER_CANCELED = 6, ORDER_TIMEOUT = 7,
    //---- [SECTION]_[recovery] ----
    ORDER_UNKNOWN = 8,  // lost tracking, needs reconciliation
};
//======================================================================
// [END_CODE]
//======================================================================
// [VALUE]_[ORDER_UNKNOWN]_[the only non-terminal recovery sink — a reconcile pass resolves it]   (SPARSE, like [ROW])
// [VALUE]_[TOMBSTONE]_[<retired>]_[<code>]   ← the form if a state retires (H21; code never reused)
// [DERIVED]  [ROW_COUNT]_[9]  [SIZE]_[uint8]  [CONSUMERS]_[[Order.flags_packed] [OMS] [Reconcile]]
// [END_ENUM]_[OrderState]
//======================================================================
```
Members: values inline (D-326), `[SECTION]` groups the value-tiers, SPARSE `[VALUE]` only for the one that needs a why.

### Type — `Money` = `FixedPoint<10,8>` (FixedPoint/FixedPointN.hpp · the money typedef + its guards · D-341)
```cpp
//======================================================================
// [TYPE]_[Money]
//----------------------------------------------------------------------
// [TAG]_[[ENGINE] [CAPITAL_BEARING] [DECIMAL] [WIRE_FORMAT]]
// [SCHEMA]_[v1.0]
// [OVERVIEW]_[the money-domain alias = FixedPoint<10,8> — exact decimal at venue 8dp; op family Money_*]
// [REFERENCE]_[DECISION]_[[D-176] [D-181]]        ← domain alias + the encoding-EPOCH flip
// [REFERENCE]_[INVARIANT]_[[H4] [H9] [H12] [H21]]
//======================================================================
// [CODE]
//======================================================================
using Money = FixedPoint<10, 8>;                    // ALIASES the [STRUCT]_[FixedPoint<10,8>] specialization
//======================================================================
// [END_CODE]
//======================================================================
// [DERIVED]  [SIZE]_[16B]  [ALIGN]_[16]
// [END_TYPE]_[Money]
//----------------------------------------------------------------------
// [ASSERT]_[LAYOUT_LOCK]_[sizeof(Money) == 16]                        [WHY]_[H9 wire pin — ~30 memcmp/SHA/HMAC sites; H21 bump on change]
// [ASSERT]_[PADDING_FREE]_[has_unique_object_representations_v<Money>] [WHY]_[H12 — memcmp/SHA/HMAC need zero padding]
// [ASSERT]_[EPOCH_TRIPWIRE]_[MONEY_ENCODING_EPOCH = is_fp_decimal_v<EngineMoneyT>]  [WHY]_[16B→16B flip invisible to sizeof]
```

### File — `CfgFieldRegistry.hpp` (the `[FILE]` orient block = the file's TOC + graph; no `[CODE]`)
```cpp
//======================================================================
// [FILE]_[CoreFrameworks/CfgFieldRegistry.hpp]
//----------------------------------------------------------------------
// [TAG]_[[ENGINE] [FRAMEWORK_DISCIPLINE]]
// [SCOPE]_[DEPLOYMENT]
// [SCHEMA]_[v1.0]
// [OVERVIEW]_[the universal cfg-field registry — two disjoint X-macro registries (global vs per-node), H17]
// [CONTAINS]
//   - [STRUCT]_[CfgFieldDescriptor] · [ENUM]_[MetadataFlag] / [Kind] / [LivesInStruct]
//   - [REGISTRY]_[FOREACH_GLOBAL_CFG_FIELD] / [FOREACH_PER_NODE_CFG_FIELD] (+ 6 more FOREACH_*)
//   - [FUNCTION]_[cfg_compute_mask] (+ the compose family) · [ENUM]_[CfgGlobalFieldIdx] / [CfgPerCoreFieldIdx]
// [INCLUDES]_[[cstdint] [cstddef] [StrategyCategories.hpp] [OpModeCategories.hpp] [5× *CfgFlagRegistry.hpp]]
// [DERIVED]  [BLAST_RADIUS]_[ControllerConfig · PerCoreCfg · SettingsPanel · parser · stamp]  [BINARIES]_[[engine] [engine_gui] [foxml_suite]]
//======================================================================
```
Orient-only (no `[CODE]`); `[CONTAINS]` is the file's clickable TOC — and it's the tier-3 container of every unit above.

### Macro — `BITMAP_IS_SET` (MemHeaders/BitmapMacros.hpp · LIGHT `[MACRO]`, no `[END]`)
```cpp
//----------------------------------------------------------------------
// [MACRO]_[BITMAP_IS_SET]
// [TAG]_[[ENGINE] [BIT_PACKED]]
// [OVERVIEW]_[branchless single-bit test over a bitmap field]
// [DERIVED]  [BRANCHES]_[0 — pure mask + compare]
//----------------------------------------------------------------------
#define BITMAP_IS_SET(field, mask)  (((field) & (mask)) != 0)
```
Most accessor macros stay terse-inline; a LIGHT `[MACRO]` block only when the WHY or a DERIVED (branchless?) earns it.

### Test — `test_config_parser` (tests/controller_test.cpp · `[TEST]` = navigation across the suite)
```cpp
//----------------------------------------------------------------------
// [TEST]_[test_config_parser]
// [TAG]_[[ENGINE] [ENTRY_POINT]]
// [OVERVIEW]_[engine.cfg parse → ControllerConfig fields + %-to-fraction coercion + missing-file defaults]
// [REFERENCE]_[REGISTRY]_[FOREACH_GLOBAL_CFG_FIELD]     ← what it verifies
//----------------------------------------------------------------------
static void test_config_parser() {
    // check("poll_interval parsed", cfg.poll_interval == 50);          ← check()s STAY inline (D-326)
    // check("take_profit_pct parsed (5% -> 0.05)", fabs(tp-0.05)<0.001);
    // check("missing file returns defaults", def.poll_interval == 100);
}
```
`[REFERENCE]` links each test to the unit / invariant / decision it verifies → jump-nav across the ~3700-test suite.

### Assert — standalone `[ASSERT]` guards (LIGHT units on `static_assert`s · the family set)
```cpp
// [ASSERT]_[LAYOUT_LOCK]_[sizeof(Order) == 64]              [WHY]_[wire/persist pin; H9 · H21 snapshot bump on change]
static_assert(sizeof(Order) == 64, "...");
// [ASSERT]_[BITMAP_OVERFLOW]_[HIGHEST_BIT < (1u<<16)]       [WHY]_[flags fit uint16; widen→uint32 at the top bit]
// [ASSERT]_[OVERLAP_EXCLUSION]_[popcount(A & B) == 0]       [WHY]_[a row carries AT MOST ONE of {LOSS,GAIN} — else compile error]
// [ASSERT]_[EPOCH_TRIPWIRE]_[trait-keyed guard]             [WHY]_[an encoding flip invisible to sizeof — the net]
// [ASSERT]_[PADDING_FREE]_[has_unique_object_representations_v<T>]  [WHY]_[H12 — memcmp/SHA/HMAC need zero padding]
```
LIGHT (no `[END]`), sited on the assert; the assert ENFORCES the bound, the guarded unit's `[SIZE]` DERIVED REPORTS the value.

### Wire-parser — `ud_parse_execution_report` (DataStream/BinanceUserData.hpp · the JSON venue field-map · D-345)
```cpp
//======================================================================
// [FUNCTION]_[ud_parse_execution_report]
//----------------------------------------------------------------------
// [TAG]_[[ENGINE] [OMS_DRAINER] [WIRE_FORMAT] [CAPITAL_BEARING]]
// [SCHEMA]_[v1.0]
// [OVERVIEW]_[parse a Binance executionReport JSON fill event → Command; returns 1 on x=="TRADE"]
// [REFERENCE]_[SOURCE]_[Binance WS executionReport docs]     ← external venue contract (widened [REFERENCE])
// [REFERENCE]_[INVARIANT]_[[H5] [H21]]                       ← no scalar JSON in the loop; keys append-only
// ---- the venue field-map (tier-2 [WIRE_FIELD] members; key-addressed) ----
// [WIRE_FIELD]_[e]_[event type = executionReport]   · [WIRE_FIELD]_[x]_[execution type — TRADE = fill]
// [WIRE_FIELD]_[c]_[clientOrderId — our idempotency key (oms_<id>)]  · [WIRE_FIELD]_[i]_[exchange orderId]
// [WIRE_FIELD]_[L]_[last executed price]            · [WIRE_FIELD]_[l]_[last executed quantity]
// [WIRE_FIELD]_[n]_[commission amount]              · [WIRE_FIELD]_[N]_[commission asset]
// [WIRE_FIELD]_[t]_[trade id (dedup)]               · [WIRE_FIELD]_[T]_[transaction time ms]
// [EXCLUDED]_[z]_[cumulative filled qty — CURRENTLY UNPARSED (A2 / TECH_DEBT-169; the partial-fill bug, now VISIBLE)]
//======================================================================
// [CODE]
//======================================================================
static inline int ud_parse_execution_report(const char* json, int len, Command* cmd_out, uint64_t* trade_id_out) { … }
//======================================================================
// [END_CODE]
// [END_FUNCTION]_[ud_parse_execution_report]
//======================================================================
```
The `[WIRE_FIELD]` legend makes the venue contract greppable, and `[EXCLUDED]` turns a documented-absent field into a **visible gap** — here, the unparsed `"z"` *is* the A2 partial-fill bug surfaced in the doc layer.

---

## CI enforcement (extend `check_doc_metadata.py` → also validates code)

1. **Vocab** — every `[CATEGORY]` in the closed set; every `[TAG]`/`[REFERENCE]` value resolves (tag ∈ doc-tag-vocab; `[DECISION]_[D-306]`/`[DESIGN_SPEC]_[x]` EXISTS — `check_capture_audit`-shape → no dangling refs).
2. **Section order** — blocks follow the ladder; out-of-order = fail.
3. **DERIVED vs ground truth** — each `[DERIVED]` line diffed against its generator (`sizeof`/`offsetof`/`gen_code_map`/`calls_graph`/conformance/git); mismatch = build error. **[STATE 2026-08-10: this is the TARGET, partially landed — the LAYOUT axes are gate-checked (`check_cache_layout`, tri-state per D-413); the CALL-GRAPH axes are write-once-UNVERIFIED today (validator header DEFERRED list; D-414 I-2 census: 1 verified / 2 drifted / 2 fabricated) until the A2 symbol-existence+reference-presence gate + the v1 foxtag call-graph axis land.]** **DERIVED facts MUST be REPRODUCIBLE** (deterministic per binary — instruction count / cache spans / offsets / SIMD / branch class, the asm-derived ones pinned by a `[BUILD]` line naming the canonical `build.sh` flags — the count is meaningless without them): a machine-variable metric (measured **ns** — clock/turbo/voltage/core-interrupt dependent) is NEVER a drift-checked comment fact (it would false-RED in CI). **Instruction count (`[SIZE]_[instr]`) is the transferable latency proxy**; the H8 ns budget is a design constraint (`[REFERENCE]_[INVARIANT]_[H8]`); actual ns measurement lives on the separate measurement surfaces (dev-time `fox-bench` fingerprints / the runtime data+monitoring planes), never in this dev-plane comment. **Toolchain split (D-321) — the two fact-families use DIFFERENT compilers:** LAYOUT facts (`[SIZE]_[bytes]` / `[ALIGN]` / `[CACHE_LINES]` / `[STRADDLE]` / offsets) are computed with clang `-Xclang -fdump-record-layouts` (a clang-only flag, but Itanium-ABI-identical to the shipped g++ for these POD / H12 / H14-no-bitfield structs). CODEGEN facts (`[SIZE]_[instr]` / `[BRANCHES]` / `[SIMD]` / spills) MUST use **g++** (the shipped compiler) with the `[BUILD]` flags — clang's instruction selection + branch codegen diverge from g++, so a clang instr-count / branch-class would be WRONG for the binary we actually run. (The clang layout probe uses only the portable flag subset `-I` / `-isystem` / `-D` / `-std` — the g++ `compile_commands.json` carries `-flto` / `-funroll-loops` that clang rejects; reuse `sizeprobe._filter_flags`, don't fork it.)
4. **Closers** — every `[STRUCT]`/`[FUNCTION]`/`[REGISTRY]` has a matching `[END_*]`.
5. **Prose asserts no DERIVABLE fact** — curated `[WHY]`/`[DETAIL]` states the WHY (rationale/intent/history) but NEVER restates a machine-derivable WHAT. Codegen-keywords in prose (branchless / CMOV / no-spill / SIMD / inlined / a size or instr claim) are cross-checked against the corresponding DERIVED tag (`[BRANCHES]`/`[SIMD]`/`[SIZE]`…) — a contradiction FAILS the build. **Rationale (SSoT):** a derivable fact restated in prose is a second, UNCHECKED copy = a drift surface; the fact lives ONCE, in its DERIVED tag, and prose *references* it (`[BRANCHES]_[0]`) rather than *asserting* it ("branchless"). This structurally closes the **prose-lies-about-codegen** class (a stale "CMOV/branchless" comment relocating verbatim as a false claim CI never inspected — RBP-class candidate).

---

## Schema evolution (`[SCHEMA]_[vN]`)

The convention self-versions. When it evolves v1→v2, a migrator greps `[SCHEMA]_[v1.0]` blocks and upgrades them in place — no big-bang re-convert. A block without `[SCHEMA]` = un-migrated legacy (reported by the metadata audit). This is how the format changes safely over the codebase's life.

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

**End of in-code-documentation-schema v1.0 — LOCKED 2026-07-14 (D-346).** Formalizes D-306 + the deep_dives sketches. First-canonical full-convention application = the incremental codebase conversion (next session).
