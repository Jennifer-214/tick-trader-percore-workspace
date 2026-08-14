# Operator ideas — 2026-08-07 (partial transmission; more pending)

**Context:** Caramel, resuming after the (f) close: *"i had alot more ideas and stuff but i cant
really send them to you at the moment, like look up tables for certain calacs, piping compile
comands for the asm viewer to terminal, so we cna make use of custom compuler work eventually,
etc."* Two ideas transmitted, more explicitly pending. Captured as given, idea-stage — NOT scoped
work; each dives at its named increment. This file is the landing pad; append later transmissions
as dated sections.

---

## 1. Lookup tables for certain calcs (ENGINE plane)

- **As given:** "look up tables for certain calacs".
- **Reading:** branchless LUT substitution for selected hot/slow-path computations. Candidate
  surfaces when it dives: the FPN transcendental family (the TECH_DEBT-242 pre-Ship-A `.w[]`/`.sign`
  op-family residue is already slated for rework — a LUT-backed rebuild could be that rework),
  ConfidenceScore / regime math, any polynomial-or-iterative kernel that dominates a budget.
- **Why it fits the house style:** a LUT is branchless by construction (H7/H20) and bit-exact —
  same input word → same output word, which is *stronger* determinism than re-deriving through an
  iterative kernel (H4/H11-compatible). The binding constraint is **L1d working-set** (CLAUDE.md
  cache-aware discipline): table sizing + whether interpolation (none vs fixed-point linear) keeps
  it cache-resident is the real design axis, not the arithmetic.
- **Where it homes:** ENGINE plane — behind the toolchain gate per the operator's own 2026-07-20
  directive (toolchain + plugin + docs + CI gate engine development). Per
  `feedback_future_headache_vs_optimization_scope_framework`: pure-performance → tracked, not
  actioned now. Dive vehicle: the resumed engine optimization arc (post-`E.1.2` SoA work).
- Deliberately NOT a TECH_DEBT entry — no defect exists; it is an optimization idea. Lives here
  until its dive.

## 2. Pipe the asm-viewer's compile commands to the terminal (TOOLCHAIN plane, `0.5`)

- **As given:** "piping compile comands for the asm viewer to terminal, so we cna make use of
  custom compuler work eventually".
- **Reading:** the `0.5` asm/layout/register-fit cards must resolve probe flags from the build's
  `compile_commands.json` (the TECH_DEBT-257 PRECONDITION, severity HIGH). This idea rides that
  precondition: **EMIT the exact resolved invocation as a runnable artifact** — terminal-pasteable /
  subprocess-spec — so the identical command the viewer compiled with is reproducible OUTSIDE the
  plugin. That is the substrate for "custom compiler work eventually": alternate flags, passes, or
  toolchains consume the same command set instead of minting a second flag source that diverges.
- **Why it is the natural rider on TD-257 and not a separate thing:** both stand on the D-397
  fact-source argument — *if the asm side-by-side disagrees with the actually-compiled binary, the
  FACT SOURCE is wrong and every surface above inherits it*. One real command source, N consumers
  (viewer card · terminal · future custom-compiler harness) is the same one-core-N-consumers thesis
  (D-337) applied to compiler invocations.
- **Sister-links:** TECH_DEBT-257 (the 1:1 precondition) · D-397 (static-analysis arc placements;
  custom LSP parked at `1.x`) · TECH_DEBT-256 (AST fact-producers — same real-command dependency) ·
  the toolio envelope (an obvious carrier for a `compile_command` payload kind IF it earns it at the
  dive — do not pre-commit the transport).
- **Dive:** `0.5`, alongside the precondition work. Cross-ref inserted at the plan body's `0.5`
  line the same day this file was written.
- **⏩ SUBSTRATE LANDED (2026-08-12, the 0.5 opener):** `tools/compile_command.py` — the ONE
  command source is real: `python3 tools/compile_command.py <file>` prints the pasteable
  `(cd <dir> && <exact command>)` per db entry (multi-target TUs emit ONE ROW PER ENTRY — the
  engine/engine_gui/suite flag sets never silently collapse); `--json` emits the NEW
  `compile_command/1` envelope the 0.5 cards will consume. Resolves the engine-root
  `compile_commands.json` symlink (today → `build_clangd/`); the SHIPPING-build db + the
  build.sh 1:1 asm sidecar remain THE next leaf (`--db` makes that cutover a flag). 7-teeth
  selftest on the floor. The terminal half of this idea is usable TODAY; the viewer-card half
  rides the 0.5 dive proper.
- **⏩ BUILD HALF LANDED (2026-08-13, engine `2654ad4`):** the "1:1 asm + binary output" ask is
  real — `./build.sh asm` objdumps the EXISTING binaries into `build*/asm/<binary>.asm`
  (provenance-stamped; no rebuild), and `CMAKE_EXPORT_COMPILE_COMMANDS=ON` gives every build
  dir its REAL db. Chosen mechanism = objdump-from-the-shipped-binary (this file's own
  "zero-divergence alternative"): the four main targets build `-flto`, so compiler `-S` asm is
  pre-link code nobody ships — the sketch's option (a) is structurally out. Bonus evidence:
  the shipping db carries `-DNDEBUG` the editor db lacks (live wrong-flags divergence, found
  on first contact). The `Notify_Send` empty-render's true mechanism: compiling a HEADER as a
  TU emits nothing for an uninstantiated inline fn — and the shipped binary shows ZERO
  standalone copies (inlined everywhere), which the 0.5 card should say BY NAME. Remaining =
  the viewer cutover (read the sidecar; honest inlined-away state; staleness refusal off the
  provenance header).
- **⏩ OPERATOR UPDATE (2026-08-10, dogfood screenshot — logged at session stop):** the asm viewer's
  `1:1 · this function` mode rendered empty (a bare `0`) on `Notify_Send` (`Notify.hpp`) — *"it will
  need work but thats part of piping the compile command to the terminal and using that to view."*
  Diagnosis-as-given: NOT a separate defect — it is THIS item's gap (the viewer compiles with
  editor-supplied flags today, so its fact source can't be trusted 1:1 and its failures are opaque).
  **NEW requirement folded in:** *"the build.sh script will probably need a 1:1 asm + binary output
  ideally"* — the build itself emits asm ALONGSIDE the binary (same invocation, same flags), so the
  viewer consumes the ACTUAL build's asm rather than re-compiling and hoping the commands match.
  That is the strongest form of the D-397 fact-source argument: viewer-asm ≡ shipped-binary **by
  construction**, not by parity-checking a second compile. Shape sketch for the `0.5` dive: a
  `build.sh` flag/target (e.g. `asm` or `-DEMIT_ASM=ON`) driving per-TU `-S`/`--save-temps` (or
  objdump-from-the-real-binary as the zero-divergence alternative) into a `build*/asm/` sidecar the
  viewer + terminal both read. Rides TD-257 (compile_commands 1:1) — same precondition, one command
  source, N consumers.

## 3. Auto-generated templates — strategies and beyond (generalizes `/strategy-template`)

- **As given:** "ideas for auto generating templates for strategies, and other things similar".
- **Canonical sister EXISTS:** the `/strategy-template` skill already scaffolds a strategy end-to-end
  (5 lifecycle stages + `FOREACH_STRATEGY` row + enum + dispatch + tests + GUI hook). The idea
  GENERALIZES it: the same declare-then-scaffold shape for the OTHER registry-backed cohorts —
  cfg-field cohorts, gates, panels, tools. The H15 meta-registry (`FOREACH_REGISTRY`) is the natural
  enumeration of "which cohorts can be templated"; candidates enumerate at dive, not here.
- **Boundary:** generation stays REGISTRY-driven (declare the row → the scaffold flows), never a
  parallel template store that drifts beside the registries (Class 21).

## 4. Declarative code-gen from PRE-assigned tags (struct/function generation; plugin-surfaced)

- **As given:** "struct and function generation based off of assigned tags that are set up before
  actual coding, like declarative code gen tools, for the plugin as well".
- **Reading — INVERT the tag system's direction.** Today: code → tag-blocks (`[STRUCT]`/`[FUNCTION]`
  + `[DERIVED]` axes) → validators/cards. The idea: author the TAG-BLOCK FIRST as a declarative spec
  (fields, hot/cold/cross-thread clustering, alignment, threading axes) and a tool GENERATES the
  conforming skeleton — `alignas` from the declared alignment, field ORDER from the declared access
  clusters (the DOD layout-by-access-pattern rule applied mechanically), `MBS_*`/`BITMAP_*` accessor
  scaffolds from declared packed state. Design-by-declaration: the code-plane completion of D-372's
  "the code becomes the IDE", and the tag-plane twin of the X-macro auto-flow (one row → N sites).
- **Why it is tractable HERE and nowhere else:** the pieces half-exist. `foxtag grammar --json` is a
  machine-readable declaration schema; `check_cache_layout --fix` already WRITES derived facts into
  blocks (the reverse-direction writer, half-built); `in-code-documentation-schema.md` is a LOCKED
  substrate (stable grammar to generate FROM); `/strategy-template` is the cohort-level cousin (§3).
- **Constraints binding at dive:** generated code lands under the SAME gates as handwritten
  (cache-layout, latency-path conformance, H14 no-bitfields, H6 alignas) — the generator CONSUMES
  the graders, never bypasses them; idempotent-writer discipline (Class 56); the compiler stays the
  totality oracle for code tokens (the cascade.py R1 lesson — no blind `--apply` over code).
- **PLACEMENT OPEN:** not on the current `0.x` roadmap. Candidates: a new increment after `0.6`
  (AST fact-producers give the parse fidelity codegen wants) or the `1.x` LSP arc. Operator places
  it at the next planning touch; a pointer sits at the plan body's `0.4` line.
- **⚠️ AMENDED 2026-08-09 (operator, recovering the original list — this was "the big thing"):**
  the generator is **DETERMINISTIC and tag/grammar-driven — explicitly NOT LLM-codegen** ("without
  using like AI codegen"). The declaration IS the spec; generation is a mechanical transform whose
  output stands under the gates like handwritten code. An AI assist is AT MOST an optional later
  layer "hooked into this locally" — and the operator already owns local-AI substrate
  (Linux_Theme's `libfox-intel.a` + the `fox-ai-*` binaries) if that layer ever earns a dive;
  building an inference engine is explicitly OUT ("thats alot to build"). Boundary: determinism-
  first keeps generated code reviewable and gate-verifiable; any AI layer PROPOSES declarations,
  never emits code past the graders.

## 5. Plane-partitioned index (STRATEGY / ENGINE / DOCUMENT / …)

- **As given:** "a seperate index for like STRATEGY/ENGINE/DOCUMENT etc or something".
- **Reading:** per-plane index VIEWS over the corpus (code units, docs, citable ids) keyed on the
  plane `[TAG]` values that already exist (`[ENGINE]`/`[DEV_PLANE]`/…) — browsable in the plugin,
  emitted as generated index files.
- **Sisters:** `0.8` `FOREACH_PLANE` (plane-first-class registry — this index is its FIRST CONSUMER;
  ~85% already spec'd at `doc-intelligence-toolchain-architecture.md` § plane-first-class) ·
  `rebuild_doc_indexes.py` (the generator family it joins — derive-and-compare, never hand-kept) ·
  `DOCS/CODE_TAG_INDEX.md` (existing generated index to EXTEND rather than sibling) · foxtag grammar
  (the plane vocab source).
- **BOUNDARY (recorded; must hold):** D-tool-385 REJECTED plane-in-the-IDENTIFIER — plane is
  METADATA; embedding it makes identity mutable (H21 hazard, ~21.5k live citations). An index/filter
  is the explicitly-blessed remainder ("a `plane:` frontmatter field is DECOUPLED … a filtering
  convenience"). **Index YES, identity NO.**
- **Dive:** `0.8` (the registry) + `0.4` (the plugin surface that consumes it).

## Pending

- 2026-08-07 second transmission added §3–§5 (template autogen · declarative tag-driven codegen · plane index).
- PROVENANCE (2026-08-09): §1–§10 are the operator's recovered original list, transmitted in
  fragments across 2026-08-07→09 — §4 declarative codegen was "the big thing", §3 the
  templating/scaffolding companion. This file is the durable copy.
- Operator has additional untransmitted ideas ("alot more"). Append here as they arrive — one dated
  section each, sister-linked at capture time (the create→capture gap is where compaction-loss
  lives; `feedback_document_as_you_go_over_catch_at_end`).

## 6. Toolchain → C++ core with Python bindings on top (directional; third transmission 2026-08-07)

- **As given:** "i wanna eventually move the toolchain to be entirely cpp written, once we have a
  solid foundation, or atleast the majority of it, and just using python bindings for the top level
  stuff".
- **Why the current architecture already points there:** `foxtag` is ALREADY the C++ half of the
  fact-producer pair, with `parity_check.sh` proving byte-parity against the Python oracles — so
  the migration path per producer is literally *flip which side is the oracle*: C++ becomes
  authoritative, Python shrinks to a binding/orchestration shim, the parity gate keeps both honest
  DURING the transition and then retires per surface. The one-resolver-N-consumers discipline
  (D-337/D-399) is what makes this tractable — each producer migrates BEHIND its stable contract
  (the toolio envelope / the JSON emissions), consumers never notice.
- **Sequencing hooks (all already recorded):** TECH_DEBT-256 (AST fact-producers at `0.6` —
  libclang work is naturally C++-side) · the custom LSP (`1.x` — C++ by necessity) · D-411 item 3
  (unit tests for fact-producers land FIRST — the safety net any rewrite needs) · idea §2
  (compile-command piping — same real-command substrate) · `run_toolchain_tests.sh` (D-411 item 2)
  as the migration's regression floor.
- **Gate ("once we have a solid foundation"):** post-`1.0.0` direction, not an `0.x` increment —
  the contract layer (a)/(d) IS the foundation it waits on. Nothing to build now; this section
  exists so the 0.x work keeps the seam clean (contracts stay language-neutral; no Python-only
  cleverness in interfaces that would block the flip).
- **⚠️ GATE REFINED 2026-08-09 — CONFIRMED, now D-412 (the decision log carries the binding form):** "the more we do this the more i wanna just make it
  mostly cpp… we could make generalized structs and pass them along… it may actually be better as
  this gets more complex… this is becoming like a feature complete custom IDE, that i may wana
  generalize to use always." **Recommendation: adopt C++-FIRST FOR NEW FACT-PRODUCERS immediately**
  — a new capability lands as a foxtag producer/subcommand (which is T1's existing text taken
  seriously), typed structs accrue inside the core from today, Python shims only where CI wiring
  needs them. **EXISTING Python tools migrate per-producer, opportunistically when touched, behind
  the parity gate with soak (T4/D-349 — the migration mechanism already designed), each surface
  gated on its D-411 unit-test net.** **BIG-BANG REJECTED** — the rewrite-without-the-net hole is
  exactly what the original "solid foundation" gate encoded, and marathon-shaped work violates the
  session model. Why the direction is RIGHT on merit: one typed core structurally CANNOT have the
  N-parsers-over-one-anchor disease ((f)/(g)'s whole pathology is a multi-parser artifact);
  "generalize to use always" wants a portable core, not 100 scripts wired to a workspace; the 1.x
  LSP is C++-by-necessity so every new Python producer is future migration surface. First test
  case: (g) step 5's resolver lift — evaluate C++-side landing at its dive.

## 7. Tools directory structure + portability (parting transmission, 2026-08-09)

- **As given:** "eventually well need to organize and update the tools to have a more defined
  directory structure maybe, unless this works, it coul intheory be portable, anyways time ot go".
- **Reading — two distinct threads:** (i) `tools/` is ~100 flat files; a defined structure
  (producers / gates / lib / goldens / plugins already exist as partial seams) may be owed as the
  count grows. (ii) PORTABILITY — the toolchain running from any clone/machine — is the deeper ask,
  and it is FURTHER ALONG than the flat layout suggests: `foxroots` is the ONE machine-portable
  root resolver (D-375; no `$HOME` hardcodes; the import-from-core lint holds the class closed),
  goldens are git-tracked-only for fresh-clone identity (D-396), and `bless.py`'s roster +
  `check_tools_inventory` enrollment make the tool SET itself enumerable.
- **The "unless this works" hedge is load-bearing:** flat-with-disciplines may simply be correct —
  the enrollment gate + `tools/lib/` (DATA) + `tools/goldens/` + `tools/foxtag/` + `tools/plugins/`
  already partition by KIND. A restructure is a mass file-move = a citation-rename event (~100 tool
  paths cited corpus-wide) — do NOT do it before (g)'s rename-resolver exists to absorb exactly that
  class of move, and fold it into the C++-core migration (§6) if that lands, so the tree moves ONCE.
- **Sisters:** TECH_DEBT-244 (tools/ de-sprawl — the tracked home for the structure half) ·
  `foxroots.py` / the import-from-core lint (the portability substrate) · D-396 (tracked-only
  goldens) · §6 (the C++-core migration this should ride with) · (g) rename-resolver (the
  precondition for any mass path move).
- **Dive:** with §6's migration planning, or at TECH_DEBT-244's trigger — whichever fires first.
  Nothing to build now; captured so the threads converge instead of colliding.

## 8. Chain-position labels (HEAD/TAIL/seq) as a [DERIVED] axis + a data-flow graph in nvim (2026-08-09)

- **As given:** "like in the DAG labeling stuff as HEAD and TAIL and like the sequence number in a
  chain may be nice for the TAG comments and stuff as well, or like a data flow graph, that is
  shown in nvim or something idk, just a thought".
- **Reading — two layers:** (i) a unit's POSITION IN A CHAIN as a derived tag axis —
  `[DERIVED]_[CHAIN]_[<chain-id> #<seq> HEAD|MID|TAIL]` — for the engine's literal pipelines
  (producer → SPSC ring → per-node hot/slow → OMS drainer is a REAL chain the architecture names);
  (ii) a rendered DATA-FLOW GRAPH surface in nvim over those edges.
- **Why it fits the existing substrate:** the DAG-labeling vocabulary she likes is already the
  sprint nav-infra convention (`*-dependency-graph.md`); the `[DERIVED]` tier is DEFINED as
  compiled/pipeline-reality axes (tools/CLAUDE.md: DEV_PLANE derived = pipeline-reality); the
  plugin already renders call-hierarchy trees (`trace.lua` incoming + callees "Calls" tree +
  neotree) — a graph view is those trees generalized; `check_cache_layout --fix` is the
  writer-precedent for stamping derived facts INTO tag blocks.
- **Design cautions at dive:** chain EDGES for data-flow (not just call-graph) need AST/dataflow
  fidelity — post-`0.6` (TD-256) territory; the KNOWN engine pipelines could land earlier as
  DECLARED chains verified against the call graph (declare-then-verify, the §4 codegen sibling
  posture). Chain-id/seq must never enter IDENTITY (D-tool-385 boundary: derived metadata, not
  identifiers — a re-sequenced chain must not rename anything).
- **Sisters:** §4 (declarative codegen — same declare/derive seam) · §5 (plane index — sibling
  derived view) · TD-256/`0.6` (edge fidelity) · `0.5` cards (where a chain badge renders) ·
  north-star §6 trees (the render surface a graph view generalizes).
- **Dive:** sketch at the `0.5` card dive (badge form), full graph at/after `0.6`.

## 9. The IDE-HUMANIZATION arc (operator directive-by-observation, 2026-08-09, mid-dogfood)

- **As given:** "theres alot that needs to be looked at because technically the tools work, but the
  actual implementation within nvim to make it human useable and into a IDE type custom plugin,
  there is alot of work like that."
- **Reading:** the FACTS layer is proven (foxtag · gates · parity); the remaining `0.4`/`0.5` work
  is USABILITY-hardening, not feature-adding — collisions, discoverability, readable surfaces,
  "what does this key actually do" legibility. Treat UX reports from dogfood as first-class work
  items on par with tool defects.
- **First two instances (operator screenshot, same session):** (i) the inline size chip
  (`◇ 42256 B · 661 cache lines`) COLLIDES with git-blame virtual text at eol — two plugins
  competing for one space; (ii) straddle-diagnostics discoverability — unclear whether it points
  at WHICH field straddles. Both actioned same-session (see plugin log).
- **(iii) NOTED 2026-08-10 (operator screenshots, note-only per operator call):** `<leader>dd → m`
  (the HUD's menu key) and `<leader>dm` (the standalone palette) render DIFFERENT popups for the
  same action set — the HUD path shows the ✎/⚠ write-tier icons + legend and docks to the HUD;
  the `dm` path renders plain labels, no tier column. Same `menu.open` primitive, two invokers
  passing different item shapes — the write-tier metadata should ride the ONE actions registry so
  both renderings are identical by construction (the cd971ac tier work appears to have landed on
  one invoker's item-build only). Fix rides the 0.4 plugin thread.
- **Positive signal recorded:** lock-layout (`<leader>da` static_assert insert) called out as
  "neat" — the insert-a-guard-from-the-HUD shape works; more one-keypress guard-writers of that
  shape are candidates.
- **Sisters:** north-star §6 Target UX (the spec this arc executes) · §8 (graph surfaces) ·
  `0.5` cards (where most rendering lands).
- **THE METHOD (operator, 2026-08-09): derive surfaces from the EXISTING vocab + documentation
  system — never invent per-feature.** "alot of stuff like this could be done based off the
  exisitng vocab and documentation system." Worked instances the same day: the menu's ⚠/✎
  write-tier icons DERIVE from T6's own vocabulary (comments-writer vs the sanctioned
  code-writer); context-gating derives from unit TYPES + runtime state (§6's rule); §5's plane
  views and §8's chain badges are the same shape. The vocab is the design system — a new
  affordance should cite which vocab axis it renders, or it does not belong.

## 10. Tag-scoped MASS OPS + foxtag as the sub-agent CONTEXT PACKER (2026-08-09)

- **As given:** "since we have the TAG system actually implemented it should be easy to make a tool
  to make mass updates at once, or spawn sub agents to assist, if we need to with anything right?
  we just need to make sure they have the appropriate context".
- **What already stands (confirm, don't rebuild):** mass-update machinery = `cascade.py rename`
  (enumerate-only; R1: the COMPILER is the totality oracle for code tokens — no blind `--apply`),
  the doc-rename executor, `check_cache_layout --fix` (the idempotent mass derived-fact writer),
  and deliverable **(d)** — the D-374 update-orchestrator IS the "one tool, mass update" ask
  (vocab → grammar → fix → writers → parity, verify-after). (g)'s new RENAMED status is a
  mass-update INPUT feed (auto-repair payloads). Sub-agent context = the M8 armed-scout
  discipline + `DOCS/SUBAGENT_ARMING.md` + the pre-armed i/a/v/c/d-class agents — "appropriate
  context" is exactly the codified arming step; T12/M10/D-385 gate what a delegate may DO
  (total-oracle delegation only; no blessing).
- **The genuinely NEW composition:** TAG-SCOPED operations — "run X over every unit tagged
  `[SLOW_PATH]`" — and **foxtag as the CONTEXT PACKER**: `foxtag unit/units --json` already emits
  the precise unit, span, and tag set; add its `[REFERENCE]` edges (the (g) resolver) and the
  gates that govern that plane, and you have an AUTO-GENERATED arming payload per unit — the
  arming discipline made mechanical instead of hand-assembled. A cohort fan-out = one agent per
  tagged unit, each armed with its packet, results gated by the same graders as handwritten work.
- **Binding constraints at dive:** Class-36 (substitution corruption) + Class-56 (idempotent
  writers) for any mass writer · R1 compiler-oracle for code · delegation only where the
  acceptance oracle is TOTAL (T12/M10) — a tag-scoped sweep whose grader is partial earns
  hand-review, exactly as today.
- **Dive:** the (d) orchestrator dive (mass-update half) + a small `foxtag arm <unit>` packer
  sketch alongside `0.4`/`0.6` (context half).

## 11.5 REGISTER-PRESSURE checker (operator idea, re-raised + first captured 2026-08-10)

- **As given:** *"we have the register pressure checker right? i think that was an idea i had to
  identify if registers were running out or something."* Verified 2026-08-10: it does NOT exist
  and was not previously captured (the greppable "spill" family is the CACHE-residency lens set —
  ambient/status/dashboard "spills N cache lines" — a different axis; likely the memory's anchor).
- **Reading:** a per-function REGISTER-pressure fact from the REAL build's disassembly — count
  stack-spill traffic (store/reload pairs to `rsp`-relative slots inside the body, distinct
  spill slots, max live span) and surface it as (a) a `[DERIVED]`-adjacent LIVE-PREVIEW fact on
  the asm card (never written — codegen-volatile, the D-327 quartet's sibling), (b) a HUD chip
  (`◇ 3 spills` with hot-path RED per H7/H8 — a spill on the per-tick path is real latency).
- **Placement:** the `0.5` asm/compiled-reality family. **HARD dependency: TD-257**
  (compile_commands 1:1) — a spill count under editor-supplied flags describes a TU nobody
  builds (the D-397 fact-source argument verbatim; -O level changes allocation entirely).
  Sisters: asmexplorer/asmview (the render seams) · `check_latency_path_conformance` (the
  instruction/branch ratchet this would join as a third measured axis) · §2 compile-piping.
- **Dive:** `0.5`, alongside TD-257 + the §2 rider. Until then: manually eyeball spills in the
  1:1 asm explorer (`<leader>de`) — the surface already shows them, uncounted.

## 11. Docview dogfood transmissions — tag-value reflection · TAG ADD · recency-as-rule · parity expansion · float UX (2026-08-10)

- **As given (mid-dogfood, several messages):** *"the floating docs thing has way less options than
  this [the HUD Docs-mention tree], is the tag system actually useful? i like how it looks, but it
  feels kinda overkill in retrospect, but its nice that the plugin can make use of it for options so
  its easy to add things, maybe like a TAG ADD function, where you browse vocab or add new or
  something, or like editable funcitons via scripting? … should we make the menus sort by date as
  well for most up to date information? like should we make other things follow this rule? can we
  expand the parity stuff to other things?"* + the float feedback: *"a little hard to read, and kind
  of makes the code hard to see, also you can[not] navigate back to it once you ctrl hjkl off it …
  it looks better on a full screen."*
- **(i) The design question — mention-sweep vs curated refs (answered, recorded):** the HUD
  "Docs mention X" tree (473 hits / 173 files for FixedPoint) is TEXT SEARCH — every doc that
  MENTIONS the symbol, noise included, unranked. `[REFERENCE]` is GOVERNANCE — the ids that BIND
  the unit (5 for FixedPoint<10,8>). Different questions: "where is this discussed" vs "what
  governs this". The tag system's load-bearing value was never browsing — it is the VERIFIED-FACT
  substrate (the whole D-413/D-414 arc: `[STRADDLE]` facts, H6 gate arming, A2 call-graph
  verification, size gates are ALL tag-driven CI; a grep cannot be gated — a tag can be validated,
  gated, and mined). Browsing consumers are the cheap dividend on top; where plain search serves as
  well, build the search consumer and skip the tag — no tag for tag's sake. The miner
  (`mine_reference_tags.py`, 550 ids from existing prose) makes the curated layer ~zero-maintenance,
  which is what retires the "overkill" cost side.
- **(ii) TAG ADD** (browse vocab → add to the unit; mint new vocab): §9-law-NATIVE — the picker
  DERIVES from the grammar payload (categories / concern / surface vocab) + writes through the
  sanctioned comment-writer tier (✎). New-vocab minting must route through the SSoT (schema fence /
  `doc-tag-vocabulary.md`), never plugin-local. Sisters: `tagwriter.lua` (the write seam) · D-374
  (explicit-invoke writers). → rides the task-#10 unified-registry work as ONE registry row + one
  vocab-derived picker. **→ SHIPPED same session (plugin `7da124e`, `tagadd.lua`):** menu row
  (✎), concern+surface picker from the decoded payload, orient-tier merge (indent-preserving,
  idempotent, tier-disciplined), MERGE-ONLY v1 (no [TAG] line = named refusal), mint-pointer at
  `add_vocab.py`. Pure teeth 8/8.
- **(iii) Recency-as-rule:** chronological-ish lists (plans · changelog · decisions · choosers over
  dated ids · the Docs-mention subtrees) sort NEWEST-FIRST as a RENDERER-level rule, not
  per-surface code; semantic sets keep grouping. → the unified renderer (task #10; I-2's
  conventions census slots it).
- **(iv) "Editable functions via scripting" / mass ops:** reads as the §10 tag-scoped MASS-OPS +
  §4 declarative code-gen family — scriptable operations addressed by tag scope. Placement
  unchanged (§10/§4).
- **(v) Float UX triad (I-2 / task-#10 input):** (a) the doc float overlays code — hard to read in
  cramped windows, fine fullscreen → size must adapt to editor dims; below a width threshold open
  the PIN split directly instead of a float; (b) **FLOAT FOCUS TRAP** — directional window-nav
  (ctrl-hjkl) skips floats, so once focus leaves, hjkl cannot re-enter (orphaned lens) → fix =
  close-on-focus-leave (transient-lens semantics; KEEPING it is what `p`-pin exists for — a split
  IS hjkl-navigable); (c) both land with the I-1/I-2/I-3 unification synthesis, not as one-off
  patches.
- **(v.5) `.toolbus/` first-consumer SHIFTED (recorded 2026-08-11):** the 0.4 plan line lands
  `.toolbus/` "WITH its first genuine consumer — the VOLATILE `layout--<target>.json` (re-running
  clang per call hurts)". That consumer was the dashboard census — which now reads the WRITTEN
  tag corpus instead (one rg pass, no clang; the 2026-08-11 rewire). The next genuine volatile
  consumer is the `0.5` asm/compiled-reality cards (TD-257-gated) → `.toolbus/` re-sequences to
  land WITH 0.5, not before. Annotate the plan's 0.4 line at the next planning touch.
- **(vi) Parity-expansion:** the plugin parity fleet (I-1/I-2/I-3, this session) is the METHOD
  instance; standing expansions already homed — TD-270 (reference-membership two-cores) ·
  `/parity-check` (train↔serve) · the toolio registry (producer surfaces, TD-258). Further
  expansion = per-surface on evidence, not a blanket sweep.

## 12. The shipped-asm substrate roadmap (operator-confirmed 2026-08-13, mid-dogfood)

- **As given:** *"i like the sound of all of these, as well as instruction counts per function,
  etc, so i can see if hotpath and slow path are within instruction budget, etc, and this can
  also be used to make the other features more informative i think, right? like the alignment
  stuff, etc, opportunities for optimizations"* — confirming the five-rung ladder proposed the
  same sitting, adding per-function budgets + cross-feature enrichment.
- **The substrate (LANDED same day):** `-g` on the four main targets (zero codegen change —
  GCC guarantee; debug sections strippable) + sidecars auto-emitted by EVERY build (`build.sh`
  `emit_asm_for_dir` chained after each `cmake --build` — always 1:1 with live, the operator's
  "compiled alongside" ask) + `objdump -l` line interleave + the card's bidirectional
  source↔shipped-asm cursor sync (both panes highlight; `line_map`/`same_source` pure core).
- **The rungs (each reads the SAME sidecars; ordered by dependency, dive per-rung):**
  1. **Inline attribution** (`--inlines`): "Notify_Send's code lives inside these N callers at
     these ranges" — DWARF inlined-subroutine records; the full answer to the bare-`0` case.
  2. **Per-line shipped-cost chips**: the explorer's "→ N instr" measured on the LINKED binary
     (post-LTO/inlining truth). `line_map.n_insn` per function already counts the total.
  3. **Per-function instruction counts vs BUDGETS (operator ask):** hot/slow-path functions'
     shipped counts joined with `check_latency_path_conformance` budgets + `[HOT_PATH]`/
     `[SLOW_PATH]` tags — over-budget = RED chip (H7/H8 made visible at edit-time). Rides the
     TD-257 probe-cutover leaf (the checker consumes the same real-build facts).
  4. **Register-pressure chips** (§11.5): spill counting over the real block — now UNBLOCKED
     (the sidecars are the real-build substrate §11.5 was gated on).
  5. **Cross-binary function diff**: same function, engine vs engine_gui, via asmdiff.
  6. **Ceiling: perf-annotate in the card** — sample counts per shipped instruction joined
     with tags + budgets: source line → shipped instructions → measured ns, one keypress.
- **Cross-feature enrichment (operator's "make the other features more informative"):** RC-F's
  access-cost axis, the `[DERIVED]` SIMD/insn facts (`fn_metrics` currently re-compiles with
  editor flags — cut standalone-fn metrics over to shipped blocks), and the dashboard's
  compiled-reality tiles all read the same sidecars once the per-rung dives land.
- **Boundary:** display/facts only — the tool never auto-reorders/unpacks (H14/H21 spirit; the
  RC-F honest-tension rule generalizes: SHOW both costs, operator decides).
