---
type: north-star
status: draft-v0.1
established: 2026-07-06
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
the IDE** — self-documenting, self-verifying, navigable. A format designed **once**, so it
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
   (:FoxTagUpdate) (edits + displays)
```

**The linchpin:** all consumers read the **one** producer + the **one** tag substrate.
Complete the producer once, correctly → CI gate + plugin + doc-viewer inherit it
simultaneously. Integration is *structural* (guaranteed by the single core), not
maintained by hand-aligning copies. This is the anti-Class-18 discipline paying off.

## 4. Layer 1 — The format (the substrate)

**Target:** capture **every** comment/documentation shape in the codebase **losslessly**.
Code-local comments STAY verbatim in `[CODE]` (D-326); only unit-level WHY relocates to
`[COMMENT]`. Reformatting must never *compress away* detail (the EngineCommon-file lesson).

**Current (schema v1):** unit blocks · `[TAG]/[SCOPE]/[SCHEMA]/[OVERVIEW]/[DIAGRAM]` ·
`[CODE]…[END_CODE]` · `[COMMENT]` · `[SUPPORTING_DOCS]` · `[DERIVED]` · `[SECTION]`
within-fn markers (`----` bars).

**Known gaps (→ schema completion; the survey will make this exhaustive):**
- No tag for **annotated include blocks** (each `#include` + what-it-provides + phased notes).
- No tag for **constexpr/const rationale** or **downstream-dep declarations**.
- No **helper-declarations** section within a function region.
- File-header **multi-section discipline blocks** (PURPOSE / LIFECYCLE / DISCIPLINE /
  exemption rationale) have no structured home — only the flat `[COMMENT]`.
- The **complete per-type `[DERIVED]` set** is unspecified + unenforced (a struct should
  autopopulate SIZE·ALIGN·CACHE_LINES·STRADDLE·UPSTREAM·CONSUMERS·BLAST_RADIUS — today even
  the "good" cases emit a partial slice).
- `[SWAR]` axis — **OPEN DECISION** (source-idiom detection vs manual tag).

> **Format input-space taxonomy: PENDING the comment-shape survey** (3 agents, 2026-07-06).
> This section becomes exhaustive when it lands. Do NOT freeze the schema before then —
> *don't generalize the substrate before its input space is known.*

## 5. Layer 2 — The toolchain (fact-producer + CI)

**Target:** a **complete**, template-aware fact-producer emitting every axis per unit
type; one command — **`:FoxTagUpdate`** — that autopopulates the full `[DERIVED]` block for
one unit interactively AND every file at CI; a **generalized drift-gate** (the cache-gate
D-320 extended from layout to all written axes: layout always, call-graph always, codegen
pinned to `[BUILD]`/`[INSTANTIATION]` per D-327).

**Current gaps (from the 2026-07-06 asm + overlay audits — RC-A…E):**
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
- **RC-F (per-FIELD facts + register-fit / access-cost axis — operator-envisioned 2026-07-18, grounded in `Learning_cpp/projects/deep_dives`):** two linked capabilities. **(a) Per-field slice on a field's card** — opening a card for one field (`cached_seq`) shows THAT field's own size / offset / which 64B line(s) it occupies + its straddle, NOT the enclosing struct's aggregate (the same bug shape as RC-D′; the producer already has the per-field offsets — the struct card renders `@0 @4 @8 @16 @144`). **(b) Access-cost / register-fit DERIVED axis** — classify each field: a naturally-aligned scalar of register width (1/2/4/8 B GPR · 16/32/64 B XMM/YMM/ZMM, `offset mod size == 0`) loads/stores in a SINGLE aligned `mov`; a bit-packed sub-byte field (`MBS_*`/`BITMAP_*` shift+mask) or a misaligned one needs an extract (shift + and) — the "40-instructions → 1 `mov`" the operator demonstrated (de Bruijn `×0x01010101` single-`imul` packing; the `(~A & B) == B` branchless gate). **The equation:** single-mov ⟺ `size ∈ {1,2,4,8,16,32,64}` ∧ `offset mod size == 0`. The tool flags shift-mask fields + computes the register-aligned reconfiguration that would make access single-mov. **Honest tension (H14 / `latency-vs-cache-decision-framework.md`):** the engine bit-packs DELIBERATELY for cache footprint / L1 residency — single-mov alignment TRADES bytes for access-instructions, so the axis SHOWS BOTH costs (access-ops AND byte/cache-line footprint) per field; the operator decides, the tool NEVER blindly unpacks. A genuinely new compiled-reality axis — "is this field a single `mov`, and what layout would make it one" surfaced at edit-time (the H6/H7/H14 disciplines made visible where you edit). Homed as a task; the per-field-slice half (a) subsumes RC-D′ / Task #10.

## 6. Layer 3 — The plugin (the nvim surface)

**Target UX:**
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

**Current gaps:** the overlay-audit findings (branchtag false-green, diagnostics 2-step,
ambient/status blank-on-templates + flicker) + all the UX targets above are unbuilt.

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

**AUTHOR (write + maintain the tags):** schema validator ✅ · cache-layout gate ✅ · scaffold generator 🟡
(golden fixture done, generator pending) · derived-write `:FoxSymdepsDerived` 🟡 (no struct size, partial
DERIVED) · **`:FoxTagUpdate`** (whole-codebase autopopulate + fix) ⬜ · **the complete schema** ⬜ (blocked on the 7 decisions).

**SEE (compiled reality):** HUD ✅ · panel ✅ · byte-map ✅ · compiled-reality probes (asm/size/branches/simd)
🟡 (RC-A templates break them) · overlays (branchtag/lens/ambient/status) 🟡 (false-green, blank-on-template) ·
**the unit CARD** (universal collapsed/expanded renderer, polymorphic over `[TYPE]`) ⬜.

**NAVIGATE (browse the tag graph):** clangd relationships (callers/callees/consumers/blast-radius) ✅ · action
menu 🟡 (all-hotkeys-shown, m/M conflict) · **tag-enriched + filterable trees** ⬜ · **graph-browser** (re-root
on edge-follow + back/forward history) ⬜ · **dual-panel compare** ⬜ · **doc-viewer** (`[REFERENCE]` float) ⬜ ·
**tag-query** ("all `SLOW_PATH` fns > 500 instr"; "every `WIRE_FORMAT` struct > 128B") ⬜.

**VERIFY (CI keeps it honest):** cache-layout gate ✅ · grammar/schema CI ✅ · **generalized drift-gate**
(all axes: layout + call-graph + codegen-pinned) ⬜ · **the code-tag index** (#14 unified fact-grammar) ⬜.

**FIFTH ROLE — tools the graph makes possible but we haven't built (the "missing" you sense):** registry/row
browser (the registries are a huge chunk) · orphan/dead-unit detector (units with zero consumers) ·
version-timeline per unit (the 899× inline version-tags → a history view) · `[SEAM]`/parity view (train↔serve
seams) · `[DEFERRED]` work-queue (prose deferrals → a tracked backlog) · `[REFERENCE]` resolver (jump to
PARITY / finding / spec / `[[memory]]`).

**The card is the NAVIGATOR's renderer; the tags are the substrate all five roles read.** Build the substrate
+ the card + the graph-walk once, and the ⬜ tools become *configurations* of them, not new engines.

## 8. The gap-to-current + the phased path

We are at (updated 2026-07-15, D-348): format LOCKED `[SCHEMA]_[v1.0]` (D-346); propagation
landed — validator caught up to the locked contract + per-type template corpus
(`DOCS/CODE_TAG_TEMPLATES.hpp`) + code-tag index + skills/CLAUDE.md alignment (D-347);
dogfood corpus LANDED + PROVEN LOSSLESS — 4 real units (rich file-header / hot struct /
registry slice / wire parser) converted in `tests/schema_golden/`, mechanical
comment-stripped code diff clean (D-348). Phase 4 OPENED: the D-337 central core
increment 1 LANDED — `tools/foxtag/` C++ parser + scanner + query engine, PARITY-PROVEN
byte-identical to the Python validator on the full tree (the migration gate
`foxtag/parity_check.sh`; ~19ms vs ~147ms); the `foxtag unit <file> <line>` JSON query
fills the plugin's `tagadapter.parse` keystone via subprocess (D-349). Increment 2a LANDED:
`foxtag layout` — the LAYOUT fact-producer consolidated into the core, parity-proven
straddler-exact vs `emit_record_layout.lua` on the 204-record census (D-350; the cache-gate's
headless-nvim dependency becomes swappable behind the gate). Increment 2b LANDED: `foxtag
codegen` — the g++ probe producer with **RC-A (instantiation anchor) / RC-C (real SIMD
width-class incl. scalar-xmm) / RC-E (never-green-on-vacuous) built in**, EXACT-match vs the
conformance analyzer's ratchet baseline on real kernels (Regime_Classify 489 instr / 8
data-dep; D-351). Tool docs: `tools/foxtag/README.md`. Remaining increment 2c = `foxtag
update` (the D-327 STRUCT writer) + the RC-B compile-DB story + the generalized drift-gate —
then the P6 CONVERSION's hard toolchain dependencies are met. Plugin major-features work,
overlays/asm half-broken (phase 5, operator's session).

**Phased path (each phase gates the next):**
1. Complete the **schema** against the survey's input-space taxonomy.
2. Stand up the **dogfood corpus**; prove the format lossless on it.
3. Fix the **toolchain** (RC-A…E) + build `:FoxTagUpdate` + generalize the drift-gate.
4. **Rework the plugin** UX (cursor-track / drawer / collapsed / context-gate / popout).
5. **Convert** the codebase (mechanical, byte-identical) — *only now* is it truly mechanical.

## 9. Non-goals / boundaries

- **Not** a substitute for the engine/edge work — this is the toolchain we build *in*.
- **Not** public — private dev-apparatus (ships later as a separate workspace-template).
- **Does not touch capital code** — comments-only, byte-identical, always.
- **Not** frozen — this is a living target; refine as the survey + dogfooding teach us.

## 10. Open decisions (resolve before the phase that needs them)

- **D-SWAR:** `[SWAR]` representation — auto-detect mask idioms (`-(uint64_t)mask`,
  `BITMAP_*`/`MBS_*`, word-level mask-select) from source, or a manual tag? *(gates RC-C.)*
- **Complete `[DERIVED]` set per unit type** — the exact axis list for struct / function /
  registry / file. *(gates the fact-producer completion.)*
- **`:FoxTagUpdate` naming + surface** — one command, both interactive + CI? *(likely yes.)*
- **Doc home for the growing tag-system docs** — co-locate under `doc-disciplines/` or a
  new `tag-system/` DESIGN_SPECS subdir?
