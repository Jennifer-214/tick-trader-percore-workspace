---
type: input-space-taxonomy
status: accumulating (1 of 3 surveys landed)
stage: 2-draft   # explicitly self-describes as accumulating (1 of 3 surveys landed), so it has not earned a first-canonical claim
established: 2026-07-06
tags: [in-code-documentation, tag-system, schema-completion, doc-discipline]
sister_specs:
  - in-code-documentation-schema.md
  - in-code-doc-system-north-star.md
---

# Format Input-Space Taxonomy — the schema-completion payload

> The enumerated set of comment/documentation SHAPES the real codebase uses, so the
> schema is designed to hold **all** of them losslessly (per *don't-generalize-the-
> substrate-before-its-input-space-is-known*). Accumulated from the 2026-07-06 comment-
> shape surveys. **Do NOT freeze the schema until all three surveys land + this is synthesized.**

## Survey status

| Survey | Scope | Status |
|---|---|---|
| A | Strategies/ + ML_Headers/ (39 files) | ✅ landed (below) |
| B | CoreFrameworks/ (richest — EngineCommon file-header blocks) | ✅ landed (below) |
| C | FixedPoint/ MemHeaders/ DataStream/ Backtest/ GUI/ | ✅ landed (below) |

## THE META-FINDING (the reframe — this is the whole insight)

The schema models documentation at **UNIT granularity** (`[FILE]`/`[STRUCT]`/`[FUNCTION]`/
`[REGISTRY]` + one flat `[COMMENT]` region + `[SECTION]` *inside a function*). Richer files
document at:
- **SUB-unit granularity** — registry *columns* + *rows*, struct *field-clusters*, enum *tiers*.
- **SUPER-unit granularity** — cross-function lifecycle stages, cross-file surfaces.
- **STRUCTURED prose** — labeled / numbered / tabular / ✓✗ / formula content that the single
  flat `[COMMENT]` flattens.

**Every gap clusters at that granularity + structure mismatch.** So schema-completion is NOT
"add N tags" — it's: **add sub-unit + super-unit granularity, add structured-prose capability,
then fold a handful of missing tags.** This unifies every scattered finding (EngineCommon's
file-header blocks = super-unit + structured; registry column docs = sub-unit; helper-decls =
super-unit).

## GAP LIST — Survey A (Strategies + ML), ranked by leverage

### Tier 1 — pervasive, highest leverage

1. **Registry column/row SUB-UNIT docs** (NO; all 11 registries). `[REGISTRY]` documents the
   unit; files document *columns* (tuple legend, dispatch-axis token-sets, metadata-bit keys,
   truth-tables) + *rows* (per-row rationale, group dividers, mid-macro essays, tombstone notes).
   → **Fix:** a `[COLUMN]` sub-schema (name→meaning→token-set) + a row-addressable in-FOREACH
   annotation (X-macro-safe analog of `[SECTION]` that survives `\`-continuation).
   *Exemplars:* `M/CfgDriftCheckRegistry.hpp:69,196,233,282` · `M/FeatureRegistry.hpp:480` ·
   `M/bandit_dispatch_table.hpp:148` · `S/StrategyInterface.hpp:275`.
2. **Structured prose inside the flat `[COMMENT]`** (PARTIAL; every algo + strategy header).
   Multi-topic labeled headers (RidgeBlender 40-line block), numbered lists, ✓/✗ pairs,
   `entry:/exit:/adaptation:`, condition→action tables, `Note:/Pitfall:` — all flatten.
   → **Fix:** labeled sub-sections `[COMMENT]_[<label>]` or a nested-heading grammar within
   `[COMMENT]`/`[DETAIL]`. *Exemplar:* `M/RidgeBlender.hpp:8-52`.
3. **Math/formula content** (PARTIAL/NO; most ML-math). No formula region; **inline equations
   COLLIDE with CI §5 (prose-asserts-derivable-fact)**. → **Fix:** a `[FORMULA]` /
   `[DIAGRAM]_[formula]` region that is **EXEMPT** from the codegen-keyword cross-check.
   *Exemplars:* `M/BarrierGate.hpp:12` · `M/LinearRegression3X.hpp:145`.
4. **Numeric-domain claims** (NO; ULP/overflow/rounding/precision — dense in ML-math).
   → **Fix:** fold the numeric-domain tag set (`OVERFLOW`/`ROUNDING`/`DOMAIN`/`PRECISION`).
   *Exemplars:* `M/ReciprocalLUT.hpp:16` · `M/BarrierValidation.hpp` (`CONVENTION:`).
5. **`[REFERENCE]_[PARITY]` subcat** (NO; pervasive). `PARITY_ISSUES.md` is a first-class ledger
   with no resolver row. → **Fix:** one `reference-subcats` row → `PARITY  DOCS/PARITY_ISSUES.md`.

### Tier 2 — high, structural

6. **`[REGION]` + `[SECTION]` beyond function bodies** — cross-fn banners, registry group
   dividers, enum/struct field-cluster headers. *Ex:* `S/StrategyLifecycle.hpp:54` ·
   `M/RollingStats.hpp:40` · `S/StrategyCategories.hpp:28`.
7. **External-repo / source-authority provenance** — `port of FoxML_Core .../*.py:line` (the
   train-side canonical anchor). → `[REFERENCE]_[SOURCE]`/`[EXTERNAL]` (resolver EXISTENCE-
   UNCHECKED). *Ex:* `M/RidgeBlender.hpp:51` · `M/BarrierGate.hpp:15`.
8. **`[ASSERT]`/`[GUARD]` unit variant** — count-lock/size-pin/tripwire static_asserts carry WHY
   + forward-migration in the message; models the assert-enforces-`[DERIVED]` relationship (+ a
   coexistence rule w/ tool-owned `[SIZE]`). *Ex:* `M/BanditAlgorithmRegistry.hpp:164` ·
   `M/RollingStats.hpp:135` (D-229 size-pin).
9. **`[DIRECTIVE]` beyond `[LAT_EXEMPT]`** — imperative `NEVER memcpy` / `Do NOT add flat field` /
   `QUARANTINED`. → fold `[NEVER]`/`[ANTI_PATTERN]`/`[WIRE_PIN]`. *Ex:* `S/RegimeDetector.hpp:572`.
10. **Train↔serve parity / `[SEAM]` as a queryable axis** — the identity `/parity-check` protects
    can't be named/grepped. → fold `[SEAM]`/`[TAG]_[PARITY]`. *Ex:* `M/BarrierValidation.hpp:8`
    (PRODUCER↔CONSUMER two-seam) · `M/FeatureStandardizer.hpp:11`.
11. **`[REFERENCE]` sub-anchor** — resolves the doc but drops `Part 2.4` / `Rule 7` / finding-IDs
    (`F7-F10`, `P6.3`, `.E.0.10 A1`). → optional sub-anchor + finding-ID subcat.
12. **Add-a-row extensibility recipe** — the numbered "adding X = 1 row: 1… 2… 3…" compresses to
    a one-line `[OVERVIEW]`. *Ex:* `M/EzooInitFlagRegistry.hpp:8`.

### Tier 3 — medium/niche (each has ≥1 concrete exemplar in the transcript)

Multi-version changelog ladder (repeatable `[VERSION]`) · persisted FILE-format byte-table
(`WIRE_VERSION` + non-offsetof `[DIAGRAM]` kind) · algorithm `COMPLEXITY` (O-notation + µs budget,
design-time — banned from `[DERIVED]`) · `CLAUDE_MD_ITEM` ref subcat · manual-vs-auto `[CONSUMERS]`
marker · in-comment usage-example + directory-tree + walker-pseudocode `[DIAGRAM]` kinds ·
status-annotated banner (`[… — STUB]`) · excluded-set-with-rationale · deliberate-duplication/
SSoT-exception · file-afterword voice-prose slot · tuning-constant `#define`-group · banner-style
normalization (`====`/`----`/unicode `─────`/width — a converter concern).

## GAP LIST — Survey C (primitives / parsers / backtest / DataStream / GUI)

The dominant NEW cluster: **venue / wire-format schema** — the parser layer documents external
contracts (JSON keys, FIX tags, REST endpoints, CSV columns, ANSI escapes) the schema has no home for.

**True gaps (NO tag fits) — the venue/wire-format cluster:**
- **JSON venue field-map** (flagship; all 3 Binance parsers) — aligned `"L": last exec price` key→meaning
  legend. A `[DIAGRAM]` byte-map does not model a JSON key list. *Ex:* `BinanceUserData.hpp:298`.
- **FIX tag=value schema table** — numbered wire-tag dictionary (`35 = MsgType (W=snapshot…)`). *Ex:* `FauxFIX.hpp:17`.
- **CSV column-schema** (pervasive, 6 recorders/logs) — the persisted-format SSoT
  (`timestamp_us,last_update_id,bid_price,…`). *Ex:* `DepthRecorder.hpp:10`.
- **REST endpoint / verb / auth doc** (`POST /api/v3/… — API-key-only, no HMAC`). *Ex:* `BinanceUserData.hpp:240`.
- **ANSI escape-code note** (`\033[H` vs `\033[2J`, truecolor SGR) — densest in TUIAnsi.hpp. *Ex:* `EngineTUI.hpp:184`.
- **Sample wire-message payload** (literal FIX/JSON exemplar bytes). *Ex:* `FauxFIX.hpp:12`.
- **REST HMAC-signing recipe** (query-string + recvWindow + signature). *Ex:* `BinanceOrderAPI.hpp:406`.

**Partial (tag exists, structure drops):** venue error-code legend + docs-URL provenance · bit-pack
Encode/Decode recipe (beyond the byte-map) · color-palette escape+hex+role triple · labeled-subsection
doc (`Returns:/USED BY:/Architecture:`) · numbered-step lifecycle contract · seqlock/single-writer SYNC
protocol recipe · integer-code→label field legend · registry-field membership binding · reader→writer
schema cross-ref · postmortem/BUG-FIX narrative · validation-STATUS marker · external-standard citation
(RFC / Numerical-Recipes) · resource/capacity estimate.

**LOSSLESS CONSTRAINT (rendering layer):** glyphs are stored TWO ways — literal Unicode (`████░░`) AND
hex-escaped UTF-8 with a trailing legend (`"\xe2\x96\x88"; // █ full block`). The converter must preserve
BOTH byte-for-byte and must NOT normalize one into the other.

**Backtest (ML) — 3 hard NOs** (prompt-predicted, confirmed): look-ahead/leakage-safety note · formal
label-definition · statistical-method/formula. (Full 36-shape backtest detail in the ad5de transcript.)

## Cross-agent META-FINDINGS (independently confirmed by ≥2 surveys — high confidence)

- **True ASCII box-art is essentially ABSENT.** `[DIAGRAM]`'s real instances are byte-maps, bit-tables,
  interval notation, byte-offset maps — NOT drawn canvases. → scope `[DIAGRAM]` to those kinds; do NOT
  over-spec it for layout art that doesn't exist (on-screen mascots live in `printf`, not comments).
- **TODO/FIXME markers are ABSENT — deferred work is prose-encoded** ("STUB" / "deferred to vX" /
  "Future-thinking:"). → a `[DEFERRED]`/`[FUTURE]` classifier, not a grep for TODO.
- **Reference "prefix zoo"** — `[REFERENCE]` must accept far more than H/D: PARITY, finding-IDs (F7-F10,
  P6.3), RFC, external URLs, CLAUDE.md items, `[[memory]]`, source-authority `.py:line`. Confirms A/5/7/11.
- **License-preamble variance** — 3-line AGPL vs 1-line SPDX vs MIT; the `[FILE]` preamble must hold all.
- **Recurring cross-thread + display shapes** — display↔execution invariant notes, torn-read/seqlock
  snapshot protocols, ImGui-idiom landmines — recur across files; confirm the `[SEAM]`/`[SYNC]`/`[INVARIANT]` gaps.

## Cleanest single-row folds (do FIRST once the schema opens)

`[REFERENCE]_[PARITY]` (gap 5) · the numeric-domain tag set (gap 4) · external-`[SOURCE]` ref
subcat (gap 7) — each is ONE `\`\`\`category-set` / `\`\`\`reference-subcats` row with an existing
exemplar. The two **deepest** structural additions: the **registry column/row sub-schema** (gap 1)
+ **labeled sub-structure inside `[COMMENT]`** (gap 2) — together they cover the majority of the
richer-file documentation the current draft can't hold losslessly.

## Cross-cutting design constraints surfaced

- **`[FORMULA]`/formula content must be EXEMPT from the CI §5 codegen-keyword cross-check** — else
  every legit equation trips the "prose asserts a derivable fact" guard.
- **`[ASSERT]`/`[DERIVED]_[SIZE]` coexistence** — a size-pin static_assert + the tool-owned SIZE
  tag both claim the size; need a rule for who-owns-what (likely: assert enforces, DERIVED reports).
- **Banner normalization** — `====` (unit) vs `----` (section) vs stray unicode `─────` / varied
  widths: the converter must normalize, and the survey found in-fn `====` where the schema wants `----`.

## GAP LIST — Survey B (CoreFrameworks — the richest; 6 sub-surveys)

**Framing fact:** NO CoreFrameworks file carries `[FILE]_[…]` yet (RegimeDetector is the sole converted
file). The dir uses the format's ANCESTORS informally: `//====` bars (47 files), `// [LABEL]` banners
(**109×**), `=== label ===` heads (23×), `//---- label ----` sub-dividers (51×). Conversion = **type +
close + normalize** these.

1. **Per-registry-ROW + COLUMN sub-schema** (pervasive — ~15 registries; THE biggest hole). A row carries
   positional metadata columns + free-text tooltip (`\n`/concat/`%%`/`R"()"`) + optional pre-row `/*…*/`
   rationale threaded through `\`-continuations + tombstone. Whole-registry `[DERIVED]` exists; NO per-row
   `[ROW]`. *Ex:* `CfgFieldRegistry.hpp:505`.
2. **Inline version-tag edit trail (899× — THE most frequent shape).** `// v5.x.y — …` leading/trailing/mid-sig
   + stacked per-field changelog. → DECISION: code-local, or an inline `[V]`/`[EDIT]` micro-tag. *Ex:* `ControllerEventLoop.hpp:2276`.
3. **[SECTION] must generalize** — 51× `----` + 23× `===` + unbarred ALL-CAPS runs; 5 competing styles; genuine
   2-LEVEL nesting (Phase ⊃ {Peak, Drawdown, Trip}); section-vs-step ambiguity; beyond function bodies. *Ex:* `ControllerEventLoop.hpp:2912`.
4. **The "Phase" cross-file taxonomy** — `Phase 2.1`/`Phase H` are stable IDs recurring non-adjacently, NOT local
   labels — but "Phase" collides with `[SECTION]`. → `[REFERENCE]_[PHASE]`. *Ex:* `ControllerEventLoop.hpp:1929` (same ID :1980/:438).
5. **`// [LABEL]` open-vocab banners (109×)** — free-text labels, UNSTATED unit-type, OPEN vocab. Conversion must
   type each + close the vocab. *Ex:* `ExecutionCore.hpp:6`.
6. **Wire-format completeness (capital-critical, H9/H21)** — raw positional `fwrite` order (no per-field ordinal),
   wire-EXCLUSION rationale (documents an ABSENT field), version-history ledger, version `Was:` tombstone,
   negative "safe-to-reorder/greps-cleared-DATE" clearance. → wire unit variant w/ per-field ordinals + present/
   absent/EXCLUDED. *Ex:* `ShardedSnapshotPersist.hpp:189,252`.
7. **Multi-section named discipline blocks** in headers (PURPOSE / LIFECYCLE / CONST-CORRECTNESS / EXEMPTION /
   STATIC-SCOPE) — flatten into one `[COMMENT]`. *Ex:* `EngineCommon.hpp:9` ← the block Caramel flagged.
8. **Thread-ownership at 3 granularities** — whole-file CONCURRENCY-MODEL narrative + cluster `Writer=/Reader=/
   Isolation=` + per-field `producer:/consumer:`. *Ex:* `OrderManager.hpp:36,543,346`.
9. **Registry orient-block sub-slots** (13 files, same opener quartet) — pattern-lineage + mirror-cost arithmetic
   + "add-1-row→N-sites" recipe + `DRIVES` enumeration. *Ex:* `SlowPathGateRegistry.hpp:24`.
10. **Provenance vocab is OPEN (306+ tokens)** — beyond `D-/H#/Class-N/TECH_DEBT-`: audit severity+`/skill`+SHA ·
    `③` sigils · `item-N`/`NEW-N` ship-phase · `option c` selectors · `✅ CLOSED vX` glyphs · `file.hpp:NNN`
    citations · `spec.md Pattern 3` · scope-caveats. *Ex:* `OrderManager.hpp:486`.
11. **[DIAGRAM] sub-types + a Unicode CONFLICT** — swim-lanes/state-machines/filesystem-trees/`→` arrow-tables/jq.
    Schema says `[DIAGRAM]` ASCII-ONLY, but code uses U+2500/2550 box-drawing (43× lines) INCONSISTENTLY. → allow
    Unicode OR transliterate (violates preserve-voice); **pick ONE canonical bar glyph.** *Ex:* `OrderManager.hpp:13`.
12. **Struct dividers carry semantics** — access-tier bands (HOT/WARM/COLD + placement rationale) + caller-obligation
    bands (REQUIRED/OPTIONAL). *Ex:* `ExecutionCore.hpp:70`.
13. **static_assert families (3 distinct)** — layout-lock cluster · semantic-epoch tripwire (invisible to sizeof) ·
    operator-remediation-playbook message. *Ex:* `Order.hpp:404`.
14. **Special WHY-blocks** — DORMANT reactivatable-guard fail-loud · embedded postmortem/repro (Run 1/Run 2) ·
    branchless before/after + budget-%. *Ex:* `OrderManager.hpp:1157`.
15. **Include-block annotation** — per-header symbol enumeration + phased grouping. `[INCLUDES]` is a NAME-list;
    loses the what-it-provides. *Ex:* `EngineCommon.hpp:99`.
16. **Two hazards the FORMAT creates** — (a) commented-out code scaffolds EXIST despite the schema calling them
    "not done" → disposition rule (delete vs `[FUTURE_WORK]`); (b) stale coexisting diagrams (Portfolio has 3
    byte-maps, one 128B + one superseded 192B) → single-source `[DIAGRAM]` + supersession marker.

## UNIFIED SYNTHESIS — the schema-completion spec (A + B + C, deduplicated)

**The meta-finding (all 3 surveys):** the v1.0 schema is UNIT-granularity + flat-prose. Real docs need three
capabilities it lacks — **SUB-unit** reach (registry rows/columns, struct field-clusters, enum tiers), **SUPER-unit**
reach (cross-function lifecycle, the cross-file Phase taxonomy), and **STRUCTURED prose** (labeled/numbered/
tabular/formula/✓✗). Schema-completion = **grant those three**, and the specific tags fall out.

**Highest-leverage additions (ranked; ≥2 surveys unless noted):**
1. Per-registry **[ROW] + [COLUMN]** sub-schema (A+B) — the single biggest hole (~15 registries).
2. Labeled sub-structure inside **[COMMENT]** (A+B+C).
3. Generalized **[SECTION]** (A+B) — absorb `===`/`----`/unbarred + ONE sub-level + section-vs-step rule + beyond-function.
4. Widened **[REFERENCE]** grammar (A+B+C) — the 306+-token "prefix zoo".
5. **Wire/persist** completeness (B+C) — per-field ordinals + present/absent/EXCLUDED + version-ledger + CSV-column-schema + JSON-field-map + FIX-table.
6. **[FORMULA]** region + numeric-domain tags (A+C) — EXEMPT from the CI §5 codegen-keyword check.
7. **[DIAGRAM]** sub-types + the Unicode/bar decision (B+C) — scope to byte-map/bit-table/swim-lane/tree/formula (NO ASCII-art); preserve glyphs-two-ways.
8. Structured **concurrency** block (B).
9. **static_assert** families + **[ASSERT]/[SIZE] coexistence** rule (assert enforces, DERIVED reports).
10. Inline **version/edit** micro-tag OR an explicit code-local ruling (B — 899×).
11. **[DEFERRED]/[FUTURE]** classifier (C — TODO/FIXME absent, prose-encoded).
12. Special **WHY-blocks** (A+B). 13. **Include-block** annotation (B). 14. **Preserve-voice** hardening (B).

## ✅ RESOLVED — the 8 format decisions LOCKED 2026-07-06 (gate LIFTED; final calls in decision-log "D-fmt SLATE RESOLVED")

> **Final slate:** 1 code-local + D-338 grammar · 2 ASCII 3-weight bars (`====`/`~~~~`/`----`) · 3 ASCII-UML +
> diagram-helper (NOT Unicode) · 4 `[SECTION]_[Phase N]` label (`[REFERENCE]_[PHASE]` dropped; cascade → dep-tools/D-334) ·
> 5 `[SWAR]` sub-tag of bit-packing · 6 `[FUTURE_WORK]` + `[OUTDATED_INFO]` (manual-delete) · 7 `[DIAGRAM]_[formula]` ·
> D-338 version-grammar-forward (NO wipe; H21). **New primitives:** sub-tags · `[OUTDATED_INFO]` · version-grammar ·
> diagram-helper · cascade-viz. The bullets below are the original options — superseded by the above.

### (original open questions — superseded, kept for context)

- **D-fmt-1 · Inline version-tags (899×):** stay code-local (survive verbatim in `[CODE]`; plugin DERIVES the
  version-edges by parsing `// vX.Y` — no hand-tagging, still navigable), or a hand-placed `[V]`/`[EDIT]` micro-tag?
  *(Recommend: code-local + derived-navigation.)*
- **D-fmt-2 · Canonical bars:** `====` unit / `----` section; normalize `===`(23×) + Unicode bars → ASCII at
  conversion. *(Recommend: ASCII structural bars.)*
- **D-fmt-3 · `[DIAGRAM]` Unicode:** allow U+2500 inside `[DIAGRAM]` (swim-lanes/trees need it); transliterating
  violates preserve-voice. *(Recommend: allow, scoped to `[DIAGRAM]`.)*
- **D-fmt-4 · `[SECTION]` vs Phase:** `[SECTION]` for local, `[REFERENCE]_[PHASE]` for the cross-file taxonomy.
- **D-fmt-5 · SWAR representation** (toolchain side) — source-idiom detection vs manual tag.
- **D-fmt-6 · Commented-out-code disposition** — delete vs `[FUTURE_WORK]`.
- **D-fmt-7 · `[FORMULA]` CI-exemption** — formula content must be exempt from the CI §5 derivable-fact check.

**Sequence:** these decisions → complete the schema → dogfood corpus (prove lossless) → toolchain → plugin → convert.
