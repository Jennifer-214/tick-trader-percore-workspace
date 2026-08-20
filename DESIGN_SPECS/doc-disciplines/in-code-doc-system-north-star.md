---
type: north-star
status: living — re-grounded 2026-08-19 against the three-agent census (evidence: plans/v5.15-live-readiness/reports/2026-08-18-north-star-gap-census/)
stage: 3-first-canonical   # the tag system it describes SHIPPED (E.1.2.A schema lock + full corpus conversion); §6/§7.5/§8.5/§8.6 are cited as the governing target UX by the live E.1.2.B plan body
established: 2026-07-06
updated: 2026-08-19
tags: [in-code-documentation, tag-system, tooling, custom-ide, doc-discipline]
sister_specs:
  - in-code-documentation-schema.md
  - format-input-space-taxonomy.md
supersedes_sketch: decision-log D-330 (custom-IDE end state)
---

# North Star — The In-Code Documentation System (the "custom IDE")

> The single authoritative statement of what we are building, why, and the gap to
> current. Every plan, schema change, toolchain fix, and plugin rework hangs off this.
> When a decision is unclear, it is resolved *against this doc*. Living draft — refined
> as the comment-shape survey lands + as decisions settle.

## 1. What we are building (one paragraph)

Source code where **every unit** (file / struct / function / registry) carries a
standardized, **tool-maintained** documentation block — human intent in prose, and
compiled-reality facts (size, layout, call-graph, codegen class) *derived by tooling and
kept honest by CI*. A shared toolchain produces those facts once; a CI gate re-derives
them on every change and red-builds on drift; an nvim plugin surfaces + edits it all at
the cursor; a pop-out viewer floats referenced docs beside the code. **The code becomes
the IDE** — self-documenting, self-verifying, navigable — with the plugin as a **non-CLI application of the whole
toolchain** (every producer/query editor-native, not just a render surface; the scope-increased V1 —
D-372 / §6 / §8.6). A format designed **once**, so it
never has to be re-standardized across a career of projects.

## 2. Why (the payoff — in priority order)

1. **No doc-drift, ever.** Derived facts are CI-gated: a stale comment is a *red build*,
   not a latent lie. Kills the recurring "the comment says X, the code does Y" bug class
   — which in HFT actively misleads (a stale `branchless`/`cmov` note inverts a judgment).
2. **Compiled-reality made visible at edit-time.** Branchless/SIMD/SWAR/layout/straddle —
   the H6/H7/H8/H20 disciplines — shown *where you edit*, not discovered in a profiler.
3. **Navigation + insight → better AI-collaboration.** Higher resolution on the codebase
   makes the operator a sharper director of the AI; raises the ceiling on *all* downstream
   work. The plugin **enables** the engine work, it does not compete with it.
4. **Design-once.** Settle the format + toolchain now → every unit ever written inherits
   it; never re-derive or re-standardize a format again.

## 3. The architecture — four layers, one producer, many consumers

```
   [ TAGS ]  ── load-bearing substrate (the SSoT every consumer reads)
      │
      ▼
   [ TOOLCHAIN ] ── ONE shared fact-producer (recordlayout · sizeprobe · asm · clangd)
      │              no Class-18 mirror; layout=clang, codegen=g++ (D-321)
      ├──────────────┬───────────────────────┐
      ▼              ▼                         ▼
   [ CI GATE ]   [ PLUGIN ]              [ DOC-VIEWER ]
   auto-rederive  nvim surface            [REFERENCE] resolves →
   + drift-gate   (HUD/panel/overlays)    floats the doc beside code
   (update_toolchain.py) (edits + displays)
```

**The linchpin:** all consumers read the **one** producer + the **one** tag substrate.
Complete the producer once, correctly → CI gate + plugin + doc-viewer inherit it
simultaneously. Integration is *structural* (guaranteed by the single core), not
maintained by hand-aligning copies. This is the anti-Class-18 discipline paying off.

> **Authority caveat (D-415, 2026-08-10):** one core in DESIGN, two-lane in runtime authority
> until the v1 re-arm — layout/inventory authority deliberately re-inverted to the script side
> (Lua emitter / Python collector; frozen foxtag is the parity-gated opt-in via `--backend
> foxtag`), while `fields`/`codegen` stay foxtag-native. The batch verb is
> `tools/update_toolchain.py` (D-374/D-418; explicit-invoke only, hooks forbidden) — nothing
> named `:FoxTagUpdate` exists or is needed (§10).

## 4. Layer 1 — The format (the substrate)

**Target:** capture **every** comment/documentation shape in the codebase **losslessly**.
Code-local comments STAY verbatim in `[CODE]` (D-326); only unit-level WHY relocates to
`[COMMENT]`. Reformatting must never *compress away* detail (the EngineCommon-file lesson).

**Current (schema v1):** unit blocks · `[TAG]/[SCOPE]/[SCHEMA]/[OVERVIEW]/[DIAGRAM]` ·
`[CODE]…[END_CODE]` · `[COMMENT]` · `[SUPPORTING_DOCS]` · `[DERIVED]` · `[SECTION]`
within-fn markers (`----` bars).

**Gap dispositions (survey landed D-333; schema LOCKED `[SCHEMA]_[v1.0]` 2026-07-14, D-345/D-346
— all 14 surveyed shapes verified covered; re-grounded 2026-08-19):**
- Annotated include blocks → **PARTIAL**: the `[INCLUDES]` name-list axis exists; the
  per-include *what-it-provides* annotation is the taxonomy's own named loss (synthesis-13).
- constexpr/const rationale → **RESOLVED-BY-SURVEY as a non-shape** (zero occurrences; absorbed
  by labeled `[COMMENT]` WHY-blocks).
- Helper-declarations section → **RESOLVED**: `[REGION]` + generalized `[SECTION]` + the tier-2
  member model.
- File-header multi-section blocks → **RESOLVED**: labeled `[COMMENT]_[<LABEL>]` partitions
  (canonical landed in `tests/schema_golden/golden_file_header.hpp`).
- Complete per-type `[DERIVED]` set → **SPECIFIED** (the D-339 declarative axes table +
  `N/A_FOLDED`/`[LAT_EXEMPT]`); enforcement is deliberately per-axis — struct layout quartet
  HARD-gated; function codegen axes live-preview-only by the T6 authorship split; completeness
  remainder tracked at TECH_DEBT-243/-236.
- `[SWAR]` axis → **DECIDED** as the `[BIT_PACKED]_[SWAR]` sub-tag (D-fmt-5, auto-detect
  direction); the source-idiom **detector itself is still unbuilt**.

> The 2026-07-06 comment-shape survey COMPLETED → `format-input-space-taxonomy.md` (3 surveys +
> the 14-item synthesis + the 8 locked format decisions). The don't-freeze-early guard did its
> job and is retired with the lock.

## 5. Layer 2 — The toolchain (fact-producer + CI)

**Target:** a **complete**, template-aware fact-producer emitting every axis per unit
type; one command — **`:FoxTagUpdate`** — that autopopulates the full `[DERIVED]` block for
one unit interactively AND every file at CI; a **generalized drift-gate** (the cache-gate
D-320 extended from layout to all written axes: layout always, call-graph always, codegen
pinned to `[BUILD]`/`[INSTANTIATION]` per D-327).

**RC dispositions (re-grounded 2026-08-19 — the catalog below is the NAMED RECORD; read state here first):**

| RC | State | How |
|---|---|---|
| RC-A | **SUPERSEDED-IN-APPROACH** | instantiation anchors landed in `foxtag codegen` (D-351); the honest asm now comes from the D-419 per-build objdump SIDECARS (real instantiations, `-flto` truth) + `--isolate` probe-TUs + `template_args` |
| RC-B | **CLOSED** (different mechanism) | TD-257: `CMAKE_EXPORT_COMPILE_COMMANDS=ON` every build dir · `compile_command.py` the ONE source · probes read the SHIPPING db · sidecars ride the build. Residual: per-header db entries + general header→TU map (parked design work) |
| RC-C | **CLOSED** | D-351 real width-class incl. scalar-xmm; SIMD chips on the shipped card |
| RC-D | **CLOSED** (flags half) | shipping-first `flags_for`; layout=clang / codegen=g++ per D-321/D-350 |
| RC-D′ | **CLOSED** | real per-function distinct-64B-line density (plugin `writers.lua`); the per-field half subsumed by RC-F(a) as predicted |
| RC-E | **CLOSED, all layers** | producer vacuity floor (D-351) · card honesty states · the last overlay residue (branchtag greening on empty parse) closed 2026-08-18 — shipped-sidecar basis + `nocode` verdicts, live-tested |
| RC-F | **SHIPPED end-to-end** | `foxtag fields` → `check_register_fit.py` (`register_fit/1`, ADVISORY-never-gate, H14 both-costs) → the `<leader>dR` card (render-only — the linchpin held) |

**The catalog (definitions as named 2026-07-06 — historical record, kept because the RC names are cited tree-wide):**
- **RC-A (spine):** header/template TUs emit nothing → 0 instr / no record layout /
  clangd omits Size. `ctx.is_template` populated but never read. Fix = inject a concrete
  instantiation anchor. Resurrects ~7 features at once.
- **RC-B (systemic):** compile DB is GUI-only + stale (14 `.cpp`, 0 headers) → thin
  fallback flags → 11% of headers fail standalone. Regenerate full + smarter header→TU pick.
- **RC-C:** SIMD detector matches only AVX (`ymm/zmm`); engine is scalar-`xmm` → always
  false. Report the real width-class; SWAR needs source-level detection (open decision).
- **RC-D:** `facts.derived` struct branch never computes size (delegated to cache-gate);
  asmdiff/sizeprobe hardcode clang while engine ships g++. Wire recordlayout; g++ for codegen.
- **RC-E (safety):** branchtag paints `✓ branchless` on 0-instruction headers — a *false*
  all-clear on a branchless-discipline engine. Guard the empty-parse case; never green on nothing.
- **RC-D′ (per-function cache-line access density — operator-flagged 2026-07-18):** the
  *"distinct 64B lines per function"* overlay shows an identical `L0…L10 (11)` for every function
  under a struct, where 11 = the *enclosing struct's* line span (NotifyEvent 656 B → 11) — i.e. the
  per-FUNCTION density isn't computed; the render falls back to the struct's line count (a
  placeholder, "nothing real shown"). RC-D-family (`facts.derived` doesn't emit a per-function
  access-density axis) OR a render fallback — undiagnosed. Deferred to the plugin session (E.1.2.A
  plan § KNOWN PLUGIN DISPLAY GAP; the FUNCTION analogue of the per-struct layout the C4 probe-TU
  materializes — fix alongside).
- **RC-F (per-FIELD facts + register-fit / access-cost axis — operator-envisioned 2026-07-18, grounded in `Learning_cpp/projects/deep_dives`; the axis SURFACES the existing `data-disciplines/function-struct-alignment-for-single-mov-access.md` discipline + rides the `framework-patterns/isolated-per-struct-layout-probe.md` producer):** two linked capabilities. **(a) Per-field slice on a field's card** — opening a card for one field (`cached_seq`) shows THAT field's own size / offset / which 64B line(s) it occupies + its straddle, NOT the enclosing struct's aggregate (the same bug shape as RC-D′; the producer already has the per-field offsets — the struct card renders `@0 @4 @8 @16 @144`). **(b) Access-cost / register-fit DERIVED axis** — classify each field: a naturally-aligned scalar of register width (1/2/4/8 B GPR · 16/32/64 B XMM/YMM/ZMM, `offset mod size == 0`) loads/stores in a SINGLE aligned `mov`; a bit-packed sub-byte field (`MBS_*`/`BITMAP_*` shift+mask) or a misaligned one needs an extract (shift + and) — the "40-instructions → 1 `mov`" the operator demonstrated (de Bruijn `×0x01010101` single-`imul` packing; the `(~A & B) == B` branchless gate). **The equation:** single-mov ⟺ `size ∈ {1,2,4,8,16,32,64}` ∧ `offset mod size == 0`. The tool flags shift-mask fields + computes the register-aligned reconfiguration that would make access single-mov. **Honest tension (H14 / `latency-vs-cache-decision-framework.md`):** the engine bit-packs DELIBERATELY for cache footprint / L1 residency — single-mov alignment TRADES bytes for access-instructions, so the axis SHOWS BOTH costs (access-ops AND byte/cache-line footprint) per field; the operator decides, the tool NEVER blindly unpacks. A genuinely new compiled-reality axis — "is this field a single `mov`, and what layout would make it one" surfaced at edit-time (the H6/H7/H14 disciplines made visible where you edit). Homed as a task; the per-field-slice half (a) subsumes RC-D′ / Task #10.

## 6. Layer 3 — The plugin (the nvim surface → a NON-CLI application of the whole toolchain, D-372)

**Scope [D-372, 2026-07-19 — the V1 completion mark, EXPANDED]:** the plugin is no longer merely a
render/navigate surface — it is a **NON-CLI APPLICATION of the WHOLE toolchain**. Everything you would do via
`foxtag <cmd>` or the `check_*` scripts is available editor-native + keyboard-first: browse units · query
facts · **invoke the producers to REFRESH DERIVED in place** (not only render pre-computed facts) · navigate
refs · surface gate results. The Target-UX below is the render/navigate portion of that fuller application;
**V1 completion now REQUIRES this app-level scope**, not only the render surface. This is the custom-IDE
endgame (§8.5 / §8.6 / D-330) made the PRIMARY plugin goal — and it is what makes the toolchain *felt*
("matters"). Full scope + sequencing (plugin-first) + open questions → §8.6 + decision log **D-372**.

**Target UX (the render/navigate portion of the app above):**
- **Cursor-tracking by enclosing unit** — resolve the unit from the outer↔`[END_X]` block,
  so the HUD/panel/derived work anywhere inside a unit, not only on the symbol name.
  *(Most current HUD/panel functionality reworks around this.)*
- **HUD vs PANEL — two roles, NOT 1:1** (correction): **HUD** = transient, single-card, AUTO-FOLLOWS the
  cursor (a quick check / nav lens). **PANEL** = persistent, MULTI-card board, EXPLICIT-add — `<leader>d[X]`
  opens it empty; `<leader>dD` **ADDS** the current unit's card (does NOT auto-rotate/replace), so you keep
  another struct/function on-screen while working on something else; the dual-panel compare is this
  generalized to N cards. `l`/Enter = jump to file; **`L` = open the unit in the panel beside you.** Both
  resolve the unit via cursor-tracking between `[TYPE]`↔`[END_TYPE]`. The current auto-rotate-and-close-on-
  reuse is a design bug against this model — the panel must **accumulate, not replace.**
- **Collapsed by default** — trees/impact views open folded.
- **Context-gated actions** — the menu/hotkeys show **only what's valid** for the current
  unit + resolvability (no "can't do that here" spam on templates). This is D-328 realized.
- **Persistent output / popout** — a formatted, keybound output pane (à la `:Noice`),
  and the **pop-out doc-viewer** (`[REFERENCE]` → float the doc beside the code).
- **Facts in the HUD** — branchless verdict + derived facts surfaced in the HUD/panel
  (only once trustworthy — RC-A + RC-E first, so it never surfaces a false-green).
- **Tag-enriched + tag-filterable dependency trees** — every `file:line` in the HUD's consumer /
  embedder / blast-radius / enforcement-site trees resolves to its ENCLOSING unit (the same resolver as
  cursor-tracking) and shows `[TYPE Name]` + the unit's `[TAG]` list (optionally its `[DERIVED]` facts +
  `[OVERVIEW]` one-liner). Turns "referenced at `PortfolioController.hpp:507`" into
  `PortfolioController_Init [FUNCTION][ENGINE][SLOW_PATH]`. Then the trees become **filterable/groupable by
  tag** — "only the `SLOW_PATH` consumers," "which `HOT` structs embed this," "every `WIRE_FORMAT`
  enforcement site" (directly useful for grouping the 51-site byte-layout blast-radius). Each entry gets a
  "compare with →" hook into the dual-panel view. Another consumer of the tag substrate; degrades to
  clangd symbol-names (+ enclosing-unit resolution for bare/raw-line entries) until units are tagged.
- **Responsive layout + dual-panel COMPARE view** — fill available space (4K/portrait
  leaves the single panel mostly empty). When there's room, show TWO units side-by-side
  (or stacked): a struct + its mutator function · a core struct + a consumer · two
  cross-thread structs. The value is the **connective tissue between them** — shared
  call-graph edges, layout blast-radius (change a core field → which consumer offsets
  shift), false-sharing/cache interaction. NEW PRESENTATION, not new analysis (the HUD
  already computes Consumers / blast-radius / callers / Written-by). Driven HUD-style:
  pick the 2nd from unit A's own lists ("compare with →"), never typed. Narrow window →
  single panel. Serves H6 (false-sharing / read-write) + H22 (blast-radius) directly.
- **Consolidation over accumulation — fox-symdeps SUBSUMES a nav-plugin cluster** (for the tagged codebase).
  Once the card-board + graph-browser land, they replace (for engine code): **harpoon** (mark/jump →
  card-board), **aerial** (symbol outline → `[CONTAINS]`/`[SECTION]` TOC), **dropbar** (breadcrumb →
  enclosing-unit chip), **treesitter-context** (sticky header → `[TYPE]` tracking), **todo-comments**
  (unused — deferrals are prose → the `[DEFERRED]` tag). fox-symdeps becomes THE nav layer, not one-of-72.
  **Keybind-SAFETY:** `<leader>dd` collides with vim delete-line (accidental deletes) → move nav/action keys
  off `d`-prefix collisions.
- **Per-`[TYPE]` card facets** (the card is polymorphic, D-334): FUNCTION → calls / called-by / call-trace /
  branchless-simd-instr; STRUCT → layout / size / embedders / blast-radius; **REGISTRY/X-macro → SPECIAL**
  (the `[ROW]`/`[COLUMN]` sub-schema — the biggest format gap; a registry card shows rows / columns /
  enrollment, not a flat symbol view).
- **Better module grouping** — organize the ~40 modules by concern (producers / overlays /
  UI / adapters).

**State (re-grounded 2026-08-19 — the bullets above are the SPEC; most are BUILT):** the 0.4
tag-native wave + parity fleet + 0.5 asm arc (2026-08-09..16) + the 2026-08-18/19 sessions
landed cursor-tracking, the three-surface HUD/follow/board model, collapsed-by-default,
context-gated actions + menu-as-root, output log + doc-viewer(+pin), tag-enriched/filterable
trees, compare v1, browse-first fuzzy pickers, the shipped-asm card family, the branch-taxonomy
overlay, and the **graph-walk** (drill `f` / trail-back `<C-t>` / open-beside `L`). The overlay-
audit findings (branchtag false-green · diagnostics 2-step · ambient template-silence + flicker)
are ALL closed. **Still open here:** the REGISTRY `[ROW]`/`[COLUMN]` card facet (render side) ·
compare CONNECTIVE TISSUE (the §-stated value of the pair view) · module grouping · per-entry
"compare with →" hooks. **Operator redefinitions that bind future work:** auto-follow lives in
the FOLLOW CARD (float stays point-at); "fill available space" = MORE PANES, never wider
(readability caps stay); d-prefix keybind move PARKED by operator; layer-stack + menu-as-root
laws apply to every new surface.

## 7. Layer 4 — Process

- **Dogfood corpus, not live capital code.** A small set of **real** units copied into a
  fixture covering every shape (rich file-header · include/constexpr block · helper-decls ·
  big templated struct w/ sub-group headers · within-fn sections · a registry). Iterate the
  format there until *provably lossless* → it becomes the golden fixture the CI checks →
  *then* convert real code. (Extends the P1 golden-fixture task.)
- **Conversion is comments-only + byte-identical** (comment-stripped diff must be empty).
  Never touches capital code.

## 7.5 · Tool inventory — the cohesive system (✅ exists / 🟡 half-functional / ⬜ missing)

The IDE = the tag substrate + FOUR tool roles over it (AUTHOR / SEE / NAVIGATE / VERIFY) + an emerging fifth.
Every ⬜ is a *view over the one tagged graph*, NOT separate machinery — which is why it's finishable.

**AUTHOR (write + maintain the tags):** schema validator ✅ · cache-layout gate ✅ (+ `--fix` writer,
in-editor menu row) · scaffold generator 🟡 (golden fixture done, generator pending — ideas §4's
substrate) · derived-write ✅ (`:FoxSymdepsDerived!` writes the stable call-graph facts; layout
quartet is the cache-gate's by the T6 authorship split — "no struct size" was re-scoped as the
DESIGN, not a gap) · whole-codebase batch ✅ as `update_toolchain.py` (D-374/D-418; the
`:FoxTagUpdate` one-command shape was OVERTURNED by write-vs-verify) · **the complete schema** ✅
LOCKED `[SCHEMA]_[v1.0]` (all format decisions resolved) · TAG ADD ✅ (vocab-derived merge).

**SEE (compiled reality):** HUD ✅ · follow card ✅ · board ✅ · byte-map ✅ · compiled-reality probes ✅
(sidecar-basis + `template_args`; RC-A superseded) · overlays ✅ (trust-fixed; branch taxonomy
▲/△/✓/feeder, shipped basis) · shipped-asm card family ✅ · register-fit card ✅ · **the unit CARD**
🟡 (one renderer reused across float/board/follow/compare, kind-dispatched — but polymorphic over
treesitter kind, not the full `[TYPE]` set; REGISTRY/FILE render generic).

**NAVIGATE (browse the tag graph):** clangd relationships ✅ · action menu ✅ (context-gated,
write-tiers, keys derived, menu-as-root) · tag-enriched + filterable trees ✅ (`/` + `T`) ·
**graph-browser** ✅ (drill `f` re-roots on any tree entry + breadcrumb + `<C-t>` trail; landed
2026-08-19) · dual-panel compare ✅ v1 (**connective tissue still owed** — the §6-stated value) ·
doc-viewer ✅ (`[REFERENCE]` float + pin) · browse-first pickers ✅ (structs / by-[TAG] / roam /
vocab) · **tag-query** ⬜ ("all `SLOW_PATH` fns > 500 instr" — browse/filter landed; the
fact-predicate composer didn't).

**VERIFY (CI keeps it honest):** cache-layout gate ✅ (HARD strict-new, both TUs) · grammar/schema
CI ✅ · drift-gate ✅-in-substance PER-AXIS (layout HARD · call-graph A2 ADVISORY, declared-PARTIAL
until the v1 generator · codegen shipping-basis via Check N + sidecars; never unified as ONE gate
— deliberate) · the code-tag index ✅ (+ index-currency HARD) · plugin live-path tests ✅ (the
2026-08-18 rule: every subprocess/async/window seam ships a `test_*_live` member).

**FIFTH ROLE — views the graph makes possible:** `[REFERENCE]` resolver ✅ (= the doc-viewer) ·
registry/row browser ⬜ (blocked on the `[ROW]`/`[COLUMN]` card render; grammar landed) ·
orphan/dead-unit detector ⬜ · version-timeline per unit ⬜ · `[SEAM]`/parity view ⬜ ·
`[DEFERRED]` work-queue **MOOT TODAY** (measured 2026-08-18: zero in-code `[DEFERRED]` across
all 8 source roots — re-arm at the first written tag).

**The card is the NAVIGATOR's renderer; the tags are the substrate all five roles read.** Build the substrate
+ the card + the graph-walk once, and the ⬜ tools become *configurations* of them, not new engines.

## 8. The gap-to-current + the phased path

We are at (re-grounded **2026-08-19**; the 2026-07-15 paragraph this replaces lives in git):
format LOCKED `[SCHEMA]_[v1.0]` (D-346) · corpus CONVERTED 100% (P6, 2026-07-18) · the
`0.2` contract+gate layer COMPLETE (D-418: `TOOLCHAIN_CONTRACTS.md` + `update_toolchain.py` +
the import-from-core lint + cite-repair) · the D-413/D-414/D-415 derived-facts-integrity arc
CLOSED all four leaves, and D-415 **PARKED the foxtag core** (frozen-kept, parity gate off,
script-side authority for layout/inventory; re-arms at the v1 conversion program) · the
plugin's V1 cycle CLOSED 2026-08-14 at feature-complete `0.5` (the 0.4 tag-native wave, the
parity fleet, the shipped-asm card family, regfit) · post-close sessions (2026-08-18/19)
landed the branch-taxonomy overlay on the SHIPPED basis, browse-first pickers, the graph-walk,
and the live-path test rule. **The old "remaining increment 2c" sentence is DEAD on all three
legs:** the STRUCT writer landed Python-side (`check_cache_layout --fix`), RC-B closed via
TD-257's shipping-db + sidecars, and the drift-gate landed per-axis (§7.5 VERIFY) — P6 never
waited for any of them. What actually remains: the v1 foxtag call-graph GENERATOR (the A2
missing-consumer half) · the `0.6` AST producers (TD-256, now UNBLOCKED) · `0.7` pre-push gate ·
`0.8` planes/self-hosting · the registry card + tissue + tag-query on the plugin side (§7.5).

**Phased path (each phase gates the next):**
1. Complete the **schema** against the survey's input-space taxonomy.
2. Stand up the **dogfood corpus**; prove the format lossless on it.
3. Fix the **toolchain** (RC-A…E) + build `:FoxTagUpdate` + generalize the drift-gate.
4. **Rework the plugin** UX (cursor-track / drawer / collapsed / context-gate / popout) — **scope-increased (D-372) to the plugin as a NON-CLI application of the whole toolchain** (§6 / §8.6); now the plugin-FIRST priority in the sequencing. *(V1 cycle DONE 2026-08-14 at feature-complete `0.5`; post-close sessions continue additively.)*
5. **Convert** the codebase (mechanical, byte-identical) — *only now* is it truly mechanical. *(DONE 2026-07-18 — corpus 100% green; the phased path above predates the D-372 V1 redefinition, which §8.6 governs.)*

## 8.5 · Planes are first-class + the toolchain self-hosts (D-367, 2026-07-18)

A late-breaking design commitment that reshapes the substrate: the `[TAG]` plane values
(`[ENGINE]`/`[DATA_PLANE]`/`[MONITORING_PLANE]`/`[DEV_PLANE]`) become a **first-class,
discipline-GATING axis** — each plane a distinct constraint profile (engine = H1–H22 + latency;
toolchain/dev-plane = functionality-not-latency; monitoring = engine-like-minus-hot-path) — via a
**`FOREACH_PLANE` registry** (`{constraints · valid [TAG] vocab · [DERIVED] axis-set}`, path-derived
value, structural gating). The **skeleton stays universal**; the **vocabulary is plane-scoped** — and the
`[DERIVED]` axes are a *different kind* per plane (engine = compiled-reality size/straddle/asm; toolchain =
pipeline-reality grammar-fences/parity/call-graph). This is what lets **the toolchain self-host in its own
system** (a **multi-comment-syntax parser** — `//`/`#`/`--` — is the V1 enabler; foxtag C++ is free). The
toolchain earns ENGINE-grade rigor precisely because it's one-producer-N-consumers — a wrong fact fans out
to every consumer. → `doc-intelligence-toolchain-architecture.md` § plane-first-class; decision log D-367.

## 8.6 · V1 = the whole toolchain, live on every surface (D-372, 2026-07-19)

The felt gap that redefines V1: the tooling + docs EXIST but "feel like none of it matters" — because
consumption is uneven (strong in CI, thin in the plugin, V1 pending). So V1 is no longer just "schema +
producers + render + conversion" — it is the toolchain **pervasively consumed from ONE core**, live on the
surface that fits each capability:

- **One core, no reinvention** — `tools/foxtag/` + `check_doc_metadata` ARE the core; every CLI tool /
  plugin / CI consumer PULLS from it, none rolls its own. The 2026-07-19 `check_meta_registry.py` straggler
  (rolled its own `Path(__file__)` root → false `exit 2`) is the anti-pattern; enforce with an
  import-from-core lint. A `tools/core/` reorg is optional — the substance is the D-349 migration + the
  discipline, not the directory name.
- **CLI** — every producer/query standalone (`foxtag <cmd>` + the `check_*` scripts). ~done.
- **Local CI (NO GitHub dependency)** — pre-commit + session-close + a NEW **pre-push** heavier gate; keeps
  the in-code `[SCHEMA]` docs SYNCED-WITH-CODE automatically (DERIVED auto-refresh + completeness/version
  gating). The operator's "a CI script that doesn't require pushes to github." ~done at commit/close;
  pre-push is the clean add.
- **Plugin = a NON-CLI application of the WHOLE toolchain** *(scope increase)* — the editor-native front-end
  (browse units / query facts / refresh DERIVED / navigate refs / surface gate-results, keyboard-native) =
  the custom-IDE endgame (§8.5, D-330) promoted to the PRIMARY plugin goal. This is what makes the toolchain
  *felt* — used IN the editor, not only via CLI/CI.
- **Sequencing: plugin-first** — land plugin V1 consuming the EXISTING producers before building more
  north-star producers (#12–14), so it pays off fast (`feedback_framework_layer_payoff_diminishing_returns`).
  Re-prioritizes #7/#8/#10 (plugin lane) AHEAD of #12–14.

Proposed surface split (operator UNSURE — open): PRODUCERS (`layout`/`units`/`fields`/register-fit) →
plugin + CLI; GATES (schema-version / meta-registry / completeness) → CI/commit/push, not the plugin. Full
decision + all open questions (the split, the `tools/core/` rename, the pre-push scope, the plugin
feature-set, the lint) → decision log **D-372**.

## 9. Non-goals / boundaries

- **Not** a substitute for the engine/edge work — this is the toolchain we build *in*.
- **Not** public — private dev-apparatus (ships later as a separate workspace-template).
- **Does not touch capital code** — comments-only, byte-identical, always.
- **Not** frozen — this is a living target; refine as the survey + dogfooding teach us.

## 10. Open decisions (dispositions re-grounded 2026-08-19)

- **D-SWAR** → **DECIDED**: `[BIT_PACKED]_[SWAR]` sub-tag, auto-detect direction (schema lock).
  Open remainder = building the idiom DETECTOR (small-medium, unscheduled).
- **Complete `[DERIVED]` set per unit type** → **DECIDED** spec-side (D-339 axes table);
  enforcement remainder lives at TECH_DEBT-243/-236, per-axis by design.
- **`:FoxTagUpdate` naming + surface** → **SUPERSEDED** — the "one command, both interactive +
  CI (likely yes)" was overturned by D-374's write-vs-verify law: batch = `update_toolchain.py`
  (human-invoked, hooks forbidden), interactive = `:FoxSymdepsDerived!` + per-card `r`-refresh +
  the `--fix` menu row. Nothing needs the old name.
- **Doc home for the tag-system docs** → the only genuinely-open row, and cosmetic: co-location
  under `doc-disciplines/` won by inertia (no `tag-system/` subdir exists). Decide-or-close at
  the next doc-system sweep.
