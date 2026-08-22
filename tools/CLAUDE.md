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
| **T13** | A fact-PRODUCER ships UNIT TESTS, wired, alongside the change — a `--selftest` is a non-vacuity proof, not a correctness proof | D-411 |

- **A fact-PRODUCER ships UNIT TESTS, alongside — not a selftest instead of them (T13, D-411).**
  The three artifacts already in use are NOT interchangeable and conflating them is how this gap
  survived: a **BASELINE** is an exception list (grandfathered known-bad, shrinking — it does not
  pin output); a **GOLDEN** pins emitted output for a fixed input; a **SELFTEST** proves the guard
  is non-vacuous (T5). **None of the three asks whether the tool is CORRECT across its inputs.**
  A selftest answers *"can this guard fail?"*; a unit test answers *"is this guard right?"* —
  and the evidence that the difference is load-bearing is `E.1.2.B` `0.2` itself: **every defect
  it found lived in a tool that had a selftest and passed it** (a suffixed id collapsing onto its
  parent; a 4295-byte block over-run under 8/8 green teeth; an absent golden silently disabling
  removal-detection while Check 14 stayed green; a hardcoded registry mirror drifted 4-vs-5).
  **Scope — producers, not everything.** The obligation attaches where a wrong fact FANS OUT
  (`citable_ids` · `foxtag` · `check_cache_layout` · anything N consumers inherit), not to all 100
  tools; blanket-testing leaf consumers is the proportionality error that gets suites abandoned.
  **And "alongside" is the operative word** — "after" is what produced 100 tools with 2 unit-test
  files. Wire them; an unwired test is `advertised-capability-never-exercised`, which cost four
  silently-dead guards (TECH_DEBT-265), two of them on capital/determinism surfaces.
  → `DESIGN_SPECS/meta-disciplines/toolchain-test-tier-model.md`.
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

### E.1.2 / D-421 steps 2+4+5 harvest (2026-08-15, session 2)

- **`bless.py::_isatty()` requires stdin AND stdout to BOTH be TTYs — so Claude Code's `!` prefix
  does NOT satisfy it.** Every D-394-gated mutation routes through this (`check_tech_debt.py
  --close`, golden re-bless, `--console`). The agent path refuses, as designed — but so does the
  operator running `! python3 tools/check_tech_debt.py --close 196`, because the `!` prefix CAPTURES
  stdout to show it in the transcript, which makes `sys.stdout.isatty()` false. Both refusals print
  the identical message, so it reads like a permission problem escalating correctly when it is
  actually the same gate twice. **It needs a real terminal outside the harness.** Do not read the
  second refusal as the gate malfunctioning, and do NOT reach for a `--yes` — there deliberately
  isn't one, and the refusal IS the control (its own message says so).
- **`check_close_out_completeness.py --since <sha>` resolves the window in the WORKSPACE repo.** Hand
  it an ENGINE sha and it prints `no commits in <sha>..HEAD — nothing to check` and exits **0**. That
  is a clean-looking pass that checked nothing — the auto-write ledgers it guards live workspace-side,
  so the window must be a workspace anchor. Observed live at this close: the engine pickup SHA
  produced a green, the workspace SHA produced **5 owed surfaces and rc 1**. Sister shape to Class 57
  (an unrunnable check rendering as a clean result); the tool is not wrong, the SHA namespace is
  ambiguous and the failure is silent.
- **`check_tools_inventory.py` scans every tool's BODY for `tools/<name>.{py,sh}` references and REDs
  on ones that do not exist** (`REF_RE = tools/([A-Za-z0-9_]+\.(?:sh|py))`). So a negative-test
  FIXTURE that names a realistic-looking tool path makes the inventory guard red on the file holding
  the fixture. Its own header records being bitten by exactly this. The fix is to put the fixture
  path OUTSIDE the pattern (`__nonexistent__/no_such_checker.py`), not to widen the exclusion list —
  the whole-file `test_` prefix exemption is the only built-in escape and it does not apply to a
  non-test tool. Keeps both guards at full strictness.
- **`gen_code_map.sh` is stamp-on-change (D-369), so its `Last regenerated: commit X` header records
  the last CONTENT change and NOT the last run** — it will legitimately sit behind HEAD after any
  commit that touched no `Pattern_FunctionName` definition (e.g. an X-macro registry or comment-only
  change). `/close-session` Stage 5.5 dimension #7 says the header "must == HEAD"; that is in tension
  with D-369 and should be read as *the CONTENT must be current*, verified by running the regen and
  seeing `already current — no write`. Churning the file to advance the stamp would defeat the
  stamp-on-change property.

### E.1.2 / D-421 harvest (2026-08-15)

- **`check_reset_before_producer.py` — finding a C++ function by name is a trap in THIS tree.** The
  first draft located the definition with "first line mentioning the name", which here is a
  `// - [FUNCTION]_[Name]` tag-block comment ~3000 lines above the real body. It brace-matched an
  unrelated region, found neither the reset nor the producer, and **REFUSED** — and that refusal is
  the only reason the mistake surfaced instead of silently passing over an empty body. Correct
  predicate: skip comment lines, then require the arg list to be followed by `{` (a call and a
  declaration both end in `;`; only a definition opens a body). **Generalizable:** any tool that
  scans "inside function F" in this codebase must survive the tag-block grammar, and must treat
  scan-found-nothing as FATAL — a wrong-region scan is indistinguishable from a clean one otherwise
  (Class 51 / Class 57).

- **`check_per_node_registry_integrity.py` — FIXED, and the first diagnosis was wrong.** It exited 2
  with "file not found: <workspace>/CoreFrameworks/…" in a gate battery, and I recorded that as
  *"must be invoked from the ENGINE root"* — a **cwd** diagnosis. The a-class review falsified it in
  both directions by probe: cwd=engine + script=workspace-path → rc 2; cwd=workspace +
  script=engine-path → rc 0. **The determinant was the SCRIPT path, never the cwd** — it rolled its
  own `REPO_ROOT = Path(__file__).absolute().parent.parent`, and `.absolute()` deliberately does not
  resolve the `tools/` symlink, so the engine root became a function of the path you typed. Now
  imports the shared `check_doc_metadata.ENGINE` like its ~20 siblings (D-372 "no tool rolls its
  own"); all three invocation forms return 0. **The lesson is the one worth keeping: a per-invocation
  ritual in a handoff expires, the tool does not** — prefer deleting the landmine to documenting it
  (`feedback_structural_fix_over_belt_and_suspenders`).
- **`emit_record_layout.lua` record-name matching had a silent hole.** It matched the fully-qualified,
  the template-stripped base, and the bare name — but NOT the namespace-stripped-template form, so
  `NodeContext<64>` matched *nothing* and the emitter answered `[]` with **rc 0**. A complement
  consumer trusting that would compute over zero members and pronounce a 49-field struct fully
  covered. Fixed (the `tmpl` form) + `--require-all` makes a requested-but-absent record fatal.
  **`--require-all` is OPT-IN on purpose**: `check_cache_layout.py` batches ~193 requests of which
  ~77 are legitimately absent and reports them TU-scope-honestly; making absence fatal by default
  converted that gate into "could not run" across all 193 — strictly worse than pass or fail.
- **`node_persist_layout._args` is deliberately NOT quote/comma-aware.** Its exact-arity REFUSAL on a
  comma-bearing row is a real tooth (a-class R1-c: "never silently eat the count token"). Do not
  "fix" it — I tried, and the selftest correctly caught that it converts a loud correct stop into a
  silent accept. A consumer needing prose columns supplies its own splitter (see
  `check_node_ctx_partition._split_cols_quoted`).
- **`_strip_comments_text` blanked `\`-continued block comments to bare newlines**, deleting the
  continuations *inside* the comment span and truncating any registry whose body contains one —
  `FOREACH_OMS_PER_SLOT_FIELD` parsed as **1 of its 5 rows**. Latent for all 5 H21 sources (verified,
  not assumed); goes live the moment a tool parses all 68. Fixed + 2 positive-control teeth.
- **`check_code_tag_blocks` DERIVES its CATEGORY set** from the ```category-set``` fence in the schema
  spec — folding a category is ONE token in the doc and ZERO tool edits. Before inventing a category,
  check whether the concept already exists one level down as a VALUE under an existing one (the RED
  now tells you which).


Harvested 2026-07-19 from E.1.2.B `0.1.5`/`0.3`, where **each of these cost a debug cycle or produced
a FALSE finding**. If you discover a tool behaviour that is not derivable from its `--help` or its
docstring, write it here — that is the entire point of this section.

- **Annotating a stale `file:line` cite in an APPEND-ONLY doc: use the two machine-recognized markers, same line as the stale cite.** `**[NOW: \`path:line\` — reason]**` = resolved; anchors INSIDE the bracket are the fresh pointers and are VERIFIED (a bad NOW-target still reds — proven by `--selftest`); the stale original on that line downgrades to `annotated`. `**[CITE-AS-EVIDENCE]**` (exact spelling, bare bracket — a suffixed form like `[CITE-AS-EVIDENCE — why]` is NOT recognized; put prose outside the bracket) = the line QUOTES dead/schematic paths as evidence (D-390's false-positive surface); nothing verified. Legacy `[PATH SUPERSEDED …]` is honored like NOW. Recognizer + teeth: `check_plan_body_symbol_existence.py` (`extract_line_anchors` + `--selftest`, wired HARD in `check_session_docs`). An annotation the scanner cannot see is decorative — Class-51 B′.
- **Re-blessing ANYTHING: `python3 tools/bless.py --console` — the one menu.** Enumerates every blessable record (citable-ids golden · both corpus pins · the H21 ledger · the latency ratchet) with drift status; enter a number and that record's OWN D-394 gate runs (diff + typed confirmation; non-TTY refuses rc=2, console included). Roster coverage of `tools/goldens/*.txt` is selftest-enforced so a new golden cannot be silently un-menued. The per-record one-liner below stays as fallback.
- **Re-blessing the citable-ID golden: use the ONE-LINER, not a heredoc — and you can DEFER it.**
  Pasting a heredoc into interactive zsh drops you at a `heredoc>` continuation prompt. This runs
  as a single command from the engine root:
  ```
  python3 -c "import sys;sys.path.insert(0,'tools');from citable_ids import defining_index;import bless as b;idx=defining_index();sys.exit(b.bless('tools/goldens/citable-ids.txt',sorted(f'{ns}|{r}' for ns,e in idx.items() for r in e),'citable-ids'))"
  ```
  **A helper script does NOT belong in `tools/`** — every `tools/*.py` must be enrolled in
  `DOCS/TOOLS.md` or the tools-inventory HARD gate fails (learned the hard way 2026-07-20;
  TECH_DEBT-244 de-sprawl). **CADENCE: the golden's job is catching REMOVALS.** Additions are legal
  under H21 and `--check 14` stays green regardless, so an un-blessed addition is an unprotected
  slot, NOT a defect. Bless at SHIP CLOSE, not every session — and check the REMOVALS count first;
  it is the only alarming number. No agent can do this for you: `bless.py` HARD-REFUSES
  non-interactively by D-394, and that refusal is the control (D-385/M10).
- **The tech-debt ledgers spell an entry's anchor THREE ways — a one-spelling grep is HALF-BLIND.**
  `### TECH_DEBT-N` (heading, always present) · `id: TECH_DEBT-N` (bare) · `- **id:** TECH_DEBT-N`
  (bold). Measured 2026-07-20: bare 99 / bold 94 in `open.md`, bare 39 / bold 15 in `closed.md`.
  **PARITY is not symmetric** — 10 of its 41 entries live in ```yaml fences with **no heading at
  all**, so "just anchor on the heading" is correct for TECH_DEBT and wrong for PARITY. Match the
  UNION. And **~37% of defining headings are ZERO-PADDED** (`TECH_DEBT-016`), so normalize through
  `int()` — `-16` and `-016` are one id. This cost three separate live defects: a pre-commit gate
  emitting HIGH findings for entries that exist, two SKILL.md prose recipes producing a false
  BLOCK *and* a vacuous PASS, and `--close 16` erroring while `--close 016` silently WROTE.
  Reference implementation: `_anchor`/`_has_entry`/`_entry_block` in `check_forward_promise_audit.py`.
- **`check_tech_debt.py --close` MUTATES two ledgers and is now TTY-gated — `--dry-run` first.**
  It moves an entry `open.md` → `closed.md` with no undo but git. Until 2026-07-20 it wrote **by
  default** with no diff and no prompt (found by firing it during a read-only verification; it
  silently moved TECH_DEBT-016). It now routes through `bless.confirm_mutation()` and HARD-REFUSES
  `rc=2` non-interactively, like every other mutating writer. **If you are an agent: the refusal is
  the control, not a permission problem to route around.**
- **A `--check` that cannot LOCATE its target must not return 0.** `rebuild_doc_indexes.py` found
  the CLAUDE.md skill table via a regex hardcoding the heading text; on a miss it printed to stderr
  and fell through, so the wired HARD gate printed *"✅ indexes current"* and exited 0. One hyphen
  in that heading disarmed it. Locator failures now return **rc=2 ("could not evaluate")**, distinct
  from rc=1 ("stale") — the same idiom as a missing golden. **General rule: 3 of that tool's 4
  targets regenerate-and-byte-compare and are structurally immune; only the one that must locate a
  region it does not generate could go blind. Prefer derive-and-compare over locate-and-check.**
- **`bless.confirm_mutation(label, action, noun)` is the ONE D-394 confirmation contract.** Import
  it; never re-type the prompt. TECH_DEBT-255 existed *because* two writers had opposite postures,
  and re-typing is how they diverged. Import it **HARD** — a `try/except` fallback would silently
  restore write-by-default the moment it broke.
- **`citable_ids.defining_index()` is UN-MEMOIZED — ~24 ms per call.** Fine once; a per-id loop over
  the 251 TECH_DEBT ids is ≈4.7 s. It also returns `(path, lineno)` only, so it **cannot** give you
  entry BLOCK boundaries — placement questions yes, body questions no. Memoize before migrating
  consumers onto it.
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

*Harvested 2026-07-19 from the `0.2` armed I→A sweep (D-392). Each is a VERIFIED code property, not a
recollection; each one cost a wrong assumption somewhere in this ship.*

- **`toolio.read()` DISCARDS the envelope frame — nothing validates the tool-I/O contract.** It is
  literally `return env["payload"]`. So `envelope_version` / `schema_version` / `payload_schema_version` /
  `producer` / `status` — the three D-379 version axes `0.1.5` exists to carry — are checked by **no one**.
  Demonstrated: an envelope with 9 simultaneous frame corruptions (wrong locked `schema_version`,
  unregistered payload kind, `status.ok:false`) passes `parity_check.sh` §3b unchanged. **Do not assume the
  envelope is self-validating because it is well-specified** — emit builds the frame, read drops it.
- **`parity_check.sh` §1 compares exit codes for EQUALITY, never for ZERO** (`:35-37`). Both validators
  failing identically prints `OK  : exit codes identical (1)` and the run still reaches `PARITY: PASS`.
  The gate can certify a corpus that is failing validation, and symmetric bilateral failure (both exit 2,
  empty stdout) is indistinguishable from bilateral success. **A green parity run is NOT a green corpus.**
- **`tools/lib/` is a GUARD BLIND SPOT — the rule is `tools/` = CODE, `tools/lib/` = DATA.**
  `check_tools_inventory.py:46-47` and `check_import_from_core.py:74` both glob **non-recursively**, so a
  `.py` placed under `tools/lib/` is exempt from inventory enrollment AND the roll-your-own-root lint.
  `tools/lib/` is deliberately code-free today (baselines · the ratchet · input lists · the schema registry).
  D-384 #4 moved `toolio.py` out for exactly this reason; C-389 re-applies it. **Never put a guard where the
  guards cannot see it.**
- **The citable-ID resolver exists TWICE — Python AND C++, and both feed the parity-diffed surface.**
  `check_code_tag_blocks.py:155-206` (by-mention at `:170`) and `foxtag.hpp:406 RefIndex` / `:432
  load_ref_index` / `:583 ref_resolves` → `validate` at `:766`. `parity_check.sh:20-21` diffs `validate`, so
  **changing the membership rule on one side alone REDs parity.** Any ref-index change is lockstep, or the
  source spec moves to a language-neutral registry both read.
- **Parity is DIFFERENTIAL — it proves agreement, never correctness.** Common-mode corruption of a shared
  SSoT is invisible by construction: both sides derive the grammar from the same fences (T2), so deleting
  vocab rows keeps them agreeing and the gate stays green. The record shows the mechanism — `categories`
  moved 76→78 across the gate's lifetime with PASS throughout. **This is why D-386 output goldens are the
  COMPLEMENT to parity, not merely more of it.**
- **`foxtag --help` under-reports its own producers.** The usage string (`foxtag_main.cpp:274`) lists
  `validate|units|unit|tags|grammar|parity-dump|selftest`, but the dispatcher also implements `codegen`,
  `codegen-selftest`, `layout`, and `fields`. **Four producers are undiscoverable from `--help`** — enumerate
  from the dispatcher, not the usage line.

*Harvested 2026-07-19 (wave 3) from the `0.2` precedent + anti-pattern sweeps. Each of these caused or
concealed a REAL defect in the artifacts landed that same session.*

- **⚠️ ALL SCALARS IN A SHARED JSON DATA FILE MUST BE STRINGS — including booleans and integers.**
  `foxtag.hpp`'s `JVal` has `Kind {STR, ARR, OBJ, OTHER}` and **no bool/number kind**, so a bare `true`
  or `150` parses as `OTHER` with an **EMPTY string** — a *silent* wrong-read, not an error. Measured
  with a compiled probe: the C++ side read `follow_file_symlinks` as empty while Python read it fine,
  which would have made the load-bearing clause invisible to exactly one of the two readers.
  `tools/lib/toolio_schemas.json` already obeys this (zero bare scalars) — that is the parser's
  constraint, not a style choice. **Do NOT "clean up" a contract file to native JSON types.**
- **A GOLDEN pins a different population than the ENUMERATOR scans.** The enumerator is gitignore-blind
  (a real source file is real whether or not it ships); a golden is a **committed, distributed** artifact
  and must pin **git-TRACKED entries only**, or it resolves differently on every machine. The first
  corpus golden pinned 31 untracked entries including two **mkstemp random-named** scratch files, so a
  fresh clone diverged 31 lines unconditionally — re-instantiating, one layer up, the machine-local-path
  class that `0.1` closed. **Any committed pin: ask "does this resolve identically on a fresh clone?"**
- **A substitution token in a data file MUST be documented beside the others.** `corpus_contract.json`
  used `PROFILE` in a path template while documenting only `$ENGINE`/`$WORKSPACE` — so each of the two
  readers would have had to GUESS the rule, which is the exact divergence axis a shared contract exists
  to eliminate. **If a data file has two substitution conventions, name both in the same place.**
- **A consumer that cannot find its golden/baseline MUST loud-fail, never treat absence as "nothing to
  compare".** Absence-passes-silently is Class-51 planted in the guard layer itself.
- **Parity is DIFFERENTIAL and a golden is ABSOLUTE — they are complements, not duplicates.** Parity
  proves the two implementations AGREE; it cannot see common-mode corruption of a shared SSoT (evidenced:
  `categories` moved 76→78 with PASS throughout). Wiring an `A==B` check as a standing gate silently
  widens its contract from AGREEMENT to VALIDITY — the thing it was never written to assert.

*Harvested 2026-07-20 (wave 4) from the `0.2` gate-layer build. Every one cost a wrong turn, a
dead tooth, or a false finding IN THIS SESSION — none is derivable from a `--help` or a docstring.*

- **⚠️ ripgrep SKIPS a gitignored DIRECTORY but RETURNS a file-level-ignored FILE.** Measured: a
  `.gitignore` containing `private/` hides `private/x.hpp` from `rg`; a `.gitignore` containing
  `hidden.hpp` does NOT hide it. This made the first TECH_DEBT-245 non-vacuity tooth **vacuous** —
  it planted a file-level ignore, so it would have passed against the very rg-based enumerator it
  existed to catch. **Any gitignore fixture must use a DIRECTORY rule**, which is also the
  real-world shape (`.gitignore:167 Strategies/private/`).
- **`DOCS/TECH_DEBT.md` is an INDEX, not a ledger.** It holds the format template and the
  entry-to-sub-file map; the actual entries live in `DOCS/tech-debt/{open,in-flight,closed}.md`.
  A `^### TECH_DEBT-` scan over it returns ~1 row. Do not read a low count there as data loss
  (TECH_DEBT-219 tracks the split).
- **MASTER banners APPEND; plan-body banners PREPEND.** `check_index_currency.py:82` takes the
  **LAST** `handoffs/*.md` reference on a `Pickup`/`ACTIVE one` line, because "banners append
  progress lines". Prepending a MASTER banner therefore leaves the check reading a SUPERSEDED
  pointer — the new banner is invisible to it. The plan body's convention is the opposite
  (prepend, preserve prior), so the two files take opposite rules.
- **`DESIGN_PHILOSOPHY.md` contains BOTH a §11.5 DEFINING table (`| **M1 — …**`, bold) and a
  cross-reference index (`| M1 — … |`, plain).** A meta-discipline regex with optional bold matches
  both and reports 8 of 10 M-numbers as DOUBLE-DEFINED — all false. The bold is load-bearing.
- **`CLAUDE.md`'s Hard-Invariants table mixes bold and plain rows** — H15/H18/H19/H21/H22 are bold,
  H1-H14 are not. A pattern requiring `|` immediately after the digits silently drops 6 of 22.
  **Check any namespace count against its KNOWN range** rather than trusting the match.
- **`check_capture_audit.py` runs ONCE per commit, not per staged file** — trigger-gated at
  `.githooks/pre-commit:193` on a memory/skill/index/decision-log path match. Cost added there is
  paid once, which is why a 14s corpus-wide check is affordable in it.
- **`check_plan_body_symbol_existence.py --all` is UNRUNNABLE** — 886 plan files, 259 with cpp
  fences, **1237 blocks × ~451ms per `g++` probe = 9.3 min**, so it times out. The staged-file path
  is milliseconds. TECH_DEBT-259; do not reach for `--all` expecting an answer.
- **`parity_check.sh` costs ~25s and the foxtag BUILD is not the cost** — it is cached. The time is
  nvim + clang + objdump in the plugin/layout/codegen sections.
- **A Python combined-alternation regex with NAMED groups wrapping inner captures returns the OUTER
  match first.** `next(g for g in m.groups() if g is not None)` yields the whole match
  (`"TECH_DEBT-114"`), not the id body — `int()` then explodes. Use `m.lastgroup` and re-apply that
  namespace's own pattern. This turned an 8-pass-to-1-pass optimisation into a behaviour change.
- **A perf fix that changes results is a behaviour change wearing a perf costume.** Two separate
  optimisations of the Check-14 scan each altered the finding count (145 → 141) while barely moving
  the clock. Both reverted. Diff the FINDINGS, not just the runtime, after any tuning.

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

## Toolchain gotchas — 2026-08-16 (E.1.2 D-422/D-423)

Four behaviours discovered by being bitten, none derivable from `--help` or a docstring.

- **`rg <pat> .` from the engine root is BLIND to `tests/`, `tools/`, `plans/`, and NO flag rescues
  it.** They are gitignored *and* directory symlinks; `--no-ignore`, `--follow` and both together
  were each measured at **0** hits while the explicit path returns 80. Cost: enumerating a producer
  set returned 2 sites when the truth was 7, and the 5 missed included the test fixtures that were
  the whole point of the check. **Name roots explicitly and state which you covered.** Full detail:
  LANDMINES 19.
- **This shell is zsh, which does NOT word-split an unquoted `$VAR`.** `R="dirA dirB"; rg pat $R`
  passes ONE bogus path named `"dirA dirB"`; rg errors to stderr and, suppressed with `2>/dev/null`,
  it is indistinguishable from a clean no-match. Use a literal list, an array, or `${=R}`.
- **`Fn\s*\(` misses explicit template arguments.** `EnsembleZoo_FinalizeCorrupt<F>(...)` puts `<F>`
  between the name and the paren, so a live capital-adjacent call read as uncalled in a
  dead-function sweep. Use `\bFN\s*(<[^;()]*>)?\s*\(`. Sister trap: **macro-pasted names** —
  `MASK_NODE_STATE_MODEL_CORRUPT` exists nowhere as a literal because the setter is
  `NODE_STATE_FLAG_SET(node, MODEL_CORRUPT)`.
- **`check_close_out_completeness.py` declines to run below `--min-commits` (default 8) — it now
  says so in a signal you cannot mistake for a pass (FIXED 2026-08-16, AR-18).** It used to print
  `SKIP — a small session legitimately owes nothing` and **exit 0**, so a caller rendering exit-0 as
  ✅ showed a green row for a check that had evaluated nothing. A session splitting work across two
  repos lands few WORKSPACE commits and trips this easily; it read as a pass twice in one close while
  **four** auto-write surfaces were genuinely owed, surfaced the moment `--min-commits 1` was passed.
  It now prints `DID NOT RUN` and **exits 3** on both the below-threshold and empty-window paths, with
  two selftest teeth pinning it. Still pair the `--since` (which resolves in the **WORKSPACE** repo —
  an engine SHA silently checks nothing) with an explicit `--min-commits` at close.
  **Treat exit 3 as "unknown", never "clean".**

## Toolchain gotchas — 2026-08-17 (E.1.2 D-426)

Three behaviours discovered by being bitten, none derivable from `--help` or a docstring.

- **B-Plus (`check_plan_body_symbol_existence.py`) COMPILES every ` ```cpp ` fence, and its
  FABRICATION leg is NOT scoped by `frozen_record_paths()` even though its ANCHOR leg is.** The
  contract it enforces is "a ` ```cpp ` fence in a plan body is proposed code, so it must compile."
  An EVIDENCE doc quoting three verbatim lines of production source is not making that claim, but
  the tool cannot tell the difference — both fail to compile. `/reports/` is already in
  `frozen_record_paths()`, which is why the RENAMED cite warnings on those same files were advisory
  while the fabrication errors were BLOCKING. Cost: a blocked close-out commit and a near-reach for
  `SKIP_PLAN_BODY_CHECK=1`. **Fix the FENCE, not the gate** — tag verbatim excerpts anything other
  than `cpp` (the extractor matches `startswith('```cpp')` exactly, so ` ```c++ ` is skipped and
  still highlights). Whether the fabrication leg should inherit the frozen scoping is open —
  TECH_DEBT entry filed; agent reports are a doc type that postdates the tool.
- **`check_close_out_completeness.py` silently EVALUATES NOTHING below `--min-commits` (default 8),
  and exits 3 — which is not 0, but is easy to read as "fine, small session."** Its own message is
  honest about this ("this run did not CHECK that"), and that honesty is the only thing standing
  between you and treating a non-evaluation as a pass. On a 3-commit close it must be re-run with
  `--min-commits 1` to actually assess the window. Cost: nearly closed a session on an unevaluated
  gate — the exact vacuity shape the session spent the day cataloguing.
- **`bless.py --console` offers EVERY drifted blessable record, so "I blessed it" and "the record
  you meant got blessed" are different claims.** Three consecutive rounds reported the identifier
  ledger as blessed while the diffs landed on `tools/goldens/citable-ids.txt` and the latency
  ratchet's `_provenance` — because the identifier ledger showed **no drift to bless** until its
  `SOURCES` row existed, so it was never offered. **Verify the target, not the act:** `grep -c
  '^<category>|' tools/identifier_ledger.txt` and confirm the guard reports no pending `ADD (ok`
  lines. A bless that had nothing to write is indistinguishable from one that was never run.

### Addendum — 2026-08-17 close (same D-426 arc, found while running the close itself)

- **`check_close_out_completeness.py --since` resolves its SHA against the WORKSPACE repo, not the
  engine.** Passing the engine's session-start SHA gets *"DID NOT RUN — no commits in <sha>..HEAD"*
  (rc=3), which reads like "nothing to evaluate" and is really "your anchor does not exist here."
  Two of the three gotchas already in this section are the same shape — **an honest refusal that is
  easy to read as a pass** — and this one is the sharpest, because the message names a real-looking
  empty window rather than an unknown ref. Anchor it to the workspace: `git -C
  ../tick-trader-percore-workspace log --oneline | head`, or just use the previous handoff's
  workspace HEAD. Cost: two wasted runs before the anchor was suspected.
- **The three gotchas above were already written down, and were hit anyway** — the close ran into
  the B-Plus fence rule and the `--min-commits` refusal, both documented in this very section hours
  earlier, because nothing consults this file at the moment of use. That is the honest limit of a
  gotcha registry: it is a *recall* aid, not a guard. Where a gotcha is mechanizable, prefer the
  guard (the `$?`-after-pipeline hook is the model — it BLOCKS rather than reminds); where it is
  not, expect to pay it once more per session and keep the entry short enough to scan.

## Toolchain gotchas — 2026-08-20 (E.1.2.C tail close)

- **`check_cache_layout.py --fix` REFRESHES existing `[DERIVED]` markers; it does not ADD them.**
  A new `[STRUCT]` block with no `// [DERIVED]` line gets "Refreshed 0 tags" (reads like a pass)
  while the conversion-completeness check simultaneously reds C3 no-DERIVED on the same block. Seed
  the bare `// [DERIVED]` marker by hand ONCE between `[END_CODE]` and `[END_STRUCT]`; `--fix` then
  owns it forever (it populated 26 tags across the 3G files the moment the markers existed).
- **The `--since`-anchor trap RE-HIT, exactly as predicted.** The 2026-08-17 addendum above said
  "expect to pay it once more per session" — paid, same shape, this close (engine SHA → rc=3
  "DID NOT RUN", two runs wasted before the workspace anchor was suspected). The prediction is now
  measured behavior, which strengthens its own conclusion: mechanize where possible, and treat any
  close-out run whose verdict is "no commits" as a WRONG-ANCHOR alarm, never a pass.
- **A handoff supersede is a TWO-KEY mutation — `status: superseded` AND `superseded_by:` — and
  half-flipping it reds a HARD gate later, not at write time.** The back-pointer as a comment
  satisfies a human reader and fails `reciprocal-supersession ((g)-4)`. Pair rule: write both keys
  in ONE edit, and run the FULL sweep (not the narrow singleton check) as the LAST act before the
  close commit — the narrow-green-standing-in-for-the-broad-check is the Class-51-adjacent shape
  the AR-8 reviewer caught this close.
- **CP-1 amendment-cascade advisory on ARCHIVED sprint plans is noise by design:** historical
  records (v5.10-era MASTERs etc.) legitimately keep retired phrasings; do not rewrite archives to
  quiet it. Its signal is for LIVE docs only.
- **`check_close_out_completeness.py --since` takes the WORKSPACE sha, not the engine one.** Passing
  the engine session-anchor makes it print `DID NOT RUN — no commits in <sha>..HEAD` and exit 3.
  That message is honest ("this is not a pass") but easy to misread as a tooling error rather than a
  wrong-repo argument, because the engine sha *resolves* — it just has no commits in the workspace
  history. Pass the workspace-side anchor. (2026-08-21, E.1.2.D close.)
- **It evaluates COMMITTED work in the window, not the working tree.** Writing the owed
  auto-write entries and immediately re-running still reports them ❌ — the entries have to be
  COMMITTED before the check sees them. Sequence it as: write → commit → re-run → `--explain` only
  what is genuinely not owed. Discovering this by re-running twice is the normal path; it is not a
  false positive. (2026-08-21.)
- **Pre-commit `Check F` (determinism net) is FILE-SET TRIGGERED.** It fires on "staged FP/parse/
  locale change detected", so a raw `atof/strtod/atoi` added to a file in
  `locale_determinism_known_pending.txt` can commit CLEAN if that commit's staged set does not arm
  the trigger — and then sits until an unrelated later commit happens to stage a triggering file.
  Measured: a raw `atoi` added at `cd9c2c7` surfaced only two commits later. When touching a parser,
  run `./tools/check_locale_determinism.sh` directly rather than trusting the hook to have looked.
  (2026-08-21, SC-1 in the E.1.2.D plan; M7 candidate — fire Check F on any staged file present in
  the manifest.)
